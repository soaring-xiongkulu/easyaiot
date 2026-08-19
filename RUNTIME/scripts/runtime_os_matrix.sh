#!/usr/bin/env bash
# ============================================
# RUNTIME 离线包构建矩阵（与 COMPILE/build.sh 目标对齐）
#
# 用法（被其它脚本 source）:
#   source RUNTIME/scripts/runtime_os_matrix.sh
#   runtime_matrix_list          # 列出全部 os_family/arch
#   runtime_matrix_image openeuler22 x86_64
#   runtime_matrix_for_compile_target centos-el9
# ============================================

# os_family:arch -> docker 镜像（可用 RUNTIME_OS_CONTAINER_IMAGE 覆盖单个目标）
# 与 COMPILE/platforms/pack_all_linux.sh 覆盖范围一致；另补 openeuler22（实机常见，COMPILE 默认仅 24.03）
declare -gA RUNTIME_MATRIX_IMAGE=(
  ["ubuntu24:x86_64"]="ubuntu:24.04"
  ["ubuntu26:x86_64"]="ubuntu:26.04"
  ["ubuntu24:arm64"]="ubuntu:24.04"
  ["ubuntu26:arm64"]="ubuntu:26.04"
  ["debian12:x86_64"]="debian:12"
  ["el7:x86_64"]="centos:7"
  ["el8:x86_64"]="rockylinux:8"
  ["el9:x86_64"]="rockylinux:9"
  ["el7:arm64"]="arm64v8/centos:7"
  ["el8:arm64"]="rockylinux:8"
  ["el9:arm64"]="rockylinux:9"
  ["openeuler22:x86_64"]="openeuler/openeuler:22.03-lts"
  ["openeuler24:x86_64"]="openeuler/openeuler:24.03-lts"
  ["openeuler22:arm64"]="openeuler/openeuler:22.03-lts"
  ["openeuler24:arm64"]="openeuler/openeuler:24.03-lts"
  # 麒麟：与 openEuler 分开；须设置专用镜像（不可混用 openEuler 包）
  # 例: export RUNTIME_KYLIN10_ARM64_IMAGE=registry.kylinos.cn/kylin/kylin-server-v10:sp3-2403
  ["kylin10:arm64"]="${RUNTIME_KYLIN10_ARM64_IMAGE:-}"
  ["kylin10:x86_64"]="${RUNTIME_KYLIN10_X86_64_IMAGE:-}"
  ["kylin11:arm64"]="${RUNTIME_KYLIN11_ARM64_IMAGE:-}"
  ["kylin11:x86_64"]="${RUNTIME_KYLIN11_X86_64_IMAGE:-}"
)

# COMPILE build.sh 目标 -> RUNTIME 矩阵项（os_family:arch）
declare -gA RUNTIME_COMPILE_TARGET_MAP=(
  ["ubuntu-x86"]="ubuntu24:x86_64 ubuntu26:x86_64"
  ["ubuntu-arm"]="ubuntu24:arm64"
  ["ubuntu-kylin"]="kylin10:arm64 kylin11:arm64"
  ["centos-el7"]="el7:x86_64"
  ["centos-el8"]="el8:x86_64"
  ["centos-el9"]="el9:x86_64"
  ["centos-arm-el7"]="el7:arm64"
  ["centos-arm-el8"]="el8:arm64"
  ["centos-arm-el9"]="el9:arm64"
  ["openeuler"]="openeuler24:x86_64 openeuler22:x86_64"
)

# 默认「实验室节点 + 控制面」优先打的包（可 RUNTIME_MATRIX_DEFAULT 覆盖）
RUNTIME_MATRIX_DEFAULT="${RUNTIME_MATRIX_DEFAULT:-openeuler22:x86_64 ubuntu26:x86_64 el9:x86_64}"

runtime_matrix_key() {
  local os_family="${1:?os_family}"
  local arch="${2:-x86_64}"
  echo "${os_family}:${arch}"
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
  echo "${RUNTIME_COMPILE_TARGET_MAP[$target]:-}"
}

runtime_matrix_all_keys() {
  printf '%s\n' "${!RUNTIME_MATRIX_IMAGE[@]}" | sort -u
}

runtime_matrix_default_keys() {
  echo "$RUNTIME_MATRIX_DEFAULT"
}
