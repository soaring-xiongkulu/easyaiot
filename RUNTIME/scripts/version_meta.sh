#!/usr/bin/env bash
# ============================================
# RUNTIME 版本元数据（供 install / export / build 共用）
# 版本号完全由 git 自动生成，无手工维护文件。
# 写出 key=value VERSION 文件；勿直接当入口脚本执行业务。
# ============================================

# 调用方需已设置 ROOT（RUNTIME 目录）与可选 REPO
# 导出: RUNTIME_VERSION / RUNTIME_GIT / RUNTIME_BUILT_AT / RUNTIME_ARCH_KEY

runtime_resolve_version_meta() {
  local root="${1:-${ROOT:-}}"
  local repo="${2:-${REPO:-}}"
  if [[ -z "$root" ]]; then
    root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  fi
  if [[ -z "$repo" ]]; then
    repo="$(cd "$root/.." && pwd)"
  fi

  local git_short="unknown"
  local version="unknown"
  if command -v git >/dev/null 2>&1 && [[ -d "$repo/.git" || -f "$repo/.git" ]]; then
    git_short="$(git -C "$repo" rev-parse --short HEAD 2>/dev/null || true)"
    [[ -n "$git_short" ]] || git_short="unknown"
    # 优先 git describe（有 tag 则带上）；否则 g{short}；工作区脏则加 -dirty
    local described
    described="$(git -C "$repo" describe --tags --always --dirty 2>/dev/null || true)"
    if [[ -n "$described" ]]; then
      version="$described"
    elif [[ "$git_short" != "unknown" ]]; then
      version="g${git_short}"
      if ! git -C "$repo" diff --quiet 2>/dev/null \
        || ! git -C "$repo" diff --cached --quiet 2>/dev/null; then
        version="${version}-dirty"
      fi
    fi
  fi

  local arch_key
  case "$(uname -m)" in
    aarch64|arm64) arch_key="arm64" ;;
    *) arch_key="x86_64" ;;
  esac

  RUNTIME_GIT="$git_short"
  RUNTIME_BUILT_AT="$(date -Iseconds 2>/dev/null || date)"
  RUNTIME_ARCH_KEY="$arch_key"
  RUNTIME_VERSION="$version"
  export RUNTIME_VERSION RUNTIME_GIT RUNTIME_BUILT_AT RUNTIME_ARCH_KEY
}

runtime_write_version_file() {
  local dest="$1"
  local source_tag="${2:-local-build}"
  local bin_path="${3:-}"
  local ort_hint="${4:-${ORT_ROOT:-${RUNTIME_ORT_LIB_HOST:-}}}"
  local build_mode="${5:-${BUILD_MODE:-${EASYAIOT_RUNTIME_BUILD_MODE:-}}}"

  if [[ -z "${RUNTIME_VERSION:-}" ]]; then
    runtime_resolve_version_meta "${ROOT:-}" "${REPO:-}"
  fi

  mkdir -p "$(dirname "$dest")"
  cat > "$dest" <<EOF
version=${RUNTIME_VERSION}
git=${RUNTIME_GIT}
built_at=${RUNTIME_BUILT_AT}
arch=${RUNTIME_ARCH_KEY}
build_mode=${build_mode}
ort=${ort_hint}
source=${source_tag}
source_bin=${bin_path}
EOF
}
