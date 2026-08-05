#!/usr/bin/env bash
# CentOS/RHEL 系 EL 版本解析（供 platforms/centos 与 centos-arm 共用）
# 用法: source el_common.sh && centos_resolve_el 7|8|9
#
# 基础镜像默认优先国内易拉的 Rocky/CentOS 标签；包源由 setup_cn_mirrors.sh 切华为云等。

centos_resolve_el() {
  local el="${1:-${EL_RELEASE:-9}}"
  case "$el" in
    7|el7|centos7)
      EL_RELEASE=7
      ;;
    8|el8|centos8|stream8)
      EL_RELEASE=8
      ;;
    9|el9|centos9|stream9|"")
      EL_RELEASE=9
      ;;
    *)
      echo "[COMPILE/centos] 不支持的 EL 版本: ${el}（仅 7|8|9）" >&2
      return 1
      ;;
  esac

  DIST_TAG="el${EL_RELEASE}"
  # 可选：COMPILE_CN_REGISTRY=docker.1panel.live 等前缀加速拉镜像
  local reg="${COMPILE_CN_REGISTRY:-}"
  local prefix=""
  if [ -n "$reg" ]; then
    prefix="${reg%/}/"
  fi

  case "$EL_RELEASE" in
    7)
      if [ "${PANEL_ARCH:-}" = "aarch64" ]; then
        BASE_IMAGE_DEFAULT="${COMPILE_CENTOS_EL7_BASE_IMAGE:-${prefix}arm64v8/centos:7}"
      else
        BASE_IMAGE_DEFAULT="${COMPILE_CENTOS_EL7_BASE_IMAGE:-${prefix}centos:7}"
      fi
      ;;
    8)
      BASE_IMAGE_DEFAULT="${COMPILE_CENTOS_EL8_BASE_IMAGE:-${prefix}rockylinux:8}"
      ;;
    9)
      BASE_IMAGE_DEFAULT="${COMPILE_CENTOS_EL9_BASE_IMAGE:-${COMPILE_CENTOS_BASE_IMAGE:-${prefix}rockylinux:9}}"
      ;;
  esac

  EL_OUT_SUFFIX="el${EL_RELEASE}"
  export EL_RELEASE DIST_TAG BASE_IMAGE_DEFAULT EL_OUT_SUFFIX
  export PANEL_DIST_TAG="${PANEL_DIST_TAG:-${DIST_TAG}}"
  export PANEL_PUBLISH_OS="${PANEL_PUBLISH_OS:-${DIST_TAG}}"
}

centos_el_help_lines() {
  cat <<'EOF'
  --el7|--el8|--el9     指定 RHEL 兼容大版本（默认 el9）
环境变量:
  COMPILE_CN_MIRROR            包源：huawei（默认）|aliyun|tuna
  COMPILE_CN_REGISTRY          可选镜像前缀，如 docker.1panel.live
  COMPILE_CENTOS_EL7_BASE_IMAGE  默认 centos:7（ARM: arm64v8/centos:7）
  COMPILE_CENTOS_EL8_BASE_IMAGE  默认 rockylinux:8
  COMPILE_CENTOS_EL9_BASE_IMAGE  默认 rockylinux:9
  PANEL_DIST_TAG / PANEL_PUBLISH_OS  覆盖 RPM dist 标签（默认 el7/el8/el9）
EOF
}
