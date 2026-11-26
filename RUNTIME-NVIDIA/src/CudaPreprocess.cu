#include "CudaPreprocess.h"

#include <cuda_fp16.h>

#include <algorithm>
#include <stdexcept>

namespace easyaiot::nvidia {
namespace {

__device__ __forceinline__ unsigned char clampByte(float value) {
    return static_cast<unsigned char>(fminf(255.0F, fmaxf(0.0F, value)));
}

template <typename T>
__device__ __forceinline__ T normalized(unsigned char value);

template <>
__device__ __forceinline__ float normalized<float>(unsigned char value) {
    return static_cast<float>(value) * (1.0F / 255.0F);
}

template <>
__device__ __forceinline__ __half normalized<__half>(unsigned char value) {
    return __float2half(static_cast<float>(value) * (1.0F / 255.0F));
}

template <typename T>
__global__ void nv12LetterboxKernel(const unsigned char* yPlane, int yPitch,
                                    const unsigned char* uvPlane, int uvPitch,
                                    int sourceWidth, int sourceHeight,
                                    T* output, int targetWidth, int targetHeight,
                                    float scale, float padX, float padY) {
    const int x = static_cast<int>(blockIdx.x * blockDim.x + threadIdx.x);
    const int y = static_cast<int>(blockIdx.y * blockDim.y + threadIdx.y);
    if (x >= targetWidth || y >= targetHeight) return;

    unsigned char red = 114;
    unsigned char green = 114;
    unsigned char blue = 114;
    const float sourceX = (static_cast<float>(x) + 0.5F - padX) / scale - 0.5F;
    const float sourceY = (static_cast<float>(y) + 0.5F - padY) / scale - 0.5F;
    if (sourceX >= 0.0F && sourceY >= 0.0F &&
        sourceX < static_cast<float>(sourceWidth) &&
        sourceY < static_cast<float>(sourceHeight)) {
        const int sx = min(sourceWidth - 1, max(0, __float2int_rn(sourceX)));
        const int sy = min(sourceHeight - 1, max(0, __float2int_rn(sourceY)));
        const int luma = static_cast<int>(yPlane[sy * yPitch + sx]);
        const int uvOffset = (sy / 2) * uvPitch + (sx / 2) * 2;
        const int u = static_cast<int>(uvPlane[uvOffset]) - 128;
        const int v = static_cast<int>(uvPlane[uvOffset + 1]) - 128;
        // BT.709 full-range approximation. The hot path remains entirely on CUDA.
        red = clampByte(static_cast<float>(luma) + 1.5748F * static_cast<float>(v));
        green = clampByte(static_cast<float>(luma) - 0.1873F * static_cast<float>(u) -
                          0.4681F * static_cast<float>(v));
        blue = clampByte(static_cast<float>(luma) + 1.8556F * static_cast<float>(u));
    }

    const int plane = targetWidth * targetHeight;
    const int offset = y * targetWidth + x;
    output[offset] = normalized<T>(red);
    output[plane + offset] = normalized<T>(green);
    output[2 * plane + offset] = normalized<T>(blue);
}

void check(cudaError_t code, const char* operation) {
    if (code != cudaSuccess) {
        throw std::runtime_error(std::string(operation) + ": " + cudaGetErrorString(code));
    }
}
}  // namespace

Letterbox launchNv12Letterbox(const unsigned char* yPlane, int yPitch,
                              const unsigned char* uvPlane, int uvPitch,
                              int sourceWidth, int sourceHeight,
                              void* tensor, nvinfer1::DataType tensorType,
                              int targetWidth, int targetHeight,
                              cudaStream_t stream) {
    if (!yPlane || !uvPlane || !tensor || sourceWidth <= 0 || sourceHeight <= 0 ||
        targetWidth <= 0 || targetHeight <= 0) {
        throw std::invalid_argument("invalid CUDA preprocessing buffer or shape");
    }
    const float scale = std::min(static_cast<float>(targetWidth) / sourceWidth,
                                 static_cast<float>(targetHeight) / sourceHeight);
    const Letterbox transform{scale,
                              (targetWidth - sourceWidth * scale) * 0.5F,
                              (targetHeight - sourceHeight * scale) * 0.5F};
    const dim3 block(16, 16);
    const dim3 grid((targetWidth + block.x - 1) / block.x,
                    (targetHeight + block.y - 1) / block.y);
    if (tensorType == nvinfer1::DataType::kFLOAT) {
        nv12LetterboxKernel<float><<<grid, block, 0, stream>>>(
            yPlane, yPitch, uvPlane, uvPitch, sourceWidth, sourceHeight,
            static_cast<float*>(tensor), targetWidth, targetHeight,
            transform.scale, transform.padX, transform.padY);
    } else if (tensorType == nvinfer1::DataType::kHALF) {
        nv12LetterboxKernel<__half><<<grid, block, 0, stream>>>(
            yPlane, yPitch, uvPlane, uvPitch, sourceWidth, sourceHeight,
            static_cast<__half*>(tensor), targetWidth, targetHeight,
            transform.scale, transform.padX, transform.padY);
    } else {
        throw std::runtime_error("TensorRT input must be FP32 or FP16");
    }
    check(cudaPeekAtLastError(), "NV12 CUDA preprocessing launch failed");
    return transform;
}

}  // namespace easyaiot::nvidia
