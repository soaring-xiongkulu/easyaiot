//
// Created by basiclab on 25-10-15.
//
#include "Detech.h"
#include "Yolov11ThreadPool.h"

static Yolov11ThreadPool *yolov11_thread_pool = nullptr;

Detech::Detech(Config &config): _config(config) {
    LOG(INFO) << "已完成配置初始化";
}

Detech::~Detech() {
}

int Detech::start() {
    _isRun = true;
    _init_yolo11_detector();
    _init_yolo11_detector();
    _init_alarm_regions();
    _init_media_player();
    _init_media_alarmer();
    _init_media_pusher();
    return 0;
}

int Detech::stop() {
    return 0;
}

bool Detech::_init_http_client() {
    if (!_httpClient) {
        _httpClient = new httplib::Client(_config.hookHttpUrl);
    }
}

bool Detech::_init_yolo11_detector() {
    if (!yolov11_thread_pool) {
        yolov11_thread_pool = new Yolov11ThreadPool();
        int ret = yolov11_thread_pool->setUp(_config.modelPaths, _config.modelClasses, _config.regions, _config.threadNums);
        if (ret) {
            LOG(ERROR) << "yolov11_thread_pool初始化失败";
            return -3;
        }
    }
}

bool Detech::_init_media_player() {
    LOG(INFO) << "初始化拉流播放器";
    if (!_ffmpegFormatCtx) {
        _ffmpegFormatCtx = avformat_alloc_context();
    }
    AVDictionary* fmt_options = NULL;
    av_dict_set(&fmt_options, "rtsp_transport", "tcp", 0);
    av_dict_set(&fmt_options, "stimeout", "3000000", 0);
    av_dict_set(&fmt_options, "timeout", "5000000", 0);
    int ret = avformat_open_input(&_ffmpegFormatCtx, _config.rtspUrl.c_str(), NULL, &fmt_options);
    if (ret != 0) {
        LOG(ERROR) << "avformat_open_input error: url=" << _config.rtspUrl.c_str();
        return false;
    }

    if (avformat_find_stream_info(_ffmpegFormatCtx, NULL) < 0)
    {
        LOG(ERROR) << "avformat_find_stream_info error";
        return false;
    }
    _videoIndex = av_find_best_stream(_ffmpegFormatCtx, AVMEDIA_TYPE_VIDEO, -1, -1, nullptr, 0);
    if (_videoIndex > -1) {
        AVCodecParameters* videoCodecPar = _ffmpegFormatCtx->streams[_videoIndex]->codecpar;
        const AVCodec* videoCodec = NULL;
        if (!videoCodec) {
            videoCodec = avcodec_find_decoder(videoCodecPar->codec_id);
            if (!videoCodec) {
                LOG(ERROR) << "avcodec_find_decoder error";
                return false;
            }
        }
        _ffmpegCodecCtx = avcodec_alloc_context3(videoCodec);
        if (avcodec_parameters_to_context(_ffmpegCodecCtx, videoCodecPar) != 0) {
            LOG(ERROR) << "avcodec_parameters_to_context error";
            return false;
        }
        if (avcodec_open2(_ffmpegCodecCtx, videoCodec, nullptr) < 0) {
            LOG(ERROR) << "avcodec_open2 error";
            return false;
        }
        _ffmpegStream = _ffmpegFormatCtx->streams[_videoIndex];
        if (0 == _ffmpegStream->avg_frame_rate.den) {
            LOG(ERROR) << "videoIndex=" << _videoIndex << ",videoStream->avg_frame_rate.den = 0";
            _videoFps = 25;
        }
        else {
            _videoFps = _ffmpegStream->avg_frame_rate.num / _ffmpegStream->avg_frame_rate.den;
        }
        _videoWidth = _ffmpegCodecCtx->width;
        _videoHeight = _ffmpegCodecCtx->height;
        _videoChannel = 3;
    }
}
