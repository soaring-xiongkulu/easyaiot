#ifndef EASYAIOT_RK3588_FRAME_VIEW_H
#define EASYAIOT_RK3588_FRAME_VIEW_H

#include <cstdint>
#include <memory>

namespace runtime::rk3588 {

enum class FrameFormat : uint8_t { BGR888, RGB888, NV12 };

/**
 * Non-owning image description with an optional owner token. For MPP frames,
 * owner keeps MppFrame/MppBuffer alive while RGA/NPU consumes the DMA-BUF.
 */
struct FrameView {
    int dmaFd{-1};
    void* virtualAddress{nullptr};
    int width{0};
    int height{0};
    int widthStride{0};
    int heightStride{0};
    FrameFormat format{FrameFormat::BGR888};
    uint64_t sequence{0};
    uint64_t bufferPoolId{0};
    std::shared_ptr<void> owner;

    bool valid() const {
        return width > 0 && height > 0 && (dmaFd >= 0 || virtualAddress != nullptr);
    }
    bool dmaBacked() const { return dmaFd >= 0; }
};

}  // namespace runtime::rk3588

#endif
