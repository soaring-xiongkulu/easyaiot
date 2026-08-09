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
 * 特性：低延迟配置、自动资源管理
 */
class RTMPEncoder {
public:
    RTMPEncoder();
    ~RTMPEncoder();

    /**
     * 初始化RTMP编码器
     * @param rtmpUrl RTMP推流地址，例如: rtmp://localhost:1935/live/stream_test
     * @param width 视频宽度
     * @param height 视频高度
     * @param fps 视频帧率
     * @return 成功返回true，失败返回false
     */
    bool init(const std::string& rtmpUrl, int width, int height, int fps);

    /**
     * 编码并推送一帧图像
     * @param frame OpenCV Mat图像（BGR24格式）
     * @return 成功返回true，失败返回false
     */
    bool encodeAndPush(const cv::Mat& frame);

    /**
     * 释放资源
     */
    void release();

    /**
     * 检查编码器是否已初始化
     */
    bool isInitialized() const { return _initialized; }

    // Parity / G-4.4 stream sampling helpers
    int width() const { return _width; }
    int height() const { return _height; }
    int fps() const { return _fps; }
    int64_t bitRate() const { return _bitRate; }
    int64_t pushedOk() const { return _pushedOk; }
    int64_t pushedFail() const { return _pushedFail; }
    const std::string& rtmpUrl() const { return _rtmpUrl; }

private:
    AVFormatContext* _outputCtx;    // 输出格式上下文
    AVCodecContext* _codecCtx;      // 编码器上下文
    AVStream* _videoStream;         // 视频流
    SwsContext* _swsCtx;            // 颜色空间转换上下文
    AVFrame* _yuvFrame;             // YUV帧
    AVPacket* _packet;              // 编码后的数据包
    
    int64_t _frameIndex;            // 当前帧索引（用于PTS计算）
    int _width;                     // 视频宽度
    int _height;                    // 视频高度
    int _fps;                       // 视频帧率
    int64_t _bitRate{2500000};      // 目标码率（与 init 一致）
    int64_t _pushedOk{0};           // 成功推送帧计数（parity）
    int64_t _pushedFail{0};         // 失败推送帧计数（parity）
    std::string _rtmpUrl;           // RTMP推流地址
    bool _initialized;              // 初始化标志
};

#endif // RTMP_ENCODER_H

