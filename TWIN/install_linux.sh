#!/bin/bash
# EasyAIoT TWIN 数字孪生模块管理脚本（仅 full / 含可视化形态启用）
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROFILE_SCRIPT="${PROJECT_ROOT}/.scripts/docker/deploy_profile.sh"
[ -f "$PROFILE_SCRIPT" ] && source "$PROFILE_SCRIPT"

if type apply_deploy_profile >/dev/null 2>&1; then
  apply_deploy_profile
fi

if type module_enabled_for_deploy_profile >/dev/null 2>&1 && ! module_enabled_for_deploy_profile TWIN; then
  echo "[INFO] 跳过 TWIN：当前部署形态 ${EASYAIOT_DEPLOY_PROFILE:-full} 不包含可视化能力"
  exit 0
fi

cd "$SCRIPT_DIR"
COMPOSE=(docker compose -f docker-compose.yml)
IMAGE="easyaiot-twin:latest"
SERVICE="twin-service"
COMMAND="${1:-install}"

ensure_network() {
  docker network inspect easyaiot-network >/dev/null 2>&1 || docker network create easyaiot-network >/dev/null
}

pull_prebuilt() {
  [ "${EASYAIOT_SKIP_BUILD:-0}" = "1" ] || return 1
  local arch remote registry
  case "$(uname -m)" in x86_64|amd64) arch=amd64;; aarch64|arm64) arch=arm64;; *) arch=amd64;; esac
  registry="${EASYAIOT_RUNTIME_REGISTRY:-docker.cnb.cool/holmesian/easyaiot/}"
  remote="${registry%/}/aiot-twin:${arch}"
  echo "[INFO] 拉取 TWIN 预构建镜像: $remote"
  docker pull "$remote" && docker tag "$remote" "$IMAGE"
}

build_image() {
  if docker image inspect "$IMAGE" >/dev/null 2>&1 && [ "${EASYAIOT_SKIP_BUILD:-0}" = "1" ]; then
    echo "[INFO] 复用预构建镜像: $IMAGE"
    return 0
  fi
  pull_prebuilt && return 0
  echo "[INFO] 构建 TWIN 数字孪生镜像"
  local -a build_args=()
  [ -n "${DOCKER_PLATFORM:-}" ] && build_args+=(--platform "$DOCKER_PLATFORM")
  docker build "${build_args[@]}" -t "$IMAGE" .
}

case "$COMMAND" in
  install)
    ensure_network
    build_image
    "${COMPOSE[@]}" up -d --no-build
    ;;
  start)
    ensure_network
    "${COMPOSE[@]}" up -d --no-build
    ;;
  stop) "${COMPOSE[@]}" down ;;
  restart)
    ensure_network
    "${COMPOSE[@]}" down
    "${COMPOSE[@]}" up -d --no-build
    ;;
  build) build_image ;;
  update)
    ensure_network
    build_image
    "${COMPOSE[@]}" up -d --no-build --force-recreate
    ;;
  status) docker ps -a --filter "name=^/${SERVICE}$" --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' ;;
  logs) "${COMPOSE[@]}" logs -f --tail=200 "$SERVICE" ;;
  clean)
    "${COMPOSE[@]}" down --remove-orphans
    docker image rm "$IMAGE" 2>/dev/null || true
    ;;
  *)
    echo "用法: $0 {install|start|stop|restart|build|update|status|logs|clean}"
    exit 1
    ;;
esac
