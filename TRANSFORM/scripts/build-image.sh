#!/usr/bin/env bash
# 构建 TRANSFORM Runtime 镜像，导出 tar 并 gzip 压缩，供 NODE 离线分发
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${TRANSFORM_IMAGE:-easyaiot/transform-runtime:1.0.0}"
OUT_TAR="${TRANSFORM_IMAGE_TAR:-$ROOT/dist/transform-runtime-1.0.0.tar}"
OUT_GZ="${TRANSFORM_IMAGE_TAR_GZ:-${OUT_TAR}.gz}"
FORCE="${TRANSFORM_IMAGE_FORCE:-0}"

cd "$ROOT"
if [[ ! -f transform-runtime/target/transform-runtime-1.0.0.jar ]]; then
  mvn -pl transform-runtime -am package -DskipTests -q
fi

mkdir -p "$(dirname "$OUT_TAR")"

need_build=1
if [[ "$FORCE" != "1" ]] \
  && docker image inspect "$IMAGE" >/dev/null 2>&1 \
  && [[ -f "$OUT_GZ" || -f "$OUT_TAR" ]]; then
  need_build=0
  echo "reuse existing image=$IMAGE artifact"
fi

if [[ "$need_build" == "1" ]]; then
  docker build -t "$IMAGE" -f Dockerfile .
  docker save -o "$OUT_TAR" "$IMAGE"
  gzip -f -k "$OUT_TAR" 2>/dev/null || gzip -f "$OUT_TAR"
  # gzip -k 保留 tar；无 -k 时只剩 gz，再解压一份供兼容
  if [[ ! -f "$OUT_TAR" && -f "$OUT_GZ" ]]; then
    gunzip -c "$OUT_GZ" > "$OUT_TAR"
  elif [[ -f "$OUT_TAR" && ! -f "$OUT_GZ" ]]; then
    gzip -c "$OUT_TAR" > "$OUT_GZ"
  fi
fi

# 确保两份都在（分发优先用 gz）
if [[ -f "$OUT_TAR" && ! -f "$OUT_GZ" ]]; then
  gzip -c "$OUT_TAR" > "$OUT_GZ"
fi
if [[ -f "$OUT_GZ" && ! -f "$OUT_TAR" ]]; then
  gunzip -c "$OUT_GZ" > "$OUT_TAR"
fi

echo "image=$IMAGE"
echo "tar=$OUT_TAR"
echo "tar.gz=$OUT_GZ"
echo "load on node: gunzip -c $(basename "$OUT_GZ") | docker load"
