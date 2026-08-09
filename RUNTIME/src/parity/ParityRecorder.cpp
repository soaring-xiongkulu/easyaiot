#include "parity/ParityRecorder.h"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <glog/logging.h>
#include <json/json.h>
#include <map>
#include <set>

namespace runtime {

void ParityRecorder::recordMotionSample(int frameIndex, const MotionResult& result, bool inferSkipped) {
    MotionSample sample;
    sample.frameIndex = frameIndex;
    sample.triggered = result.triggered;
    sample.reason = result.reason;
    sample.score = result.score;
    sample.changedAreaRatio = result.changedAreaRatio;
    sample.inferSkipped = inferSkipped;
    motionSamples_.push_back(sample);
    samplesSinceFlush_ += 1;
}

void ParityRecorder::recordTrackSample(int frameIndex, const std::vector<DetectObject>& detections) {
    ParityTrackFrame frame;
    frame.frameIndex = frameIndex;
    frame.detections = detections;
    trackFrames_.push_back(frame);
    samplesSinceFlush_ += 1;
}

void ParityRecorder::recordScheduleEvent(const std::string& kind,
                                         const std::string& deviceId,
                                         const std::string& slotKey,
                                         std::time_t unixTs) {
    ScheduleEvent ev;
    ev.kind = kind;
    ev.deviceId = deviceId;
    ev.slotKey = slotKey;
    ev.unixTs = unixTs;
    scheduleEvents_.push_back(ev);
    samplesSinceFlush_ += 1;
}

void ParityRecorder::recordOverlaySample(int frameIndex, double latencyMs, int boxCount, bool drawn) {
    OverlaySample sample;
    sample.frameIndex = frameIndex;
    sample.latencyMs = latencyMs;
    sample.boxCount = boxCount;
    sample.drawn = drawn;
    overlaySamples_.push_back(sample);
    samplesSinceFlush_ += 1;
}

void ParityRecorder::setStreamMeta(const std::string& rtmpUrl, int width, int height, int fps, int bitrateKbps,
                                   const std::string& codecName,
                                   const std::string& qualityProfile,
                                   bool nvencRequested,
                                   bool nvencFallback,
                                   bool qualityDowngraded) {
    streamRtmpUrl_ = rtmpUrl;
    streamWidth_ = width;
    streamHeight_ = height;
    streamFps_ = fps;
    streamBitrateKbps_ = bitrateKbps;
    streamCodecName_ = codecName;
    streamQualityProfile_ = qualityProfile;
    streamNvencRequested_ = nvencRequested;
    streamNvencFallback_ = nvencFallback;
    streamQualityDowngraded_ = qualityDowngraded;
    streamMetaSet_ = true;
    samplesSinceFlush_ += 1;
}

void ParityRecorder::recordStreamPush(bool ok) {
    if (ok) {
        streamPushedOk_ += 1;
    } else {
        streamPushedFail_ += 1;
    }
    samplesSinceFlush_ += 1;
}

void ParityRecorder::setInferCounts(int submits, int skipsMotion) {
    inferSubmits_ = submits;
    inferSkipsMotion_ = skipsMotion;
}

namespace {

double percentileSorted(std::vector<double> values, double p) {
    if (values.empty()) {
        return 0.0;
    }
    std::sort(values.begin(), values.end());
    if (values.size() == 1) {
        return values[0];
    }
    const double idx = p * static_cast<double>(values.size() - 1);
    const size_t lo = static_cast<size_t>(idx);
    const size_t hi = std::min(lo + 1, values.size() - 1);
    const double frac = idx - static_cast<double>(lo);
    return values[lo] * (1.0 - frac) + values[hi] * frac;
}

}  // namespace

bool ParityRecorder::writeToFile(const std::string& logPath) const {
    if (logPath.empty()) {
        LOG(WARNING) << "[PARITY] log_path empty; skip parity_sample.json";
        return false;
    }

    std::error_code ec;
    std::filesystem::create_directories(logPath, ec);

    Json::Value root;
    Json::Value motion(Json::objectValue);
    int baseline = static_cast<int>(motionSamples_.size());
    int motionTriggers = 0;
    int inferSkips = 0;
    Json::Value motionFrames(Json::arrayValue);
    for (const auto& s : motionSamples_) {
        if (s.triggered) {
            motionTriggers += 1;
        }
        if (s.inferSkipped) {
            inferSkips += 1;
        }
        Json::Value item;
        item["frame_index"] = s.frameIndex;
        item["triggered"] = s.triggered;
        item["reason"] = s.reason;
        item["score"] = s.score;
        item["changed_area_ratio"] = s.changedAreaRatio;
        item["infer_skipped"] = s.inferSkipped;
        motionFrames.append(item);
    }
    motion["baseline_triggers"] = baseline;
    motion["motion_triggers"] = motionTriggers;
    motion["infer_submits"] = inferSubmits_;
    motion["infer_skips_motion"] = inferSkipsMotion_ > 0 ? inferSkipsMotion_ : inferSkips;
    motion["frames"] = motionFrames;
    root["motion"] = motion;

    Json::Value track(Json::objectValue);
    Json::Value trackFrames(Json::arrayValue);
    for (const auto& frame : trackFrames_) {
        Json::Value frameObj;
        frameObj["frame_index"] = frame.frameIndex;
        Json::Value dets(Json::arrayValue);
        for (const auto& det : frame.detections) {
            Json::Value detObj;
            detObj["bbox_xyxy"] = Json::arrayValue;
            detObj["bbox_xyxy"].append(det.x1);
            detObj["bbox_xyxy"].append(det.y1);
            detObj["bbox_xyxy"].append(det.x2);
            detObj["bbox_xyxy"].append(det.y2);
            detObj["class"] = det.class_name;
            detObj["confidence"] = det.class_score;
            detObj["track_id"] = det.track_id;
            dets.append(detObj);
        }
        frameObj["detections"] = dets;
        trackFrames.append(frameObj);
    }
    track["frames"] = trackFrames;
    std::set<int> seenIds;
    for (const auto& frame : trackFrames_) {
        for (const auto& det : frame.detections) {
            if (det.track_id >= 0) {
                seenIds.insert(det.track_id);
            }
        }
    }
    track["track_switch_count"] = static_cast<int>(seenIds.size());
    root["track"] = track;

    // L_schedule / CAP-CRON-SNAP / CAP-PATROL-*
    Json::Value schedule(Json::objectValue);
    Json::Value events(Json::arrayValue);
    int cronSlots = 0;
    int patrolEvents = 0;
    std::map<std::string, std::vector<std::time_t>> byDevice;
    for (const auto& ev : scheduleEvents_) {
        Json::Value item;
        item["kind"] = ev.kind;
        item["device_id"] = ev.deviceId;
        item["slot_key"] = ev.slotKey;
        item["unix_ts"] = static_cast<Json::Int64>(ev.unixTs);
        events.append(item);
        if (ev.kind == "cron_slot" || ev.kind == "snap_interval") {
            cronSlots += 1;
        }
        if (ev.kind == "patrol") {
            patrolEvents += 1;
            byDevice[ev.deviceId].push_back(ev.unixTs);
        }
    }
    schedule["events"] = events;
    schedule["slot_count"] = cronSlots;
    schedule["patrol_count"] = patrolEvents;

    Json::Value intervals(Json::objectValue);
    double sumMean = 0.0;
    int meanCount = 0;
    for (const auto& kv : byDevice) {
        Json::Value arr(Json::arrayValue);
        const auto& ts = kv.second;
        for (size_t i = 1; i < ts.size(); ++i) {
            double delta = static_cast<double>(ts[i] - ts[i - 1]);
            arr.append(delta);
            sumMean += delta;
            meanCount += 1;
        }
        intervals[kv.first] = arr;
    }
    schedule["device_intervals"] = intervals;
    schedule["mean_interval_sec"] = meanCount > 0 ? (sumMean / meanCount) : 0.0;
    root["schedule"] = schedule;

    // L_overlay / CAP-OVERLAY-* — visible draw latency vs capture
    Json::Value overlay(Json::objectValue);
    Json::Value overlayFrames(Json::arrayValue);
    std::vector<double> latencies;
    int drawnCount = 0;
    for (const auto& s : overlaySamples_) {
        Json::Value item;
        item["frame_index"] = s.frameIndex;
        item["latency_ms"] = s.latencyMs;
        item["box_count"] = s.boxCount;
        item["drawn"] = s.drawn;
        overlayFrames.append(item);
        if (s.drawn) {
            drawnCount += 1;
            latencies.push_back(s.latencyMs);
        }
    }
    overlay["sample_count"] = static_cast<int>(overlaySamples_.size());
    overlay["drawn_count"] = drawnCount;
    overlay["p50_latency_ms"] = percentileSorted(latencies, 0.50);
    overlay["p95_latency_ms"] = percentileSorted(latencies, 0.95);
    overlay["frames"] = overlayFrames;
    root["overlay"] = overlay;

    // L_stream / CAP-RTMP-PUSH — encoder meta + push counters
    Json::Value stream(Json::objectValue);
    stream["rtmp_url"] = streamRtmpUrl_;
    stream["width"] = streamWidth_;
    stream["height"] = streamHeight_;
    stream["fps"] = streamFps_;
    stream["bitrate_kbps"] = streamBitrateKbps_;
    stream["pushed_ok"] = streamPushedOk_;
    stream["pushed_fail"] = streamPushedFail_;
    stream["meta_set"] = streamMetaSet_;
    stream["gray_frame_count"] = 0;  // placeholder; ffprobe path may refine
    stream["codec_name"] = streamCodecName_;
    stream["quality_profile"] = streamQualityProfile_;
    stream["nvenc_requested"] = streamNvencRequested_;
    stream["nvenc_fallback"] = streamNvencFallback_;
    stream["quality_downgraded"] = streamQualityDowngraded_;
    root["stream"] = stream;

    const std::filesystem::path outPath = std::filesystem::path(logPath) / "parity_sample.json";
    std::ofstream ofs(outPath);
    if (!ofs.is_open()) {
        LOG(ERROR) << "[PARITY] failed to write " << outPath.string();
        return false;
    }
    Json::StreamWriterBuilder writer;
    writer["indentation"] = "  ";
    ofs << Json::writeString(writer, root);
    LOG(INFO) << "[PARITY] wrote " << outPath.string();
    return true;
}

void ParityRecorder::maybeFlush(const std::string& logPath) {
    if (logPath.empty()) {
        return;
    }
    if (samplesSinceFlush_ < 1) {
        return;
    }
    if (motionSamples_.empty() && trackFrames_.empty() && scheduleEvents_.empty()
        && overlaySamples_.empty() && streamPushedOk_ == 0 && streamPushedFail_ == 0
        && !streamMetaSet_) {
        return;
    }
    writeToFile(logPath);
    samplesSinceFlush_ = 0;
    lastFlushPath_ = logPath;
}

}  // namespace runtime
