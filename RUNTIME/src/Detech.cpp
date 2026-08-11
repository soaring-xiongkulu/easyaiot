//
// Created by basiclab on 25-10-15.
//
#include "AlgoMqttBus.h"
#include "Detech.h"
#include "YoloThreadPool.h"
#include "Datatype.h"
#include "ffmpeg_hw.h"
#include <atomic>
#include <chrono>
#include <ctime>
#include <fstream>
#include <iomanip>
#include <map>
#include <sstream>
#include <sys/stat.h>
#include <opencv2/imgproc.hpp>
#include <opencv2/geometry.hpp>
#include <unistd.h>

// Defined in Manage.cpp — request clean process exit on finite-source EOF
extern std::atomic<int> s_exit;

static YoloThreadPool *yolo_thread_pool = nullptr;

namespace {
std::string formatUtcNow() {
    auto now = std::chrono::system_clock::now();
    std::time_t t = std::chrono::system_clock::to_time_t(now);
    std::tm tm{};
    gmtime_r(&t, &tm);
    std::ostringstream oss;
    oss << std::put_time(&tm, "%Y-%m-%dT%H:%M:%SZ");
    return oss.str();
}

bool parseHttpUrl(const std::string& url, std::string& host, int& port, std::string& path) {
    size_t protocolPos = url.find("://");
    if (protocolPos == std::string::npos) {
        return false;
    }
    std::string rest = url.substr(protocolPos + 3);
    size_t pathPos = rest.find('/');
    std::string hostPort = pathPos == std::string::npos ? rest : rest.substr(0, pathPos);
    path = pathPos == std::string::npos ? "/" : rest.substr(pathPos);
    size_t colonPos = hostPort.find(':');
    if (colonPos != std::string::npos) {
        host = hostPort.substr(0, colonPos);
        try {
            port = std::stoi(hostPort.substr(colonPos + 1));
        } catch (...) {
            port = 80;
        }
    } else {
        host = hostPort;
        port = 80;
    }
    return !host.empty();
}
}  // namespace

Detech::Detech(Config &config): _config(config) {
    LOG(INFO) << "[INIT] Config initialization completed";
}

std::string Detech::_normalizedTaskType() const {
    std::string tt = _config.taskType;
    if (tt == "snapshot") return "snap";
    if (tt.empty()) return "realtime";
    return tt;
}

Detech::~Detech() {
    LOG(INFO) << "[CLEANUP] Detech destructor called, cleaning up resources...";
    stop();

    if (_workerThread.joinable()) {
        _workerThread.join();
    }
    if (_pipeline) {
        _pipeline->join();
        _pipeline.reset();
    }
    if (_streamForwarder) {
        _streamForwarder->join();
        _streamForwarder.reset();
    }
    if (_snapScheduler) {
        _snapScheduler->join();
        _snapScheduler.reset();
    }
    if (_patrolScheduler) {
        _patrolScheduler->join();
        _patrolScheduler.reset();
    }

    _stopHeartbeatThread();
    _stopControlServer();
    _stopAlarmSenderThread();

    if (_rtmpEncoder) {
        _rtmpEncoder->release();
        delete _rtmpEncoder;
        _rtmpEncoder = nullptr;
    }
    if (_httpClient) {
        delete _httpClient;
        _httpClient = nullptr;
    }
    runtime::releaseHwDecodeState(&_hwDecodeState);
    LOG(INFO) << "[CLEANUP] Detech cleanup completed successfully";
}

int Detech::start() {
    _isRun = true;
    const std::string mode = _normalizedTaskType();
    const bool isForward = (mode == "forward");
    LOG(INFO) << "[INIT] task_type=" << mode;

    if (!isForward && !_init_yolo_detector()) {
        LOG(ERROR) << "[INIT] YOLO detector initialization failed!";
        return -1;
    }

    // realtime needs FFmpeg decode pipeline; forward uses copy relay
    if (mode == "realtime") {
        if (!_init_media_player()) {
            LOG(ERROR) << "[INIT] Media player initialization failed!";
            return -2;
        }
    } else if (isForward) {
        if (_config.rtspUrl.empty()) {
            LOG(ERROR) << "[INIT] forward mode requires rtsp_url";
            return -2;
        }
        if (_config.rtmpUrl.empty()) {
            LOG(ERROR) << "[INIT] forward mode requires rtmp_url";
            return -2;
        }
        LOG(INFO) << "[INIT] forward-only relay (no AI/decode/encode)";
    }

    if (!_init_http_client()) {
        LOG(ERROR) << "[INIT] HTTP client initialization failed!";
        return -3;
    }
    if (!isForward && !_init_media_alarmer()) {
        return -4;
    }
    if (mode == "realtime") {
        if (!_init_media_pusher()) {
            return -5;
        }
    }
    if (!_init_control_server()) {
        return -6;
    }

    if (!isForward) {
        _startAlarmSenderThread();
    }
    _startControlServer();
    _startHeartbeatThread();

    if (isForward) {
        LOG(INFO) << "[VIDEO] Forward-only copy relay mode";
        _streamingEnabled.store(true);
        _workerThread = std::thread([this]() { _run_forward_loop(); });
    } else if (mode == "snap") {
        LOG(INFO) << "[VIDEO] Snap scheduler mode";
        _workerThread = std::thread([this]() { _run_snap_loop(); });
    } else if (mode == "patrol") {
        LOG(INFO) << "[VIDEO] Patrol scheduler mode";
        _workerThread = std::thread([this]() { _run_patrol_loop(); });
    } else if (_config.headless) {
        LOG(INFO) << "[VIDEO] Headless realtime pipeline";
        _workerThread = std::thread([this]() { _run_pipeline_loop(); });
    } else {
        LOG(WARNING) << "[VIDEO] Display mode not supported in production; forcing headless pipeline";
        _workerThread = std::thread([this]() { _run_pipeline_loop(); });
    }

    LOG(INFO) << "[OK] RUNTIME started (non-blocking)";
    return 0;
}

int Detech::stop() {
    _isRun = false;
    if (_pipeline) {
        _pipeline->stop();
    }
    if (_streamForwarder) {
        _streamForwarder->stop();
    }
    if (_snapScheduler) {
        _snapScheduler->stop();
    }
    if (_patrolScheduler) {
        _patrolScheduler->stop();
    }
    return 0;
}

namespace {
RtmpEncoderOptions makeRtmpOpts(const Config& cfg) {
    RtmpEncoderOptions opts;
    opts.preferHw = cfg.preferHwaccel;
    opts.forceSoft = cfg.forceSoftAv;
    opts.gpuDeviceId = cfg.hwaccelDeviceId >= 0 ? cfg.hwaccelDeviceId : cfg.gpuDeviceId;
    opts.nvencPreset = cfg.nvencPreset.empty() ? "p3" : cfg.nvencPreset;
    return opts;
}
}  // namespace

void Detech::_run_forward_loop() {
    _streamForwarder = std::make_unique<runtime::StreamForwarder>(_config, &_metrics);
    _streamForwarder->start();
    _streamForwarder->join();
    _streamForwarder.reset();
    LOG(INFO) << "[FORWARD] Relay loop exited";
}

void Detech::_run_pipeline_loop() {
    _pipeline = std::make_unique<runtime::Pipeline>(
        _config,
        _ffmpegFormatCtx,
        _ffmpegCodecCtx,
        _videoIndex,
        _videoWidth,
        _videoHeight,
        _videoFps,
        yolo_thread_pool,
        &_rtmpEncoder,
        [this](const std::vector<DetectObject>& dets, const std::string& region, const cv::Mat& snapshot) {
            if (_checkAlarmCooldown()) {
                _sendAlarmCallback(dets, region, snapshot);
            }
        },
        [this](int cx, int cy) { return _isInAlarmRegion(cx, cy, _videoWidth, _videoHeight); },
        [this]() { return _streamingEnabled.load(); },
        &_metrics,
        &_hwDecodeState
    );
    _pipeline->start();
    while (_isRun && _pipeline && _pipeline->isRunning()) {
        std::this_thread::sleep_for(std::chrono::milliseconds(200));
    }
    if (_pipeline) {
        _pipeline->stop();
        _pipeline->join();
    }
    // Finite file/VOD exhausted: exit process (Manage waits on s_exit)
    if (_pipeline && _pipeline->endedByEof()) {
        LOG(INFO) << "[VIDEO] Finite media EOF — requesting process shutdown";
        _isRun = false;
        s_exit.store(1, std::memory_order_release);
    }
}

void Detech::_run_snap_loop() {
    _snapScheduler = std::make_unique<runtime::SnapScheduler>(
        _config,
        yolo_thread_pool,
        [this](const std::vector<DetectObject>& dets, const std::string& region,
               const std::string& deviceId, const std::string& deviceName, const cv::Mat& frame) {
            if (_checkAlarmCooldown()) {
                _sendAlarmCallback(dets, region, frame, deviceId, deviceName);
            }
        }
    );
    _snapScheduler->start();
    while (_isRun && _snapScheduler && _snapScheduler->isRunning()) {
        std::this_thread::sleep_for(std::chrono::milliseconds(200));
    }
    if (_snapScheduler) {
        _snapScheduler->stop();
        _snapScheduler->join();
    }
}

void Detech::_run_patrol_loop() {
    _patrolScheduler = std::make_unique<runtime::PatrolScheduler>(
        _config,
        yolo_thread_pool,
        [this](const std::vector<DetectObject>& dets, const std::string& region,
               const std::string& deviceId, const std::string& deviceName, const cv::Mat& frame) {
            if (_checkAlarmCooldown()) {
                _sendAlarmCallback(dets, region, frame, deviceId, deviceName);
            }
        }
    );
    _patrolScheduler->start();
    while (_isRun && _patrolScheduler && _patrolScheduler->isRunning()) {
        std::this_thread::sleep_for(std::chrono::milliseconds(200));
    }
    if (_patrolScheduler) {
        _patrolScheduler->stop();
        _patrolScheduler->join();
    }
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
        if (!_rtmpEncoder->init(_config.rtmpUrl, _videoWidth, _videoHeight, _videoFps,
                                makeRtmpOpts(_config))) {
            LOG(ERROR) << "[STREAMING] Failed to initialize RTMP encoder";
            delete _rtmpEncoder;
            _rtmpEncoder = nullptr;
            return false;
        }
        
        LOG(INFO) << "[STREAMING] RTMP encoder initialized successfully encode_ep="
                  << _rtmpEncoder->encodeEp();
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
    if (!_controlServerRunning.load() && !_controlHttpServer) {
        return;
    }

    LOG(INFO) << "[CONTROL] Stopping control server...";
    _controlServerRunning.store(false);
    if (_controlHttpServer) {
        _controlHttpServer->stop();
    }

    if (_controlServerThread.joinable()) {
        _controlServerThread.join();
    }
    _controlHttpServer = nullptr;
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
        _controlHttpServer = &svr;
        
        // 健康检查接口（含流水线指标）
        svr.Get("/health", [this](const Request& req, Response& res) {
            Json::Value response;
            response["status"] = "ok";
            response["service"] = "RUNTIME Control Server";
            response["task_id"] = this->_config.taskId;
            response["task_type"] = this->_config.taskType;
            response["streaming"] = this->isStreaming();
            Json::Value metrics;
            metrics["packets_in"] = (Json::UInt64)this->_metrics.packetsIn.load();
            metrics["frames_decoded"] = (Json::UInt64)this->_metrics.framesDecoded.load();
            metrics["frames_dropped"] = (Json::UInt64)this->_metrics.framesDropped.load();
            metrics["infer_in"] = (Json::UInt64)this->_metrics.inferIn.load();
            metrics["infer_out"] = (Json::UInt64)this->_metrics.inferOut.load();
            metrics["alarms_emitted"] = (Json::UInt64)this->_metrics.alarmsEmitted.load();
            metrics["last_latency_ms"] = (Json::UInt64)this->_metrics.lastLatencyMs.load();
            if (this->_streamForwarder) {
                metrics["packets_remuxed"] = (Json::UInt64)this->_streamForwarder->packetsRemuxed();
            }
            response["metrics"] = metrics;
            if (yolo_thread_pool) {
                response["infer_ep"] = yolo_thread_pool->inferEp();
                response["model_layout"] = yolo_thread_pool->modelLayout();
            } else {
                response["infer_ep"] = "none";
                response["model_layout"] = "none";
            }
            if (this->_pipeline) {
                response["decode_ep"] = this->_pipeline->decodeEp();
            } else {
                response["decode_ep"] = this->_hwDecodeState.decodeEp.empty()
                    ? "none"
                    : this->_hwDecodeState.decodeEp;
            }
            if (this->_rtmpEncoder && this->_rtmpEncoder->isInitialized()) {
                response["encode_ep"] = this->_rtmpEncoder->encodeEp();
            } else if (this->_streamForwarder) {
                response["encode_ep"] = "copy";
            } else {
                response["encode_ep"] = "none";
            }
            response["prefer_gpu"] = this->_config.preferGpu;
            response["force_cpu"] = this->_config.forceCpu;
            response["gpu_device_id"] = this->_config.gpuDeviceId;
            response["prefer_hwaccel"] = this->_config.preferHwaccel;
            response["force_soft_av"] = this->_config.forceSoftAv;
            
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
        _controlHttpServer = nullptr;
        
    } catch (const std::exception& e) {
        _controlHttpServer = nullptr;
        LOG(ERROR) << "[CONTROL-THREAD] Exception in control server: " << e.what();
    }
    
    LOG(INFO) << "[CONTROL-THREAD] Control server thread exiting";
}

bool Detech::_init_http_client() {
    // cpp-httplib需要"host:port"格式，不是完整URL
    std::string host = "localhost";
    int port = 6000;
    const std::string& hookUrl = !_config.alertHookUrl.empty()
        ? _config.alertHookUrl
        : _config.hookHttpUrl;

    if (!hookUrl.empty()) {
        size_t protocolEnd = hookUrl.find("://");
        if (protocolEnd != std::string::npos) {
            size_t hostStart = protocolEnd + 3;
            size_t portStart = hookUrl.find(":", hostStart);
            size_t pathStart = hookUrl.find("/", hostStart);

            if (portStart != std::string::npos && pathStart != std::string::npos) {
                host = hookUrl.substr(hostStart, portStart - hostStart);
                std::string portStr = hookUrl.substr(portStart + 1, pathStart - portStart - 1);
                port = std::stoi(portStr);
            } else if (pathStart != std::string::npos) {
                host = hookUrl.substr(hostStart, pathStart - hostStart);
            }
        }
    }

    LOG(INFO) << "[INIT] Creating HTTP client for " << host << ":" << port;
    _httpClient = new httplib::Client(host, port);
    _httpClient->set_connection_timeout(5, 0);
    _httpClient->set_read_timeout(5, 0);
    _httpClient->set_write_timeout(5, 0);

    LOG(INFO) << "[INIT] HTTP client created successfully";
    return true;
}

bool Detech::_init_yolo_detector() {
    // Skip YOLO initialization if AI is disabled
    if (!_config.enableAI) {
        LOG(INFO) << "[INIT] AI inference disabled, skipping YOLO initialization";
        return true;
    }
    
    if (!yolo_thread_pool) {
        yolo_thread_pool = new YoloThreadPool();
        
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

        if (!_config.modelClasses.empty()) {
            std::string classFile = _config.modelClasses.begin()->second;
            LOG(INFO) << "[INIT] Classes file: " << classFile;
            std::ifstream ifs(classFile);
            if (ifs.is_open()) {
                std::string line;
                while (std::getline(ifs, line)) {
                    // trim
                    size_t a = line.find_first_not_of(" \t\r\n");
                    if (a == std::string::npos) continue;
                    size_t b = line.find_last_not_of(" \t\r\n");
                    classes.push_back(line.substr(a, b - a + 1));
                }
                LOG(INFO) << "[INIT] Loaded " << classes.size() << " classes from file";
            } else {
                LOG(WARNING) << "[INIT] Cannot open classes file, using default COCO names";
            }
        }
        
        LOG(INFO) << "[INIT] Loading YOLO model with " << _config.threadNums << " threads"
                  << " prefer_gpu=" << (_config.preferGpu ? "true" : "false")
                  << " force_cpu=" << (_config.forceCpu ? "true" : "false")
                  << " gpu_device_id=" << _config.gpuDeviceId;
        int ret = yolo_thread_pool->setUp(
            modelPath, classes, _config.threadNums,
            _config.preferGpu, _config.forceCpu, _config.gpuDeviceId,
            _config.alarmConfidenceThreshold);
        if (ret) {
            LOG(ERROR) << "[ERROR] YOLO thread pool initialization failed, error code: " << ret;
            return false;
        }
        LOG(INFO) << "[OK] YOLO thread pool initialized infer_ep=" << yolo_thread_pool->inferEp()
                  << " layout=" << yolo_thread_pool->modelLayout();
    }
    return true;
}

bool Detech::_init_media_player() {
    LOG(INFO) << "[INIT] Initializing media player"
              << " prefer_hwaccel=" << (_config.preferHwaccel ? "true" : "false")
              << " force_soft_av=" << (_config.forceSoftAv ? "true" : "false")
              << " hwaccel_device_id=" << _config.hwaccelDeviceId;
    if (!_ffmpegFormatCtx) {
        _ffmpegFormatCtx = avformat_alloc_context();
    }
    // RTSP-only options. For rtmp://, FFmpeg treats "timeout" as listen_timeout and
    // implies listen mode — that breaks pull from SRS/ZLM.
    AVDictionary* fmt_options = NULL;
    const std::string& openUrl = _config.rtspUrl;
    const bool isRtsp = openUrl.rfind("rtsp://", 0) == 0 || openUrl.rfind("rtsps://", 0) == 0;
    const bool isRtmp = openUrl.rfind("rtmp://", 0) == 0 || openUrl.rfind("rtmps://", 0) == 0;
    if (isRtsp) {
        av_dict_set(&fmt_options, "rtsp_transport", "tcp", 0);
        av_dict_set(&fmt_options, "stimeout", "3000000", 0);
        av_dict_set(&fmt_options, "timeout", "5000000", 0);
    } else if (isRtmp) {
        av_dict_set(&fmt_options, "rtmp_live", "live", 0);
    }
    int ret = avformat_open_input(&_ffmpegFormatCtx, openUrl.c_str(), NULL, &fmt_options);
    av_dict_free(&fmt_options);
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
        if (!runtime::openVideoDecoder(&_ffmpegCodecCtx, videoCodecPar,
                                       _config.preferHwaccel,
                                       _config.forceSoftAv,
                                       _config.hwaccelDeviceId,
                                       &_hwDecodeState)) {
            LOG(ERROR) << "openVideoDecoder error";
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
        LOG(INFO) << "[OK] Media player ready " << _videoWidth << "x" << _videoHeight
                  << "@" << _videoFps << "fps decode_ep=" << _hwDecodeState.decodeEp;
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
    
    if (!_rtmpEncoder->init(_config.rtmpUrl, _videoWidth, _videoHeight, _videoFps,
                            makeRtmpOpts(_config))) {
        LOG(WARNING) << "[INIT] ⚠️ RTMP encoder initialization failed (ZLMediaKit not running?)";
        LOG(WARNING) << "[INIT] ⚠️ Streaming disabled, but program will continue";
        LOG(WARNING) << "[INIT] ⚠️ You can start streaming later via API when ZLM is ready";
        delete _rtmpEncoder;
        _rtmpEncoder = nullptr;
        _streamingEnabled.store(false);
        return true;  // 不阻止程序启动
    }
    
    // 默认启用推流
    _streamingEnabled.store(true);
    LOG(INFO) << "[OK] RTMP encoder initialized successfully encode_ep="
              << _rtmpEncoder->encodeEp();
    LOG(INFO) << "[OK] Streaming enabled by default (can be controlled via API)";
    
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
    
    if (!AlgoMqttBus::busEnabled(_config)) {
        LOG(WARNING) << "[INIT] Alarm enabled but ALGO_BUS_TRANSPORT disabled";
        return true;
    }
    if (_config.mqttBrokerUrls.empty()) {
        LOG(WARNING) << "[INIT] Alarm enabled but MQTT broker URLs empty "
                     << "(set mqtt_broker_urls / MQTT_BROKER_URLS)";
    }
    
    LOG(INFO) << "[INIT] Alarm callback initialized (MQTT → iot-sink)";
    LOG(INFO) << "  → MQTT brokers: " << _config.mqttBrokerUrls;
    LOG(INFO) << "  → Confidence threshold: " << _config.alarmConfidenceThreshold;
    LOG(INFO) << "  → Cooldown time: " << _config.alarmCooldownTime << "s";
    
    return true;
}

// 检查检测框中心点是否在任何报警区域内（支持归一化 0-10000 坐标）
bool Detech::_isInAlarmRegion(int centerX, int centerY, int frameW, int frameH) {
    if (_config.regions.empty()) {
        return true;
    }

    cv::Point2f center(static_cast<float>(centerX), static_cast<float>(centerY));
    for (const auto& regionPair : _config.regions) {
        for (const auto& polygon : regionPair.second) {
            if (polygon.size() < 3) {
                continue;
            }
            std::vector<cv::Point> scaled;
            scaled.reserve(polygon.size());
            bool looksNormalized = true;
            for (const auto& pt : polygon) {
                if (pt.x > 10000 || pt.y > 10000) {
                    looksNormalized = false;
                    break;
                }
            }
            if (looksNormalized && frameW > 0 && frameH > 0) {
                for (const auto& pt : polygon) {
                    scaled.emplace_back(
                        static_cast<int>(pt.x / 10000.0 * frameW),
                        static_cast<int>(pt.y / 10000.0 * frameH));
                }
            } else {
                scaled = polygon;
            }
            if (cv::pointPolygonTest(scaled, center, false) >= 0) {
                return true;
            }
        }
    }
    return false;
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
    if (!_config.enableAlarm || !AlgoMqttBus::busEnabled(_config)) {
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
        
        // 发送告警：默认 MQTT → iot-sink；ALGO_BUS_TRANSPORT=http 时回退 VIDEO hook
        try {
            const std::string ts = formatUtcNow();
            std::string primaryObject = alarmData.detections.empty()
                ? "object"
                : alarmData.detections.front().class_name;

            Json::Value root;
            root["object"] = primaryObject;
            root["event"] = _config.algorithmName.empty() ? "detection" : _config.algorithmName;
            const std::string did = !alarmData.deviceId.empty() ? alarmData.deviceId : _config.deviceId;
            const std::string dname = !alarmData.deviceName.empty()
                ? alarmData.deviceName
                : (_config.deviceName.empty() ? did : _config.deviceName);
            root["device_id"] = did;
            root["device_name"] = dname;
            root["task_type"] = _config.taskType.empty() ? "realtime" : _config.taskType;
            root["correlation_id"] = (_config.taskId.empty() ? "runtime" : _config.taskId) + "_" + ts;
            root["time"] = ts;
            root["image_path"] = alarmData.imagePath;
            root["region"] = alarmData.regionName;
            if (!_config.taskId.empty()) {
                root["task_id"] = _config.taskId;
            }

            Json::Value info;
            info["task_id"] = _config.taskId;
            info["region"] = alarmData.regionName;
            info["detection_count"] = static_cast<int>(alarmData.detections.size());
            info["runtime_ts_ms"] = (Json::Value::UInt64)alarmData.timestamp;
            Json::Value detectionsArray(Json::arrayValue);
            for (const auto& det : alarmData.detections) {
                Json::Value detObj;
                detObj["class_name"] = det.class_name;
                detObj["confidence"] = det.class_score;
                detObj["class_id"] = det.class_id;
                Json::Value bbox(Json::arrayValue);
                bbox.append(static_cast<int>(det.x1));
                bbox.append(static_cast<int>(det.y1));
                bbox.append(static_cast<int>(det.x2));
                bbox.append(static_cast<int>(det.y2));
                detObj["bbox"] = bbox;
                detectionsArray.append(detObj);
            }
            info["detections"] = detectionsArray;
            Json::StreamWriterBuilder compact;
            compact["indentation"] = "";
            root["information"] = Json::writeString(compact, info);

            Json::StreamWriterBuilder writer;
            writer["indentation"] = "";
            std::string jsonStr = Json::writeString(writer, root);

            const bool snapshot = (_config.taskType == "snap" || _config.taskType == "snapshot");
            if (!AlgoMqttBus::busEnabled(_config)) {
                LOG(ERROR) << "[ALARM-THREAD] ALGO_BUS_TRANSPORT disabled; alert dropped (HTTP hook removed)";
            } else if (AlgoMqttBus::publishAlert(_config, jsonStr, snapshot)) {
                LOG(INFO) << "[ALARM-THREAD] MQTT alert published device=" << did;
            } else {
                LOG(ERROR) << "[ALARM-THREAD] MQTT alert publish failed device=" << did;
            }
        } catch (const std::exception& e) {
            LOG(ERROR) << "[ALARM-THREAD] Exception while sending alarm: " << e.what();
        }
    }
    
    LOG(INFO) << "[ALARM-THREAD] Alarm sender thread exiting gracefully";
}

void Detech::_startHeartbeatThread() {
    if (_config.heartbeatUrl.empty()) {
        LOG(INFO) << "[HEARTBEAT] heartbeat_url not set, heartbeat disabled";
        return;
    }
    if (_heartbeatRunning.load()) {
        return;
    }
    _heartbeatRunning.store(true);
    _heartbeatThread = std::thread(&Detech::_heartbeatThreadFunc, this);
    LOG(INFO) << "[HEARTBEAT] thread started -> " << _config.heartbeatUrl;
}

void Detech::_stopHeartbeatThread() {
    if (!_heartbeatRunning.load()) {
        return;
    }
    _heartbeatRunning.store(false);
    if (_heartbeatThread.joinable()) {
        _heartbeatThread.join();
    }
    LOG(INFO) << "[HEARTBEAT] thread stopped";
}

void Detech::_heartbeatThreadFunc() {
    std::string host;
    int port = 80;
    std::string path = "/video/algorithm/heartbeat/realtime";
    if (!parseHttpUrl(_config.heartbeatUrl, host, port, path)) {
        LOG(ERROR) << "[HEARTBEAT] invalid URL: " << _config.heartbeatUrl;
        return;
    }
    httplib::Client client(host, port);
    client.set_connection_timeout(3, 0);
    client.set_read_timeout(3, 0);
    client.set_write_timeout(3, 0);

    int interval = _config.heartbeatIntervalSec > 0 ? _config.heartbeatIntervalSec : 10;
    while (_heartbeatRunning.load() && _isRun) {
        try {
            Json::Value root;
            int taskIdNum = 0;
            try {
                taskIdNum = std::stoi(_config.taskId);
            } catch (...) {
                taskIdNum = 0;
            }
            root["task_id"] = taskIdNum;
            root["server_ip"] = "127.0.0.1";
            root["port"] = _config.controlPort;
            root["process_id"] = static_cast<int>(::getpid());
            root["log_path"] = _config.logPath;
            if (_patrolScheduler) {
                root["total_patrols"] = (Json::UInt64)_patrolScheduler->totalPatrols.load();
                root["total_detections"] = (Json::UInt64)_patrolScheduler->totalDetections.load();
            }
            Json::StreamWriterBuilder writer;
            writer["indentation"] = "";
            std::string body = Json::writeString(writer, root);
            auto res = client.Post(path.c_str(), body, "application/json");
            if (!(res && res->status == 200)) {
                LOG(WARNING) << "[HEARTBEAT] post failed status="
                             << (res ? res->status : -1);
            }
        } catch (const std::exception& e) {
            LOG(WARNING) << "[HEARTBEAT] exception: " << e.what();
        }
        for (int i = 0; i < interval * 10 && _heartbeatRunning.load() && _isRun; ++i) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    }
}

std::string Detech::_saveAlertImage(const cv::Mat& frame) {
    if (frame.empty()) {
        return "";
    }
    std::string dir = _config.alertImageDir;
    if (dir.empty()) {
        dir = "alerts";
    }
    ::mkdir(dir.c_str(), 0755);
    std::ostringstream name;
    name << dir << "/alert_" << _config.taskId << "_" << _get_curtime_stamp_ms() << ".jpg";
    try {
        cv::Mat out = frame;
        if (out.cols > 640) {
            double scale = 640.0 / out.cols;
            cv::resize(frame, out, cv::Size(), scale, scale);
        }
        if (cv::imwrite(name.str(), out)) {
            return name.str();
        }
    } catch (...) {
    }
    return "";
}

// 发送告警回调（入队；可选落盘截图）
void Detech::_sendAlarmCallback(const std::vector<DetectObject>& detections,
                                const std::string& regionName,
                                const cv::Mat& frame,
                                const std::string& deviceId,
                                const std::string& deviceName) {
    if (!_config.enableAlarm) {
        return;
    }
    if (!AlgoMqttBus::busEnabled(_config)) {
        return;
    }
    if (!_alarmThreadRunning.load()) {
        LOG(WARNING) << "[ALARM] Alarm sender thread not running, alarm dropped";
        return;
    }

    std::string imagePath = _saveAlertImage(frame);

    {
        std::lock_guard<std::mutex> lock(_alarmQueueMutex);
        if (_alarmQueue.size() >= MAX_ALARM_QUEUE_SIZE) {
            _alarmQueue.pop();
        }
        AlarmData alarmData(detections, regionName, _get_curtime_stamp_ms(), imagePath, deviceId, deviceName);
        _alarmQueue.push(std::move(alarmData));
        LOG(INFO) << "[ALARM] Alarm enqueued, queue size: " << _alarmQueue.size();
    }
    _alarmQueueCV.notify_one();
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
        
        if (_config.enableAI && yolo_thread_pool) {
            // Submit task every N frames to avoid queue buildup
            if (aiFrameInterval % SUBMIT_INTERVAL == 0) {
                yolo_thread_pool->submitTask(img, 0, frameCount);
                lastSubmittedFrameId = frameCount;
            }
            aiFrameInterval++;
            
            // Try to get any available result (non-blocking)
            bool foundNewResult = false;
            for (int checkFrame = lastSubmittedFrameId; checkFrame >= 0 && checkFrame >= lastSubmittedFrameId - 30; checkFrame--) {
                int ret = yolo_thread_pool->getTargetResultNonBlock(detections, 0, checkFrame);
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
                    bool inAlarmRegion = _isInAlarmRegion(centerX, centerY, img.cols, img.rows);
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
                    _sendAlarmCallback(alarmDetections, regionName, img);
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
