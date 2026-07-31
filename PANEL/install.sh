#!/usr/bin/env bash
# EasyAIoT PANEL：构建独立前端镜像并启动容器（与 WEB 完全解耦）
#
# 用法:
#   bash PANEL/install.sh build    # 构建 easyaiot/panel 镜像（含 UI）
#   bash PANEL/install.sh start    # 构建（若无镜像）并启动容器
#   bash PANEL/install.sh stop|restart|status|logs|rebuild
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$SCRIPT_DIR"

PANEL_IMAGE="${PANEL_IMAGE:-easyaiot/panel:latest}"
PANEL_NAME="${PANEL_NAME:-easyaiot-panel}"
PANEL_PORT="${PANEL_LISTEN_PORT:-9200}"
PANEL_ENV="${PANEL_ENV_FILE:-${SCRIPT_DIR}/panel.env}"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"

if [ ! -f "$PANEL_ENV" ]; then
  cp "${SCRIPT_DIR}/panel.env.example" "$PANEL_ENV"
  echo "[PANEL] 已生成 $PANEL_ENV"
fi

# shellcheck disable=SC1090
set -a
# shellcheck source=/dev/null
source "$PANEL_ENV" 2>/dev/null || true
set +a

export EASYAIOT_ROOT="${EASYAIOT_ROOT:-$PROJECT_ROOT}"
export PANEL_IMAGE
export PANEL_LISTEN_PORT="${PANEL_LISTEN_PORT:-$PANEL_PORT}"
export PANEL_TOKEN="${PANEL_TOKEN:-}"
export PANEL_ALLOW_DANGEROUS="${PANEL_ALLOW_DANGEROUS:-1}"

cmd="${1:-start}"

need_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "[PANEL] 需要 Docker" >&2
    exit 1
  fi
}

compose() {
  if docker compose version >/dev/null 2>&1; then
    docker compose -f "$COMPOSE_FILE" "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f "$COMPOSE_FILE" "$@"
  else
    echo "[PANEL] 需要 docker compose" >&2
    exit 1
  fi
}

stop_legacy_host_process() {
  # 兼容早期 nohup 宿主机进程
  local pid_file="${SCRIPT_DIR}/.panel.pid"
  if [ -f "$pid_file" ]; then
    local pid
    pid="$(cat "$pid_file" 2>/dev/null || true)"
    if [ -n "${pid:-}" ] && kill -0 "$pid" 2>/dev/null; then
      echo "[PANEL] 停止旧版宿主机进程 pid=$pid"
      kill "$pid" 2>/dev/null || true
      sleep 1
      kill -9 "$pid" 2>/dev/null || true
    fi
    rm -f "$pid_file"
  fi

  # COMPILE 打包安装的 systemd 宿主机服务也会占用 PANEL_LISTEN_PORT（默认 9200）
  if command -v systemctl >/dev/null 2>&1; then
    if systemctl is-active --quiet easyaiot-panel.service 2>/dev/null \
      || systemctl is-enabled --quiet easyaiot-panel.service 2>/dev/null; then
      echo "[PANEL] 停止宿主机 systemd 服务 easyaiot-panel（释放 :${PANEL_LISTEN_PORT}）"
      systemctl stop easyaiot-panel.service 2>/dev/null || true
      systemctl disable easyaiot-panel.service 2>/dev/null || true
    fi
  fi

  # 兜底：仍占用端口的 /opt/easyaiot-panel 或同名二进制
  local port="${PANEL_LISTEN_PORT:-9200}"
  local pids
  pids="$(ss -tlnp 2>/dev/null | awk -v p=":${port}" '$4 ~ p"$" {print}' | grep -oE 'pid=[0-9]+' | cut -d= -f2 | sort -u || true)"
  if [ -z "$pids" ]; then
    pids="$(fuser "${port}/tcp" 2>/dev/null | tr ' ' '\n' | grep -E '^[0-9]+$' || true)"
  fi
  local pid cmd
  for pid in $pids; do
    cmd="$(ps -p "$pid" -o args= 2>/dev/null || true)"
    case "$cmd" in
      *easyaiot-panel*|*PANEL*panel*)
        echo "[PANEL] 停止占用 :${port} 的宿主机进程 pid=$pid ($cmd)"
        kill "$pid" 2>/dev/null || true
        sleep 1
        kill -9 "$pid" 2>/dev/null || true
        ;;
    esac
  done
}

image_exists() {
  docker image inspect "$PANEL_IMAGE" >/dev/null 2>&1
}

do_build() {
  need_docker
  echo "[PANEL] 构建镜像 $PANEL_IMAGE （含独立前端 UI）..."
  local -a build_args=(-t "$PANEL_IMAGE" -f "${SCRIPT_DIR}/Dockerfile")
  if [ -n "${DOCKER_PLATFORM:-}" ]; then
    echo "[PANEL] 跨架构构建: --platform ${DOCKER_PLATFORM}"
    build_args+=(--platform "$DOCKER_PLATFORM")
  fi
  docker build "${build_args[@]}" "$SCRIPT_DIR"
  echo "[PANEL] 镜像构建完成: $PANEL_IMAGE"
}

do_start() {
  need_docker
  stop_legacy_host_process
  if ! image_exists; then
    do_build
  fi
  echo "[PANEL] 启动容器 $PANEL_NAME （UI+API → :${PANEL_LISTEN_PORT}）"
  compose up -d --remove-orphans
  sleep 2
  do_status
  echo "[PANEL] 打开浏览器访问: http://127.0.0.1:${PANEL_LISTEN_PORT}/"
}

do_stop() {
  need_docker
  stop_legacy_host_process
  compose down --remove-orphans 2>/dev/null || docker rm -f "$PANEL_NAME" 2>/dev/null || true
  echo "[PANEL] 已停止"
}

do_restart() {
  do_stop
  do_start
}

do_rebuild() {
  need_docker
  stop_legacy_host_process
  compose down --remove-orphans 2>/dev/null || true
  do_build
  compose up -d --force-recreate --remove-orphans
  sleep 2
  do_status
  echo "[PANEL] 重建完成 → http://127.0.0.1:${PANEL_LISTEN_PORT}/"
}

do_status() {
  need_docker
  if docker ps --format '{{.Names}}' | grep -qx "$PANEL_NAME"; then
    echo "[PANEL] running container=$PANEL_NAME port=${PANEL_LISTEN_PORT}"
    curl -sf "http://127.0.0.1:${PANEL_LISTEN_PORT}/health" || true
    echo
  else
    echo "[PANEL] stopped"
    docker ps -a --filter "name=^/${PANEL_NAME}$" --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null || true
  fi
}

do_logs() {
  need_docker
  docker logs ${2:-} "$PANEL_NAME"
}

case "$cmd" in
  build) do_build ;;
  # install / update / clean：供上级 install_*.sh 统一管理命令委托
  install|start) do_start ;;
  stop|clean) do_stop ;;
  restart) do_restart ;;
  update|rebuild) do_rebuild ;;
  status) do_status ;;
  logs) shift; do_logs "$@" ;;
  *)
    echo "用法: $0 {install|build|start|stop|restart|rebuild|update|clean|status|logs}"
    exit 1
    ;;
esac
