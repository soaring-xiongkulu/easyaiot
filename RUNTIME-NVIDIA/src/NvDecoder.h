#pragma once

#include <cstdint>
#include <memory>
#include <string>

extern "C" {
#include <libavutil/frame.h>
struct AVCodecContext;
struct AVFormatContext;
struct AVBufferRef;
struct AVPacket;
}

namespace easyaiot::nvidia {

struct DeviceFrame {
    std::uint64_t sequence{0};
    std::shared_ptr<AVFrame> frame;
    int width{0};
    int height{0};
};

class NvDecoder {
public:
    NvDecoder(std::string source, int cudaDevice, int extraSurfaces);
    ~NvDecoder();

    NvDecoder(const NvDecoder&) = delete;
    NvDecoder& operator=(const NvDecoder&) = delete;

    DeviceFrame next();
    std::string codecName() const;

private:
    static AVPixelFormat selectCudaFormat(AVCodecContext* context, const AVPixelFormat* formats);
    void open();
    DeviceFrame receive();

    std::string source_;
    int cudaDevice_{0};
    int extraSurfaces_{16};
    std::uint64_t sequence_{0};
    int videoStream_{-1};
    bool inputEnded_{false};
    struct AVFormatContext* format_{nullptr};
    struct AVCodecContext* codec_{nullptr};
    struct AVBufferRef* hardwareDevice_{nullptr};
    struct AVPacket* packet_{nullptr};
    struct AVFrame* receiveFrame_{nullptr};
};

}  // namespace easyaiot::nvidia
