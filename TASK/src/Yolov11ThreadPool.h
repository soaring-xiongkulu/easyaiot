// @author 翱翔的雄库鲁
// @email andywebjava@163.com
// @wechat EasyAIoT2025

#ifndef Yolov11_THREAD_POOL_H
#define Yolov11_THREAD_POOL_H

#include "Yolov11Engine.h"

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
    std::vector<std::shared_ptr<Yolov11Engine>> Yolov11_instances;
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
    std::map<int, std::map<int, std::vector<DetectObject>>> results;

    int setUp(std::string model_path, std::vector<std::string> model_class, int num_threads = 3);
    int submitTask(const cv::Mat &img, int input_id, int frame_id);
    int getTargetResult(std::vector<DetectObject> &objects, int input_id, int frame_id);
    int getTargetImgResult(cv::Mat &img, int input_id, int frame_id);
    int getTargetResultNonBlock(std::vector<DetectObject> &objects, int input_id, int frame_id);
    void stopAll();
};

#endif // Yolov8_THREAD_POOL_H
