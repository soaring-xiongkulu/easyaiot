#include "pipeline/Pipeline.h"

#include <algorithm>
#include <chrono>
#include <glog/logging.h>
#include <opencv2/opencv.hpp>

#include "RTMPEncoder.h"
#include "Yolov11ThreadPool.h"
#include "pipeline/AlertFilters.h"

namespace runtime {

namespace {
int64_t nowNs() {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(
               std::chrono::steady_clock::now().time_since_epoch())
        .count();
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
                   Yolov11ThreadPool* yoloPool,
                   RTMPEncoder** rtmpEncoder,
                   AlarmFn alarmFn,
                   RegionFn regionFn,
                   StreamingEnabledFn streamingFn,
                   PipelineMetrics* metrics)
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
      frameRing_(8),
      resultRing_(64) {
    framePool_.reset(8, videoWidth_, videoHeight_);
    if (config_.motionGateEnabled) {
        MotionGateConfig mgCfg =
            MotionGateConfig::fromJson(config_.motionGateConfigJson, true);
        motionGate_ = std::make_unique<MotionGate>(mgCfg);
        LOG(INFO) << "[PIPELINE] motion_gate enabled preset=" << mgCfg.preset
                  << " min_area=" << mgCfg.minChangedAreaRatio;
    }
    if (config_.trackingEnabled) {
        tracker_ = std::make_unique<SimpleTracker>(
            config_.trackingSimilarityThreshold,
            config_.trackingMaxAge,
            config_.trackingSmoothAlpha);
        LOG(INFO) << "[PIPELINE] tracking enabled similarity_threshold="
                  << config_.trackingSimilarityThreshold;
    }
}

Pipeline::~Pipeline() {
    stop();
    join();
}

void Pipeline::start() {
    if (running_.exchange(true)) {
        return;
    }
    LOG(INFO) << "[PIPELINE] Starting pull/decode + infer + emit stages";
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
    parityRecorder_.setInferCounts(inferSubmits_, inferSkipsMotion_);
    if (config_.motionGateEnabled || config_.trackingEnabled) {
        parityRecorder_.writeToFile(config_.logPath);
    }
}

bool Pipeline::reopenStream() {
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

    formatCtx_ = avformat_alloc_context();
    AVDictionary* fmt_options = nullptr;
    av_dict_set(&fmt_options, "rtsp_transport", "tcp", 0);
    av_dict_set(&fmt_options, "stimeout", "3000000", 0);
    av_dict_set(&fmt_options, "timeout", "5000000", 0);

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
    const AVCodec* videoCodec = avcodec_find_decoder(videoCodecPar->codec_id);
    if (!videoCodec) {
        LOG(ERROR) << "[PIPELINE] avcodec_find_decoder failed";
        avformat_close_input(&formatCtx_);
        return false;
    }

    codecCtx_ = avcodec_alloc_context3(videoCodec);
    if (!codecCtx_ || avcodec_parameters_to_context(codecCtx_, videoCodecPar) != 0) {
        LOG(ERROR) << "[PIPELINE] codec context setup failed";
        if (codecCtx_) {
            avcodec_free_context(&codecCtx_);
        }
        avformat_close_input(&formatCtx_);
        return false;
    }
    if (avcodec_open2(codecCtx_, videoCodec, nullptr) < 0) {
        LOG(ERROR) << "[PIPELINE] avcodec_open2 failed";
        avcodec_free_context(&codecCtx_);
        avformat_close_input(&formatCtx_);
        return false;
    }

    AVStream* stream = formatCtx_->streams[videoIndex_];
    if (stream->avg_frame_rate.den == 0) {
        videoFps_ = 25;
    } else {
        videoFps_ = stream->avg_frame_rate.num / stream->avg_frame_rate.den;
    }
    videoWidth_ = codecCtx_->width;
    videoHeight_ = codecCtx_->height;
    LOG(INFO) << "[PIPELINE] reopened stream " << videoWidth_ << "x" << videoHeight_
              << "@" << videoFps_ << "fps";
    return true;
}

void Pipeline::pullDecodeLoop() {
    LOG(INFO) << "[PIPELINE-PULL] thread started";
    if (!formatCtx_ || !codecCtx_) {
        LOG(ERROR) << "[PIPELINE-PULL] FFmpeg not ready";
        running_.store(false);
        return;
    }

    AVPacket* packet = av_packet_alloc();
    AVFrame* frame = av_frame_alloc();
    AVFrame* frameBGR = av_frame_alloc();
    if (!packet || !frame || !frameBGR) {
        LOG(ERROR) << "[PIPELINE-PULL] alloc failed";
        running_.store(false);
        return;
    }

    int numBytes = av_image_get_buffer_size(AV_PIX_FMT_BGR24, videoWidth_, videoHeight_, 1);
    uint8_t* buffer = static_cast<uint8_t*>(av_malloc(numBytes * sizeof(uint8_t)));
    av_image_fill_arrays(frameBGR->data, frameBGR->linesize, buffer, AV_PIX_FMT_BGR24,
                         videoWidth_, videoHeight_, 1);

    SwsContext* swsCtx = sws_getContext(
        videoWidth_, videoHeight_, codecCtx_->pix_fmt,
        videoWidth_, videoHeight_, AV_PIX_FMT_BGR24,
        SWS_BILINEAR, nullptr, nullptr, nullptr);

    if (!swsCtx) {
        LOG(ERROR) << "[PIPELINE-PULL] sws_getContext failed";
        av_free(buffer);
        av_frame_free(&frameBGR);
        av_frame_free(&frame);
        av_packet_free(&packet);
        running_.store(false);
        return;
    }

    int reconnectBackoffSec = 1;
    const int kMaxBackoffSec = 30;

    auto rebuildConverters = [&]() -> bool {
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
        swsCtx = sws_getContext(
            videoWidth_, videoHeight_, codecCtx_->pix_fmt,
            videoWidth_, videoHeight_, AV_PIX_FMT_BGR24,
            SWS_BILINEAR, nullptr, nullptr, nullptr);
        if (!swsCtx) {
            LOG(ERROR) << "[PIPELINE-PULL] sws rebuild failed";
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
            if (ret == AVERROR_EOF) {
                LOG(WARNING) << "[PIPELINE-PULL] EOF, attempting reconnect";
            } else {
                LOG(WARNING) << "[PIPELINE-PULL] read error: " << errbuf << ", attempting reconnect";
            }

            while (running_.load()) {
                LOG(INFO) << "[PIPELINE-PULL] reconnect sleep " << reconnectBackoffSec << "s";
                for (int s = 0; s < reconnectBackoffSec && running_.load(); ++s) {
                    std::this_thread::sleep_for(std::chrono::seconds(1));
                }
                if (!running_.load()) {
                    break;
                }
                if (reopenStream() && rebuildConverters()) {
                    reconnectBackoffSec = 1;
                    LOG(INFO) << "[PIPELINE-PULL] reconnect success";
                    break;
                }
                reconnectBackoffSec = std::min(reconnectBackoffSec * 2, kMaxBackoffSec);
                LOG(WARNING) << "[PIPELINE-PULL] reopen failed, next backoff="
                             << reconnectBackoffSec << "s";
            }
            continue;
        }
        reconnectBackoffSec = 1;

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

            FrameSlot* slot = framePool_.acquire();
            if (!slot) {
                // Pool exhausted: drop by popping one pending frame index
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

            sws_scale(swsCtx, frame->data, frame->linesize, 0, videoHeight_,
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
    const std::string deviceId = config_.deviceId.empty() ? "device" : config_.deviceId;

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
            bool submitInfer = false;
            bool inferSkippedMotion = false;
            const bool isSampleFrame = (aiFrameInterval % submitInterval == 0);

            MotionResult motionResult;
            if (isSampleFrame && motionGate_) {
                motionResult = motionGate_->onSampleFrame(deviceId, img, localFrameId);
                submitInfer = motionResult.triggered || motionResult.reason == "warmup"
                              || motionResult.reason == "disabled";
                if (!submitInfer) {
                    inferSkippedMotion = true;
                    inferSkipsMotion_ += 1;
                }
                parityRecorder_.recordMotionSample(paritySampleIndex_++, motionResult, inferSkippedMotion);
                parityRecorder_.setInferCounts(inferSubmits_, inferSkipsMotion_);
                parityRecorder_.maybeFlush(config_.logPath);
            } else if (isSampleFrame) {
                submitInfer = true;
            }

            if (submitInfer && isSampleFrame) {
                yoloPool_->submitTask(img, 0, localFrameId);
                lastSubmittedFrameId = localFrameId;
                inferSubmits_ += 1;
            }
            aiFrameInterval++;
            localFrameId++;

            for (int checkFrame = lastSubmittedFrameId;
                 checkFrame >= 0 && checkFrame >= lastSubmittedFrameId - 30;
                 checkFrame--) {
                int r = yoloPool_->getTargetResultNonBlock(detections, 0, checkFrame);
                if (r == 0) {
                    lastDetections = detections;
                    // CAP-MULTI-MODEL: serial extra ONNX merge on same frame
                    if (yoloPool_->extraModelCount() > 0) {
                        yoloPool_->mergeExtraModelDetections(img, lastDetections);
                    }
                    break;
                }
            }

            if (tracker_ && !lastDetections.empty() && isSampleFrame) {
                lastDetections = tracker_->update(lastDetections, localFrameId - 1);
                parityRecorder_.recordTrackSample(paritySampleIndex_++, lastDetections);
                parityRecorder_.setInferCounts(inferSubmits_, inferSkipsMotion_);
                parityRecorder_.maybeFlush(config_.logPath);
            }

            if (!lastDetections.empty()) {
                std::vector<DetectObject> alarmDetections;
                int drawnBoxes = 0;
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
                    if (config_.enableDrawRtmp) {
                        cv::Scalar color = inAlarmRegion ? cv::Scalar(0, 0, 255) : cv::Scalar(255, 0, 0);
                        int thickness = inAlarmRegion ? 3 : 1;
                        cv::rectangle(img, cv::Point(x1, y1), cv::Point(x2, y2), color, thickness);
                        drawnBoxes += 1;
                    }
                }
                // CAP-ALERT-CLASS / FACE / PLATE filters (Python-aligned)
                if (!alarmDetections.empty()) {
                    alarmDetections = filterDetectionsForAlert(alarmDetections, config_);
                }
                // CAP-DEFENSE: skip emit outside armed windows
                if (!alarmDetections.empty() && !isDefenseArmed(config_)) {
                    alarmDetections.clear();
                }

                // G-4.4: overlay visible latency = capture → draw complete
                if (config_.enableDrawRtmp && drawnBoxes > 0) {
                    const double latencyMs =
                        static_cast<double>(nowNs() - slot->captureNs) / 1000000.0;
                    parityRecorder_.recordOverlaySample(
                        paritySampleIndex_++, latencyMs, drawnBoxes, true);
                    parityRecorder_.maybeFlush(config_.logPath);
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
            RTMPEncoder* enc = *rtmpEncoder_;
            // One-shot stream meta for L_stream parity sampling
            static thread_local bool streamMetaLogged = false;
            if (!streamMetaLogged) {
                parityRecorder_.setStreamMeta(
                    enc->rtmpUrl(),
                    enc->width(),
                    enc->height(),
                    enc->fps(),
                    static_cast<int>(enc->bitRate() / 1000),
                    enc->codecName(),
                    enc->qualityProfile(),
                    enc->nvencRequested(),
                    enc->nvencFallback(),
                    enc->qualityDowngraded());
                streamMetaLogged = true;
            }
            const bool ok = enc->encodeAndPush(img);
            parityRecorder_.recordStreamPush(ok);
            // Throttle flush: every ~25 pushes
            if ((enc->pushedOk() + enc->pushedFail()) % 25 == 0) {
                parityRecorder_.maybeFlush(config_.logPath);
            }
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
