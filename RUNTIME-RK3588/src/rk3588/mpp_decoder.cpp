#include "rk3588/mpp_decoder.h"

#include <chrono>
#include <algorithm>
#include <atomic>
#include <cstring>
#include <glog/logging.h>
#include <thread>

#include <mpp_buffer.h>
#include <mpp_frame.h>
#include <mpp_packet.h>
#include <rk_mpi_cmd.h>

namespace runtime::rk3588 {
namespace {
std::atomic<uint64_t> g_bufferPoolIds{1};
}

struct MppDecoder::FrameOwner {
    explicit FrameOwner(MppFrame value) : frame(value) {}
    ~FrameOwner() {
        if (frame) mpp_frame_deinit(&frame);
    }
    MppFrame frame{nullptr};
};

MppDecoder::~MppDecoder() { close(); }

MppCodingType MppDecoder::codingType(AVCodecID codec) {
    switch (codec) {
        case AV_CODEC_ID_H264: return MPP_VIDEO_CodingAVC;
        case AV_CODEC_ID_HEVC: return MPP_VIDEO_CodingHEVC;
        case AV_CODEC_ID_VP8: return MPP_VIDEO_CodingVP8;
        case AV_CODEC_ID_VP9: return MPP_VIDEO_CodingVP9;
        case AV_CODEC_ID_AV1: return MPP_VIDEO_CodingAV1;
        case AV_CODEC_ID_MJPEG: return MPP_VIDEO_CodingMJPEG;
        default: return MPP_VIDEO_CodingUnused;
    }
}

bool MppDecoder::supports(AVCodecID codec) {
    return codingType(codec) != MPP_VIDEO_CodingUnused;
}

bool MppDecoder::open(const AVCodecParameters* parameters, int outputBufferCount) {
    close();
    if (!parameters || !supports(parameters->codec_id)) {
        LOG(ERROR) << "[MPP] 不支持的输入编码";
        return false;
    }
    outputBufferCount_ = std::max(4, std::min(32, outputBufferCount));
    if (mpp_create(&context_, &api_) != MPP_OK || !context_ || !api_) {
        LOG(ERROR) << "[MPP] mpp_create 失败";
        close();
        return false;
    }
    RK_U32 split = 1;
    if (api_->control(context_, MPP_DEC_SET_PARSER_SPLIT_MODE, &split) != MPP_OK) {
        LOG(ERROR) << "[MPP] 无法启用 parser split";
        close();
        return false;
    }
    if (mpp_init(context_, MPP_CTX_DEC, codingType(parameters->codec_id)) != MPP_OK) {
        LOG(ERROR) << "[MPP] mpp_init 解码器失败";
        close();
        return false;
    }
    bufferPoolId_ = g_bufferPoolIds.fetch_add(1, std::memory_order_relaxed);
    MppFrameFormat outputFormat = MPP_FMT_YUV420SP;
    if (api_->control(context_, MPP_DEC_SET_OUTPUT_FORMAT, &outputFormat) != MPP_OK) {
        LOG(ERROR) << "[MPP] 无法强制线性 NV12 输出";
        close();
        return false;
    }
    if (mpp_buffer_group_get_internal(&packetGroup_, MPP_BUFFER_TYPE_DMA_HEAP) != MPP_OK) {
        LOG(ERROR) << "[MPP] 压缩包 DMA 缓冲组创建失败";
        close();
        return false;
    }
    // FFmpeg demuxers expose codec headers separately for MP4/FLV style streams.
    if (parameters->extradata && parameters->extradata_size > 0 &&
        !submitBytes(parameters->extradata, static_cast<size_t>(parameters->extradata_size),
                     AV_NOPTS_VALUE, AV_NOPTS_VALUE, true)) {
        LOG(ERROR) << "[MPP] codec extradata 提交失败";
        close();
        return false;
    }
    LOG(INFO) << "[MPP] 解码器初始化完成 codec_id=" << parameters->codec_id
              << " buffers=" << outputBufferCount_ << " output=NV12 DMA-BUF";
    return true;
}

void MppDecoder::close() {
    if (context_ && api_) api_->reset(context_);
    if (outputGroup_) {
        mpp_buffer_group_put(outputGroup_);
        outputGroup_ = nullptr;
    }
    if (packetGroup_) {
        mpp_buffer_group_put(packetGroup_);
        packetGroup_ = nullptr;
    }
    if (context_) {
        mpp_destroy(context_);
        context_ = nullptr;
    }
    api_ = nullptr;
    bufferPoolId_ = 0;
}

bool MppDecoder::submitBytes(const uint8_t* data, size_t size,
                             int64_t pts, int64_t dts, bool extra) {
    if (!context_ || !packetGroup_ || !data || size == 0) return false;
    MppBuffer buffer = nullptr;
    if (mpp_buffer_get(packetGroup_, &buffer, size) != MPP_OK || !buffer) return false;
    std::memcpy(mpp_buffer_get_ptr(buffer), data, size);
    MppPacket packet = nullptr;
    if (mpp_packet_init_with_buffer(&packet, buffer) != MPP_OK || !packet) {
        mpp_buffer_put(buffer);
        return false;
    }
    mpp_packet_set_pos(packet, mpp_buffer_get_ptr(buffer));
    mpp_packet_set_length(packet, size);
    if (pts != AV_NOPTS_VALUE) mpp_packet_set_pts(packet, pts);
    if (dts != AV_NOPTS_VALUE) mpp_packet_set_dts(packet, dts);
    if (extra) mpp_packet_set_extra_data(packet);

    MPP_RET ret = MPP_NOK;
    for (int attempt = 0; attempt < 100; ++attempt) {
        ret = api_->decode_put_packet(context_, packet);
        if (ret == MPP_OK) break;
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    mpp_packet_deinit(&packet);
    mpp_buffer_put(buffer);
    return ret == MPP_OK;
}

bool MppDecoder::submit(const AVPacket* packet) {
    if (!packet || !packet->data || packet->size <= 0) return false;
    return submitBytes(packet->data, static_cast<size_t>(packet->size),
                       packet->pts, packet->dts, false);
}

bool MppDecoder::handleInfoChange(MppFrame frame) {
    const size_t bytes = mpp_frame_get_buf_size(frame);
    if (bytes == 0) return false;
    if (!outputGroup_ &&
        mpp_buffer_group_get_internal(&outputGroup_, MPP_BUFFER_TYPE_DMA_HEAP) != MPP_OK) {
        LOG(ERROR) << "[MPP] 输出 DMA 缓冲组创建失败";
        return false;
    }
    if (mpp_buffer_group_limit_config(outputGroup_, bytes, outputBufferCount_) != MPP_OK ||
        api_->control(context_, MPP_DEC_SET_EXT_BUF_GROUP, outputGroup_) != MPP_OK ||
        api_->control(context_, MPP_DEC_SET_INFO_CHANGE_READY, nullptr) != MPP_OK) {
        LOG(ERROR) << "[MPP] 外部缓冲组配置失败 bytes=" << bytes;
        return false;
    }
    LOG(INFO) << "[MPP] 解码缓冲组就绪 "
              << mpp_frame_get_width(frame) << "x" << mpp_frame_get_height(frame)
              << " stride=" << mpp_frame_get_hor_stride(frame) << "x"
              << mpp_frame_get_ver_stride(frame) << " bytes=" << bytes
              << " count=" << outputBufferCount_;
    return true;
}

bool MppDecoder::receive(FrameView& output) {
    output = {};
    if (!context_) return false;
    for (int attempt = 0; attempt < 4; ++attempt) {
        MppFrame frame = nullptr;
        const MPP_RET ret = api_->decode_get_frame(context_, &frame);
        if (ret != MPP_OK || !frame) return false;
        if (mpp_frame_get_info_change(frame)) {
            const bool ok = handleInfoChange(frame);
            mpp_frame_deinit(&frame);
            if (!ok) return false;
            continue;
        }
        if (mpp_frame_get_errinfo(frame) || mpp_frame_get_discard(frame)) {
            LOG(WARNING) << "[MPP] 丢弃损坏帧 err=" << mpp_frame_get_errinfo(frame)
                         << " discard=" << mpp_frame_get_discard(frame);
            mpp_frame_deinit(&frame);
            continue;
        }
        if ((mpp_frame_get_fmt(frame) & MPP_FRAME_FMT_MASK) != MPP_FMT_YUV420SP) {
            LOG(ERROR) << "[MPP] 输出不是线性 NV12 fmt=" << mpp_frame_get_fmt(frame);
            mpp_frame_deinit(&frame);
            return false;
        }
        MppBuffer buffer = mpp_frame_get_buffer(frame);
        if (!buffer) {
            mpp_frame_deinit(&frame);
            return false;
        }
        auto owner = std::make_shared<FrameOwner>(frame);
        output.dmaFd = mpp_buffer_get_fd(buffer);
        output.virtualAddress = mpp_buffer_get_ptr(buffer);
        output.width = static_cast<int>(mpp_frame_get_width(frame));
        output.height = static_cast<int>(mpp_frame_get_height(frame));
        output.widthStride = static_cast<int>(mpp_frame_get_hor_stride(frame));
        output.heightStride = static_cast<int>(mpp_frame_get_ver_stride(frame));
        output.format = FrameFormat::NV12;
        output.sequence = static_cast<uint64_t>(std::max<RK_S64>(0, mpp_frame_get_pts(frame)));
        output.bufferPoolId = bufferPoolId_;
        output.owner = std::static_pointer_cast<void>(owner);
        return output.valid();
    }
    return false;
}

bool MppDecoder::flush() {
    if (!context_) return false;
    MppPacket packet = nullptr;
    if (mpp_packet_init(&packet, nullptr, 0) != MPP_OK || !packet) return false;
    mpp_packet_set_eos(packet);
    const MPP_RET ret = api_->decode_put_packet(context_, packet);
    mpp_packet_deinit(&packet);
    return ret == MPP_OK;
}

}  // namespace runtime::rk3588
