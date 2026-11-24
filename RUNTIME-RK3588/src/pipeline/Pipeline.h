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
#include "ffmpeg_hw.h"

extern "C" {
#include "libavcodec/avcodec.h"
#include "libavformat/avformat.h"
#include "libswscale/swscale.h"
#include "libavutil/imgutils.h"
}

class YoloThreadPool;
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
             YoloThreadPool* yoloPool,
             RTMPEncoder** rtmpEncoder,
             AlarmFn alarmFn,
             RegionFn regionFn,
             StreamingEnabledFn streamingFn,
             PipelineMetrics* metrics,
             HwDecodeState* sharedHwState = nullptr);

    ~Pipeline();

    void start();
    void stop();
    void join();
    bool isRunning() const { return running_.load(); }

    /** cuda | cpu — updated after reopen / downgrade */
    std::string decodeEp() const { return decodeEp_; }

    /** True if pull loop stopped because a finite file/VOD hit EOF. */
    bool endedByEof() const { return endedByEof_.load(); }

private:
    void pullDecodeLoop();
    void inferLoop();
    void emitLoop();
    bool reopenStream(bool forceSoft = false);
    void setDecodeEp(const std::string& ep);
    static bool isFiniteMediaUrl(const std::string& url);

    Config& config_;
    std::string rtspUrl_;
    AVFormatContext* formatCtx_;
    AVCodecContext* codecCtx_;
    int videoIndex_;
    int videoWidth_;
    int videoHeight_;
    int videoFps_;
    YoloThreadPool* yoloPool_;
    RTMPEncoder** rtmpEncoder_;
    AlarmFn alarmFn_;
    RegionFn regionFn_;
    StreamingEnabledFn streamingFn_;
    PipelineMetrics* metrics_;

    HwDecodeState hwState_{};
    HwDecodeState* sharedHwState_{nullptr};  // optional mirror for /health
    std::string decodeEp_{"cpu"};
    bool forceSoftSession_{false};
    int hwTransferFailStreak_{0};
    static constexpr int kHwFailDowngradeThreshold = 3;

    FramePool framePool_;
    SpscRing<int> frameRing_;       // pool indices
    SpscRing<InferResult> resultRing_;

    std::atomic<bool> running_{false};
    std::atomic<bool> endedByEof_{false};
    std::thread pullThread_;
    std::thread inferThread_;
    std::thread emitThread_;
    std::atomic<uint64_t> seqGen_{0};
};

}  // namespace runtime

#endif
