#!/usr/bin/env bash
# ============================================
# VIDEO ↔ 芯片算法运行时部署桥接
# ============================================
# 用法（在 VIDEO 目录或任意目录）:
#   bash VIDEO/scripts/ensure_runtime_cpp.sh          # 按芯片编译 RUNTIME 并写 compose 挂载
#   bash VIDEO/scripts/ensure_runtime_cpp.sh wire     # 仅根据目标运行时写挂载（不重编译）
#   bash VIDEO/scripts/ensure_runtime_cpp.sh skip-check
#
# 目标芯片:
#   EASYAIOT_RUNTIME_TARGET=auto|generic|rk3588|bm1688
#   auto（默认）按设备树选择 RUNTIME-RK3588 / RUNTIME-BM1688，其余选择通用 RUNTIME
#
# 依赖环境变量（可由调用方设置）:
#   EASYAIOT_ROOT          仓库根（默认由本脚本推断）
#   EASYAIOT_RUNTIME_SKIP=1
#   EASYAIOT_RUNTIME_REQUIRED=1
# ============================================
set -euo pipefail

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VIDEO_DIR="$(cd "$SCRIPT_PATH/.." && pwd)"
EASYAIOT_ROOT="${EASYAIOT_ROOT:-$(cd "$VIDEO_DIR/.." && pwd)}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

detect_runtime_target() {
  local requested
  requested="$(printf '%s' "${EASYAIOT_RUNTIME_TARGET:-${RUNTIME_TARGET:-auto}}" | tr '[:upper:]' '[:lower:]')"
  case "$requested" in
    rk3588|rknn-rk3588|runtime-rk3588|rockchip-rk3588) echo "rk3588"; return 0 ;;
    bm1688|cv186x|sophon-bm1688|runtime-bm1688) echo "bm1688"; return 0 ;;
    generic|runtime|onnx|cpu|cuda) echo "generic"; return 0 ;;
  esac
  local probe
  for probe in \
    /proc/device-tree/compatible \
    /sys/firmware/devicetree/base/compatible \
    /proc/device-tree/model \
    /sys/firmware/devicetree/base/model; do
    [[ -r "$probe" ]] || continue
    if grep -qi 'rk3588' "$probe" 2>/dev/null; then
      echo "rk3588"
      return 0
    fi
    if tr '\0' ' ' < "$probe" 2>/dev/null | grep -Eqi 'bm1688|cv186|sophon.*1688'; then
      echo "bm1688"
      return 0
    fi
  done
  if command -v bm-smi >/dev/null 2>&1 && bm-smi 2>/dev/null | grep -Eqi 'bm1688|cv186'; then
    echo "bm1688"
    return 0
  fi
  echo "generic"
}

# Rockchip 用户态库通常只装在宿主机；VIDEO 容器内没有。收集到独立目录后
# 只挂载这些厂商库，避免整目录挂载 /usr/lib 覆盖容器 glibc。
stage_rk3588_libs() {
  local dest="${VIDEO_DIR}/.runtime-rk3588-libs"
  local name lib found=0
  rm -rf "$dest"
  mkdir -p "$dest"
  for name in rknnrt rga rockchip_mpp mpp; do
    while IFS= read -r lib; do
      [[ -n "$lib" && -e "$lib" ]] || continue
      if cp -a "$lib" "$dest/" 2>/dev/null; then
        found=1
      fi
    done < <(ldconfig -p 2>/dev/null | awk -v n="lib${name}.so" '$1 == n || index($1, n ".") == 1 {print $NF}' | sort -u)
  done
  if [[ "$found" == "1" ]]; then
    printf '%s\n' "$dest"
  else
    rmdir "$dest" 2>/dev/null || true
    return 0
  fi
}

# 只收集 BM1688 二进制实际链接到的 /opt/sophon 厂商库；不挂载宿主机
# glibc 目录，避免覆盖 VIDEO 容器运行时。
stage_bm1688_libs() {
  local runtime_bin="${EASYAIOT_ROOT}/RUNTIME-BM1688/build/RUNTIME"
  local dest="${VIDEO_DIR}/.runtime-bm1688-libs"
  local lib found=0
  rm -rf "$dest"
  mkdir -p "$dest"
  if [[ -x "$runtime_bin" ]] && command -v ldd >/dev/null 2>&1; then
    while IFS= read -r lib; do
      [[ -f "$lib" ]] || continue
      case "$lib" in
        /opt/sophon/*|*/libbm*.so*|*/libsophon*.so*|*/libopencv_*.so*|*/libavcodec.so*|*/libavformat.so*|*/libavutil.so*|*/libswscale.so*)
          if cp -aL "$lib" "$dest/" 2>/dev/null; then found=1; fi
          ;;
      esac
    done < <(ldd "$runtime_bin" 2>/dev/null | awk '{for (i=1;i<=NF;i++) if ($i ~ /^\//) {print $i; break}}' | sort -u)
  fi
  if [[ "$found" == "1" ]]; then
    printf '%s\n' "$dest"
  else
    rmdir "$dest" 2>/dev/null || true
    return 0
  fi
}

# Portable KEY=VALUE updater for .env.docker (reuse deploy_profile if available)
_set_env_docker_kv_local() {
  local file="$1" key="$2" value="$3"
  if type _set_env_docker_kv >/dev/null 2>&1; then
    _set_env_docker_kv "$file" "$key" "$value"
    return 0
  fi
  mkdir -p "$(dirname "$file")"
  touch "$file"
  if grep -qE "^${key}=" "$file" 2>/dev/null; then
    # portable in-place replace
    local tmp
    tmp="$(mktemp)"
    awk -v k="$key" -v v="$value" 'BEGIN{FS=OFS="="} $1==k{$0=k"="v} {print}' "$file" > "$tmp"
    mv "$tmp" "$file"
  else
    printf '%s=%s\n' "$key" "$value" >> "$file"
  fi
}

wire_runtime_override() {
  local target
  target="$(detect_runtime_target)"
  if [[ "$target" == "rk3588" ]]; then
    wire_rk3588_override
  elif [[ "$target" == "bm1688" ]]; then
    wire_bm1688_override
  else
    wire_generic_runtime_override
  fi
}

wire_rk3588_override() {
  local module_dir="${EASYAIOT_ROOT}/RUNTIME-RK3588"
  local override_file="${VIDEO_DIR}/.docker-compose.runtime.override.yaml"
  local env_file="${VIDEO_DIR}/.env.docker"
  local runtime_bin="${module_dir}/build/RUNTIME"

  if [[ ! -x "$runtime_bin" ]]; then
    rm -f "$override_file"
    print_warning "RK3588 运行时未编译: $runtime_bin（已清理旧挂载配置）"
    return 0
  fi
  if [[ ! -f "$env_file" ]]; then
    if [[ -f "${VIDEO_DIR}/env.example" ]]; then
      cp "${VIDEO_DIR}/env.example" "$env_file"
    else
      touch "$env_file"
    fi
  fi
  mkdir -p "${module_dir}/config"
  local libs_dir
  libs_dir="$(stage_rk3588_libs)"
  if [[ -z "$libs_dir" ]]; then
    print_warning "未在宿主机找到 librknnrt/librga/librockchip_mpp；容器内 RK3588 运行可能缺少厂商库"
  fi

  local model_path="/opt/easyaiot/RUNTIME-RK3588/models/yolov8n-rk3588-int8.rknn"
  local classes_path="/opt/easyaiot/RUNTIME-RK3588/models/coco.names"
  local ld_path="/opt/easyaiot/RUNTIME-RK3588/lib:/usr/local/lib:/usr/lib/aarch64-linux-gnu"

  _set_env_docker_kv_local "$env_file" EASYAIOT_RUNTIME_TARGET "rk3588"
  _set_env_docker_kv_local "$env_file" RUNTIME_RK3588_BIN "$runtime_bin"
  _set_env_docker_kv_local "$env_file" RUNTIME_RK3588_CONFIG_DIR "/opt/easyaiot/RUNTIME-RK3588/config"
  _set_env_docker_kv_local "$env_file" RUNTIME_BM1688_BIN ""
  _set_env_docker_kv_local "$env_file" RUNTIME_BM1688_CONFIG_DIR ""
  _set_env_docker_kv_local "$env_file" RUNTIME_BIN ""
  _set_env_docker_kv_local "$env_file" RUNTIME_CONFIG_DIR ""
  _set_env_docker_kv_local "$env_file" RUNTIME_RK3588_CLASSES_PATH "$classes_path"
  if [[ -f "${module_dir}/models/yolov8n-rk3588-int8.rknn" ]]; then
    _set_env_docker_kv_local "$env_file" RUNTIME_RK3588_MODEL_PATH "$model_path"
  else
    _set_env_docker_kv_local "$env_file" RUNTIME_RK3588_MODEL_PATH ""
    print_warning "未找到默认 RKNN 模型；可执行 RUNTIME-RK3588/scripts/prepare_yolov8n_rk3588.sh <calibration.txt> 生成"
  fi
  _set_env_docker_kv_local "$env_file" LD_LIBRARY_PATH "$ld_path"
  _set_env_docker_kv_local "$env_file" USE_GPU "false"
  _set_env_docker_kv_local "$env_file" RUNTIME_PREFER_GPU "false"

  local devices_block=""
  local dev
  for dev in /dev/rknpu /dev/rga /dev/mpp_service /dev/dma_heap /dev/dri; do
    [[ -e "$dev" ]] || continue
    devices_block+="      - ${dev}:${dev}"$'\n'
  done

  {
    echo "# Auto-generated by VIDEO/scripts/ensure_runtime_cpp.sh — RUNTIME-RK3588 芯片运行时挂载"
    echo "services:"
    echo "  video-service:"
    echo "    volumes:"
    echo "      - ${module_dir}:/opt/easyaiot/RUNTIME-RK3588:ro"
    echo "      - ${module_dir}/config:/opt/easyaiot/RUNTIME-RK3588/config:rw"
    if [[ -n "$libs_dir" ]]; then
      echo "      - ${libs_dir}:/opt/easyaiot/RUNTIME-RK3588/lib:ro"
    fi
    if [[ -n "$devices_block" ]]; then
      echo "    devices:"
      printf '%s' "$devices_block"
    else
      print_warning "未检测到 RK3588 设备节点（/dev/rknpu、/dev/rga、/dev/mpp_service、/dev/dma_heap、/dev/dri）"
    fi
    echo "    environment:"
    echo "      - EASYAIOT_RUNTIME_TARGET=rk3588"
    echo "      - RUNTIME_RK3588_BIN=/opt/easyaiot/RUNTIME-RK3588/build/RUNTIME"
    echo "      - RUNTIME_RK3588_CONFIG_DIR=/opt/easyaiot/RUNTIME-RK3588/config"
    echo "      - RUNTIME_BIN="
    echo "      - RUNTIME_CONFIG_DIR="
    echo "      - RUNTIME_RK3588_CLASSES_PATH=${classes_path}"
    if [[ -f "${module_dir}/models/yolov8n-rk3588-int8.rknn" ]]; then
      echo "      - RUNTIME_RK3588_MODEL_PATH=${model_path}"
    fi
    echo "      - LD_LIBRARY_PATH=${ld_path}"
    echo "      - USE_GPU=false"
    echo "      - RUNTIME_PREFER_GPU=false"
  } > "$override_file"

  print_success "已配置 RUNTIME-RK3588 容器挂载 ($override_file)"
}

wire_bm1688_override() {
  local module_dir="${EASYAIOT_ROOT}/RUNTIME-BM1688"
  local override_file="${VIDEO_DIR}/.docker-compose.runtime.override.yaml"
  local env_file="${VIDEO_DIR}/.env.docker"
  local runtime_bin="${module_dir}/build/RUNTIME"

  if [[ ! -x "$runtime_bin" ]]; then
    rm -f "$override_file"
    print_warning "BM1688 运行时未编译: $runtime_bin（已清理旧挂载配置）"
    return 0
  fi
  if [[ ! -f "$env_file" ]]; then
    if [[ -f "${VIDEO_DIR}/env.example" ]]; then cp "${VIDEO_DIR}/env.example" "$env_file"; else touch "$env_file"; fi
  fi
  mkdir -p "${module_dir}/config"
  local libs_dir
  libs_dir="$(stage_bm1688_libs)"
  if [[ -z "$libs_dir" ]]; then
    print_warning "未收集到 BMRuntime/BMCV/Sophon OpenCV 动态库；请确认 SOPHONSDK 已安装"
  fi

  local model_path="/opt/easyaiot/RUNTIME-BM1688/models/yolov8n-bm1688-int8-4b.bmodel"
  local classes_path="/opt/easyaiot/RUNTIME-BM1688/models/coco.names"
  local ld_path="/opt/easyaiot/RUNTIME-BM1688/lib:/opt/sophon/libsophon-current/lib:/opt/sophon/sophon-opencv-latest/lib:/usr/lib/aarch64-linux-gnu"
  _set_env_docker_kv_local "$env_file" EASYAIOT_RUNTIME_TARGET "bm1688"
  _set_env_docker_kv_local "$env_file" RUNTIME_BM1688_BIN "$runtime_bin"
  _set_env_docker_kv_local "$env_file" RUNTIME_BM1688_CONFIG_DIR "/opt/easyaiot/RUNTIME-BM1688/config"
  _set_env_docker_kv_local "$env_file" RUNTIME_BM1688_CLASSES_PATH "$classes_path"
  _set_env_docker_kv_local "$env_file" RUNTIME_RK3588_BIN ""
  _set_env_docker_kv_local "$env_file" RUNTIME_RK3588_CONFIG_DIR ""
  _set_env_docker_kv_local "$env_file" RUNTIME_BIN ""
  _set_env_docker_kv_local "$env_file" RUNTIME_CONFIG_DIR ""
  if [[ -f "${module_dir}/models/yolov8n-bm1688-int8-4b.bmodel" ]]; then
    _set_env_docker_kv_local "$env_file" RUNTIME_BM1688_MODEL_PATH "$model_path"
  else
    _set_env_docker_kv_local "$env_file" RUNTIME_BM1688_MODEL_PATH ""
    print_warning "未找到默认 BModel；请上传 BM1688/CV186X .bmodel 后在 VIDEO 模型管理中选择"
  fi
  _set_env_docker_kv_local "$env_file" LD_LIBRARY_PATH "$ld_path"
  _set_env_docker_kv_local "$env_file" USE_GPU "false"
  _set_env_docker_kv_local "$env_file" RUNTIME_PREFER_GPU "false"

  local devices_block="" dev
  for dev in /dev/bmdev-ctl /dev/bm-sophon0 /dev/ion /dev/vpu /dev/dri; do
    [[ -e "$dev" ]] || continue
    devices_block+="      - ${dev}:${dev}"$'\n'
  done
  {
    echo "# Auto-generated by VIDEO/scripts/ensure_runtime_cpp.sh — RUNTIME-BM1688 芯片运行时挂载"
    echo "services:"
    echo "  video-service:"
    echo "    volumes:"
    echo "      - ${module_dir}:/opt/easyaiot/RUNTIME-BM1688:ro"
    echo "      - ${module_dir}/config:/opt/easyaiot/RUNTIME-BM1688/config:rw"
    if [[ -n "$libs_dir" ]]; then echo "      - ${libs_dir}:/opt/easyaiot/RUNTIME-BM1688/lib:ro"; fi
    if [[ -n "$devices_block" ]]; then
      echo "    devices:"
      printf '%s' "$devices_block"
    else
      print_warning "未检测到 BM1688 设备节点；容器内硬件任务将无法启动"
    fi
    echo "    environment:"
    echo "      - EASYAIOT_RUNTIME_TARGET=bm1688"
    echo "      - RUNTIME_BM1688_BIN=/opt/easyaiot/RUNTIME-BM1688/build/RUNTIME"
    echo "      - RUNTIME_BM1688_CONFIG_DIR=/opt/easyaiot/RUNTIME-BM1688/config"
    echo "      - RUNTIME_BM1688_CLASSES_PATH=${classes_path}"
    if [[ -f "${module_dir}/models/yolov8n-bm1688-int8-4b.bmodel" ]]; then echo "      - RUNTIME_BM1688_MODEL_PATH=${model_path}"; fi
    echo "      - RUNTIME_BIN="
    echo "      - RUNTIME_CONFIG_DIR="
    echo "      - LD_LIBRARY_PATH=${ld_path}"
    echo "      - USE_GPU=false"
    echo "      - RUNTIME_PREFER_GPU=false"
  } > "$override_file"
  print_success "已配置 RUNTIME-BM1688 容器挂载 ($override_file)"
}

wire_generic_runtime_override() {
  local deploy_env="${EASYAIOT_ROOT}/RUNTIME/deploy.env"
  local override_file="${VIDEO_DIR}/.docker-compose.runtime.override.yaml"
  local env_file="${VIDEO_DIR}/.env.docker"

  # 从芯片运行时切回通用运行时时清掉遗留配置。
  if [[ -f "$env_file" ]]; then
    _set_env_docker_kv_local "$env_file" EASYAIOT_RUNTIME_TARGET "generic"
    _set_env_docker_kv_local "$env_file" RUNTIME_RK3588_BIN ""
    _set_env_docker_kv_local "$env_file" RUNTIME_RK3588_CONFIG_DIR ""
    _set_env_docker_kv_local "$env_file" RUNTIME_RK3588_CLASSES_PATH ""
    _set_env_docker_kv_local "$env_file" RUNTIME_RK3588_MODEL_PATH ""
    _set_env_docker_kv_local "$env_file" RUNTIME_BM1688_BIN ""
    _set_env_docker_kv_local "$env_file" RUNTIME_BM1688_CONFIG_DIR ""
    _set_env_docker_kv_local "$env_file" RUNTIME_BM1688_CLASSES_PATH ""
    _set_env_docker_kv_local "$env_file" RUNTIME_BM1688_MODEL_PATH ""
  fi

  if [[ ! -f "$deploy_env" ]]; then
    rm -f "$override_file"
    print_warning "未找到 $deploy_env，跳过 RUNTIME 容器挂载"
    return 0
  fi

  set -a
  # shellcheck disable=SC1090
  source "$deploy_env"
  set +a

  if [[ ! -x "${RUNTIME_BIN:-}" ]]; then
    print_warning "RUNTIME 二进制不可执行: ${RUNTIME_BIN:-}"
    return 0
  fi

  if [[ ! -f "$env_file" ]]; then
    if [[ -f "${VIDEO_DIR}/env.example" ]]; then
      cp "${VIDEO_DIR}/env.example" "$env_file"
    else
      touch "$env_file"
    fi
  fi

  # Only mount a CUDA toolkit dir that contains libcudart.
  # Never mount generic system lib dirs (e.g. /usr/lib/x86_64-linux-gnu) —
  # they contain libc and break the container entrypoint.
  local cuda_host="" cuda_volume_line=""
  if [[ -n "${RUNTIME_CUDA_LIB_HOST:-}" ]]; then
    local cand
    IFS=':' read -r -a _cuda_cands <<< "${RUNTIME_CUDA_LIB_HOST}"
    for cand in "${_cuda_cands[@]}"; do
      [[ -d "$cand" ]] || continue
      case "$cand" in
        /usr/lib|/usr/lib/*|/lib|/lib/*|/usr/lib64|/lib64) continue ;;
      esac
      if compgen -G "${cand}/libcudart.so*" >/dev/null 2>&1; then
        cuda_host="$cand"
        break
      fi
    done
  fi

  local ld_path="/opt/easyaiot/runtime-conda-lib:/opt/easyaiot/ort-lib:/opt/conda/lib/python3.11/site-packages/nvidia/cudnn/lib"
  if [[ -n "$cuda_host" ]]; then
    ld_path="${ld_path}:/opt/easyaiot/cuda-lib"
    cuda_volume_line="      - ${cuda_host}:/opt/easyaiot/cuda-lib:ro"
  fi

  _set_env_docker_kv_local "$env_file" RUNTIME_BIN "/opt/easyaiot/RUNTIME/build/RUNTIME"
  _set_env_docker_kv_local "$env_file" LD_LIBRARY_PATH "$ld_path"
  _set_env_docker_kv_local "$env_file" USE_GPU "${USE_GPU:-true}"
  _set_env_docker_kv_local "$env_file" RUNTIME_PREFER_GPU "${RUNTIME_PREFER_GPU:-true}"
  _set_env_docker_kv_local "$env_file" RUNTIME_HOST_DIR "${RUNTIME_HOST_DIR}"
  _set_env_docker_kv_local "$env_file" RUNTIME_CONDA_LIB_HOST "${RUNTIME_CONDA_LIB_HOST}"
  _set_env_docker_kv_local "$env_file" RUNTIME_ORT_LIB_HOST "${RUNTIME_ORT_LIB_HOST}"
  if [[ -n "$cuda_host" ]]; then
    _set_env_docker_kv_local "$env_file" RUNTIME_CUDA_LIB_HOST "$cuda_host"
  else
    # Clear stale unsafe value from earlier installs
    _set_env_docker_kv_local "$env_file" RUNTIME_CUDA_LIB_HOST ""
  fi

  {
    echo "# Auto-generated by VIDEO/scripts/ensure_runtime_cpp.sh — RUNTIME 高性能执行器挂载"
    echo "services:"
    echo "  video-service:"
    echo "    volumes:"
    echo "      - ${RUNTIME_HOST_DIR}:/opt/easyaiot/RUNTIME:ro"
    echo "      - ${RUNTIME_HOST_DIR}/config:/opt/easyaiot/RUNTIME/config:rw"
    echo "      - ${RUNTIME_CONDA_LIB_HOST}:/opt/easyaiot/runtime-conda-lib:ro"
    echo "      - ${RUNTIME_ORT_LIB_HOST}:/opt/easyaiot/ort-lib:ro"
    if [[ -n "$cuda_volume_line" ]]; then
      echo "$cuda_volume_line"
    fi
    echo "    environment:"
    echo "      - EASYAIOT_RUNTIME_TARGET=generic"
    echo "      - RUNTIME_BIN=/opt/easyaiot/RUNTIME/build/RUNTIME"
    echo "      - LD_LIBRARY_PATH=${ld_path}"
    echo "      - USE_GPU=${USE_GPU:-true}"
    echo "      - RUNTIME_PREFER_GPU=${RUNTIME_PREFER_GPU:-true}"
  } > "$override_file"

  print_success "已配置 RUNTIME 容器挂载 ($override_file)"
}

ensure_rk3588_runtime() {
  local runtime_install="${EASYAIOT_ROOT}/RUNTIME-RK3588/install_linux.sh"
  local runtime_bin="${EASYAIOT_ROOT}/RUNTIME-RK3588/build/RUNTIME"

  if [[ ! -f "$runtime_install" ]]; then
    print_warning "未找到 $runtime_install，跳过 RUNTIME-RK3588 编译"
    return 0
  fi

  if [[ "${EASYAIOT_RUNTIME_PREINSTALLED:-0}" == "1" ]] || [[ -x "$runtime_bin" ]]; then
    print_info "检测到 RUNTIME-RK3588 已编译，仅配置 VIDEO 容器挂载..."
    wire_rk3588_override
    return 0
  fi

  print_info "编译 RUNTIME-RK3588（Rockchip MPP + RGA + 三核 RKNN NPU）..."
  local rt_log="${EASYAIOT_ROOT}/.scripts/docker/logs/runtime_rk3588_$(date +%Y%m%d_%H%M%S).log"
  mkdir -p "$(dirname "$rt_log")" 2>/dev/null || true
  print_info "RUNTIME-RK3588 编译日志: ${rt_log}"
  if ! bash "$runtime_install" build 2>&1 | tee "$rt_log"; then
    print_warning "RUNTIME-RK3588 编译失败：RK3588 硬件任务将不可用，通用/普通算法任务不受影响"
    print_error "========================================"
    print_error "  RUNTIME-RK3588 部署失败 — 详细日志"
    print_error "========================================"
    print_error "完整日志: ${rt_log}"
    print_error "日志末尾 (tail -80):"
    tail -n 80 "$rt_log" 2>/dev/null | while IFS= read -r line; do print_error "  ${line}"; done || true
    print_error "可跳过: EASYAIOT_RUNTIME_SKIP=1"
    print_error "或强制失败: EASYAIOT_RUNTIME_REQUIRED=1"
    rm -f "${VIDEO_DIR}/.docker-compose.runtime.override.yaml"
    if [[ "${EASYAIOT_RUNTIME_REQUIRED:-0}" == "1" ]]; then
      print_error "EASYAIOT_RUNTIME_REQUIRED=1，终止"
      return 1
    fi
    return 0
  fi

  wire_rk3588_override
}

ensure_bm1688_runtime() {
  local runtime_install="${EASYAIOT_ROOT}/RUNTIME-BM1688/install_linux.sh"
  local runtime_bin="${EASYAIOT_ROOT}/RUNTIME-BM1688/build/RUNTIME"
  if [[ ! -f "$runtime_install" ]]; then
    print_warning "未找到 $runtime_install，跳过 RUNTIME-BM1688 编译"
    return 0
  fi
  if [[ "${EASYAIOT_RUNTIME_PREINSTALLED:-0}" == "1" ]] || [[ -x "$runtime_bin" ]]; then
    print_info "检测到 RUNTIME-BM1688 已编译，仅配置 VIDEO 容器挂载..."
    wire_bm1688_override
    return 0
  fi

  print_info "编译 RUNTIME-BM1688（Sophon VPU + BMCV/VPSS + 双核 TPU）..."
  local rt_log="${EASYAIOT_ROOT}/.scripts/docker/logs/runtime_bm1688_$(date +%Y%m%d_%H%M%S).log"
  mkdir -p "$(dirname "$rt_log")" 2>/dev/null || true
  print_info "RUNTIME-BM1688 编译日志: ${rt_log}"
  if ! bash "$runtime_install" build 2>&1 | tee "$rt_log"; then
    print_error "RUNTIME-BM1688 编译失败；不会回退到 ONNX/CPU"
    print_error "完整日志: ${rt_log}"
    tail -n 80 "$rt_log" 2>/dev/null | while IFS= read -r line; do print_error "  ${line}"; done || true
    rm -f "${VIDEO_DIR}/.docker-compose.runtime.override.yaml"
    if [[ "${EASYAIOT_RUNTIME_REQUIRED:-0}" == "1" ]]; then return 1; fi
    return 0
  fi
  wire_bm1688_override
}

ensure_runtime_cpp() {
  if [[ "$(uname -s)" != "Linux" ]]; then
    print_warning "当前系统 $(uname -s) 非 Linux：跳过 RUNTIME（C++/CUDA）一键编译。mac/Windows 请使用普通算法任务，或自行交叉编译。"
    return 0
  fi
  if [[ "${EASYAIOT_RUNTIME_SKIP:-0}" == "1" ]]; then
    print_warning "EASYAIOT_RUNTIME_SKIP=1，跳过 RUNTIME（高性能）编译"
    return 0
  fi

  case "$(detect_runtime_target)" in
    rk3588) ensure_rk3588_runtime; return 0 ;;
    bm1688) ensure_bm1688_runtime; return 0 ;;
  esac

  local runtime_install="${EASYAIOT_ROOT}/RUNTIME/install_linux.sh"
  if [[ ! -f "$runtime_install" ]]; then
    print_warning "未找到 $runtime_install，跳过 RUNTIME 编译"
    return 0
  fi

  # 全量部署已把 RUNTIME 提前编译时，此处仅 wire 挂载，避免重复长编译
  if [[ "${EASYAIOT_RUNTIME_PREINSTALLED:-0}" == "1" ]] \
    || [[ -x "${EASYAIOT_ROOT}/RUNTIME/build/RUNTIME" && -f "${EASYAIOT_ROOT}/RUNTIME/deploy.env" ]]; then
    print_info "检测到 RUNTIME 已编译，仅配置 VIDEO 容器挂载..."
    wire_runtime_override
    return 0
  fi

  print_info "安装/编译 RUNTIME（算法任务高性能执行器，默认 GPU）..."
  local rt_log="${EASYAIOT_ROOT}/.scripts/docker/logs/runtime_cpp_$(date +%Y%m%d_%H%M%S).log"
  mkdir -p "$(dirname "$rt_log")" 2>/dev/null || true
  print_info "RUNTIME 编译日志: ${rt_log}"
  if ! bash "$runtime_install" install 2>&1 | tee "$rt_log"; then
    print_warning "RUNTIME 编译失败：高性能任务将不可用，普通算法任务仍可使用"
    print_error "========================================"
    print_error "  RUNTIME 部署失败 — 详细日志"
    print_error "========================================"
    print_error "完整日志: ${rt_log}"
    print_error "日志末尾 (tail -80):"
    tail -n 80 "$rt_log" 2>/dev/null | while IFS= read -r line; do print_error "  ${line}"; done || true
    print_error "可跳过: EASYAIOT_RUNTIME_SKIP=1"
    print_error "或强制失败: EASYAIOT_RUNTIME_REQUIRED=1"
    rm -f "${VIDEO_DIR}/.docker-compose.runtime.override.yaml"
    if [[ "${EASYAIOT_RUNTIME_REQUIRED:-0}" == "1" ]]; then
      print_error "EASYAIOT_RUNTIME_REQUIRED=1，终止"
      return 1
    fi
    # 默认不阻断 VIDEO 后续部署（其它模块/VIDEO 容器仍可继续）
    return 0
  fi

  wire_runtime_override
}

main() {
  local cmd="${1:-install}"
  case "$cmd" in
    install|"")
      ensure_runtime_cpp
      ;;
    wire)
      wire_runtime_override
      ;;
    help|-h|--help)
      sed -n '2,18p' "$0"
      ;;
    *)
      print_error "未知命令: $cmd"
      exit 1
      ;;
  esac
}

main "$@"
