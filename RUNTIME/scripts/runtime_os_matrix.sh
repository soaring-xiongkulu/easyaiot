#!/usr/bin/env bash
# ============================================
# RUNTIME 离线包构建矩阵（与 COMPILE/build.sh / pack_all_linux.sh 目标对齐）
#
# 部署侧按节点 os-release → os_family/arch 精确匹配 tarball，与「默认打哪几个包」无关。
# 本文件定义：哪些 {os_family}/{arch} 可构建，以及如何与 COMPILE 打包目标对应。
#
# 用法（被其它脚本 source）:
#   source RUNTIME/scripts/runtime_os_matrix.sh
#   runtime_matrix_list
#   runtime_matrix_image openeuler24 x86_64
#   runtime_matrix_for_compile_target centos-el9
#   runtime_matrix_compile_coverage_keys   # 与 COMPILE pack_all_linux 一致的全覆盖
# ============================================

# os_family:arch -> docker 镜像（可用 RUNTIME_OS_CONTAINER_IMAGE 覆盖单个目标）
declare -gA RUNTIME_MATRIX_IMAGE=(
  ["ubuntu24:x86_64"]="ubuntu:24.04"
  ["ubuntu26:x86_64"]="ubuntu:26.04"
  ["ubuntu24:arm64"]="ubuntu:24.04"
  ["ubuntu26:arm64"]="ubuntu:26.04"
  ["el7:x86_64"]="centos:7"
  ["el8:x86_64"]="rockylinux:8"
  ["el9:x86_64"]="rockylinux:9"
  ["el7:arm64"]="arm64v8/centos:7"
  ["el8:arm64"]="rockylinux:8"
  ["el9:arm64"]="rockylinux:9"
  ["openeuler24:x86_64"]="openeuler/openeuler:24.03-lts"
  # 实机存量（COMPILE 不打 PANEL，但分片节点可能是 22.03）
  ["openeuler22:x86_64"]="openeuler/openeuler:22.03-lts"
  ["openeuler22:arm64"]="openeuler/openeuler:22.03-lts"
  ["openeuler24:arm64"]="openeuler/openeuler:24.03-lts"
  # 麒麟：仅 arm64；暂不纳入默认批量构建（需 RUNTIME_KYLIN10_ARM64_IMAGE + 实机/内网镜像）
  ["kylin10:arm64"]="${RUNTIME_KYLIN10_ARM64_IMAGE:-}"
  ["kylin11:arm64"]="${RUNTIME_KYLIN11_ARM64_IMAGE:-}"
)

# COMPILE build.sh / pack_all_linux.sh 目标 -> RUNTIME 矩阵项（os_family:arch）
declare -gA RUNTIME_COMPILE_TARGET_MAP=(
  ["ubuntu-x86"]="ubuntu24:x86_64 ubuntu26:x86_64"
  ["ubuntu-arm"]="ubuntu24:arm64 ubuntu26:arm64"
  ["ubuntu-kylin"]="kylin10:arm64 kylin11:arm64"
  ["centos-el7"]="el7:x86_64"
  ["centos-el8"]="el8:x86_64"
  ["centos-el9"]="el9:x86_64"
  ["centos"]="el9:x86_64"
  ["centos-arm-el7"]="el7:arm64"
  ["centos-arm-el8"]="el8:arm64"
  ["centos-arm-el9"]="el9:arm64"
  ["centos-arm"]="el9:arm64"
  ["openeuler"]="openeuler24:x86_64"
  ["all-linux"]=""
)

# 默认批量构建顺序（不含 ubuntu-kylin；麒麟需专用镜像，另行 --compile-target ubuntu-kylin）
RUNTIME_COMPILE_PACK_ALL_ORDER=(
  ubuntu-x86
  ubuntu-arm
  centos-el7
  centos-el8
  centos-el9
  centos-arm-el7
  centos-arm-el8
  centos-arm-el9
  openeuler
)

runtime_matrix_key() {
  local os_family="${1:?os_family}"
  local arch="${2:-x86_64}"
  echo "${os_family}:${arch}"
}

runtime_matrix_ort_arch_tag() {
  local arch="${1:-x86_64}"
  case "$arch" in
    arm64|aarch64) echo "aarch64" ;;
    *) echo "x64" ;;
  esac
}

runtime_matrix_ort_version() {
  local os_family="${1:-${RUNTIME_OS_FAMILY:-}}"
  if [[ "$os_family" == "el7" ]]; then
    echo "${RUNTIME_EL7_ORT_VERSION:-1.16.3}"
  else
    echo "${ORT_VERSION:-1.23.2}"
  fi
}

runtime_matrix_ort_deps_dir() {
  local repo="${1:?repo root}"
  local arch="${2:-x86_64}"
  local os_family="${3:-${RUNTIME_OS_FAMILY:-}}"
  local ver tag
  ver="$(runtime_matrix_ort_version "$os_family")"
  tag="$(runtime_matrix_ort_arch_tag "$arch")"
  echo "${repo}/.deps/onnxruntime-linux-${tag}-${ver}"
}

runtime_matrix_image() {
  local os_family="$1" arch="${2:-x86_64}"
  local key
  key="$(runtime_matrix_key "$os_family" "$arch")"
  if [[ -n "${RUNTIME_OS_CONTAINER_IMAGE:-}" ]]; then
    echo "$RUNTIME_OS_CONTAINER_IMAGE"
    return 0
  fi
  echo "${RUNTIME_MATRIX_IMAGE[$key]:-}"
}

runtime_matrix_docker_platform() {
  local arch="${1:-x86_64}"
  case "$arch" in
    arm64|aarch64) echo "linux/arm64" ;;
    *) echo "linux/amd64" ;;
  esac
}

runtime_matrix_list() {
  local k
  for k in $(printf '%s\n' "${!RUNTIME_MATRIX_IMAGE[@]}" | sort); do
    echo "$k -> ${RUNTIME_MATRIX_IMAGE[$k]}"
  done
}

runtime_matrix_for_compile_target() {
  local target="${1:-}"
  if [[ "$target" == "all-linux" ]]; then
    runtime_matrix_compile_coverage_keys
    return 0
  fi
  echo "${RUNTIME_COMPILE_TARGET_MAP[$target]:-}"
}

runtime_matrix_compile_coverage_keys() {
  local target keys item seen=""
  for target in "${RUNTIME_COMPILE_PACK_ALL_ORDER[@]}"; do
    keys="$(runtime_matrix_for_compile_target "$target")"
    for item in $keys; do
      [[ -z "$item" ]] && continue
      case " $seen " in
        *" $item "*) ;;
        *) seen+="$item " ;;
      esac
    done
  done
  echo "$seen"
}

runtime_matrix_all_keys() {
  printf '%s\n' "${!RUNTIME_MATRIX_IMAGE[@]}" | sort -u
}

# 当前节点 os_family:arch 是否在 RUNTIME 覆盖矩阵内（镜像非空）
runtime_matrix_is_supported() {
  local os_family="${1:-$(runtime_detect_os_family)}"
  local arch="${2:-$(runtime_arch_key)}"
  local key img
  key="$(runtime_matrix_key "$os_family" "$arch")"
  img="$(runtime_matrix_image "$os_family" "$arch")"
  if [[ -z "$img" ]]; then
    return 1
  fi
  return 0
}

runtime_matrix_assert_supported() {
  local os_family="${1:-$(runtime_detect_os_family)}"
  local arch="${2:-$(runtime_arch_key)}"
  if runtime_matrix_is_supported "$os_family" "$arch"; then
    return 0
  fi
  echo "[RUNTIME] 不支持的操作系统: os_family=${os_family} arch=${arch}" >&2
  echo "[RUNTIME] 当前 RUNTIME 矩阵覆盖:" >&2
  runtime_matrix_list | sed 's/^/  /' >&2
  if [[ "$os_family" == kylin* ]]; then
    echo "[RUNTIME] 麒麟需设置专用镜像，例如:" >&2
    echo "  export RUNTIME_KYLIN10_ARM64_IMAGE=<kylin-v10-sp3-arm64-image>" >&2
  fi
  return 1
}

runtime_matrix_ort_archs_for_keys() {
  local keys="$1" item arch seen=""
  for item in $keys; do
    arch="${item##*:}"
    case " $seen " in
      *" $arch "*) ;;
      *) seen+="$arch " ;;
    esac
  done
  echo "$seen"
}
