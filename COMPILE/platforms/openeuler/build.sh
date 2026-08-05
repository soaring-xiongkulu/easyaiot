#!/usr/bin/env bash
# openEuler 24.x 目标：支持 Docker 标准化构建，或本机构建
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPILE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REPO_ROOT="$(cd "${COMPILE_ROOT}/.." && pwd)"
OUT_DIR="${COMPILE_OUT:-${COMPILE_ROOT}/dist/openeuler}"
VENV_DIR="${COMPILE_ROOT}/.venv-build-openeuler"
IMAGE_TAG="${COMPILE_IMAGE:-easyaiot/compile-panel-openeuler:latest}"
BASE_IMAGE="${COMPILE_OPENEULER_BASE_IMAGE:-openeuler/openeuler:24.03}"

MODE="docker"
DO_RPM=1

log() { echo "[COMPILE/openeuler] $*"; }

for arg in "$@"; do
  case "$arg" in
    --docker|docker)
      MODE="docker"
      ;;
    --local|local)
      MODE="local"
      ;;
    --rpm|rpm|--package|package)
      DO_RPM=1
      ;;
    --no-rpm)
      DO_RPM=0
      ;;
    -h|--help)
      echo "用法: $0 [--docker|--local] [--rpm|--no-rpm]"
      echo "环境变量:"
      echo "  COMPILE_OPENEULER_BASE_IMAGE  默认 openeuler/openeuler:24.03"
      echo "  COMPILE_CN_MIRROR             包源 huawei（默认）|aliyun|tuna"
      echo "  COMPILE_OUT                  默认 COMPILE/dist/openeuler"
      exit 0
      ;;
    *)
      echo "[COMPILE/openeuler] 未知参数: $arg" >&2
      exit 1
      ;;
  esac
done

build_local() {
  if ! command -v python3 >/dev/null 2>&1; then
    echo "[COMPILE/openeuler] 需要 python3" >&2
    exit 1
  fi

  mkdir -p "$OUT_DIR"

  if [ "${SKIP_UI_BUILD:-0}" = "1" ] && [ -f "${REPO_ROOT}/PANEL/ui/dist/index.html" ]; then
    log "复用已有前端 ui/dist"
  else
    if ! command -v npm >/dev/null 2>&1; then
      echo "[COMPILE/openeuler] 本地构建前端需要 npm" >&2
      exit 1
    fi
    log "构建前端 ui/dist"
    (cd "${REPO_ROOT}/PANEL/ui" && npm install --no-audit --no-fund && npm run build)
    test -f "${REPO_ROOT}/PANEL/ui/dist/index.html"
  fi

  if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
  fi
  # shellcheck disable=SC1091
  source "${VENV_DIR}/bin/activate"
  # Docker/国内网络访问 pypi.org 常失败；未指定时默认清华源
  export PIP_INDEX_URL="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
  export PIP_TRUSTED_HOST="${PIP_TRUSTED_HOST:-pypi.tuna.tsinghua.edu.cn}"
  python3 -m pip install -U pip
  python3 -m pip install -r "${COMPILE_ROOT}/requirements-build.txt"

  export PANEL_SRC="${REPO_ROOT}/PANEL"
  WORK_DIR="${COMPILE_ROOT}/work/openeuler"
  rm -rf "$WORK_DIR"
  mkdir -p "$WORK_DIR"

  log "PyInstaller 生成 Linux 二进制"
  pyinstaller \
    --clean \
    --noconfirm \
    --distpath "$OUT_DIR" \
    --workpath "$WORK_DIR" \
    "${COMPILE_ROOT}/platforms/ubuntu/panel.spec"

  if [ ! -f "${OUT_DIR}/easyaiot-panel" ]; then
    echo "[COMPILE/openeuler] 未生成 easyaiot-panel" >&2
    exit 1
  fi
  chmod +x "${OUT_DIR}/easyaiot-panel"
  cp -f "${REPO_ROOT}/PANEL/panel.env.example" "${OUT_DIR}/panel.env.example"

  cat > "${OUT_DIR}/run.sh" <<'EOF'
#!/usr/bin/env bash
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

  log "完成: ${OUT_DIR}/easyaiot-panel"
  ls -lh "${OUT_DIR}/easyaiot-panel"

  if [ "$DO_RPM" -eq 1 ]; then
    bash "${SCRIPT_DIR}/pack_rpm.sh"
  fi
}

build_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "[COMPILE/openeuler] 需要 Docker（容器标准化构建）" >&2
    exit 1
  fi

  if ! command -v npm >/dev/null 2>&1; then
    echo "[COMPILE/openeuler] Docker 打包需要本机 npm 先构建 PANEL/ui" >&2
    exit 1
  fi
  log "宿主机构建前端 ui/dist（容器内不再跑 npm）"
  (cd "${REPO_ROOT}/PANEL/ui" && npm install --no-audit --no-fund && npm run build)
  test -f "${REPO_ROOT}/PANEL/ui/dist/index.html"

  mkdir -p "$OUT_DIR"
  CTX_DIR="${COMPILE_ROOT}/work/openeuler-docker-context"
  rm -rf "${CTX_DIR}"
  mkdir -p "${CTX_DIR}/PANEL" "${CTX_DIR}/COMPILE"
  # 仅复制最小构建上下文，避免仓库内受限目录导致 docker context 读取失败
  cp -a "${REPO_ROOT}/PANEL/." "${CTX_DIR}/PANEL/"
  cp -a "${COMPILE_ROOT}/assets" "${CTX_DIR}/COMPILE/"
  cp -a "${COMPILE_ROOT}/requirements-build.txt" "${CTX_DIR}/COMPILE/"
  cp -a "${COMPILE_ROOT}/platforms" "${CTX_DIR}/COMPILE/"
  mkdir -p "${CTX_DIR}/COMPILE/lib"
  cp -a "${COMPILE_ROOT}/lib/." "${CTX_DIR}/COMPILE/lib/"

  PANEL_VERSION_ARG=""
  if [ "$DO_RPM" -eq 1 ]; then
    # 在宿主机解析并递增版本，再传入容器，避免容器内状态无法回写
    # shellcheck source=../../lib/resolve_panel_version.sh
    source "${COMPILE_ROOT}/lib/resolve_panel_version.sh"
    PANEL_VERSION_ARG="$(resolve_panel_version)"
    printf 'V%s\n' "$PANEL_VERSION_ARG" > "${CTX_DIR}/COMPILE/.panel-version"
  fi

  if [ "$DO_RPM" -eq 1 ]; then
    log "Docker 标准化构建 openEuler 二进制 + RPM (version=${PANEL_VERSION_ARG} base=${BASE_IMAGE} cn=${COMPILE_CN_MIRROR:-huawei})"
  else
    log "Docker 标准化构建 openEuler 二进制 (base=${BASE_IMAGE})"
  fi
  DOCKER_BUILDKIT=1 docker build \
    -f "${SCRIPT_DIR}/Dockerfile" \
    --build-arg BASE_IMAGE="${BASE_IMAGE}" \
    --build-arg BUILD_RPM="${DO_RPM}" \
    --build-arg PANEL_VERSION="${PANEL_VERSION_ARG}" \
    --build-arg COMPILE_CN_MIRROR="${COMPILE_CN_MIRROR:-huawei}" \
    --target export \
    -t "${IMAGE_TAG}" \
    --output "type=local,dest=${OUT_DIR}" \
    "${CTX_DIR}"

  # 某些 docker 版本会输出到子目录，做一次兜底
  if [ -d "${OUT_DIR}/out" ]; then
    cp -f "${OUT_DIR}/out/"* "${OUT_DIR}/" 2>/dev/null || true
    rm -rf "${OUT_DIR}/out"
  fi
  ls -lh "${OUT_DIR}"
}

case "$MODE" in
  local) build_local ;;
  docker) build_docker ;;
esac
