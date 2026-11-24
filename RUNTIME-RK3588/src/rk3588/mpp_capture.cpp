#include "rk3588/mpp_capture.h"

#include <glog/logging.h>

namespace runtime::rk3588 {

MppCapture::~MppCapture() { close(); }

bool MppCapture::open(const std::string& url, int bufferCount) {
    close();
    format_ = avformat_alloc_context();
    AVDictionary* options = nullptr;
    if (url.rfind("rtsp://", 0) == 0 || url.rfind("rtsps://", 0) == 0) {
        av_dict_set(&options, "rtsp_transport", "tcp", 0);
        av_dict_set(&options, "stimeout", "3000000", 0);
        av_dict_set(&options, "timeout", "5000000", 0);
    }
    const int ret = avformat_open_input(&format_, url.c_str(), nullptr, &options);
    av_dict_free(&options);
    if (ret < 0 || avformat_find_stream_info(format_, nullptr) < 0) {
        close();
        return false;
    }
    videoIndex_ = av_find_best_stream(format_, AVMEDIA_TYPE_VIDEO, -1, -1, nullptr, 0);
    if (videoIndex_ < 0 || !decoder_.open(format_->streams[videoIndex_]->codecpar, bufferCount)) {
        close();
        return false;
    }
    return true;
}

bool MppCapture::convert(const FrameView& source, cv::Mat& bgr) {
    bgr.create(source.height, source.width, CV_8UC3);
    auto item = imports_.find(source.dmaFd);
    if (item == imports_.end()) {
        const int size = source.widthStride * source.heightStride * 3 / 2;
        const auto handle = importbuffer_fd(source.dmaFd, size);
        if (!handle) return false;
        item = imports_.emplace(source.dmaFd, handle).first;
    }
    const rga_buffer_t src = wrapbuffer_handle_t(
        item->second, source.width, source.height,
        source.widthStride, source.heightStride, RK_FORMAT_YCbCr_420_SP);
    const rga_buffer_t dst = wrapbuffer_virtualaddr_t(
        bgr.data, bgr.cols, bgr.rows,
        static_cast<int>(bgr.step[0] / bgr.elemSize()), bgr.rows, RK_FORMAT_BGR_888);
    im_rect srcRect{0, 0, source.width, source.height};
    im_rect dstRect{0, 0, bgr.cols, bgr.rows};
    im_rect patRect{};
    rga_buffer_t pat{};
    im_opt_t options{};
    const IM_STATUS status = improcess(src, dst, pat, srcRect, dstRect, patRect,
                                       -1, nullptr, &options, IM_SYNC);
    if (status != IM_STATUS_SUCCESS) {
        LOG(ERROR) << "[RGA] 抓拍帧转换失败: " << imStrError(status);
        return false;
    }
    return true;
}

bool MppCapture::read(cv::Mat& bgr, FrameView& source) {
    if (!isOpen()) return false;
    AVPacket* packet = av_packet_alloc();
    if (!packet) return false;
    bool ok = false;
    for (int attempts = 0; attempts < 300 && !ok; ++attempts) {
        const int ret = av_read_frame(format_, packet);
        if (ret < 0) break;
        if (packet->stream_index == videoIndex_) {
            if (!decoder_.submit(packet)) {
                av_packet_unref(packet);
                break;
            }
            FrameView decoded;
            while (decoder_.receive(decoded)) {
                if (convert(decoded, bgr)) {
                    source = std::move(decoded);
                    ok = true;
                    break;
                }
            }
        }
        av_packet_unref(packet);
    }
    av_packet_free(&packet);
    return ok;
}

void MppCapture::close() {
    for (auto& item : imports_) {
        if (item.second) releasebuffer_handle(item.second);
    }
    imports_.clear();
    decoder_.close();
    if (format_) avformat_close_input(&format_);
    videoIndex_ = -1;
}

}  // namespace runtime::rk3588
