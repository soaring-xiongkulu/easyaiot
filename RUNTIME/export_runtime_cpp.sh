#!/usr/bin/env bash
# ============================================
# 导出 RUNTIME C++ 离线包（供 iot-node SSH 分发到计算节点）
# ============================================
# 用法:
#   bash RUNTIME/export_runtime_cpp.sh
#   RUNTIME_ARCH=arm64 bash RUNTIME/export_runtime_cpp.sh
#
# 产出（按目标操作系统 + 架构分区，禁止跨 ABI 混用）:
#   RUNTIME/.bundle-runtime/{os_family}/{arch}/easyaiot-runtime-{os_family}-{arch}.tar.gz
#   例: openeuler24/x86_64、ubuntu24/x86_64、el9/x86_64
#   同目录 .ready 标记
#
# 必须在目标同类系统（或同类容器）里编译再导出。RUNTIME_OS_FAMILY 若与本机
# os-release 不一致会直接拒绝，避免把 Ubuntu 包打成 openEuler 标签。
#
# 一键：若尚未编译，默认自动执行 ./install_linux.sh install（可用 RUNTIME_AUTO_INSTALL=0 关闭）
# ============================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"

# shellcheck disable=SC1091
source "$ROOT/scripts/version_meta.sh"
# shellcheck disable=SC1091
source "$ROOT/scripts/os_family.sh"

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

  local conda_lib="${RUNTIME_CONDA_LIB_HOST:-${CONDA_PREFIX:-}/lib}"
  copy_named_libs_from() {
    local src="$1"
    [[ -d "$src" ]] || return 0
    local pattern f base
    for pattern in \
      'libcblas.so*' 'libblas.so*' 'liblapack.so*' 'libgfortran.so*' \
      'libopenblas.so*' 'libopenblasp*.so*' 'libgomp.so*'; do
      shopt -s nullglob
      for f in "$src"/$pattern; do
        base="$(basename "$f")"
        cp -L -f "$f" "$dest_lib/$base" 2>/dev/null || true
      done
      shopt -u nullglob
    done
  }
  copy_named_libs_from "$conda_lib"

  if ! command -v ldd >/dev/null 2>&1; then
    print_warning "无 ldd，跳过依赖收集（仅含 ORT lib）"
    return 0
  fi

  local line so real base
  while IFS= read -r line; do
    so="$(echo "$line" | awk '/=>/ {print $3}')"
    [[ -z "$so" || "$so" == "not" ]] && continue
    [[ ! -e "$so" ]] && continue
    # 跳过系统核心 libc/libm/libpthread/ld
    case "$(basename "$so")" in
      libc.so*|libm.so*|libpthread.so*|libdl.so*|librt.so*|ld-linux*|libresolv.so*|libnss_*|libanl.so*) continue ;;
    esac
    real="$(readlink -f "$so" 2>/dev/null || echo "$so")"
    base="$(basename "$so")"
    # 解引用 symlink，避免包内链到 /opt/miniconda3/... 绝对路径
    cp -L -f "$real" "$dest_lib/$base" 2>/dev/null || true
    if [[ -n "$real" && "$real" != "$so" ]]; then
      cp -L -f "$real" "$dest_lib/$(basename "$real")" 2>/dev/null || true
    fi
  done < <(ldd "$bin" 2>/dev/null || true)

  copy_named_libs_from "$conda_lib"
}

relocate_runtime_rpath() {
  local bin="$1"
  if command -v patchelf >/dev/null 2>&1; then
    patchelf --set-rpath '$ORIGIN/../lib' "$bin" 2>/dev/null || true
  elif command -v chrpath >/dev/null 2>&1; then
    chrpath -r '$ORIGIN/../lib' "$bin" 2>/dev/null || true
  fi
}

main() {
  ensure_built

  local arch os_family host_family requested
  arch="$(arch_key)"
  requested="${RUNTIME_OS_FAMILY:-}"
  host_family="$(RUNTIME_OS_FAMILY= runtime_detect_os_family)"
  if [[ -n "$requested" && "$requested" != "$host_family" ]]; then
    print_error "本机 os-release 为 ${host_family}，拒绝打成 ${requested} 包（ABI 会错）。"
    print_error "请在 ${requested} 系统或同类容器中执行 export_runtime_cpp.sh。"
    exit 1
  fi
  os_family="$host_family"
  export RUNTIME_OS_FAMILY="$os_family"
  local cache="${RUNTIME_CACHE_DIR:-$ROOT/.bundle-runtime/${os_family}/${arch}}"
  mkdir -p "$cache"
  print_info "目标包键: os=${os_family} arch=${arch}"

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
  local pkg="easyaiot-runtime-${os_family}-${arch}"
  local staging="$RUNTIME_EXPORT_WORK/${pkg}"
  mkdir -p "$staging/bin" "$staging/lib" "$staging/config" "$staging/models" "$staging/scripts"

  cp -f "$bin" "$staging/bin/RUNTIME"
  chmod +x "$staging/bin/RUNTIME"

  print_info "收集动态库依赖..."
  collect_libs "$staging/bin/RUNTIME" "$staging/lib"
  relocate_runtime_rpath "$staging/bin/RUNTIME"

  # .pt → onnx 兜底脚本（节点上若有 ultralytics / RUNTIME_PYTHON 可用）
  if [[ -f "$ROOT/scripts/ensure_onnx_model.py" ]]; then
    cp -f "$ROOT/scripts/ensure_onnx_model.py" "$staging/scripts/" || true
  fi
  if [[ -f "$ROOT/scripts/smoke_runtime.sh" ]]; then
    cp -f "$ROOT/scripts/smoke_runtime.sh" "$staging/scripts/" || true
    chmod +x "$staging/scripts/smoke_runtime.sh"
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
  {
    echo "os_family=${os_family}"
    echo "arch=${arch}"
  } >> "$staging/VERSION"
  # Also refresh control-plane copy for check UI
  cp -f "$staging/VERSION" "$ROOT/build/VERSION" 2>/dev/null || true
  cp -f "$staging/VERSION" "$ROOT/VERSION" 2>/dev/null || true
  print_info "打包 VERSION: version=${RUNTIME_VERSION} git=${RUNTIME_GIT} os=${os_family} arch=${arch}"

  print_info "本机冒烟：source env.sh && RUNTIME --version ..."
  if ! bash "$ROOT/scripts/smoke_runtime.sh" "$staging"; then
    print_error "导出包在本机无法执行，拒绝产出（请检查动态库收集是否跳过了 glibc 组件）"
    exit 1
  fi

  local tar_name="easyaiot-runtime-${os_family}-${arch}.tar.gz"
  local tar_path="$cache/$tar_name"
  print_info "打包 $tar_path ..."
  tar -czf "$tar_path" -C "$RUNTIME_EXPORT_WORK" "$pkg"
  date -Iseconds 2>/dev/null || date > "$cache/.ready"
  echo "${os_family}" > "$cache/.os-family"
  echo "${arch}" > "$cache/.arch"
  print_success "已导出: $tar_path ($(du -h "$tar_path" | awk '{print $1}')) version=${RUNTIME_VERSION} os=${os_family}"
  echo "RUNTIME_EXPORT_OK=$tar_path"
}

main "$@"
