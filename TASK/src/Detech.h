#ifndef DETECH_H
#define DETECH_H

#include <iostream>
#include <glog/logging.h>
#include <httplib.h>
#include "Config.h"

extern "C" {
#include "libavcodec/avcodec.h"
#include "libavformat/avformat.h"
}

class Detech {
    public:
        Detech(Config &config);
        ~Detech();
        int start();
        int stop();
    private:
        bool _init_media_player();
        bool _init_media_pusher();
        bool _init_media_alarmer();
        bool _init_alarm_regions();
        bool _init_yolo11_model_resources();
        bool _init_yolo11_detector();
        bool _on_play_event();
        bool _on_push_event();
        bool _release_media();
        bool _release_pusher();
        bool _release_alarmer();
        uint64_t _get_curtime_stamp_ms();
        int _decode_frame_callback();
        int _decode_frame_yolo11_detech();
        int _decode_frame_alarm();
        int _encode_frame_callback();
        int _encode_frame_push_frame();
    private:
        Config &_config;
        bool _isRun{false};
        httplib::Client *_httpClient;
        AVFormatContext *_ffmpegFormatCtx{nullptr};
};
#endif //DETECH_H
