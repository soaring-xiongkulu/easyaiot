#include "YoloThreadPool.h"

#include <chrono>
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

int YoloThreadPool::setUp(std::string model_path,
                          std::vector<std::string> model_class,
                          int num_threads,
                          bool prefer_gpu,
                          bool force_cpu,
                          int gpu_device_id,
                          float score_threshold) {
    for (int i = 0; i < num_threads; ++i) {
        auto engine = std::make_shared<YoloEngine>();
        int ret = engine->LoadModel(model_path, model_class, prefer_gpu, force_cpu, gpu_device_id);
        if (ret != 0) {
            return ret;
        }
        engine->setScoreThreshold(score_threshold);
        engines_.push_back(engine);
    }
    for (int i = 0; i < num_threads; ++i) {
        threads.emplace_back(&YoloThreadPool::worker, this, i);
    }
    return 0;
}

std::string YoloThreadPool::inferEp() const {
    if (engines_.empty() || !engines_[0]) {
        return "none";
    }
    return engines_[0]->inferEp();
}

std::string YoloThreadPool::modelLayout() const {
    if (engines_.empty() || !engines_[0]) {
        return "unknown";
    }
    return engines_[0]->modelLayout();
}

void YoloThreadPool::worker(int id) {
    while (!stop) {
        std::tuple<int, int, cv::Mat> task;
        std::shared_ptr<YoloEngine> instance = engines_[static_cast<size_t>(id)];
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
        instance->Run(std::get<2>(task), detections);
        {
            std::lock_guard<std::mutex> lock(mtx2);
            const int input_id = std::get<0>(task);
            const int frame_id = std::get<1>(task);
            results[input_id][frame_id] = detections;
        }
    }
}

int YoloThreadPool::submitTask(const cv::Mat& img, int input_id, int frame_id) {
    while (tasks.size() > 10) {
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    {
        std::lock_guard<std::mutex> lock(mtx1);
        tasks.push({input_id, frame_id, img});
    }
    cv_task.notify_one();
    return 0;
}

int YoloThreadPool::getTargetResult(std::vector<DetectObject>& objects, int input_id, int frame_id) {
    while (results.find(input_id) == results.end() ||
           results[input_id].find(frame_id) == results[input_id].end()) {
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    std::lock_guard<std::mutex> lock(mtx2);
    objects = results[input_id][frame_id];
    results[input_id].erase(frame_id);
    img_results[input_id].erase(frame_id);
    return 0;
}

int YoloThreadPool::getTargetImgResult(cv::Mat& img, int input_id, int frame_id) {
    int loop_cnt = 0;
    while (img_results.find(input_id) == img_results.end() ||
           img_results[input_id].find(frame_id) == img_results[input_id].end()) {
        std::this_thread::sleep_for(std::chrono::milliseconds(5));
        loop_cnt++;
        if (loop_cnt > 1000) {
            return -1;
        }
    }
    std::lock_guard<std::mutex> lock(mtx2);
    img = img_results[input_id][frame_id];
    img_results[input_id].erase(frame_id);
    results[input_id].erase(frame_id);
    return 0;
}

int YoloThreadPool::getTargetResultNonBlock(std::vector<DetectObject>& objects, int input_id, int frame_id) {
    if (results.find(input_id) == results.end() ||
        results[input_id].find(frame_id) == results[input_id].end()) {
        return -1;
    }
    std::lock_guard<std::mutex> lock(mtx2);
    objects = results[input_id][frame_id];
    results[input_id].erase(frame_id);
    img_results[input_id].erase(frame_id);
    return 0;
}

void YoloThreadPool::stopAll() {
    stop = true;
    cv_task.notify_all();
}
