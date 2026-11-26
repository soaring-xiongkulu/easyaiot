#!/usr/bin/env bash
set -euo pipefail

MODE="${1:---runtime}"
fail() { echo "[NVIDIA 预检失败] $*" >&2; exit 1; }
ok() { echo "[NVIDIA 预检] $*"; }

[[ "$(uname -s)" == "Linux" ]] || fail "仅支持 Linux NVIDIA 盒子"

is_jetson=0
if [[ -r /proc/device-tree/compatible ]] && tr '\0' ' ' < /proc/device-tree/compatible | grep -Eqi 'nvidia,tegra'; then
  is_jetson=1
fi
if [[ "$is_jetson" == "0" ]]; then
  command -v nvidia-smi >/dev/null 2>&1 || fail "未发现 Jetson 设备树或 nvidia-smi"
  nvidia-smi -L 2>/dev/null | grep -qi 'GPU' || fail "NVIDIA 驱动没有可用 GPU"
else
  [[ -e /dev/nvhost-ctrl-gpu || -e /dev/nvmap ]] || fail "Jetson GPU 设备节点不可用"
fi
ok "NVIDIA GPU 识别通过"

find_library() {
  local pattern="$1" glob="$2"
  ldconfig -p 2>/dev/null | grep -E "$pattern" >/dev/null ||
    find /usr /usr/local /opt -name "$glob" -print -quit 2>/dev/null | grep . >/dev/null
}
find_library 'libcuda\.so' 'libcuda.so*' || fail "缺少 NVIDIA Driver libcuda"
find_library 'libcudart\.so' 'libcudart.so*' || fail "缺少 CUDA Runtime libcudart"
find_library 'libnvinfer\.so' 'libnvinfer.so*' || fail "缺少 TensorRT libnvinfer"
ok "CUDA / TensorRT 动态库通过"

command -v ffmpeg >/dev/null 2>&1 || fail "缺少 FFmpeg"
ffmpeg -hide_banner -hwaccels 2>/dev/null | grep -qx 'cuda' \
  || fail "FFmpeg 未暴露 CUDA hwdevice，无法生成 CUDA surface"
ffmpeg -hide_banner -decoders 2>/dev/null | grep -Eq 'cuvid|nvdec' \
  || fail "FFmpeg 未暴露 NVDEC/CUVID 解码器；不会回退软件解码"
ok "NVDEC → CUDA surface 能力通过"

if [[ "$MODE" == "--build" ]]; then
  for command in cmake c++ pkg-config nvcc; do
    command -v "$command" >/dev/null 2>&1 || fail "缺少编译工具: $command"
  done
  [[ -r /usr/include/NvInferVersion.h || -r /usr/include/x86_64-linux-gnu/NvInferVersion.h || \
     -r /usr/include/aarch64-linux-gnu/NvInferVersion.h || -r /usr/local/include/NvInferVersion.h ]] \
    || fail "缺少 TensorRT C++ 头文件"
fi
