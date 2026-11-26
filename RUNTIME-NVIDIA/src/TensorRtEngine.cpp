#include "TensorRtEngine.h"

#include <NvInferVersion.h>

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <utility>

#if NV_TENSORRT_MAJOR < 10
#error "RUNTIME-NVIDIA requires TensorRT 10 or newer"
#endif

namespace easyaiot::nvidia {
namespace {

class Logger final : public nvinfer1::ILogger {
public:
    void log(Severity severity, const char* message) noexcept override {
        if (severity <= Severity::kWARNING) std::cerr << "[TensorRT] " << message << '\n';
    }
};

Logger gLogger;

void checkCuda(cudaError_t code, const char* operation) {
    if (code != cudaSuccess) {
        throw std::runtime_error(std::string(operation) + ": " + cudaGetErrorString(code));
    }
}

std::size_t typeBytes(nvinfer1::DataType type) {
    switch (type) {
        case nvinfer1::DataType::kFLOAT: return 4;
        case nvinfer1::DataType::kHALF: return 2;
        case nvinfer1::DataType::kINT8: return 1;
        case nvinfer1::DataType::kINT32: return 4;
        case nvinfer1::DataType::kBOOL: return 1;
        case nvinfer1::DataType::kUINT8: return 1;
        case nvinfer1::DataType::kFP8: return 1;
        case nvinfer1::DataType::kBF16: return 2;
        case nvinfer1::DataType::kINT64: return 8;
    }
    throw std::runtime_error("unsupported TensorRT data type");
}

std::size_t elementCount(const nvinfer1::Dims& dims) {
    std::size_t count = 1;
    if (dims.nbDims <= 0) throw std::runtime_error("TensorRT tensor has no dimensions");
    for (int index = 0; index < dims.nbDims; ++index) {
        if (dims.d[index] <= 0) {
            throw std::runtime_error("dynamic TensorRT shapes are forbidden; build a static edge engine");
        }
        count *= static_cast<std::size_t>(dims.d[index]);
    }
    return count;
}

std::vector<char> readFile(const std::string& path) {
    std::ifstream input(path, std::ios::binary | std::ios::ate);
    if (!input) throw std::runtime_error("cannot open TensorRT engine: " + path);
    const auto size = input.tellg();
    if (size <= 0) throw std::runtime_error("TensorRT engine is empty: " + path);
    std::vector<char> bytes(static_cast<std::size_t>(size));
    input.seekg(0);
    input.read(bytes.data(), size);
    if (!input) throw std::runtime_error("cannot read TensorRT engine: " + path);
    return bytes;
}

std::vector<std::string> readLines(const std::string& path) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("cannot open classes file: " + path);
    std::vector<std::string> lines;
    for (std::string line; std::getline(input, line);) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (!line.empty()) lines.push_back(line);
    }
    return lines;
}

float halfToFloat(std::uint16_t half) {
    const std::uint32_t sign = static_cast<std::uint32_t>(half & 0x8000U) << 16U;
    std::uint32_t exponent = (half >> 10U) & 0x1fU;
    std::uint32_t mantissa = half & 0x03ffU;
    std::uint32_t bits = 0;
    if (exponent == 0) {
        if (mantissa == 0) {
            bits = sign;
        } else {
            exponent = 1;
            while ((mantissa & 0x0400U) == 0) { mantissa <<= 1U; --exponent; }
            mantissa &= 0x03ffU;
            bits = sign | ((exponent + 112U) << 23U) | (mantissa << 13U);
        }
    } else if (exponent == 31) {
        bits = sign | 0x7f800000U | (mantissa << 13U);
    } else {
        bits = sign | ((exponent + 112U) << 23U) | (mantissa << 13U);
    }
    float value = 0;
    std::memcpy(&value, &bits, sizeof(value));
    return value;
}

float valueAt(const void* data, nvinfer1::DataType type, std::size_t index) {
    if (type == nvinfer1::DataType::kFLOAT) return static_cast<const float*>(data)[index];
    if (type == nvinfer1::DataType::kHALF) {
        return halfToFloat(static_cast<const std::uint16_t*>(data)[index]);
    }
    throw std::runtime_error("YOLO output must be FP32 or FP16");
}

float intersectionOverUnion(const Detection& left, const Detection& right) {
    const float x1 = std::max(left.x1, right.x1);
    const float y1 = std::max(left.y1, right.y1);
    const float x2 = std::min(left.x2, right.x2);
    const float y2 = std::min(left.y2, right.y2);
    const float intersection = std::max(0.0F, x2 - x1) * std::max(0.0F, y2 - y1);
    const float leftArea = std::max(0.0F, left.x2 - left.x1) * std::max(0.0F, left.y2 - left.y1);
    const float rightArea = std::max(0.0F, right.x2 - right.x1) * std::max(0.0F, right.y2 - right.y1);
    return intersection / std::max(1e-6F, leftArea + rightArea - intersection);
}
}  // namespace

TensorRtModel::TensorRtModel(int cudaDevice, ModelConfig config,
                             float confidence, float nmsThreshold)
    : cudaDevice_(cudaDevice), config_(std::move(config)), confidence_(confidence),
      nmsThreshold_(nmsThreshold), classes_(readLines(config_.classesPath)) {
    checkCuda(cudaSetDevice(cudaDevice_), "select CUDA device");
    const auto serialized = readFile(config_.path);
    engineBytes_ = serialized.size();
    runtime_ = nvinfer1::createInferRuntime(gLogger);
    if (!runtime_) throw std::runtime_error("create TensorRT runtime failed");
    engine_ = runtime_->deserializeCudaEngine(serialized.data(), serialized.size());
    if (!engine_) {
        throw std::runtime_error(
            "deserialize TensorRT engine failed; engines are device/TensorRT-version specific");
    }

    for (int index = 0; index < engine_->getNbIOTensors(); ++index) {
        const char* name = engine_->getIOTensorName(index);
        TensorInfo info;
        info.name = name;
        info.dims = engine_->getTensorShape(name);
        info.type = engine_->getTensorDataType(name);
        info.elements = elementCount(info.dims);
        info.bytes = info.elements * typeBytes(info.type);
        if (engine_->getTensorIOMode(name) == nvinfer1::TensorIOMode::kINPUT) {
            if (!input_.name.empty()) throw std::runtime_error("only one TensorRT input tensor is supported");
            input_ = info;
        } else {
            outputs_.push_back(std::move(info));
        }
    }
    if (input_.name.empty() || outputs_.empty()) {
        throw std::runtime_error("TensorRT engine must expose one input and at least one output");
    }
    if (input_.dims.nbDims != 4 || input_.dims.d[0] != 1 || input_.dims.d[1] != 3) {
        throw std::runtime_error("TensorRT input must be static NCHW [1,3,H,W]");
    }
    if (input_.type != nvinfer1::DataType::kFLOAT && input_.type != nvinfer1::DataType::kHALF) {
        throw std::runtime_error("TensorRT input tensor must be FP32 or FP16");
    }
    inputHeight_ = input_.dims.d[2];
    inputWidth_ = input_.dims.d[3];
    for (const auto& output : outputs_) {
        if (output.type != nvinfer1::DataType::kFLOAT && output.type != nvinfer1::DataType::kHALF) {
            throw std::runtime_error("TensorRT YOLO outputs must be FP32 or FP16");
        }
    }
}

TensorRtModel::~TensorRtModel() {
    delete engine_;
    delete runtime_;
}

std::unique_ptr<TensorRtSession> TensorRtModel::createSession(bool cudaGraph) {
    return std::make_unique<TensorRtSession>(*this, cudaGraph);
}

TensorRtSession::TensorRtSession(TensorRtModel& model, bool cudaGraph)
    : model_(model), cudaGraphEnabled_(cudaGraph) {
    checkCuda(cudaSetDevice(model_.cudaDevice_), "select CUDA device");
    checkCuda(cudaStreamCreateWithFlags(&stream_, cudaStreamNonBlocking), "create CUDA inference stream");
    context_ = model_.engine_->createExecutionContext();
    if (!context_) throw std::runtime_error("create TensorRT execution context failed");
    checkCuda(cudaMalloc(&inputDevice_, model_.input_.bytes), "allocate TensorRT input");
    allocatedBytes_ += model_.input_.bytes;
    if (!context_->setTensorAddress(model_.input_.name.c_str(), inputDevice_)) {
        throw std::runtime_error("bind TensorRT input failed");
    }
    for (const auto& info : model_.outputs_) {
        OutputBuffer output;
        output.info = info;
        checkCuda(cudaMalloc(&output.device, info.bytes), "allocate TensorRT output");
        checkCuda(cudaHostAlloc(&output.host, info.bytes, cudaHostAllocPortable),
                  "allocate pinned TensorRT output");
        allocatedBytes_ += info.bytes * 2;
        if (!context_->setTensorAddress(info.name.c_str(), output.device)) {
            throw std::runtime_error("bind TensorRT output failed: " + info.name);
        }
        outputs_.push_back(std::move(output));
    }
    checkCuda(cudaMemsetAsync(inputDevice_, 0, model_.input_.bytes, stream_), "clear TensorRT input");
    if (!context_->enqueueV3(stream_)) throw std::runtime_error("TensorRT warmup enqueue failed");
    checkCuda(cudaStreamSynchronize(stream_), "TensorRT warmup synchronize");
    if (cudaGraphEnabled_) initializeGraph();
}

TensorRtSession::~TensorRtSession() {
    if (stream_) cudaStreamSynchronize(stream_);
    if (graphExec_) cudaGraphExecDestroy(graphExec_);
    if (graph_) cudaGraphDestroy(graph_);
    for (auto& output : outputs_) {
        if (output.device) cudaFree(output.device);
        if (output.host) cudaFreeHost(output.host);
    }
    if (inputDevice_) cudaFree(inputDevice_);
    delete context_;
    if (stream_) cudaStreamDestroy(stream_);
}

void TensorRtSession::initializeGraph() {
    checkCuda(cudaStreamBeginCapture(stream_, cudaStreamCaptureModeThreadLocal),
              "begin TensorRT CUDA Graph capture");
    if (!context_->enqueueV3(stream_)) {
        cudaStreamEndCapture(stream_, &graph_);
        throw std::runtime_error("TensorRT CUDA Graph enqueue failed");
    }
    for (auto& output : outputs_) {
        checkCuda(cudaMemcpyAsync(output.host, output.device, output.info.bytes,
                                  cudaMemcpyDeviceToHost, stream_),
                  "capture TensorRT output copy");
    }
    checkCuda(cudaStreamEndCapture(stream_, &graph_), "end TensorRT CUDA Graph capture");
    checkCuda(cudaGraphInstantiate(&graphExec_, graph_, nullptr, nullptr, 0),
              "instantiate TensorRT CUDA Graph");
}

std::vector<Detection> TensorRtSession::infer(const DeviceFrame& frame) {
    if (!frame.frame || frame.frame->format != AV_PIX_FMT_CUDA) {
        throw std::runtime_error("TensorRT received a non-CUDA frame");
    }
    const Letterbox transform = launchNv12Letterbox(
        frame.frame->data[0], frame.frame->linesize[0],
        frame.frame->data[1], frame.frame->linesize[1],
        frame.width, frame.height, inputDevice_, model_.input_.type,
        model_.inputWidth_, model_.inputHeight_, stream_);
    if (cudaGraphEnabled_) {
        checkCuda(cudaGraphLaunch(graphExec_, stream_), "launch TensorRT CUDA Graph");
    } else {
        if (!context_->enqueueV3(stream_)) throw std::runtime_error("TensorRT enqueueV3 failed");
        for (auto& output : outputs_) {
            checkCuda(cudaMemcpyAsync(output.host, output.device, output.info.bytes,
                                      cudaMemcpyDeviceToHost, stream_),
                      "copy TensorRT output to pinned memory");
        }
    }
    checkCuda(cudaStreamSynchronize(stream_), "synchronize TensorRT stream");
    return decode(frame, transform);
}

std::vector<Detection> TensorRtSession::decode(const DeviceFrame& frame,
                                                const Letterbox& transform) const {
    // The first output must be either [1,boxes,attrs], [1,attrs,boxes], or [1,boxes,6].
    const auto& output = outputs_.front();
    const auto& dims = output.info.dims;
    if (dims.nbDims != 3 || dims.d[0] != 1) {
        throw std::runtime_error("unsupported TensorRT YOLO output shape");
    }
    const bool fused = dims.d[2] == 6;
    const bool attributesLast = fused || dims.d[2] >= 6;
    const int boxes = attributesLast ? dims.d[1] : dims.d[2];
    const int attributes = attributesLast ? dims.d[2] : dims.d[1];
    if ((!fused && attributes < 5) || boxes <= 0) {
        throw std::runtime_error("invalid TensorRT YOLO output dimensions");
    }

    auto at = [&](int box, int attribute) {
        const std::size_t index = attributesLast
            ? static_cast<std::size_t>(box) * attributes + attribute
            : static_cast<std::size_t>(attribute) * boxes + box;
        return valueAt(output.host, output.info.type, index);
    };
    std::vector<Detection> candidates;
    candidates.reserve(std::min(boxes, 4096));
    for (int box = 0; box < boxes; ++box) {
        Detection detection;
        if (fused) {
            detection.x1 = at(box, 0);
            detection.y1 = at(box, 1);
            detection.x2 = at(box, 2);
            detection.y2 = at(box, 3);
            detection.score = at(box, 4);
            detection.classId = static_cast<int>(at(box, 5));
        } else {
            int classId = 0;
            float score = -std::numeric_limits<float>::infinity();
            for (int attribute = 4; attribute < attributes; ++attribute) {
                const float current = at(box, attribute);
                if (current > score) { score = current; classId = attribute - 4; }
            }
            if (score < model_.confidence_) continue;
            const float centerX = at(box, 0);
            const float centerY = at(box, 1);
            const float width = at(box, 2);
            const float height = at(box, 3);
            detection.x1 = centerX - width * 0.5F;
            detection.y1 = centerY - height * 0.5F;
            detection.x2 = centerX + width * 0.5F;
            detection.y2 = centerY + height * 0.5F;
            detection.score = score;
            detection.classId = classId;
        }
        if (detection.score < model_.confidence_) continue;
        detection.x1 = std::clamp((detection.x1 - transform.padX) / transform.scale,
                                  0.0F, static_cast<float>(frame.width));
        detection.y1 = std::clamp((detection.y1 - transform.padY) / transform.scale,
                                  0.0F, static_cast<float>(frame.height));
        detection.x2 = std::clamp((detection.x2 - transform.padX) / transform.scale,
                                  0.0F, static_cast<float>(frame.width));
        detection.y2 = std::clamp((detection.y2 - transform.padY) / transform.scale,
                                  0.0F, static_cast<float>(frame.height));
        if (detection.x2 <= detection.x1 || detection.y2 <= detection.y1) continue;
        detection.modelId = model_.config_.id;
        detection.className = detection.classId >= 0 &&
            static_cast<std::size_t>(detection.classId) < model_.classes_.size()
            ? model_.classes_[static_cast<std::size_t>(detection.classId)]
            : "class_" + std::to_string(detection.classId);
        candidates.push_back(std::move(detection));
    }

    std::sort(candidates.begin(), candidates.end(), [](const Detection& left, const Detection& right) {
        return left.score > right.score;
    });
    std::vector<Detection> kept;
    kept.reserve(std::min<std::size_t>(candidates.size(), 300));
    for (auto& candidate : candidates) {
        bool suppressed = false;
        for (const auto& accepted : kept) {
            if (candidate.classId == accepted.classId &&
                intersectionOverUnion(candidate, accepted) > model_.nmsThreshold_) {
                suppressed = true;
                break;
            }
        }
        if (!suppressed) kept.push_back(std::move(candidate));
        if (kept.size() == 300) break;
    }
    return kept;
}

}  // namespace easyaiot::nvidia
