#!/usr/bin/env bash
# 在 Ubuntu/glibc 目标上编译 PANEL 为单文件可执行程序，并可打 .deb
#
# 用法（也可经 COMPILE/build.sh 调用）:
#   bash COMPILE/platforms/ubuntu/build.sh
#   bash COMPILE/platforms/ubuntu/build.sh --local
#   bash COMPILE/platforms/ubuntu/build.sh --deb
#   bash COMPILE/platforms/ubuntu/build.sh --docker --deb
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPILE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REPO_ROOT="$(cd "${COMPILE_ROOT}/.." && pwd)"
OUT_VARIANT=""
DOCKER_PLATFORM="linux/amd64"
DEB_VARIANT="ubuntu"   # ubuntu|arm|kylin
DEB_ARCH_OVERRIDE=""

OUT_DIR="${COMPILE_OUT:-${COMPILE_ROOT}/dist/ubuntu}"
IMAGE_TAG="${COMPILE_IMAGE:-easyaiot/compile-panel-ubuntu:latest}"

MODE="docker"
DO_DEB=0
ARGS=("$@")
if [ "${#ARGS[@]}" -eq 0 ]; then
  ARGS=(--docker)
fi

for arg in "${ARGS[@]}"; do
  case "$arg" in
    docker|--docker) MODE="docker" ;;
    --local|local) MODE="local" ;;
    --deb|deb|package|--package) DO_DEB=1 ;;
    --arm|arm|arm64|aarch64) 
      DEB_VARIANT="arm"
      DOCKER_PLATFORM="linux/arm64"
      OUT_VARIANT="-arm"
      DEB_ARCH_OVERRIDE="arm64"
      OUT_DIR="${COMPILE_OUT:-${COMPILE_ROOT}/dist/ubuntu-arm}"
      IMAGE_TAG="${COMPILE_IMAGE:-easyaiot/compile-panel-ubuntu:arm64}"
      ;;
    --kylin|kylin|银河麒麟|麒麟) 
      DEB_VARIANT="kylin"
      DOCKER_PLATFORM="linux/arm64"
      OUT_VARIANT="-kylin"
      DEB_ARCH_OVERRIDE="arm64"
      OUT_DIR="${COMPILE_OUT:-${COMPILE_ROOT}/dist/ubuntu-kylin}"
      IMAGE_TAG="${COMPILE_IMAGE:-easyaiot/compile-panel-ubuntu:kylin-arm64}"
      ;;
    -h|--help)
      echo "用法: $0 [--docker|--local] [--deb]"
      exit 0
      ;;
    *)
      echo "未知参数: $arg" >&2
      echo "用法: $0 [--docker|--local] [--deb]" >&2
      exit 1
      ;;
  esac
done

mkdir -p "$OUT_DIR"

log() { echo "[COMPILE/ubuntu] $*"; }

write_run_sh() {
  cp -f "${REPO_ROOT}/PANEL/panel.env.example" "${OUT_DIR}/panel.env.example"
  cat > "${OUT_DIR}/run.sh" <<'EOF'
#!/usr/bin/env bash
# 运行编译后的 EasyAIoT PANEL（需本机 docker CLI + 仓库根）
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export EASYAIOT_ROOT="${EASYAIOT_ROOT:-$(cd "${HERE}/../../.." && pwd)}"
export PANEL_ENV_FILE="${PANEL_ENV_FILE:-${HERE}/panel.env}"
if [ ! -f "$PANEL_ENV_FILE" ] && [ -f "${HERE}/panel.env.example" ]; then
  cp "${HERE}/panel.env.example" "$PANEL_ENV_FILE"
fi
exec "${HERE}/easyaiot-panel"
EOF
  chmod +x "${OUT_DIR}/run.sh"
}

build_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "[COMPILE] 需要 Docker" >&2
    exit 1
  fi
  if ! command -v npm >/dev/null 2>&1; then
    echo "[COMPILE] Docker 打包需要本机 npm 先构建 PANEL/ui（容器内不再跑 npm）" >&2
    exit 1
  fi

  local panel="${REPO_ROOT}/PANEL"
  local ctx="${COMPILE_ROOT}/work/ubuntu-docker-ctx"
  local ignore_src="${SCRIPT_DIR}/context.dockerignore"

  log "宿主机构建前端 ui/dist（避免容器内 npm 卡住）"
  (cd "${panel}/ui" && npm install --no-audit --no-fund && npm run build)
  test -f "${panel}/ui/dist/index.html"

  log "准备精简 Docker 上下文 → ${ctx}"
  rm -rf "$ctx"
  mkdir -p "${ctx}/PANEL/ui" "${ctx}/COMPILE/platforms/ubuntu"
  # 仅复制打包所需文件，避免把整个仓库（AI/DEVICE 等数 GB）传给 dockerd
  cp -a "${panel}/docker_ops.py" "${panel}/stack_ops.py" "${panel}/topology.py" \
    "${panel}/panel_server.py" "${panel}/run_panel.py" "${ctx}/PANEL/"
  cp -a "${panel}/ui/dist" "${ctx}/PANEL/ui/dist"
  cp -a "${COMPILE_ROOT}/requirements-build.txt" "${ctx}/COMPILE/"
  cp -a "${SCRIPT_DIR}/panel.spec" "${SCRIPT_DIR}/Dockerfile" "${ctx}/COMPILE/platforms/ubuntu/"
  if [ -f "$ignore_src" ]; then
    cp -f "$ignore_src" "${ctx}/.dockerignore"
  fi

  local ctx_size
  ctx_size="$(du -sh "$ctx" 2>/dev/null | awk '{print $1}')"
  log "Docker 构建 PANEL → ${OUT_DIR}/easyaiot-panel（精简上下文约 ${ctx_size}）"

  DOCKER_BUILDKIT=1 docker build \
    --platform "${DOCKER_PLATFORM}" \
    -f "${ctx}/COMPILE/platforms/ubuntu/Dockerfile" \
    --target export \
    -t "${IMAGE_TAG}" \
    --output "type=local,dest=${OUT_DIR}" \
    "$ctx"

  if [ ! -x "${OUT_DIR}/easyaiot-panel" ]; then
    if [ -x "${OUT_DIR}/easyaiot-panel/easyaiot-panel" ]; then
      mv "${OUT_DIR}/easyaiot-panel/easyaiot-panel" "${OUT_DIR}/easyaiot-panel.bin"
      rm -rf "${OUT_DIR}/easyaiot-panel"
      mv "${OUT_DIR}/easyaiot-panel.bin" "${OUT_DIR}/easyaiot-panel"
    fi
  fi

  chmod +x "${OUT_DIR}/easyaiot-panel"
  write_run_sh
  log "完成: ${OUT_DIR}/easyaiot-panel"
  ls -lh "${OUT_DIR}/easyaiot-panel"
}

build_local() {
  local panel="${REPO_ROOT}/PANEL"
  local venv="${COMPILE_ROOT}/.venv-build"
  log "本地构建（不经 Docker）"

  if ! command -v npm >/dev/null 2>&1; then
    echo "[COMPILE] 本地模式需要 npm" >&2
    exit 1
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    echo "[COMPILE] 本地模式需要 python3" >&2
    exit 1
  fi

  log "构建前端 ui/dist"
  (cd "${panel}/ui" && npm install --no-audit --no-fund && npm run build)
  test -f "${panel}/ui/dist/index.html"

  if [ ! -d "$venv" ]; then
    python3 -m venv "$venv"
  fi
  # shellcheck disable=SC1091
  source "${venv}/bin/activate"
  pip install -U pip
  pip install -r "${COMPILE_ROOT}/requirements-build.txt"

  export PANEL_SRC="$panel"
  rm -rf "${COMPILE_ROOT}/work/ubuntu"
  mkdir -p "${COMPILE_ROOT}/work/ubuntu"
  pyinstaller \
    --clean \
    --noconfirm \
    --distpath "$OUT_DIR" \
    --workpath "${COMPILE_ROOT}/work/ubuntu" \
    "${SCRIPT_DIR}/panel.spec"

  chmod +x "${OUT_DIR}/easyaiot-panel"
  write_run_sh
  log "完成: ${OUT_DIR}/easyaiot-panel"
  ls -lh "${OUT_DIR}/easyaiot-panel"
}

case "$MODE" in
  docker) build_docker ;;
  local) build_local ;;
esac

if [ "$DO_DEB" -eq 1 ]; then
  COMPILE_OUT="${OUT_DIR}" \
    DEB_VARIANT="${DEB_VARIANT}" \
    DEB_ARCH="${DEB_ARCH_OVERRIDE}" \
    bash "${SCRIPT_DIR}/pack_deb.sh"
fi
