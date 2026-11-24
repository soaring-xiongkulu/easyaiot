#include "pipeline/Pipeline.h"

#include <algorithm>
#include <cctype>
#include <chrono>
#include <cmath>
#include <glog/logging.h>
#include <map>
#include <opencv2/opencv.hpp>

#include "AlgoMqttBus.h"
#include "RTMPEncoder.h"
#include "YoloThreadPool.h"

namespace runtime {
namespace {

int64_t nowNs() {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(
               std::chrono::steady_clock::now().time_since_epoch())
        .count();
}

void drawDetectionOverlay(cv::Mat& image, const DetectObject& detection) {
    if (image.empty()) return;
    const int x1 = std::clamp(detection.x1, 0, image.cols - 1);
    const int y1 = std::clamp(detection.y1, 0, image.rows - 1);
    const int x2 = std::clamp(detection.x2, x1 + 1, image.cols);
    const int y2 = std::clamp(detection.y2, y1 + 1, image.rows);
    const double scale = std::clamp(image.rows / 1080.0, 0.45, 1.0);
    const int thickness = std::max(1, static_cast<int>(std::lround(2.0 * scale)));
    const cv::Scalar color(0, 255, 0);
    cv::rectangle(image, {x1, y1}, {x2, y2}, color, thickness, cv::LINE_AA);
    if (!detection.class_name.empty()) {
        cv::putText(image, detection.class_name, {x1, std::max(20, y1 - 5)},
                    cv::FONT_HERSHEY_SIMPLEX, 0.8 * scale, color, thickness, cv::LINE_AA);
    }
}

cv::Mat makeSnapshot(const cv::Mat& image) {
    if (image.empty()) return {};
    if (image.cols <= 640) return image.clone();
    const double scale = 640.0 / image.cols;
    cv::Mat output;
    cv::resize(image, output, {}, scale, scale, cv::INTER_AREA);
    return output;
}

}  // namespace

Pipeline::Pipeline(Config& config,
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
                   rk3588::MppDecodeState* sharedMppState)
    : config_(config),
      rtspUrl_(config.rtspUrl),
      formatCtx_(formatCtx),
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
      sharedMppState_(sharedMppState),
      needsBgr_(config.enableRtmp || config.enableAlarm),
      frameRing_(static_cast<size_t>(std::max(3, config.rkFramePoolSize))),
      resultRing_(64) {
    framePool_.reset(static_cast<size_t>(std::max(3, config_.rkFramePoolSize)),
                     videoWidth_, videoHeight_, needsBgr_);
    setDecodeEp("mpp-rk3588");
}

Pipeline::~Pipeline() {
    stop();
    join();
    releaseRgaImports();
    decoder_.close();
    if (formatCtx_) avformat_close_input(&formatCtx_);
}

void Pipeline::setDecodeEp(const std::string& value) {
    decodeEp_ = value.empty() ? "none" : value;
    if (sharedMppState_) {
        sharedMppState_->active = decodeEp_.find("mpp") != std::string::npos;
        sharedMppState_->endpoint = decodeEp_;
    }
}

bool Pipeline::isFiniteMediaUrl(const std::string& url) {
    if (url.empty()) return false;
    const auto schemeEnd = url.find("://");
    if (schemeEnd == std::string::npos) return true;
    std::string scheme = url.substr(0, schemeEnd);
    std::transform(scheme.begin(), scheme.end(), scheme.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });
    return scheme == "file";
}

void Pipeline::start() {
    if (running_.exchange(true)) return;
    if (!formatCtx_ || videoIndex_ < 0 ||
        !decoder_.open(formatCtx_->streams[videoIndex_]->codecpar, config_.rkMppBufferCount)) {
        LOG(ERROR) << "[流水线] MPP 解码器初始化失败，拒绝启动";
        running_.store(false);
        return;
    }
    pullThread_ = std::thread(&Pipeline::pullDecodeLoop, this);
    inferThread_ = std::thread(&Pipeline::inferLoop, this);
    emitThread_ = std::thread(&Pipeline::emitLoop, this);
    LOG(INFO) << "[流水线] MPP DMA-BUF → RGA → RKNN 流水线已启动";
}

void Pipeline::stop() { running_.store(false); }

void Pipeline::join() {
    if (pullThread_.joinable()) pullThread_.join();
    if (inferThread_.joinable()) inferThread_.join();
    if (emitThread_.joinable()) emitThread_.join();
}

void Pipeline::releaseRgaImports() {
    for (auto& item : decodedRgaHandles_) {
        if (item.second) releasebuffer_handle(item.second);
    }
    decodedRgaHandles_.clear();
}

bool Pipeline::convertNv12ToBgr(const rk3588::FrameView& source, cv::Mat& destination) {
    if (!source.valid() || !source.dmaBacked() || source.format != rk3588::FrameFormat::NV12 ||
        destination.empty()) {
        return false;
    }
    auto found = decodedRgaHandles_.find(source.dmaFd);
    if (found == decodedRgaHandles_.end()) {
        const int size = source.widthStride * source.heightStride * 3 / 2;
        const rga_buffer_handle_t handle = importbuffer_fd(source.dmaFd, size);
        if (!handle) {
            LOG(ERROR) << "[RGA] 无法导入 MPP 帧 fd=" << source.dmaFd;
            return false;
        }
        found = decodedRgaHandles_.emplace(source.dmaFd, handle).first;
    }
    const rga_buffer_t src = wrapbuffer_handle_t(
        found->second, source.width, source.height,
        source.widthStride, source.heightStride, RK_FORMAT_YCbCr_420_SP);
    const int dstStride = static_cast<int>(destination.step[0] / destination.elemSize());
    const rga_buffer_t dst = wrapbuffer_virtualaddr_t(
        destination.data, destination.cols, destination.rows,
        dstStride, destination.rows, RK_FORMAT_BGR_888);
    im_rect srcRect{0, 0, source.width, source.height};
    im_rect dstRect{0, 0, destination.cols, destination.rows};
    im_rect patRect{};
    rga_buffer_t pat{};
    im_opt_t options{};
    const IM_STATUS status = improcess(src, dst, pat, srcRect, dstRect, patRect,
                                       -1, nullptr, &options, IM_SYNC);
    if (status != IM_STATUS_SUCCESS) {
        LOG(ERROR) << "[RGA] NV12 DMA-BUF 转 BGR 失败: " << imStrError(status);
        return false;
    }
    if (metrics_) metrics_->rgaOperations.fetch_add(1, std::memory_order_relaxed);
    return true;
}

bool Pipeline::reopenStream() {
    releaseRgaImports();
    decoder_.close();
    if (formatCtx_) avformat_close_input(&formatCtx_);
    formatCtx_ = avformat_alloc_context();
    AVDictionary* options = nullptr;
    const bool rtsp = rtspUrl_.rfind("rtsp://", 0) == 0 || rtspUrl_.rfind("rtsps://", 0) == 0;
    if (rtsp) {
        av_dict_set(&options, "rtsp_transport", "tcp", 0);
        av_dict_set(&options, "stimeout", "3000000", 0);
        av_dict_set(&options, "timeout", "5000000", 0);
    }
    const int ret = avformat_open_input(&formatCtx_, rtspUrl_.c_str(), nullptr, &options);
    av_dict_free(&options);
    if (ret < 0 || avformat_find_stream_info(formatCtx_, nullptr) < 0) return false;
    videoIndex_ = av_find_best_stream(formatCtx_, AVMEDIA_TYPE_VIDEO, -1, -1, nullptr, 0);
    if (videoIndex_ < 0) return false;
    AVStream* stream = formatCtx_->streams[videoIndex_];
    if (!decoder_.open(stream->codecpar, config_.rkMppBufferCount)) return false;
    const int reopenedWidth = stream->codecpar->width;
    const int reopenedHeight = stream->codecpar->height;
    if (reopenedWidth > 0 && reopenedHeight > 0 && videoWidth_ > 0 && videoHeight_ > 0 &&
        (reopenedWidth != videoWidth_ || reopenedHeight != videoHeight_)) {
        LOG(ERROR) << "[MPP] 重连后分辨率变化，拒绝并发重建帧池 "
                   << videoWidth_ << "x" << videoHeight_ << " -> "
                   << reopenedWidth << "x" << reopenedHeight;
        decoder_.close();
        return false;
    }
    if (stream->avg_frame_rate.den) {
        videoFps_ = std::max(1, stream->avg_frame_rate.num / stream->avg_frame_rate.den);
    }
    setDecodeEp("mpp-rk3588");
    LOG(INFO) << "[MPP] 视频流重连成功 " << videoWidth_ << "x" << videoHeight_;
    return true;
}

void Pipeline::pullDecodeLoop() {
    AVPacket* packet = av_packet_alloc();
    if (!packet) {
        running_.store(false);
        return;
    }
    const bool finiteSource = isFiniteMediaUrl(rtspUrl_);
    int reconnectBackoff = 1;
    bool geometryInitialized = false;

    while (running_.load(std::memory_order_acquire)) {
        const int readRet = av_read_frame(formatCtx_, packet);
        if (readRet < 0) {
            if (readRet == AVERROR_EOF && finiteSource) {
                endedByEof_.store(true);
                break;
            }
            bool reopened = false;
            while (running_.load() && !reopened) {
                LOG(WARNING) << "[MPP] 拉流中断，" << reconnectBackoff << " 秒后重连";
                for (int i = 0; i < reconnectBackoff * 10 && running_.load(); ++i) {
                    std::this_thread::sleep_for(std::chrono::milliseconds(100));
                }
                reopened = running_.load() && reopenStream();
                reconnectBackoff = reopened ? 1 : std::min(30, reconnectBackoff * 2);
            }
            if (!reopened) break;
            continue;
        }
        if (packet->stream_index != videoIndex_) {
            av_packet_unref(packet);
            continue;
        }
        if (metrics_) metrics_->packetsIn.fetch_add(1, std::memory_order_relaxed);
        const bool accepted = decoder_.submit(packet);
        av_packet_unref(packet);
        if (!accepted) {
            LOG(ERROR) << "[MPP] 压缩包提交失败，硬件链路停止（无软件回退）";
            running_.store(false);
            break;
        }

        rk3588::FrameView decoded;
        while (decoder_.receive(decoded)) {
            if (!geometryInitialized) {
                videoWidth_ = decoded.width;
                videoHeight_ = decoded.height;
                framePool_.reset(static_cast<size_t>(std::max(3, config_.rkFramePoolSize)),
                                 videoWidth_, videoHeight_, needsBgr_);
                geometryInitialized = true;
            } else if (decoded.width != videoWidth_ || decoded.height != videoHeight_) {
                LOG(ERROR) << "[MPP] 运行中分辨率变化，拒绝无界重分配 "
                           << videoWidth_ << "x" << videoHeight_ << " -> "
                           << decoded.width << "x" << decoded.height;
                running_.store(false);
                break;
            }

            FrameSlot* slot = framePool_.acquire();
            if (!slot) {
                int old = -1;
                if (frameRing_.pop(old)) {
                    framePool_.release(old);
                    if (metrics_) metrics_->framesDropped.fetch_add(1, std::memory_order_relaxed);
                    slot = framePool_.acquire();
                }
            }
            if (!slot) continue;
            if (needsBgr_ && !convertNv12ToBgr(decoded, slot->bgr)) {
                framePool_.release(slot->poolIndex);
                running_.store(false);
                break;
            }
            slot->source = decoded;
            slot->seq = seqGen_.fetch_add(1, std::memory_order_relaxed) + 1;
            slot->ptsNs = static_cast<int64_t>(decoded.sequence);
            slot->captureNs = nowNs();
            slot->width = decoded.width;
            slot->height = decoded.height;
            slot->format = PixelFormat::NV12;
            int discarded = -1;
            bool dropped = false;
            frameRing_.pushDropOldest(slot->poolIndex, discarded, &dropped);
            if (dropped && discarded >= 0) framePool_.release(discarded);
            if (metrics_) {
                metrics_->framesDecoded.fetch_add(1, std::memory_order_relaxed);
                metrics_->mppFrames.fetch_add(1, std::memory_order_relaxed);
                if (dropped) metrics_->framesDropped.fetch_add(1, std::memory_order_relaxed);
            }
        }
    }
    decoder_.flush();
    av_packet_free(&packet);
    running_.store(false);
    LOG(INFO) << "[MPP] 拉流解码线程退出";
}

void Pipeline::inferLoop() {
    struct Pending {
        std::vector<std::vector<DetectObject>> results;
        std::vector<bool> ready;
    };
    std::map<int, Pending> pending;
    std::vector<DetectObject> lastDetections;
    const int submitInterval = std::max(1, config_.frameSkip);
    int interval = 0;
    int frameId = 0;

    while (running_.load() || frameRing_.sizeApprox() > 0) {
        int poolIndex = -1;
        if (!frameRing_.pop(poolIndex)) {
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
            continue;
        }
        FrameSlot* slot = framePool_.at(poolIndex);
        if (!slot) continue;
        if (metrics_) metrics_->inferIn.fetch_add(1, std::memory_order_relaxed);
        cv::Mat image = slot->bgr;

        if (config_.enableAI && yoloPool_) {
            const size_t count = yoloPool_->modelCount();
            if (interval % submitInterval == 0) {
                Pending work;
                work.results.resize(count);
                work.ready.assign(count, false);
                for (size_t model = 0; model < count; ++model) {
                    if (yoloPool_->submitTask(slot->source, static_cast<int>(model), 0, frameId) != 0) {
                        work.ready[model] = true;
                    }
                }
                pending.emplace(frameId, std::move(work));
            }
            ++interval;
            ++frameId;

            for (auto it = pending.begin(); it != pending.end();) {
                for (size_t model = 0; model < it->second.ready.size(); ++model) {
                    if (!it->second.ready[model] &&
                        yoloPool_->getTargetResultNonBlock(it->second.results[model],
                                                          static_cast<int>(model), 0, it->first) == 0) {
                        it->second.ready[model] = true;
                    }
                }
                const bool complete = std::all_of(it->second.ready.begin(), it->second.ready.end(),
                                                  [](bool value) { return value; });
                if (complete) {
                    std::vector<DetectObject> merged;
                    for (auto& result : it->second.results) {
                        merged.insert(merged.end(), result.begin(), result.end());
                    }
                    lastDetections = std::move(merged);
                    it = pending.erase(it);
                } else {
                    ++it;
                }
            }
            const size_t pendingLimit = static_cast<size_t>(config_.rkNpuWorkers) *
                                        static_cast<size_t>(config_.rkTaskQueueDepth + 1);
            while (pending.size() > pendingLimit) {
                pending.erase(pending.begin());
            }
            if (metrics_) {
                metrics_->npuQueueDrops.store(yoloPool_->droppedTasks(), std::memory_order_relaxed);
                metrics_->npuDurationUs.store(
                    static_cast<uint64_t>(std::max<int64_t>(0, yoloPool_->lastNpuDurationUs())),
                    std::memory_order_relaxed);
                metrics_->npuCompleted.store(
                    yoloPool_->completedTasks(), std::memory_order_relaxed);
                metrics_->npuThroughputMilliFps.store(
                    static_cast<uint64_t>(std::max(0.0, yoloPool_->throughputFps()) * 1000.0),
                    std::memory_order_relaxed);
            }

            std::vector<DetectObject> alarmDetections;
            const bool skipRegionGate = AlgoMqttBus::shouldPublishInferEvent();
            for (const auto& detection : lastDetections) {
                const int centerX = (detection.x1 + detection.x2) / 2;
                const int centerY = (detection.y1 + detection.y2) / 2;
                const bool inRegion = skipRegionGate || !regionFn_ || regionFn_(centerX, centerY);
                if (inRegion && config_.enableAlarm &&
                    detection.class_score >= config_.alarmConfidenceThreshold) {
                    alarmDetections.push_back(detection);
                }
                if (config_.enableDrawRtmp &&
                    detection.class_score >= config_.alarmConfidenceThreshold) {
                    drawDetectionOverlay(image, detection);
                }
            }
            if (!alarmDetections.empty()) {
                InferResult result;
                result.seq = slot->seq;
                result.ptsNs = slot->ptsNs;
                result.inferNs = nowNs();
                result.detections = std::move(alarmDetections);
                result.regionName = config_.regions.empty() ? "全画面" : config_.regions.begin()->first;
                result.snapshot = makeSnapshot(image);
                if (metrics_) {
                    metrics_->lastLatencyMs.store(
                        static_cast<uint64_t>((result.inferNs - slot->captureNs) / 1000000),
                        std::memory_order_relaxed);
                }
                resultRing_.pushDropOldest(result);
            }
        }

        if (streamingFn_ && streamingFn_() && rtmpEncoder_ && *rtmpEncoder_ &&
            (*rtmpEncoder_)->isInitialized()) {
            (*rtmpEncoder_)->encodeAndPush(image);
        }
        if (metrics_) metrics_->inferOut.fetch_add(1, std::memory_order_relaxed);
        framePool_.release(poolIndex);
    }
    LOG(INFO) << "[RKNN] 推理线程退出";
}

void Pipeline::emitLoop() {
    while (running_.load() || resultRing_.sizeApprox() > 0) {
        InferResult result;
        if (!resultRing_.pop(result)) {
            std::this_thread::sleep_for(std::chrono::milliseconds(5));
            continue;
        }
        if (alarmFn_) {
            alarmFn_(result.detections, result.regionName, result.snapshot);
            if (metrics_) metrics_->alarmsEmitted.fetch_add(1, std::memory_order_relaxed);
        }
    }
}

}  // namespace runtime
