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

/**
 * RTMP推流编码器
 * 功能：将OpenCV Mat图像编码为H.264并推送到RTMP服务器
 * 特性：低延迟配置、NVENC 自动回退软件编码、画质档位
 */
class RTMPEncoder {
public:
    RTMPEncoder();
    ~RTMPEncoder();

    /**
     * 初始化RTMP编码器
     * @param rtmpUrl RTMP推流地址
     * @param width 视频宽度
     * @param height 视频高度
     * @param fps 视频帧率
     * @param nvencAuto CAP-NVENC-AUTO：优先尝试 h264_nvenc，失败回退 libx264
     * @param qualityProfile low|medium|high（码率档位）
     * @param qualityAutoDowngrade 编码失败时降档（与 Python AUTO_QUALITY 对齐的最小行为）
     * @return 成功返回true，失败返回false
     */
    bool init(const std::string& rtmpUrl, int width, int height, int fps,
              bool nvencAuto = false,
              const std::string& qualityProfile = "high",
              bool qualityAutoDowngrade = false);

    bool encodeAndPush(const cv::Mat& frame);

    void release();

    bool isInitialized() const { return _initialized; }

    // Parity / G-4.4 stream sampling helpers
    int width() const { return _width; }
    int height() const { return _height; }
    int fps() const { return _fps; }
    int64_t bitRate() const { return _bitRate; }
    int64_t pushedOk() const { return _pushedOk; }
    int64_t pushedFail() const { return _pushedFail; }
    const std::string& rtmpUrl() const { return _rtmpUrl; }
    const std::string& codecName() const { return _codecName; }
    const std::string& qualityProfile() const { return _qualityProfile; }
    bool nvencRequested() const { return _nvencRequested; }
    bool nvencFallback() const { return _nvencFallback; }
    bool qualityDowngraded() const { return _qualityDowngraded; }

private:
    struct QualityPreset {
        const char* name;
        int bitrate;
    };

    static QualityPreset presetFor(const std::string& name);
    static std::string downgradeProfile(const std::string& name);

    bool openCodec(const AVCodec* codec, const std::string& codecLabel, int bitrate);

    AVFormatContext* _outputCtx;
    AVCodecContext* _codecCtx;
    AVStream* _videoStream;
    SwsContext* _swsCtx;
    AVFrame* _yuvFrame;
    AVPacket* _packet;

    int64_t _frameIndex;
    int _width;
    int _height;
    int _fps;
    int64_t _bitRate{2500000};
    int64_t _pushedOk{0};
    int64_t _pushedFail{0};
    std::string _rtmpUrl;
    bool _initialized;

    std::string _codecName{"libx264"};
    std::string _qualityProfile{"high"};
    bool _nvencRequested{false};
    bool _nvencFallback{false};
    bool _qualityDowngraded{false};
};

#endif // RTMP_ENCODER_H
