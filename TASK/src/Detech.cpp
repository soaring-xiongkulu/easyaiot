//
// Created by basiclab on 25-10-15.
//
#include "Detech.h"
#include "Yolov11ThreadPool.h"

static Yolov11ThreadPool *yolov11_thread_pool = nullptr; // yolo线程池

Detech::Detech(Config &config): _config(config) {
    LOG(INFO) << "【Detech】已完成配置初始化";
}

Detech::~Detech() {
}

int Detech::start() {
    if (!yolov11_thread_pool) {
        yolov11_thread_pool = new Yolov11ThreadPool();
        int ret = yolov11_thread_pool->setUp(_config.modelPaths, _config.modelClasses, _config.regions, _config.threadNums);
        if (ret) {
            LOG(ERROR) << "yolov11_thread_pool初始化失败";
            return -3;
        }
    }

    if (!_ffmpegFormatCtx) {
        _ffmpegFormatCtx = avformat_alloc_context();
        AVDictionary* fmt_options = NULL;
        av_dict_set(&fmt_options, "rtsp_transport", "tcp", 0);
        av_dict_set(&fmt_options, "stimeout", "5000000", 0);
        av_dict_set(&fmt_options, "max_delay", "500000", 0);
        av_dict_set(&fmt_options, "fflags", "+genpts", 0);
    }

    _httpClient = new httplib::Client(_config.hookHttpUrl);
    _isRun = true;
    _pdebugThread = new std::thread(&videoDetect::_pullstreamHandle, this);
    return 0;
}

int Detech::stop() {
    return 0;
}
