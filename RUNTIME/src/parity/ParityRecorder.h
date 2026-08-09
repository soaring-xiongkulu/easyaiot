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

    std::vector<MotionSample> motionSamples_;
    std::vector<ParityTrackFrame> trackFrames_;
    std::vector<ScheduleEvent> scheduleEvents_;
    int inferSubmits_{0};
    int inferSkipsMotion_{0};
    mutable std::string lastFlushPath_;
    mutable int samplesSinceFlush_{0};
};

}  // namespace runtime

#endif
