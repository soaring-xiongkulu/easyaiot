#include "pipeline/Pipeline.h"

#include <algorithm>
#include <cctype>
#include <chrono>
#include <glog/logging.h>
#include <opencv2/opencv.hpp>

#include "RTMPEncoder.h"
#include "YoloThreadPool.h"

namespace runtime {

namespace {
int64_t nowNs() {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(
               std::chrono::steady_clock::now().time_since_epoch())
        .count();
}

void drawDetectionOverlay(cv::Mat& img, const DetectObject& det, bool /*inAlarmRegion*/) {
    // Align with VIDEO draw_detections(); scale stroke/font for output resolution.
    const int h = img.rows;
    const int w = img.cols;
    int x1 = static_cast<int>(det.x1);
    int y1 = static_cast<int>(det.y1);
    int x2 = static_cast<int>(det.x2);
    int y2 = static_cast<int>(det.y2);
    x1 = std::max(0, std::min(x1, w - 1));
    y1 = std::max(0, std::min(y1, h - 1));
    x2 = std::max(x1 + 1, std::min(x2, w));
    y2 = std::max(y1 + 1, std::min(y2, h));

    const double refH = 1080.0;
    const double resScale = std::max(0.45, std::min(1.0, h / refH));
    const cv::Scalar color(0, 255, 0);
    const int thickness = std::max(1, static_cast<int>(std::lround(2.0 * resScale)));
    cv::rectangle(img, cv::Point(x1, y1), cv::Point(x2, y2), color, thickness, cv::LINE_AA);

    const std::string& label = det.class_name;
    if (label.empty()) {
        return;
    }

    const double fontScale = 0.8 * resScale;
    const int fontThickness = std::max(1, static_cast<int>(std::lround(2.0 * resScale)));
    int baseLine = 0;
    const cv::Size labelSize = cv::getTextSize(
        label, cv::FONT_HERSHEY_SIMPLEX, fontScale, fontThickness, &baseLine);

    int textX = std::max(0, std::min(x1, std::max(0, w - labelSize.width)));
    int textY = std::max(labelSize.height + 5, y1 - 5);
    textY = std::min(h - std::max(1, baseLine), textY);

    cv::putText(img, label,
                cv::Point(textX, textY),
                cv::FONT_HERSHEY_SIMPLEX, fontScale,
                color, fontThickness, cv::LINE_AA);
}

cv::Mat makeSnapshot(const cv::Mat& img) {
    if (img.empty()) {
        return {};
    }
    if (img.cols <= 640) {
        return img.clone();
    }
    const double scale = 640.0 / static_cast<double>(img.cols);
    cv::Mat resized;
    cv::resize(img, resized, cv::Size(), scale, scale);
    return resized;
}
}  // namespace

Pipeline::Pipeline(Config& config,
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
                   HwDecodeState* sharedHwState)
    : config_(config),
      rtspUrl_(config.rtspUrl),
      formatCtx_(formatCtx),
      codecCtx_(codecCtx),
      videoIndex_(videoIndex),
      videoWidth_(videoWidth),
      videoHeight_(videoHeight),
      videoFps_(videoFps),
      yoloPool_(yoloPool),
      rtmpEncoder_(rtmpEncoder),
      alarmFn_(std::move(alarmFn)),
      regionFn_(std::move(regionFn)),
      streamingFn_(std::move(streamingFn)),
      metrics_(metrics),
      sharedHwState_(sharedHwState),
      frameRing_(8),
      resultRing_(64) {
    framePool_.reset(8, videoWidth_, videoHeight_);
    if (sharedHwState_) {
        // Mirror Detech's initial decoder open (hw device stays owned by Detech until reopen)
        hwState_.usingCuda = sharedHwState_->usingCuda;
        hwState_.decodeEp = sharedHwState_->decodeEp.empty()
            ? (sharedHwState_->usingCuda ? "cuda" : "cpu")
            : sharedHwState_->decodeEp;
        setDecodeEp(hwState_.decodeEp);
    } else {
        setDecodeEp("cpu");
    }
    forceSoftSession_ = config_.forceSoftAv || !config_.preferHwaccel;
}

Pipeline::~Pipeline() {
    stop();
    join();
    releaseHwDecodeState(&hwState_);
}

void Pipeline::setDecodeEp(const std::string& ep) {
    decodeEp_ = ep.empty() ? "cpu" : ep;
    if (sharedHwState_) {
        sharedHwState_->decodeEp = decodeEp_;
        sharedHwState_->usingCuda = (decodeEp_ == "cuda");
    }
}

bool Pipeline::isFiniteMediaUrl(const std::string& url) {
    if (url.empty()) {
        return false;
    }
    // Bare filesystem path → finite VOD/file
    const auto schemeEnd = url.find("://");
    if (schemeEnd == std::string::npos) {
        return true;
    }
    std::string scheme = url.substr(0, schemeEnd);
    for (char& c : scheme) {
        c = static_cast<char>(::tolower(static_cast<unsigned char>(c)));
    }
    // Explicit file URL; everything else treated as live (rtsp/rtmp/udp/http/...)
    return scheme == "file";
}

void Pipeline::start() {
    if (running_.exchange(true)) {
        return;
    }
    LOG(INFO) << "[PIPELINE] Starting pull/decode + infer + emit stages decode_ep=" << decodeEp_;
    pullThread_ = std::thread(&Pipeline::pullDecodeLoop, this);
    inferThread_ = std::thread(&Pipeline::inferLoop, this);
    emitThread_ = std::thread(&Pipeline::emitLoop, this);
}

void Pipeline::stop() {
    running_.store(false);
}

void Pipeline::join() {
    if (pullThread_.joinable()) {
        pullThread_.join();
    }
    if (inferThread_.joinable()) {
        inferThread_.join();
    }
    if (emitThread_.joinable()) {
        emitThread_.join();
    }
}

bool Pipeline::reopenStream(bool forceSoft) {
    if (rtspUrl_.empty()) {
        LOG(ERROR) << "[PIPELINE] reopenStream: empty rtsp url";
        return false;
    }

    if (codecCtx_) {
        avcodec_free_context(&codecCtx_);
        codecCtx_ = nullptr;
    }
    if (formatCtx_) {
        avformat_close_input(&formatCtx_);
        formatCtx_ = nullptr;
    }
    releaseHwDecodeState(&hwState_);

    formatCtx_ = avformat_alloc_context();
    // RTSP-only options. For rtmp://, FFmpeg "timeout" implies listen mode.
    AVDictionary* fmt_options = nullptr;
    const bool isRtsp = rtspUrl_.rfind("rtsp://", 0) == 0 || rtspUrl_.rfind("rtsps://", 0) == 0;
    const bool isRtmp = rtspUrl_.rfind("rtmp://", 0) == 0 || rtspUrl_.rfind("rtmps://", 0) == 0;
    if (isRtsp) {
        av_dict_set(&fmt_options, "rtsp_transport", "tcp", 0);
        av_dict_set(&fmt_options, "stimeout", "3000000", 0);
        av_dict_set(&fmt_options, "timeout", "5000000", 0);
    } else if (isRtmp) {
        av_dict_set(&fmt_options, "rtmp_live", "live", 0);
    }

    int ret = avformat_open_input(&formatCtx_, rtspUrl_.c_str(), nullptr, &fmt_options);
    av_dict_free(&fmt_options);
    if (ret != 0) {
        char errbuf[128];
        av_strerror(ret, errbuf, sizeof(errbuf));
        LOG(ERROR) << "[PIPELINE] avformat_open_input failed: " << errbuf;
        if (formatCtx_) {
            avformat_free_context(formatCtx_);
            formatCtx_ = nullptr;
        }
        return false;
    }

    if (avformat_find_stream_info(formatCtx_, nullptr) < 0) {
        LOG(ERROR) << "[PIPELINE] avformat_find_stream_info failed";
        avformat_close_input(&formatCtx_);
        return false;
    }

    videoIndex_ = av_find_best_stream(formatCtx_, AVMEDIA_TYPE_VIDEO, -1, -1, nullptr, 0);
    if (videoIndex_ < 0) {
        LOG(ERROR) << "[PIPELINE] no video stream";
        avformat_close_input(&formatCtx_);
        return false;
    }

    AVCodecParameters* videoCodecPar = formatCtx_->streams[videoIndex_]->codecpar;
    const bool soft = forceSoft || forceSoftSession_ || config_.forceSoftAv;
    if (!openVideoDecoder(&codecCtx_, videoCodecPar,
                          config_.preferHwaccel && !soft,
                          soft,
                          config_.hwaccelDeviceId,
                          &hwState_)) {
        LOG(ERROR) << "[PIPELINE] openVideoDecoder failed";
        avformat_close_input(&formatCtx_);
        return false;
    }
    setDecodeEp(hwState_.decodeEp);

    AVStream* stream = formatCtx_->streams[videoIndex_];
    if (stream->avg_frame_rate.den == 0) {
        videoFps_ = 25;
    } else {
        videoFps_ = stream->avg_frame_rate.num / stream->avg_frame_rate.den;
    }
    videoWidth_ = codecCtx_->width;
    videoHeight_ = codecCtx_->height;
    LOG(INFO) << "[PIPELINE] reopened stream " << videoWidth_ << "x" << videoHeight_
              << "@" << videoFps_ << "fps decode_ep=" << decodeEp_;
    return true;
}

void Pipeline::pullDecodeLoop() {
    LOG(INFO) << "[PIPELINE-PULL] thread started decode_ep=" << decodeEp_;
    if (!formatCtx_ || !codecCtx_) {
        LOG(ERROR) << "[PIPELINE-PULL] FFmpeg not ready";
        running_.store(false);
        return;
    }

    AVPacket* packet = av_packet_alloc();
    AVFrame* frame = av_frame_alloc();
    AVFrame* swFrame = av_frame_alloc();
    AVFrame* frameBGR = av_frame_alloc();
    if (!packet || !frame || !swFrame || !frameBGR) {
        LOG(ERROR) << "[PIPELINE-PULL] alloc failed";
        running_.store(false);
        return;
    }

    int numBytes = av_image_get_buffer_size(AV_PIX_FMT_BGR24, videoWidth_, videoHeight_, 1);
    uint8_t* buffer = static_cast<uint8_t*>(av_malloc(numBytes * sizeof(uint8_t)));
    av_image_fill_arrays(frameBGR->data, frameBGR->linesize, buffer, AV_PIX_FMT_BGR24,
                         videoWidth_, videoHeight_, 1);

    AVPixelFormat swPixFmt = codecCtx_->pix_fmt;
    const bool initialCuda = hwState_.usingCuda || decodeEp_ == "cuda" ||
                             swPixFmt == AV_PIX_FMT_CUDA;
    if (swPixFmt == AV_PIX_FMT_CUDA || swPixFmt == AV_PIX_FMT_NONE || initialCuda) {
        // Will be set from first transferred frame; NV12 is common NVDEC download fmt
        swPixFmt = AV_PIX_FMT_NV12;
    }

    SwsContext* swsCtx = sws_getContext(
        videoWidth_, videoHeight_, swPixFmt,
        videoWidth_, videoHeight_, AV_PIX_FMT_BGR24,
        SWS_BILINEAR, nullptr, nullptr, nullptr);

    // Soft path with known host pix_fmt from codec
    if (!initialCuda && codecCtx_->pix_fmt != AV_PIX_FMT_NONE &&
        codecCtx_->pix_fmt != AV_PIX_FMT_CUDA) {
        if (swsCtx) {
            sws_freeContext(swsCtx);
        }
        swPixFmt = codecCtx_->pix_fmt;
        swsCtx = sws_getContext(
            videoWidth_, videoHeight_, swPixFmt,
            videoWidth_, videoHeight_, AV_PIX_FMT_BGR24,
            SWS_BILINEAR, nullptr, nullptr, nullptr);
    }

    if (!swsCtx) {
        LOG(ERROR) << "[PIPELINE-PULL] sws_getContext failed";
        av_free(buffer);
        av_frame_free(&frameBGR);
        av_frame_free(&swFrame);
        av_frame_free(&frame);
        av_packet_free(&packet);
        running_.store(false);
        return;
    }

    int reconnectBackoffSec = 1;
    const int kMaxBackoffSec = 30;
    const int kSustainPacketsToResetBackoff = 50;  // live: only reset after sustained read
    const int kShortSessionPackets = 25;           // below → treat as rapid EOF
    int packetsThisSession = 0;
    int rapidEofStreak = 0;
    const bool finiteSource = isFiniteMediaUrl(rtspUrl_);
    if (finiteSource) {
        LOG(INFO) << "[PIPELINE-PULL] finite media source detected (file/VOD); "
                     "EOF will end pull loop instead of reconnect storm";
    }

    auto rebuildConverters = [&](AVPixelFormat srcFmt) -> bool {
        if (swsCtx) {
            sws_freeContext(swsCtx);
            swsCtx = nullptr;
        }
        if (buffer) {
            av_free(buffer);
            buffer = nullptr;
        }
        numBytes = av_image_get_buffer_size(AV_PIX_FMT_BGR24, videoWidth_, videoHeight_, 1);
        buffer = static_cast<uint8_t*>(av_malloc(numBytes * sizeof(uint8_t)));
        av_image_fill_arrays(frameBGR->data, frameBGR->linesize, buffer, AV_PIX_FMT_BGR24,
                             videoWidth_, videoHeight_, 1);
        swPixFmt = srcFmt;
        swsCtx = sws_getContext(
            videoWidth_, videoHeight_, swPixFmt,
            videoWidth_, videoHeight_, AV_PIX_FMT_BGR24,
            SWS_BILINEAR, nullptr, nullptr, nullptr);
        if (!swsCtx) {
            LOG(ERROR) << "[PIPELINE-PULL] sws rebuild failed src_fmt=" << srcFmt;
            return false;
        }
        framePool_.reset(8, videoWidth_, videoHeight_);
        return true;
    };

    while (running_.load()) {
        int ret = av_read_frame(formatCtx_, packet);
        if (ret < 0) {
            char errbuf[128];
            av_strerror(ret, errbuf, sizeof(errbuf));
            const bool isEof = (ret == AVERROR_EOF);

            // Finite file/VOD: stop cleanly — reopen would just EOF again and burn CPU
            if (isEof && finiteSource) {
                LOG(INFO) << "[PIPELINE-PULL] EOF on finite source, ending pull loop "
                             "(packets_this_session=" << packetsThisSession << ")";
                endedByEof_.store(true);
                break;
            }

            if (isEof) {
                LOG(WARNING) << "[PIPELINE-PULL] EOF, attempting reconnect"
                             << " session_packets=" << packetsThisSession
                             << " rapid_eof_streak=" << rapidEofStreak;
            } else {
                LOG(WARNING) << "[PIPELINE-PULL] read error: " << errbuf
                             << ", attempting reconnect";
            }

            // Live: short session ending in EOF → grow backoff (avoid 1s reopen storms)
            if (isEof && packetsThisSession < kShortSessionPackets) {
                ++rapidEofStreak;
                reconnectBackoffSec = std::min(
                    std::max(reconnectBackoffSec, 1) * 2, kMaxBackoffSec);
                if (rapidEofStreak >= 3) {
                    reconnectBackoffSec = std::max(reconnectBackoffSec, 5);
                }
                LOG(WARNING) << "[PIPELINE-PULL] rapid EOF (short session), backoff="
                             << reconnectBackoffSec << "s streak=" << rapidEofStreak;
            }

            bool reopened = false;
            while (running_.load()) {
                LOG(INFO) << "[PIPELINE-PULL] reconnect sleep " << reconnectBackoffSec << "s";
                for (int s = 0; s < reconnectBackoffSec && running_.load(); ++s) {
                    std::this_thread::sleep_for(std::chrono::seconds(1));
                }
                if (!running_.load()) {
                    break;
                }
                if (reopenStream(forceSoftSession_) &&
                    rebuildConverters(hwState_.usingCuda ? AV_PIX_FMT_NV12 : codecCtx_->pix_fmt)) {
                    packetsThisSession = 0;
                    hwTransferFailStreak_ = 0;
                    // Do NOT reset backoff here — wait until sustained packets
                    LOG(INFO) << "[PIPELINE-PULL] reconnect success decode_ep=" << decodeEp_
                              << " (backoff stays " << reconnectBackoffSec
                              << "s until sustained read)";
                    reopened = true;
                    break;
                }
                reconnectBackoffSec = std::min(reconnectBackoffSec * 2, kMaxBackoffSec);
                LOG(WARNING) << "[PIPELINE-PULL] reopen failed, next backoff="
                             << reconnectBackoffSec << "s";
            }
            if (!reopened) {
                break;
            }
            continue;
        }

        ++packetsThisSession;
        if (packetsThisSession >= kSustainPacketsToResetBackoff) {
            if (reconnectBackoffSec != 1 || rapidEofStreak != 0) {
                LOG(INFO) << "[PIPELINE-PULL] sustained read (" << packetsThisSession
                          << " packets), reset reconnect backoff";
            }
            reconnectBackoffSec = 1;
            rapidEofStreak = 0;
        }

        if (metrics_) {
            metrics_->packetsIn.fetch_add(1, std::memory_order_relaxed);
        }
        if (packet->stream_index != videoIndex_) {
            av_packet_unref(packet);
            continue;
        }

        ret = avcodec_send_packet(codecCtx_, packet);
        av_packet_unref(packet);
        if (ret < 0) {
            continue;
        }

        while (ret >= 0 && running_.load()) {
            ret = avcodec_receive_frame(codecCtx_, frame);
            if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
                break;
            }
            if (ret < 0) {
                break;
            }

            AVFrame* srcForSws = ensureSoftwareFrame(frame, swFrame);
            if (!srcForSws) {
                ++hwTransferFailStreak_;
                if (!forceSoftSession_ && hwTransferFailStreak_ >= kHwFailDowngradeThreshold) {
                    LOG(WARNING) << "[PIPELINE-PULL] NVDEC transfer failed "
                                 << hwTransferFailStreak_
                                 << " times, downgrading to software decode";
                    forceSoftSession_ = true;
                    if (reopenStream(true) &&
                        rebuildConverters(codecCtx_ ? codecCtx_->pix_fmt : AV_PIX_FMT_YUV420P)) {
                        hwTransferFailStreak_ = 0;
                    }
                }
                continue;
            }
            hwTransferFailStreak_ = 0;

            if (srcForSws->format != swPixFmt ||
                srcForSws->width != videoWidth_ ||
                srcForSws->height != videoHeight_) {
                videoWidth_ = srcForSws->width > 0 ? srcForSws->width : videoWidth_;
                videoHeight_ = srcForSws->height > 0 ? srcForSws->height : videoHeight_;
                if (!rebuildConverters(static_cast<AVPixelFormat>(srcForSws->format))) {
                    continue;
                }
            }

            FrameSlot* slot = framePool_.acquire();
            if (!slot) {
                int dropIdx = -1;
                if (frameRing_.pop(dropIdx)) {
                    framePool_.release(dropIdx);
                    if (metrics_) {
                        metrics_->framesDropped.fetch_add(1, std::memory_order_relaxed);
                    }
                    slot = framePool_.acquire();
                }
                if (!slot) {
                    continue;
                }
            }

            sws_scale(swsCtx, srcForSws->data, srcForSws->linesize, 0, videoHeight_,
                      frameBGR->data, frameBGR->linesize);
            cv::Mat temp(videoHeight_, videoWidth_, CV_8UC3, frameBGR->data[0], frameBGR->linesize[0]);
            temp.copyTo(slot->bgr);

            slot->seq = seqGen_.fetch_add(1, std::memory_order_relaxed) + 1;
            slot->ptsNs = frame->pts;
            slot->captureNs = nowNs();
            slot->width = videoWidth_;
            slot->height = videoHeight_;
            slot->format = PixelFormat::BGR24;

            int discardedIdx = -1;
            bool dropped = false;
            frameRing_.pushDropOldest(slot->poolIndex, discardedIdx, &dropped);
            if (dropped && discardedIdx >= 0) {
                framePool_.release(discardedIdx);
            }
            if (metrics_) {
                metrics_->framesDecoded.fetch_add(1, std::memory_order_relaxed);
                if (dropped) {
                    metrics_->framesDropped.fetch_add(1, std::memory_order_relaxed);
                }
            }
        }
    }

    if (swsCtx) {
        sws_freeContext(swsCtx);
    }
    if (buffer) {
        av_free(buffer);
    }
    av_frame_free(&frameBGR);
    av_frame_free(&swFrame);
    av_frame_free(&frame);
    av_packet_free(&packet);
    running_.store(false);
    LOG(INFO) << "[PIPELINE-PULL] thread exit";
}

void Pipeline::inferLoop() {
    LOG(INFO) << "[PIPELINE-INFER] thread started";
    std::vector<DetectObject> lastDetections;
    int lastSubmittedFrameId = -1;
    int aiFrameInterval = 0;
    const int submitInterval = std::max(1, config_.frameSkip);
    int localFrameId = 0;

    while (running_.load() || frameRing_.sizeApprox() > 0) {
        int poolIndex = -1;
        if (!frameRing_.pop(poolIndex)) {
            std::this_thread::sleep_for(std::chrono::milliseconds(2));
            if (!running_.load()) {
                break;
            }
            continue;
        }

        FrameSlot* slot = framePool_.at(poolIndex);
        if (!slot) {
            continue;
        }

        if (metrics_) {
            metrics_->inferIn.fetch_add(1, std::memory_order_relaxed);
        }

        cv::Mat img = slot->bgr;
        std::vector<DetectObject> detections;
        int detectCount = 0;

        if (config_.enableAI && yoloPool_) {
            if (aiFrameInterval % submitInterval == 0) {
                yoloPool_->submitTask(img, 0, localFrameId);
                lastSubmittedFrameId = localFrameId;
            }
            aiFrameInterval++;
            localFrameId++;

            for (int checkFrame = lastSubmittedFrameId;
                 checkFrame >= 0 && checkFrame >= lastSubmittedFrameId - 30;
                 checkFrame--) {
                int r = yoloPool_->getTargetResultNonBlock(detections, 0, checkFrame);
                if (r == 0) {
                    lastDetections = detections;
                    break;
                }
            }

            if (!lastDetections.empty()) {
                std::vector<DetectObject> alarmDetections;
                for (const auto& det : lastDetections) {
                    int x1 = static_cast<int>(det.x1);
                    int y1 = static_cast<int>(det.y1);
                    int x2 = static_cast<int>(det.x2);
                    int y2 = static_cast<int>(det.y2);
                    int centerX = (x1 + x2) / 2;
                    int centerY = (y1 + y2) / 2;
                    bool inAlarmRegion = regionFn_ ? regionFn_(centerX, centerY) : true;
                    if (inAlarmRegion) {
                        detectCount++;
                        if (config_.enableAlarm && det.class_score >= config_.alarmConfidenceThreshold) {
                            alarmDetections.push_back(det);
                        }
                    }
                    if (config_.enableDrawRtmp &&
                        det.class_score >= config_.alarmConfidenceThreshold) {
                        drawDetectionOverlay(img, det, inAlarmRegion);
                    }
                }

                if (!alarmDetections.empty()) {
                    InferResult result;
                    result.seq = slot->seq;
                    result.ptsNs = slot->ptsNs;
                    result.inferNs = nowNs();
                    result.detections = std::move(alarmDetections);
                    result.regionName = config_.regions.empty() ? "全画面" : config_.regions.begin()->first;
                    result.snapshot = makeSnapshot(img);
                    if (metrics_) {
                        metrics_->lastLatencyMs.store(
                            static_cast<uint64_t>((result.inferNs - slot->captureNs) / 1000000),
                            std::memory_order_relaxed);
                    }
                    resultRing_.pushDropOldest(result);
                }
            }
        }

        if (streamingFn_ && streamingFn_() && rtmpEncoder_ && *rtmpEncoder_ &&
            (*rtmpEncoder_)->isInitialized()) {
            (*rtmpEncoder_)->encodeAndPush(img);
        }

        if (metrics_) {
            metrics_->inferOut.fetch_add(1, std::memory_order_relaxed);
        }
        framePool_.release(poolIndex);
    }

    LOG(INFO) << "[PIPELINE-INFER] thread exit";
}

void Pipeline::emitLoop() {
    LOG(INFO) << "[PIPELINE-EMIT] thread started";
    while (running_.load() || resultRing_.sizeApprox() > 0) {
        InferResult result;
        if (!resultRing_.pop(result)) {
            std::this_thread::sleep_for(std::chrono::milliseconds(5));
            if (!running_.load()) {
                break;
            }
            continue;
        }
        if (alarmFn_) {
            alarmFn_(result.detections, result.regionName, result.snapshot);
            if (metrics_) {
                metrics_->alarmsEmitted.fetch_add(1, std::memory_order_relaxed);
            }
        }
    }
    LOG(INFO) << "[PIPELINE-EMIT] thread exit";
}

}  // namespace runtime
