#!/usr/bin/env bash
# RUNTIME C++ 离线包矩阵 / 预检 — 供 install_linux*.sh 复用

runtime_cpp_bundle_repo_root() {
  local here
  here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  cd "$here/../.." && pwd
}

runtime_cpp_build_matrix() {
  local root script
  root="$(runtime_cpp_bundle_repo_root)"
  script="$root/RUNTIME/build_runtime_matrix.sh"
  if [[ ! -f "$script" ]]; then
    echo "[runtime-cpp] 未找到 $script" >&2
    return 1
  fi
  bash "$script" "$@"
}

runtime_cpp_preflight_bundle() {
  local root script
  root="$(runtime_cpp_bundle_repo_root)"
  script="$root/RUNTIME/scripts/preflight_runtime_bundle.sh"
  if [[ ! -f "$script" ]]; then
    echo "[runtime-cpp] 未找到 $script" >&2
    return 1
  fi
  bash "$script" "$@"
}

runtime_cpp_verify_matrix() {
  local root script
  root="$(runtime_cpp_bundle_repo_root)"
  script="$root/RUNTIME/scripts/verify_runtime_compile_matrix.sh"
  if [[ ! -f "$script" ]]; then
    echo "[runtime-cpp] 未找到 $script" >&2
    return 1
  fi
  bash "$script" "$@"
}

runtime_cpp_export_one() {
  local root script os_family
  root="$(runtime_cpp_bundle_repo_root)"
  os_family="${1:?os_family}"
  script="$root/RUNTIME/scripts/export_runtime_os_container.sh"
  if [[ ! -f "$script" ]]; then
    echo "[runtime-cpp] 未找到 $script" >&2
    return 1
  fi
  bash "$script" "$os_family" "${@:2}"
}

runtime_cpp_bundle_usage() {
  cat <<'EOF'
RUNTIME C++ 离线包（与 COMPILE pack_all_linux 矩阵对齐）:

  build-runtime-cpp [--compile-target NAME|--all]
      批量在目标 OS 容器内编译并导出 tarball
      无参数 = --compile-target all-linux（与 COMPILE pack-all 覆盖一致）
      例: build-runtime-cpp --compile-target openeuler
          build-runtime-cpp --compile-target ubuntu-arm
          build-runtime-cpp --all

  preflight-runtime-cpp [--compile-coverage | --node N | os_family [arch]]
      分发前预检：Docker、ORT、本地 tarball
      无参数 = --compile-coverage（COMPILE 全覆盖）
      例: preflight-runtime-cpp --node 5
          preflight-runtime-cpp openeuler24 x86_64

  verify-runtime-cpp [--check-tarballs]
      验证 RUNTIME 矩阵与 COMPILE 映射一致（不构建）

  export-runtime-cpp <os_family>
      单 OS 容器内导出（如 openeuler24 / kylin10）

麒麟 RUNTIME 与 openEuler 不混用；需设置 RUNTIME_KYLIN10_ARM64_IMAGE 或使用实机 kylin 编译。
EOF
}
