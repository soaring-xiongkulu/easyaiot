#include "RTMPEncoder.h"

#include <algorithm>
#include <climits>
#include <glog/logging.h>
#include <im2d.hpp>

RTMPEncoder::~RTMPEncoder() { release(); }

int RTMPEncoder::alignDim(int value, int alignment) {
    return std::max(alignment, (value + alignment - 1) / alignment * alignment);
}

int64_t RTMPEncoder::defaultBitRate(int width, int height) {
    const int64_t pixels = static_cast<int64_t>(width) * height;
    if (pixels <= 1280LL * 720) return 3500000;
    if (pixels <= 1920LL * 1080) return 4500000;
    if (pixels <= 2560LL * 1440) return 6000000;
    return 10000000;
}

bool RTMPEncoder::openEncoder(const AVCodec* encoder, const RtmpEncoderOptions& options) {
    codec_ = avcodec_alloc_context3(encoder);
    if (!codec_) return false;
    const int64_t bitRate = options.bitRate > 0
        ? options.bitRate : defaultBitRate(encodeWidth_, encodeHeight_);
    codec_->width = encodeWidth_;
    codec_->height = encodeHeight_;
    codec_->pix_fmt = AV_PIX_FMT_NV12;
    codec_->time_base = {1, fps_};
    codec_->framerate = {fps_, 1};
    codec_->bit_rate = bitRate;
    codec_->gop_size = options.gopSize > 0 ? options.gopSize : fps_ * 2;
    codec_->keyint_min = fps_;
    codec_->max_b_frames = 0;
    codec_->thread_count = 1;
    codec_->rc_buffer_size = static_cast<int>(std::min<int64_t>(bitRate * 2, INT_MAX));
    codec_->rc_max_rate = bitRate;
    if (output_->oformat->flags & AVFMT_GLOBALHEADER) codec_->flags |= AV_CODEC_FLAG_GLOBAL_HEADER;
    av_opt_set(codec_->priv_data, "rc_mode", "VBR", 0);
    av_opt_set(codec_->priv_data, "profile", "main", 0);
    av_opt_set(codec_->priv_data, "level", "5.1", 0);
    const int ret = avcodec_open2(codec_, encoder, nullptr);
    if (ret < 0) {
        char error[AV_ERROR_MAX_STRING_SIZE]{};
        av_strerror(ret, error, sizeof(error));
        LOG(ERROR) << "[MPP编码] h264_rkmpp 打开失败: " << error;
        avcodec_free_context(&codec_);
        return false;
    }
    return true;
}

bool RTMPEncoder::init(const std::string& rtmpUrl, int width, int height, int fps,
                       const RtmpEncoderOptions& options) {
    if (initialized_) return true;
    url_ = rtmpUrl;
    sourceWidth_ = width;
    sourceHeight_ = height;
    encodeWidth_ = alignDim(width);
    encodeHeight_ = alignDim(height);
    fps_ = std::max(1, fps);

    if (avformat_alloc_output_context2(&output_, nullptr, "flv", url_.c_str()) < 0 || !output_) {
        LOG(ERROR) << "[MPP编码] 无法创建 FLV 输出";
        return false;
    }
    const AVCodec* encoder = avcodec_find_encoder_by_name("h264_rkmpp");
    if (!encoder) {
        LOG(ERROR) << "[MPP编码] FFmpeg 未提供 h264_rkmpp，拒绝回退 libx264";
        release();
        return false;
    }
    if (!openEncoder(encoder, options)) {
        release();
        return false;
    }
    stream_ = avformat_new_stream(output_, nullptr);
    if (!stream_) {
        release();
        return false;
    }
    stream_->time_base = codec_->time_base;
    stream_->avg_frame_rate = codec_->framerate;
    if (avcodec_parameters_from_context(stream_->codecpar, codec_) < 0) {
        release();
        return false;
    }
    AVDictionary* ioOptions = nullptr;
    av_dict_set(&ioOptions, "rtmp_buffer", "100", 0);
    av_dict_set(&ioOptions, "rtmp_live", "live", 0);
    if (!(output_->oformat->flags & AVFMT_NOFILE) &&
        avio_open2(&output_->pb, url_.c_str(), AVIO_FLAG_WRITE, nullptr, &ioOptions) < 0) {
        av_dict_free(&ioOptions);
        release();
        return false;
    }
    av_dict_free(&ioOptions);
    AVDictionary* muxOptions = nullptr;
    av_dict_set(&muxOptions, "flvflags", "no_duration_filesize", 0);
    if (avformat_write_header(output_, &muxOptions) < 0) {
        av_dict_free(&muxOptions);
        release();
        return false;
    }
    av_dict_free(&muxOptions);

    nv12_ = av_frame_alloc();
    packet_ = av_packet_alloc();
    if (!nv12_ || !packet_) {
        release();
        return false;
    }
    nv12_->format = AV_PIX_FMT_NV12;
    nv12_->width = encodeWidth_;
    nv12_->height = encodeHeight_;
    if (av_frame_get_buffer(nv12_, 64) < 0) {
        release();
        return false;
    }
    initialized_ = true;
    encodeEp_ = "h264_rkmpp";
    LOG(INFO) << "[MPP编码] 初始化成功 " << encodeWidth_ << "x" << encodeHeight_
              << "@" << fps_ << "，无软件编码回退";
    return true;
}

bool RTMPEncoder::convertWithRga(const cv::Mat& frame) {
    if (av_frame_make_writable(nv12_) < 0) return false;
    const int srcStride = static_cast<int>(frame.step[0] / frame.elemSize());
    rga_buffer_t src = wrapbuffer_virtualaddr_t(
        frame.data, frame.cols, frame.rows, srcStride, frame.rows, RK_FORMAT_BGR_888);
    rga_buffer_t dst = wrapbuffer_virtualaddr_t(
        nv12_->data[0], encodeWidth_, encodeHeight_, nv12_->linesize[0], encodeHeight_,
        RK_FORMAT_YCbCr_420_SP);
    im_rect srcRect{0, 0, frame.cols, frame.rows};
    im_rect dstRect{0, 0, encodeWidth_, encodeHeight_};
    im_rect patRect{};
    rga_buffer_t pat{};
    im_opt_t options{};
    const IM_STATUS status = improcess(src, dst, pat, srcRect, dstRect, patRect,
                                       -1, nullptr, &options, IM_SYNC);
    if (status != IM_STATUS_SUCCESS) {
        LOG(ERROR) << "[RGA] BGR 转编码 NV12 失败: " << imStrError(status);
        return false;
    }
    return true;
}

bool RTMPEncoder::writeAvailablePackets() {
    while (true) {
        const int ret = avcodec_receive_packet(codec_, packet_);
        if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) return true;
        if (ret < 0) return false;
        av_packet_rescale_ts(packet_, codec_->time_base, stream_->time_base);
        packet_->stream_index = stream_->index;
        const int writeRet = av_interleaved_write_frame(output_, packet_);
        av_packet_unref(packet_);
        if (writeRet < 0) return false;
    }
}

bool RTMPEncoder::encodeAndPush(const cv::Mat& frame) {
    if (!initialized_ || frame.empty()) return false;
    if (!convertWithRga(frame)) return false;
    nv12_->pts = frameIndex_++;
    if (avcodec_send_frame(codec_, nv12_) < 0) return false;
    return writeAvailablePackets();
}

void RTMPEncoder::release() {
    if (codec_ && initialized_) {
        avcodec_send_frame(codec_, nullptr);
        writeAvailablePackets();
    }
    if (output_ && initialized_) av_write_trailer(output_);
    if (packet_) av_packet_free(&packet_);
    if (nv12_) av_frame_free(&nv12_);
    if (codec_) avcodec_free_context(&codec_);
    if (output_) {
        if (!(output_->oformat->flags & AVFMT_NOFILE)) avio_closep(&output_->pb);
        avformat_free_context(output_);
        output_ = nullptr;
    }
    stream_ = nullptr;
    initialized_ = false;
    encodeEp_ = "none";
    frameIndex_ = 0;
}
