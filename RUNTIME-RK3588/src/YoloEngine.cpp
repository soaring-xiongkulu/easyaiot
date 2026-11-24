#include "YoloEngine.h"

#include <algorithm>
#include <cmath>
#include <cctype>
#include <cstring>
#include <fstream>
#include <glog/logging.h>
#include <limits>
#include <numeric>

namespace {

bool fileExists(const std::string& path) {
    std::ifstream input(path, std::ios::binary);
    return input.good();
}

float intersectionOverUnion(const cv::Rect2f& a, const cv::Rect2f& b) {
    const float left = std::max(a.x, b.x);
    const float top = std::max(a.y, b.y);
    const float right = std::min(a.x + a.width, b.x + b.width);
    const float bottom = std::min(a.y + a.height, b.y + b.height);
    const float intersection =
        std::max(0.0f, right - left) * std::max(0.0f, bottom - top);
    const float total = a.area() + b.area() - intersection;
    return total > 0.0f ? intersection / total : 0.0f;
}

}  // namespace

YoloEngine::~YoloEngine() { release(); }

bool YoloEngine::hasRknnExtension(const std::string& path) {
    if (path.size() < 5) return false;
    std::string suffix = path.substr(path.size() - 5);
    std::transform(suffix.begin(), suffix.end(), suffix.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });
    return suffix == ".rknn";
}

void YoloEngine::release() {
    ready_ = false;
    paddingInitialized_ = false;
    paddedWidth_ = 0;
    paddedHeight_ = 0;
    for (auto& item : importedSources_) {
        if (item.second.handle) releasebuffer_handle(item.second.handle);
    }
    importedSources_.clear();
    if (inputRgaHandle_) {
        releasebuffer_handle(inputRgaHandle_);
        inputRgaHandle_ = 0;
    }
    if (context_) {
        for (rknn_tensor_mem* memory : outputMems_) {
            if (memory) rknn_destroy_mem(context_, memory);
        }
        outputMems_.clear();
        if (inputMem_) {
            rknn_destroy_mem(context_, inputMem_);
            inputMem_ = nullptr;
        }
        rknn_destroy(context_);
        context_ = 0;
    }
    outputAttrs_.clear();
    outputNativeAttrs_.clear();
}

void YoloEngine::setScoreThreshold(float threshold) {
    if (threshold > 0.0f && threshold <= 1.0f) scoreThreshold_ = threshold;
}

int YoloEngine::LoadModel(const std::string& modelPath,
                          const std::vector<std::string>& modelClasses,
                          int npuCoreIndex,
                          bool useSram,
                          bool enablePerfQuery) {
    release();
    if (!hasRknnExtension(modelPath) || !fileExists(modelPath)) {
        LOG(ERROR) << "[RKNN] 仅接受存在的 RK3588 .rknn 模型: " << modelPath;
        return -1;
    }

    uint32_t flags = RKNN_FLAG_SHARE_WEIGHT_MEM;
#ifdef RKNN_FLAG_DISABLE_FLUSH_INPUT_MEM_CACHE
    flags |= RKNN_FLAG_DISABLE_FLUSH_INPUT_MEM_CACHE;
#endif
#ifdef RKNN_FLAG_DISABLE_INVALIDATE_OUTPUT_MEM_CACHE
    flags |= RKNN_FLAG_DISABLE_INVALIDATE_OUTPUT_MEM_CACHE;
#endif
#ifdef RKNN_FLAG_ENABLE_SRAM
    if (useSram) flags |= RKNN_FLAG_ENABLE_SRAM;
#endif
    int ret = rknn_init(&context_, const_cast<char*>(modelPath.c_str()), 0, flags, nullptr);
    if (ret != RKNN_SUCC) {
        LOG(ERROR) << "[RKNN] rknn_init 失败 ret=" << ret << " model=" << modelPath;
        release();
        return -2;
    }

    const rknn_core_mask masks[3] = {
        RKNN_NPU_CORE_0, RKNN_NPU_CORE_1, RKNN_NPU_CORE_2};
    const int core = std::clamp(npuCoreIndex, 0, 2);
    ret = rknn_set_core_mask(context_, masks[core]);
    if (ret != RKNN_SUCC) {
        LOG(ERROR) << "[RKNN] NPU 核绑定失败 core=" << core << " ret=" << ret;
        release();
        return -3;
    }

    rknn_sdk_version version{};
    if (rknn_query(context_, RKNN_QUERY_SDK_VERSION, &version, sizeof(version)) != RKNN_SUCC) {
        LOG(ERROR) << "[RKNN] 无法读取 SDK/驱动版本";
        release();
        return -4;
    }
    LOG(INFO) << "[RKNN] api=" << version.api_version << " driver=" << version.drv_version;

    rknn_input_output_num io{};
    if (rknn_query(context_, RKNN_QUERY_IN_OUT_NUM, &io, sizeof(io)) != RKNN_SUCC ||
        io.n_input != 1 || io.n_output != 9) {
        LOG(ERROR) << "[RKNN] 仅支持 Rockchip 优化版 YOLOv8 1 输入/9 输出 INT8 模型，实际 input="
                   << io.n_input << " output=" << io.n_output;
        release();
        return -5;
    }

    std::memset(&inputAttr_, 0, sizeof(inputAttr_));
    inputAttr_.index = 0;
    std::memset(&inputNativeAttr_, 0, sizeof(inputNativeAttr_));
    inputNativeAttr_.index = 0;
    if (rknn_query(context_, RKNN_QUERY_INPUT_ATTR, &inputAttr_, sizeof(inputAttr_)) != RKNN_SUCC ||
        rknn_query(context_, RKNN_QUERY_NATIVE_INPUT_ATTR,
                   &inputNativeAttr_, sizeof(inputNativeAttr_)) != RKNN_SUCC) {
        release();
        return -6;
    }
    if (inputAttr_.n_dims != 4) {
        LOG(ERROR) << "[RKNN] 输入必须为四维图像张量";
        release();
        return -7;
    }
    if (inputAttr_.fmt == RKNN_TENSOR_NHWC) {
        inputHeight_ = static_cast<int>(inputAttr_.dims[1]);
        inputWidth_ = static_cast<int>(inputAttr_.dims[2]);
        inputChannels_ = static_cast<int>(inputAttr_.dims[3]);
    } else if (inputAttr_.fmt == RKNN_TENSOR_NCHW) {
        inputChannels_ = static_cast<int>(inputAttr_.dims[1]);
        inputHeight_ = static_cast<int>(inputAttr_.dims[2]);
        inputWidth_ = static_cast<int>(inputAttr_.dims[3]);
    } else {
        LOG(ERROR) << "[RKNN] 不支持的输入布局 fmt=" << inputAttr_.fmt;
        release();
        return -8;
    }
    if (inputChannels_ != 3 || inputWidth_ <= 0 || inputHeight_ <= 0) {
        LOG(ERROR) << "[RKNN] 仅支持三通道静态图像输入";
        release();
        return -9;
    }
    if (inputNativeAttr_.fmt != RKNN_TENSOR_NHWC) {
        LOG(ERROR) << "[RKNN] RGA 直写要求原生输入布局为 NHWC，实际 fmt="
                   << inputNativeAttr_.fmt;
        release();
        return -9;
    }

    outputAttrs_.resize(io.n_output);
    outputNativeAttrs_.resize(io.n_output);
    for (uint32_t index = 0; index < io.n_output; ++index) {
        std::memset(&outputAttrs_[index], 0, sizeof(rknn_tensor_attr));
        std::memset(&outputNativeAttrs_[index], 0, sizeof(rknn_tensor_attr));
        outputAttrs_[index].index = index;
        outputNativeAttrs_[index].index = index;
        if (rknn_query(context_, RKNN_QUERY_OUTPUT_ATTR, &outputAttrs_[index],
                       sizeof(rknn_tensor_attr)) != RKNN_SUCC ||
            rknn_query(context_, RKNN_QUERY_NATIVE_OUTPUT_ATTR, &outputNativeAttrs_[index],
                       sizeof(rknn_tensor_attr)) != RKNN_SUCC) {
            release();
            return -10;
        }
        const auto& logical = outputAttrs_[index];
        const auto& native = outputNativeAttrs_[index];
        if (logical.n_dims != 4 || logical.fmt != RKNN_TENSOR_NCHW ||
            native.type != RKNN_TENSOR_INT8 ||
            native.qnt_type != RKNN_TENSOR_QNT_AFFINE_ASYMMETRIC ||
            native.scale <= 0.0f ||
            (native.fmt != RKNN_TENSOR_NCHW && native.fmt != RKNN_TENSOR_NC1HWC2)) {
            LOG(ERROR) << "[RKNN] 输出 " << index
                       << " 不是 YOLOv8 RK3588 INT8 NCHW/NC1HWC2 张量";
            release();
            return -11;
        }
    }
    const uint32_t expectedClassCount = outputAttrs_[1].dims[1];
    for (int branch = 0; branch < 3; ++branch) {
        const auto& boxes = outputAttrs_[static_cast<size_t>(branch * 3)];
        const auto& scores = outputAttrs_[static_cast<size_t>(branch * 3 + 1)];
        const auto& scoreSum = outputAttrs_[static_cast<size_t>(branch * 3 + 2)];
        if (boxes.dims[1] == 0 || boxes.dims[1] % 4 != 0 ||
            boxes.dims[2] != scores.dims[2] || boxes.dims[3] != scores.dims[3] ||
            scores.dims[1] != expectedClassCount ||
            scoreSum.dims[1] != 1 || scoreSum.dims[2] != boxes.dims[2] ||
            scoreSum.dims[3] != boxes.dims[3]) {
            LOG(ERROR) << "[RKNN] YOLOv8 第 " << branch << " 个检测分支形状不匹配";
            release();
            return -12;
        }
    }

    inputNativeAttr_.type = RKNN_TENSOR_UINT8;
    inputNativeAttr_.pass_through = 0;
    inputWidthStride_ = inputNativeAttr_.w_stride > 0
        ? static_cast<int>(inputNativeAttr_.w_stride)
        : inputWidth_;
    const uint64_t memoryFlags = useSram ? RKNN_FLAG_MEMORY_TRY_ALLOC_SRAM
                                         : RKNN_FLAG_MEMORY_FLAGS_DEFAULT;
    const uint32_t inputBytes = inputNativeAttr_.size_with_stride > 0
        ? inputNativeAttr_.size_with_stride
        : static_cast<uint32_t>(inputWidthStride_ * inputHeight_ * inputChannels_);
    inputMem_ = rknn_create_mem2(context_, inputBytes, memoryFlags);
    if (!inputMem_) {
        LOG(ERROR) << "[RKNN] 输入 DMA 张量分配失败 size=" << inputBytes;
        release();
        return -13;
    }
    if (rknn_set_io_mem(context_, inputMem_, &inputNativeAttr_) != RKNN_SUCC) {
        LOG(ERROR) << "[RKNN] 输入 DMA 张量绑定失败";
        release();
        return -14;
    }
    inputRgaHandle_ = importbuffer_fd(inputMem_->fd, static_cast<int>(inputMem_->size));
    if (!inputRgaHandle_) {
        LOG(ERROR) << "[RGA] 无法导入 RKNN 输入 DMA-BUF fd=" << inputMem_->fd;
        release();
        return -15;
    }

    outputMems_.reserve(io.n_output);
    for (uint32_t index = 0; index < io.n_output; ++index) {
        const uint32_t bytes = outputNativeAttrs_[index].size_with_stride > 0
            ? outputNativeAttrs_[index].size_with_stride
            : outputNativeAttrs_[index].size;
        rknn_tensor_mem* output = rknn_create_mem2(context_, bytes, memoryFlags);
        if (!output) {
            LOG(ERROR) << "[RKNN] 输出 DMA 张量分配失败 index=" << index
                       << " size=" << bytes;
            release();
            return -16;
        }
        outputMems_.push_back(output);
        if (rknn_set_io_mem(context_, output, &outputNativeAttrs_[index]) != RKNN_SUCC) {
            LOG(ERROR) << "[RKNN] 输出 DMA 张量绑定失败 index=" << index;
            release();
            return -17;
        }
    }

    size_t candidates = 0;
    for (int branch = 0; branch < 3; ++branch) {
        const auto& boxes = outputAttrs_[static_cast<size_t>(branch * 3)];
        candidates += static_cast<size_t>(boxes.dims[2]) * boxes.dims[3];
    }
    scratchBoxes_.reserve(candidates);
    scratchScores_.reserve(candidates);
    scratchClassIds_.reserve(candidates);
    scratchOrder_.reserve(candidates);
    scratchKeep_.reserve(candidates);
    scratchSuppressed_.reserve(candidates);

    rknn_mem_size memory{};
    if (rknn_query(context_, RKNN_QUERY_MEM_SIZE, &memory, sizeof(memory)) == RKNN_SUCC) {
        LOG(INFO) << "[RKNN] memory weight=" << memory.total_weight_size
                  << " internal=" << memory.total_internal_size
                  << " dma=" << memory.total_dma_allocated_size
                  << " sram=" << memory.total_sram_size
                  << " free_sram=" << memory.free_sram_size;
    }

    classes_ = modelClasses;
    const uint32_t classCount = expectedClassCount;
    if (!classes_.empty() && classes_.size() != classCount) {
        LOG(WARNING) << "[RKNN] 类别名数量 " << classes_.size()
                     << " 与模型类别数 " << classCount << " 不一致";
    }
    loadedModelPath_ = modelPath;
    inferEp_ = "rknn-core" + std::to_string(core);
    modelLayout_ = "yolov8-dfl-int8-9out";
    perfQueryEnabled_ = enablePerfQuery;
    runCounter_ = 0;
    ready_ = true;
    LOG(INFO) << "[RKNN] YOLOv8n INT8 模型加载完成 model=" << modelPath
              << " input=" << inputWidth_ << "x" << inputHeight_
              << " candidates=" << candidates << " ep=" << inferEp_;
    return 0;
}

int YoloEngine::rgaFormat(runtime::rk3588::FrameFormat format) {
    using runtime::rk3588::FrameFormat;
    switch (format) {
        case FrameFormat::BGR888: return RK_FORMAT_BGR_888;
        case FrameFormat::RGB888: return RK_FORMAT_RGB_888;
        case FrameFormat::NV12: return RK_FORMAT_YCbCr_420_SP;
    }
    return RK_FORMAT_UNKNOWN;
}

int YoloEngine::prepareRgaInput(const runtime::rk3588::FrameView& frame) {
    if (!frame.valid()) return -1;
    const int sourceFormat = rgaFormat(frame.format);
    if (sourceFormat == RK_FORMAT_UNKNOWN) return -2;
    const int sourceWidthStride = frame.widthStride > 0 ? frame.widthStride : frame.width;
    const int sourceHeightStride = frame.heightStride > 0 ? frame.heightStride : frame.height;

    rga_buffer_t source{};
    if (frame.dmaBacked()) {
        const uint64_t key = (frame.bufferPoolId << 32) ^ static_cast<uint32_t>(frame.dmaFd);
        auto found = importedSources_.find(key);
        if (found == importedSources_.end()) {
            if (importedSources_.size() >= 64) {
                for (auto& item : importedSources_) {
                    if (item.second.handle) releasebuffer_handle(item.second.handle);
                }
                importedSources_.clear();
            }
            const int bytes = frame.format == runtime::rk3588::FrameFormat::NV12
                ? sourceWidthStride * sourceHeightStride * 3 / 2
                : sourceWidthStride * sourceHeightStride * 3;
            ImportedBuffer imported;
            imported.handle = importbuffer_fd(frame.dmaFd, bytes);
            imported.width = frame.width;
            imported.height = frame.height;
            imported.widthStride = sourceWidthStride;
            imported.heightStride = sourceHeightStride;
            imported.format = sourceFormat;
            if (!imported.handle) {
                LOG(ERROR) << "[RGA] 导入 MPP DMA-BUF 失败 fd=" << frame.dmaFd;
                return -3;
            }
            found = importedSources_.emplace(key, imported).first;
        }
        source = wrapbuffer_handle_t(found->second.handle, frame.width, frame.height,
                                     sourceWidthStride, sourceHeightStride, sourceFormat);
    } else {
        source = wrapbuffer_virtualaddr_t(frame.virtualAddress, frame.width, frame.height,
                                          sourceWidthStride, sourceHeightStride, sourceFormat);
    }
    rga_buffer_t destination =
        wrapbuffer_handle_t(inputRgaHandle_, inputWidth_, inputHeight_,
                            inputWidthStride_, inputHeight_, RK_FORMAT_RGB_888);

    const float scale = std::min(inputWidth_ / static_cast<float>(frame.width),
                                 inputHeight_ / static_cast<float>(frame.height));
    int resizedWidth = std::clamp(
        static_cast<int>(std::round(frame.width * scale)), 2, inputWidth_);
    int resizedHeight = std::clamp(
        static_cast<int>(std::round(frame.height * scale)), 2, inputHeight_);
    const int padX = (inputWidth_ - resizedWidth) / 2;
    const int padY = (inputHeight_ - resizedHeight) / 2;

    IM_STATUS status = IM_STATUS_SUCCESS;
    if (!paddingInitialized_ || paddedWidth_ != resizedWidth || paddedHeight_ != resizedHeight) {
        im_rect whole{0, 0, inputWidth_, inputHeight_};
        status = imfill(destination, whole, 0x727272);
        if (status != IM_STATUS_SUCCESS) {
            LOG(ERROR) << "[RGA] letterbox 填充失败: " << imStrError(status);
            return -4;
        }
        paddingInitialized_ = true;
        paddedWidth_ = resizedWidth;
        paddedHeight_ = resizedHeight;
    }
    im_rect sourceRect{0, 0, frame.width, frame.height};
    im_rect destinationRect{padX, padY, resizedWidth, resizedHeight};
    im_rect patternRect{};
    rga_buffer_t pattern{};
    im_opt_t options{};
    status = improcess(source, destination, pattern, sourceRect, destinationRect,
                       patternRect, -1, nullptr, &options, IM_SYNC);
    if (status != IM_STATUS_SUCCESS) {
        LOG(ERROR) << "[RGA] DMA 预处理失败: " << imStrError(status)
                   << " src=" << frame.width << "x" << frame.height
                   << " dst=" << resizedWidth << "x" << resizedHeight;
        return -5;
    }
    lastScale_ = scale;
    lastPadX_ = padX;
    lastPadY_ = padY;
    return rknn_mem_sync(context_, inputMem_, RKNN_MEMORY_SYNC_TO_DEVICE);
}

int8_t YoloEngine::outputValue(size_t outputIndex, int channel, int y, int x) const {
    const auto& native = outputNativeAttrs_[outputIndex];
    const int8_t* data = static_cast<const int8_t*>(outputMems_[outputIndex]->virt_addr);
    if (native.fmt == RKNN_TENSOR_NC1HWC2 && native.n_dims == 5) {
        const size_t c2 = native.dims[4];
        const size_t height = native.dims[2];
        const size_t width = native.dims[3];
        const size_t index =
            (((static_cast<size_t>(channel) / c2) * height + static_cast<size_t>(y)) *
                 width +
             static_cast<size_t>(x)) *
                c2 +
            static_cast<size_t>(channel) % c2;
        return data[index];
    }
    const size_t height = native.dims[2];
    const size_t width = native.dims[3];
    const size_t index =
        (static_cast<size_t>(channel) * height + static_cast<size_t>(y)) * width +
        static_cast<size_t>(x);
    return data[index];
}

float YoloEngine::dequantize(size_t outputIndex, int8_t value) const {
    const auto& attr = outputNativeAttrs_[outputIndex];
    return (static_cast<float>(value) - static_cast<float>(attr.zp)) * attr.scale;
}

int YoloEngine::parseYolov8Output(const runtime::rk3588::FrameView& frame,
                                  float scale,
                                  int padX,
                                  int padY,
                                  std::vector<DetectObject>& detections) {
    detections.clear();
    scratchBoxes_.clear();
    scratchScores_.clear();
    scratchClassIds_.clear();

    for (int branch = 0; branch < 3; ++branch) {
        const size_t boxIndex = static_cast<size_t>(branch * 3);
        const size_t scoreIndex = boxIndex + 1;
        const size_t sumIndex = boxIndex + 2;
        const auto& boxAttr = outputAttrs_[boxIndex];
        const auto& scoreAttr = outputAttrs_[scoreIndex];
        const int height = static_cast<int>(boxAttr.dims[2]);
        const int width = static_cast<int>(boxAttr.dims[3]);
        const int stride = inputHeight_ / height;
        const int dflLength = static_cast<int>(boxAttr.dims[1]) / 4;
        const int classCount = static_cast<int>(scoreAttr.dims[1]);
        const auto& scoreNative = outputNativeAttrs_[scoreIndex];
        const auto& sumNative = outputNativeAttrs_[sumIndex];
        const int scoreThreshold = std::clamp(
            static_cast<int>(std::lround(scoreThreshold_ / scoreNative.scale)) +
                scoreNative.zp,
            -128, 127);
        const int sumThreshold = std::clamp(
            static_cast<int>(std::lround(scoreThreshold_ / sumNative.scale)) +
                sumNative.zp,
            -128, 127);

        for (int y = 0; y < height; ++y) {
            for (int x = 0; x < width; ++x) {
                if (static_cast<int>(outputValue(sumIndex, 0, y, x)) < sumThreshold) continue;
                int bestClass = -1;
                int bestRawScore = -129;
                for (int classId = 0; classId < classCount; ++classId) {
                    const int raw = outputValue(scoreIndex, classId, y, x);
                    if (raw > bestRawScore) {
                        bestRawScore = raw;
                        bestClass = classId;
                    }
                }
                if (bestClass < 0 || bestRawScore < scoreThreshold) continue;

                float distances[4]{};
                for (int side = 0; side < 4; ++side) {
                    float maximum = -std::numeric_limits<float>::infinity();
                    for (int bin = 0; bin < dflLength; ++bin) {
                        maximum = std::max(
                            maximum,
                            dequantize(boxIndex,
                                       outputValue(boxIndex, side * dflLength + bin, y, x)));
                    }
                    float denominator = 0.0f;
                    float numerator = 0.0f;
                    for (int bin = 0; bin < dflLength; ++bin) {
                        const float value =
                            dequantize(boxIndex,
                                       outputValue(boxIndex, side * dflLength + bin, y, x));
                        const float weight = std::exp(value - maximum);
                        denominator += weight;
                        numerator += weight * static_cast<float>(bin);
                    }
                    distances[side] = denominator > 0.0f ? numerator / denominator : 0.0f;
                }

                const float centerX = (static_cast<float>(x) + 0.5f) * stride;
                const float centerY = (static_cast<float>(y) + 0.5f) * stride;
                const float x1 = centerX - distances[0] * stride;
                const float y1 = centerY - distances[1] * stride;
                const float x2 = centerX + distances[2] * stride;
                const float y2 = centerY + distances[3] * stride;
                scratchBoxes_.emplace_back(
                    x1, y1, std::max(0.0f, x2 - x1), std::max(0.0f, y2 - y1));
                scratchScores_.push_back(
                    dequantize(scoreIndex, static_cast<int8_t>(bestRawScore)));
                scratchClassIds_.push_back(bestClass);
            }
        }
    }

    scratchOrder_.resize(scratchBoxes_.size());
    std::iota(scratchOrder_.begin(), scratchOrder_.end(), 0);
    std::sort(scratchOrder_.begin(), scratchOrder_.end(), [&](size_t left, size_t right) {
        return scratchScores_[left] > scratchScores_[right];
    });
    scratchSuppressed_.assign(scratchBoxes_.size(), 0);
    scratchKeep_.clear();
    for (size_t orderIndex = 0; orderIndex < scratchOrder_.size(); ++orderIndex) {
        const size_t current = scratchOrder_[orderIndex];
        if (scratchSuppressed_[current]) continue;
        scratchKeep_.push_back(current);
        for (size_t candidateIndex = orderIndex + 1;
             candidateIndex < scratchOrder_.size(); ++candidateIndex) {
            const size_t candidate = scratchOrder_[candidateIndex];
            if (!scratchSuppressed_[candidate] &&
                scratchClassIds_[current] == scratchClassIds_[candidate] &&
                intersectionOverUnion(scratchBoxes_[current], scratchBoxes_[candidate]) >
                    nmsThreshold_) {
                scratchSuppressed_[candidate] = 1;
            }
        }
    }

    detections.reserve(std::max(detections.capacity(), scratchKeep_.size()));
    auto className = [&](int index) {
        return index >= 0 && index < static_cast<int>(classes_.size())
            ? classes_[static_cast<size_t>(index)]
            : "class_" + std::to_string(index);
    };
    auto restoreX = [&](float coordinate) {
        return std::clamp((coordinate - padX) / scale, 0.0f,
                          static_cast<float>(frame.width));
    };
    auto restoreY = [&](float coordinate) {
        return std::clamp((coordinate - padY) / scale, 0.0f,
                          static_cast<float>(frame.height));
    };
    for (size_t index : scratchKeep_) {
        const cv::Rect2f& box = scratchBoxes_[index];
        DetectObject detection{};
        detection.x1 = static_cast<int>(restoreX(box.x));
        detection.y1 = static_cast<int>(restoreY(box.y));
        detection.x2 = static_cast<int>(restoreX(box.x + box.width));
        detection.y2 = static_cast<int>(restoreY(box.y + box.height));
        detection.class_score = scratchScores_[index];
        detection.class_id = scratchClassIds_[index];
        detection.class_name = className(detection.class_id);
        detections.push_back(std::move(detection));
    }
    return 0;
}

int YoloEngine::Run(const runtime::rk3588::FrameView& frame,
                    std::vector<DetectObject>& objects) {
    if (!ready_) return -1;
    int ret = prepareRgaInput(frame);
    if (ret != RKNN_SUCC) return -2;
    ret = rknn_run(context_, nullptr);
    if (ret != RKNN_SUCC) {
        LOG(ERROR) << "[RKNN] rknn_run 失败 ret=" << ret;
        return -3;
    }
    for (rknn_tensor_mem* output : outputMems_) {
        ret = rknn_mem_sync(context_, output, RKNN_MEMORY_SYNC_FROM_DEVICE);
        if (ret != RKNN_SUCC) return -4;
    }
    ++runCounter_;
    if (perfQueryEnabled_ && runCounter_ % 30 == 1) {
        rknn_perf_run perf{};
        if (rknn_query(context_, RKNN_QUERY_PERF_RUN, &perf, sizeof(perf)) == RKNN_SUCC) {
            lastNpuDurationUs_ = perf.run_duration;
        }
    }
    return parseYolov8Output(frame, lastScale_, lastPadX_, lastPadY_, objects);
}

int YoloEngine::Run(cv::Mat& image, std::vector<DetectObject>& objects) {
    runtime::rk3588::FrameView view;
    view.virtualAddress = image.data;
    view.width = image.cols;
    view.height = image.rows;
    view.widthStride = static_cast<int>(image.step[0] / image.elemSize());
    view.heightStride = image.rows;
    view.format = runtime::rk3588::FrameFormat::BGR888;
    return Run(view, objects);
}
