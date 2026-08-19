#!/usr/bin/env bash
# ============================================
# 真正拉起 RUNTIME --version。文件存在不算就绪。
# CUDA 驱动库缺失视为 CPU 可用；glibc / libstdc++ / 其它 .so 缺失则失败。
#
# 用法:
#   bash smoke_runtime.sh [/opt/easyaiot/RUNTIME]
# ============================================
set -u

ROOT="${1:-}"
if [[ -z "$ROOT" ]]; then
  ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

BIN="${RUNTIME_BIN:-$ROOT/bin/RUNTIME}"
ENV_SH="$ROOT/env.sh"

if [[ ! -x "$BIN" ]]; then
  echo "SMOKE_FAIL: 二进制不存在或不可执行: $BIN" >&2
  exit 1
fi

unset LD_LIBRARY_PATH LD_PRELOAD
if [[ -f "$ENV_SH" ]]; then
  # shellcheck disable=SC1090
  . "$ENV_SH"
fi

cuda_noise='libcuda\.so|libcudart|libcublas|libcudnn|libnvinfer|libnvrtc|libnvidia'

if command -v ldd >/dev/null 2>&1; then
  miss="$(ldd "$BIN" 2>/dev/null | grep 'not found' | grep -Ev "$cuda_noise" || true)"
  if [[ -n "$miss" ]]; then
    echo "SMOKE_FAIL: 动态库缺失（非 CUDA）:" >&2
    echo "$miss" >&2
    exit 2
  fi
fi

out="$("$BIN" --version 2>&1)" || true
ec=$?
echo "$out"

if [[ "$ec" -eq 0 ]]; then
  echo "SMOKE_OK: $BIN"
  exit 0
fi

# 动态链接器失败
if echo "$out" | grep -Eqi 'not found|GLIBCXX_|CXXABI_|GLIBC_'; then
  if echo "$out" | grep -Ev "$cuda_noise" | grep -Eqi 'not found|GLIBCXX_|CXXABI_|GLIBC_'; then
    echo "SMOKE_FAIL: 无法执行 --version (exit=$ec)" >&2
    exit 3
  fi
  echo "SMOKE_OK: $BIN（仅缺 CUDA 驱动库，可作 CPU 执行器）"
  exit 0
fi

if [[ "$ec" -eq 127 ]]; then
  echo "SMOKE_FAIL: 无法执行 --version (exit=127)" >&2
  exit 3
fi

# --version 正常应返回 0；其它退出码也视为不可用
echo "SMOKE_FAIL: --version 退出码 $ec" >&2
exit 3
