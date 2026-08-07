#!/usr/bin/env bash
# ============================================
# 在计算节点安装 RUNTIME C++ 离线包（iot-node SSH 上传后执行）
# ============================================
# 用法:
#   sudo bash install_runtime_cpp.sh /opt/easyaiot/RUNTIME /path/to/easyaiot-runtime-x86_64.tar.gz
# ============================================
set -euo pipefail

INSTALL_DIR="${1:-/opt/easyaiot/RUNTIME}"
TAR_PATH="${2:-}"

if [[ -z "${TAR_PATH}" || ! -f "${TAR_PATH}" ]]; then
  echo "INSTALL_FAIL: 缺少 RUNTIME tarball: ${TAR_PATH}" >&2
  exit 1
fi

echo "==> 安装 RUNTIME 至 ${INSTALL_DIR}"
sudo mkdir -p "${INSTALL_DIR}"
work="$(mktemp -d)"
trap 'rm -rf "${work}"' EXIT

tar -xzf "${TAR_PATH}" -C "${work}"
inner="$(find "${work}" -maxdepth 1 -type d -name 'easyaiot-runtime-*' | head -1)"
if [[ -z "${inner}" || ! -x "${inner}/bin/RUNTIME" ]]; then
  echo "INSTALL_FAIL: tarball 结构异常（缺少 bin/RUNTIME）" >&2
  exit 1
fi

sudo mkdir -p "${INSTALL_DIR}/bin" "${INSTALL_DIR}/lib" "${INSTALL_DIR}/config" "${INSTALL_DIR}/models" "${INSTALL_DIR}/cache"
sudo cp -f "${inner}/bin/RUNTIME" "${INSTALL_DIR}/bin/RUNTIME"
sudo chmod +x "${INSTALL_DIR}/bin/RUNTIME"
if [[ -d "${inner}/lib" ]]; then
  sudo cp -a "${inner}/lib/." "${INSTALL_DIR}/lib/"
fi
if [[ -f "${inner}/env.sh" ]]; then
  sudo cp -f "${inner}/env.sh" "${INSTALL_DIR}/env.sh"
  sudo chmod +x "${INSTALL_DIR}/env.sh"
fi
if [[ -d "${inner}/models" ]]; then
  sudo cp -a "${inner}/models/." "${INSTALL_DIR}/models/" 2>/dev/null || true
fi
if [[ -f "${inner}/VERSION" ]]; then
  sudo cp -f "${inner}/VERSION" "${INSTALL_DIR}/VERSION"
fi

# profile.d 便于交互式调试；工作负载通过 env 注入
if [[ -d /etc/profile.d ]]; then
  sudo tee /etc/profile.d/easyaiot-runtime.sh > /dev/null <<PROFILE
export RUNTIME_BIN="${INSTALL_DIR}/bin/RUNTIME"
export LD_LIBRARY_PATH="${INSTALL_DIR}/lib:\${LD_LIBRARY_PATH:-}"
PROFILE
fi

sudo tee "${INSTALL_DIR}/.installed" > /dev/null <<EOF
installed_at=$(date -Iseconds 2>/dev/null || date)
tar=${TAR_PATH}
EOF

if [[ ! -x "${INSTALL_DIR}/bin/RUNTIME" ]]; then
  echo "INSTALL_FAIL: 安装后二进制不可执行" >&2
  exit 1
fi

# 轻量自检：能加载动态库即可（不跑模型）
if command -v ldd >/dev/null 2>&1; then
  if ldd "${INSTALL_DIR}/bin/RUNTIME" 2>&1 | grep -q "not found"; then
    echo "INSTALL_WARN: 仍有未解析动态库（节点可能缺 CUDA 系统库，运行时将回退 CPU）:" >&2
    ldd "${INSTALL_DIR}/bin/RUNTIME" 2>&1 | grep "not found" || true
  fi
fi

echo "RUNTIME_OK: ${INSTALL_DIR}/bin/RUNTIME"
ls -la "${INSTALL_DIR}/bin/RUNTIME"
