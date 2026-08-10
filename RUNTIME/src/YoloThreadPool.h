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
private:
    std::queue<std::tuple<int, int, cv::Mat>> tasks;
    std::vector<std::shared_ptr<YoloEngine>> engines_;
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
    std::map<int, std::map<int, std::vector<DetectObject>>> results;

    int setUp(std::string model_path,
              std::vector<std::string> model_class,
              int num_threads = 3,
              bool prefer_gpu = true,
              bool force_cpu = false,
              int gpu_device_id = 0,
              float score_threshold = 0.25f);
    int submitTask(const cv::Mat& img, int input_id, int frame_id);
    int getTargetResult(std::vector<DetectObject>& objects, int input_id, int frame_id);
    int getTargetImgResult(cv::Mat& img, int input_id, int frame_id);
    int getTargetResultNonBlock(std::vector<DetectObject>& objects, int input_id, int frame_id);
    void stopAll();
    std::string inferEp() const;
    std::string modelLayout() const;
};

#endif
