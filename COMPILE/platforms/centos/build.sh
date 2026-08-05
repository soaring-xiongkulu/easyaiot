#!/usr/bin/env bash
# CentOS/RHEL 目标：按 EL 大版本（7/8/9）分别打包
#   bash COMPILE/platforms/centos/build.sh --el9
#   bash COMPILE/platforms/centos/build.sh --el8 --docker
#   bash COMPILE/platforms/centos/build.sh --el7 --no-rpm
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPILE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REPO_ROOT="$(cd "${COMPILE_ROOT}/.." && pwd)"
# shellcheck source=el_common.sh
source "${SCRIPT_DIR}/el_common.sh"

EL_ARG="${EL_RELEASE:-9}"
MODE="docker"
DO_RPM=1

for arg in "$@"; do
  case "$arg" in
    --el7|el7) EL_ARG=7 ;;
    --el8|el8) EL_ARG=8 ;;
    --el9|el9) EL_ARG=9 ;;
    --docker|docker) MODE="docker" ;;
    --local|local) MODE="local" ;;
    --rpm|rpm|--package|package) DO_RPM=1 ;;
    --no-rpm) DO_RPM=0 ;;
    -h|--help)
      echo "用法: $0 [--el7|--el8|--el9] [--docker|--local] [--rpm|--no-rpm]"
      centos_el_help_lines
      echo "  COMPILE_OUT  默认 COMPILE/dist/centos-el{7|8|9}"
      exit 0
      ;;
    *)
      echo "[COMPILE/centos] 未知参数: $arg" >&2
      exit 1
      ;;
  esac
done

centos_resolve_el "$EL_ARG"

OUT_DIR="${COMPILE_OUT:-${COMPILE_ROOT}/dist/centos-${EL_OUT_SUFFIX}}"
VENV_DIR="${COMPILE_ROOT}/.venv-build-centos-${EL_OUT_SUFFIX}"
IMAGE_TAG="${COMPILE_IMAGE:-easyaiot/compile-panel-centos:${EL_OUT_SUFFIX}}"
BASE_IMAGE="${COMPILE_CENTOS_BASE_IMAGE:-${BASE_IMAGE_DEFAULT}}"
export COMPILE_OUT="$OUT_DIR"
export PANEL_DIST_TAG PANEL_PUBLISH_OS EL_RELEASE

log() { echo "[COMPILE/centos-${EL_OUT_SUFFIX}] $*"; }

pick_python() {
  # 优先较新的解释器（el8 常有 python3.9；el7 容器内用 SCL）
  local c
  for c in python3.11 python3.10 python3.9 python3.8 python3; do
    if command -v "$c" >/dev/null 2>&1; then
      echo "$c"
      return 0
    fi
  done
  return 1
}

build_local() {
  local py
  if ! py="$(pick_python)"; then
    echo "[COMPILE/centos-${EL_OUT_SUFFIX}] 需要 python3（建议 >= 3.8）" >&2
    exit 1
  fi
  log "使用 Python: $py ($("$py" -V 2>&1))"

  mkdir -p "$OUT_DIR"

  if [ "${SKIP_UI_BUILD:-0}" = "1" ] && [ -f "${REPO_ROOT}/PANEL/ui/dist/index.html" ]; then
    log "复用已有前端 ui/dist"
  else
    if ! command -v npm >/dev/null 2>&1; then
      echo "[COMPILE/centos-${EL_OUT_SUFFIX}] 本地构建前端需要 npm" >&2
      exit 1
    fi
    log "构建前端 ui/dist"
    (cd "${REPO_ROOT}/PANEL/ui" && npm install --no-audit --no-fund && npm run build)
    test -f "${REPO_ROOT}/PANEL/ui/dist/index.html"
  fi

  if [ ! -d "$VENV_DIR" ]; then
    "$py" -m venv "$VENV_DIR"
  fi
  # shellcheck disable=SC1091
  source "${VENV_DIR}/bin/activate"
  export PIP_INDEX_URL="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
  export PIP_TRUSTED_HOST="${PIP_TRUSTED_HOST:-pypi.tuna.tsinghua.edu.cn}"
  python -m pip install -U pip
  python -m pip install -r "${COMPILE_ROOT}/requirements-build.txt"

  export PANEL_SRC="${REPO_ROOT}/PANEL"
  WORK_DIR="${COMPILE_ROOT}/work/centos-${EL_OUT_SUFFIX}"
  rm -rf "$WORK_DIR"
  mkdir -p "$WORK_DIR"

  log "PyInstaller 生成 Linux 二进制 (el${EL_RELEASE})"
  pyinstaller \
    --clean \
    --noconfirm \
    --distpath "$OUT_DIR" \
    --workpath "$WORK_DIR" \
    "${COMPILE_ROOT}/platforms/ubuntu/panel.spec"

  if [ ! -f "${OUT_DIR}/easyaiot-panel" ]; then
    echo "[COMPILE/centos-${EL_OUT_SUFFIX}] 未生成 easyaiot-panel" >&2
    exit 1
  fi
  chmod +x "${OUT_DIR}/easyaiot-panel"
  cp -f "${REPO_ROOT}/PANEL/panel.env.example" "${OUT_DIR}/panel.env.example"

  cat > "${OUT_DIR}/run.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
HERE="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
export EASYAIOT_ROOT="\${EASYAIOT_ROOT:-\$(cd "\${HERE}/../../.." && pwd)}"
export PANEL_ENV_FILE="\${PANEL_ENV_FILE:-\${HERE}/panel.env}"
if [ ! -f "\$PANEL_ENV_FILE" ] && [ -f "\${HERE}/panel.env.example" ]; then
  cp "\${HERE}/panel.env.example" "\$PANEL_ENV_FILE"
fi
export INSTALL_SCRIPT="\${INSTALL_SCRIPT:-.scripts/docker/install_linux_centos.sh}"
exec "\${HERE}/easyaiot-panel"
EOF
  chmod +x "${OUT_DIR}/run.sh"

  log "完成: ${OUT_DIR}/easyaiot-panel"
  ls -lh "${OUT_DIR}/easyaiot-panel"

  if [ "$DO_RPM" -eq 1 ]; then
    EL_RELEASE="$EL_RELEASE" PANEL_DIST_TAG="$PANEL_DIST_TAG" \
      COMPILE_OUT="$OUT_DIR" bash "${SCRIPT_DIR}/pack_rpm.sh"
  fi
}

build_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "[COMPILE/centos-${EL_OUT_SUFFIX}] 需要 Docker（容器标准化构建）" >&2
    exit 1
  fi

  if ! command -v npm >/dev/null 2>&1; then
    echo "[COMPILE/centos-${EL_OUT_SUFFIX}] Docker 打包需要本机 npm 先构建 PANEL/ui" >&2
    exit 1
  fi
  log "宿主机构建前端 ui/dist（容器内不再跑 npm）"
  (cd "${REPO_ROOT}/PANEL/ui" && npm install --no-audit --no-fund && npm run build)
  test -f "${REPO_ROOT}/PANEL/ui/dist/index.html"

  mkdir -p "$OUT_DIR"
  CTX_DIR="${COMPILE_ROOT}/work/centos-${EL_OUT_SUFFIX}-docker-context"
  rm -rf "${CTX_DIR}"
  mkdir -p "${CTX_DIR}/PANEL" "${CTX_DIR}/COMPILE"
  cp -a "${REPO_ROOT}/PANEL/." "${CTX_DIR}/PANEL/"
  cp -a "${COMPILE_ROOT}/assets" "${CTX_DIR}/COMPILE/"
  cp -a "${COMPILE_ROOT}/requirements-build.txt" "${CTX_DIR}/COMPILE/"
  cp -a "${COMPILE_ROOT}/platforms" "${CTX_DIR}/COMPILE/"
  mkdir -p "${CTX_DIR}/COMPILE/lib"
  cp -a "${COMPILE_ROOT}/lib/." "${CTX_DIR}/COMPILE/lib/"

  PANEL_VERSION_ARG=""
  if [ "$DO_RPM" -eq 1 ]; then
    # shellcheck source=../../lib/resolve_panel_version.sh
    source "${COMPILE_ROOT}/lib/resolve_panel_version.sh"
    PANEL_VERSION_ARG="$(resolve_panel_version)"
    printf 'V%s\n' "$PANEL_VERSION_ARG" > "${CTX_DIR}/COMPILE/.panel-version"
  fi

  if [ "$DO_RPM" -eq 1 ]; then
    log "Docker 构建 CentOS ${DIST_TAG} 二进制 + RPM (base=${BASE_IMAGE} version=${PANEL_VERSION_ARG})"
  else
    log "Docker 构建 CentOS ${DIST_TAG} 二进制 (base=${BASE_IMAGE})"
  fi
  DOCKER_BUILDKIT=1 docker build \
    -f "${SCRIPT_DIR}/Dockerfile" \
    --build-arg BASE_IMAGE="${BASE_IMAGE}" \
    --build-arg EL_RELEASE="${EL_RELEASE}" \
    --build-arg BUILD_RPM="${DO_RPM}" \
    --build-arg PANEL_VERSION="${PANEL_VERSION_ARG}" \
    --build-arg COMPILE_CN_MIRROR="${COMPILE_CN_MIRROR:-huawei}" \
    --target export \
    -t "${IMAGE_TAG}" \
    --output "type=local,dest=${OUT_DIR}" \
    "${CTX_DIR}"

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
