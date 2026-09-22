#!/usr/bin/env bash
# EasyAIoT TERMINAL 安装/构建/启停（Wails v3 server 模式容器，多协议终端）
# 上级 .scripts/docker/install_*.sh 通过 install_linux.sh 委托本脚本
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "${ROOT}"

EASYAIOT_ROOT="$(cd "${ROOT}/.." && pwd)"
# shellcheck source=../.scripts/docker/deploy_profile.sh
source "${EASYAIOT_ROOT}/.scripts/docker/deploy_profile.sh" 2>/dev/null || true

cmd="${1:-help}"

ensure_env_file() {
  if [[ ! -f "${ROOT}/terminal.env" && -f "${ROOT}/terminal.env.example" ]]; then
    cp "${ROOT}/terminal.env.example" "${ROOT}/terminal.env"
    echo "[terminal] 已生成 ${ROOT}/terminal.env"
  fi
}

load_env() {
  ensure_env_file
  if [[ -f "${ROOT}/terminal.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "${ROOT}/terminal.env"
    set +a
  fi
}

compose() {
  load_env
  if [[ -f "${ROOT}/terminal.env" ]]; then
    docker compose -f "${ROOT}/docker-compose.yml" --env-file "${ROOT}/terminal.env" "$@"
  else
    docker compose -f "${ROOT}/docker-compose.yml" "$@"
  fi
}

image_exists() {
  docker image inspect "${TERMINAL_IMAGE:-easyaiot/terminal:latest}" >/dev/null 2>&1
}

do_build() {
  load_env
  echo "[terminal] building ${TERMINAL_IMAGE:-easyaiot/terminal:latest}（server 模式，多阶段自包含构建）"
  local -a build_args=(
    -f "${ROOT}/build/docker/Dockerfile.server"
    -t "${TERMINAL_IMAGE:-easyaiot/terminal:latest}"
  )
  if [[ -n "${DOCKER_PLATFORM:-}" ]]; then
    build_args+=(--platform "${DOCKER_PLATFORM}")
  fi
  docker build "${build_args[@]}" "${ROOT}"
}

usage() {
  cat <<'EOF'
用法: bash TERMINAL/install.sh <command>

  install           构建镜像并启动（统一部署入口）
  build             构建 Docker 镜像
  start             启动服务
  stop / clean      停止并移除容器
  restart           重启
  update / rebuild  重建镜像并重启
  logs              查看日志
  status            健康检查
  help              显示帮助

示例:
  bash TERMINAL/install.sh install
EOF
}

do_install() {
  load_env
  if [[ "${EASYAIOT_SKIP_BUILD:-0}" = "1" ]] && image_exists; then
    echo "[terminal] 镜像已存在且 EASYAIOT_SKIP_BUILD=1，跳过构建"
  else
    do_build
  fi
  compose up -d
  echo "[terminal] Web UI: http://127.0.0.1:${TERMINAL_LISTEN_PORT:-9245}"
}

show_status() {
  load_env
  local port="${TERMINAL_LISTEN_PORT:-9245}"
  echo "[terminal] container:"
  compose ps 2>/dev/null || true
  echo "[terminal] HTTP check:"
  curl -sS -o /dev/null -w "HTTP %{http_code}\n" "http://127.0.0.1:${port}/" 2>/dev/null || echo "unreachable"
}

case "${cmd}" in
  install) do_install ;;
  build) do_build ;;
  start)
    load_env
    if ! image_exists; then
      echo "[terminal] 镜像不存在，先构建..."
      do_build
    fi
    compose up -d
    echo "[terminal] Web UI: http://127.0.0.1:${TERMINAL_LISTEN_PORT:-9245}"
    ;;
  stop|clean) compose down ;;
  restart)
    bash "${ROOT}/install.sh" stop
    bash "${ROOT}/install.sh" start
    ;;
  update|rebuild)
    load_env
    if [[ "${EASYAIOT_SKIP_BUILD:-0}" = "1" ]] && image_exists; then
      echo "[terminal] 预构建镜像已就绪（EASYAIOT_SKIP_BUILD=1），跳过构建，仅 recreate"
    elif ! command -v git >/dev/null 2>&1 && image_exists; then
      echo "[terminal] 未检测到 git，使用本地镜像 recreate（不构建）"
    else
      do_build
    fi
    compose up -d --force-recreate
    echo "[terminal] Web UI: http://127.0.0.1:${TERMINAL_LISTEN_PORT:-9245}"
    ;;
  logs) compose logs -f --tail=200 ;;
  status) show_status ;;
  help|--help|-h) usage ;;
  *)
    echo "unknown command: ${cmd}" >&2
    usage
    exit 1
    ;;
esac
