#ifndef RUNTIME_STREAM_FORWARDER_H
#define RUNTIME_STREAM_FORWARDER_H

#include <atomic>
#include <string>
#include <thread>

#include "Config.h"
#include "core/frame_pool.h"

extern "C" {
#include "libavformat/avformat.h"
}

namespace runtime {

/** RTSP/RTMP pull -> RTMP push with codec copy (no decode/infer/encode). */
class StreamForwarder {
public:
    explicit StreamForwarder(const Config& config, PipelineMetrics* metrics = nullptr);
    ~StreamForwarder();

    void start();
    void stop();
    void join();
    bool isRunning() const { return running_.load(); }
    uint64_t packetsRemuxed() const { return packetsRemuxed_.load(); }
    PipelineMetrics* metrics() { return metrics_; }

private:
    void forwardLoop();
    bool openInput();
    bool openOutput();
    void closeAll();
    bool remuxSession();

    Config config_;
    PipelineMetrics* metrics_{nullptr};
    std::atomic<bool> running_{false};
    std::thread thread_;
    std::atomic<uint64_t> packetsRemuxed_{0};

    AVFormatContext* inCtx_{nullptr};
    AVFormatContext* outCtx_{nullptr};
    int videoInIndex_{-1};
    int videoOutIndex_{-1};
};

}  // namespace runtime

#endif
