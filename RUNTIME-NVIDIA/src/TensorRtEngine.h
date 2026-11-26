#pragma once

#include "Config.h"
#include "CudaPreprocess.h"
#include "NvDecoder.h"

#include <NvInfer.h>
#include <cuda_runtime_api.h>

#include <cstddef>
#include <memory>
#include <string>
#include <vector>

namespace easyaiot::nvidia {

struct Detection {
    float x1{0};
    float y1{0};
    float x2{0};
    float y2{0};
    float score{0};
    int classId{0};
    int modelId{0};
    std::string className;
};

class TensorRtSession;

class TensorRtModel {
public:
    TensorRtModel(int cudaDevice, ModelConfig config, float confidence, float nmsThreshold);
    ~TensorRtModel();

    TensorRtModel(const TensorRtModel&) = delete;
    TensorRtModel& operator=(const TensorRtModel&) = delete;

    std::unique_ptr<TensorRtSession> createSession(bool cudaGraph);
    int inputWidth() const noexcept { return inputWidth_; }
    int inputHeight() const noexcept { return inputHeight_; }
    std::size_t engineBytes() const noexcept { return engineBytes_; }

private:
    friend class TensorRtSession;
    struct TensorInfo {
        std::string name;
        nvinfer1::Dims dims{};
        nvinfer1::DataType type{nvinfer1::DataType::kFLOAT};
        std::size_t elements{0};
        std::size_t bytes{0};
    };

    int cudaDevice_{0};
    ModelConfig config_;
    float confidence_{0.5F};
    float nmsThreshold_{0.45F};
    std::vector<std::string> classes_;
    std::size_t engineBytes_{0};
    nvinfer1::IRuntime* runtime_{nullptr};
    nvinfer1::ICudaEngine* engine_{nullptr};
    TensorInfo input_;
    std::vector<TensorInfo> outputs_;
    int inputWidth_{0};
    int inputHeight_{0};
};

class TensorRtSession {
public:
    TensorRtSession(TensorRtModel& model, bool cudaGraph);
    ~TensorRtSession();

    TensorRtSession(const TensorRtSession&) = delete;
    TensorRtSession& operator=(const TensorRtSession&) = delete;

    std::vector<Detection> infer(const DeviceFrame& frame);
    std::size_t allocatedBytes() const noexcept { return allocatedBytes_; }

private:
    struct OutputBuffer {
        TensorRtModel::TensorInfo info;
        void* device{nullptr};
        void* host{nullptr};
    };

    void initializeGraph();
    std::vector<Detection> decode(const DeviceFrame& frame, const Letterbox& letterbox) const;

    TensorRtModel& model_;
    nvinfer1::IExecutionContext* context_{nullptr};
    cudaStream_t stream_{nullptr};
    void* inputDevice_{nullptr};
    std::vector<OutputBuffer> outputs_;
    bool cudaGraphEnabled_{false};
    cudaGraph_t graph_{nullptr};
    cudaGraphExec_t graphExec_{nullptr};
    std::size_t allocatedBytes_{0};
};

}  // namespace easyaiot::nvidia
