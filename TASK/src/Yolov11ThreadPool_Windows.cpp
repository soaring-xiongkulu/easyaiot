#include "Yolov11ThreadPool.h"
#include "Draw.h"
#include <glog/logging.h>
// Windows compatible: Linux-specific headers removed
// #include <unistd.h>
// #include <sys/stat.h>
// #include <sys/types.h>
// #include <dirent.h>
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
    LOG(INFO) << "[YOLO] Creating " << num_threads << " YOLO engine instances...";
    
    for (size_t i = 0; i < num_threads; ++i) {
        LOG(INFO) << "[YOLO] Loading model instance " << (i+1) << "/" << num_threads << "...";
        std::shared_ptr<Yolov11Engine> Yolov11 = std::make_shared<Yolov11Engine>();
        
        int ret = Yolov11->LoadModel(model_path, model_class);
        if (ret != 0) {
            LOG(ERROR) << "[YOLO] Failed to load model for instance " << (i+1) << ", error: " << ret;
            return -1;
        }
        
        Yolov11_instances.push_back(Yolov11);
        LOG(INFO) << "[YOLO] Instance " << (i+1) << " loaded successfully";
    }
    
    LOG(INFO) << "[YOLO] Starting worker threads...";
    for (size_t i = 0; i < num_threads; ++i) {
        threads.emplace_back(&Yolov11ThreadPool::worker, this, i);
    }
    
    LOG(INFO) << "[YOLO] Thread pool setup completed";
    return 0;
}

void Yolov11ThreadPool::worker(int id) {
    while (!stop) {
        std::tuple<int, int, cv::Mat> task;
        std::shared_ptr<Yolov11Engine> instance = Yolov11_instances[id]; // Get model instance
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
            int input_id = std::get<0>(task); // Get input_id
            int frame_id = std::get<1>(task);
            cv::Mat img = std::get<2>(task); // Get image
            
            // Clean up old results to prevent memory leak (keep only last 50 frames)
            if (results.find(input_id) != results.end()) {
                auto& frameMap = results[input_id];
                if (frameMap.size() > 50) {
                    // Find and remove oldest frames
                    int minFrame = frame_id - 50;
                    for (auto it = frameMap.begin(); it != frameMap.end(); ) {
                        if (it->first < minFrame) {
                            it = frameMap.erase(it);
                        } else {
                            ++it;
                        }
                    }
                }
            }
            
            results[input_id][frame_id] = detections; // Save detection results
            
            // Also clean up img_results
            if (img_results.find(input_id) != img_results.end()) {
                auto& imgMap = img_results[input_id];
                if (imgMap.size() > 50) {
                    int minFrame = frame_id - 50;
                    for (auto it = imgMap.begin(); it != imgMap.end(); ) {
                        if (it->first < minFrame) {
                            it = imgMap.erase(it);
                        } else {
                            ++it;
                        }
                    }
                }
            }
        }
    }
}

int Yolov11ThreadPool::submitTask(const cv::Mat &img, int input_id, int frame_id) {
    // If task queue has more than 10 items, wait to avoid excessive memory usage
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
    // Wait if no results available
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
    // Wait if no results available
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
    // Remove from map
    results[input_id].erase(frame_id);
    img_results[input_id].erase(frame_id);

    return 0;
}

// Stop all threads
void Yolov11ThreadPool::stopAll() {
    stop = true;
    cv_task.notify_all();
}
