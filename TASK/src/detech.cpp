//
// Created by basiclab on 25-10-15.
//

#include "detech.h"
#include "yolov11_thread_pool.h"

static Yolov11ThreadPool *yolov11_thread_pool = nullptr; // yolo线程池

Detech::Detech(Config &config): _config(config) {
    LOG(INFO) << "【Detech】已完成配置初始化";
}

Detech::~Detech() {
}

int Detech::start() {

    if (!yolov11_thread_pool) {
        yolov11_thread_pool = new Yolov11ThreadPool(); // 创建线程池
        int ret = yolov11_thread_pool->setUp(_config.modelClass, 12);
        if (ret) {
            LOG(ERROR) << "yolov11_thread_pool初始化失败";
            return -3;
        }
    }


    return 0;
}

int Detech::stop() {
    return 0;
}
