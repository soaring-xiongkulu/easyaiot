#ifndef DETECH_H
#define DETECH_H

#include <iostream>
#include <thread>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <atomic>
#include <glog/logging.h>
#include <httplib.h>
#include <opencv2/opencv.hpp>
#include <json/json.h>
#include "Config.h"
#include "RTMPEncoder.h"
#include "Datatype.h"

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
        
        // 动态推流控制（运行时启停RTMP推流）
        bool startStreaming();   // 启动RTMP推流
        bool stopStreaming();    // 停止RTMP推流
        bool isStreaming() const; // 查询推流状态
    private:
        bool _init_yolo11_detector();
        bool _init_http_client();
        bool _init_media_player();
        bool _init_media_pusher();
        bool _init_media_alarmer();
        bool _init_control_server();  // 初始化HTTP控制服务器
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
        
        // 区域过滤相关方法
        bool _isInAlarmRegion(int centerX, int centerY);
        void _drawAlarmRegions(cv::Mat& image);
        
        // 告警回调相关方法（企业级队列版本）
        void _sendAlarmCallback(const std::vector<DetectObject>& detections, const std::string& regionName);
        bool _checkAlarmCooldown();
        
        // 告警发送线程相关
        void _startAlarmSenderThread();
        void _stopAlarmSenderThread();
        void _alarmSenderThreadFunc();
        
        // HTTP控制服务器线程相关
        void _startControlServer();
        void _stopControlServer();
        void _controlServerThreadFunc();
        
        // 告警数据结构
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
        httplib::Client* _httpClient;
        AVFormatContext* _ffmpegFormatCtx{nullptr};
        AVCodecContext* _ffmpegCodecCtx{nullptr};
        AVStream* _ffmpegStream{nullptr};
        int _videoIndex = -1;
        int _videoFps = 0;
        int _videoWidth = 0;
        int _videoHeight = 0;
        int _videoChannel = 0;
        
        // RTMP推流编码器
        RTMPEncoder* _rtmpEncoder{nullptr};
        
        // 告警冷却相关
        uint64_t _lastAlarmTime{0};  // 上次告警时间戳（毫秒）
        
        // 企业级告警队列系统
        std::queue<AlarmData> _alarmQueue;          // 告警队列
        std::mutex _alarmQueueMutex;                // 队列互斥锁
        std::condition_variable _alarmQueueCV;      // 条件变量
        std::thread _alarmSenderThread;             // 告警发送线程
        std::atomic<bool> _alarmThreadRunning{false}; // 线程运行标志
        static const size_t MAX_ALARM_QUEUE_SIZE = 20; // 最大队列长度
        
        // 动态推流控制
        std::atomic<bool> _streamingEnabled{false};  // 推流启用标志（线程安全）
        std::mutex _streamingMutex;                  // 推流控制互斥锁
        
        // HTTP控制服务器
        std::thread _controlServerThread;            // 控制服务器线程
        std::atomic<bool> _controlServerRunning{false}; // 控制服务器运行标志
        int _controlPort{0};                         // 控制服务器端口（8000+taskId）
};

#endif

