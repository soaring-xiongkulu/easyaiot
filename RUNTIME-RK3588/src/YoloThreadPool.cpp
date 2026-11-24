#include "YoloThreadPool.h"

#include <algorithm>
#include <chrono>
#include <glog/logging.h>
#include <limits>
#include <pthread.h>
#include <sched.h>

namespace {

void pinCurrentThread(int cpu, const std::string& name) {
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(cpu, &set);
    const int affinityResult = pthread_setaffinity_np(pthread_self(), sizeof(set), &set);
    if (affinityResult != 0) {
        LOG(WARNING) << "[RK3588] 线程亲和设置失败 name=" << name
                     << " cpu=" << cpu << " error=" << affinityResult;
    }
    pthread_setname_np(pthread_self(), name.substr(0, 15).c_str());
}

}  // namespace

YoloThreadPool::~YoloThreadPool() {
    stopAll();
    for (auto& thread : workerThreads_) {
        if (thread.joinable()) thread.join();
    }
    workersDone_.store(true, std::memory_order_release);
    if (collectorThread_.joinable()) collectorThread_.join();
}

int YoloThreadPool::setUp(const std::vector<ModelSpec>& models,
                          int workersPerModel,
                          size_t queueDepth,
                          bool useSram,
                          bool enablePerfQuery,
                          float scoreThreshold) {
    if (models.empty() || !workerThreads_.empty() || collectorThread_.joinable()) return -1;
    workersPerModel = std::clamp(workersPerModel, 1, 3);
    queueDepth = std::clamp<size_t>(queueDepth, 1, 16);
    stop_.store(false, std::memory_order_release);
    workersDone_.store(false, std::memory_order_release);
    completedTasks_.store(0, std::memory_order_relaxed);
    droppedTasks_.store(0, std::memory_order_relaxed);
    models_.clear();
    models_.reserve(models.size());
    maxResults_ = std::max<size_t>(128, models.size() * workersPerModel * queueDepth * 8);

    for (const ModelSpec& spec : models) {
        auto runtime = std::make_unique<ModelRuntime>();
        runtime->businessModelId = spec.businessModelId;
        runtime->lanes.reserve(static_cast<size_t>(workersPerModel));
        for (int core = 0; core < workersPerModel; ++core) {
            auto lane = std::make_unique<WorkerLane>();
            lane->engine = std::make_shared<YoloEngine>();
            const int ret = lane->engine->LoadModel(
                spec.modelPath, spec.classes, core, useSram, enablePerfQuery);
            if (ret != 0) {
                LOG(ERROR) << "[RKNN] 模型组初始化失败 key=" << spec.key
                           << " core=" << core << " ret=" << ret;
                models_.clear();
                return ret;
            }
            lane->engine->setScoreThreshold(scoreThreshold);
            lane->taskRing = std::make_unique<runtime::SpscRing<Task>>(queueDepth);
            lane->completionRing =
                std::make_unique<runtime::SpscRing<Completion>>(std::max<size_t>(8, queueDepth * 2));
            runtime->lanes.push_back(std::move(lane));
        }
        models_.push_back(std::move(runtime));
    }

    collectorThread_ = std::thread(&YoloThreadPool::collectCompletions, this);
    for (size_t model = 0; model < models_.size(); ++model) {
        for (size_t lane = 0; lane < models_[model]->lanes.size(); ++lane) {
            workerThreads_.emplace_back(&YoloThreadPool::worker, this, model, lane);
        }
    }
    LOG(INFO) << "[RKNN] 多环形队列推理池就绪 models=" << models_.size()
              << " npu_lanes_per_model=" << workersPerModel
              << " ring_depth_per_lane=" << queueDepth
              << " result_window=" << maxResults_;
    return 0;
}

std::string YoloThreadPool::inferEp() const {
    if (models_.empty() || models_[0]->lanes.empty()) return "none";
    return "rknn-rk3588-3core-ring";
}

std::string YoloThreadPool::modelLayout() const {
    if (models_.empty() || models_[0]->lanes.empty()) return "unknown";
    return models_[0]->lanes[0]->engine->modelLayout();
}

void YoloThreadPool::storeResult(int modelId, int inputId, int frameId,
                                 std::vector<DetectObject> detections) {
    std::lock_guard<std::mutex> lock(resultsMutex_);
    resultOrder_.erase(
        std::remove_if(resultOrder_.begin(), resultOrder_.end(), [&](const ResultKey& key) {
            return key.modelId == modelId && key.inputId == inputId && key.frameId == frameId;
        }),
        resultOrder_.end());
    results_[modelId][inputId][frameId] = std::move(detections);
    resultOrder_.push_back({modelId, inputId, frameId});
    while (resultOrder_.size() > maxResults_) {
        const ResultKey oldest = resultOrder_.front();
        resultOrder_.pop_front();
        auto model = results_.find(oldest.modelId);
        if (model == results_.end()) continue;
        auto input = model->second.find(oldest.inputId);
        if (input == model->second.end()) continue;
        input->second.erase(oldest.frameId);
        if (input->second.empty()) model->second.erase(input);
        if (model->second.empty()) results_.erase(model);
    }
}

void YoloThreadPool::publishDropped(const Task& task) {
    storeResult(task.modelId, task.inputId, task.frameId, {});
    droppedTasks_.fetch_add(1, std::memory_order_relaxed);
    resultReady_.notify_all();
}

void YoloThreadPool::publishCompletion(Completion completion) {
    lastNpuDurationUs_.store(completion.npuDurationUs, std::memory_order_relaxed);
    storeResult(completion.modelId, completion.inputId, completion.frameId,
                std::move(completion.detections));
    completedTasks_.fetch_add(1, std::memory_order_relaxed);
    resultReady_.notify_all();
}

int YoloThreadPool::submit(Task task) {
    if (stop_.load(std::memory_order_acquire) || task.modelId < 0 ||
        task.modelId >= static_cast<int>(models_.size()) || !task.frame.valid()) {
        return -1;
    }
    ModelRuntime& runtime = *models_[static_cast<size_t>(task.modelId)];
    if (runtime.lanes.empty()) return -1;

    const size_t start = runtime.nextLane.fetch_add(1, std::memory_order_relaxed);
    size_t selected = start % runtime.lanes.size();
    size_t smallest = std::numeric_limits<size_t>::max();
    for (size_t offset = 0; offset < runtime.lanes.size(); ++offset) {
        const size_t candidate = (start + offset) % runtime.lanes.size();
        const size_t queued = runtime.lanes[candidate]->taskRing->sizeApprox();
        if (queued < smallest) {
            smallest = queued;
            selected = candidate;
            if (queued == 0) break;
        }
    }

    Task displaced;
    bool dropped = false;
    runtime.lanes[selected]->taskRing->pushDropOldest(std::move(task), displaced, &dropped);
    if (dropped) publishDropped(displaced);
    return 0;
}

int YoloThreadPool::submitTask(const cv::Mat& img, int modelId, int inputId, int frameId) {
    if (img.empty()) return -1;
    Task task;
    task.modelId = modelId;
    task.inputId = inputId;
    task.frameId = frameId;
    task.ownedImage = img.clone();
    task.frame.virtualAddress = task.ownedImage.data;
    task.frame.width = task.ownedImage.cols;
    task.frame.height = task.ownedImage.rows;
    task.frame.widthStride = static_cast<int>(task.ownedImage.step[0] / task.ownedImage.elemSize());
    task.frame.heightStride = task.ownedImage.rows;
    task.frame.format = runtime::rk3588::FrameFormat::BGR888;
    return submit(std::move(task));
}

int YoloThreadPool::submitTask(const runtime::rk3588::FrameView& frame,
                               int modelId, int inputId, int frameId) {
    Task task;
    task.modelId = modelId;
    task.inputId = inputId;
    task.frameId = frameId;
    task.frame = frame;
    return submit(std::move(task));
}

void YoloThreadPool::worker(size_t modelIndex, size_t laneIndex) {
    pinCurrentThread(4 + static_cast<int>(laneIndex),
                     "rknn-npu" + std::to_string(laneIndex));
    ModelRuntime& runtime = *models_[modelIndex];
    WorkerLane& lane = *runtime.lanes[laneIndex];
    while (!stop_.load(std::memory_order_acquire) || lane.taskRing->sizeApprox() > 0) {
        Task task;
        if (!lane.taskRing->pop(task)) {
            std::this_thread::sleep_for(std::chrono::microseconds(50));
            continue;
        }

        Completion completion;
        completion.modelId = task.modelId;
        completion.inputId = task.inputId;
        completion.frameId = task.frameId;
        const int ret = lane.engine->Run(task.frame, completion.detections);
        if (ret != 0) {
            LOG(ERROR) << "[RKNN] 推理失败 model=" << modelIndex
                       << " npu_lane=" << laneIndex << " ret=" << ret;
            completion.detections.clear();
        }
        for (auto& detection : completion.detections) {
            detection.model_id = runtime.businessModelId;
        }
        completion.npuDurationUs = lane.engine->lastNpuDurationUs();

        Completion displaced;
        bool dropped = false;
        lane.completionRing->pushDropOldest(std::move(completion), displaced, &dropped);
        if (dropped) {
            storeResult(displaced.modelId, displaced.inputId, displaced.frameId, {});
            droppedTasks_.fetch_add(1, std::memory_order_relaxed);
            resultReady_.notify_all();
        }
    }
}

bool YoloThreadPool::completionRingsEmpty() const {
    for (const auto& model : models_) {
        for (const auto& lane : model->lanes) {
            if (lane->completionRing->sizeApprox() != 0) return false;
        }
    }
    return true;
}

void YoloThreadPool::collectCompletions() {
    pinCurrentThread(7, "rknn-collector");
    auto windowStart = std::chrono::steady_clock::now();
    uint64_t windowCompleted = 0;
    while (!workersDone_.load(std::memory_order_acquire) || !completionRingsEmpty()) {
        bool found = false;
        for (auto& model : models_) {
            for (auto& lane : model->lanes) {
                Completion completion;
                while (lane->completionRing->pop(completion)) {
                    found = true;
                    ++windowCompleted;
                    publishCompletion(std::move(completion));
                }
            }
        }

        const auto now = std::chrono::steady_clock::now();
        const double elapsed = std::chrono::duration<double>(now - windowStart).count();
        if (elapsed >= 1.0) {
            throughputFps_.store(static_cast<double>(windowCompleted) / elapsed,
                                 std::memory_order_relaxed);
            windowStart = now;
            windowCompleted = 0;
        }
        if (!found) std::this_thread::sleep_for(std::chrono::microseconds(100));
    }
    throughputFps_.store(0.0, std::memory_order_relaxed);
}

bool YoloThreadPool::takeResult(std::vector<DetectObject>& objects,
                                int modelId, int inputId, int frameId) {
    auto model = results_.find(modelId);
    if (model == results_.end()) return false;
    auto input = model->second.find(inputId);
    if (input == model->second.end()) return false;
    auto frame = input->second.find(frameId);
    if (frame == input->second.end()) return false;
    objects = std::move(frame->second);
    input->second.erase(frame);
    resultOrder_.erase(
        std::remove_if(resultOrder_.begin(), resultOrder_.end(), [&](const ResultKey& key) {
            return key.modelId == modelId && key.inputId == inputId && key.frameId == frameId;
        }),
        resultOrder_.end());
    if (input->second.empty()) model->second.erase(input);
    if (model->second.empty()) results_.erase(model);
    return true;
}

int YoloThreadPool::getTargetResult(std::vector<DetectObject>& objects,
                                    int modelId, int inputId, int frameId) {
    std::unique_lock<std::mutex> lock(resultsMutex_);
    const bool ready = resultReady_.wait_for(lock, std::chrono::seconds(10), [&] {
        auto model = results_.find(modelId);
        if (model == results_.end()) return stop_.load(std::memory_order_acquire);
        auto input = model->second.find(inputId);
        return (input != model->second.end() && input->second.count(frameId) != 0) ||
               stop_.load(std::memory_order_acquire);
    });
    if (!ready) return -1;
    return takeResult(objects, modelId, inputId, frameId) ? 0 : -1;
}

int YoloThreadPool::getTargetResultNonBlock(std::vector<DetectObject>& objects,
                                            int modelId, int inputId, int frameId) {
    std::lock_guard<std::mutex> lock(resultsMutex_);
    return takeResult(objects, modelId, inputId, frameId) ? 0 : -1;
}

int YoloThreadPool::getTargetImgResult(cv::Mat& img,
                                       int modelId, int inputId, int frameId) {
    img.release();
    std::vector<DetectObject> ignored;
    return getTargetResult(ignored, modelId, inputId, frameId);
}

void YoloThreadPool::stopAll() {
    if (stop_.exchange(true, std::memory_order_acq_rel)) return;
    resultReady_.notify_all();
}
