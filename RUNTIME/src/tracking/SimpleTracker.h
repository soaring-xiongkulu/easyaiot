#ifndef RUNTIME_SIMPLE_TRACKER_H
#define RUNTIME_SIMPLE_TRACKER_H

#include "Datatype.h"

#include <unordered_map>
#include <vector>

namespace runtime {

/** IoU/center-distance tracker aligned with VIDEO app/utils/tracker.py (lightweight). */
class SimpleTracker {
public:
    SimpleTracker(float similarityThreshold, int maxAge, float smoothAlpha);

    std::vector<DetectObject> update(const std::vector<DetectObject>& detections, int frameNumber);
    int switchCount() const { return switchCount_; }

private:
    struct Track {
        int x1{0};
        int y1{0};
        int x2{0};
        int y2{0};
        int classId{0};
        std::string className;
        float confidence{0.0f};
        int age{0};
        int lastSeen{0};
        int lastX1{0};
        int lastY1{0};
        int lastX2{0};
        int lastY2{0};
        float vx{0.0f};
        float vy{0.0f};
        bool hasVelocity{false};
    };

    static float boxSimilarity(const int box1[4], const int box2[4]);
    static void smoothBox(const int oldBox[4], const int newBox[4], float alpha, int out[4]);

    float similarityThreshold_;
    int maxAge_;
    float smoothAlpha_;
    int nextId_{1};
    int switchCount_{0};
    std::unordered_map<int, Track> tracks_;
};

}  // namespace runtime

#endif
