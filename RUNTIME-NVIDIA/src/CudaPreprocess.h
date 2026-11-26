#pragma once

#include <NvInfer.h>
#include <cuda_runtime_api.h>

namespace easyaiot::nvidia {

struct Letterbox {
    float scale{1.0F};
    float padX{0.0F};
    float padY{0.0F};
};

Letterbox launchNv12Letterbox(const unsigned char* yPlane, int yPitch,
                              const unsigned char* uvPlane, int uvPitch,
                              int sourceWidth, int sourceHeight,
                              void* tensor, nvinfer1::DataType tensorType,
                              int targetWidth, int targetHeight,
                              cudaStream_t stream);

}  // namespace easyaiot::nvidia
