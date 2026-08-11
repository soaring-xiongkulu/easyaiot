#!/usr/bin/env bash
# 以当前用户重建 SRS 容器，使 NFS 媒体根与宿主机 VIDEO/算法进程一致。
#
# 背景：若以 root/sudo 启动过 SRS，compose 卷可能挂到 /root/...，
# 而 VIDEO 在普通用户下读的是 $HOME/easyaiot/media，导致 DVR 录像路径对不上。
# 本脚本会删除旧容器并以当前用户重新创建（仅 restart 无法更换 volume 挂载）。
#
# 用法（在 VIDEO 目录或任意路径）：
#   ./fix_srs.sh
#   bash fix_srs.sh
set -euo pipefail

VIDEO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$(cd "${VIDEO_DIR}/../.scripts/docker" && pwd)"
COMPOSE_FILE="${COMPOSE_DIR}/docker-compose.yml"
CONTAINER_NAME="${SRS_CONTAINER_NAME:-srs-server}"
COMPOSE_SERVICE="${SRS_COMPOSE_SERVICE:-SRS}"
HOST_DATA_DIR="${EASYAIOT_MEDIA_ROOT:-${HOME}/easyaiot/media}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
ok() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err() { echo -e "${RED}[ERROR]${NC} $1"; }

if ! docker info &>/dev/null; then
    err "Docker 不可用，请确认 daemon 已启动且当前用户有权限访问"
    exit 1
fi

if [[ ! -f "${COMPOSE_FILE}" ]]; then
    err "未找到 compose 文件: ${COMPOSE_FILE}"
    exit 1
fi

if command -v docker-compose &>/dev/null; then
    COMPOSE_CMD=(docker-compose -f "${COMPOSE_FILE}")
else
    COMPOSE_CMD=(docker compose -f "${COMPOSE_FILE}")
fi

mkdir -p "${HOST_DATA_DIR}/playbacks"
chmod 777 "${HOST_DATA_DIR}" "${HOST_DATA_DIR}/playbacks" 2>/dev/null || true

info "当前用户: $(whoami)  数据目录: ${HOST_DATA_DIR}"

if docker inspect "${CONTAINER_NAME}" &>/dev/null; then
    info "停止并删除旧容器 ${CONTAINER_NAME} ..."
    docker stop "${CONTAINER_NAME}" >/dev/null 2>&1 || true
    docker rm "${CONTAINER_NAME}" >/dev/null 2>&1 || true
else
    warn "未找到容器 ${CONTAINER_NAME}，将直接创建"
fi

info "以当前用户重建 SRS (${COMPOSE_SERVICE}) ..."
(
    cd "${COMPOSE_DIR}"
    "${COMPOSE_CMD[@]}" up -d --force-recreate --no-deps "${COMPOSE_SERVICE}"
)

ok "SRS 已重建，录像目录应与 VIDEO 一致: ${HOST_DATA_DIR}/playbacks"
