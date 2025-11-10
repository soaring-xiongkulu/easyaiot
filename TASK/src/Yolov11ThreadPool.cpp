// @author 翱翔的雄库鲁
// @email andywebjava@163.com
// @wechat EasyAIoT2025

#include "Yolov11ThreadPool.h"
#include "Draw.h"
#include <unistd.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <dirent.h>
#include <Yolov11Engine.h>

Yolov11ThreadPool::Yolov11ThreadPool() { stop = false; }

Yolov11ThreadPool::~Yolov11ThreadPool() {
    stopAll();
    for (auto &thread: threads) {
        if (thread.joinable()) {
            thread.join();
        }
    }
}

int Yolov11ThreadPool::setUp(std::string model_path, std::vector<std::string> model_class, int num_threads) {
    for (size_t i = 0; i < num_threads; ++i) {
        std::shared_ptr<Yolov11Engine> Yolov11 = std::make_shared<Yolov11Engine>();
        Yolov11->LoadModel(model_path, model_class);
        Yolov11_instances.push_back(Yolov11);
    }
    for (size_t i = 0; i < num_threads; ++i) {
        threads.emplace_back(&Yolov11ThreadPool::worker, this, i);
    }
    return 0;
}

void Yolov11ThreadPool::worker(int id) {
    while (!stop) {
        std::tuple<int, int, cv::Mat> task;
        std::shared_ptr<Yolov11Engine> instance = Yolov11_instances[id]; // 获取模型实例
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
            int input_id = std::get<0>(task); // 获取 input_id
            int frame_id = std::get<1>(task);
            cv::Mat img = std::get<2>(task); // 获取 frame_id
            results[input_id][frame_id] = detections; // 保存检测结果
            // DrawDetections(img, detections); // 绘制检测框
            // std::string dir_path = "/projects/dvm-edge/output_images/" + std::to_string(input_id) + "/";
            // std::string file_path = dir_path + "result_" + std::to_string(frame_id) + ".jpg";
            // if (access(dir_path.data(), 0) == -1) { // 检查目录是否存在，如果不存在，则创建它
                // mkdir(dir_path.data(), 0777);
            // }
            // cv::imwrite(file_path, img);
        }
    }
}

int Yolov11ThreadPool::submitTask(const cv::Mat &img, int input_id, int frame_id) {
    // 如果任务队列中的任务数量大于10，等待，避免内存占用过多
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

int Yolov11ThreadPool::getTargetResult(std::vector<DetectObject> &objects, int input_id, int frame_id) {
    // 如果没有结果，等待
    while (results.find(input_id) == results.end() || results[input_id].find(frame_id) == results[input_id].end()) {
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    std::lock_guard<std::mutex> lock(mtx2);
    objects = results[input_id][frame_id];
    results[input_id].erase(frame_id);
    img_results[input_id].erase(frame_id);

    return 0;
}

int Yolov11ThreadPool::getTargetImgResult(cv::Mat &img, int input_id, int frame_id) {
    int loop_cnt = 0;
    // 如果没有结果，等待
    while (img_results.find(input_id) == img_results.end() || img_results[input_id].find(frame_id) == img_results[
               input_id].end()) {
        std::this_thread::sleep_for(std::chrono::milliseconds(5));
        loop_cnt++;
        if (loop_cnt > 1000) {
            printf("getTargetImgResult timeout\n");
            return -1;
        }
    }
    std::lock_guard<std::mutex> lock(mtx2);
    img = img_results[input_id][frame_id];
    img_results[input_id].erase(frame_id);
    results[input_id].erase(frame_id);

    return 0;
}


int Yolov11ThreadPool::getTargetResultNonBlock(std::vector<DetectObject> &objects, int input_id, int frame_id) {
    if (results.find(input_id) == results.end() || results[input_id].find(frame_id) == results[input_id].end()) {
        return -1;
    }
    std::lock_guard<std::mutex> lock(mtx2);
    objects = results[input_id][frame_id];
    // 从 map 中移除
    results[input_id].erase(frame_id);
    img_results[input_id].erase(frame_id);

    return 0;
}

// 停止所有线程
void Yolov11ThreadPool::stopAll() {
    stop = true;
    cv_task.notify_all();
}
