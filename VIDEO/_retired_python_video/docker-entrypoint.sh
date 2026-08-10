#!/bin/sh
# 容器启动时用当前 Python 解析 pip 安装的 nvidia/*/lib，避免硬编码 site-packages 路径。
set -e

if [ "${_ONNX_NVIDIA_LD_PATH_DONE:-}" != "1" ]; then
  NVIDIA_ORT_LD="$(python -c "
import glob
import os
import site

paths = sorted({
    d
    for root in site.getsitepackages()
    for d in glob.glob(os.path.join(root, 'nvidia', '*', 'lib'))
    if os.path.isdir(d)
})
print(':'.join(paths))
" 2>/dev/null || true)"

  if [ -n "$NVIDIA_ORT_LD" ]; then
    if [ -n "${LD_LIBRARY_PATH:-}" ]; then
      export LD_LIBRARY_PATH="${NVIDIA_ORT_LD}:${LD_LIBRARY_PATH}"
    else
      export LD_LIBRARY_PATH="${NVIDIA_ORT_LD}"
    fi
  fi
  export _ONNX_NVIDIA_LD_PATH_DONE=1
fi

exec "$@"
