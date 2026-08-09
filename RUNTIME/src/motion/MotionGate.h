#ifndef RUNTIME_MOTION_GATE_H
#define RUNTIME_MOTION_GATE_H

#include <opencv2/opencv.hpp>
#include <string>
#include <unordered_map>

namespace runtime {

struct MotionGateConfig {
    bool enabled{false};
    std::string preset{"conservative"};
    int pixelDiffThresh{25};
    float minChangedAreaRatio{0.08f};
    float minMeanScore{0.025f};
    int consecutiveHitsRequired{2};
    int cooldownFrames{125};
    int downscaleWidth{160};
    int downscaleHeight{90};
    bool alertMotionSync{false};

    static MotionGateConfig fromJson(const std::string& json, bool enabledFlag);
};

struct MotionResult {
    bool triggered{false};
    float score{0.0f};
    float changedAreaRatio{0.0f};
    std::string reason{"skip"};
    int consecutiveHits{0};
};

struct MotionStats {
    int baselineTriggers{0};
    int motionTriggers{0};
    int supplementTriggers{0};
    int inferSkips{0};
    int inferSubmits{0};
};

/** Lightweight frame-diff motion gate (parity with VIDEO motion_gate.py). */
class MotionGate {
public:
    explicit MotionGate(const MotionGateConfig& config);

    MotionResult onSampleFrame(const std::string& deviceId, const cv::Mat& frameBgr, int frameNumber);
    bool shouldSupplementAlert(const std::string& deviceId, int frameNumber) const;
    void reset(const std::string& deviceId);
    MotionStats stats(const std::string& deviceId) const;

private:
    struct DeviceState {
        cv::Mat prevGray;
        int consecutiveHits{0};
        int cooldownUntil{0};
        int baselineTriggers{0};
        int motionTriggers{0};
        int supplementTriggers{0};
        float lastScore{0.0f};
        float lastAreaRatio{0.0f};
    };

    cv::Mat toSmallGray(const cv::Mat& frameBgr) const;
    void evaluate(const cv::Mat& prevGray, const cv::Mat& currGray, float& meanScore, float& changedRatio) const;
    DeviceState& stateFor(const std::string& deviceId);

    MotionGateConfig config_;
    cv::Mat kernel_;
    mutable std::unordered_map<std::string, DeviceState> states_;
};

}  // namespace runtime

#endif
