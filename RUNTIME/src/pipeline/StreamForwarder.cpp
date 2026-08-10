#include "pipeline/StreamForwarder.h"

#include <chrono>
#include <thread>

#include <glog/logging.h>

namespace runtime {
namespace {

constexpr int kReconnectDelayMs = 2000;

void logAvError(const char* tag, int ret) {
    char errbuf[AV_ERROR_MAX_STRING_SIZE];
    av_strerror(ret, errbuf, sizeof(errbuf));
    LOG(ERROR) << tag << ": " << errbuf;
}

bool isRtspUrl(const std::string& url) {
    return url.rfind("rtsp://", 0) == 0 || url.rfind("rtsps://", 0) == 0;
}

bool isRtmpUrl(const std::string& url) {
    return url.rfind("rtmp://", 0) == 0 || url.rfind("rtmps://", 0) == 0;
}

}  // namespace

StreamForwarder::StreamForwarder(const Config& config, PipelineMetrics* metrics)
    : config_(config), metrics_(metrics) {}

StreamForwarder::~StreamForwarder() {
    stop();
    join();
    closeAll();
}

void StreamForwarder::start() {
    if (running_.exchange(true)) {
        return;
    }
    thread_ = std::thread(&StreamForwarder::forwardLoop, this);
}

void StreamForwarder::stop() {
    running_.store(false);
}

void StreamForwarder::join() {
    if (thread_.joinable()) {
        thread_.join();
    }
}

void StreamForwarder::closeAll() {
    if (outCtx_) {
        if (outCtx_->pb) {
            av_write_trailer(outCtx_);
        }
        if (!(outCtx_->oformat->flags & AVFMT_NOFILE) && outCtx_->pb) {
            avio_closep(&outCtx_->pb);
        }
        avformat_free_context(outCtx_);
        outCtx_ = nullptr;
    }
    if (inCtx_) {
        avformat_close_input(&inCtx_);
        inCtx_ = nullptr;
    }
    videoInIndex_ = -1;
    videoOutIndex_ = -1;
}

bool StreamForwarder::openInput() {
    if (inCtx_) {
        avformat_close_input(&inCtx_);
        inCtx_ = nullptr;
    }

    inCtx_ = avformat_alloc_context();
    if (!inCtx_) {
        LOG(ERROR) << "[FORWARD] Failed to allocate input context";
        return false;
    }

    AVDictionary* fmtOptions = nullptr;
    const std::string& openUrl = config_.rtspUrl;
    if (isRtspUrl(openUrl)) {
        av_dict_set(&fmtOptions, "rtsp_transport", "tcp", 0);
        av_dict_set(&fmtOptions, "stimeout", "3000000", 0);
        av_dict_set(&fmtOptions, "timeout", "5000000", 0);
        av_dict_set(&fmtOptions, "max_delay", "500000", 0);
        av_dict_set(&fmtOptions, "fflags", "nobuffer", 0);
        av_dict_set(&fmtOptions, "flags", "low_delay", 0);
        av_dict_set(&fmtOptions, "probesize", "32768", 0);
        av_dict_set(&fmtOptions, "analyzeduration", "0", 0);
    } else if (isRtmpUrl(openUrl)) {
        av_dict_set(&fmtOptions, "rtmp_live", "live", 0);
    }

    int ret = avformat_open_input(&inCtx_, openUrl.c_str(), nullptr, &fmtOptions);
    av_dict_free(&fmtOptions);
    if (ret < 0) {
        logAvError("[FORWARD] avformat_open_input failed", ret);
        return false;
    }

    AVDictionary* probeOptions = nullptr;
    if (isRtspUrl(openUrl)) {
        av_dict_set(&probeOptions, "probesize", "32768", 0);
        av_dict_set(&probeOptions, "analyzeduration", "0", 0);
    }
    ret = avformat_find_stream_info(inCtx_, &probeOptions);
    av_dict_free(&probeOptions);
    if (ret < 0) {
        logAvError("[FORWARD] avformat_find_stream_info failed", ret);
        return false;
    }

    if (isRtspUrl(openUrl)) {
        inCtx_->flags |= AVFMT_FLAG_NOBUFFER;
        inCtx_->max_delay = 500000;
    }

    videoInIndex_ = av_find_best_stream(inCtx_, AVMEDIA_TYPE_VIDEO, -1, -1, nullptr, 0);
    if (videoInIndex_ < 0) {
        LOG(ERROR) << "[FORWARD] No video stream found in " << openUrl;
        return false;
    }

    AVStream* inStream = inCtx_->streams[videoInIndex_];
    const char* codecName = avcodec_get_name(inStream->codecpar->codec_id);
    LOG(INFO) << "[FORWARD] Input ready: " << openUrl
              << " video=" << inStream->codecpar->width << "x" << inStream->codecpar->height
              << " codec=" << (codecName ? codecName : "unknown");
    return true;
}

bool StreamForwarder::openOutput() {
    if (outCtx_) {
        if (outCtx_->pb) {
            av_write_trailer(outCtx_);
        }
        if (!(outCtx_->oformat->flags & AVFMT_NOFILE) && outCtx_->pb) {
            avio_closep(&outCtx_->pb);
        }
        avformat_free_context(outCtx_);
        outCtx_ = nullptr;
    }

    int ret = avformat_alloc_output_context2(&outCtx_, nullptr, "flv", config_.rtmpUrl.c_str());
    if (ret < 0 || !outCtx_) {
        logAvError("[FORWARD] avformat_alloc_output_context2 failed", ret);
        return false;
    }

    AVStream* inStream = inCtx_->streams[videoInIndex_];
    AVStream* outStream = avformat_new_stream(outCtx_, nullptr);
    if (!outStream) {
        LOG(ERROR) << "[FORWARD] avformat_new_stream failed";
        return false;
    }

    ret = avcodec_parameters_copy(outStream->codecpar, inStream->codecpar);
    if (ret < 0) {
        logAvError("[FORWARD] avcodec_parameters_copy failed", ret);
        return false;
    }
    outStream->codecpar->codec_tag = 0;
    outStream->time_base = inStream->time_base;
    videoOutIndex_ = outStream->index;

    if (!(outCtx_->oformat->flags & AVFMT_NOFILE)) {
        AVDictionary* options = nullptr;
        av_dict_set(&options, "rtmp_buffer", "50", 0);
        av_dict_set(&options, "rtmp_live", "live", 0);
        av_dict_set(&options, "buffer_size", "65536", 0);
        ret = avio_open2(&outCtx_->pb, config_.rtmpUrl.c_str(), AVIO_FLAG_WRITE, nullptr, &options);
        av_dict_free(&options);
        if (ret < 0) {
            logAvError("[FORWARD] avio_open2 failed", ret);
            return false;
        }
    }

    ret = avformat_write_header(outCtx_, nullptr);
    if (ret < 0) {
        logAvError("[FORWARD] avformat_write_header failed", ret);
        return false;
    }

    LOG(INFO) << "[FORWARD] Output ready: " << config_.rtmpUrl << " mode=copy";
    return true;
}

bool StreamForwarder::remuxSession() {
    if (!openInput()) {
        return false;
    }
    if (!openOutput()) {
        closeAll();
        return false;
    }

    AVPacket pkt;
    while (running_.load()) {
        int ret = av_read_frame(inCtx_, &pkt);
        if (ret < 0) {
            if (ret == AVERROR_EOF) {
                LOG(INFO) << "[FORWARD] Input EOF";
            } else {
                logAvError("[FORWARD] av_read_frame failed", ret);
            }
            break;
        }

        if (pkt.stream_index != videoInIndex_) {
            av_packet_unref(&pkt);
            continue;
        }

        if (metrics_) {
            metrics_->packetsIn.fetch_add(1, std::memory_order_relaxed);
        }
        packetsRemuxed_.fetch_add(1, std::memory_order_relaxed);

        AVStream* inStream = inCtx_->streams[videoInIndex_];
        AVStream* outStream = outCtx_->streams[videoOutIndex_];
        if (pkt.dts == AV_NOPTS_VALUE && pkt.pts != AV_NOPTS_VALUE) {
            pkt.dts = pkt.pts;
        }
        av_packet_rescale_ts(&pkt, inStream->time_base, outStream->time_base);
        pkt.stream_index = videoOutIndex_;
        pkt.pos = -1;

        ret = av_interleaved_write_frame(outCtx_, &pkt);
        av_packet_unref(&pkt);
        if (ret < 0) {
            logAvError("[FORWARD] av_interleaved_write_frame failed", ret);
            break;
        }
    }

    closeAll();
    return true;
}

void StreamForwarder::forwardLoop() {
    LOG(INFO) << "[FORWARD] Starting copy relay "
              << config_.rtspUrl << " -> " << config_.rtmpUrl;

    while (running_.load()) {
        if (!remuxSession()) {
            LOG(WARNING) << "[FORWARD] Session failed, retry in "
                         << kReconnectDelayMs << "ms";
        } else if (!running_.load()) {
            break;
        } else {
            LOG(WARNING) << "[FORWARD] Session ended, reconnect in "
                         << kReconnectDelayMs << "ms";
        }

        for (int i = 0; i < kReconnectDelayMs / 100 && running_.load(); ++i) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    }

    closeAll();
    LOG(INFO) << "[FORWARD] Relay stopped, packets=" << packetsRemuxed_.load();
}

}  // namespace runtime
