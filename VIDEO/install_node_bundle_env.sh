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
ONLINE_INSTALL="${BUNDLE_ONLINE_INSTALL:-0}"
VENV_DIR="${VENV_DIR:-${BUNDLE_DIR}/.venv}"
VENV_PY="${VENV_DIR}/bin/python"
VENV_PIP="${VENV_DIR}/bin/pip"

if [[ ! -f "${REQ_FILE}" ]]; then
  echo "INSTALL_FAIL: 缺少 requirements.txt" >&2
  exit 1
fi
ensure_pip_online() {
  if "${PYTHON}" -m pip --version >/dev/null 2>&1; then
    return 0
  fi
  if "${PYTHON}" -m ensurepip --upgrade >/dev/null 2>&1; then
    return 0
  fi
  if [[ -f "${GET_PIP}" ]]; then
    echo "==> pip 不存在，尝试执行 get-pip.py（在线引导）"
    if "${PYTHON}" "${GET_PIP}"; then
      return 0
    fi
    echo "==> get-pip.py 执行失败" >&2
  fi
  return 1
}

install_system_pip_online() {
  if command -v apt-get >/dev/null 2>&1; then
    echo "==> 尝试 apt-get 安装 python3-pip"
    as_root apt-get update -y || true
    as_root apt-get install -y python3-pip || return 1
    return 0
  fi
  if command -v dnf >/dev/null 2>&1; then
    echo "==> 尝试 dnf 安装 python3-pip"
    as_root dnf install -y python3-pip || return 1
    return 0
  fi
  if command -v yum >/dev/null 2>&1; then
    echo "==> 尝试 yum 安装 python3-pip"
    as_root yum install -y python3-pip || return 1
    return 0
  fi
  return 1
}

if [[ "${ONLINE_INSTALL}" == "1" ]]; then
  echo "==> 在线安装 bundle 运行时: ${BUNDLE_DIR}"
  # 兼容 PEP 668：系统 Python 可能被标记为 externally-managed，无法直接安装 pip/依赖
  # 因此在线模式改用 venv：依赖安装在 bundle 目录下，避免污染系统环境。
  echo "==> 创建 venv: ${VENV_DIR}"
  as_root rm -rf "${VENV_DIR}"
  # Debian/Ubuntu 可能缺少 ensurepip（即缺少 python3-venv 包），导致 venv 创建失败。
  # 使用 --without-pip 后再在 venv 内用 get-pip.py 引导 pip，避免依赖系统 ensurepip/PEP668 限制。
  if ! as_root "${PYTHON}" -m venv "${VENV_DIR}"; then
    echo "INSTALL_WARN: venv 创建失败（可能缺少 ensurepip），改用 --without-pip"
    as_root "${PYTHON}" -m venv --without-pip "${VENV_DIR}" || exit 1
    if [[ -f "${GET_PIP}" ]]; then
      echo "==> 在 venv 内引导安装 pip（get-pip.py）"
      as_root "${VENV_PY}" "${GET_PIP}" || exit 1
    else
      echo "INSTALL_FAIL: 缺少 get-pip.py，无法在 venv 内引导 pip" >&2
      exit 1
    fi
  fi

  if ! as_root "${VENV_PIP}" install -U pip setuptools wheel >/dev/null 2>&1; then
    echo "INSTALL_WARN: venv 内升级 pip/setuptools/wheel 失败（继续安装依赖）" >&2
  fi
  if ! as_root "${VENV_PIP}" install -r "${REQ_FILE}" -q; then
    echo "INSTALL_FAIL: 在线依赖安装失败" >&2
    exit 1
  fi
else
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
fi

if [[ "${ONLINE_INSTALL}" == "1" ]]; then
  as_root tee "${LAUNCHER}" > /dev/null <<WRAP
#!/bin/bash
exec "${VENV_PY}" "\$@"
WRAP
else
  as_root tee "${LAUNCHER}" > /dev/null <<WRAP
#!/bin/bash
export PYTHONPATH="${SITE_PKG}\${PYTHONPATH:+:\$PYTHONPATH}"
exec ${PYTHON} "\$@"
WRAP
fi
as_root chmod +x "${LAUNCHER}"
echo "BUNDLE_ENV_OK: ${LAUNCHER}"
