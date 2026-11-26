#include "Pipeline.h"

extern "C" {
#include <libavcodec/avcodec.h>
}

#include <json/json.h>
#include <opencv2/imgcodecs.hpp>

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <unistd.h>

#include <algorithm>
#include <chrono>
#include <csignal>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>

namespace easyaiot::bm1688 {
namespace {

std::string compactJson(const Json::Value& value) {
    Json::StreamWriterBuilder builder;
    builder["indentation"] = "";
    return Json::writeString(builder, value);
}

}  // namespace

Pipeline::Pipeline(RuntimeConfig config)
    : config_(std::move(config)), eventBus_(config_),
      decodeRing_(static_cast<std::size_t>(config_.decodeQueueDepth)),
      resultRing_(static_cast<std::size_t>(config_.resultQueueDepth)) {
    for (int core : config_.coreIds) {
        auto lane = std::make_unique<Lane>();
        lane->coreId = core;
        lane->queue = std::make_unique<BoundedRing<FramePacket>>(
            static_cast<std::size_t>(config_.inferQueueDepth));
        for (const auto& model : config_.models) {
            lane->engines.push_back(std::make_unique<SophonEngine>(
                config_.deviceId, core, model, config_.confidence, config_.nmsThreshold));
        }
        lanes_.push_back(std::move(lane));
    }
}

Pipeline::~Pipeline() { stop(); }

void Pipeline::validateHardware() const {
    if (!avcodec_find_decoder_by_name("h264_bm") || !avcodec_find_decoder_by_name("hevc_bm")) {
        throw std::runtime_error(
            "Sophon FFmpeg h264_bm/hevc_bm decoder is unavailable; software decode fallback is forbidden");
    }
    if (config_.enableRtmp && !avcodec_find_encoder_by_name("h264_bm")) {
        throw std::runtime_error(
            "Sophon FFmpeg h264_bm encoder is unavailable; software encode fallback is forbidden");
    }
}

void Pipeline::start() {
    bool expected = false;
    if (!started_.compare_exchange_strong(expected, true)) return;
    validateHardware();
    for (auto& lane : lanes_) {
        for (auto& engine : lane->engines) engine->initialize();
    }
    running_.store(true);
    startedAt_ = std::chrono::steady_clock::now();
    for (auto& lane : lanes_) {
        lane->worker = std::thread([this, ptr = lane.get()] { inferLoop(*ptr); });
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

void Pipeline::wait() {
    while (running_.load()) std::this_thread::sleep_for(std::chrono::milliseconds(200));
    stop();
}

void Pipeline::decodeLoop() {
    try {
        cv::VideoCapture capture;
        // SOPHON OpenCV's third argument selects the BM device. CAP_PROP_OUTPUT_YUV
        // keeps the hardware-decoded frame in device memory for cv::bmcv::toBMI.
        capture.open(config_.source, cv::CAP_FFMPEG, config_.deviceId);
        if (!capture.isOpened()) throw std::runtime_error("Sophon VideoCapture open failed");
        capture.set(cv::CAP_PROP_OUTPUT_SRC, 1.0);
        capture.set(cv::CAP_PROP_OUTPUT_YUV, cv::PROP_TRUE);
        std::uint64_t sequence = 0;
        int consecutiveFailures = 0;
        while (running_.load()) {
            cv::Mat image;
            if (!capture.read(image) || image.empty()) {
                if (++consecutiveFailures > 200) {
                    throw std::runtime_error("hardware decoder stopped producing frames");
                }
                std::this_thread::sleep_for(std::chrono::milliseconds(10));
                continue;
            }
            consecutiveFailures = 0;
            ++sequence;
            metrics_.decoded.fetch_add(1);
            if ((sequence - 1) % static_cast<std::uint64_t>(config_.frameSkip) != 0) continue;
            FramePacket frame{sequence, std::chrono::steady_clock::now(), std::move(image)};
            bool dropped = false;
            if (decodeRing_.pushDropOldest(std::move(frame), &dropped) && dropped) {
                metrics_.decodeDrops.fetch_add(1);
            }
        }
        capture.release();
    } catch (const std::exception& error) {
        metrics_.errors.fetch_add(1);
        std::cerr << "[BM1688 decode] " << error.what() << '\n';
        running_.store(false);
        decodeRing_.close();
    }
}

void Pipeline::dispatchLoop() {
    std::size_t laneIndex = 0;
    while (running_.load() || decodeRing_.size() > 0) {
        FramePacket frame;
        if (!decodeRing_.pop(frame)) continue;
        auto& lane = *lanes_[laneIndex++ % lanes_.size()];
        bool dropped = false;
        if (lane.queue->pushDropOldest(std::move(frame), &dropped)) {
            metrics_.dispatched.fetch_add(1);
            if (dropped) metrics_.inferDrops.fetch_add(1);
        }
    }
    for (auto& lane : lanes_) lane->queue->close();
}

void Pipeline::inferLoop(Lane& lane) {
    std::size_t maxBatch = 1;
    for (const auto& engine : lane.engines) {
        maxBatch = std::max(maxBatch, static_cast<std::size_t>(engine->batchSize()));
    }
    while (running_.load() || lane.queue->size() > 0) {
        FramePacket first;
        if (!lane.queue->pop(first)) continue;
        std::vector<FramePacket> packets;
        packets.reserve(maxBatch);
        packets.push_back(std::move(first));
        while (packets.size() < maxBatch) {
            FramePacket next;
            if (!lane.queue->pop(next, std::chrono::milliseconds(1))) break;
            packets.push_back(std::move(next));
        }

        std::vector<std::vector<Detection>> merged(packets.size());
        const auto started = std::chrono::steady_clock::now();
        try {
            for (auto& engine : lane.engines) {
                const std::size_t engineBatch = static_cast<std::size_t>(engine->batchSize());
                for (std::size_t offset = 0; offset < packets.size(); offset += engineBatch) {
                    const std::size_t count = std::min(engineBatch, packets.size() - offset);
                    std::vector<cv::Mat> images;
                    images.reserve(count);
                    for (std::size_t i = 0; i < count; ++i) images.push_back(packets[offset + i].image);
                    auto outputs = engine->infer(images);
                    for (std::size_t i = 0; i < outputs.size(); ++i) {
                        auto& target = merged[offset + i];
                        target.insert(target.end(), outputs[i].begin(), outputs[i].end());
                    }
                }
            }
        } catch (const std::exception& error) {
            metrics_.errors.fetch_add(1);
            std::cerr << "[BM1688 infer core " << lane.coreId << "] " << error.what() << '\n';
            running_.store(false);
            break;
        }
        const double elapsed = std::chrono::duration<double, std::milli>(
            std::chrono::steady_clock::now() - started).count();
        metrics_.lastInferenceMs.store(elapsed);
        for (std::size_t i = 0; i < packets.size(); ++i) {
            metrics_.inferred.fetch_add(1);
            metrics_.detections.fetch_add(merged[i].size());
            FrameResult result{std::move(packets[i]), std::move(merged[i]), lane.coreId, elapsed};
            bool dropped = false;
            if (resultRing_.pushDropOldest(std::move(result), &dropped) && dropped) {
                metrics_.resultDrops.fetch_add(1);
            }
        }
    }
}

std::string Pipeline::saveAlertImage(const FrameResult& result) const {
    if (config_.alertImageDir.empty()) return {};
    try {
        std::filesystem::create_directories(config_.alertImageDir);
        const std::string path = config_.alertImageDir + "/bm1688_" +
            std::to_string(config_.taskId) + "_" + std::to_string(result.frame.sequence) + ".jpg";
        if (cv::imwrite(path, result.frame.image)) return path;
    } catch (const std::exception& error) {
        std::cerr << "[BM1688 alert image] " << error.what() << '\n';
    }
    return {};
}

std::string Pipeline::makeAlertJson(const FrameResult& result, const std::string& imagePath) const {
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
        detections.append(item);
    }
    Json::Value information;
    information["task_id"] = config_.taskId;
    information["detection_count"] = static_cast<Json::UInt64>(result.detections.size());
    information["runtime"] = "bmrt-bm1688-2core-ring";
    information["core_id"] = result.coreId;
    information["inference_ms"] = result.inferenceMs;
    information["detections"] = detections;

    Json::Value alert;
    alert["object"] = result.detections.empty() ? "object" : result.detections.front().className;
    alert["event"] = config_.algorithmName;
    alert["device_id"] = config_.deviceIdText;
    alert["device_name"] = config_.deviceName;
    alert["task_type"] = config_.taskType;
    alert["task_id"] = config_.taskId;
    alert["correlation_id"] = std::to_string(config_.taskId) + "_" + std::to_string(result.frame.sequence);
    alert["time"] = nowIso();
    alert["image_path"] = imagePath;
    alert["region"] = "";
    alert["information"] = compactJson(information);
    return compactJson(alert);
}

void Pipeline::emitLoop() {
    cv::VideoWriter writer;
    if (config_.enableRtmp && !config_.rtmpUrl.empty()) {
        writer.open(config_.rtmpUrl, cv::CAP_FFMPEG,
                    cv::VideoWriter::fourcc('H', '2', '6', '4'),
                    config_.fps, cv::Size(config_.width, config_.height), true);
        if (!writer.isOpened()) {
            metrics_.errors.fetch_add(1);
            std::cerr << "[BM1688 encode] h264_bm VideoWriter open failed\n";
            running_.store(false);
            return;
        }
    }
    while (running_.load() || resultRing_.size() > 0) {
        FrameResult result;
        if (!resultRing_.pop(result)) continue;
        if (writer.isOpened()) writer.write(result.frame.image);
        if (!config_.enableAlarm || result.detections.empty()) continue;
        const auto now = std::chrono::steady_clock::now();
        if (lastAlertAt_ != std::chrono::steady_clock::time_point{} &&
            now - lastAlertAt_ < std::chrono::seconds(config_.cooldownSec)) continue;
        lastAlertAt_ = now;
        const std::string imagePath = saveAlertImage(result);
        if (eventBus_.publishAlert(makeAlertJson(result, imagePath), config_.taskType == "snap")) {
            metrics_.alerts.fetch_add(1);
        }
    }
    writer.release();
}

void Pipeline::heartbeatLoop() {
    while (running_.load()) {
        Json::Value stream;
        stream["device_id"] = config_.deviceIdText;
        stream["status"] = "running";
        stream["source_mode"] = "bm1688-vpu-bmrt";
        stream["stream_key"] = "task_" + std::to_string(config_.taskId) + "_" + config_.deviceIdText;
        stream["last_frame_time"] = static_cast<Json::Int64>(std::time(nullptr));
        Json::Value streams(Json::arrayValue);
        streams.append(stream);
        Json::Value heartbeat;
        heartbeat["task_id"] = config_.taskId;
        heartbeat["port"] = config_.controlPort;
        heartbeat["process_id"] = static_cast<int>(::getpid());
        heartbeat["log_path"] = config_.logPath;
        heartbeat["runtime_target"] = "bm1688";
        heartbeat["stream_runtime"] = streams;
        heartbeat["total_frames"] = static_cast<Json::UInt64>(metrics_.inferred.load());
        heartbeat["total_detections"] = static_cast<Json::UInt64>(metrics_.detections.load());
        eventBus_.postHeartbeat(compactJson(heartbeat));
        for (int tenth = 0; tenth < config_.heartbeatIntervalSec * 10 && running_.load(); ++tenth) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    }
}

std::string Pipeline::healthJson() const {
    Json::Value root;
    root["status"] = running_.load() ? "ok" : "stopping";
    root["runtime"] = "RUNTIME-BM1688";
    root["target"] = "bm1688";
    root["decode_ep"] = "sophon-vpu";
    root["preprocess_ep"] = "bmcv-vpp";
    root["infer_ep"] = "bmrt-2core";
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
        const bool known = line.rfind("GET /health", 0) == 0 || line.rfind("GET /metrics", 0) == 0 || stopRequested;
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
    std::tm tm{};
    gmtime_r(&time, &tm);
    std::ostringstream out;
    out << std::put_time(&tm, "%Y-%m-%dT%H:%M:%SZ");
    return out.str();
}

}  // namespace easyaiot::bm1688
