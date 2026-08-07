#ifndef DETECH_H
#define DETECH_H

#include <iostream>
#include <thread>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <atomic>
#include <memory>
#include <glog/logging.h>
#include <httplib.h>
#include <opencv2/opencv.hpp>
#include <json/json.h>
#include "Config.h"
#include "RTMPEncoder.h"
#include "Datatype.h"
#include "core/frame_pool.h"
#include "pipeline/Pipeline.h"

extern "C" {
#include "libavcodec/avcodec.h"
#include "libavformat/avformat.h"
#include "libswscale/swscale.h"
#include "libavutil/imgutils.h"
}

class Detech {
    public:
        Detech(Config &config);
        ~Detech();
        int start();
        int stop();

        bool startStreaming();
        bool stopStreaming();
        bool isStreaming() const;

        const runtime::PipelineMetrics& metrics() const { return _metrics; }

    private:
        bool _init_yolo11_detector();
        bool _init_http_client();
        bool _init_media_player();
        bool _init_media_pusher();
        bool _init_media_alarmer();
        bool _init_control_server();
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
        void _display_video_loop();
        void _run_pipeline_loop();

        bool _isInAlarmRegion(int centerX, int centerY);
        void _drawAlarmRegions(cv::Mat& image);

        void _sendAlarmCallback(const std::vector<DetectObject>& detections, const std::string& regionName);
        bool _checkAlarmCooldown();

        void _startAlarmSenderThread();
        void _stopAlarmSenderThread();
        void _alarmSenderThreadFunc();

        void _startControlServer();
        void _stopControlServer();
        void _controlServerThreadFunc();

        void _startHeartbeatThread();
        void _stopHeartbeatThread();
        void _heartbeatThreadFunc();

        struct AlarmData {
            std::vector<DetectObject> detections;
            std::string regionName;
            uint64_t timestamp;

            AlarmData() : timestamp(0) {}
            AlarmData(const std::vector<DetectObject>& dets, const std::string& region, uint64_t ts)
                : detections(dets), regionName(region), timestamp(ts) {}
        };

    private:
        Config &_config;
        bool _isRun{false};
        httplib::Client* _httpClient{nullptr};
        AVFormatContext* _ffmpegFormatCtx{nullptr};
        AVCodecContext* _ffmpegCodecCtx{nullptr};
        AVStream* _ffmpegStream{nullptr};
        int _videoIndex = -1;
        int _videoFps = 0;
        int _videoWidth = 0;
        int _videoHeight = 0;
        int _videoChannel = 0;

        RTMPEncoder* _rtmpEncoder{nullptr};

        uint64_t _lastAlarmTime{0};

        std::queue<AlarmData> _alarmQueue;
        std::mutex _alarmQueueMutex;
        std::condition_variable _alarmQueueCV;
        std::thread _alarmSenderThread;
        std::atomic<bool> _alarmThreadRunning{false};
        static const size_t MAX_ALARM_QUEUE_SIZE = 20;

        std::atomic<bool> _streamingEnabled{false};
        std::mutex _streamingMutex;

        std::thread _controlServerThread;
        std::atomic<bool> _controlServerRunning{false};
        int _controlPort{0};

        std::thread _heartbeatThread;
        std::atomic<bool> _heartbeatRunning{false};

        runtime::PipelineMetrics _metrics;
        std::unique_ptr<runtime::Pipeline> _pipeline;
};

#endif
