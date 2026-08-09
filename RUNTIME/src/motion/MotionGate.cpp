#include "motion/MotionGate.h"

#include <algorithm>
#include <glog/logging.h>
#include <json/json.h>

namespace runtime {

namespace {

void applyPreset(const std::string& preset, MotionGateConfig& cfg) {
    if (preset == "standard") {
        cfg.minChangedAreaRatio = 0.05f;
        cfg.minMeanScore = 0.020f;
        cfg.consecutiveHitsRequired = 2;
        cfg.cooldownFrames = 75;
        cfg.preset = "standard";
    } else if (preset == "sensitive") {
        cfg.minChangedAreaRatio = 0.03f;
        cfg.minMeanScore = 0.015f;
        cfg.consecutiveHitsRequired = 1;
        cfg.cooldownFrames = 50;
        cfg.preset = "sensitive";
    } else {
        cfg.minChangedAreaRatio = 0.08f;
        cfg.minMeanScore = 0.025f;
        cfg.consecutiveHitsRequired = 2;
        cfg.cooldownFrames = 125;
        cfg.preset = "conservative";
    }
}

}  // namespace

MotionGateConfig MotionGateConfig::fromJson(const std::string& json, bool enabledFlag) {
    MotionGateConfig cfg;
    cfg.enabled = enabledFlag;
    applyPreset("conservative", cfg);

    if (json.empty() || json == "{}") {
        return cfg;
    }

    Json::Value root;
    Json::Reader reader;
    if (!reader.parse(json, root) || !root.isObject()) {
        LOG(WARNING) << "[MOTION-GATE] motion_gate config_json parse failed; using conservative preset";
        return cfg;
    }

    if (root.isMember("preset") && root["preset"].isString()) {
        applyPreset(root["preset"].asString(), cfg);
    }
    if (root.isMember("enabled")) {
        cfg.enabled = root["enabled"].asBool();
    }
    if (root.isMember("pixel_diff_thresh")) {
        cfg.pixelDiffThresh = root["pixel_diff_thresh"].asInt();
    }
    if (root.isMember("min_changed_area_ratio")) {
        cfg.minChangedAreaRatio = static_cast<float>(root["min_changed_area_ratio"].asDouble());
    }
    if (root.isMember("min_mean_score")) {
        cfg.minMeanScore = static_cast<float>(root["min_mean_score"].asDouble());
    }
    if (root.isMember("consecutive_hits_required")) {
        cfg.consecutiveHitsRequired = root["consecutive_hits_required"].asInt();
    }
    if (root.isMember("cooldown_frames")) {
        cfg.cooldownFrames = root["cooldown_frames"].asInt();
    }
    if (root.isMember("downscale_width")) {
        cfg.downscaleWidth = root["downscale_width"].asInt();
    }
    if (root.isMember("downscale_height")) {
        cfg.downscaleHeight = root["downscale_height"].asInt();
    }
    if (root.isMember("alert_motion_sync")) {
        cfg.alertMotionSync = root["alert_motion_sync"].asBool();
    }

    cfg.enabled = enabledFlag && cfg.enabled;
    return cfg;
}

MotionGate::MotionGate(const MotionGateConfig& config) : config_(config) {
    kernel_ = cv::getStructuringElement(cv::MORPH_RECT, cv::Size(3, 3));
}

MotionGate::DeviceState& MotionGate::stateFor(const std::string& deviceId) {
    return states_[deviceId];
}

cv::Mat MotionGate::toSmallGray(const cv::Mat& frameBgr) const {
    cv::Mat gray;
    cv::cvtColor(frameBgr, gray, cv::COLOR_BGR2GRAY);
    cv::Mat small;
    cv::resize(gray, small, cv::Size(config_.downscaleWidth, config_.downscaleHeight), 0, 0, cv::INTER_AREA);
    return small;
}

void MotionGate::evaluate(const cv::Mat& prevGray, const cv::Mat& currGray, float& meanScore,
                          float& changedRatio) const {
    cv::Mat diff;
    cv::absdiff(prevGray, currGray, diff);
    meanScore = static_cast<float>(cv::mean(diff)[0]) / 255.0f;

    cv::Mat binary;
    cv::threshold(diff, binary, config_.pixelDiffThresh, 255, cv::THRESH_BINARY);
    cv::morphologyEx(binary, binary, cv::MORPH_OPEN, kernel_);
    const int changed = cv::countNonZero(binary);
    changedRatio = static_cast<float>(changed) / static_cast<float>(binary.total());
}

MotionResult MotionGate::onSampleFrame(const std::string& deviceId, const cv::Mat& frameBgr, int frameNumber) {
    if (!config_.enabled) {
        MotionResult out;
        out.reason = "disabled";
        return out;
    }
    if (frameBgr.empty()) {
        LOG(WARNING) << "[MOTION-GATE] empty frame for device=" << deviceId;
        MotionResult out;
        out.reason = "empty_frame";
        return out;
    }

    DeviceState& st = stateFor(deviceId);
    st.baselineTriggers += 1;
    cv::Mat curr = toSmallGray(frameBgr);
    cv::Mat prev = st.prevGray;
    st.prevGray = curr;

    if (prev.empty()) {
        MotionResult out;
        out.reason = "warmup";
        return out;
    }

    float meanScore = 0.0f;
    float changedRatio = 0.0f;
    evaluate(prev, curr, meanScore, changedRatio);
    st.lastScore = meanScore;
    st.lastAreaRatio = changedRatio;

    const bool hit = changedRatio >= config_.minChangedAreaRatio && meanScore >= config_.minMeanScore;
    if (hit) {
        st.consecutiveHits += 1;
    } else {
        st.consecutiveHits = 0;
    }

    if (frameNumber <= st.cooldownUntil) {
        MotionResult out;
        out.score = meanScore;
        out.changedAreaRatio = changedRatio;
        out.reason = "cooldown";
        out.consecutiveHits = st.consecutiveHits;
        return out;
    }

    if (st.consecutiveHits >= config_.consecutiveHitsRequired) {
        st.motionTriggers += 1;
        st.consecutiveHits = 0;
        st.cooldownUntil = frameNumber + config_.cooldownFrames;
        MotionResult out;
        out.triggered = true;
        out.score = meanScore;
        out.changedAreaRatio = changedRatio;
        out.reason = "motion";
        out.consecutiveHits = config_.consecutiveHitsRequired;
        return out;
    }

    MotionResult out;
    out.score = meanScore;
    out.changedAreaRatio = changedRatio;
    out.reason = "below_threshold";
    out.consecutiveHits = st.consecutiveHits;
    return out;
}

bool MotionGate::shouldSupplementAlert(const std::string& deviceId, int frameNumber) const {
    if (!config_.enabled || !config_.alertMotionSync) {
        return false;
    }
    auto it = states_.find(deviceId);
    if (it == states_.end()) {
        return false;
    }
    const DeviceState& st = it->second;
    if (frameNumber <= st.cooldownUntil) {
        return false;
    }
    if (st.lastAreaRatio >= config_.minChangedAreaRatio && st.lastScore >= config_.minMeanScore
        && st.consecutiveHits >= std::max(0, config_.consecutiveHitsRequired - 1)) {
        return true;
    }
    return false;
}

void MotionGate::reset(const std::string& deviceId) {
    states_.erase(deviceId);
}

MotionStats MotionGate::stats(const std::string& deviceId) const {
    MotionStats out;
    auto it = states_.find(deviceId);
    if (it == states_.end()) {
        return out;
    }
    const DeviceState& st = it->second;
    out.baselineTriggers = st.baselineTriggers;
    out.motionTriggers = st.motionTriggers;
    out.supplementTriggers = st.supplementTriggers;
    return out;
}

}  // namespace runtime
