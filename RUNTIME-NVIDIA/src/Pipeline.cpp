#include "Pipeline.h"

extern "C" {
#include <libavcodec/avcodec.h>
#include <libavutil/hwcontext.h>
}

#include <cuda_runtime_api.h>
#include <json/json.h>

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <unistd.h>

#include <algorithm>
#include <chrono>
#include <ctime>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <utility>

namespace easyaiot::nvidia {
namespace {

std::string compactJson(const Json::Value& value) {
    Json::StreamWriterBuilder builder;
    builder["indentation"] = "";
    return Json::writeString(builder, value);
}

void checkCuda(cudaError_t code, const char* operation) {
    if (code != cudaSuccess) {
        throw std::runtime_error(std::string(operation) + ": " + cudaGetErrorString(code));
    }
}
}  // namespace

Pipeline::Pipeline(RuntimeConfig config)
    : config_(std::move(config)), eventBus_(config_),
      decodeRing_(static_cast<std::size_t>(config_.decodeQueueDepth)),
      resultRing_(static_cast<std::size_t>(config_.resultQueueDepth)) {
    for (const auto& model : config_.models) {
        models_.push_back(std::make_unique<TensorRtModel>(
            config_.cudaDevice, model, config_.confidence, config_.nmsThreshold));
        preallocatedBytes_ += models_.back()->engineBytes();
    }
    for (int index = 0; index < config_.inferStreams; ++index) {
        auto lane = std::make_unique<Lane>();
        lane->id = index;
        lane->queue = std::make_unique<BoundedRing<DeviceFrame>>(
            static_cast<std::size_t>(config_.inferQueueDepth));
        for (auto& model : models_) {
            lane->sessions.push_back(model->createSession(config_.cudaGraph));
            preallocatedBytes_ += lane->sessions.back()->allocatedBytes();
        }
        lanes_.push_back(std::move(lane));
    }
}

Pipeline::~Pipeline() { stop(); }

void Pipeline::validateHardware() {
    int devices = 0;
    checkCuda(cudaGetDeviceCount(&devices), "query CUDA devices");
    if (config_.cudaDevice >= devices) throw std::runtime_error("configured CUDA device does not exist");
    checkCuda(cudaSetDevice(config_.cudaDevice), "select CUDA device");
    cudaDeviceProp properties{};
    checkCuda(cudaGetDeviceProperties(&properties, config_.cudaDevice), "query CUDA device properties");
    gpuName_ = properties.name;
    computeMajor_ = properties.major;
    computeMinor_ = properties.minor;
    if (av_hwdevice_find_type_by_name("cuda") == AV_HWDEVICE_TYPE_NONE) {
        throw std::runtime_error("FFmpeg CUDA hardware context is unavailable; software fallback is forbidden");
    }
    // The exact decoder is selected after probing the RTSP codec. Some NVIDIA
    // FFmpeg builds expose *_cuvid names, others expose CUDA hw-config on the
    // standard decoder; NvDecoder accepts either only when AV_PIX_FMT_CUDA is
    // actually negotiated.
}

void Pipeline::start() {
    bool expected = false;
    if (!started_.compare_exchange_strong(expected, true)) return;
    validateHardware();
    running_.store(true);
    startedAt_ = std::chrono::steady_clock::now();
    for (auto& lane : lanes_) {
        lane->worker = std::thread([this, pointer = lane.get()] { inferLoop(*pointer); });
    }
    decodeThread_ = std::thread(&Pipeline::decodeLoop, this);
    dispatchThread_ = std::thread(&Pipeline::dispatchLoop, this);
    emitThread_ = std::thread(&Pipeline::emitLoop, this);
    heartbeatThread_ = std::thread(&Pipeline::heartbeatLoop, this);
    controlThread_ = std::thread(&Pipeline::controlLoop, this);
}

void Pipeline::stop() {
    if (!started_.load()) return;
    running_.store(false);
    decodeRing_.close();
    for (auto& lane : lanes_) lane->queue->close();
    resultRing_.close();
    if (decodeThread_.joinable()) decodeThread_.join();
    if (dispatchThread_.joinable()) dispatchThread_.join();
    for (auto& lane : lanes_) if (lane->worker.joinable()) lane->worker.join();
    if (emitThread_.joinable()) emitThread_.join();
    if (heartbeatThread_.joinable()) heartbeatThread_.join();
    if (controlThread_.joinable()) controlThread_.join();
}

void Pipeline::decodeLoop() {
    try {
        NvDecoder decoder(config_.source, config_.cudaDevice, config_.decoderSurfaces);
        while (running_.load()) {
            DeviceFrame frame = decoder.next();
            metrics_.decoded.fetch_add(1);
            if ((frame.sequence - 1) % static_cast<std::uint64_t>(config_.frameSkip) != 0) continue;
            bool dropped = false;
            if (decodeRing_.pushDropOldest(std::move(frame), &dropped) && dropped) {
                metrics_.decodeDrops.fetch_add(1);
            }
        }
    } catch (const std::exception& error) {
        metrics_.errors.fetch_add(1);
        std::cerr << "[NVIDIA NVDEC] " << error.what() << '\n';
        running_.store(false);
        decodeRing_.close();
    }
}

void Pipeline::dispatchLoop() {
    std::size_t nextLane = 0;
    while (running_.load() || decodeRing_.size() > 0) {
        DeviceFrame frame;
        if (!decodeRing_.pop(frame)) continue;
        auto& lane = *lanes_[nextLane++ % lanes_.size()];
        bool dropped = false;
        if (lane.queue->pushDropOldest(std::move(frame), &dropped)) {
            metrics_.dispatched.fetch_add(1);
            if (dropped) metrics_.inferDrops.fetch_add(1);
        }
    }
    for (auto& lane : lanes_) lane->queue->close();
}

void Pipeline::inferLoop(Lane& lane) {
    while (running_.load() || lane.queue->size() > 0) {
        DeviceFrame frame;
        if (!lane.queue->pop(frame)) continue;
        const auto started = std::chrono::steady_clock::now();
        try {
            std::vector<Detection> detections;
            for (auto& session : lane.sessions) {
                auto output = session->infer(frame);
                detections.insert(detections.end(),
                                  std::make_move_iterator(output.begin()),
                                  std::make_move_iterator(output.end()));
            }
            const double elapsed = std::chrono::duration<double, std::milli>(
                std::chrono::steady_clock::now() - started).count();
            metrics_.lastInferenceMs.store(elapsed);
            metrics_.inferred.fetch_add(1);
            metrics_.detections.fetch_add(detections.size());
            FrameResult result{frame.sequence, std::move(detections), lane.id, elapsed};
            // Release the NVDEC surface before the result/event queue. No frame pixels
            // cross the GPU hot-path boundary.
            frame.frame.reset();
            bool dropped = false;
            if (resultRing_.pushDropOldest(std::move(result), &dropped) && dropped) {
                metrics_.resultDrops.fetch_add(1);
            }
        } catch (const std::exception& error) {
            metrics_.errors.fetch_add(1);
            std::cerr << "[NVIDIA TensorRT lane " << lane.id << "] " << error.what() << '\n';
            running_.store(false);
            break;
        }
    }
}

std::string Pipeline::makeAlertJson(const FrameResult& result) const {
    Json::Value detections(Json::arrayValue);
    for (const auto& detection : result.detections) {
        Json::Value item;
        item["class_name"] = detection.className;
        item["confidence"] = detection.score;
        item["class_id"] = detection.classId;
        item["model_id"] = detection.modelId;
        Json::Value box(Json::arrayValue);
        box.append(static_cast<int>(detection.x1));
        box.append(static_cast<int>(detection.y1));
        box.append(static_cast<int>(detection.x2));
        box.append(static_cast<int>(detection.y2));
        item["bbox"] = box;
        detections.append(std::move(item));
    }
    Json::Value information;
    information["task_id"] = config_.taskId;
    information["runtime"] = "nvdec-cuda-tensorrt-graph";
    information["cuda_device"] = config_.cudaDevice;
    information["lane"] = result.lane;
    information["inference_ms"] = result.inferenceMs;
    information["detections"] = std::move(detections);
    Json::Value alert;
    alert["object"] = result.detections.empty() ? "object" : result.detections.front().className;
    alert["event"] = config_.algorithmName;
    alert["device_id"] = config_.deviceIdText;
    alert["device_name"] = config_.deviceName;
    alert["task_type"] = "realtime";
    alert["task_id"] = config_.taskId;
    alert["correlation_id"] = std::to_string(config_.taskId) + "_" + std::to_string(result.sequence);
    alert["time"] = nowIso();
    alert["image_path"] = "";
    alert["region"] = "";
    alert["information"] = compactJson(information);
    return compactJson(alert);
}

void Pipeline::emitLoop() {
    while (running_.load() || resultRing_.size() > 0) {
        FrameResult result;
        if (!resultRing_.pop(result)) continue;
        if (!config_.enableAlarm || result.detections.empty()) continue;
        const auto now = std::chrono::steady_clock::now();
        if (lastAlertAt_ != std::chrono::steady_clock::time_point{} &&
            now - lastAlertAt_ < std::chrono::seconds(config_.cooldownSec)) continue;
        lastAlertAt_ = now;
        if (eventBus_.publishAlert(makeAlertJson(result))) metrics_.alerts.fetch_add(1);
    }
}

void Pipeline::heartbeatLoop() {
    while (running_.load()) {
        Json::Value stream;
        stream["device_id"] = config_.deviceIdText;
        stream["status"] = "running";
        stream["source_mode"] = "nvdec-cuda-tensorrt";
        stream["stream_key"] = "task_" + std::to_string(config_.taskId) + "_" + config_.deviceIdText;
        stream["last_frame_time"] = static_cast<Json::Int64>(std::time(nullptr));
        Json::Value streams(Json::arrayValue);
        streams.append(std::move(stream));
        Json::Value heartbeat;
        heartbeat["task_id"] = config_.taskId;
        heartbeat["port"] = config_.controlPort;
        heartbeat["process_id"] = static_cast<int>(::getpid());
        heartbeat["log_path"] = config_.logPath;
        heartbeat["runtime_target"] = "nvidia";
        heartbeat["stream_runtime"] = std::move(streams);
        heartbeat["total_frames"] = static_cast<Json::UInt64>(metrics_.inferred.load());
        heartbeat["total_detections"] = static_cast<Json::UInt64>(metrics_.detections.load());
        eventBus_.postHeartbeat(compactJson(heartbeat));
        for (int tick = 0; tick < config_.heartbeatIntervalSec * 10 && running_.load(); ++tick) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    }
}

std::string Pipeline::healthJson() const {
    Json::Value root;
    root["status"] = running_.load() ? "ok" : "stopping";
    root["runtime"] = "RUNTIME-NVIDIA";
    root["target"] = "nvidia";
    root["gpu"] = gpuName_;
    root["compute_capability"] = std::to_string(computeMajor_) + "." + std::to_string(computeMinor_);
    root["decode_ep"] = "nvdec-cuda-surface";
    root["preprocess_ep"] = "cuda-nv12-letterbox";
    root["infer_ep"] = "tensorrt-enqueue-v3";
    root["cuda_graph"] = config_.cudaGraph;
    root["infer_streams"] = config_.inferStreams;
    root["preallocated_bytes"] = static_cast<Json::UInt64>(preallocatedBytes_);
    root["uptime_sec"] = static_cast<Json::Int64>(std::chrono::duration_cast<std::chrono::seconds>(
        std::chrono::steady_clock::now() - startedAt_).count());
    root["decoded"] = static_cast<Json::UInt64>(metrics_.decoded.load());
    root["inferred"] = static_cast<Json::UInt64>(metrics_.inferred.load());
    root["detections"] = static_cast<Json::UInt64>(metrics_.detections.load());
    root["alerts"] = static_cast<Json::UInt64>(metrics_.alerts.load());
    root["decode_drops"] = static_cast<Json::UInt64>(metrics_.decodeDrops.load());
    root["infer_drops"] = static_cast<Json::UInt64>(metrics_.inferDrops.load());
    root["result_drops"] = static_cast<Json::UInt64>(metrics_.resultDrops.load());
    root["errors"] = static_cast<Json::UInt64>(metrics_.errors.load());
    root["last_inference_ms"] = metrics_.lastInferenceMs.load();
    return compactJson(root);
}

void Pipeline::controlLoop() {
    const int server = ::socket(AF_INET, SOCK_STREAM, 0);
    if (server < 0) return;
    int reuse = 1;
    setsockopt(server, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));
    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = htonl(INADDR_ANY);
    address.sin_port = htons(static_cast<std::uint16_t>(config_.controlPort));
    if (::bind(server, reinterpret_cast<sockaddr*>(&address), sizeof(address)) != 0 ||
        ::listen(server, 8) != 0) {
        ::close(server);
        return;
    }
    while (running_.load()) {
        fd_set set;
        FD_ZERO(&set);
        FD_SET(server, &set);
        timeval timeout{0, 250000};
        if (::select(server + 1, &set, nullptr, nullptr, &timeout) <= 0) continue;
        const int client = ::accept(server, nullptr, nullptr);
        if (client < 0) continue;
        char request[2048]{};
        const auto count = ::recv(client, request, sizeof(request) - 1, 0);
        const std::string line = count > 0 ? std::string(request, static_cast<std::size_t>(count)) : "";
        const bool stopRequested = line.rfind("POST /stop", 0) == 0;
        const bool known = line.rfind("GET /health", 0) == 0 ||
                           line.rfind("GET /metrics", 0) == 0 || stopRequested;
        const std::string body = known ? healthJson() : "{\"error\":\"not found\"}";
        const std::string response = "HTTP/1.1 " + std::string(known ? "200 OK" : "404 Not Found") +
            "\r\nContent-Type: application/json\r\nConnection: close\r\nContent-Length: " +
            std::to_string(body.size()) + "\r\n\r\n" + body;
        ::send(client, response.data(), response.size(), MSG_NOSIGNAL);
        ::close(client);
        if (stopRequested) running_.store(false);
    }
    ::close(server);
}

std::string Pipeline::nowIso() {
    const auto now = std::chrono::system_clock::now();
    const auto time = std::chrono::system_clock::to_time_t(now);
    std::tm value{};
    gmtime_r(&time, &value);
    std::ostringstream output;
    output << std::put_time(&value, "%Y-%m-%dT%H:%M:%SZ");
    return output.str();
}

}  // namespace easyaiot::nvidia
