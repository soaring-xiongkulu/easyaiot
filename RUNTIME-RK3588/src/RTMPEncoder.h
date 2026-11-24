#ifndef RTMP_ENCODER_H
#define RTMP_ENCODER_H

#include <string>
#include <opencv2/opencv.hpp>

extern "C" {
#include "libavcodec/avcodec.h"
#include "libavformat/avformat.h"
#include "libswscale/swscale.h"
#include "libavutil/opt.h"
#include "libavutil/imgutils.h"
}

struct RtmpEncoderOptions {
    bool preferHw{true};
    bool forceSoft{false};
    int gpuDeviceId{0};
    std::string nvencPreset{"p3"};
    /** Target ABR bitrate in bits/sec; <=0 = auto by resolution (align VIDEO clarity). */
    int64_t bitRate{0};
    /** GOP size in frames; <=0 = 2 * fps (keyframe ~every 2s). */
    int gopSize{0};
};

/**
 * RTMP推流编码器
 * 功能：将OpenCV Mat图像编码为H.264并推送到RTMP服务器
 * 优先 h264_nvenc，失败回退 libx264
 */
class RTMPEncoder {
public:
    RTMPEncoder();
    ~RTMPEncoder();

    bool init(const std::string& rtmpUrl, int width, int height, int fps,
              const RtmpEncoderOptions& opts = RtmpEncoderOptions());

    bool encodeAndPush(const cv::Mat& frame);

    void release();

    bool isInitialized() const { return _initialized; }

    /** h264_nvenc | libx264 | none */
    const std::string& encodeEp() const { return _encodeEp; }

private:
    bool openEncoder(const AVCodec* codec, bool isNvenc, const RtmpEncoderOptions& opts);
    static int alignDim(int v, int align = 16);
    static int64_t defaultBitRate(int width, int height);

    AVFormatContext* _outputCtx;    // 输出格式上下文
    AVCodecContext* _codecCtx;      // 编码器上下文
    AVStream* _videoStream;         // 视频流
    SwsContext* _swsCtx;            // 颜色空间转换上下文
    AVFrame* _yuvFrame;             // YUV帧
    AVPacket* _packet;              // 编码后的数据包

    int64_t _frameIndex;
    int _srcWidth;                  // OpenCV 输入宽
    int _srcHeight;
    int _encWidth;                  // 编码器宽（NVENC 16 对齐）
    int _encHeight;
    int _fps;
    std::string _rtmpUrl;
    std::string _encodeEp{"none"};
    bool _initialized;
};

#endif // RTMP_ENCODER_H
