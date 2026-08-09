#include "parity/ParityRecorder.h"

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

void ParityRecorder::setInferCounts(int submits, int skipsMotion) {
    inferSubmits_ = submits;
    inferSkipsMotion_ = skipsMotion;
}

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
    if (motionSamples_.empty() && trackFrames_.empty() && scheduleEvents_.empty()) {
        return;
    }
    writeToFile(logPath);
    samplesSinceFlush_ = 0;
    lastFlushPath_ = logPath;
}

}  // namespace runtime
