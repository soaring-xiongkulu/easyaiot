#include "ffmpeg_hw.h"

#include <cstdio>
#include <glog/logging.h>

extern "C" {
#include "libavutil/error.h"
#include "libavutil/pixdesc.h"
}

namespace runtime {

namespace {

enum AVPixelFormat getHwFormatCuda(AVCodecContext* /*ctx*/, const enum AVPixelFormat* pixFmts) {
    for (const enum AVPixelFormat* p = pixFmts; *p != AV_PIX_FMT_NONE; ++p) {
        if (*p == AV_PIX_FMT_CUDA) {
            return *p;
        }
    }
    return AV_PIX_FMT_NONE;
}

bool openSoftDecoder(AVCodecContext** codecCtxOut, AVCodecParameters* par) {
    const AVCodec* codec = avcodec_find_decoder(par->codec_id);
    if (!codec) {
        LOG(ERROR) << "[HW] avcodec_find_decoder failed codec_id=" << par->codec_id;
        return false;
    }
    AVCodecContext* ctx = avcodec_alloc_context3(codec);
    if (!ctx) {
        return false;
    }
    if (avcodec_parameters_to_context(ctx, par) != 0) {
        avcodec_free_context(&ctx);
        return false;
    }
    if (avcodec_open2(ctx, codec, nullptr) < 0) {
        avcodec_free_context(&ctx);
        return false;
    }
    *codecCtxOut = ctx;
    return true;
}

bool openCudaDecoder(AVCodecContext** codecCtxOut,
                     AVCodecParameters* par,
                     int deviceId,
                     HwDecodeState* state) {
    if (!createCudaHwDevice(&state->hwDeviceCtx, deviceId)) {
        return false;
    }

    const AVCodec* codec = avcodec_find_decoder(par->codec_id);
    if (!codec) {
        releaseHwDecodeState(state);
        return false;
    }

    AVCodecContext* ctx = avcodec_alloc_context3(codec);
    if (!ctx) {
        releaseHwDecodeState(state);
        return false;
    }
    if (avcodec_parameters_to_context(ctx, par) != 0) {
        avcodec_free_context(&ctx);
        releaseHwDecodeState(state);
        return false;
    }

    ctx->hw_device_ctx = av_buffer_ref(state->hwDeviceCtx);
    if (!ctx->hw_device_ctx) {
        avcodec_free_context(&ctx);
        releaseHwDecodeState(state);
        return false;
    }
    ctx->get_format = getHwFormatCuda;

    if (avcodec_open2(ctx, codec, nullptr) < 0) {
        LOG(WARNING) << "[HW] CUDA decoder open failed, will fall back to software";
        avcodec_free_context(&ctx);
        releaseHwDecodeState(state);
        return false;
    }

    *codecCtxOut = ctx;
    state->usingCuda = true;
    state->decodeEp = "cuda";
    LOG(INFO) << "[HW] NVDEC enabled decode_ep=cuda device_id=" << deviceId
              << " codec=" << codec->name;
    return true;
}

}  // namespace

bool createCudaHwDevice(AVBufferRef** out, int deviceId) {
    if (!out) {
        return false;
    }
    *out = nullptr;

    enum AVHWDeviceType type = av_hwdevice_find_type_by_name("cuda");
    if (type == AV_HWDEVICE_TYPE_NONE) {
        LOG(INFO) << "[HW] FFmpeg build has no CUDA hwdevice";
        return false;
    }

    char device[16];
    snprintf(device, sizeof(device), "%d", deviceId < 0 ? 0 : deviceId);
    int ret = av_hwdevice_ctx_create(out, type, device, nullptr, 0);
    if (ret < 0) {
        char errbuf[128];
        av_strerror(ret, errbuf, sizeof(errbuf));
        LOG(WARNING) << "[HW] av_hwdevice_ctx_create(cuda) failed: " << errbuf;
        *out = nullptr;
        return false;
    }
    return true;
}

bool openVideoDecoder(AVCodecContext** codecCtxOut,
                      AVCodecParameters* par,
                      bool preferHw,
                      bool forceSoft,
                      int deviceId,
                      HwDecodeState* state) {
    if (!codecCtxOut || !par || !state) {
        return false;
    }
    *codecCtxOut = nullptr;
    releaseHwDecodeState(state);
    state->usingCuda = false;
    state->decodeEp = "cpu";

    const bool tryHw = preferHw && !forceSoft;
    if (tryHw) {
        if (openCudaDecoder(codecCtxOut, par, deviceId, state)) {
            return true;
        }
        LOG(INFO) << "[HW] Falling back to software decode";
    }

    if (!openSoftDecoder(codecCtxOut, par)) {
        LOG(ERROR) << "[HW] Software decoder open failed";
        return false;
    }
    state->usingCuda = false;
    state->decodeEp = "cpu";
    LOG(INFO) << "[HW] Using software decode decode_ep=cpu";
    return true;
}

void releaseHwDecodeState(HwDecodeState* state) {
    if (!state) {
        return;
    }
    if (state->hwDeviceCtx) {
        av_buffer_unref(&state->hwDeviceCtx);
        state->hwDeviceCtx = nullptr;
    }
    state->usingCuda = false;
}

bool isCudaHwFrame(const AVFrame* frame) {
    return frame && frame->format == AV_PIX_FMT_CUDA;
}

AVFrame* ensureSoftwareFrame(AVFrame* src, AVFrame* dst) {
    if (!src || !dst) {
        return nullptr;
    }
    if (!isCudaHwFrame(src)) {
        return src;
    }
    av_frame_unref(dst);
    int ret = av_hwframe_transfer_data(dst, src, 0);
    if (ret < 0) {
        char errbuf[128];
        av_strerror(ret, errbuf, sizeof(errbuf));
        LOG(WARNING) << "[HW] av_hwframe_transfer_data failed: " << errbuf;
        return nullptr;
    }
    dst->pts = src->pts;
    dst->pkt_dts = src->pkt_dts;
    return dst;
}

}  // namespace runtime
