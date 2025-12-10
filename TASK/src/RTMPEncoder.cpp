#include "RTMPEncoder.h"
#include <glog/logging.h>

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

bool RTMPEncoder::init(const std::string& rtmpUrl, int width, int height, int fps) {
    if (_initialized) {
        LOG(WARNING) << "[RTMP] Encoder already initialized";
        return true;
    }
    
    _rtmpUrl = rtmpUrl;
    _width = width;
    _height = height;
    _fps = fps;
    
    LOG(INFO) << "[RTMP] Initializing encoder: " << rtmpUrl 
              << " (" << width << "x" << height << "@" << fps << "fps)";
    
    // 1. Allocate output context
    int ret = avformat_alloc_output_context2(&_outputCtx, nullptr, "flv", rtmpUrl.c_str());
    if (ret < 0 || !_outputCtx) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        LOG(ERROR) << "[RTMP] Failed to create output context: " << errbuf;
        return false;
    }
    
    // 2. Find H.264 encoder
    const AVCodec* codec = avcodec_find_encoder(AV_CODEC_ID_H264);
    if (!codec) {
        LOG(ERROR) << "[RTMP] H.264 codec not found";
        release();
        return false;
    }
    
    // 3. Create encoder context
    _codecCtx = avcodec_alloc_context3(codec);
    if (!_codecCtx) {
        LOG(ERROR) << "[RTMP] Failed to allocate codec context";
        release();
        return false;
    }
    
    _codecCtx->width = width;
    _codecCtx->height = height;
    _codecCtx->time_base = AVRational{1, fps};
    _codecCtx->framerate = AVRational{fps, 1};
    _codecCtx->pix_fmt = AV_PIX_FMT_YUV420P;
    _codecCtx->bit_rate = 2500000;  // 2.5Mbps - 平衡画质和带宽
    _codecCtx->gop_size = 10;       // GOP=10帧(400ms) - 平衡延迟和编码效率
    _codecCtx->max_b_frames = 0;    // No B-frames for low latency
    _codecCtx->rc_buffer_size = _codecCtx->bit_rate / 2;  // 适度缓冲
    _codecCtx->rc_max_rate = _codecCtx->bit_rate * 1.2;
    _codecCtx->rc_min_rate = _codecCtx->bit_rate * 0.8;
    _codecCtx->thread_count = 4;    // 多线程加速编码
    
    // H.264 balanced low-latency parameters
    av_opt_set(_codecCtx->priv_data, "preset", "veryfast", 0);  // 平衡速度和质量
    av_opt_set(_codecCtx->priv_data, "tune", "zerolatency", 0);
    av_opt_set(_codecCtx->priv_data, "profile", "main", 0);     // Main profile更好的压缩
    av_opt_set(_codecCtx->priv_data, "crf", "23", 0);           // 质量优先
    
    if (_outputCtx->oformat->flags & AVFMT_GLOBALHEADER) {
        _codecCtx->flags |= AV_CODEC_FLAG_GLOBAL_HEADER;
    }
    
    // 4. Open encoder
    ret = avcodec_open2(_codecCtx, codec, nullptr);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        LOG(ERROR) << "[RTMP] Failed to open codec: " << errbuf;
        release();
        return false;
    }
    
    // 5. Create video stream
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
    
    // 6. Open RTMP output with low latency options
    AVDictionary* options = nullptr;
    av_dict_set(&options, "rtmp_buffer", "100", 0);      // Small RTMP buffer (100ms)
    av_dict_set(&options, "rtmp_live", "live", 0);       // Live stream mode
    av_dict_set(&options, "buffer_size", "65536", 0);    // Small IO buffer
    
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
    
    // 7. Write stream header with low latency muxer options
    AVDictionary* muxer_opts = nullptr;
    av_dict_set(&muxer_opts, "flvflags", "no_duration_filesize", 0);  // No metadata overhead
    av_dict_set(&muxer_opts, "fflags", "nobuffer", 0);                // No buffering
    
    ret = avformat_write_header(_outputCtx, &muxer_opts);
    av_dict_free(&muxer_opts);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        LOG(ERROR) << "[RTMP] Failed to write header: " << errbuf;
        release();
        return false;
    }
    
    // 8. Initialize color space converter (BGR -> YUV420P)
    _swsCtx = sws_getContext(
        width, height, AV_PIX_FMT_BGR24,       // Input: OpenCV BGR format
        width, height, AV_PIX_FMT_YUV420P,     // Output: YUV420P
        SWS_BILINEAR, nullptr, nullptr, nullptr
    );
    if (!_swsCtx) {
        LOG(ERROR) << "[RTMP] Failed to create sws context";
        release();
        return false;
    }
    
    // 9. Allocate YUV frame
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
    
    // 10. Allocate packet
    _packet = av_packet_alloc();
    if (!_packet) {
        LOG(ERROR) << "[RTMP] Failed to allocate packet";
        release();
        return false;
    }
    
    _initialized = true;
    _frameIndex = 0;
    
    LOG(INFO) << "[RTMP] Encoder initialized successfully: " << rtmpUrl;
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
    
    // 1. Convert BGR to YUV420P
    const uint8_t* srcData[1] = {frame.data};
    int srcLinesize[1] = {static_cast<int>(frame.step[0])};
    
    int ret = sws_scale(_swsCtx, srcData, srcLinesize, 0, _height, 
                       _yuvFrame->data, _yuvFrame->linesize);
    if (ret < 0) {
        LOG(ERROR) << "[RTMP] Failed to convert color space";
        return false;
    }
    
    // 2. Set frame PTS
    _yuvFrame->pts = _frameIndex;
    _frameIndex++;
    
    // 3. Send frame to encoder
    ret = avcodec_send_frame(_codecCtx, _yuvFrame);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        LOG(ERROR) << "[RTMP] Failed to send frame: " << errbuf;
        return false;
    }
    
    // 4. Receive and write encoded packets
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
        
        // Rescale packet timestamp
        av_packet_rescale_ts(_packet, _codecCtx->time_base, _videoStream->time_base);
        _packet->stream_index = _videoStream->index;
        
        // Write packet to RTMP stream
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
    
    LOG(INFO) << "[RTMP] Releasing encoder resources...";
    
    // Flush encoder
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
    
    // Write trailer
    if (_outputCtx && _initialized) {
        av_write_trailer(_outputCtx);
    }
    
    // Free resources
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
