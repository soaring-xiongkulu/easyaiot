#!/usr/bin/env bash
set -euo pipefail

[[ $# -ge 2 ]] || { echo "用法: $0 <model.onnx> <model.engine> [fp16|fp32]" >&2; exit 2; }
ONNX="$1"
ENGINE="$2"
PRECISION="${3:-fp16}"
[[ -s "$ONNX" ]] || { echo "ONNX 不存在或为空: $ONNX" >&2; exit 1; }
command -v trtexec >/dev/null 2>&1 || { echo "缺少 TensorRT trtexec" >&2; exit 1; }
case "$ENGINE" in *.engine|*.plan) ;; *) echo "输出必须是 .engine 或 .plan" >&2; exit 1 ;; esac
case "$PRECISION" in fp16) precision_flag=--fp16 ;; fp32) precision_flag=--noTF32 ;; *) echo "精度仅支持 fp16|fp32" >&2; exit 1 ;; esac

mkdir -p "$(dirname "$ENGINE")"
trtexec --onnx="$ONNX" --saveEngine="$ENGINE" "$precision_flag" \
  --useCudaGraph --noDataTransfers --builderOptimizationLevel=5 --timingCacheFile="${ENGINE}.timing.cache"
echo "[NVIDIA] TensorRT engine 已生成: $ENGINE"
echo "[NVIDIA] engine 与 GPU 架构/TensorRT 版本绑定，请在实际盒子上构建并验收"
