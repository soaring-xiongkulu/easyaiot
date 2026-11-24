#ifndef EASYAIOT_RK3588_MPP_DECODER_H
#define EASYAIOT_RK3588_MPP_DECODER_H

#include "rk3588/frame_view.h"

#include <cstddef>
#include <cstdint>

#include <rk_mpi.h>

extern "C" {
#include <libavcodec/avcodec.h>
}

namespace runtime::rk3588 {

class MppDecoder {
public:
    MppDecoder() = default;
    ~MppDecoder();

    MppDecoder(const MppDecoder&) = delete;
    MppDecoder& operator=(const MppDecoder&) = delete;

    bool open(const AVCodecParameters* parameters, int outputBufferCount);
    void close();
    bool submit(const AVPacket* packet);
    bool receive(FrameView& frame);
    bool flush();
    bool isOpen() const { return context_ != nullptr; }
    static bool supports(AVCodecID codec);

private:
    struct FrameOwner;
    static MppCodingType codingType(AVCodecID codec);
    bool submitBytes(const uint8_t* data, size_t size, int64_t pts, int64_t dts, bool extra);
    bool handleInfoChange(MppFrame frame);

    MppCtx context_{nullptr};
    MppApi* api_{nullptr};
    MppBufferGroup outputGroup_{nullptr};
    MppBufferGroup packetGroup_{nullptr};
    int outputBufferCount_{8};
    uint64_t bufferPoolId_{0};
};

}  // namespace runtime::rk3588

#endif
