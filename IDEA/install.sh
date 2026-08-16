#!/usr/bin/env bash
# EasyAIoT IDEA 安装/构建/启停
# 上级 .scripts/docker/install_*.sh 通过 install_linux.sh 委托本脚本（install/start/stop/...）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "${ROOT}"

cmd="${1:-help}"

ensure_env_file() {
  if [[ ! -f "${ROOT}/idea.env" ]]; then
    cp "${ROOT}/idea.env.example" "${ROOT}/idea.env"
    echo "[idea] 已生成 ${ROOT}/idea.env"
  fi
  # 旧模板未给含空格的 scope 加引号，source 会报 user:email: command not found
  if grep -q '^IDEA_GITHUB_SCOPE=read:user user:email$' "${ROOT}/idea.env" 2>/dev/null; then
    sed -i 's/^IDEA_GITHUB_SCOPE=read:user user:email$/IDEA_GITHUB_SCOPE="read:user user:email"/' "${ROOT}/idea.env"
    echo "[idea] 已修复 idea.env 中 IDEA_GITHUB_SCOPE 引号"
  fi
}

load_env() {
  ensure_env_file
  if [[ -f "${ROOT}/idea.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "${ROOT}/idea.env"
    set +a
  fi
}

portal_image() {
  echo "${IDEA_PORTAL_IMAGE:-easyaiot/idea-portal:latest}"
}

workspace_image() {
  echo "${IDEA_WORKSPACE_IMAGE:-easyaiot/idea-workspace:latest}"
}

image_exists() {
  docker image inspect "$1" >/dev/null 2>&1
}

images_ready() {
  image_exists "$(portal_image)" && image_exists "$(workspace_image)"
}

ensure_host_paths() {
  load_env
  mkdir -p "${ROOT}/.data/workspaces" "${ROOT}/.data/git-reference"
  if [[ -z "${IDEA_DATA_DIR_HOST:-}" ]]; then
    export IDEA_DATA_DIR_HOST="${ROOT}/.data/workspaces"
  fi
  if [[ -z "${IDEA_HOST_PROJECT_ROOT:-}" ]]; then
    export IDEA_HOST_PROJECT_ROOT="$(cd "${ROOT}/.." && pwd)"
  fi
  if [[ -z "${IDEA_GIT_REFERENCE_DIR:-}" ]]; then
    export IDEA_GIT_REFERENCE_DIR="${ROOT}/.data/git-reference"
  fi
  mkdir -p "${IDEA_DATA_DIR_HOST}" "${IDEA_GIT_REFERENCE_DIR}"
}

compose() {
  ensure_host_paths
  if [[ -f "${ROOT}/idea.env" ]]; then
    docker compose -f "${ROOT}/docker-compose.yml" --env-file "${ROOT}/idea.env" "$@"
  else
    docker compose -f "${ROOT}/docker-compose.yml" "$@"
  fi
}

api_headers() {
  HDR=(-H 'Content-Type: application/json')
  if [[ -n "${IDEA_TOKEN:-}" ]]; then
    HDR+=(-H "X-IDEA-Token: ${IDEA_TOKEN}")
  fi
}

usage() {
  cat <<'EOF'
用法: bash IDEA/install.sh <command>

  install           一键安装（构建镜像并启动；供上级 install_*.sh 委托）
  build-workspace   构建贡献者 code-server 镜像
  build-portal      构建 IDEA 门户镜像
  build             构建全部镜像
  start             启动门户 (docker compose)
  stop / clean      停止门户
  restart           重启门户
  update / rebuild  重建镜像并重启
  logs              查看门户日志
  status            健康检查 + 容量统计
  prepare-ref       准备 git reference 仓（加速全仓 clone）
  create-demo       调用 API 创建一个演示工作区
  reap-idle         立即执行一次闲置回收
  dev               本机 Python 直接跑门户（需已 pip install -r requirements.txt）
  help              显示帮助

示例:
  cp IDEA/idea.env.example IDEA/idea.env
  bash IDEA/install.sh install
  bash IDEA/install.sh build
  bash IDEA/install.sh start
  bash IDEA/install.sh create-demo
EOF
}

do_install() {
  load_env
  if [[ "${EASYAIOT_SKIP_BUILD:-0}" = "1" ]] && images_ready; then
    echo "[idea] 镜像已存在且 EASYAIOT_SKIP_BUILD=1，跳过构建"
  else
    build_workspace
    build_portal
  fi
  compose up -d
  echo "[idea] portal: http://127.0.0.1:${IDEA_LISTEN_PORT:-9300}"
  echo "[idea] data host dir: ${IDEA_DATA_DIR_HOST}"
}

do_update() {
  load_env
  if [[ "${EASYAIOT_SKIP_BUILD:-0}" = "1" ]] && images_ready; then
    echo "[idea] 预构建镜像已就绪（EASYAIOT_SKIP_BUILD=1），跳过构建，仅 recreate"
  elif [[ "${EASYAIOT_SKIP_BUILD:-0}" = "1" ]]; then
    echo "[idea] EASYAIOT_SKIP_BUILD=1 但本地镜像不完整，请先 pull；本次将尝试构建补齐" >&2
    build_workspace
    build_portal
  elif ! command -v git >/dev/null 2>&1 && images_ready; then
    echo "[idea] 未检测到 git，使用本地镜像 recreate（不构建）"
  else
    build_workspace
    build_portal
  fi
  compose up -d --force-recreate
  echo "[idea] portal: http://127.0.0.1:${IDEA_LISTEN_PORT:-9300}"
}

build_workspace() {
  load_env
  local image="${IDEA_WORKSPACE_IMAGE:-easyaiot/idea-workspace:latest}"
  echo "[idea] building workspace image: ${image}"
  local -a build_args=(-f "${ROOT}/image/Dockerfile" -t "${image}")
  if [[ -n "${DOCKER_PLATFORM:-}" ]]; then
    echo "[idea] 跨架构构建: --platform ${DOCKER_PLATFORM}"
    build_args+=(--platform "${DOCKER_PLATFORM}")
  fi
  docker build "${build_args[@]}" "${ROOT}"
}

build_portal() {
  load_env
  local image="${IDEA_PORTAL_IMAGE:-easyaiot/idea-portal:latest}"
  echo "[idea] building portal image: ${image}"
  local -a build_args=(-f "${ROOT}/Dockerfile" -t "${image}")
  if [[ -n "${DOCKER_PLATFORM:-}" ]]; then
    echo "[idea] 跨架构构建: --platform ${DOCKER_PLATFORM}"
    build_args+=(--platform "${DOCKER_PLATFORM}")
  fi
  docker build "${build_args[@]}" "${ROOT}"
}

prepare_ref() {
  load_env
  local url="${IDEA_GIT_URL:-https://gitee.com/volara/easyaiot.git}"
  local ref_dir="${ROOT}/.data/git-reference/easyaiot.git"
  mkdir -p "$(dirname "${ref_dir}")"
  if [[ -d "${ref_dir}" ]]; then
    echo "[idea] updating reference ${ref_dir}"
    git --git-dir="${ref_dir}" fetch --all --prune
  else
    echo "[idea] cloning bare reference from ${url}"
    git clone --bare "${url}" "${ref_dir}"
  fi
  echo "[idea] set in idea.env:"
  echo "       IDEA_GIT_REFERENCE=/opt/git-reference/easyaiot.git"
  echo "       IDEA_GIT_REFERENCE_HOST=${ref_dir}"
  echo "       IDEA_GIT_REFERENCE_DIR=$(dirname "${ref_dir}")"
}

create_demo() {
  load_env
  local port="${IDEA_LISTEN_PORT:-9300}"
  local user="${2:-demo}"
  api_headers
  echo "[idea] creating workspace for user=${user}"
  curl -sS -X POST "http://127.0.0.1:${port}/api/workspaces" \
    "${HDR[@]}" \
    -d "{\"user\":\"${user}\"}" | tee /tmp/idea-create.json
  echo
}

show_status() {
  load_env
  local port="${IDEA_LISTEN_PORT:-9300}"
  api_headers
  echo "[idea] health:"
  curl -sS "http://127.0.0.1:${port}/health" || true
  echo
  echo "[idea] stats:"
  curl -sS "http://127.0.0.1:${port}/api/stats" "${HDR[@]}" || true
  echo
}

reap_idle() {
  load_env
  local port="${IDEA_LISTEN_PORT:-9300}"
  api_headers
  curl -sS -X POST "http://127.0.0.1:${port}/api/reap-idle" "${HDR[@]}"
  echo
}

run_dev() {
  load_env
  if [[ -z "${IDEA_DATA_DIR_HOST:-}" ]]; then
    export IDEA_DATA_DIR_HOST="${ROOT}/.data/workspaces"
  fi
  export IDEA_DATA_DIR="${IDEA_DATA_DIR_HOST}"
  if [[ -z "${IDEA_HOST_PROJECT_ROOT:-}" ]]; then
    export IDEA_HOST_PROJECT_ROOT="$(cd "${ROOT}/.." && pwd)"
  fi
  mkdir -p "${IDEA_DATA_DIR_HOST}"
  if [[ ! -d "${ROOT}/.venv" ]]; then
    python3 -m venv "${ROOT}/.venv"
    # shellcheck disable=SC1091
    source "${ROOT}/.venv/bin/activate"
    pip install -r "${ROOT}/requirements.txt"
  else
    # shellcheck disable=SC1091
    source "${ROOT}/.venv/bin/activate"
  fi
  echo "[idea] dev portal on :${IDEA_LISTEN_PORT:-9300} (data=${IDEA_DATA_DIR_HOST})"
  exec python "${ROOT}/run_idea.py"
}

case "${cmd}" in
  install) do_install ;;
  build-workspace) build_workspace ;;
  build-portal) build_portal ;;
  build) build_workspace; build_portal ;;
  start)
    load_env
    if ! images_ready; then
      echo "[idea] 镜像不完整，先构建..."
      build_workspace
      build_portal
    fi
    compose up -d
    echo "[idea] portal: http://127.0.0.1:${IDEA_LISTEN_PORT:-9300}"
    echo "[idea] data host dir: ${IDEA_DATA_DIR_HOST}"
    ;;
  stop|clean)
    compose down
    ;;
  restart)
    bash "${ROOT}/install.sh" stop
    bash "${ROOT}/install.sh" start
    ;;
  update|rebuild) do_update ;;
  logs)
    compose logs -f --tail=200
    ;;
  status) show_status ;;
  prepare-ref) prepare_ref ;;
  create-demo) create_demo "$@" ;;
  reap-idle) reap_idle ;;
  dev) run_dev ;;
  help|--help|-h) usage ;;
  *)
    echo "unknown command: ${cmd}" >&2
    usage
    exit 1
    ;;
esac
