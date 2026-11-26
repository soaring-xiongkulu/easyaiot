#include "NvDecoder.h"

extern "C" {
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/hwcontext.h>
#include <libavutil/pixdesc.h>
}

#include <cerrno>
#include <cstring>
#include <stdexcept>
#include <utility>

namespace easyaiot::nvidia {
namespace {

std::string ffmpegError(int code) {
    char buffer[AV_ERROR_MAX_STRING_SIZE]{};
    av_strerror(code, buffer, sizeof(buffer));
    return buffer;
}

const AVCodec* findNvdecCodec(AVCodecID id) {
    const char* name = nullptr;
    switch (id) {
        case AV_CODEC_ID_H264: name = "h264_cuvid"; break;
        case AV_CODEC_ID_HEVC: name = "hevc_cuvid"; break;
        case AV_CODEC_ID_AV1: name = "av1_cuvid"; break;
        case AV_CODEC_ID_VP9: name = "vp9_cuvid"; break;
        case AV_CODEC_ID_MJPEG: name = "mjpeg_cuvid"; break;
        default: break;
    }
    if (name) {
        if (const AVCodec* codec = avcodec_find_decoder_by_name(name)) return codec;
    }
    const AVCodec* codec = avcodec_find_decoder(id);
    if (!codec) return nullptr;
    for (int index = 0;; ++index) {
        const AVCodecHWConfig* hardware = avcodec_get_hw_config(codec, index);
        if (!hardware) break;
        if (hardware->device_type == AV_HWDEVICE_TYPE_CUDA &&
            hardware->pix_fmt == AV_PIX_FMT_CUDA) return codec;
    }
    return nullptr;
}

void frameDeleter(AVFrame* frame) { av_frame_free(&frame); }
}  // namespace

NvDecoder::NvDecoder(std::string source, int cudaDevice, int extraSurfaces)
    : source_(std::move(source)), cudaDevice_(cudaDevice), extraSurfaces_(extraSurfaces) {
    open();
}

NvDecoder::~NvDecoder() {
    av_frame_free(&receiveFrame_);
    av_packet_free(&packet_);
    avcodec_free_context(&codec_);
    avformat_close_input(&format_);
    av_buffer_unref(&hardwareDevice_);
}

AVPixelFormat NvDecoder::selectCudaFormat(AVCodecContext*, const AVPixelFormat* formats) {
    for (const AVPixelFormat* candidate = formats; *candidate != AV_PIX_FMT_NONE; ++candidate) {
        if (*candidate == AV_PIX_FMT_CUDA) return *candidate;
    }
    return AV_PIX_FMT_NONE;
}

void NvDecoder::open() {
    AVDictionary* options = nullptr;
    av_dict_set(&options, "rtsp_transport", "tcp", 0);
    av_dict_set(&options, "stimeout", "5000000", 0);
    av_dict_set(&options, "fflags", "nobuffer", 0);
    int result = avformat_open_input(&format_, source_.c_str(), nullptr, &options);
    av_dict_free(&options);
    if (result < 0) throw std::runtime_error("open RTSP failed: " + ffmpegError(result));
    if ((result = avformat_find_stream_info(format_, nullptr)) < 0) {
        throw std::runtime_error("read stream information failed: " + ffmpegError(result));
    }
    videoStream_ = av_find_best_stream(format_, AVMEDIA_TYPE_VIDEO, -1, -1, nullptr, 0);
    if (videoStream_ < 0) throw std::runtime_error("RTSP has no video stream");
    const AVCodecParameters* parameters = format_->streams[videoStream_]->codecpar;
    const AVCodec* decoder = findNvdecCodec(parameters->codec_id);
    if (!decoder) {
        throw std::runtime_error("NVDEC/CUVID decoder is unavailable for source codec; software decode is forbidden");
    }

    const std::string device = std::to_string(cudaDevice_);
    result = av_hwdevice_ctx_create(&hardwareDevice_, AV_HWDEVICE_TYPE_CUDA,
                                    device.c_str(), nullptr, 0);
    if (result < 0) throw std::runtime_error("create FFmpeg CUDA device failed: " + ffmpegError(result));
    codec_ = avcodec_alloc_context3(decoder);
    if (!codec_) throw std::runtime_error("allocate NVDEC context failed");
    if ((result = avcodec_parameters_to_context(codec_, parameters)) < 0) {
        throw std::runtime_error("copy codec parameters failed: " + ffmpegError(result));
    }
    codec_->get_format = &NvDecoder::selectCudaFormat;
    codec_->hw_device_ctx = av_buffer_ref(hardwareDevice_);
    codec_->extra_hw_frames = extraSurfaces_;
    codec_->thread_count = 1;
    codec_->flags |= AV_CODEC_FLAG_LOW_DELAY;
    if ((result = avcodec_open2(codec_, decoder, nullptr)) < 0) {
        throw std::runtime_error("open NVDEC failed: " + ffmpegError(result));
    }
    packet_ = av_packet_alloc();
    receiveFrame_ = av_frame_alloc();
    if (!packet_ || !receiveFrame_) throw std::runtime_error("allocate FFmpeg packet/frame failed");
}

DeviceFrame NvDecoder::receive() {
    const int result = avcodec_receive_frame(codec_, receiveFrame_);
    if (result < 0) {
        if (result == AVERROR(EAGAIN)) return {};
        if (result == AVERROR_EOF) throw std::runtime_error("NVDEC stream ended");
        throw std::runtime_error("NVDEC receive failed: " + ffmpegError(result));
    }
    if (receiveFrame_->format != AV_PIX_FMT_CUDA || !receiveFrame_->hw_frames_ctx) {
        av_frame_unref(receiveFrame_);
        throw std::runtime_error("decoder returned a host frame; CUDA zero-copy contract was violated");
    }
    auto* frames = reinterpret_cast<AVHWFramesContext*>(receiveFrame_->hw_frames_ctx->data);
    if (!frames || frames->sw_format != AV_PIX_FMT_NV12) {
        const std::string format = frames ? av_get_pix_fmt_name(frames->sw_format) : "unknown";
        av_frame_unref(receiveFrame_);
        throw std::runtime_error("NVDEC output must be NV12, got " + format);
    }
    AVFrame* owned = av_frame_alloc();
    if (!owned || av_frame_ref(owned, receiveFrame_) < 0) {
        av_frame_free(&owned);
        av_frame_unref(receiveFrame_);
        throw std::runtime_error("reference NVDEC surface failed");
    }
    DeviceFrame output{++sequence_, std::shared_ptr<AVFrame>(owned, frameDeleter),
                       receiveFrame_->width, receiveFrame_->height};
    av_frame_unref(receiveFrame_);
    return output;
}

DeviceFrame NvDecoder::next() {
    for (;;) {
        if (DeviceFrame output = receive(); output.frame) return output;
        if (inputEnded_) {
            const int sent = avcodec_send_packet(codec_, nullptr);
            if (sent < 0 && sent != AVERROR_EOF) {
                throw std::runtime_error("flush NVDEC failed: " + ffmpegError(sent));
            }
            continue;
        }
        int result = av_read_frame(format_, packet_);
        if (result == AVERROR_EOF) {
            inputEnded_ = true;
            continue;
        }
        if (result < 0) throw std::runtime_error("read RTSP packet failed: " + ffmpegError(result));
        if (packet_->stream_index != videoStream_) {
            av_packet_unref(packet_);
            continue;
        }
        result = avcodec_send_packet(codec_, packet_);
        av_packet_unref(packet_);
        if (result < 0 && result != AVERROR(EAGAIN)) {
            throw std::runtime_error("send packet to NVDEC failed: " + ffmpegError(result));
        }
    }
}

std::string NvDecoder::codecName() const {
    return codec_ && codec_->codec ? codec_->codec->name : "nvdec";
}

}  // namespace easyaiot::nvidia
