#ifndef RUNTIME_FFMPEG_HW_H
#define RUNTIME_FFMPEG_HW_H

#include <string>

extern "C" {
#include "libavcodec/avcodec.h"
#include "libavutil/buffer.h"
#include "libavutil/hwcontext.h"
#include "libavutil/pixfmt.h"
}

namespace runtime {

struct HwDecodeState {
    AVBufferRef* hwDeviceCtx{nullptr};
    bool usingCuda{false};
    std::string decodeEp{"cpu"};
};

/** Create CUDA hwdevice context for deviceId. Returns true on success. */
bool createCudaHwDevice(AVBufferRef** out, int deviceId);

/**
 * Open a video decoder. When preferHw && !forceSoft, tries CUDA NVDEC
 * (hw_device_ctx + get_format). On failure falls back to software decode once.
 * On success *codecCtxOut is allocated and opened; caller owns it.
 */
bool openVideoDecoder(AVCodecContext** codecCtxOut,
                      AVCodecParameters* par,
                      bool preferHw,
                      bool forceSoft,
                      int deviceId,
                      HwDecodeState* state);

void releaseHwDecodeState(HwDecodeState* state);

/** True if frame is a CUDA hw frame. */
bool isCudaHwFrame(const AVFrame* frame);

/**
 * If src is CUDA, transfer to *dst (must be allocated empty AVFrame).
 * Returns pointer to software frame to feed sws (dst on transfer, else src).
 * On transfer failure returns nullptr.
 */
AVFrame* ensureSoftwareFrame(AVFrame* src, AVFrame* dst);

}  // namespace runtime

#endif
