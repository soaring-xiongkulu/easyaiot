#!/usr/bin/env bash
# EasyAIoT HARNESS 安装/构建/启停
# 上级 .scripts/docker/install_*.sh 通过 install_linux.sh 委托本脚本
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "${ROOT}"

EASYAIOT_ROOT="$(cd "${ROOT}/.." && pwd)"
# shellcheck source=../.scripts/docker/deploy_profile.sh
source "${EASYAIOT_ROOT}/.scripts/docker/deploy_profile.sh" 2>/dev/null || true

cmd="${1:-help}"

ensure_env_file() {
  if [[ ! -f "${ROOT}/harness.env" ]]; then
    cp "${ROOT}/harness.env.example" "${ROOT}/harness.env"
    echo "[harness] 已生成 ${ROOT}/harness.env"
  fi
}

set_harness_env_var() {
  local key="$1"
  local val="$2"
  local file="${ROOT}/harness.env"
  ensure_env_file
  if grep -q "^${key}=" "${file}"; then
    sed -i "s|^${key}=.*|${key}=${val}|" "${file}"
  else
    echo "${key}=${val}" >> "${file}"
  fi
}

prompt_deepseek_api_key() {
  if [[ "${EASYAIOT_SKIP_HARNESS_KEY_PROMPT:-0}" = "1" ]]; then
    return 0
  fi
  if [[ ! -t 0 ]]; then
    echo "[harness] 非交互环境，跳过 DeepSeek Key 输入（可在 Web UI Settings → Models 中配置）"
    return 0
  fi

  load_env
  if [[ -n "${DEEPSEEK_API_KEY:-}" ]]; then
    echo "[harness] harness.env 已有 DEEPSEEK_API_KEY，跳过输入（可在 Web UI Settings → Models 修改）"
    return 0
  fi

  echo ""
  echo "[harness] AI 助手需 DeepSeek API Key 才能对话；也可跳过，稍后在 Web UI 配置。"
  echo "[harness] 注册 / 充值：https://platform.deepseek.com/"
  read -r -p "请输入 DeepSeek API Key [回车跳过]: " _ds_key || _ds_key=""
  _ds_key="$(echo "${_ds_key}" | xargs)"
  if [[ -z "${_ds_key}" ]]; then
    echo "[harness] 已跳过 — 打开 :3080 → Settings → Models 填写 Key 即可"
    echo "[harness] 获取 Key：https://platform.deepseek.com/"
    return 0
  fi

  set_harness_env_var DEEPSEEK_API_KEY "${_ds_key}"
  export DEEPSEEK_API_KEY="${_ds_key}"
  echo "[harness] 已写入 harness.env（Web UI 中可随时修改，重启不会覆盖 UI 中的 Key）"
}

load_env() {
  ensure_env_file
  if [[ -f "${ROOT}/harness.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "${ROOT}/harness.env"
    set +a
  fi
}

ensure_host_paths() {
  load_env
  if [[ -z "${HARNESS_WORKSPACE_HOST:-}" ]]; then
    export HARNESS_WORKSPACE_HOST="${EASYAIOT_ROOT}"
    set_harness_env_var HARNESS_WORKSPACE_HOST "${EASYAIOT_ROOT}"
    echo "[harness] HARNESS_WORKSPACE_HOST -> ${EASYAIOT_ROOT}"
  fi
  mkdir -p "${ROOT}/.data"
}

compose() {
  ensure_host_paths
  if [[ -f "${ROOT}/harness.env" ]]; then
    docker compose -f "${ROOT}/docker-compose.yml" --env-file "${ROOT}/harness.env" "$@"
  else
    docker compose -f "${ROOT}/docker-compose.yml" "$@"
  fi
}

image_exists() {
  docker image inspect "${HARNESS_IMAGE:-easyaiot/harness:latest}" >/dev/null 2>&1
}

usage() {
  cat <<'EOF'
用法: bash HARNESS/install.sh <command>

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
  cp HARNESS/harness.env.example HARNESS/harness.env
  bash HARNESS/install.sh install
EOF
}

do_build() {
  load_env
  echo "[harness] building ${HARNESS_IMAGE:-easyaiot/harness:latest} (dsh ${DSH_VERSION:-0.1.0-rc.6})"
  local -a build_args=(
    -f "${ROOT}/Dockerfile"
    -t "${HARNESS_IMAGE:-easyaiot/harness:latest}"
    --build-arg "DSH_VERSION=${DSH_VERSION:-0.1.0-rc.6}"
    --build-arg "HARNESS_SIDEBAR_PACKAGE=${HARNESS_SIDEBAR_PACKAGE:-dsh-better-sidebar@0.12.1}"
  )
  if [[ -n "${DOCKER_PLATFORM:-}" ]]; then
    build_args+=(--platform "${DOCKER_PLATFORM}")
  fi
  docker build "${build_args[@]}" "${ROOT}"
}

do_install() {
  load_env
  prompt_deepseek_api_key
  load_env
  if [[ "${EASYAIOT_SKIP_BUILD:-0}" = "1" ]] && image_exists; then
    echo "[harness] 镜像已存在且 EASYAIOT_SKIP_BUILD=1，跳过构建"
  else
    do_build
  fi
  compose up -d
  echo "[harness] Web UI: http://127.0.0.1:${HARNESS_LISTEN_PORT:-3080}"
  echo "[harness] workspace: ${HARNESS_WORKSPACE_HOST}"
}

show_status() {
  load_env
  local port="${HARNESS_LISTEN_PORT:-3080}"
  echo "[harness] container:"
  compose ps 2>/dev/null || true
  echo "[harness] HTTP check:"
  curl -sS -o /dev/null -w "HTTP %{http_code}\n" "http://127.0.0.1:${port}/" 2>/dev/null || echo "unreachable"
}

case "${cmd}" in
  install) do_install ;;
  build) do_build ;;
  start)
    load_env
    if ! image_exists; then
      echo "[harness] 镜像不存在，先构建..."
      do_build
    fi
    compose up -d
    echo "[harness] Web UI: http://127.0.0.1:${HARNESS_LISTEN_PORT:-3080}"
    ;;
  stop|clean) compose down ;;
  restart)
    bash "${ROOT}/install.sh" stop
    bash "${ROOT}/install.sh" start
    ;;
  update|rebuild)
    load_env
    if [[ "${EASYAIOT_SKIP_BUILD:-0}" = "1" ]] && image_exists; then
      echo "[harness] 预构建镜像已就绪（EASYAIOT_SKIP_BUILD=1），跳过构建，仅 recreate"
    elif ! command -v git >/dev/null 2>&1 && image_exists; then
      echo "[harness] 未检测到 git，使用本地镜像 recreate（不构建）"
    else
      do_build
    fi
    compose up -d --force-recreate
    echo "[harness] Web UI: http://127.0.0.1:${HARNESS_LISTEN_PORT:-3080}"
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
