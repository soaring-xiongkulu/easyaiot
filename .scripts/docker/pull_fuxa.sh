#!/bin/bash
# ---------------------------------------------------------------------------
# 拉取 FUXA 镜像（国内 DaoCloud 403 时的多源回退）
# 用法:
#   bash .scripts/docker/pull_fuxa.sh
#   DOCKER_MIRROR=https://<id>.mirror.swr.myhuaweicloud.com bash .scripts/docker/pull_fuxa.sh
#   FUXA_TAG=1.3.3 bash .scripts/docker/pull_fuxa.sh
#
# 华为云加速器（推荐）：
#   1. 登录华为云控制台 → 容器镜像服务 SWR → 镜像中心 → 镜像加速器
#   2. 复制加速器地址，例如 https://xxxx.mirror.swr.myhuaweicloud.com
#   3. export DOCKER_MIRROR=https://xxxx.mirror.swr.myhuaweicloud.com
#   4. 可选写入 daemon.json 后 systemctl restart docker
# ---------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=docker_mirror_common.sh
source "${SCRIPT_DIR}/docker_mirror_common.sh"

FUXA_TAG="${FUXA_TAG:-1.3.3}"
FUXA_IMAGE_LOCAL="${FUXA_IMAGE_LOCAL:-docker.1panel.live/frangoteam/fuxa:${FUXA_TAG}}"
# 同时打官方名标签，便于其它脚本按 frangoteam/fuxa 引用
FUXA_IMAGE_ALIAS="${FUXA_IMAGE_ALIAS:-frangoteam/fuxa:${FUXA_TAG}}"

print_info() { echo -e "\033[0;34m[INFO]\033[0m $1"; }
print_success() { echo -e "\033[0;32m[OK]\033[0m $1"; }
print_warning() { echo -e "\033[0;33m[WARN]\033[0m $1"; }
print_error() { echo -e "\033[0;31m[ERR]\033[0m $1" >&2; }

if ! command -v docker >/dev/null 2>&1; then
    print_error "未找到 docker 命令"
    exit 1
fi

print_info "目标镜像: ${FUXA_IMAGE_LOCAL}"
print_info "主镜像源: ${DOCKER_MIRROR}"
print_info "回退链: ${DOCKER_MIRROR_FALLBACKS}"

if docker_pull_with_mirror_fallback "${FUXA_IMAGE_LOCAL}"; then
    docker tag "${FUXA_IMAGE_LOCAL}" "${FUXA_IMAGE_ALIAS}" 2>/dev/null || true
    print_success "FUXA 镜像已就绪: ${FUXA_IMAGE_LOCAL}"
    print_info "别名标签: ${FUXA_IMAGE_ALIAS}"
    print_info "启动: cd ${SCRIPT_DIR} && docker compose up -d FUXA"
    exit 0
fi

print_error "所有镜像源均拉取失败"
echo ""
echo "可手动尝试（任选）："
echo "  docker pull docker.1panel.live/frangoteam/fuxa:${FUXA_TAG}"
echo "  docker pull docker.1ms.run/frangoteam/fuxa:${FUXA_TAG}"
echo "  cd ${SCRIPT_DIR} && docker compose up -d FUXA"
exit 1
