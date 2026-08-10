#!/usr/bin/env bash
# ============================================
# 导出 RUNTIME C++ 离线包（供 iot-node SSH 分发到计算节点）
# ============================================
# 用法:
#   bash RUNTIME/export_runtime_cpp.sh
#   RUNTIME_ARCH=arm64 bash RUNTIME/export_runtime_cpp.sh
#
# 产出:
#   RUNTIME/.bundle-runtime/{x86_64|arm64}/easyaiot-runtime-{arch}.tar.gz
#   同目录 .ready 标记
#
# 一键：若尚未编译，默认自动执行 ./install_linux.sh install（可用 RUNTIME_AUTO_INSTALL=0 关闭）
# ============================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"

# shellcheck disable=SC1091
source "$ROOT/scripts/version_meta.sh"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

arch_key() {
  local m="${RUNTIME_ARCH:-$(uname -m)}"
  m="$(echo "$m" | tr '[:upper:]' '[:lower:]')"
  case "$m" in
    aarch64|arm64) echo "arm64" ;;
    *) echo "x86_64" ;;
  esac
}

ensure_built() {
  local bin="$ROOT/build/RUNTIME"
  local deploy_env="$ROOT/deploy.env"
  if [[ -f "$deploy_env" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$deploy_env"
    set +a
    bin="${RUNTIME_BIN:-$bin}"
  fi
  if [[ -x "$bin" && -f "$deploy_env" ]]; then
    return 0
  fi
  if [[ "${RUNTIME_AUTO_INSTALL:-1}" != "1" ]]; then
    print_error "未找到可执行 RUNTIME: $bin（已关闭自动编译 RUNTIME_AUTO_INSTALL=0）"
    return 1
  fi
  local install_sh="$ROOT/install_linux.sh"
  if [[ ! -f "$install_sh" ]]; then
    print_error "缺少 $install_sh"
    return 1
  fi
  print_info "控制面尚未编译 RUNTIME，自动执行 install_linux.sh ..."
  bash "$install_sh" install
}

collect_libs() {
  local bin="$1" dest_lib="$2"
  mkdir -p "$dest_lib"
  # ORT / conda / CUDA 优先从 deploy.env 拷贝整目录中的 .so*
  if [[ -n "${RUNTIME_ORT_LIB_HOST:-}" && -d "${RUNTIME_ORT_LIB_HOST}" ]]; then
    cp -a "${RUNTIME_ORT_LIB_HOST}/." "$dest_lib/" 2>/dev/null || true
  fi
  if [[ -n "${RUNTIME_CONDA_LIB_HOST:-}" && -d "${RUNTIME_CONDA_LIB_HOST}" ]]; then
    # 仅拷贝 RUNTIME 实际依赖的 .so（避免整个 conda lib 过大）
    :
  fi

  if ! command -v ldd >/dev/null 2>&1; then
    print_warning "无 ldd，跳过依赖收集（仅含 ORT lib）"
    return 0
  fi

  local line so real
  while IFS= read -r line; do
    so="$(echo "$line" | awk '/=>/ {print $3}')"
    [[ -z "$so" || "$so" == "not" ]] && continue
    [[ ! -f "$so" ]] && continue
    # 跳过系统核心 libc/libm/libpthread/ld
    case "$(basename "$so")" in
      libc.so*|libm.so*|libpthread.so*|libdl.so*|librt.so*|ld-linux*) continue ;;
    esac
    real="$(readlink -f "$so" 2>/dev/null || echo "$so")"
    cp -a "$so" "$dest_lib/" 2>/dev/null || true
    if [[ -n "$real" && "$real" != "$so" && -f "$real" ]]; then
      cp -a "$real" "$dest_lib/" 2>/dev/null || true
    fi
  done < <(ldd "$bin" 2>/dev/null || true)
}

main() {
  ensure_built

  local arch
  arch="$(arch_key)"
  local cache="${RUNTIME_CACHE_DIR:-$ROOT/.bundle-runtime/$arch}"
  mkdir -p "$cache"

  local deploy_env="$ROOT/deploy.env"
  local bin="$ROOT/build/RUNTIME"
  if [[ -f "$deploy_env" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$deploy_env"
    set +a
    bin="${RUNTIME_BIN:-$bin}"
  fi

  if [[ ! -x "$bin" ]]; then
    print_error "编译后仍未找到可执行 RUNTIME: $bin"
    exit 1
  fi

  # 清理目录必须用全局变量：local 在 main 返回后 EXIT trap 看不到
  RUNTIME_EXPORT_WORK="$(mktemp -d)"
  trap 'rm -rf "${RUNTIME_EXPORT_WORK:-}"' EXIT
  local staging="$RUNTIME_EXPORT_WORK/easyaiot-runtime-${arch}"
  mkdir -p "$staging/bin" "$staging/lib" "$staging/config" "$staging/models" "$staging/scripts"

  cp -f "$bin" "$staging/bin/RUNTIME"
  chmod +x "$staging/bin/RUNTIME"

  print_info "收集动态库依赖..."
  collect_libs "$staging/bin/RUNTIME" "$staging/lib"

  # .pt → onnx 兜底脚本（节点上若有 ultralytics / RUNTIME_PYTHON 可用）
  if [[ -f "$ROOT/scripts/ensure_onnx_model.py" ]]; then
    cp -f "$ROOT/scripts/ensure_onnx_model.py" "$staging/scripts/" || true
  fi

  # 内置 ONNX（存在则打入；-L 解引用 yolo11n.onnx → yolov11n.onnx）
  local model_file
  for model_file in \
    yolo11n.onnx yolov11n.onnx \
    yolov8n.onnx yolo26n.onnx \
    coco.names yolo11n.names yolov8n.names yolo26n.names; do
    if [[ -e "$ROOT/models/$model_file" ]]; then
      cp -L -f "$ROOT/models/$model_file" "$staging/models/" || true
    fi
  done
  # 规范名：仅有历史 yolov11n.onnx 时补一份 yolo11n.onnx
  if [[ ! -f "$staging/models/yolo11n.onnx" && -f "$staging/models/yolov11n.onnx" ]]; then
    cp -f "$staging/models/yolov11n.onnx" "$staging/models/yolo11n.onnx" || true
  fi

  cat > "$staging/env.sh" <<'EOF'
#!/usr/bin/env bash
# Sourced on compute nodes after install_runtime_cpp.sh
RUNTIME_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export RUNTIME_ROOT
export RUNTIME_BIN="${RUNTIME_ROOT}/bin/RUNTIME"
export LD_LIBRARY_PATH="${RUNTIME_ROOT}/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
# Prefer host CUDA if present
for _cuda in /usr/local/cuda/lib64 /usr/local/cuda/lib; do
  if [[ -d "$_cuda" ]]; then
    export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:$_cuda"
  fi
done
export RUNTIME_PREFER_GPU="${RUNTIME_PREFER_GPU:-true}"
export USE_GPU="${USE_GPU:-true}"
# .pt→onnx：指向带 ultralytics 的 Python（可选）
# export RUNTIME_PYTHON=/path/to/python
EOF
  chmod +x "$staging/env.sh"

  # Prefer existing build VERSION fields; refresh built_at/source for export package
  runtime_resolve_version_meta "$ROOT" "$REPO"
  if [[ -f "$ROOT/build/VERSION" ]]; then
    # Keep version/git from build if present
    while IFS='=' read -r k v; do
      case "$k" in
        version) RUNTIME_VERSION="$v" ;;
        git) RUNTIME_GIT="$v" ;;
      esac
    done < <(grep -E '^(version|git)=' "$ROOT/build/VERSION" 2>/dev/null || true)
  fi
  runtime_write_version_file "$staging/VERSION" "export" "$bin" "${RUNTIME_ORT_LIB_HOST:-${ORT_ROOT:-}}" "${RUNTIME_BUILD_MODE:-${BUILD_MODE:-}}"
  # Also refresh control-plane copy for check UI
  cp -f "$staging/VERSION" "$ROOT/build/VERSION" 2>/dev/null || true
  cp -f "$staging/VERSION" "$ROOT/VERSION" 2>/dev/null || true
  print_info "打包 VERSION: version=${RUNTIME_VERSION} git=${RUNTIME_GIT}"

  local tar_name="easyaiot-runtime-${arch}.tar.gz"
  local tar_path="$cache/$tar_name"
  print_info "打包 $tar_path ..."
  tar -czf "$tar_path" -C "$RUNTIME_EXPORT_WORK" "easyaiot-runtime-${arch}"
  date -Iseconds 2>/dev/null || date > "$cache/.ready"
  print_success "已导出: $tar_path ($(du -h "$tar_path" | awk '{print $1}')) version=${RUNTIME_VERSION}"
  echo "RUNTIME_EXPORT_OK=$tar_path"
}

main "$@"
