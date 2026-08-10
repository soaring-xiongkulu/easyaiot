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
#include "ffmpeg_hw.h"
#include "core/frame_pool.h"
#include "pipeline/Pipeline.h"
#include "pipeline/SnapScheduler.h"
#include "pipeline/PatrolScheduler.h"
#include "pipeline/StreamForwarder.h"

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
        bool _init_yolo_detector();
        bool _init_http_client();
        bool _init_media_player();
        bool _init_media_pusher();
        bool _init_media_alarmer();
        bool _init_control_server();
        uint64_t _get_curtime_stamp_ms();

        void _run_pipeline_loop();
        void _run_forward_loop();
        void _run_snap_loop();
        void _run_patrol_loop();
        void _display_video_loop();  // legacy; unused in headless production path

        bool _isInAlarmRegion(int centerX, int centerY, int frameW = 0, int frameH = 0);
        void _drawAlarmRegions(cv::Mat& image);

        void _sendAlarmCallback(const std::vector<DetectObject>& detections,
                                const std::string& regionName,
                                const cv::Mat& frame = cv::Mat(),
                                const std::string& deviceId = "",
                                const std::string& deviceName = "");
        bool _checkAlarmCooldown();
        std::string _saveAlertImage(const cv::Mat& frame);

        void _startAlarmSenderThread();
        void _stopAlarmSenderThread();
        void _alarmSenderThreadFunc();

        void _startControlServer();
        void _stopControlServer();
        void _controlServerThreadFunc();

        void _startHeartbeatThread();
        void _stopHeartbeatThread();
        void _heartbeatThreadFunc();

        std::string _normalizedTaskType() const;

        struct AlarmData {
            std::vector<DetectObject> detections;
            std::string regionName;
            std::string imagePath;
            std::string deviceId;
            std::string deviceName;
            uint64_t timestamp;

            AlarmData() : timestamp(0) {}
            AlarmData(const std::vector<DetectObject>& dets, const std::string& region, uint64_t ts,
                      const std::string& img = "", const std::string& did = "", const std::string& dname = "")
                : detections(dets), regionName(region), imagePath(img), deviceId(did), deviceName(dname), timestamp(ts) {}
        };

    private:
        Config &_config;
        bool _isRun{false};
        httplib::Client* _httpClient{nullptr};
        AVFormatContext* _ffmpegFormatCtx{nullptr};
        AVCodecContext* _ffmpegCodecCtx{nullptr};
        AVStream* _ffmpegStream{nullptr};
        runtime::HwDecodeState _hwDecodeState{};
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
        httplib::Server* _controlHttpServer{nullptr};

        std::thread _heartbeatThread;
        std::atomic<bool> _heartbeatRunning{false};

        runtime::PipelineMetrics _metrics;
        std::unique_ptr<runtime::Pipeline> _pipeline;
        std::unique_ptr<runtime::StreamForwarder> _streamForwarder;
        std::unique_ptr<runtime::SnapScheduler> _snapScheduler;
        std::unique_ptr<runtime::PatrolScheduler> _patrolScheduler;
        std::thread _workerThread;
};

#endif
