#!/usr/bin/env bash
# 可选：从 VIDEO 种子拷贝算法服务到 EDGE/runtime，再打上 EDGE 自有 overlays。
# 日常运行以 EDGE/runtime 为准；VIDEO 不是运行时依赖。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DEST="${ROOT}/EDGE/runtime"
OVERLAY_APPLY="${DEST}/overlays/apply_overlays.py"

copy_tree() {
  local src="$1"
  local dest="$2"
  mkdir -p "${dest}"
  # 避免依赖 rsync（部分环境会卡住）；排除缓存
  find "${src}" -type f ! -path '*/__pycache__/*' ! -name '*.pyc' -print0 \
    | while IFS= read -r -d '' f; do
        rel="${f#${src}/}"
        mkdir -p "${dest}/$(dirname "${rel}")"
        cp -f "${f}" "${dest}/${rel}"
      done
}

mkdir -p "${DEST}/services"
for svc in realtime_algorithm_service snapshot_algorithm_service patrol_algorithm_service; do
  src="${ROOT}/VIDEO/services/${svc}"
  if [[ -d "${src}" ]]; then
    copy_tree "${src}" "${DEST}/services/${svc}"
    echo "seeded ${svc}"
  else
    echo "skip missing ${src}" >&2
  fi
done

# 将 VIDEO 的中文检测标签绘制工具同步到 EDGE 公共运行库。
# EDGE 实时/抓拍服务会从 lib.utf8_detection_label 导入该工具，用 Pillow + CJK
# 字体绘制中文类别名；若重新生成 EDGE/runtime 时漏复制此文件，服务会因缺少
# 模块而无法启动。这里保留独立副本，确保 EDGE 部署后不依赖 VIDEO 源码目录。
mkdir -p "${DEST}/lib"
cp -f \
  "${ROOT}/VIDEO/app/utils/utf8_detection_label.py" \
  "${DEST}/lib/utf8_detection_label.py"

if [[ -f "${OVERLAY_APPLY}" ]]; then
  python3 "${OVERLAY_APPLY}"
else
  echo "[warn] overlay applier missing: ${OVERLAY_APPLY}" >&2
fi

echo "done → ${DEST} （EDGE overlays 已重新应用；VIDEO 源码未被修改）"
