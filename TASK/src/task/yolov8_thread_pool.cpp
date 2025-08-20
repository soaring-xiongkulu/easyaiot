
#include "yolov8_thread_pool.h"
#include "draw/cv_draw.h"

Yolov8ThreadPool::Yolov8ThreadPool() { stop = false; }

Yolov8ThreadPool::~Yolov8ThreadPool()
{
    // stop all threads
    stop = true;
    cv_task.notify_all();
    for (auto &thread : threads)
    {
        if (thread.joinable())
        {
            thread.join();
        }
    }
}

int Yolov8ThreadPool::setUp(std::string &model_path, int num_threads)
{
    for (size_t i = 0; i < num_threads; ++i)
    {
        std::shared_ptr<Yolov8Engine> Yolov8 = std::make_shared<Yolov8Engine>();
        Yolov8->LoadModel(model_path.c_str());
        Yolov8_instances.push_back(Yolov8);
    }
    for (size_t i = 0; i < num_threads; ++i)
    {
        threads.emplace_back(&Yolov8ThreadPool::worker, this, i);
    }
    return 0;
}

void Yolov8ThreadPool::worker(int id)
{
    while (!stop)
    {
        std::tuple<int, int, cv::Mat> task;
        std::shared_ptr<Yolov8Engine> instance = Yolov8_instances[id]; // 获取模型实例
        {
            std::unique_lock<std::mutex> lock(mtx1);
            cv_task.wait(lock, [&]
                         { return !tasks.empty() || stop; });

            if (stop)
            {
                return;
            }

            task = tasks.front();
            tasks.pop();
        }

        std::vector<Detection> detections;
        instance->Run(std::get<2>(task), detections);
        {
            
            std::lock_guard<std::mutex> lock(mtx2);
            int input_id = std::get<0>(task);                               // 获取 input_id
            int frame_id = std::get<1>(task);                               // 获取 frame_id
            results[input_id][frame_id] = detections;                       // 保存检测结果
            DrawDetections(std::get<2>(task), detections);                  // 绘制检测框
            // std::string dir_path = "./output_images/" + std::to_string(input_id) + "/";
            // std::string file_path = dir_path + "result_" + std::to_string(frame_id) + ".jpg";
            // cv::imwrite(file_path, std::get<2>(task));
            // img_results[input_id][frame_id] = std::get<2>(task);               
        }

    }
}
int Yolov8ThreadPool::submitTask(const cv::Mat &img, int input_id, int frame_id)
{
    // 如果任务队列中的任务数量大于10，等待，避免内存占用过多
    while (tasks.size() > 25)
    {
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }

    {
        std::lock_guard<std::mutex> lock(mtx1);
        tasks.push({input_id, frame_id, img});
    }
    cv_task.notify_one();
    return 0;
}

int Yolov8ThreadPool::getTargetResult(std::vector<Detection> &objects, int input_id, int frame_id)
{
    // 如果没有结果，等待
    while (results.find(input_id) == results.end() || results[input_id].find(frame_id) == results[input_id].end())
    {
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    std::lock_guard<std::mutex> lock(mtx2);
    objects = results[input_id][frame_id];
    results[input_id].erase(frame_id);
    img_results[input_id].erase(frame_id);

    return 0;
}

int Yolov8ThreadPool::getTargetImgResult(cv::Mat &img, int input_id, int frame_id)
{
    int loop_cnt = 0;
    // 如果没有结果，等待
    while (img_results.find(input_id) == img_results.end() || img_results[input_id].find(frame_id) == img_results[input_id].end())
    {
        std::this_thread::sleep_for(std::chrono::milliseconds(5));
        loop_cnt++;
        if (loop_cnt > 1000)
        {
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



int Yolov8ThreadPool::getTargetResultNonBlock(std::vector<Detection> &objects, int input_id, int frame_id)
{
    if (results.find(input_id) == results.end() || results[input_id].find(frame_id) == results[input_id].end())
    {
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
void Yolov8ThreadPool::stopAll()
{
    stop = true;
    cv_task.notify_all();
}