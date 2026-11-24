#ifndef RTMP_ENCODER_H
#define RTMP_ENCODER_H

#include <cstdint>
#include <opencv2/opencv.hpp>
#include <string>

extern "C" {
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/imgutils.h>
#include <libavutil/opt.h>
}

struct RtmpEncoderOptions {
    int64_t bitRate{0};
    int gopSize{0};
};

/** RK3588 MPP-only H.264 RTMP encoder. */
class RTMPEncoder {
public:
    RTMPEncoder() = default;
    ~RTMPEncoder();

    bool init(const std::string& rtmpUrl, int width, int height, int fps,
              const RtmpEncoderOptions& options = {});
    bool encodeAndPush(const cv::Mat& frame);
    void release();
    bool isInitialized() const { return initialized_; }
    const std::string& encodeEp() const { return encodeEp_; }

private:
    bool openEncoder(const AVCodec* codec, const RtmpEncoderOptions& options);
    bool convertWithRga(const cv::Mat& frame);
    bool writeAvailablePackets();
    static int alignDim(int value, int alignment = 16);
    static int64_t defaultBitRate(int width, int height);

    AVFormatContext* output_{nullptr};
    AVCodecContext* codec_{nullptr};
    AVStream* stream_{nullptr};
    AVFrame* nv12_{nullptr};
    AVPacket* packet_{nullptr};
    int64_t frameIndex_{0};
    int sourceWidth_{0};
    int sourceHeight_{0};
    int encodeWidth_{0};
    int encodeHeight_{0};
    int fps_{25};
    std::string url_;
    std::string encodeEp_{"none"};
    bool initialized_{false};
};

#endif
