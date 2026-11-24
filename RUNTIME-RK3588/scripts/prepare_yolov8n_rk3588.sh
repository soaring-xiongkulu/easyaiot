#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATASET="${1:-}"
OUTPUT="${2:-$ROOT/models/yolov8n-rk3588-int8.rknn}"
ONNX_PATH="${RK3588_YOLOV8_ONNX:-$ROOT/models/yolov8n-rockchip-9out.onnx}"
MODEL_URL="https://ftrg.zbox.filez.com/v2/delivery/data/95f00b0fc900458ba134f8b180b3f7a1/examples/yolov8/yolov8n.onnx"

if [[ -z "$DATASET" || ! -f "$DATASET" ]]; then
  echo "用法: $0 <calibration.txt> [output.rknn]" >&2
  echo "calibration.txt 每行是一张有代表性的现场图片路径。" >&2
  exit 64
fi

mkdir -p "$(dirname "$ONNX_PATH")" "$(dirname "$OUTPUT")"
if [[ ! -s "$ONNX_PATH" ]]; then
  echo "下载 Rockchip Model Zoo 优化版 YOLOv8n（1 输入/9 输出）..."
  if command -v curl >/dev/null 2>&1; then
    curl --fail --location --retry 3 "$MODEL_URL" --output "$ONNX_PATH"
  elif command -v wget >/dev/null 2>&1; then
    wget --tries=3 --output-document="$ONNX_PATH" "$MODEL_URL"
  else
    echo "缺少 curl/wget，无法下载官方模型。" >&2
    exit 69
  fi
fi

python3 "$ROOT/scripts/convert_rknn_model.py" \
  "$ONNX_PATH" "$OUTPUT" --dataset "$DATASET"
echo "MODEL_OK: $OUTPUT"
