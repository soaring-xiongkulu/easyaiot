#include "tracking/SimpleTracker.h"

#include <algorithm>
#include <cmath>
#include <set>

namespace runtime {

namespace {

float iouBoxes(const int a[4], const int b[4]) {
    const int interX1 = std::max(a[0], b[0]);
    const int interY1 = std::max(a[1], b[1]);
    const int interX2 = std::min(a[2], b[2]);
    const int interY2 = std::min(a[3], b[3]);
    const int interW = std::max(0, interX2 - interX1);
    const int interH = std::max(0, interY2 - interY1);
    const float inter = static_cast<float>(interW * interH);
    const float areaA = static_cast<float>((a[2] - a[0]) * (a[3] - a[1]));
    const float areaB = static_cast<float>((b[2] - b[0]) * (b[3] - b[1]));
    const float uni = areaA + areaB - inter;
    if (uni <= 0.0f) {
        return 0.0f;
    }
    return inter / uni;
}

}  // namespace

SimpleTracker::SimpleTracker(float similarityThreshold, int maxAge, float smoothAlpha)
    : similarityThreshold_(similarityThreshold), maxAge_(maxAge), smoothAlpha_(smoothAlpha) {}

float SimpleTracker::boxSimilarity(const int box1[4], const int box2[4]) {
    const float iou = iouBoxes(box1, box2);
    const float w1 = static_cast<float>(box1[2] - box1[0]);
    const float h1 = static_cast<float>(box1[3] - box1[1]);
    const float w2 = static_cast<float>(box2[2] - box2[0]);
    const float h2 = static_cast<float>(box2[3] - box2[1]);
    const float xmin = std::min(static_cast<float>(box1[0]), static_cast<float>(box2[0]));
    const float ymin = std::min(static_cast<float>(box1[1]), static_cast<float>(box2[1]));
    const float xmax = std::max(static_cast<float>(box1[2]), static_cast<float>(box2[2]));
    const float ymax = std::max(static_cast<float>(box1[3]), static_cast<float>(box2[3]));
    const float w = xmax - xmin;
    const float h = ymax - ymin;

    float disSim = 1.0f;
    if (w > 0.0f && h > 0.0f) {
        const float c1x = (box1[0] + box1[2]) / 2.0f;
        const float c1y = (box1[1] + box1[3]) / 2.0f;
        const float c2x = (box2[0] + box2[2]) / 2.0f;
        const float c2y = (box2[1] + box2[3]) / 2.0f;
        const float dist = std::hypot(c1x - c2x, c1y - c2y);
        const float diag = std::hypot(w, h);
        if (diag > 0.0f) {
            disSim = std::max(0.0f, 1.0f - dist / (diag * 1.5f));
        }
    }

    float shapeSim = 1.0f;
    if (w > 0.0f && h > 0.0f) {
        const float widthDiff = std::abs(w1 - w2) / std::max(w, 1.0f);
        const float heightDiff = std::abs(h1 - h2) / std::max(h, 1.0f);
        shapeSim = std::max(0.0f, 1.0f - (widthDiff + heightDiff) / 2.0f);
    }

    return iou * 0.6f + disSim * 0.35f + shapeSim * 0.05f;
}

void SimpleTracker::smoothBox(const int oldBox[4], const int newBox[4], float alpha, int out[4]) {
    out[0] = static_cast<int>(oldBox[0] * alpha + newBox[0] * (1.0f - alpha));
    out[1] = static_cast<int>(oldBox[1] * alpha + newBox[1] * (1.0f - alpha));
    out[2] = static_cast<int>(oldBox[2] * alpha + newBox[2] * (1.0f - alpha));
    out[3] = static_cast<int>(oldBox[3] * alpha + newBox[3] * (1.0f - alpha));
}

std::vector<DetectObject> SimpleTracker::update(const std::vector<DetectObject>& detections, int frameNumber) {
    std::vector<int> removeIds;
    for (auto& kv : tracks_) {
        kv.second.age += 1;
        if (kv.second.age > maxAge_) {
            removeIds.push_back(kv.first);
        }
    }
    for (int id : removeIds) {
        tracks_.erase(id);
    }

    std::set<int> matchedTracks;
    std::vector<DetectObject> out;

    for (const auto& det : detections) {
        int detBox[4] = {det.x1, det.y1, det.x2, det.y2};
        float bestSim = 0.0f;
        int bestId = -1;

        for (auto& kv : tracks_) {
            if (matchedTracks.count(kv.first) > 0) {
                continue;
            }
            Track& track = kv.second;
            int trackBox[4] = {track.x1, track.y1, track.x2, track.y2};
            float sim1 = boxSimilarity(detBox, trackBox);

            float sim2 = sim1;
            if (track.hasVelocity) {
                int predicted[4] = {
                    static_cast<int>(track.x1 + track.vx),
                    static_cast<int>(track.y1 + track.vy),
                    static_cast<int>(track.x2 + track.vx),
                    static_cast<int>(track.y2 + track.vy),
                };
                sim2 = boxSimilarity(detBox, predicted);
            }
            const float sim = std::max(sim1, sim2);
            if (sim > bestSim && sim >= similarityThreshold_) {
                bestSim = sim;
                bestId = kv.first;
            }
        }

        DetectObject tracked = det;
        if (bestId >= 0) {
            matchedTracks.insert(bestId);
            Track& track = tracks_[bestId];
            int oldBox[4] = {track.x1, track.y1, track.x2, track.y2};
            int newBox[4] = {det.x1, det.y1, det.x2, det.y2};
            int smoothed[4];
            smoothBox(oldBox, newBox, smoothAlpha_, smoothed);

            if (track.lastSeen > 0) {
                const float oldCx = (oldBox[0] + oldBox[2]) / 2.0f;
                const float oldCy = (oldBox[1] + oldBox[3]) / 2.0f;
                const float newCx = (newBox[0] + newBox[2]) / 2.0f;
                const float newCy = (newBox[1] + newBox[3]) / 2.0f;
                const float velocityAlpha = 0.7f;
                if (track.hasVelocity) {
                    track.vx = track.vx * velocityAlpha + (newCx - oldCx) * (1.0f - velocityAlpha);
                    track.vy = track.vy * velocityAlpha + (newCy - oldCy) * (1.0f - velocityAlpha);
                } else {
                    track.vx = newCx - oldCx;
                    track.vy = newCy - oldCy;
                    track.hasVelocity = true;
                }
            } else {
                track.vx = 0.0f;
                track.vy = 0.0f;
                track.hasVelocity = true;
            }

            track.lastX1 = track.x1;
            track.lastY1 = track.y1;
            track.lastX2 = track.x2;
            track.lastY2 = track.y2;
            track.x1 = smoothed[0];
            track.y1 = smoothed[1];
            track.x2 = smoothed[2];
            track.y2 = smoothed[3];
            track.classId = det.class_id;
            track.className = det.class_name;
            track.confidence = det.class_score;
            track.age = 0;
            track.lastSeen = frameNumber;

            tracked.x1 = track.x1;
            tracked.y1 = track.y1;
            tracked.x2 = track.x2;
            tracked.y2 = track.y2;
            tracked.track_id = bestId;
            out.push_back(tracked);
        } else {
            const int newId = nextId_++;
            Track track;
            track.x1 = det.x1;
            track.y1 = det.y1;
            track.x2 = det.x2;
            track.y2 = det.y2;
            track.classId = det.class_id;
            track.className = det.class_name;
            track.confidence = det.class_score;
            track.age = 0;
            track.lastSeen = frameNumber;
            tracks_[newId] = track;

            tracked.track_id = newId;
            out.push_back(tracked);
            switchCount_ += 1;
        }
    }

    for (auto& kv : tracks_) {
        if (matchedTracks.count(kv.first) > 0) {
            continue;
        }
        const Track& track = kv.second;
        DetectObject cached;
        cached.x1 = track.x1;
        cached.y1 = track.y1;
        cached.x2 = track.x2;
        cached.y2 = track.y2;
        cached.class_id = track.classId;
        cached.class_name = track.className;
        cached.class_score = track.confidence;
        cached.track_id = kv.first;
        out.push_back(cached);
    }

    return out;
}

}  // namespace runtime
