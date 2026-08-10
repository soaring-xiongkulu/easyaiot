#include "RTMPEncoder.h"
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

bool RTMPEncoder::openEncoder(const AVCodec* codec, bool isNvenc, const RtmpEncoderOptions& opts) {
    _codecCtx = avcodec_alloc_context3(codec);
    if (!_codecCtx) {
        LOG(ERROR) << "[RTMP] Failed to allocate codec context";
        return false;
    }

    _codecCtx->width = _encWidth;
    _codecCtx->height = _encHeight;
    _codecCtx->time_base = AVRational{1, _fps};
    _codecCtx->framerate = AVRational{_fps, 1};
    _codecCtx->pix_fmt = AV_PIX_FMT_YUV420P;
    _codecCtx->bit_rate = 2500000;
    _codecCtx->gop_size = 10;
    _codecCtx->max_b_frames = 0;
    _codecCtx->rc_buffer_size = _codecCtx->bit_rate / 2;
    _codecCtx->rc_max_rate = static_cast<int64_t>(_codecCtx->bit_rate * 1.2);
    _codecCtx->rc_min_rate = static_cast<int64_t>(_codecCtx->bit_rate * 0.8);

    if (_outputCtx->oformat->flags & AVFMT_GLOBALHEADER) {
        _codecCtx->flags |= AV_CODEC_FLAG_GLOBAL_HEADER;
    }

    if (isNvenc) {
        const std::string preset = opts.nvencPreset.empty() ? "p3" : opts.nvencPreset;
        av_opt_set(_codecCtx->priv_data, "preset", preset.c_str(), 0);
        av_opt_set(_codecCtx->priv_data, "tune", "ll", 0);
        av_opt_set(_codecCtx->priv_data, "rc", "vbr", 0);
        av_opt_set(_codecCtx->priv_data, "profile", "main", 0);
        char gpuBuf[16];
        snprintf(gpuBuf, sizeof(gpuBuf), "%d", opts.gpuDeviceId < 0 ? 0 : opts.gpuDeviceId);
        av_opt_set(_codecCtx->priv_data, "gpu", gpuBuf, 0);
        _codecCtx->thread_count = 1;
    } else {
        _codecCtx->thread_count = 4;
        av_opt_set(_codecCtx->priv_data, "preset", "veryfast", 0);
        av_opt_set(_codecCtx->priv_data, "tune", "zerolatency", 0);
        av_opt_set(_codecCtx->priv_data, "profile", "main", 0);
        av_opt_set(_codecCtx->priv_data, "crf", "23", 0);
    }

    int ret = avcodec_open2(_codecCtx, codec, nullptr);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        LOG(WARNING) << "[RTMP] Failed to open codec " << codec->name << ": " << errbuf;
        avcodec_free_context(&_codecCtx);
        _codecCtx = nullptr;
        return false;
    }
    return true;
}

bool RTMPEncoder::init(const std::string& rtmpUrl, int width, int height, int fps,
                       const RtmpEncoderOptions& opts) {
    if (_initialized) {
        LOG(WARNING) << "[RTMP] Encoder already initialized";
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

    LOG(INFO) << "[RTMP] Initializing encoder: " << rtmpUrl
              << " (" << width << "x" << height << " -> " << _encWidth << "x" << _encHeight
              << "@" << _fps << "fps)"
              << " prefer_hw=" << (opts.preferHw ? "true" : "false")
              << " force_soft=" << (opts.forceSoft ? "true" : "false");

    int ret = avformat_alloc_output_context2(&_outputCtx, nullptr, "flv", rtmpUrl.c_str());
    if (ret < 0 || !_outputCtx) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        LOG(ERROR) << "[RTMP] Failed to create output context: " << errbuf;
        return false;
    }

    bool opened = false;
    if (tryNvenc) {
        const AVCodec* nvenc = avcodec_find_encoder_by_name("h264_nvenc");
        if (nvenc) {
            if (openEncoder(nvenc, true, opts)) {
                _encodeEp = "h264_nvenc";
                opened = true;
                LOG(INFO) << "[RTMP] Using h264_nvenc preset=" << opts.nvencPreset
                          << " gpu=" << opts.gpuDeviceId;
            } else {
                LOG(WARNING) << "[RTMP] h264_nvenc open failed, falling back to libx264";
                _encWidth = width;
                _encHeight = height;
            }
        } else {
            LOG(INFO) << "[RTMP] h264_nvenc not found in FFmpeg, using libx264";
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
            LOG(ERROR) << "[RTMP] H.264 codec not found";
            release();
            return false;
        }
        if (!openEncoder(soft, false, opts)) {
            LOG(ERROR) << "[RTMP] Failed to open libx264";
            release();
            return false;
        }
        _encodeEp = "libx264";
    }

    _videoStream = avformat_new_stream(_outputCtx, nullptr);
    if (!_videoStream) {
        LOG(ERROR) << "[RTMP] Failed to create video stream";
        release();
        return false;
    }

    _videoStream->time_base = _codecCtx->time_base;
    _videoStream->avg_frame_rate = _codecCtx->framerate;

    ret = avcodec_parameters_from_context(_videoStream->codecpar, _codecCtx);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        LOG(ERROR) << "[RTMP] Failed to copy codec parameters: " << errbuf;
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
            LOG(ERROR) << "[RTMP] Failed to open RTMP URL: " << errbuf
                      << " (URL: " << rtmpUrl << ")";
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
        LOG(ERROR) << "[RTMP] Failed to write header: " << errbuf;
        release();
        return false;
    }

    // BGR -> YUV420P；若 NVENC 对齐导致尺寸变化，在 sws 中一并缩放
    _swsCtx = sws_getContext(
        _srcWidth, _srcHeight, AV_PIX_FMT_BGR24,
        _encWidth, _encHeight, AV_PIX_FMT_YUV420P,
        SWS_BILINEAR, nullptr, nullptr, nullptr
    );
    if (!_swsCtx) {
        LOG(ERROR) << "[RTMP] Failed to create sws context";
        release();
        return false;
    }

    _yuvFrame = av_frame_alloc();
    if (!_yuvFrame) {
        LOG(ERROR) << "[RTMP] Failed to allocate YUV frame";
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
        LOG(ERROR) << "[RTMP] Failed to allocate frame buffer: " << errbuf;
        release();
        return false;
    }

    _packet = av_packet_alloc();
    if (!_packet) {
        LOG(ERROR) << "[RTMP] Failed to allocate packet";
        release();
        return false;
    }

    _initialized = true;
    _frameIndex = 0;

    LOG(INFO) << "[RTMP] Encoder initialized successfully encode_ep=" << _encodeEp
              << " url=" << rtmpUrl;
    return true;
}

bool RTMPEncoder::encodeAndPush(const cv::Mat& frame) {
    if (!_initialized) {
        LOG(ERROR) << "[RTMP] Encoder not initialized";
        return false;
    }

    if (frame.empty()) {
        LOG(WARNING) << "[RTMP] Empty frame received";
        return false;
    }

    cv::Mat bgr = frame;
    if (frame.cols != _srcWidth || frame.rows != _srcHeight) {
        // Unexpected size: scale to encoder source geometry
        cv::resize(frame, bgr, cv::Size(_srcWidth, _srcHeight));
    }

    const uint8_t* srcData[1] = {bgr.data};
    int srcLinesize[1] = {static_cast<int>(bgr.step[0])};

    int ret = sws_scale(_swsCtx, srcData, srcLinesize, 0, _srcHeight,
                       _yuvFrame->data, _yuvFrame->linesize);
    if (ret < 0) {
        LOG(ERROR) << "[RTMP] Failed to convert color space";
        return false;
    }

    _yuvFrame->pts = _frameIndex;
    _frameIndex++;

    ret = avcodec_send_frame(_codecCtx, _yuvFrame);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        LOG(ERROR) << "[RTMP] Failed to send frame: " << errbuf;
        return false;
    }

    while (ret >= 0) {
        ret = avcodec_receive_packet(_codecCtx, _packet);

        if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
            break;
        } else if (ret < 0) {
            char errbuf[AV_ERROR_MAX_STRING_SIZE];
            av_strerror(ret, errbuf, sizeof(errbuf));
            LOG(ERROR) << "[RTMP] Failed to receive packet: " << errbuf;
            return false;
        }

        av_packet_rescale_ts(_packet, _codecCtx->time_base, _videoStream->time_base);
        _packet->stream_index = _videoStream->index;

        ret = av_interleaved_write_frame(_outputCtx, _packet);
        if (ret < 0) {
            char errbuf[AV_ERROR_MAX_STRING_SIZE];
            av_strerror(ret, errbuf, sizeof(errbuf));
            LOG(ERROR) << "[RTMP] Failed to write frame: " << errbuf;
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

    LOG(INFO) << "[RTMP] Releasing encoder resources encode_ep=" << _encodeEp;

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

    LOG(INFO) << "[RTMP] Encoder resources released";
}
