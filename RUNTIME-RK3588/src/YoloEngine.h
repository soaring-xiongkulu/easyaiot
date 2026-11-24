#ifndef YOLO_ENGINE_H
#define YOLO_ENGINE_H

#include "Datatype.h"
#include "rk3588/frame_view.h"

#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

#include <im2d.hpp>
#include <rknn_api.h>

/** RK3588-only RKNN2 inference engine with persistent zero-copy tensor memory. */
class YoloEngine {
public:
    YoloEngine() = default;
    ~YoloEngine();

    YoloEngine(const YoloEngine&) = delete;
    YoloEngine& operator=(const YoloEngine&) = delete;

    int LoadModel(const std::string& modelPath,
                  const std::vector<std::string>& modelClasses,
                  int npuCoreIndex,
                  bool useSram = true,
                  bool enablePerfQuery = false);
    int Run(const runtime::rk3588::FrameView& frame, std::vector<DetectObject>& objects);
    int Run(cv::Mat& image, std::vector<DetectObject>& objects);

    const std::string& inferEp() const { return inferEp_; }
    const std::string& modelLayout() const { return modelLayout_; }
    const std::string& loadedModelPath() const { return loadedModelPath_; }
    int64_t lastNpuDurationUs() const { return lastNpuDurationUs_; }
    void setScoreThreshold(float threshold);

private:
    struct ImportedBuffer {
        rga_buffer_handle_t handle{0};
        int width{0};
        int height{0};
        int widthStride{0};
        int heightStride{0};
        int format{0};
    };

    int prepareRgaInput(const runtime::rk3588::FrameView& frame);
    int parseYolov8Output(const runtime::rk3588::FrameView& frame,
                          float scale, int padX, int padY,
                          std::vector<DetectObject>& objects);
    int8_t outputValue(size_t outputIndex, int channel, int y, int x) const;
    float dequantize(size_t outputIndex, int8_t value) const;
    void release();
    static int rgaFormat(runtime::rk3588::FrameFormat format);
    static bool hasRknnExtension(const std::string& path);

    rknn_context context_{0};
    rknn_tensor_attr inputAttr_{};
    rknn_tensor_attr inputNativeAttr_{};
    std::vector<rknn_tensor_attr> outputAttrs_;
    std::vector<rknn_tensor_attr> outputNativeAttrs_;
    rknn_tensor_mem* inputMem_{nullptr};
    std::vector<rknn_tensor_mem*> outputMems_;
    rga_buffer_handle_t inputRgaHandle_{0};
    std::unordered_map<uint64_t, ImportedBuffer> importedSources_;

    std::vector<std::string> classes_;
    int inputWidth_{0};
    int inputHeight_{0};
    int inputChannels_{0};
    int inputWidthStride_{0};
    float lastScale_{1.0f};
    int lastPadX_{0};
    int lastPadY_{0};
    int paddedWidth_{0};
    int paddedHeight_{0};
    bool paddingInitialized_{false};
    int64_t lastNpuDurationUs_{0};
    uint64_t runCounter_{0};
    bool ready_{false};
    bool perfQueryEnabled_{false};
    float scoreThreshold_{0.25f};
    float nmsThreshold_{0.45f};
    std::vector<cv::Rect2f> scratchBoxes_;
    std::vector<float> scratchScores_;
    std::vector<int> scratchClassIds_;
    std::vector<size_t> scratchOrder_;
    std::vector<size_t> scratchKeep_;
    std::vector<uint8_t> scratchSuppressed_;
    std::string inferEp_{"none"};
    std::string modelLayout_{"unknown"};
    std::string loadedModelPath_;
};

#endif
