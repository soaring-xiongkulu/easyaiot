#!/usr/bin/env bash
# 计算节点工作负载离线 Python 运行时安装（目标机无外网）
# 由 iot-node SSH 同步后在目标机执行: sudo bash install_node_bundle_env.sh
set -euo pipefail

# RUNTIME 可能把专用 lib 写进 LD_LIBRARY_PATH，sudo 会因此无法加载插件
unset LD_LIBRARY_PATH LD_PRELOAD || true

as_root() {
  if [[ "$(id -u)" -eq 0 ]]; then
    "$@"
  else
    command sudo env -u LD_LIBRARY_PATH -u LD_PRELOAD "$@"
  fi
}

BUNDLE_DIR="${1:-}"
if [[ -z "${BUNDLE_DIR}" || ! -d "${BUNDLE_DIR}" ]]; then
  echo "INSTALL_FAIL: 缺少 bundle 目录参数" >&2
  exit 1
fi

cd "${BUNDLE_DIR}"
PYTHON="${PYTHON:-python3}"
WHEELS_DIR="${BUNDLE_DIR}/pip-wheels"
REQ_FILE="${BUNDLE_DIR}/requirements.txt"
SITE_PKG="${BUNDLE_DIR}/site-packages"
GET_PIP="${BUNDLE_DIR}/get-pip.py"
LAUNCHER="${BUNDLE_DIR}/run-python.sh"

if [[ ! -f "${REQ_FILE}" ]]; then
  echo "INSTALL_FAIL: 缺少 requirements.txt" >&2
  exit 1
fi
if [[ ! -d "${WHEELS_DIR}" ]]; then
  echo "INSTALL_FAIL: 缺少 pip-wheels 目录" >&2
  exit 1
fi

has_wheel() {
  compgen -G "${WHEELS_DIR}/$1"*.whl >/dev/null 2>&1 \
    || compgen -G "${WHEELS_DIR}/${1,,}"*.whl >/dev/null 2>&1
}

if ! has_wheel pip || ! has_wheel setuptools || ! has_wheel wheel; then
  echo "INSTALL_FAIL: pip/setuptools/wheel bootstrap 包不完整" >&2
  exit 1
fi

echo "==> 离线安装 bundle 运行时: ${BUNDLE_DIR}"
as_root rm -rf "${SITE_PKG}"
as_root mkdir -p "${SITE_PKG}"

as_root "${PYTHON}" - "${SITE_PKG}" "${WHEELS_DIR}" <<'PY'
import glob, os, sys, zipfile
site, wheels_dir = sys.argv[1], sys.argv[2]
os.makedirs(site, exist_ok=True)
for pkg in ("pip", "setuptools", "wheel"):
    matches = glob.glob(os.path.join(wheels_dir, f"{pkg}-*.whl"))
    if not matches:
        print(f"INSTALL_FAIL: missing wheel for {pkg}", file=sys.stderr)
        sys.exit(1)
    with zipfile.ZipFile(matches[0]) as zf:
        zf.extractall(site)
PY

if ! as_root env PYTHONPATH="${SITE_PKG}" "${PYTHON}" -m pip --version >/dev/null 2>&1; then
  echo "INSTALL_FAIL: bootstrap pip 不可用" >&2
  exit 1
fi

if ! as_root env PYTHONPATH="${SITE_PKG}" "${PYTHON}" -m pip install \
    --target="${SITE_PKG}" --no-index --find-links "${WHEELS_DIR}" \
    -r "${REQ_FILE}" -q; then
  echo "INSTALL_FAIL: 离线依赖安装失败" >&2
  exit 1
fi

as_root tee "${LAUNCHER}" > /dev/null <<WRAP
#!/bin/bash
export PYTHONPATH="${SITE_PKG}\${PYTHONPATH:+:\$PYTHONPATH}"
exec ${PYTHON} "\$@"
WRAP
as_root chmod +x "${LAUNCHER}"
echo "BUNDLE_ENV_OK: ${LAUNCHER}"
