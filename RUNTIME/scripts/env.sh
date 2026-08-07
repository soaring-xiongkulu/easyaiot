#!/usr/bin/env bash
# Activate RUNTIME build/run environment (conda + ONNX Runtime SDK).
# Usage: source RUNTIME/scripts/env.sh

_REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
_ORT="${ORT_ROOT:-$_REPO/.deps/onnxruntime-linux-x64-1.23.2}"

if [[ -f /home/ubuntu/miniconda3/etc/profile.d/conda.sh ]]; then
  # shellcheck disable=SC1091
  source /home/ubuntu/miniconda3/etc/profile.d/conda.sh
  conda activate easyaiot-runtime
fi

export ORT_ROOT="$_ORT"
export LD_LIBRARY_PATH="${CONDA_PREFIX}/lib:${_ORT}/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PKG_CONFIG_PATH="${CONDA_PREFIX}/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
export CMAKE_PREFIX_PATH="${CONDA_PREFIX}${CMAKE_PREFIX_PATH:+:$CMAKE_PREFIX_PATH}"
export RUNTIME_BIN="${RUNTIME_BIN:-$_REPO/RUNTIME/build/RUNTIME}"

echo "RUNTIME env ready"
echo "  CONDA_PREFIX=$CONDA_PREFIX"
echo "  RUNTIME_BIN=$RUNTIME_BIN"
echo "  ORT_ROOT=$ORT_ROOT"
