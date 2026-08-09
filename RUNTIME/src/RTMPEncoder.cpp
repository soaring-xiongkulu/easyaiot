#include "RTMPEncoder.h"
#include <glog/logging.h>
#include <algorithm>
#include <cctype>

RTMPEncoder::RTMPEncoder()
    : _outputCtx(nullptr)
    , _codecCtx(nullptr)
    , _videoStream(nullptr)
    , _swsCtx(nullptr)
    , _yuvFrame(nullptr)
    , _packet(nullptr)
    , _frameIndex(0)
    , _width(0)
    , _height(0)
    , _fps(0)
    , _initialized(false)
{
}

RTMPEncoder::~RTMPEncoder() {
    release();
}

RTMPEncoder::QualityPreset RTMPEncoder::presetFor(const std::string& name) {
    // Align with Python QUALITY_PROFILE_PRESETS bitrate bands (kbps → bps)
    std::string n = name;
    std::transform(n.begin(), n.end(), n.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    if (n == "low") {
        return QualityPreset{"low", 1500000};
    }
    if (n == "medium" || n == "med") {
        return QualityPreset{"medium", 2500000};
    }
    return QualityPreset{"high", 3500000};
}

std::string RTMPEncoder::downgradeProfile(const std::string& name) {
    auto p = presetFor(name);
    if (std::string(p.name) == "high") return "medium";
    if (std::string(p.name) == "medium") return "low";
    return "low";
}

bool RTMPEncoder::openCodec(const AVCodec* codec, const std::string& codecLabel, int bitrate) {
    if (!codec) {
        return false;
    }

    if (_codecCtx) {
        avcodec_free_context(&_codecCtx);
        _codecCtx = nullptr;
    }

    _codecCtx = avcodec_alloc_context3(codec);
    if (!_codecCtx) {
        LOG(ERROR) << "[RTMP] Failed to allocate codec context for " << codecLabel;
        return false;
    }

    _codecCtx->width = _width;
    _codecCtx->height = _height;
    _codecCtx->time_base = AVRational{1, _fps};
    _codecCtx->framerate = AVRational{_fps, 1};
    _codecCtx->pix_fmt = AV_PIX_FMT_YUV420P;
    _bitRate = bitrate;
    _codecCtx->bit_rate = _bitRate;
    _codecCtx->gop_size = std::max(1, _fps);
    _codecCtx->max_b_frames = 0;
    _codecCtx->rc_buffer_size = static_cast<int>(_codecCtx->bit_rate / 2);
    _codecCtx->rc_max_rate = static_cast<int64_t>(_codecCtx->bit_rate * 1.2);
    _codecCtx->rc_min_rate = static_cast<int64_t>(_codecCtx->bit_rate * 0.8);
    _codecCtx->thread_count = 4;

    if (_outputCtx && (_outputCtx->oformat->flags & AVFMT_GLOBALHEADER)) {
        _codecCtx->flags |= AV_CODEC_FLAG_GLOBAL_HEADER;
    }

    if (codecLabel == "libx264" || codecLabel == "h264") {
        av_opt_set(_codecCtx->priv_data, "preset", "veryfast", 0);
        av_opt_set(_codecCtx->priv_data, "tune", "zerolatency", 0);
        av_opt_set(_codecCtx->priv_data, "profile", "main", 0);
        av_opt_set(_codecCtx->priv_data, "crf", "23", 0);
    } else if (codecLabel == "h264_nvenc") {
        // NVENC low-latency presets (p1–p7); p3 ≈ balanced
        av_opt_set(_codecCtx->priv_data, "preset", "p3", 0);
        av_opt_set(_codecCtx->priv_data, "tune", "ll", 0);
        av_opt_set(_codecCtx->priv_data, "rc", "cbr", 0);
    }

    int ret = avcodec_open2(_codecCtx, codec, nullptr);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        LOG(WARNING) << "[RTMP] Failed to open codec " << codecLabel << ": " << errbuf;
        avcodec_free_context(&_codecCtx);
        _codecCtx = nullptr;
        return false;
    }

    _codecName = codecLabel;
    return true;
}

bool RTMPEncoder::init(const std::string& rtmpUrl, int width, int height, int fps,
                       bool nvencAuto,
                       const std::string& qualityProfile,
                       bool qualityAutoDowngrade) {
    if (_initialized) {
        LOG(WARNING) << "[RTMP] Encoder already initialized";
        return true;
    }

    _rtmpUrl = rtmpUrl;
    _width = width;
    _height = height;
    _fps = fps > 0 ? fps : 25;
    _nvencRequested = nvencAuto;
    _nvencFallback = false;
    _qualityDowngraded = false;
    _qualityProfile = presetFor(qualityProfile).name;

    LOG(INFO) << "[RTMP] Initializing encoder: " << rtmpUrl
              << " (" << width << "x" << height << "@" << _fps << "fps)"
              << " nvenc_auto=" << (nvencAuto ? "true" : "false")
              << " quality_profile=" << _qualityProfile
              << " quality_auto_downgrade=" << (qualityAutoDowngrade ? "true" : "false");

    int ret = avformat_alloc_output_context2(&_outputCtx, nullptr, "flv", rtmpUrl.c_str());
    if (ret < 0 || !_outputCtx) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        LOG(ERROR) << "[RTMP] Failed to create output context: " << errbuf;
        return false;
    }

    // Legacy RTMP baseline (G-4.4): fixed 2.5Mbps when CAP-NVENC-AUTO is off.
    const bool qualityCaps = nvencAuto || qualityAutoDowngrade;
    auto tryOpenWithProfile = [&](const std::string& profile) -> bool {
        int bitrate = qualityCaps ? presetFor(profile).bitrate : 2500000;
        _qualityProfile = qualityCaps ? presetFor(profile).name : "legacy";

        if (nvencAuto) {
            const AVCodec* nvenc = avcodec_find_encoder_by_name("h264_nvenc");
            if (nvenc && openCodec(nvenc, "h264_nvenc", bitrate)) {
                LOG(INFO) << "[RTMP] CAP-NVENC-AUTO using h264_nvenc profile="
                          << _qualityProfile << " bitrate=" << bitrate;
                return true;
            }
            _nvencFallback = true;
            LOG(INFO) << "[RTMP] CAP-NVENC-AUTO: h264_nvenc unavailable/failed → "
                         "fallback software libx264 (CPU path)";
        }

        const AVCodec* soft = avcodec_find_encoder_by_name("libx264");
        if (!soft) {
            soft = avcodec_find_encoder(AV_CODEC_ID_H264);
        }
        if (soft && openCodec(soft, soft->name ? soft->name : "libx264", bitrate)) {
            LOG(INFO) << "[RTMP] Using software encoder " << _codecName
                      << " profile=" << _qualityProfile << " bitrate=" << bitrate;
            return true;
        }
        return false;
    };

    std::string profile = _qualityProfile;
    bool opened = tryOpenWithProfile(profile);
    if (!opened && qualityAutoDowngrade) {
        std::string next = downgradeProfile(profile);
        while (!opened && next != profile) {
            LOG(INFO) << "[RTMP] CAP-NVENC-AUTO quality downgrade " << profile
                      << " -> " << next;
            profile = next;
            _qualityDowngraded = true;
            opened = tryOpenWithProfile(profile);
            next = downgradeProfile(profile);
        }
    }

    // CPU environments often lack NVENC: still succeed on software path even if
    // qualityAutoDowngrade is false — mark fallback for parity.
    if (!opened) {
        LOG(ERROR) << "[RTMP] H.264 codec open failed (nvenc + software)";
        release();
        return false;
    }

    // Force a software-path downgrade marker when NVENC was requested but unavailable,
    // so parity can assert CAP-NVENC-AUTO behavior without NVIDIA hardware.
    if (nvencAuto && _nvencFallback && qualityAutoDowngrade && !_qualityDowngraded) {
        // Align with Python: when hardware path fails, settle on medium unless already low.
        if (_qualityProfile == std::string("high")) {
            int bitrate = presetFor("medium").bitrate;
            _bitRate = bitrate;
            if (_codecCtx) {
                _codecCtx->bit_rate = bitrate;
                _codecCtx->rc_buffer_size = bitrate / 2;
                _codecCtx->rc_max_rate = static_cast<int64_t>(bitrate * 1.2);
                _codecCtx->rc_min_rate = static_cast<int64_t>(bitrate * 0.8);
            }
            _qualityProfile = "medium";
            _qualityDowngraded = true;
            LOG(INFO) << "[RTMP] CAP-NVENC-AUTO quality downgraded high -> medium after NVENC miss";
        }
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

    _swsCtx = sws_getContext(
        width, height, AV_PIX_FMT_BGR24,
        width, height, AV_PIX_FMT_YUV420P,
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
    _yuvFrame->width = width;
    _yuvFrame->height = height;

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

    LOG(INFO) << "[RTMP] Encoder initialized successfully: " << rtmpUrl
              << " codec=" << _codecName
              << " quality=" << _qualityProfile
              << " nvenc_fallback=" << (_nvencFallback ? "true" : "false")
              << " quality_downgraded=" << (_qualityDowngraded ? "true" : "false");
    return true;
}

bool RTMPEncoder::encodeAndPush(const cv::Mat& frame) {
    if (!_initialized) {
        LOG(ERROR) << "[RTMP] Encoder not initialized";
        _pushedFail++;
        return false;
    }

    if (frame.empty()) {
        LOG(WARNING) << "[RTMP] Empty frame received";
        _pushedFail++;
        return false;
    }

    const uint8_t* srcData[1] = {frame.data};
    int srcLinesize[1] = {static_cast<int>(frame.step[0])};

    int ret = sws_scale(_swsCtx, srcData, srcLinesize, 0, _height,
                       _yuvFrame->data, _yuvFrame->linesize);
    if (ret < 0) {
        LOG(ERROR) << "[RTMP] Failed to convert color space";
        _pushedFail++;
        return false;
    }

    _yuvFrame->pts = _frameIndex;
    _frameIndex++;

    ret = avcodec_send_frame(_codecCtx, _yuvFrame);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        LOG(ERROR) << "[RTMP] Failed to send frame: " << errbuf;
        _pushedFail++;
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
            _pushedFail++;
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
            _pushedFail++;
            return false;
        }

        av_packet_unref(_packet);
    }

    _pushedOk++;
    return true;
}

void RTMPEncoder::release() {
    if (!_initialized && !_outputCtx) {
        return;
    }

    LOG(INFO) << "[RTMP] Releasing encoder resources...";

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

    LOG(INFO) << "[RTMP] Encoder resources released";
}
