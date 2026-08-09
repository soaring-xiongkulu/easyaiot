#ifndef RUNTIME_PARITY_RECORDER_H
#define RUNTIME_PARITY_RECORDER_H

#include "Datatype.h"
#include "motion/MotionGate.h"

#include <ctime>
#include <string>
#include <vector>

namespace runtime {

struct ParityTrackFrame {
    int frameIndex{0};
    std::vector<DetectObject> detections;
};

class ParityRecorder {
public:
    void recordMotionSample(int frameIndex, const MotionResult& result, bool inferSkipped);
    void recordTrackSample(int frameIndex, const std::vector<DetectObject>& detections);
    void recordScheduleEvent(const std::string& kind,
                             const std::string& deviceId,
                             const std::string& slotKey,
                             std::time_t unixTs);
    // G-4.4: overlay visible latency (capture → draw) samples
    void recordOverlaySample(int frameIndex, double latencyMs, int boxCount, bool drawn);
    // G-4.4: RTMP push counters + configured stream meta
    void setStreamMeta(const std::string& rtmpUrl, int width, int height, int fps, int bitrateKbps);
    void recordStreamPush(bool ok);
    void setInferCounts(int submits, int skipsMotion);
    bool writeToFile(const std::string& logPath) const;
    void maybeFlush(const std::string& logPath);

private:
    struct MotionSample {
        int frameIndex{0};
        bool triggered{false};
        std::string reason;
        float score{0.0f};
        float changedAreaRatio{0.0f};
        bool inferSkipped{false};
    };

    struct ScheduleEvent {
        std::string kind;
        std::string deviceId;
        std::string slotKey;
        std::time_t unixTs{0};
    };

    struct OverlaySample {
        int frameIndex{0};
        double latencyMs{0.0};
        int boxCount{0};
        bool drawn{false};
    };

    std::vector<MotionSample> motionSamples_;
    std::vector<ParityTrackFrame> trackFrames_;
    std::vector<ScheduleEvent> scheduleEvents_;
    std::vector<OverlaySample> overlaySamples_;
    int inferSubmits_{0};
    int inferSkipsMotion_{0};

    std::string streamRtmpUrl_;
    int streamWidth_{0};
    int streamHeight_{0};
    int streamFps_{0};
    int streamBitrateKbps_{0};
    int streamPushedOk_{0};
    int streamPushedFail_{0};
    bool streamMetaSet_{false};

    mutable std::string lastFlushPath_;
    mutable int samplesSinceFlush_{0};
};

}  // namespace runtime

#endif
