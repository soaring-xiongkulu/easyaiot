#!/usr/bin/env bash
# ============================================
# 在目标 OS 容器内编译并导出 RUNTIME 离线包（禁止 Ubuntu 冒充 openEuler）
#
# 用法:
#   bash RUNTIME/scripts/export_runtime_os_container.sh openeuler22
#   bash RUNTIME/scripts/export_runtime_all.sh --compile-target openeuler
#   RUNTIME_OS_CONTAINER_IMAGE=... bash ... openeuler24
#
# 产出:
#   RUNTIME/.bundle-runtime/{os_family}/{arch}/easyaiot-runtime-*.tar.gz
# ============================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"

# shellcheck disable=SC1091
source "$ROOT/scripts/os_family.sh"
# shellcheck disable=SC1091
source "$ROOT/scripts/runtime_os_matrix.sh"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'
print_info() { echo -e "${BLUE}[RUNTIME/os-container]${NC} $1"; }
print_success() { echo -e "${GREEN}[RUNTIME/os-container]${NC} $1"; }
print_error() { echo -e "${RED}[RUNTIME/os-container]${NC} $1"; }

OS_FAMILY="${1:-${RUNTIME_OS_FAMILY:-}}"
ARCH="$(runtime_arch_key)"
if [[ -n "${RUNTIME_ARCH:-}" ]]; then
  case "${RUNTIME_ARCH}" in
    arm64|aarch64) ARCH="arm64" ;;
    *) ARCH="x86_64" ;;
  esac
fi

if [[ -z "$OS_FAMILY" ]]; then
  print_error "用法: $0 <os_family>   例: openeuler22 ubuntu26 el9"
  print_error "或: bash RUNTIME/scripts/export_runtime_all.sh --all"
  exit 1
fi

IMAGE="$(runtime_matrix_image "$OS_FAMILY" "$ARCH")"
if [[ -z "$IMAGE" ]]; then
  if [[ "$OS_FAMILY" == kylin* ]]; then
    print_error "麒麟 RUNTIME 不能使用 openEuler 容器冒充，请设置专用镜像，例如:"
    print_error "  export RUNTIME_KYLIN10_ARM64_IMAGE=<kylin-v10-sp3-arm64-image>"
    print_error "  bash RUNTIME/scripts/export_runtime_os_container.sh $OS_FAMILY"
    print_error "或在实机麒麟上: bash RUNTIME/export_runtime_cpp.sh"
  else
    print_error "矩阵未登记 os_family=$OS_FAMILY arch=$ARCH，请设置 RUNTIME_OS_CONTAINER_IMAGE"
  fi
  print_error "已登记目标:"
  runtime_matrix_list | sed 's/^/  /'
  exit 1
fi

if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
  print_error "需要可用的 Docker"
  exit 1
fi

print_info "拉取/确保镜像: $IMAGE (platform=$(runtime_matrix_docker_platform "$ARCH"))"
docker pull "$IMAGE"

uid="$(id -u)"
gid="$(id -g)"
export TMPDIR="${TMPDIR:-$REPO/.tmp}"
CONDA_VOL="$REPO/.tmp/miniconda-${OS_FAMILY}-${ARCH}"
mkdir -p "$TMPDIR" "$ROOT/.bundle-runtime" "$CONDA_VOL"

print_info "在容器 ($IMAGE) 内编译 os_family=$OS_FAMILY arch=$ARCH ..."

docker_platform=()
if [[ "$ARCH" == "arm64" ]]; then
  docker_platform=(--platform "$(runtime_matrix_docker_platform arm64)")
fi

docker run --rm \
  "${docker_platform[@]}" \
  --runtime=runc \
  -e NVIDIA_VISIBLE_DEVICES= \
  -e RUNTIME_OS_FAMILY="$OS_FAMILY" \
  -e RUNTIME_ARCH="$ARCH" \
  -e RUNTIME_AUTO_INSTALL=1 \
  -e EASYAIOT_RUNTIME_BUILD_MODE=host \
  -e EASYAIOT_AUTO_INSTALL_DEPS=1 \
  -e ORT_ROOT=/opt/ort \
  -e ORT_VERSION="${ORT_VERSION:-1.23.2}" \
  -e MINICONDA_PREFIX=/opt/miniconda3 \
  -v "$REPO:/src:rw" \
  -v "$REPO/.deps/onnxruntime-linux-x64-${ORT_VERSION:-1.23.2}:/opt/ort:ro" \
  -v "$CONDA_VOL:/opt/miniconda3:rw" \
  -w /src/RUNTIME \
  "$IMAGE" \
  bash /src/RUNTIME/scripts/build_inside_os_container.sh

if [[ "$(id -u)" -ne 0 ]]; then
  docker run --rm --runtime=runc -e NVIDIA_VISIBLE_DEVICES= \
    -v "$REPO:/src:rw" \
    "$IMAGE" \
    chown -R "${uid}:${gid}" /src/RUNTIME/build /src/RUNTIME/.bundle-runtime /src/RUNTIME/deploy.env /src/RUNTIME/VERSION 2>/dev/null || true
fi

tar_path="$ROOT/.bundle-runtime/${OS_FAMILY}/${ARCH}/easyaiot-runtime-${OS_FAMILY}-${ARCH}.tar.gz"
if [[ ! -f "$tar_path" ]]; then
  print_error "未找到导出包: $tar_path"
  exit 1
fi

print_success "导出完成: $tar_path ($(du -h "$tar_path" | awk '{print $1}'))"
echo "RUNTIME_EXPORT_OK=$tar_path"
