#include "pipeline/Pipeline.h"

#include <chrono>
#include <glog/logging.h>
#include <opencv2/opencv.hpp>

#include "RTMPEncoder.h"
#include "Yolov11ThreadPool.h"

namespace runtime {

namespace {
int64_t nowNs() {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(
               std::chrono::steady_clock::now().time_since_epoch())
        .count();
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

    while (running_.load()) {
        int ret = av_read_frame(formatCtx_, packet);
        if (ret < 0) {
            if (ret == AVERROR_EOF) {
                LOG(INFO) << "[PIPELINE-PULL] EOF";
                break;
            }
            continue;
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

    sws_freeContext(swsCtx);
    av_free(buffer);
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
    const int SUBMIT_INTERVAL = 8;
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
            if (aiFrameInterval % SUBMIT_INTERVAL == 0) {
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
                    if (config_.enableDrawRtmp) {
                        cv::Scalar color = inAlarmRegion ? cv::Scalar(0, 0, 255) : cv::Scalar(255, 0, 0);
                        int thickness = inAlarmRegion ? 3 : 1;
                        cv::rectangle(img, cv::Point(x1, y1), cv::Point(x2, y2), color, thickness);
                    }
                }

                if (!alarmDetections.empty()) {
                    InferResult result;
                    result.seq = slot->seq;
                    result.ptsNs = slot->ptsNs;
                    result.inferNs = nowNs();
                    result.detections = std::move(alarmDetections);
                    result.regionName = config_.regions.empty() ? "全画面" : config_.regions.begin()->first;
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
            alarmFn_(result.detections, result.regionName);
            if (metrics_) {
                metrics_->alarmsEmitted.fetch_add(1, std::memory_order_relaxed);
            }
        }
    }
    LOG(INFO) << "[PIPELINE-EMIT] thread exit";
}

}  // namespace runtime
