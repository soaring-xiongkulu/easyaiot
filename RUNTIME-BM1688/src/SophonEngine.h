#pragma once

#include "Config.h"

#include <bmcv_api_ext.h>
#include <bmlib_runtime.h>
#include <bmruntime_interface.h>
#include <opencv2/core.hpp>

#include <cstdint>
#include <string>
#include <vector>

namespace easyaiot::bm1688 {

struct Detection {
    float x1{0};
    float y1{0};
    float x2{0};
    float y2{0};
    float score{0};
    int classId{-1};
    int modelId{-1};
    std::string className;
};

class SophonEngine {
public:
    SophonEngine(int deviceId, int coreId, ModelConfig model, float confidence, float nms);
    ~SophonEngine();

    SophonEngine(const SophonEngine&) = delete;
    SophonEngine& operator=(const SophonEngine&) = delete;

    void initialize();
    std::vector<std::vector<Detection>> infer(const std::vector<cv::Mat>& frames);

    int batchSize() const noexcept { return batch_; }
    int coreId() const noexcept { return coreId_; }
    const std::string& networkName() const noexcept { return networkName_; }

private:
    void release() noexcept;
    void allocateImages();
    void allocateOutputs();
    std::vector<float> readOutput(int outputIndex);
    std::vector<Detection> decodeOutput(const std::vector<float>& output,
                                        const bm_shape_t& shape,
                                        int batchIndex,
                                        int sourceWidth,
                                        int sourceHeight) const;
    static void nms(std::vector<Detection>& detections, float threshold);
    static std::vector<std::string> loadClasses(const std::string& path);

    int deviceId_;
    int coreId_;
    ModelConfig model_;
    float confidence_;
    float nmsThreshold_;
    std::vector<std::string> classes_;

    bm_handle_t handle_{nullptr};
    void* runtime_{nullptr};
    const bm_net_info_t* network_{nullptr};
    std::string networkName_;
    int stageIndex_{0};
    int batch_{1};
    int inputWidth_{0};
    int inputHeight_{0};
    bool nchw_{true};
    std::vector<bm_image> resized_;
    std::vector<bm_image> converted_;
    bool resizedAllocated_{false};
    bool convertedAllocated_{false};
    std::vector<bm_tensor_t> outputTensors_;
    std::vector<bm_device_mem_t> outputMemory_;
};

}  // namespace easyaiot::bm1688
