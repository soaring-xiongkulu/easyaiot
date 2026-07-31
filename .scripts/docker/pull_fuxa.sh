#!/bin/bash
# ---------------------------------------------------------------------------
# 拉取 FUXA 镜像（专用多源；与 Linux/compose 约定对齐）
#
# 要点：
#   - compose / 本地固定名: docker.1panel.live/frangoteam/fuxa:<tag>
#     （即使 1panel HEAD 403，也仍用此名作为最终 tag，供 docker-compose.yml 引用）
#   - 实际拉取优先 docker.1ms.run（国内较稳）；DaoCloud 对 frangoteam/fuxa 常 403，放最后
#   - 同时打官方短名标签 frangoteam/fuxa:<tag>
#
# 用法:
#   bash .scripts/docker/pull_fuxa.sh
#   FUXA_TAG=1.3.3 bash .scripts/docker/pull_fuxa.sh
#   FUXA_IMAGE_LOCAL=docker.1panel.live/frangoteam/fuxa:1.3.3 bash .scripts/docker/pull_fuxa.sh
# ---------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=docker_mirror_common.sh
source "${SCRIPT_DIR}/docker_mirror_common.sh"

FUXA_TAG="${FUXA_TAG:-1.3.3}"
# 与 docker-compose.yml 默认值保持一致（canonical 本地名）
FUXA_IMAGE_LOCAL="${FUXA_IMAGE_LOCAL:-docker.1panel.live/frangoteam/fuxa:${FUXA_TAG}}"
FUXA_IMAGE_ALIAS="${FUXA_IMAGE_ALIAS:-frangoteam/fuxa:${FUXA_TAG}}"

print_info() { echo -e "\033[0;34m[INFO]\033[0m $1"; }
print_success() { echo -e "\033[0;32m[OK]\033[0m $1"; }
print_warning() { echo -e "\033[0;33m[WARN]\033[0m $1"; }
print_error() { echo -e "\033[0;31m[ERR]\033[0m $1" >&2; }

if ! command -v docker >/dev/null 2>&1; then
    print_error "未找到 docker 命令"
    exit 1
fi

print_info "目标镜像(compose 名): ${FUXA_IMAGE_LOCAL}"
print_info "别名标签: ${FUXA_IMAGE_ALIAS}"

if docker image inspect "${FUXA_IMAGE_LOCAL}" >/dev/null 2>&1; then
    docker tag "${FUXA_IMAGE_LOCAL}" "${FUXA_IMAGE_ALIAS}" 2>/dev/null || true
    print_success "FUXA 镜像已存在: ${FUXA_IMAGE_LOCAL}"
    exit 0
fi

# 本地已有其它源同 tag，直接标记，避免再拉
for alt in \
    "docker.1ms.run/frangoteam/fuxa:${FUXA_TAG}" \
    "docker.1panel.live/frangoteam/fuxa:${FUXA_TAG}" \
    "docker.m.daocloud.io/frangoteam/fuxa:${FUXA_TAG}" \
    "frangoteam/fuxa:${FUXA_TAG}"
do
    if docker image inspect "$alt" >/dev/null 2>&1; then
        docker tag "$alt" "${FUXA_IMAGE_LOCAL}" 2>/dev/null || true
        docker tag "$alt" "${FUXA_IMAGE_ALIAS}" 2>/dev/null || true
        if docker image inspect "${FUXA_IMAGE_LOCAL}" >/dev/null 2>&1; then
            print_success "已用本地镜像 $alt 标记为 ${FUXA_IMAGE_LOCAL}"
            exit 0
        fi
    fi
done

export DOCKER_CONTENT_TRUST=0

# FUXA 专用回退：1ms 优先；DaoCloud 对 frangoteam 常 403，放后
# 覆盖通用 DOCKER_MIRROR_FALLBACKS，避免先撞 DaoCloud
FUXA_MIRROR_FALLBACKS="${FUXA_MIRROR_FALLBACKS:-docker.1ms.run,docker.1panel.live,docker.m.daocloud.io}"
print_info "FUXA 拉取回退链: ${FUXA_MIRROR_FALLBACKS}"

if DOCKER_MIRROR="https://docker.1ms.run" \
   DOCKER_MIRROR_FALLBACKS="${FUXA_MIRROR_FALLBACKS}" \
   docker_pull_with_mirror_fallback "${FUXA_IMAGE_LOCAL}"; then
    docker tag "${FUXA_IMAGE_LOCAL}" "${FUXA_IMAGE_ALIAS}" 2>/dev/null || true
    print_success "FUXA 镜像已就绪: ${FUXA_IMAGE_LOCAL}"
    print_info "别名标签: ${FUXA_IMAGE_ALIAS}"
    print_info "启动: cd ${SCRIPT_DIR} && docker compose up -d FUXA"
    exit 0
fi

# 再按显式候选直连一轮（与 start_fuxa_centos7.sh 对齐）
candidates=(
    "docker.1ms.run/frangoteam/fuxa:${FUXA_TAG}"
    "docker.1panel.live/frangoteam/fuxa:${FUXA_TAG}"
    "docker.m.daocloud.io/frangoteam/fuxa:${FUXA_TAG}"
    "frangoteam/fuxa:${FUXA_TAG}"
)

for src in "${candidates[@]}"; do
    print_info "尝试直连拉取: ${src}"
    if docker pull "$src"; then
        docker tag "$src" "${FUXA_IMAGE_LOCAL}" 2>/dev/null || true
        docker tag "$src" "${FUXA_IMAGE_ALIAS}" 2>/dev/null || true
        if docker image inspect "${FUXA_IMAGE_LOCAL}" >/dev/null 2>&1; then
            print_success "FUXA 镜像已就绪: ${FUXA_IMAGE_LOCAL} (来自 ${src})"
            exit 0
        fi
    fi
done

print_error "所有镜像源均拉取失败"
echo ""
echo "可手动尝试后 tag 回 compose 名："
echo "  docker pull docker.1ms.run/frangoteam/fuxa:${FUXA_TAG}"
echo "  docker tag docker.1ms.run/frangoteam/fuxa:${FUXA_TAG} ${FUXA_IMAGE_LOCAL}"
echo "  docker tag docker.1ms.run/frangoteam/fuxa:${FUXA_TAG} ${FUXA_IMAGE_ALIAS}"
echo "  cd ${SCRIPT_DIR} && docker compose up -d FUXA"
exit 1
