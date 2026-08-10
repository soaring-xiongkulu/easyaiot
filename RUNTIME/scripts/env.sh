#!/usr/bin/env bash
# Activate RUNTIME build/run environment (conda + ONNX Runtime SDK).
# Usage: source RUNTIME/scripts/env.sh

_REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
_ARCH="$(uname -m)"
case "$_ARCH" in
  x86_64|amd64) _ARCH_TAG=x64 ;;
  aarch64|arm64) _ARCH_TAG=aarch64 ;;
  *) _ARCH_TAG=x64 ;;
esac
_ORT="${ORT_ROOT:-$_REPO/.deps/onnxruntime-linux-${_ARCH_TAG}-1.23.2}"

_find_conda_sh() {
  local c
  for c in \
    "$HOME/miniconda3/etc/profile.d/conda.sh" \
    "$HOME/anaconda3/etc/profile.d/conda.sh" \
    /opt/conda/etc/profile.d/conda.sh \
    /usr/local/miniconda3/etc/profile.d/conda.sh \
    /home/ubuntu/miniconda3/etc/profile.d/conda.sh
  do
    [[ -f "$c" ]] && { echo "$c"; return 0; }
  done
  if command -v conda >/dev/null 2>&1; then
    local base
    base="$(conda info --base 2>/dev/null || true)"
    [[ -n "$base" && -f "$base/etc/profile.d/conda.sh" ]] && { echo "$base/etc/profile.d/conda.sh"; return 0; }
  fi
  return 1
}

if _CS="$(_find_conda_sh)"; then
  # shellcheck disable=SC1090
  source "$_CS"
  conda activate "${EASYAIOT_RUNTIME_CONDA_ENV:-easyaiot-runtime}" 2>/dev/null || true
fi

export ORT_ROOT="$_ORT"
if [[ -n "${CONDA_PREFIX:-}" ]]; then
  export LD_LIBRARY_PATH="${CONDA_PREFIX}/lib:${_ORT}/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
  export PKG_CONFIG_PATH="${CONDA_PREFIX}/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
  export CMAKE_PREFIX_PATH="${CONDA_PREFIX}${CMAKE_PREFIX_PATH:+:$CMAKE_PREFIX_PATH}"
fi
export RUNTIME_BIN="${RUNTIME_BIN:-$_REPO/RUNTIME/build/RUNTIME}"
export EASYAIOT_ROOT="${EASYAIOT_ROOT:-$_REPO}"
export RUNTIME_ROOT="${RUNTIME_ROOT:-$_REPO/RUNTIME}"
# Prefer a Python with ultralytics for .pt→onnx (override as needed)
if [[ -z "${RUNTIME_PYTHON:-}" ]]; then
  for _py in \
    "$HOME/miniconda3/bin/python" \
    /home/ubuntu/miniconda3/bin/python \
    "$HOME/anaconda3/bin/python"
  do
    if [[ -x "$_py" ]] && "$_py" -c "import ultralytics" >/dev/null 2>&1; then
      export RUNTIME_PYTHON="$_py"
      break
    fi
  done
fi

echo "RUNTIME env ready"
echo "  CONDA_PREFIX=${CONDA_PREFIX:-}"
echo "  RUNTIME_BIN=$RUNTIME_BIN"
echo "  ORT_ROOT=$ORT_ROOT"
echo "  RUNTIME_PYTHON=${RUNTIME_PYTHON:-}"
