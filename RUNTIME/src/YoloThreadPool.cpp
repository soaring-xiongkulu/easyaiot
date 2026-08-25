#include "YoloThreadPool.h"

#include <chrono>
#include <glog/logging.h>
#include <thread>

YoloThreadPool::YoloThreadPool() { stop = false; }

YoloThreadPool::~YoloThreadPool() {
    stopAll();
    for (auto& thread : threads) {
        if (thread.joinable()) {
            thread.join();
        }
    }
}

int YoloThreadPool::setUp(const std::vector<ModelSpec>& models,
                          int num_threads,
                          bool prefer_gpu,
                          bool force_cpu,
                          int gpu_device_id,
                          float score_threshold) {
    if (models.empty()) {
        return -1;
    }
    if (num_threads <= 0) {
        num_threads = 2;
    }
    threadsPerModel_ = num_threads;
    groups_.clear();
    groups_.reserve(models.size());
    for (const auto& spec : models) {
        std::vector<std::shared_ptr<YoloEngine>> group;
        group.reserve(static_cast<size_t>(num_threads));
        for (int i = 0; i < num_threads; ++i) {
            auto engine = std::make_shared<YoloEngine>();
            int ret = engine->LoadModel(spec.modelPath, spec.classes, prefer_gpu, force_cpu, gpu_device_id);
            if (ret != 0) {
                return ret;
            }
            engine->setScoreThreshold(score_threshold);
            group.push_back(engine);
        }
        groups_.push_back(std::move(group));
    }
    for (int i = 0; i < static_cast<int>(groups_.size()) * num_threads; ++i) {
        threads.emplace_back(&YoloThreadPool::worker, this, i);
    }
    return 0;
}

std::string YoloThreadPool::inferEp() const {
    if (groups_.empty() || groups_[0].empty() || !groups_[0][0]) {
        return "none";
    }
    return groups_[0][0]->inferEp();
}

std::string YoloThreadPool::modelLayout() const {
    if (groups_.empty() || groups_[0].empty() || !groups_[0][0]) {
        return "unknown";
    }
    return groups_[0][0]->modelLayout();
}

void YoloThreadPool::worker(int id) {
    const int groupIdx = id / threadsPerModel_;
    const int engineIdx = id % threadsPerModel_;
    while (!stop) {
        std::tuple<int, int, int, cv::Mat> task;
        {
            std::unique_lock<std::mutex> lock(mtx1);
            cv_task.wait(lock, [&] { return !tasks.empty() || stop; });
            if (stop) {
                return;
            }
            task = tasks.front();
            tasks.pop();
        }

        std::vector<DetectObject> detections;
        std::shared_ptr<YoloEngine> instance;
        if (groupIdx >= 0 && groupIdx < static_cast<int>(groups_.size())
            && engineIdx >= 0 && engineIdx < static_cast<int>(groups_[static_cast<size_t>(groupIdx)].size())) {
            instance = groups_[static_cast<size_t>(groupIdx)][static_cast<size_t>(engineIdx)];
        }
        const int model_id = std::get<0>(task);
        if (instance) {
            try {
                instance->Run(std::get<3>(task), detections);
            } catch (const std::exception& e) {
                // 推理异常不得逃逸 worker 线程（进程退出瞬间 ORT 会话异常曾导致 std::terminate）
                LOG(ERROR) << "[YOLO] worker inference exception model=" << model_id
                           << ": " << e.what();
            }
        }
        // 标记检测来源模型，供多模型告警审计与模型_ids 上报
        for (auto& det : detections) {
            det.model_id = model_id;
        }
        {
            std::lock_guard<std::mutex> lock(mtx2);
            const int input_id = std::get<1>(task);
            const int frame_id = std::get<2>(task);
            results[model_id][input_id][frame_id] = detections;
        }
    }
}

int YoloThreadPool::submitTask(const cv::Mat& img, int model_id, int input_id, int frame_id) {
    while (tasks.size() > 10) {
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    {
        std::lock_guard<std::mutex> lock(mtx1);
        tasks.push({model_id, input_id, frame_id, img});
    }
    cv_task.notify_one();
    return 0;
}

int YoloThreadPool::getTargetResult(std::vector<DetectObject>& objects, int model_id, int input_id, int frame_id) {
    while (results.find(model_id) == results.end() ||
           results[model_id].find(input_id) == results[model_id].end() ||
           results[model_id][input_id].find(frame_id) == results[model_id][input_id].end()) {
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    std::lock_guard<std::mutex> lock(mtx2);
    objects = results[model_id][input_id][frame_id];
    results[model_id][input_id].erase(frame_id);
    img_results[input_id].erase(frame_id);
    return 0;
}

int YoloThreadPool::getTargetImgResult(cv::Mat& img, int model_id, int input_id, int frame_id) {
    int loop_cnt = 0;
    while (results.find(model_id) == results.end() ||
           results[model_id].find(input_id) == results[model_id].end() ||
           results[model_id][input_id].find(frame_id) == results[model_id][input_id].end()) {
        std::this_thread::sleep_for(std::chrono::milliseconds(5));
        loop_cnt++;
        if (loop_cnt > 1000) {
            return -1;
        }
    }
    std::lock_guard<std::mutex> lock(mtx2);
    img = img_results[input_id][frame_id];
    img_results[input_id].erase(frame_id);
    results[model_id][input_id].erase(frame_id);
    return 0;
}

int YoloThreadPool::getTargetResultNonBlock(std::vector<DetectObject>& objects, int model_id, int input_id, int frame_id) {
    if (results.find(model_id) == results.end() ||
        results[model_id].find(input_id) == results[model_id].end() ||
        results[model_id][input_id].find(frame_id) == results[model_id][input_id].end()) {
        return -1;
    }
    std::lock_guard<std::mutex> lock(mtx2);
    objects = results[model_id][input_id][frame_id];
    results[model_id][input_id].erase(frame_id);
    img_results[input_id].erase(frame_id);
    return 0;
}

void YoloThreadPool::stopAll() {
    stop = true;
    cv_task.notify_all();
}
