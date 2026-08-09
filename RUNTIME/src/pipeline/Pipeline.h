#ifndef RUNTIME_PIPELINE_H
#define RUNTIME_PIPELINE_H

#include <atomic>
#include <functional>
#include <string>
#include <thread>

#include "Config.h"
#include "Datatype.h"
#include "core/frame_pool.h"
#include "core/spsc_ring.h"
#include "motion/MotionGate.h"
#include "parity/ParityRecorder.h"
#include "tracking/SimpleTracker.h"

extern "C" {
#include "libavcodec/avcodec.h"
#include "libavformat/avformat.h"
#include "libswscale/swscale.h"
#include "libavutil/imgutils.h"
}

class Yolov11ThreadPool;
class RTMPEncoder;

namespace runtime {

/**
 * Four-stage realtime pipeline:
 *   Pull+Decode -> FrameRing -> Infer -> ResultRing -> Emit
 * Packet demux and decode stay co-located (FFmpeg) but feed FrameRing;
 * Infer and Emit run on dedicated threads with drop-oldest backpressure.
 */
class Pipeline {
public:
    using AlarmFn = std::function<void(const std::vector<DetectObject>&, const std::string&, const cv::Mat&)>;
    using RegionFn = std::function<bool(int, int)>;
    using StreamingEnabledFn = std::function<bool()>;

    Pipeline(Config& config,
             AVFormatContext* formatCtx,
             AVCodecContext* codecCtx,
             int videoIndex,
             int videoWidth,
             int videoHeight,
             int videoFps,
             Yolov11ThreadPool* yoloPool,
             RTMPEncoder** rtmpEncoder,
             AlarmFn alarmFn,
             RegionFn regionFn,
             StreamingEnabledFn streamingFn,
             PipelineMetrics* metrics);

    ~Pipeline();

    void start();
    void stop();
    void join();
    bool isRunning() const { return running_.load(); }

private:
    void pullDecodeLoop();
    void inferLoop();
    void emitLoop();
    bool reopenStream();

    Config& config_;
    std::string rtspUrl_;
    AVFormatContext* formatCtx_;
    AVCodecContext* codecCtx_;
    int videoIndex_;
    int videoWidth_;
    int videoHeight_;
    int videoFps_;
    Yolov11ThreadPool* yoloPool_;
    RTMPEncoder** rtmpEncoder_;
    AlarmFn alarmFn_;
    RegionFn regionFn_;
    StreamingEnabledFn streamingFn_;
    PipelineMetrics* metrics_;

    FramePool framePool_;
    SpscRing<int> frameRing_;       // pool indices
    SpscRing<InferResult> resultRing_;

    std::atomic<bool> running_{false};
    std::thread pullThread_;
    std::thread inferThread_;
    std::thread emitThread_;
    std::atomic<uint64_t> seqGen_{0};

    std::unique_ptr<MotionGate> motionGate_;
    std::unique_ptr<SimpleTracker> tracker_;
    ParityRecorder parityRecorder_;
    int inferSubmits_{0};
    int inferSkipsMotion_{0};
    int paritySampleIndex_{0};
};

}  // namespace runtime

#endif
