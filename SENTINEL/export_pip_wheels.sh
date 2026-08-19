#!/usr/bin/env bash
# Download Node Agent pip wheels on the control plane for offline deploy to air-gapped nodes.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EASYAIOT_ROOT="$(cd "${ROOT}/.." && pwd)"
# 支持 iot-node 在 install 目录不可写时指定缓存路径（AGENT_PIP_WHEELS_DIR）
WHEELS_DIR="${AGENT_PIP_WHEELS_DIR:-${ROOT}/pip-wheels}"
REQ_FILE="${ROOT}/requirements.txt"
REQ_PY39_EXTRAS="${ROOT}/requirements-py39-extras.txt"
PYPI_INDEX="${PYPI_INDEX:-https://pypi.tuna.tsinghua.edu.cn/simple}"
detect_default_target_python() {
  local py="${PYTHON:-python3}"
  if command -v "${py}" >/dev/null 2>&1; then
    "${py}" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "3.10"
  else
    echo "3.10"
  fi
}

TARGET_PYTHON="${AGENT_TARGET_PYTHON:-$(detect_default_target_python)}"
TARGET_PLATFORM="${AGENT_TARGET_PLATFORM:-manylinux2014_x86_64}"
GET_PIP_URL="${GET_PIP_URL:-https://bootstrap.pypa.io/get-pip.py}"
GET_PIP_LOCAL="${ROOT}/get-pip.py"

print_step() { echo ">>> $*"; }
print_ok() { echo "[OK] $*"; }
print_err() { echo "[ERROR] $*" >&2; }

pip_manual_hint() {
  print_err "本机未检测到可用的 pip，请先手动安装后再重试："
  print_err "  Debian/Ubuntu: sudo apt install python3-pip"
  print_err "  或创建 venv 后指定: PYTHON=/path/to/venv/bin/python bash export_pip_wheels.sh"
  print_err "  CentOS/RHEL:     sudo yum install python3-pip"
}

if [[ ! -f "${REQ_FILE}" ]]; then
  print_err "requirements.txt not found: ${REQ_FILE}"
  exit 1
fi

mkdir -p "${WHEELS_DIR}"

TARGET_MARKER="${WHEELS_DIR}/.target-python"
if [[ -f "${TARGET_MARKER}" ]] && [[ "$(cat "${TARGET_MARKER}")" != "${TARGET_PYTHON}" ]]; then
  old_ver="$(cat "${TARGET_MARKER}")"
  print_step "Target Python changed (${old_ver} -> ${TARGET_PYTHON}), refreshing wheels..."
  find "${WHEELS_DIR}" -maxdepth 1 -type f ! -name '.target-python' -delete 2>/dev/null || true
fi

target_python_major() {
  echo "${TARGET_PYTHON%%.*}"
}

target_python_minor() {
  local rest="${TARGET_PYTHON#*.}"
  echo "${rest%%.*}"
}

needs_py39_extras() {
  local major minor
  major="$(target_python_major)"
  minor="$(target_python_minor)"
  [[ "${major}" == "3" && "${minor}" -lt 10 ]]
}

wheel_matches_pattern() {
  local pattern="$1"
  compgen -G "${WHEELS_DIR}/${pattern}" >/dev/null 2>&1 \
    || compgen -G "${WHEELS_DIR}/${pattern,,}" >/dev/null 2>&1
}

verify_offline_install() {
  local py="python${TARGET_PYTHON}"
  if command -v "${py}" >/dev/null 2>&1 && "${py}" -m pip --version >/dev/null 2>&1; then
    "${py}" -m pip install --dry-run --no-index --find-links "${WHEELS_DIR}" \
      -r "${REQ_FILE}" --ignore-installed >/dev/null 2>&1
    return $?
  fi

  local pat count
  for pat in requests psutil Flask minio pip setuptools wheel; do
    if ! wheel_matches_pattern "${pat}*"; then
      return 1
    fi
  done
  if needs_py39_extras; then
    if ! wheel_matches_pattern "importlib_metadata*"; then
      return 1
    fi
    if ! wheel_matches_pattern "zipp*"; then
      return 1
    fi
  fi
  count="$(find "${WHEELS_DIR}" -maxdepth 1 -name '*.whl' | wc -l | tr -d ' ')"
  [[ "${count}" -ge 10 ]]
}

if compgen -G "${WHEELS_DIR}"/*.{whl,tar.gz,zip} >/dev/null 2>&1; then
  if [[ -f "${TARGET_MARKER}" ]] && [[ "$(cat "${TARGET_MARKER}")" == "${TARGET_PYTHON}" ]] \
      && verify_offline_install; then
    count="$(find "${WHEELS_DIR}" -maxdepth 1 -type f \( -name '*.whl' -o -name '*.tar.gz' -o -name '*.zip' \) | wc -l | tr -d ' ')"
    print_ok "Offline wheels ready (${count} files, Python ${TARGET_PYTHON})"
    exit 0
  fi
  print_step "Existing wheels incomplete or target mismatch, refreshing..."
  find "${WHEELS_DIR}" -maxdepth 1 -type f ! -name '.target-python' -delete 2>/dev/null || true
fi

python_has_pip() {
  local py="$1"
  command -v "${py}" >/dev/null 2>&1 && "${py}" -m pip --version >/dev/null 2>&1
}

resolve_python_with_pip() {
  local candidates=() py seen=""
  if [[ -n "${PYTHON:-}" ]]; then candidates+=("${PYTHON}"); fi
  candidates+=(python3 python)
  for py in "${candidates[@]}"; do
    [[ "${seen}" == *"|${py}|"* ]] && continue
    seen="${seen}|${py}|"
    if python_has_pip "${py}"; then
      echo "${py}"
      return 0
    fi
  done
  return 1
}

collect_build_cache_find_links() {
  local links="" dir
  for dir in "${EASYAIOT_ROOT}/.build-cache"/*/pip-wheels; do
    if [[ -d "${dir}" ]] && compgen -G "${dir}"/*.{whl,tar.gz,zip} >/dev/null 2>&1; then
      links="${links} --find-links ${dir}"
    fi
  done
  echo "${links}"
}

if ! PYTHON="$(resolve_python_with_pip)"; then
  pip_manual_hint
  exit 1
fi

print_ok "使用 ${PYTHON} ($(${PYTHON} --version 2>&1), pip $(${PYTHON} -m pip --version 2>&1 | awk '{print $2}')) 下载 wheel，目标节点 Python ${TARGET_PYTHON}"

FIND_LINKS="$(collect_build_cache_find_links)"
print_step "Downloading wheels for Python ${TARGET_PYTHON} (${TARGET_PLATFORM})..."

print_step "Downloading pip/setuptools/wheel for target offline bootstrap..."
# shellcheck disable=SC2086
"${PYTHON}" -m pip download pip setuptools wheel \
  -d "${WHEELS_DIR}" \
  --python-version "${TARGET_PYTHON}" \
  --platform "${TARGET_PLATFORM}" \
  --only-binary=:all: \
  --timeout 120 \
  --retries 3 \
  --find-links "${WHEELS_DIR}" \
  ${FIND_LINKS} \
  -i "${PYPI_INDEX}"

if [[ ! -f "${GET_PIP_LOCAL}" ]]; then
  print_step "Saving get-pip.py for target offline bootstrap..."
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "${GET_PIP_URL}" -o "${GET_PIP_LOCAL}"
  elif command -v wget >/dev/null 2>&1; then
    wget -q -O "${GET_PIP_LOCAL}" "${GET_PIP_URL}"
  else
    print_err "无法下载 get-pip.py（缺少 curl/wget），目标机离线 bootstrap pip 将不可用"
  fi
fi

if [[ ! -f "${GET_PIP_LOCAL}" ]]; then
  print_err "缺少 get-pip.py，目标机无法离线 bootstrap pip"
  print_err "请确认平台服务器可访问 ${GET_PIP_URL}"
  exit 1
fi

print_step "Downloading agent dependencies..."
# shellcheck disable=SC2086
"${PYTHON}" -m pip download \
  -r "${REQ_FILE}" \
  -d "${WHEELS_DIR}" \
  --python-version "${TARGET_PYTHON}" \
  --platform "${TARGET_PLATFORM}" \
  --only-binary=:all: \
  --timeout 120 \
  --retries 3 \
  --find-links "${WHEELS_DIR}" \
  ${FIND_LINKS} \
  -i "${PYPI_INDEX}"

if needs_py39_extras && [[ -f "${REQ_PY39_EXTRAS}" ]]; then
  print_step "Downloading Python < 3.10 backport dependencies..."
  # shellcheck disable=SC2086
  "${PYTHON}" -m pip download \
    -r "${REQ_PY39_EXTRAS}" \
    -d "${WHEELS_DIR}" \
    --python-version "${TARGET_PYTHON}" \
    --platform "${TARGET_PLATFORM}" \
    --only-binary=:all: \
    --timeout 120 \
    --retries 3 \
    --find-links "${WHEELS_DIR}" \
    ${FIND_LINKS} \
    -i "${PYPI_INDEX}"
fi

if ! verify_offline_install; then
  print_err "Incomplete offline bundle for Python ${TARGET_PYTHON}"
  print_err "Ensure PyPI is reachable on the control plane and AGENT_TARGET_PYTHON matches node python3"
  exit 1
fi

count="$(find "${WHEELS_DIR}" -maxdepth 1 -type f \( -name '*.whl' -o -name '*.tar.gz' -o -name '*.zip' \) | wc -l | tr -d ' ')"
echo "${TARGET_PYTHON}" > "${TARGET_MARKER}"
print_ok "Downloaded ${count} offline wheels to ${WHEELS_DIR} (Python ${TARGET_PYTHON})"
