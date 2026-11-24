#ifndef EASYAIOT_RK3588_MPP_CAPTURE_H
#define EASYAIOT_RK3588_MPP_CAPTURE_H

#include "rk3588/frame_view.h"
#include "rk3588/mpp_decoder.h"

#include <opencv2/core.hpp>
#include <string>
#include <unordered_map>

#include <im2d.hpp>

extern "C" {
#include <libavformat/avformat.h>
}

namespace runtime::rk3588 {

/** Long-lived demux + MPP capture used by snap/patrol modes. */
class MppCapture {
public:
    MppCapture() = default;
    ~MppCapture();
    MppCapture(const MppCapture&) = delete;
    MppCapture& operator=(const MppCapture&) = delete;

    bool open(const std::string& url, int bufferCount);
    bool read(cv::Mat& bgr, FrameView& source);
    void close();
    bool isOpen() const { return format_ != nullptr && decoder_.isOpen(); }

private:
    bool convert(const FrameView& source, cv::Mat& bgr);

    AVFormatContext* format_{nullptr};
    int videoIndex_{-1};
    MppDecoder decoder_;
    std::unordered_map<int, rga_buffer_handle_t> imports_;
};

}  // namespace runtime::rk3588

#endif
