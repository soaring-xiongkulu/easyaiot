//
// Created by basiclab on 25-10-15.
//
#include "Detech.h"
#include "Yolov11ThreadPool.h"
#include "Datatype.h"
#include <chrono>
#include <map>

static Yolov11ThreadPool *yolov11_thread_pool = nullptr;

Detech::Detech(Config &config): _config(config) {
    LOG(INFO) << "[INIT] Config initialization completed";
}

Detech::~Detech() {
    LOG(INFO) << "[CLEANUP] Detech destructor called, cleaning up resources...";
    
    // 停止HTTP控制服务器
    _stopControlServer();
    
    // 停止告警发送线程（企业级队列版本）
    _stopAlarmSenderThread();
    
    // 释放RTMP编码器
    if (_rtmpEncoder) {
        LOG(INFO) << "[CLEANUP] Releasing RTMP encoder...";
        _rtmpEncoder->release();
        delete _rtmpEncoder;
        _rtmpEncoder = nullptr;
    }
    
    // 释放HTTP客户端
    if (_httpClient) {
        LOG(INFO) << "[CLEANUP] Releasing HTTP client...";
        delete _httpClient;
        _httpClient = nullptr;
    }
    
    LOG(INFO) << "[CLEANUP] Detech cleanup completed successfully";
}

int Detech::start() {
    _isRun = true;
    
    LOG(INFO) << "[INIT] Step 1: Initializing YOLO detector...";
    if (!_init_yolo11_detector()) {
        LOG(ERROR) << "[INIT] YOLO detector initialization failed!";
        return -1;
    }
    LOG(INFO) << "[INIT] YOLO detector initialized successfully";
    
    LOG(INFO) << "[INIT] Step 2: Initializing media player...";
    if (!_init_media_player()) {
        LOG(ERROR) << "[INIT] Media player initialization failed!";
        return -2;
    }
    LOG(INFO) << "[INIT] Media player initialized successfully";
    
    LOG(INFO) << "[INIT] Step 3: Initializing HTTP client...";
    if (!_init_http_client()) {
        LOG(ERROR) << "[INIT] HTTP client initialization failed!";
        return -3;
    }
    LOG(INFO) << "[INIT] HTTP client initialized successfully";
    
    LOG(INFO) << "[INIT] Step 4: Initializing media alarmer...";
    if (!_init_media_alarmer()) {
        LOG(ERROR) << "[INIT] Media alarmer initialization failed!";
        return -4;
    }
    LOG(INFO) << "[INIT] Media alarmer initialized successfully";
    
    LOG(INFO) << "[INIT] Step 5: Initializing media pusher...";
    if (!_init_media_pusher()) {
        LOG(ERROR) << "[INIT] Media pusher initialization failed!";
        return -5;
    }
    LOG(INFO) << "[INIT] Media pusher initialized successfully";
    
    LOG(INFO) << "[INIT] Step 6: Initializing control server...";
    if (!_init_control_server()) {
        LOG(ERROR) << "[INIT] Control server initialization failed!";
        return -6;
    }
    LOG(INFO) << "[INIT] Control server initialized successfully";
    
    LOG(INFO) << "[INIT] Step 7: Starting alarm sender thread...";
    _startAlarmSenderThread();  // 启动告警发送线程（企业级队列版本）
    LOG(INFO) << "[INIT] Alarm sender thread started successfully";
    
    LOG(INFO) << "[INIT] Step 8: Starting control server...";
    _startControlServer();  // 启动HTTP控制服务器线程
    LOG(INFO) << "[INIT] Control server started successfully";
    
    LOG(INFO) << "[OK] All components initialized successfully!";
    
    // Start video display loop
    LOG(INFO) << "";
    LOG(INFO) << "[VIDEO] Starting real-time video display...";
    LOG(INFO) << "[VIDEO] Resolution: " << _videoWidth << "x" << _videoHeight << " @ " << _videoFps << " FPS";
    LOG(INFO) << "[VIDEO] Press 'q' or ESC to exit";
    LOG(INFO) << "";
    
    _display_video_loop();
    
    return 0;
}

int Detech::stop() {
    _isRun = false;
    return 0;
}

// ==================== 动态推流控制实现 ====================

// 启动RTMP推流（运行时动态启用）
bool Detech::startStreaming() {
    std::lock_guard<std::mutex> lock(_streamingMutex);
    
    // 如果已经在推流，直接返回
    if (_streamingEnabled.load()) {
        LOG(WARNING) << "[STREAMING] Already streaming, ignoring start request";
        return true;
    }
    
    LOG(INFO) << "[STREAMING] Starting RTMP streaming...";
    
    // 如果RTMP编码器未初始化，需要先初始化
    if (!_rtmpEncoder) {
        if (_config.rtmpUrl.empty()) {
            LOG(ERROR) << "[STREAMING] Cannot start streaming: RTMP URL not configured";
            return false;
        }
        
        // 创建并初始化RTMP编码器
        _rtmpEncoder = new RTMPEncoder();
        if (!_rtmpEncoder->init(_config.rtmpUrl, _videoWidth, _videoHeight, _videoFps)) {
            LOG(ERROR) << "[STREAMING] Failed to initialize RTMP encoder";
            delete _rtmpEncoder;
            _rtmpEncoder = nullptr;
            return false;
        }
        
        LOG(INFO) << "[STREAMING] RTMP encoder initialized successfully";
    }
    
    // 启用推流
    _streamingEnabled.store(true);
    LOG(INFO) << "[STREAMING] ✅ RTMP streaming started successfully";
    LOG(INFO) << "[STREAMING]   → URL: " << _config.rtmpUrl;
    LOG(INFO) << "[STREAMING]   → Resolution: " << _videoWidth << "x" << _videoHeight << "@" << _videoFps << "fps";
    
    return true;
}

// 停止RTMP推流（运行时动态停止）
bool Detech::stopStreaming() {
    std::lock_guard<std::mutex> lock(_streamingMutex);
    
    // 如果已经停止，直接返回
    if (!_streamingEnabled.load()) {
        LOG(WARNING) << "[STREAMING] Already stopped, ignoring stop request";
        return true;
    }
    
    LOG(INFO) << "[STREAMING] Stopping RTMP streaming...";
    
    // 禁用推流标志
    _streamingEnabled.store(false);
    
    // 释放RTMP编码器资源（节省内存）
    if (_rtmpEncoder) {
        LOG(INFO) << "[STREAMING] Releasing RTMP encoder to free memory...";
        _rtmpEncoder->release();
        delete _rtmpEncoder;
        _rtmpEncoder = nullptr;
        LOG(INFO) << "[STREAMING] RTMP encoder released (~111MB memory freed)";
    }
    
    LOG(INFO) << "[STREAMING] ✅ RTMP streaming stopped successfully";
    
    return true;
}

// 查询推流状态
bool Detech::isStreaming() const {
    return _streamingEnabled.load();
}

// ==================== HTTP控制服务器实现 ====================

// 初始化HTTP控制服务器
bool Detech::_init_control_server() {
    // 检查控制端口是否配置
    if (_config.controlPort <= 0) {
        LOG(INFO) << "[CONTROL] Control port not configured, control server disabled";
        return true;
    }
    
    _controlPort = _config.controlPort;
    LOG(INFO) << "[CONTROL] Control server will listen on port " << _controlPort;
    LOG(INFO) << "[CONTROL] Task ID: " << _config.taskId;
    
    return true;
}

// 启动HTTP控制服务器线程
void Detech::_startControlServer() {
    if (_controlPort <= 0) {
        return;  // 未配置控制端口
    }
    
    LOG(INFO) << "[CONTROL] Starting control server thread...";
    _controlServerRunning.store(true);
    _controlServerThread = std::thread(&Detech::_controlServerThreadFunc, this);
    LOG(INFO) << "[CONTROL] Control server thread started on port " << _controlPort;
}

// 停止HTTP控制服务器线程
void Detech::_stopControlServer() {
    if (!_controlServerRunning.load()) {
        return;
    }
    
    LOG(INFO) << "[CONTROL] Stopping control server...";
    _controlServerRunning.store(false);
    
    if (_controlServerThread.joinable()) {
        _controlServerThread.join();
    }
    
    LOG(INFO) << "[CONTROL] Control server stopped";
}

// HTTP控制服务器线程主函数
void Detech::_controlServerThreadFunc() {
    using namespace httplib;
    
    LOG(INFO) << "[CONTROL-THREAD] Control server thread running (Thread ID: " << std::this_thread::get_id() << ")";
    LOG(INFO) << "[CONTROL-THREAD] Listening on http://0.0.0.0:" << _controlPort;
    
    try {
        // 创建HTTP服务器
        Server svr;
        
        // 健康检查接口
        svr.Get("/health", [](const Request& req, Response& res) {
            Json::Value response;
            response["status"] = "ok";
            response["service"] = "TASK Control Server";
            
            Json::StreamWriterBuilder writer;
            res.set_content(Json::writeString(writer, response), "application/json");
        });
        
        // 启动推流接口
        svr.Post("/control/streaming/start", [this](const Request& req, Response& res) {
            LOG(INFO) << "[CONTROL-THREAD] Received start streaming request";
            
            bool success = this->startStreaming();
            
            Json::Value response;
            response["success"] = success;
            response["streaming"] = this->isStreaming();
            response["message"] = success ? "Streaming started successfully" : "Failed to start streaming";
            
            Json::StreamWriterBuilder writer;
            res.set_content(Json::writeString(writer, response), "application/json");
            res.status = success ? 200 : 500;
        });
        
        // 停止推流接口
        svr.Post("/control/streaming/stop", [this](const Request& req, Response& res) {
            LOG(INFO) << "[CONTROL-THREAD] Received stop streaming request";
            
            bool success = this->stopStreaming();
            
            Json::Value response;
            response["success"] = success;
            response["streaming"] = this->isStreaming();
            response["message"] = success ? "Streaming stopped successfully" : "Failed to stop streaming";
            
            Json::StreamWriterBuilder writer;
            res.set_content(Json::writeString(writer, response), "application/json");
            res.status = success ? 200 : 500;
        });
        
        // 查询推流状态接口
        svr.Get("/control/streaming/status", [this](const Request& req, Response& res) {
            Json::Value response;
            response["streaming"] = this->isStreaming();
            response["taskId"] = this->_config.taskId;
            response["rtmpUrl"] = this->_config.rtmpUrl;
            
            Json::StreamWriterBuilder writer;
            res.set_content(Json::writeString(writer, response), "application/json");
        });
        
        // 设置服务器参数
        svr.set_read_timeout(5, 0);   // 5秒超时
        svr.set_write_timeout(5, 0);
        
        LOG(INFO) << "[CONTROL-THREAD] ✅ Control server ready";
        LOG(INFO) << "[CONTROL-THREAD] Available endpoints:";
        LOG(INFO) << "[CONTROL-THREAD]   GET  /health - Health check";
        LOG(INFO) << "[CONTROL-THREAD]   POST /control/streaming/start - Start streaming";
        LOG(INFO) << "[CONTROL-THREAD]   POST /control/streaming/stop - Stop streaming";
        LOG(INFO) << "[CONTROL-THREAD]   GET  /control/streaming/status - Get streaming status";
        
        // 启动服务器（阻塞）
        if (!svr.listen("0.0.0.0", _controlPort)) {
            LOG(ERROR) << "[CONTROL-THREAD] Failed to start control server on port " << _controlPort;
        }
        
    } catch (const std::exception& e) {
        LOG(ERROR) << "[CONTROL-THREAD] Exception in control server: " << e.what();
    }
    
    LOG(INFO) << "[CONTROL-THREAD] Control server thread exiting";
}

bool Detech::_init_http_client() {
    // cpp-httplib需要"host:port"格式，不是完整URL
    // 从hookHttpUrl提取主机和端口
    std::string host = "localhost";
    int port = 5000;
    
    // 简单解析：假设格式为 http://host:port/path
    if (!_config.hookHttpUrl.empty()) {
        size_t protocolEnd = _config.hookHttpUrl.find("://");
        if (protocolEnd != std::string::npos) {
            size_t hostStart = protocolEnd + 3;
            size_t portStart = _config.hookHttpUrl.find(":", hostStart);
            size_t pathStart = _config.hookHttpUrl.find("/", hostStart);
            
            if (portStart != std::string::npos && pathStart != std::string::npos) {
                host = _config.hookHttpUrl.substr(hostStart, portStart - hostStart);
                std::string portStr = _config.hookHttpUrl.substr(portStart + 1, pathStart - portStart - 1);
                port = std::stoi(portStr);
            } else if (pathStart != std::string::npos) {
                host = _config.hookHttpUrl.substr(hostStart, pathStart - hostStart);
            }
        }
    }
    
    LOG(INFO) << "[INIT] Creating HTTP client for " << host << ":" << port;
    _httpClient = new httplib::Client(host, port);
    _httpClient->set_connection_timeout(5, 0);  // 5秒连接超时
    _httpClient->set_read_timeout(5, 0);        // 5秒读取超时
    _httpClient->set_write_timeout(5, 0);       // 5秒写入超时
    
    LOG(INFO) << "[INIT] HTTP client created successfully";
    return true;
}

bool Detech::_init_yolo11_detector() {
    // Skip YOLO initialization if AI is disabled
    if (!_config.enableAI) {
        LOG(INFO) << "[INIT] AI inference disabled, skipping YOLO initialization";
        return true;
    }
    
    if (!yolov11_thread_pool) {
        yolov11_thread_pool = new Yolov11ThreadPool();
        
        // Extract first model path and classes from map
        // TODO: Support multiple models in future version
        if (_config.modelPaths.empty()) {
            LOG(ERROR) << "[ERROR] No model path configured in config file!";
            return false;
        }
        
        std::string modelPath = _config.modelPaths.begin()->second;
        
        // Check if model path is empty string
        if (modelPath.empty()) {
            LOG(WARNING) << "[INIT] Model path is empty, skipping YOLO initialization";
            return true;
        }
        
        LOG(INFO) << "[INIT] Model path: " << modelPath;
        
        std::vector<std::string> classes;
        
        // Load classes if configured
        if (!_config.modelClasses.empty()) {
            std::string classFile = _config.modelClasses.begin()->second;
            LOG(INFO) << "[INIT] Classes file: " << classFile;
            // TODO: Load classes from file
            // For now, use empty vector (will use default COCO classes)
        }
        
        LOG(INFO) << "[INIT] Loading YOLO model with " << _config.threadNums << " threads...";
        int ret = yolov11_thread_pool->setUp(modelPath, classes, _config.threadNums);
        if (ret) {
            LOG(ERROR) << "[ERROR] YOLO thread pool initialization failed, error code: " << ret;
            return false;
        }
        LOG(INFO) << "[OK] YOLO thread pool initialized";
    }
    return true;
}

bool Detech::_init_media_player() {
    LOG(INFO) << "[INIT] Initializing media player";
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
    return true;
}

bool Detech::_init_media_pusher() {
    // 检查配置：如果enable_rtmp=true，则默认启用推流
    if (!_config.enableRtmp) {
        LOG(INFO) << "[INIT] RTMP streaming disabled in config";
        LOG(INFO) << "[INIT]   → Can be enabled later via API call (on-demand streaming)";
        _streamingEnabled.store(false);
        return true;
    }
    
    // 检查RTMP URL是否配置
    if (_config.rtmpUrl.empty()) {
        LOG(WARNING) << "[INIT] RTMP URL not configured, streaming disabled";
        _streamingEnabled.store(false);
        return true;
    }
    
    // 创建并初始化RTMP编码器
    _rtmpEncoder = new RTMPEncoder();
    
    LOG(INFO) << "[INIT] Initializing RTMP encoder...";
    LOG(INFO) << "[INIT] RTMP URL: " << _config.rtmpUrl;
    LOG(INFO) << "[INIT] Video: " << _videoWidth << "x" << _videoHeight << "@" << _videoFps << "fps";
    
    if (!_rtmpEncoder->init(_config.rtmpUrl, _videoWidth, _videoHeight, _videoFps)) {
        LOG(WARNING) << "[INIT] ⚠️ RTMP encoder initialization failed (ZLMediaKit not running?)";
        LOG(WARNING) << "[INIT] ⚠️ Streaming disabled, but program will continue";
        LOG(WARNING) << "[INIT] ⚠️ You can start streaming later via API when ZLM is ready";
        delete _rtmpEncoder;
        _rtmpEncoder = nullptr;
        _streamingEnabled.store(false);
        // ✅ 不阻止程序启动
        return true;
    }
    
    // 初始化成功，自动启用推流
    _streamingEnabled.store(true);
    LOG(INFO) << "[OK] RTMP encoder initialized successfully";
    LOG(INFO) << "[OK] ✅ Streaming enabled by default (config: enable_rtmp=true)";
    
    return true;
}

// 获取当前时间戳（毫秒）
uint64_t Detech::_get_curtime_stamp_ms() {
    auto now = std::chrono::system_clock::now();
    auto duration = now.time_since_epoch();
    auto millis = std::chrono::duration_cast<std::chrono::milliseconds>(duration).count();
    return static_cast<uint64_t>(millis);
}

bool Detech::_init_media_alarmer() {
    if (!_config.enableAlarm) {
        LOG(INFO) << "[INIT] Alarm detection disabled";
        return true;
    }
    
    if (_config.hookHttpUrl.empty()) {
        LOG(WARNING) << "[INIT] Alarm enabled but hook URL not configured";
        return true;
    }
    
    // HTTP客户端已在_init_http_client()中初始化，这里只需验证
    if (!_httpClient) {
        LOG(ERROR) << "[INIT] HTTP client not initialized for alarm callback";
        return false;
    }
    
    LOG(INFO) << "[INIT] Alarm callback initialized";
    LOG(INFO) << "  → Hook URL: " << _config.hookHttpUrl;
    LOG(INFO) << "  → Confidence threshold: " << _config.alarmConfidenceThreshold;
    LOG(INFO) << "  → Cooldown time: " << _config.alarmCooldownTime << "s";
    
    return true;
}

// 检查检测框中心点是否在任何报警区域内
bool Detech::_isInAlarmRegion(int centerX, int centerY) {
    // 如果没有配置报警区域，默认全区域都触发告警
    if (_config.regions.empty()) {
        return true;
    }
    
    cv::Point2f center(centerX, centerY);
    
    // 遍历所有配置的报警区域
    for (const auto& regionPair : _config.regions) {
        const std::vector<std::vector<cv::Point>>& polygons = regionPair.second;
        
        // 每个区域可能有多个多边形
        for (const auto& polygon : polygons) {
            if (polygon.size() < 3) {
                continue;  // 多边形至少需要3个点
            }
            
            // 使用OpenCV的pointPolygonTest判断点是否在多边形内
            // 返回值 >= 0 表示在多边形内或边上
            double result = cv::pointPolygonTest(polygon, center, false);
            if (result >= 0) {
                return true;  // 在某个报警区域内
            }
        }
    }
    
    return false;  // 不在任何报警区域内
}

// 绘制所有报警区域边界（半透明多边形）
void Detech::_drawAlarmRegions(cv::Mat& image) {
    if (_config.regions.empty()) {
        return;
    }
    
    int colorIndex = 0;
    // 定义区域颜色（绿色系表示报警区域）
    std::vector<cv::Scalar> colors = {
        cv::Scalar(0, 255, 0),     // 绿色
        cv::Scalar(0, 255, 255),   // 黄色
        cv::Scalar(255, 0, 255),   // 紫色
        cv::Scalar(255, 255, 0),   // 青色
    };
    
    // 遍历所有报警区域
    for (const auto& regionPair : _config.regions) {
        const std::string& regionName = regionPair.first;
        const std::vector<std::vector<cv::Point>>& polygons = regionPair.second;
        
        cv::Scalar color = colors[colorIndex % colors.size()];
        colorIndex++;
        
        // 绘制每个多边形
        for (const auto& polygon : polygons) {
            if (polygon.size() < 3) {
                continue;
            }
            
            // ✅ 直接在原图上绘制多边形边界（不使用掩码）
            // 绘制多边形边界（粗绿色线）
            cv::polylines(image, polygon, true, color, 3);
            
            // ✅ 在区域中心显示区域名称
            if (!polygon.empty()) {
                // 计算多边形中心点
                int sumX = 0, sumY = 0;
                for (const auto& pt : polygon) {
                    sumX += pt.x;
                    sumY += pt.y;
                }
                cv::Point center(sumX / polygon.size(), sumY / polygon.size());
                
                // 绘制区域名称背景
                std::string label = regionName;
                int baseLine;
                cv::Size labelSize = cv::getTextSize(label, cv::FONT_HERSHEY_SIMPLEX, 0.8, 2, &baseLine);
                
                cv::rectangle(image, 
                             cv::Point(center.x - labelSize.width/2 - 10, center.y - labelSize.height - 10),
                             cv::Point(center.x + labelSize.width/2 + 10, center.y + 10),
                             color, -1);
                
                // 绘制区域名称（白色文字）
                cv::putText(image, label, 
                           cv::Point(center.x - labelSize.width/2, center.y), 
                           cv::FONT_HERSHEY_SIMPLEX, 0.8, 
                           cv::Scalar(255, 255, 255), 2);
            }
        }
    }
}

// 检查告警冷却时间
bool Detech::_checkAlarmCooldown() {
    uint64_t currentTime = _get_curtime_stamp_ms();
    uint64_t timeSinceLastAlarm = currentTime - _lastAlarmTime;
    uint64_t cooldownMs = _config.alarmCooldownTime * 1000;  // 转换为毫秒
    
    if (timeSinceLastAlarm < cooldownMs) {
        // 仍在冷却期内
        return false;
    }
    
    // 冷却期已过
    return true;
}

// ==================== 企业级告警队列系统实现 ====================

// 启动告警发送线程
void Detech::_startAlarmSenderThread() {
    if (!_config.enableAlarm || _config.hookHttpUrl.empty()) {
        LOG(INFO) << "[ALARM] Alarm disabled or no hook URL, skipping alarm thread";
        return;
    }
    
    LOG(INFO) << "[ALARM] Starting alarm sender thread...";
    _alarmThreadRunning.store(true);
    _alarmSenderThread = std::thread(&Detech::_alarmSenderThreadFunc, this);
    LOG(INFO) << "[ALARM] Alarm sender thread started successfully";
}

// 停止告警发送线程
void Detech::_stopAlarmSenderThread() {
    if (!_alarmThreadRunning.load()) {
        return;
    }
    
    LOG(INFO) << "[ALARM] Stopping alarm sender thread...";
    _alarmThreadRunning.store(false);
    _alarmQueueCV.notify_all();  // 唤醒线程
    
    if (_alarmSenderThread.joinable()) {
        _alarmSenderThread.join();  // 等待线程结束
    }
    
    // 清空队列
    {
        std::lock_guard<std::mutex> lock(_alarmQueueMutex);
        while (!_alarmQueue.empty()) {
            _alarmQueue.pop();
        }
    }
    
    LOG(INFO) << "[ALARM] Alarm sender thread stopped successfully";
}

// 告警发送线程主函数
void Detech::_alarmSenderThreadFunc() {
    LOG(INFO) << "[ALARM-THREAD] Alarm sender thread running (Thread ID: " << std::this_thread::get_id() << ")";
    
    while (_alarmThreadRunning.load()) {
        AlarmData alarmData;
        bool hasData = false;
        
        // 从队列中获取告警数据
        {
            std::unique_lock<std::mutex> lock(_alarmQueueMutex);
            
            // 等待队列有数据或线程停止信号
            _alarmQueueCV.wait(lock, [this] {
                return !_alarmQueue.empty() || !_alarmThreadRunning.load();
            });
            
            // 如果线程要停止且队列为空，退出循环
            if (!_alarmThreadRunning.load() && _alarmQueue.empty()) {
                break;
            }
            
            // 取出队列头部数据
            if (!_alarmQueue.empty()) {
                alarmData = std::move(_alarmQueue.front());
                _alarmQueue.pop();
                hasData = true;
                LOG(INFO) << "[ALARM-THREAD] Dequeued alarm, remaining in queue: " << _alarmQueue.size();
            }
        }
        
        // 如果没有数据，继续等待
        if (!hasData) {
            continue;
        }
        
        // 发送告警（不持锁，避免阻塞队列）
        try {
            // 构建JSON数据
            Json::Value root;
            root["taskId"] = _config.taskId.empty() ? "camera_test" : _config.taskId;
            root["timestamp"] = (Json::Value::Int64)alarmData.timestamp;
            root["alarmType"] = "region_intrusion";
            root["regionName"] = alarmData.regionName;
            root["detectionCount"] = static_cast<int>(alarmData.detections.size());
            
            // 添加检测结果数组
            Json::Value detectionsArray(Json::arrayValue);
            for (const auto& det : alarmData.detections) {
                Json::Value detObj;
                detObj["class_name"] = det.class_name;
                detObj["confidence"] = det.class_score;
                
                Json::Value bbox(Json::arrayValue);
                bbox.append(static_cast<int>(det.x1));
                bbox.append(static_cast<int>(det.y1));
                bbox.append(static_cast<int>(det.x2));
                bbox.append(static_cast<int>(det.y2));
                detObj["bbox"] = bbox;
                
                detObj["centerX"] = static_cast<int>((det.x1 + det.x2) / 2);
                detObj["centerY"] = static_cast<int>((det.y1 + det.y2) / 2);
                
                detectionsArray.append(detObj);
            }
            root["detections"] = detectionsArray;
            
            // 转换为字符串
            Json::StreamWriterBuilder writer;
            std::string jsonStr = Json::writeString(writer, root);
            
            // 从完整URL中提取路径部分
            std::string path = "/api/alarm/callback/123";
            if (!_config.hookHttpUrl.empty()) {
                size_t protocolEnd = _config.hookHttpUrl.find("://");
                if (protocolEnd != std::string::npos) {
                    size_t pathStart = _config.hookHttpUrl.find("/", protocolEnd + 3);
                    if (pathStart != std::string::npos) {
                        path = _config.hookHttpUrl.substr(pathStart);
                    }
                }
            }
            
            // 发送HTTP POST请求
            LOG(INFO) << "[ALARM-THREAD] Sending callback to: " << _config.hookHttpUrl;
            
            auto res = _httpClient->Post(path.c_str(), jsonStr, "application/json");
            
            if (res && res->status == 200) {
                LOG(INFO) << "[ALARM-THREAD] ✅ Callback sent successfully";
                // 只在DEBUG模式打印响应体（减少日志输出）
                // LOG(INFO) << "[ALARM-THREAD] Response: " << res->body;
            } else {
                LOG(ERROR) << "[ALARM-THREAD] ❌ Callback failed";
                if (res) {
                    LOG(ERROR) << "  → HTTP Status: " << res->status;
                } else {
                    LOG(ERROR) << "  → Network error or timeout";
                }
            }
            
        } catch (const std::exception& e) {
            LOG(ERROR) << "[ALARM-THREAD] Exception while sending alarm: " << e.what();
        }
    }
    
    LOG(INFO) << "[ALARM-THREAD] Alarm sender thread exiting gracefully";
}

// 发送告警回调（企业级队列版本 - 只负责入队）
void Detech::_sendAlarmCallback(const std::vector<DetectObject>& detections, const std::string& regionName) {
    if (!_config.enableAlarm || _config.hookHttpUrl.empty()) {
        return;
    }
    
    // 检查告警发送线程是否正在运行
    if (!_alarmThreadRunning.load()) {
        LOG(WARNING) << "[ALARM] Alarm sender thread not running, alarm dropped";
        return;
    }
    
    // 入队操作
    {
        std::lock_guard<std::mutex> lock(_alarmQueueMutex);
        
        // 检查队列是否已满
        if (_alarmQueue.size() >= MAX_ALARM_QUEUE_SIZE) {
            LOG(WARNING) << "[ALARM] Queue full (" << _alarmQueue.size() 
                        << "/" << MAX_ALARM_QUEUE_SIZE << "), dropping oldest alarm";
            _alarmQueue.pop();  // 移除最旧的告警
        }
        
        // 创建告警数据并入队
        AlarmData alarmData(detections, regionName, _get_curtime_stamp_ms());
        _alarmQueue.push(std::move(alarmData));
        
        LOG(INFO) << "[ALARM] Alarm enqueued, queue size: " << _alarmQueue.size() 
                  << "/" << MAX_ALARM_QUEUE_SIZE;
    }
    
    // 唤醒告警发送线程
    _alarmQueueCV.notify_one();
    
    // 更新最后告警时间（用于冷却机制）
    _lastAlarmTime = _get_curtime_stamp_ms();
}

void Detech::_display_video_loop() {
    if (!_ffmpegFormatCtx || !_ffmpegCodecCtx) {
        LOG(ERROR) << "[VIDEO] FFmpeg not initialized!";
        return;
    }
    
    // Create OpenCV window
    const char* windowName = "RTSP Live Stream - Press 'q' to exit";
    cv::namedWindow(windowName, cv::WINDOW_NORMAL);
    cv::resizeWindow(windowName, 1280, 720);
    
    // Allocate packet and frame
    AVPacket* packet = av_packet_alloc();
    AVFrame* frame = av_frame_alloc();
    AVFrame* frameRGB = av_frame_alloc();
    
    if (!packet || !frame || !frameRGB) {
        LOG(ERROR) << "[VIDEO] Failed to allocate AVPacket or AVFrame";
        return;
    }
    
    // Allocate RGB buffer
    int numBytes = av_image_get_buffer_size(AV_PIX_FMT_BGR24, _videoWidth, _videoHeight, 1);
    uint8_t* buffer = (uint8_t*)av_malloc(numBytes * sizeof(uint8_t));
    av_image_fill_arrays(frameRGB->data, frameRGB->linesize, buffer, AV_PIX_FMT_BGR24, _videoWidth, _videoHeight, 1);
    
    // Create SwsContext for pixel format conversion
    struct SwsContext* swsCtx = sws_getContext(
        _videoWidth, _videoHeight, _ffmpegCodecCtx->pix_fmt,
        _videoWidth, _videoHeight, AV_PIX_FMT_BGR24,
        SWS_BILINEAR, NULL, NULL, NULL
    );
    
    if (!swsCtx) {
        LOG(ERROR) << "[VIDEO] Failed to create SwsContext";
        av_free(buffer);
        av_frame_free(&frameRGB);
        av_frame_free(&frame);
        av_packet_free(&packet);
        return;
    }
    
    LOG(INFO) << "[VIDEO] Display loop started";
    
    // FPS calculation
    int frameCount = 0;
    auto startTime = std::chrono::steady_clock::now();
    auto lastFrameTime = startTime;
    double currentFPS = 0.0;
    double currentLatency = 0.0;
    
    while (_isRun) {
        // Read packet
        int ret = av_read_frame(_ffmpegFormatCtx, packet);
        if (ret < 0) {
            if (ret == AVERROR_EOF) {
                LOG(INFO) << "[VIDEO] End of stream";
                break;
            }
            LOG(WARNING) << "[VIDEO] Error reading frame: " << ret;
            continue;
        }
        
        // Only process video packets
        if (packet->stream_index != _videoIndex) {
            av_packet_unref(packet);
            continue;
        }
        
        // Decode video packet
        ret = avcodec_send_packet(_ffmpegCodecCtx, packet);
        if (ret < 0) {
            LOG(WARNING) << "[VIDEO] Error sending packet to decoder";
            av_packet_unref(packet);
            continue;
        }
        
        ret = avcodec_receive_frame(_ffmpegCodecCtx, frame);
        if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
            av_packet_unref(packet);
            continue;
        } else if (ret < 0) {
            LOG(WARNING) << "[VIDEO] Error decoding frame";
            av_packet_unref(packet);
            continue;
        }
        
        // Convert to BGR24 for OpenCV
        sws_scale(swsCtx, frame->data, frame->linesize, 0, _videoHeight,
                  frameRGB->data, frameRGB->linesize);
        
        // Create OpenCV Mat (deep copy for AI processing)
        cv::Mat img(_videoHeight, _videoWidth, CV_8UC3);
        cv::Mat tempImg(_videoHeight, _videoWidth, CV_8UC3, frameRGB->data[0], frameRGB->linesize[0]);
        tempImg.copyTo(img);
        
        // AI Detection (if enabled) - ASYNCHRONOUS MODE
        static std::vector<DetectObject> lastDetections;  // Cache last detection results
        static int lastSubmittedFrameId = -1;
        static int aiFrameInterval = 0;
        const int SUBMIT_INTERVAL = 8;  // 每8帧检测一次
        std::vector<DetectObject> detections;
        int detectCount = 0;
        
        if (_config.enableAI && yolov11_thread_pool) {
            // Submit task every N frames to avoid queue buildup
            if (aiFrameInterval % SUBMIT_INTERVAL == 0) {
                yolov11_thread_pool->submitTask(img, 0, frameCount);
                lastSubmittedFrameId = frameCount;
            }
            aiFrameInterval++;
            
            // Try to get any available result (non-blocking)
            bool foundNewResult = false;
            for (int checkFrame = lastSubmittedFrameId; checkFrame >= 0 && checkFrame >= lastSubmittedFrameId - 30; checkFrame--) {
                int ret = yolov11_thread_pool->getTargetResultNonBlock(detections, 0, checkFrame);
                if (ret == 0) {
                    // Successfully got results, cache them
                    lastDetections = detections;
                    foundNewResult = true;
                    break;
                }
            }
            
            // 🎯 绘制报警区域（ROI）- 已禁用，前端页面绘制
            // _drawAlarmRegions(img);
            
            // 🎯 绘制检测框并应用区域过滤
            if (_config.enableDrawRtmp && !lastDetections.empty()) {
                int totalDetections = lastDetections.size();
                int inRegionCount = 0;  // 在报警区域内的目标数量
                std::vector<DetectObject> alarmDetections;  // 触发告警的目标列表
                
                for (const auto& det : lastDetections) {
                    int x1 = (int)det.x1;
                    int y1 = (int)det.y1;
                    int x2 = (int)det.x2;
                    int y2 = (int)det.y2;
                    
                    // 计算检测框中心点
                    int centerX = (x1 + x2) / 2;
                    int centerY = (y1 + y2) / 2;
                    
                    // 检查是否在报警区域内
                    bool inAlarmRegion = _isInAlarmRegion(centerX, centerY);
                    if (inAlarmRegion) {
                        inRegionCount++;
                        
                        // 检查置信度是否达到告警阈值
                        if (det.class_score >= _config.alarmConfidenceThreshold) {
                            alarmDetections.push_back(det);
                        }
                    }
                    
                    // 根据是否在报警区域内选择颜色
                    cv::Scalar color;
                    if (inAlarmRegion) {
                        // 在报警区域内：使用红色（告警）
                        color = cv::Scalar(0, 0, 255);  // 红色
                    } else {
                        // 不在报警区域内：使用蓝色（正常）
                        color = cv::Scalar(255, 0, 0);  // 蓝色
                    }
                    
                    // 绘制边界框（在报警区域内的框更粗）
                    int thickness = inAlarmRegion ? 3 : 1;
                    cv::rectangle(img, cv::Point(x1, y1), cv::Point(x2, y2), color, thickness);
                    
                    // 绘制中心点（用于调试）
                    cv::circle(img, cv::Point(centerX, centerY), 5, color, -1);
                    
                    // 准备标签文本
                    std::string label = det.class_name + " " + 
                                       std::to_string((int)(det.class_score * 100)) + "%";
                    if (inAlarmRegion) {
                        label += " [ALARM]";  // 在报警区域内的目标添加标记
                    }
                    
                    // 计算文本背景框大小
                    int baseLine;
                    cv::Size labelSize = cv::getTextSize(label, cv::FONT_HERSHEY_SIMPLEX, 
                                                         0.6, 2, &baseLine);
                    
                    // 确保标签不会超出图像顶部
                    int labelY = std::max(y1, labelSize.height + 5);
                    
                    // 绘制标签背景
                    cv::rectangle(img,
                                 cv::Point(x1, labelY - labelSize.height - 5),
                                 cv::Point(x1 + labelSize.width + 5, labelY),
                                 color, -1);
                    
                    // 绘制标签文本
                    cv::putText(img, label,
                               cv::Point(x1 + 3, labelY - 3),
                               cv::FONT_HERSHEY_SIMPLEX, 0.6, 
                               cv::Scalar(255, 255, 255), 2);
                }
                
                // 更新检测计数（只计算在报警区域内的目标）
                detectCount = inRegionCount;
                
                // 🚨 触发告警回调（如果有目标在区域内且满足条件）
                if (!alarmDetections.empty() && _checkAlarmCooldown()) {
                    std::string regionName = _config.regions.empty() ? "全画面" : "检测区域";
                    if (!_config.regions.empty()) {
                        regionName = _config.regions.begin()->first;  // 获取第一个区域名称
                    }
                    _sendAlarmCallback(alarmDetections, regionName);
                }
            }
        }
        
        // Calculate FPS
        frameCount++;
        auto currentTime = std::chrono::steady_clock::now();
        auto elapsedTime = std::chrono::duration_cast<std::chrono::milliseconds>(currentTime - startTime).count();
        
        if (elapsedTime >= 1000) {
            currentFPS = frameCount * 1000.0 / elapsedTime;
            frameCount = 0;
            startTime = currentTime;
        }
        
        // Calculate latency (time between frames)
        auto frameLatency = std::chrono::duration_cast<std::chrono::milliseconds>(currentTime - lastFrameTime).count();
        currentLatency = frameLatency;
        lastFrameTime = currentTime;
        
        // Draw info overlay
        std::string fpsText = "FPS: " + std::to_string((int)currentFPS);
        std::string latencyText = "Frame: " + std::to_string((int)currentLatency) + " ms";
        std::string resText = std::to_string(_videoWidth) + "x" + std::to_string(_videoHeight);
        std::string aiText = _config.enableAI ? 
            ("AI: ON | Objects: " + std::to_string(detectCount)) : "AI: OFF";
        
        cv::putText(img, fpsText, cv::Point(10, 30), 
                    cv::FONT_HERSHEY_SIMPLEX, 0.8, cv::Scalar(0, 255, 0), 2);
        cv::putText(img, latencyText, cv::Point(10, 65), 
                    cv::FONT_HERSHEY_SIMPLEX, 0.8, cv::Scalar(0, 255, 0), 2);
        cv::putText(img, resText, cv::Point(10, 100), 
                    cv::FONT_HERSHEY_SIMPLEX, 0.8, cv::Scalar(0, 255, 0), 2);
        cv::putText(img, aiText, cv::Point(10, 135), 
                    cv::FONT_HERSHEY_SIMPLEX, 0.8, 
                    _config.enableAI ? cv::Scalar(0, 255, 255) : cv::Scalar(128, 128, 128), 2);
        
        // Display frame
        cv::imshow(windowName, img);
        
        // RTMP推流（按需推流：只在_streamingEnabled=true时推流）
        if (_streamingEnabled.load() && _rtmpEncoder && _rtmpEncoder->isInitialized()) {
            // 推送带检测框的画面
            if (!_rtmpEncoder->encodeAndPush(img)) {
                // 推流失败只记录警告，不中断程序
                static int pushErrorCount = 0;
                pushErrorCount++;
                if (pushErrorCount % 100 == 1) {  // 每100次失败输出一次日志
                    LOG(WARNING) << "[RTMP] Push frame failed (error count: " << pushErrorCount << ")";
                }
            }
        }
        
        // Check for key press
        int key = cv::waitKey(1);
        if (key == 'q' || key == 'Q' || key == 27) { // 'q' or ESC
            LOG(INFO) << "[VIDEO] User requested exit";
            _isRun = false;
            break;
        }
        
        av_packet_unref(packet);
    }
    
    // Cleanup
    LOG(INFO) << "[VIDEO] Cleaning up...";
    cv::destroyAllWindows();
    sws_freeContext(swsCtx);
    av_free(buffer);
    av_frame_free(&frameRGB);
    av_frame_free(&frame);
    av_packet_free(&packet);
    
    LOG(INFO) << "[VIDEO] Display loop stopped";
}
