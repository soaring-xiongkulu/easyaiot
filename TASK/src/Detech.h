//
// Created by basiclab on 25-10-15.
//
#include "config.h"
#include <glog/logging.h>
#include <httplib.h>

#ifndef DETECH_H
#define DETECH_H
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
        httplib::Client *_httpClient;
};
#endif //DETECH_H
