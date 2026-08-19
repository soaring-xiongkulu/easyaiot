#!/usr/bin/env bash
# ============================================
# 在计算节点安装 RUNTIME C++ 离线包（iot-node SSH 上传后执行）
# ============================================
# 用法:
#   bash install_runtime_cpp.sh /opt/easyaiot/RUNTIME /path/to/easyaiot-runtime-x86_64.tar.gz
#   （目标目录无写权限时自动 sudo）
# ============================================
set -euo pipefail

INSTALL_DIR="${1:-/opt/easyaiot/RUNTIME}"
TAR_PATH="${2:-}"

if [[ -z "${TAR_PATH}" || ! -f "${TAR_PATH}" ]]; then
  echo "INSTALL_FAIL: 缺少 RUNTIME tarball: ${TAR_PATH}" >&2
  exit 1
fi

need_priv=0
parent="$(dirname "$INSTALL_DIR")"
if [[ -e "$INSTALL_DIR" ]]; then
  [[ -w "$INSTALL_DIR" ]] || need_priv=1
elif [[ ! -w "$parent" ]]; then
  need_priv=1
fi

run_as() {
  if [[ "$need_priv" -eq 1 ]]; then
    sudo "$@"
  else
    "$@"
  fi
}

echo "==> 安装 RUNTIME 至 ${INSTALL_DIR} (priv=${need_priv})"
run_as mkdir -p "${INSTALL_DIR}"

RUNTIME_INSTALL_WORK="$(mktemp -d)"
trap 'rm -rf "${RUNTIME_INSTALL_WORK:-}"' EXIT

tar -xzf "${TAR_PATH}" -C "${RUNTIME_INSTALL_WORK}"
inner="$(find "${RUNTIME_INSTALL_WORK}" -maxdepth 1 -type d -name 'easyaiot-runtime-*' | head -1)"
if [[ -z "${inner}" || ! -x "${inner}/bin/RUNTIME" ]]; then
  echo "INSTALL_FAIL: tarball 结构异常（缺少 bin/RUNTIME）" >&2
  exit 1
fi

run_as mkdir -p "${INSTALL_DIR}/bin" "${INSTALL_DIR}/lib" "${INSTALL_DIR}/config" "${INSTALL_DIR}/models" "${INSTALL_DIR}/scripts" "${INSTALL_DIR}/cache"
run_as cp -f "${inner}/bin/RUNTIME" "${INSTALL_DIR}/bin/RUNTIME"
run_as chmod +x "${INSTALL_DIR}/bin/RUNTIME"
if [[ -d "${inner}/lib" ]]; then
  # 全量替换 lib，避免旧包残留 symlink 导致 cp -a 失败（openEuler 常见）
  run_as rm -rf "${INSTALL_DIR}/lib"
  run_as mkdir -p "${INSTALL_DIR}/lib"
  run_as cp -a "${inner}/lib/." "${INSTALL_DIR}/lib/"
fi
if [[ -f "${inner}/env.sh" ]]; then
  run_as cp -f "${inner}/env.sh" "${INSTALL_DIR}/env.sh"
  run_as chmod +x "${INSTALL_DIR}/env.sh"
fi
if [[ -d "${inner}/models" ]]; then
  run_as cp -a "${inner}/models/." "${INSTALL_DIR}/models/" 2>/dev/null || true
fi
if [[ -d "${inner}/scripts" ]]; then
  run_as cp -a "${inner}/scripts/." "${INSTALL_DIR}/scripts/" 2>/dev/null || true
fi
if [[ -f "${INSTALL_DIR}/scripts/smoke_runtime.sh" ]]; then
  run_as chmod +x "${INSTALL_DIR}/scripts/smoke_runtime.sh" || true
fi
# 兼容旧包：只有 yolov11n.onnx 时补规范名
if [[ ! -f "${INSTALL_DIR}/models/yolo11n.onnx" && -f "${INSTALL_DIR}/models/yolov11n.onnx" ]]; then
  run_as cp -f "${INSTALL_DIR}/models/yolov11n.onnx" "${INSTALL_DIR}/models/yolo11n.onnx" || true
fi
if [[ -f "${inner}/VERSION" ]]; then
  run_as cp -f "${inner}/VERSION" "${INSTALL_DIR}/VERSION"
  # 标记安装来源，保留 version/git 等字段
  if grep -q '^source=' "${INSTALL_DIR}/VERSION" 2>/dev/null; then
    run_as sed -i 's/^source=.*/source=atomic-install/' "${INSTALL_DIR}/VERSION" 2>/dev/null \
      || run_as sed -i '' 's/^source=.*/source=atomic-install/' "${INSTALL_DIR}/VERSION" 2>/dev/null \
      || true
  else
    echo "source=atomic-install" | run_as tee -a "${INSTALL_DIR}/VERSION" >/dev/null
  fi
fi

# profile.d 便于交互式调试；工作负载通过 env 注入（无权限则跳过）
if [[ -d /etc/profile.d ]]; then
  if [[ "$need_priv" -eq 1 ]] || [[ -w /etc/profile.d ]]; then
    run_as tee /etc/profile.d/easyaiot-runtime.sh > /dev/null <<PROFILE
export RUNTIME_BIN="${INSTALL_DIR}/bin/RUNTIME"
export PATH="${INSTALL_DIR}/bin:\${PATH}"
# 不要把 RUNTIME/lib 放进全局 LD_LIBRARY_PATH：其中的 libresolv 会污染 sudo/系统动态链接器。
# 运行 RUNTIME 时 source ${INSTALL_DIR}/env.sh
PROFILE
  fi
fi

run_as tee "${INSTALL_DIR}/.installed" > /dev/null <<EOF
installed_at=$(date -Iseconds 2>/dev/null || date)
tar=${TAR_PATH}
EOF

if [[ ! -x "${INSTALL_DIR}/bin/RUNTIME" ]]; then
  echo "INSTALL_FAIL: 安装后二进制不可执行" >&2
  exit 1
fi

# 真正能 exec 才算装好：文件存在 / ldd 前几行不够。
SMOKE="${INSTALL_DIR}/scripts/smoke_runtime.sh"
if [[ -f "$SMOKE" ]]; then
  if ! bash "$SMOKE" "${INSTALL_DIR}"; then
    echo "INSTALL_FAIL: RUNTIME 在本节点无法执行 --version（OS/ABI 包不匹配或动态库缺失）" >&2
    exit 1
  fi
else
  echo "INSTALL_WARN: 包内无 smoke_runtime.sh，回退 env.sh + --version" >&2
  unset LD_LIBRARY_PATH LD_PRELOAD
  # shellcheck disable=SC1091
  if [[ -f "${INSTALL_DIR}/env.sh" ]]; then
    # shellcheck disable=SC1090
    . "${INSTALL_DIR}/env.sh"
  fi
  if ! "${INSTALL_DIR}/bin/RUNTIME" --version >/dev/null 2>&1; then
    echo "INSTALL_FAIL: RUNTIME --version 失败" >&2
    "${INSTALL_DIR}/bin/RUNTIME" --version || true
    exit 1
  fi
fi

if [[ -f "${INSTALL_DIR}/node.env" ]]; then
  echo "INSTALL_INFO: 检测到原子模式 node.env（VIDEO 汇聚面已配置）"
elif [[ -n "${VIDEO_BASE_URL:-${EASYAIOT_VIDEO_BASE_URL:-}}" ]]; then
  echo "INSTALL_INFO: 未写 node.env；可用 VIDEO_BASE_URL=... ./RUNTIME/install_linux.sh atomic 补齐汇聚面配置"
fi

echo "RUNTIME_OK: ${INSTALL_DIR}/bin/RUNTIME"
if [[ -f "${INSTALL_DIR}/VERSION" ]]; then
  echo "RUNTIME_VERSION_FILE:"
  cat "${INSTALL_DIR}/VERSION" || true
  ver_line="$(grep -E '^version=' "${INSTALL_DIR}/VERSION" 2>/dev/null | head -1 || true)"
  [[ -n "$ver_line" ]] && echo "RUNTIME_VERSION=${ver_line#version=}"
fi
ls -la "${INSTALL_DIR}/bin/RUNTIME"
