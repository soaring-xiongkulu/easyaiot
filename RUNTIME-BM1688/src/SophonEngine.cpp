#include "SophonEngine.h"

#include <opencv2/imgproc.hpp>

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits>
#include <numeric>
#include <stdexcept>

namespace easyaiot::bm1688 {
namespace {

void requireBm(bm_status_t status, const std::string& action) {
    if (status != BM_SUCCESS) {
        throw std::runtime_error(action + " failed, bm_status=" + std::to_string(status));
    }
}

std::size_t shapeCount(const bm_shape_t& shape) {
    return static_cast<std::size_t>(bmrt_shape_count(&shape));
}

float overlap(const Detection& a, const Detection& b) {
    const float left = std::max(a.x1, b.x1);
    const float top = std::max(a.y1, b.y1);
    const float right = std::min(a.x2, b.x2);
    const float bottom = std::min(a.y2, b.y2);
    const float intersection = std::max(0.0F, right - left) * std::max(0.0F, bottom - top);
    const float areaA = std::max(0.0F, a.x2 - a.x1) * std::max(0.0F, a.y2 - a.y1);
    const float areaB = std::max(0.0F, b.x2 - b.x1) * std::max(0.0F, b.y2 - b.y1);
    return intersection / std::max(1e-6F, areaA + areaB - intersection);
}

}  // namespace

SophonEngine::SophonEngine(int deviceId, int coreId, ModelConfig model,
                           float confidence, float nms)
    : deviceId_(deviceId), coreId_(coreId), model_(std::move(model)),
      confidence_(confidence), nmsThreshold_(nms), classes_(loadClasses(model_.classesPath)) {}

SophonEngine::~SophonEngine() { release(); }

void SophonEngine::release() noexcept {
    if (convertedAllocated_ && !converted_.empty()) {
        bm_image_free_contiguous_mem(static_cast<int>(converted_.size()), converted_.data());
    }
    if (resizedAllocated_ && !resized_.empty()) {
        bm_image_free_contiguous_mem(static_cast<int>(resized_.size()), resized_.data());
    }
    for (auto image : converted_) bm_image_destroy(image);
    for (auto image : resized_) bm_image_destroy(image);
    converted_.clear();
    resized_.clear();
    if (handle_) {
        for (auto memory : outputMemory_) bm_free_device(handle_, memory);
    }
    outputMemory_.clear();
    outputTensors_.clear();
    if (runtime_) bmrt_destroy(runtime_);
    runtime_ = nullptr;
    if (handle_) bm_dev_free(handle_);
    handle_ = nullptr;
}

std::vector<std::string> SophonEngine::loadClasses(const std::string& path) {
    std::vector<std::string> classes;
    std::ifstream input(path);
    std::string line;
    while (std::getline(input, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (!line.empty()) classes.push_back(line);
    }
    return classes;
}

void SophonEngine::initialize() {
    if (handle_) return;
    requireBm(bm_dev_request(&handle_, deviceId_), "bm_dev_request");
    runtime_ = bmrt_create(handle_);
    if (!runtime_) throw std::runtime_error("bmrt_create failed");
    if (!bmrt_load_bmodel(runtime_, model_.path.c_str())) {
        throw std::runtime_error("bmrt_load_bmodel failed: " + model_.path);
    }
    const int networks = bmrt_get_network_number(runtime_);
    if (networks != 1) {
        throw std::runtime_error("BModel must contain exactly one YOLO network");
    }
    const char* name = bmrt_get_network_name(runtime_, 0);
    if (!name) throw std::runtime_error("bmrt_get_network_name failed");
    networkName_ = name;
    network_ = bmrt_get_network_info(runtime_, networkName_.c_str());
    if (!network_ || network_->input_num != 1 || network_->stage_num < 1) {
        throw std::runtime_error("BModel requires one input and at least one static stage");
    }
    if (network_->core_num < 2) {
        throw std::runtime_error("BModel is not compiled for BM1688 two-core runtime");
    }

    // Prefer the largest static batch stage; workers fill a partial batch by
    // repeating the newest device frame, keeping all device allocations stable.
    int bestBatch = 0;
    for (int stage = 0; stage < network_->stage_num; ++stage) {
        const bm_shape_t& shape = network_->stages[stage].input_shapes[0];
        if (shape.num_dims != 4) continue;
        const int candidate = shape.dims[0];
        if (candidate > bestBatch) {
            stageIndex_ = stage;
            bestBatch = candidate;
        }
    }
    if (bestBatch <= 0) throw std::runtime_error("BModel has no supported 4-D input stage");
    const bm_shape_t& inputShape = network_->stages[stageIndex_].input_shapes[0];
    batch_ = inputShape.dims[0];
    nchw_ = inputShape.dims[1] == 3;
    inputHeight_ = nchw_ ? inputShape.dims[2] : inputShape.dims[1];
    inputWidth_ = nchw_ ? inputShape.dims[3] : inputShape.dims[2];
    if (batch_ < 1 || batch_ > 16 || inputWidth_ <= 0 || inputHeight_ <= 0) {
        throw std::runtime_error("unsupported BModel input shape");
    }

    allocateImages();
    allocateOutputs();
    const int core[] = {coreId_};
    if (!bmrt_pre_alloc_neuron_multi_cores(
            runtime_, networkName_.c_str(), stageIndex_, core, 1)) {
        throw std::runtime_error("bmrt_pre_alloc_neuron_multi_cores failed on core " +
                                 std::to_string(coreId_));
    }
    std::cerr << "[BM1688] core=" << coreId_ << " network=" << networkName_
              << " batch=" << batch_ << " input=" << inputWidth_ << "x" << inputHeight_
              << " outputs=" << network_->output_num << '\n';
}

void SophonEngine::allocateImages() {
    resized_.resize(batch_);
    converted_.resize(batch_);
    const int alignedWidth = (inputWidth_ + 63) & ~63;
    int strides[] = {alignedWidth, alignedWidth, alignedWidth};
    for (int index = 0; index < batch_; ++index) {
        requireBm(
            bm_image_create(handle_, inputHeight_, inputWidth_, FORMAT_RGB_PLANAR,
                            DATA_TYPE_EXT_1N_BYTE, &resized_[index], strides),
            "bm_image_create resized");
    }
    requireBm(bm_image_alloc_contiguous_mem(batch_, resized_.data()),
              "bm_image_alloc_contiguous_mem resized");
    resizedAllocated_ = true;

    const auto dtype = network_->input_dtypes[0];
    bm_image_data_format_ext imageType = DATA_TYPE_EXT_FLOAT32;
    if (dtype == BM_INT8) imageType = DATA_TYPE_EXT_1N_BYTE_SIGNED;
    else if (dtype == BM_UINT8) imageType = DATA_TYPE_EXT_1N_BYTE;
    else if (dtype != BM_FLOAT32) {
        throw std::runtime_error("only FP32/INT8/UINT8 BModel input is supported");
    }
    for (int index = 0; index < batch_; ++index) {
        requireBm(
            bm_image_create(handle_, inputHeight_, inputWidth_, FORMAT_RGB_PLANAR,
                            imageType, &converted_[index]),
            "bm_image_create converted");
    }
    requireBm(bm_image_alloc_contiguous_mem(batch_, converted_.data()),
              "bm_image_alloc_contiguous_mem converted");
    convertedAllocated_ = true;
}

void SophonEngine::allocateOutputs() {
    outputTensors_.resize(network_->output_num);
    outputMemory_.resize(network_->output_num);
    const auto& stage = network_->stages[stageIndex_];
    for (int index = 0; index < network_->output_num; ++index) {
        const std::size_t bytes = network_->max_output_bytes[index];
        requireBm(bm_malloc_device_byte(handle_, &outputMemory_[index], bytes),
                  "bm_malloc_device_byte output");
        bmrt_tensor_with_device(&outputTensors_[index], outputMemory_[index],
                                network_->output_dtypes[index], stage.output_shapes[index]);
    }
}

std::vector<std::vector<Detection>> SophonEngine::infer(const std::vector<cv::Mat>& frames) {
    if (!runtime_) initialize();
    if (frames.empty()) return {};
    if (frames.size() > static_cast<std::size_t>(batch_)) {
        throw std::runtime_error("infer batch exceeds BModel batch");
    }

    std::vector<bm_image> borrowed;
    borrowed.reserve(batch_);
    for (int index = 0; index < batch_; ++index) {
        cv::Mat& frame = const_cast<cv::Mat&>(frames[std::min<std::size_t>(index, frames.size() - 1)]);
        bm_image source{};
        if (cv::bmcv::toBMI(frame, &source, true) != 0) {
            for (auto image : borrowed) bm_image_destroy(image);
            throw std::runtime_error("cv::bmcv::toBMI failed; Sophon device frame is required");
        }
        borrowed.push_back(source);

        const float ratio = std::min(
            static_cast<float>(inputWidth_) / source.width,
            static_cast<float>(inputHeight_) / source.height);
        bmcv_padding_atrr_t padding{};
        padding.dst_crop_w = static_cast<int>(std::round(source.width * ratio));
        padding.dst_crop_h = static_cast<int>(std::round(source.height * ratio));
        padding.dst_crop_stx = (inputWidth_ - padding.dst_crop_w) / 2;
        padding.dst_crop_sty = (inputHeight_ - padding.dst_crop_h) / 2;
        padding.padding_r = 114;
        padding.padding_g = 114;
        padding.padding_b = 114;
        padding.if_memset = 1;
        bmcv_rect_t crop{0, 0, source.width, source.height};
        requireBm(
            bmcv_image_vpp_convert_padding(handle_, 1, source, &resized_[index],
                                           &padding, &crop, BMCV_INTER_NEAREST),
            "bmcv_image_vpp_convert_padding");
    }

    bmcv_convert_to_attr conversion{};
    const float alpha = network_->input_scales[0] / 255.0F;
    conversion.alpha_0 = alpha;
    conversion.alpha_1 = alpha;
    conversion.alpha_2 = alpha;
    // Match SOPHGO's BM1688 BMCV samples: model input_scale performs the
    // quantisation and beta remains zero for RGB planar input.
    conversion.beta_0 = 0.0F;
    conversion.beta_1 = 0.0F;
    conversion.beta_2 = 0.0F;
    requireBm(bmcv_image_convert_to(handle_, batch_, conversion,
                                    resized_.data(), converted_.data()),
              "bmcv_image_convert_to");
    for (auto image : borrowed) bm_image_destroy(image);

    bm_device_mem_t inputMemory{};
    requireBm(bm_image_get_contiguous_device_mem(batch_, converted_.data(), &inputMemory),
              "bm_image_get_contiguous_device_mem");
    bm_tensor_t input{};
    bmrt_tensor_with_device(&input, inputMemory, network_->input_dtypes[0],
                            network_->stages[stageIndex_].input_shapes[0]);
    const int core[] = {coreId_};
    if (!bmrt_launch_tensor_multi_cores(
            runtime_, networkName_.c_str(), &input, 1, outputTensors_.data(),
            network_->output_num, true, false, core, 1)) {
        throw std::runtime_error("bmrt_launch_tensor_multi_cores failed");
    }
    requireBm(bm_thread_sync_from_core(handle_, coreId_), "bm_thread_sync_from_core");

    std::vector<std::vector<Detection>> results(frames.size());
    for (int outputIndex = 0; outputIndex < network_->output_num; ++outputIndex) {
        const auto host = readOutput(outputIndex);
        const auto& shape = network_->stages[stageIndex_].output_shapes[outputIndex];
        for (std::size_t batchIndex = 0; batchIndex < frames.size(); ++batchIndex) {
            auto decoded = decodeOutput(host, shape, static_cast<int>(batchIndex),
                                        frames[batchIndex].cols, frames[batchIndex].rows);
            results[batchIndex].insert(results[batchIndex].end(), decoded.begin(), decoded.end());
        }
    }
    for (auto& detections : results) nms(detections, nmsThreshold_);
    return results;
}

std::vector<float> SophonEngine::readOutput(int outputIndex) {
    const auto& tensor = outputTensors_.at(outputIndex);
    const std::size_t count = shapeCount(tensor.shape);
    std::vector<float> output(count);
    if (tensor.dtype == BM_FLOAT32) {
        requireBm(bm_memcpy_d2s(handle_, output.data(), tensor.device_mem), "bm_memcpy_d2s FP32");
        return output;
    }
    if (tensor.dtype == BM_INT8) {
        std::vector<std::int8_t> raw(count);
        requireBm(bm_memcpy_d2s(handle_, raw.data(), tensor.device_mem), "bm_memcpy_d2s INT8");
        const float scale = network_->output_scales[outputIndex];
        const int zero = network_->output_zero_point[outputIndex];
        for (std::size_t i = 0; i < count; ++i) output[i] = (raw[i] - zero) * scale;
        return output;
    }
    if (tensor.dtype == BM_UINT8) {
        std::vector<std::uint8_t> raw(count);
        requireBm(bm_memcpy_d2s(handle_, raw.data(), tensor.device_mem), "bm_memcpy_d2s UINT8");
        const float scale = network_->output_scales[outputIndex];
        const int zero = network_->output_zero_point[outputIndex];
        for (std::size_t i = 0; i < count; ++i) output[i] = (raw[i] - zero) * scale;
        return output;
    }
    throw std::runtime_error("unsupported BModel output dtype; use FP32/INT8/UINT8 output");
}

std::vector<Detection> SophonEngine::decodeOutput(
    const std::vector<float>& output, const bm_shape_t& shape, int batchIndex,
    int sourceWidth, int sourceHeight) const {
    std::vector<Detection> detections;
    if (shape.num_dims != 3 || shape.dims[0] < 1) return detections;
    const int dim1 = shape.dims[1];
    const int dim2 = shape.dims[2];
    const bool channelsFirst = dim1 >= 6 && dim1 <= 512 && dim2 > dim1;
    const int candidates = channelsFirst ? dim2 : dim1;
    const int attributes = channelsFirst ? dim1 : dim2;
    if (attributes < 6 || candidates <= 0) return detections;
    const std::size_t perBatch = static_cast<std::size_t>(dim1) * dim2;
    const std::size_t offset = perBatch * batchIndex;
    if (offset + perBatch > output.size()) return detections;

    auto at = [&](int candidate, int attribute) -> float {
        const std::size_t index = channelsFirst
            ? offset + static_cast<std::size_t>(attribute) * candidates + candidate
            : offset + static_cast<std::size_t>(candidate) * attributes + attribute;
        return output[index];
    };
    const float ratio = std::min(static_cast<float>(inputWidth_) / sourceWidth,
                                 static_cast<float>(inputHeight_) / sourceHeight);
    const float padX = (inputWidth_ - sourceWidth * ratio) * 0.5F;
    const float padY = (inputHeight_ - sourceHeight * ratio) * 0.5F;

    for (int candidate = 0; candidate < candidates; ++candidate) {
        Detection detection;
        if (attributes == 6) {
            detection.score = at(candidate, 4);
            detection.classId = static_cast<int>(std::round(at(candidate, 5)));
            if (detection.score < confidence_) continue;
            detection.x1 = (at(candidate, 0) - padX) / ratio;
            detection.y1 = (at(candidate, 1) - padY) / ratio;
            detection.x2 = (at(candidate, 2) - padX) / ratio;
            detection.y2 = (at(candidate, 3) - padY) / ratio;
        } else {
            int bestClass = -1;
            float bestScore = 0.0F;
            for (int cls = 4; cls < attributes; ++cls) {
                const float score = at(candidate, cls);
                if (score > bestScore) { bestScore = score; bestClass = cls - 4; }
            }
            if (bestScore < confidence_) continue;
            const float cx = at(candidate, 0);
            const float cy = at(candidate, 1);
            const float width = at(candidate, 2);
            const float height = at(candidate, 3);
            detection.score = bestScore;
            detection.classId = bestClass;
            detection.x1 = (cx - width * 0.5F - padX) / ratio;
            detection.y1 = (cy - height * 0.5F - padY) / ratio;
            detection.x2 = (cx + width * 0.5F - padX) / ratio;
            detection.y2 = (cy + height * 0.5F - padY) / ratio;
        }
        detection.x1 = std::clamp(detection.x1, 0.0F, static_cast<float>(sourceWidth - 1));
        detection.y1 = std::clamp(detection.y1, 0.0F, static_cast<float>(sourceHeight - 1));
        detection.x2 = std::clamp(detection.x2, 0.0F, static_cast<float>(sourceWidth - 1));
        detection.y2 = std::clamp(detection.y2, 0.0F, static_cast<float>(sourceHeight - 1));
        detection.modelId = model_.id;
        detection.className = detection.classId >= 0 && detection.classId < static_cast<int>(classes_.size())
            ? classes_[detection.classId]
            : "class_" + std::to_string(detection.classId);
        detections.push_back(std::move(detection));
    }
    return detections;
}

void SophonEngine::nms(std::vector<Detection>& detections, float threshold) {
    std::sort(detections.begin(), detections.end(), [](const Detection& a, const Detection& b) {
        return a.score > b.score;
    });
    std::vector<Detection> kept;
    kept.reserve(detections.size());
    for (const auto& detection : detections) {
        const bool suppressed = std::any_of(kept.begin(), kept.end(), [&](const Detection& item) {
            return item.classId == detection.classId && overlap(item, detection) > threshold;
        });
        if (!suppressed) kept.push_back(detection);
    }
    detections.swap(kept);
}

}  // namespace easyaiot::bm1688
