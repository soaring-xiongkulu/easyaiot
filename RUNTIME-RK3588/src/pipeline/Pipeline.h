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
#include "rk3588/hardware_state.h"
#include "rk3588/mpp_decoder.h"

#include <im2d.hpp>
#include <unordered_map>

extern "C" {
#include "libavcodec/avcodec.h"
#include "libavformat/avformat.h"
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
             rk3588::MppDecodeState* sharedMppState = nullptr);

    ~Pipeline();

    void start();
    void stop();
    void join();
    bool isRunning() const { return running_.load(); }

    /** Always "mpp-rk3588" after successful initialization. */
    std::string decodeEp() const { return decodeEp_; }

    /** True if pull loop stopped because a finite file/VOD hit EOF. */
    bool endedByEof() const { return endedByEof_.load(); }

private:
    void pullDecodeLoop();
    void inferLoop();
    void emitLoop();
    bool reopenStream();
    bool convertNv12ToBgr(const rk3588::FrameView& source, cv::Mat& destination);
    void releaseRgaImports();
    void setDecodeEp(const std::string& ep);
    static bool isFiniteMediaUrl(const std::string& url);

    Config& config_;
    std::string rtspUrl_;
    AVFormatContext* formatCtx_;
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

    rk3588::MppDecodeState* sharedMppState_{nullptr};  // optional mirror for /health
    std::string decodeEp_{"none"};
    bool needsBgr_{false};
    rk3588::MppDecoder decoder_;
    std::unordered_map<int, rga_buffer_handle_t> decodedRgaHandles_;

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
