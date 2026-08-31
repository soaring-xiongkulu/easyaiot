#!/usr/bin/env bash
# 下载 InsightFace buffalo_l 的 ArcFace 识别模型和 SCRFD 检测模型
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${SCRIPT_DIR}/face_rec.onnx"
DETECT_TARGET="${SCRIPT_DIR}/scrfd_10g.onnx"
ZIP_URL="${FACE_REC_MODEL_DOWNLOAD_URL:-https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip}"
ONNX_IN_ZIP_CANDIDATES=("w600k_r50.onnx" "buffalo_l/w600k_r50.onnx")

if [ -f "$TARGET" ] && [ -f "$DETECT_TARGET" ] \
  && [ "$(stat -c%s "$TARGET" 2>/dev/null || stat -f%z "$TARGET" 2>/dev/null || echo 0)" -ge 10485760 ] \
  && [ "$(stat -c%s "$DETECT_TARGET" 2>/dev/null || stat -f%z "$DETECT_TARGET" 2>/dev/null || echo 0)" -ge 1048576 ]; then
  echo "[INFO] ArcFace 与 SCRFD 模型均已存在"
  exit 0
fi

# Docker 单独挂载不存在的文件时会建成目录，需先清理
if [ -d "$TARGET" ]; then
  echo "[WARN] $TARGET 误为目录（多为 Docker 文件卷导致），正在删除..."
  rm -rf "$TARGET"
fi

# 清理空文件或损坏的占位文件
if [ -e "$TARGET" ]; then
  rm -f "$TARGET"
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "[ERROR] 需要 curl 才能下载模型" >&2
  exit 1
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
ZIP_FILE="${TMP_DIR}/buffalo_l.zip"

echo "[INFO] 正在下载 buffalo_l.zip（约 167MB）..."
curl -L --fail --retry 3 --retry-delay 5 -o "$ZIP_FILE" "$ZIP_URL"

extract_ok=0
if command -v unzip >/dev/null 2>&1; then
  for ONNX_IN_ZIP in "${ONNX_IN_ZIP_CANDIDATES[@]}"; do
    if unzip -q -j "$ZIP_FILE" "$ONNX_IN_ZIP" -d "$TMP_DIR" 2>/dev/null; then
      mv "${TMP_DIR}/w600k_r50.onnx" "$TARGET"
      extract_ok=1
      break
    fi
  done
fi

if [ "$extract_ok" -ne 1 ]; then
  if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] 解压失败且未找到 python3" >&2
    exit 1
  fi
  python3 - "$ZIP_FILE" "$TARGET" <<'PY'
import sys
import zipfile

zip_path, target_path = sys.argv[1:3]
candidates = ("w600k_r50.onnx", "buffalo_l/w600k_r50.onnx")
with zipfile.ZipFile(zip_path) as zf:
    names = set(zf.namelist())
    member = next((c for c in candidates if c in names), None)
    if member is None:
        member = next(
            (n for n in zf.namelist() if n.rstrip("/").endswith("w600k_r50.onnx")),
            None,
        )
    if member is None:
        onnx = [n for n in zf.namelist() if n.lower().endswith(".onnx")]
        raise SystemExit(f"archive 中未找到 w600k_r50.onnx，onnx 条目: {onnx}")
    with zf.open(member) as src, open(target_path, "wb") as dst:
        dst.write(src.read())
PY
fi

if command -v unzip >/dev/null 2>&1; then
  unzip -q -p "$ZIP_FILE" det_10g.onnx > "$DETECT_TARGET"
else
  python3 - "$ZIP_FILE" "$DETECT_TARGET" <<'PY'
import sys, zipfile
with zipfile.ZipFile(sys.argv[1]) as zf, zf.open('det_10g.onnx') as src, open(sys.argv[2], 'wb') as dst:
    dst.write(src.read())
PY
fi

echo "[SUCCESS] ArcFace: $TARGET ($(du -h "$TARGET" | awk '{print $1}'))"
echo "[SUCCESS] SCRFD: $DETECT_TARGET ($(du -h "$DETECT_TARGET" | awk '{print $1}'))"
