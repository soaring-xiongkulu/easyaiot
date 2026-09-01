#include "RTMPEncoder.h"
#include <climits>
#include <cstdio>
#include <glog/logging.h>
#include <algorithm>

RTMPEncoder::RTMPEncoder()
    : _outputCtx(nullptr)
    , _codecCtx(nullptr)
    , _videoStream(nullptr)
    , _swsCtx(nullptr)
    , _yuvFrame(nullptr)
    , _packet(nullptr)
    , _frameIndex(0)
    , _srcWidth(0)
    , _srcHeight(0)
    , _encWidth(0)
    , _encHeight(0)
    , _fps(0)
    , _initialized(false)
{
}

RTMPEncoder::~RTMPEncoder() {
    release();
}

int RTMPEncoder::alignDim(int v, int align) {
    if (v <= 0) return align;
    return (v + align - 1) / align * align;
}

int64_t RTMPEncoder::defaultBitRate(int width, int height) {
    // RUNTIME keeps source resolution (often 1080p/4K). VIDEO's Python path often
    // scales to 720p @ 3500k; at full res we need higher ABR or the picture looks soft.
    const int64_t pixels = static_cast<int64_t>(std::max(1, width)) * std::max(1, height);
    if (pixels <= 640LL * 360) {
        return 1500000;
    }
    if (pixels <= 1280LL * 720) {
        return 3500000;
    }
    if (pixels <= 1920LL * 1080) {
        return 4500000;
    }
    if (pixels <= 2560LL * 1440) {
        return 6000000;
    }
    return 8000000;
}

bool RTMPEncoder::openEncoder(const AVCodec* codec, bool isNvenc, const RtmpEncoderOptions& opts) {
    _codecCtx = avcodec_alloc_context3(codec);
    if (!_codecCtx) {
        LOG(ERROR) << "[推流] 编码器上下文分配失败";
        return false;
    }

    const int64_t bitRate = opts.bitRate > 0 ? opts.bitRate : defaultBitRate(_encWidth, _encHeight);
    const int gop = opts.gopSize > 0 ? opts.gopSize : std::max(1, _fps * 2);

    _codecCtx->width = _encWidth;
    _codecCtx->height = _encHeight;
    _codecCtx->time_base = AVRational{1, _fps};
    _codecCtx->framerate = AVRational{_fps, 1};
    _codecCtx->pix_fmt = AV_PIX_FMT_YUV420P;
    _codecCtx->bit_rate = bitRate;
    // Align VIDEO: ~2s keyframe interval; short GOP wastes bitrate on I-frames → blurrier P-frames.
    _codecCtx->gop_size = gop;
    _codecCtx->keyint_min = std::max(1, _fps);
    _codecCtx->max_b_frames = 0;
    // bufsize 2x bitrate avoids RC starvation that makes the picture mushy under motion.
    _codecCtx->rc_buffer_size = static_cast<int>(std::min<int64_t>(bitRate * 2, INT_MAX));
    _codecCtx->rc_max_rate = bitRate;
    // Do not clamp rc_min_rate: hard min forces CBR and hurts perceived clarity.

    if (_outputCtx->oformat->flags & AVFMT_GLOBALHEADER) {
        _codecCtx->flags |= AV_CODEC_FLAG_GLOBAL_HEADER;
    }

    if (isNvenc) {
        const std::string preset = opts.nvencPreset.empty() ? "p3" : opts.nvencPreset;
        av_opt_set(_codecCtx->priv_data, "preset", preset.c_str(), 0);
        av_opt_set(_codecCtx->priv_data, "tune", "ll", 0);
        av_opt_set(_codecCtx->priv_data, "rc", "vbr", 0);
        av_opt_set(_codecCtx->priv_data, "profile", "main", 0);
        // Mild CQ bias toward clarity while still respecting bit_rate / rc_max_rate.
        av_opt_set(_codecCtx->priv_data, "cq", "19", 0);
        char gpuBuf[16];
        snprintf(gpuBuf, sizeof(gpuBuf), "%d", opts.gpuDeviceId < 0 ? 0 : opts.gpuDeviceId);
        av_opt_set(_codecCtx->priv_data, "gpu", gpuBuf, 0);
        _codecCtx->thread_count = 1;
    } else {
        _codecCtx->thread_count = 4;
        av_opt_set(_codecCtx->priv_data, "preset", "veryfast", 0);
        av_opt_set(_codecCtx->priv_data, "tune", "zerolatency", 0);
        av_opt_set(_codecCtx->priv_data, "profile", "main", 0);
        // ABR only (no CRF): mixing CRF with bit_rate/rc_* fights and often looks worse live.
    }

    int ret = avcodec_open2(_codecCtx, codec, nullptr);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        LOG(WARNING) << "[推流] 编码器打开失败 " << codec->name << ": " << errbuf;
        avcodec_free_context(&_codecCtx);
        _codecCtx = nullptr;
        return false;
    }

    LOG(INFO) << "[推流] 编码器已打开 " << codec->name
              << " 码率=" << (bitRate / 1000) << "k"
              << " 关键帧间隔=" << gop
              << " 缓冲=" << (_codecCtx->rc_buffer_size / 1000) << "k"
              << " " << _encWidth << "x" << _encHeight << "@" << _fps << "fps";
    return true;
}

bool RTMPEncoder::init(const std::string& rtmpUrl, int width, int height, int fps,
                       const RtmpEncoderOptions& opts) {
    if (_initialized) {
        LOG(WARNING) << "[推流] 编码器已初始化";
        return true;
    }

    _rtmpUrl = rtmpUrl;
    _srcWidth = width;
    _srcHeight = height;
    _fps = fps > 0 ? fps : 25;
    _encodeEp = "none";

    const bool tryNvenc = opts.preferHw && !opts.forceSoft;
    if (tryNvenc) {
        _encWidth = alignDim(width);
        _encHeight = alignDim(height);
    } else {
        _encWidth = width;
        _encHeight = height;
    }

    LOG(INFO) << "[推流] 正在初始化编码器: " << rtmpUrl
              << " (" << width << "x" << height << " -> " << _encWidth << "x" << _encHeight
              << "@" << _fps << "fps)"
              << " 优先硬编=" << (opts.preferHw ? "true" : "false")
              << " 强制软编=" << (opts.forceSoft ? "true" : "false")
              << " 码率提示=" << (opts.bitRate > 0 ? opts.bitRate / 1000 : 0) << "k";

    int ret = avformat_alloc_output_context2(&_outputCtx, nullptr, "flv", rtmpUrl.c_str());
    if (ret < 0 || !_outputCtx) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        LOG(ERROR) << "[推流] 输出上下文创建失败: " << errbuf;
        return false;
    }

    bool opened = false;
    if (tryNvenc) {
        const AVCodec* nvenc = avcodec_find_encoder_by_name("h264_nvenc");
        if (nvenc) {
            if (openEncoder(nvenc, true, opts)) {
                _encodeEp = "h264_nvenc";
                opened = true;
                LOG(INFO) << "[推流] 使用 h264_nvenc 预设=" << opts.nvencPreset
                          << " GPU=" << opts.gpuDeviceId;
            } else {
                LOG(WARNING) << "[推流] h264_nvenc 打开失败，回退到 libx264";
                _encWidth = width;
                _encHeight = height;
            }
        } else {
            LOG(INFO) << "[推流] FFmpeg 中未找到 h264_nvenc，使用 libx264";
            _encWidth = width;
            _encHeight = height;
        }
    }

    if (!opened) {
        const AVCodec* soft = avcodec_find_encoder_by_name("libx264");
        if (!soft) {
            soft = avcodec_find_encoder(AV_CODEC_ID_H264);
        }
        if (!soft) {
            LOG(ERROR) << "[推流] 未找到 H.264 编码器";
            release();
            return false;
        }
        if (!openEncoder(soft, false, opts)) {
            LOG(ERROR) << "[推流] libx264 打开失败";
            release();
            return false;
        }
        _encodeEp = "libx264";
    }

    _videoStream = avformat_new_stream(_outputCtx, nullptr);
    if (!_videoStream) {
        LOG(ERROR) << "[推流] 视频流创建失败";
        release();
        return false;
    }

    _videoStream->time_base = _codecCtx->time_base;
    _videoStream->avg_frame_rate = _codecCtx->framerate;

    ret = avcodec_parameters_from_context(_videoStream->codecpar, _codecCtx);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        LOG(ERROR) << "[推流] 复制编码参数失败: " << errbuf;
        release();
        return false;
    }

    AVDictionary* options = nullptr;
    av_dict_set(&options, "rtmp_buffer", "100", 0);
    av_dict_set(&options, "rtmp_live", "live", 0);
    av_dict_set(&options, "buffer_size", "65536", 0);

    if (!((_outputCtx->oformat->flags & AVFMT_NOFILE))) {
        ret = avio_open2(&_outputCtx->pb, rtmpUrl.c_str(), AVIO_FLAG_WRITE, nullptr, &options);
        if (ret < 0) {
            char errbuf[AV_ERROR_MAX_STRING_SIZE];
            av_strerror(ret, errbuf, sizeof(errbuf));
            LOG(ERROR) << "[推流] RTMP 地址打开失败: " << errbuf
                      << "（地址: " << rtmpUrl << "）";
            av_dict_free(&options);
            release();
            return false;
        }
    }
    av_dict_free(&options);

    AVDictionary* muxer_opts = nullptr;
    av_dict_set(&muxer_opts, "flvflags", "no_duration_filesize", 0);
    av_dict_set(&muxer_opts, "fflags", "nobuffer", 0);

    ret = avformat_write_header(_outputCtx, &muxer_opts);
    av_dict_free(&muxer_opts);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        LOG(ERROR) << "[推流] 封装头写入失败: " << errbuf;
        release();
        return false;
    }

    // BGR -> YUV420P；NVENC 16 对齐偶发缩放时用 bicubic，比 bilinear 更锐
    _swsCtx = sws_getContext(
        _srcWidth, _srcHeight, AV_PIX_FMT_BGR24,
        _encWidth, _encHeight, AV_PIX_FMT_YUV420P,
        SWS_BICUBIC, nullptr, nullptr, nullptr
    );
    if (!_swsCtx) {
        LOG(ERROR) << "[推流] sws 转换上下文创建失败";
        release();
        return false;
    }

    _yuvFrame = av_frame_alloc();
    if (!_yuvFrame) {
        LOG(ERROR) << "[推流] YUV 帧分配失败";
        release();
        return false;
    }

    _yuvFrame->format = AV_PIX_FMT_YUV420P;
    _yuvFrame->width = _encWidth;
    _yuvFrame->height = _encHeight;

    ret = av_frame_get_buffer(_yuvFrame, 0);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        LOG(ERROR) << "[推流] 帧缓冲分配失败: " << errbuf;
        release();
        return false;
    }

    _packet = av_packet_alloc();
    if (!_packet) {
        LOG(ERROR) << "[推流] 数据包分配失败";
        release();
        return false;
    }

    _initialized = true;
    _frameIndex = 0;

    LOG(INFO) << "[推流] 编码器初始化成功 encode_ep=" << _encodeEp
              << " url=" << rtmpUrl;
    return true;
}

bool RTMPEncoder::encodeAndPush(const cv::Mat& frame) {
    if (!_initialized) {
        LOG(ERROR) << "[推流] 编码器未初始化";
        return false;
    }

    if (frame.empty()) {
        LOG(WARNING) << "[推流] 收到空帧";
        return false;
    }

    cv::Mat bgr = frame;
    if (frame.cols != _srcWidth || frame.rows != _srcHeight) {
        // Unexpected size: scale to encoder source geometry
        cv::resize(frame, bgr, cv::Size(_srcWidth, _srcHeight), 0, 0, cv::INTER_AREA);
    }

    const uint8_t* srcData[1] = {bgr.data};
    int srcLinesize[1] = {static_cast<int>(bgr.step[0])};

    int ret = sws_scale(_swsCtx, srcData, srcLinesize, 0, _srcHeight,
                       _yuvFrame->data, _yuvFrame->linesize);
    if (ret < 0) {
        LOG(ERROR) << "[推流] 色彩空间转换失败";
        return false;
    }

    _yuvFrame->pts = _frameIndex;
    _frameIndex++;

    ret = avcodec_send_frame(_codecCtx, _yuvFrame);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        LOG(ERROR) << "[推流] 帧送入编码器失败: " << errbuf;
        return false;
    }

    while (ret >= 0) {
        ret = avcodec_receive_packet(_codecCtx, _packet);

        if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
            break;
        } else if (ret < 0) {
            char errbuf[AV_ERROR_MAX_STRING_SIZE];
            av_strerror(ret, errbuf, sizeof(errbuf));
            LOG(ERROR) << "[推流] 接收编码包失败: " << errbuf;
            return false;
        }

        av_packet_rescale_ts(_packet, _codecCtx->time_base, _videoStream->time_base);
        _packet->stream_index = _videoStream->index;

        ret = av_interleaved_write_frame(_outputCtx, _packet);
        if (ret < 0) {
            char errbuf[AV_ERROR_MAX_STRING_SIZE];
            av_strerror(ret, errbuf, sizeof(errbuf));
            LOG(ERROR) << "[推流] 帧写入失败: " << errbuf;
            av_packet_unref(_packet);
            return false;
        }

        av_packet_unref(_packet);
    }

    return true;
}

void RTMPEncoder::release() {
    if (!_initialized && !_outputCtx) {
        return;
    }

    LOG(INFO) << "[推流] 正在释放编码器资源 encode_ep=" << _encodeEp;

    if (_codecCtx && _initialized) {
        avcodec_send_frame(_codecCtx, nullptr);

        while (true) {
            int ret = avcodec_receive_packet(_codecCtx, _packet);
            if (ret == AVERROR_EOF || ret == AVERROR(EAGAIN)) {
                break;
            }
            if (ret >= 0) {
                av_packet_rescale_ts(_packet, _codecCtx->time_base, _videoStream->time_base);
                _packet->stream_index = _videoStream->index;
                av_interleaved_write_frame(_outputCtx, _packet);
                av_packet_unref(_packet);
            }
        }
    }

    if (_outputCtx && _initialized) {
        av_write_trailer(_outputCtx);
    }

    if (_outputCtx) {
        if (!(_outputCtx->oformat->flags & AVFMT_NOFILE)) {
            avio_closep(&_outputCtx->pb);
        }
        avformat_free_context(_outputCtx);
        _outputCtx = nullptr;
    }

    if (_codecCtx) {
        avcodec_free_context(&_codecCtx);
        _codecCtx = nullptr;
    }

    if (_swsCtx) {
        sws_freeContext(_swsCtx);
        _swsCtx = nullptr;
    }

    if (_yuvFrame) {
        av_frame_free(&_yuvFrame);
        _yuvFrame = nullptr;
    }

    if (_packet) {
        av_packet_free(&_packet);
        _packet = nullptr;
    }

    _initialized = false;
    _frameIndex = 0;
    _encodeEp = "none";

    LOG(INFO) << "[推流] 编码器资源已释放";
}
