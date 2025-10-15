
#ifndef RK3588_DEMO_Yolov8_THREAD_POOL_H
#define RK3588_DEMO_Yolov8_THREAD_POOL_H

#include "yolov11_engine.h"

#include <iostream>
#include <vector>
#include <queue>
#include <map>
#include <thread>
#include <mutex>
#include <condition_variable>

class Yolov11ThreadPool
{
private:
    std::queue<std::tuple<int, int, cv::Mat>> tasks;
    std::vector<std::shared_ptr<Yolov11Engine>> Yolov8_instances;
    std::map<int, std::map<int, cv::Mat>> img_results;
    std::vector<std::thread> threads;
    std::mutex mtx1;
    std::mutex mtx2;
    std::condition_variable cv_task;

    bool stop;
    void worker(int id);

public:
    Yolov11ThreadPool();
    ~Yolov11ThreadPool();
    std::map<int, std::map<int, std::vector<Detection>>> results;

    int setUp(const char *model_path, int num_threads = 12);
    int submitTask(const cv::Mat &img, int input_id, int frame_id);
    int getTargetResult(std::vector<Detection> &objects, int input_id, int frame_id);
    int getTargetImgResult(cv::Mat &img, int input_id, int frame_id);
    int getTargetResultNonBlock(std::vector<Detection> &objects, int input_id, int frame_id);
    void stopAll();
};

#endif // RK3588_DEMO_Yolov8_THREAD_POOL_H
