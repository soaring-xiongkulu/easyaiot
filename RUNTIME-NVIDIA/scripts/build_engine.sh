#!/usr/bin/env bash
set -euo pipefail

[[ $# -ge 2 ]] || {
  echo "用法: $0 <model.onnx> <model.engine> [fp16|int8|fp32] [calibration.cache]" >&2
  exit 2
}
ONNX="$1"
ENGINE="$2"
PRECISION="${3:-fp16}"
CALIBRATION_CACHE="${4:-}"
[[ -s "$ONNX" ]] || { echo "ONNX 不存在或为空: $ONNX" >&2; exit 1; }
command -v trtexec >/dev/null 2>&1 || { echo "缺少 TensorRT trtexec" >&2; exit 1; }
case "$ENGINE" in *.engine|*.plan) ;; *) echo "输出必须是 .engine 或 .plan" >&2; exit 1 ;; esac
precision_flags=()
case "$PRECISION" in
  fp16) precision_flags+=(--fp16) ;;
  fp32) precision_flags+=(--noTF32) ;;
  int8)
    precision_flags+=(--int8)
    if [[ -n "$CALIBRATION_CACHE" ]]; then
      [[ -s "$CALIBRATION_CACHE" ]] || { echo "INT8 校准缓存不存在或为空: $CALIBRATION_CACHE" >&2; exit 1; }
      precision_flags+=("--calib=$CALIBRATION_CACHE")
    else
      echo "[NVIDIA] INT8 未提供校准缓存：要求 ONNX 自带显式 Q/DQ 量化节点"
    fi
    ;;
  *) echo "精度仅支持 fp16|int8|fp32" >&2; exit 1 ;;
esac

mkdir -p "$(dirname "$ENGINE")"
trtexec --onnx="$ONNX" --saveEngine="$ENGINE" "${precision_flags[@]}" \
  --useCudaGraph --noDataTransfers --builderOptimizationLevel=5 --timingCacheFile="${ENGINE}.timing.cache"
[[ -s "$ENGINE" ]] || { echo "TensorRT 未生成有效 engine: $ENGINE" >&2; exit 1; }
echo "[NVIDIA] TensorRT engine 已生成: $ENGINE"
echo "[NVIDIA] engine 与 GPU 架构/TensorRT 版本绑定，请在实际盒子上构建并验收"
