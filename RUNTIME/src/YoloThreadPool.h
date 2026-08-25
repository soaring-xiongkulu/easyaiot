#ifndef YOLO_THREAD_POOL_H
#define YOLO_THREAD_POOL_H

#include "YoloEngine.h"

#include <condition_variable>
#include <map>
#include <memory>
#include <mutex>
#include <queue>
#include <string>
#include <thread>
#include <vector>

class YoloThreadPool {
public:
    /** 单个模型规格；key 为 ini 中的模型键（如 "default" 或模型 ID） */
    struct ModelSpec {
        std::string key;
        std::string modelPath;
        std::vector<std::string> classes;
    };

private:
    /** 任务：(model_id, input_id, frame_id, img) */
    std::queue<std::tuple<int, int, int, cv::Mat>> tasks;
    /** 每个模型一组引擎：groups_[model_id][engine_idx] */
    std::vector<std::vector<std::shared_ptr<YoloEngine>>> groups_;
    int threadsPerModel_{0};
    /** 结果：results_[model_id][input_id][frame_id] */
    std::map<int, std::map<int, std::map<int, std::vector<DetectObject>>>> results;
    std::map<int, std::map<int, cv::Mat>> img_results;
    std::vector<std::thread> threads;
    std::mutex mtx1;
    std::mutex mtx2;
    std::condition_variable cv_task;
    bool stop{false};
    void worker(int id);

public:
    YoloThreadPool();
    ~YoloThreadPool();

    int setUp(const std::vector<ModelSpec>& models,
              int num_threads = 3,
              bool prefer_gpu = true,
              bool force_cpu = false,
              int gpu_device_id = 0,
              float score_threshold = 0.25f);
    size_t modelCount() const { return groups_.size(); }
    int submitTask(const cv::Mat& img, int model_id, int input_id, int frame_id);
    int getTargetResult(std::vector<DetectObject>& objects, int model_id, int input_id, int frame_id);
    int getTargetImgResult(cv::Mat& img, int model_id, int input_id, int frame_id);
    int getTargetResultNonBlock(std::vector<DetectObject>& objects, int model_id, int input_id, int frame_id);
    void stopAll();
    std::string inferEp() const;
    std::string modelLayout() const;
};

#endif
