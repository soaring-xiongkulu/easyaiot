#!/usr/bin/env bash
# 在控制面下载 AI 模型服务计算节点离线 pip wheel
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EASYAIOT_ROOT="$(cd "${ROOT}/.." && pwd)"
BUNDLE_TYPE="${BUNDLE_TYPE:-ai_service}"
WHEELS_DIR="${BUNDLE_PIP_WHEELS_DIR:-${ROOT}/.bundle-wheels/${BUNDLE_TYPE}}"
PYPI_INDEX="${PYPI_INDEX:-https://pypi.tuna.tsinghua.edu.cn/simple}"
TARGET_PYTHON="${BUNDLE_TARGET_PYTHON:-${AGENT_TARGET_PYTHON:-3.10}}"
TARGET_PLATFORM="${BUNDLE_TARGET_PLATFORM:-manylinux2014_x86_64}"
GET_PIP_URL="${GET_PIP_URL:-https://bootstrap.pypa.io/get-pip.py}"
GET_PIP_LOCAL="${ROOT}/get-pip.py"
REQ_FILE="${ROOT}/requirements-node-ai-service.txt"
case "${BUNDLE_TYPE}" in
  model_train)
    REQ_FILE="${ROOT}/requirements-node-model-train.txt"
    ;;
  llm_service)
    REQ_FILE="${ROOT}/requirements-node-llm-service.txt"
    ;;
esac

if [[ ! -f "${REQ_FILE}" ]]; then
  echo "[ERROR] requirements not found: ${REQ_FILE}" >&2
  exit 1
fi

print_step() { echo ">>> $*"; }
print_ok() { echo "[OK] $*"; }
print_err() { echo "[ERROR] $*" >&2; }

mkdir -p "${WHEELS_DIR}"
TARGET_MARKER="${WHEELS_DIR}/.target-python"

resolve_python_with_pip() {
  local py
  for py in ${PYTHON:-} python3 python; do
    [[ -z "${py}" ]] && continue
    if command -v "${py}" >/dev/null 2>&1 && "${py}" -m pip --version >/dev/null 2>&1; then
      echo "${py}"
      return 0
    fi
  done
  return 1
}

collect_build_cache_find_links() {
  local links="" dir
  for dir in "${EASYAIOT_ROOT}/.build-cache"/*/pip-wheels "${EASYAIOT_ROOT}/SENTINEL/pip-wheels"; do
    if [[ -d "${dir}" ]] && compgen -G "${dir}"/*.{whl,tar.gz,zip} >/dev/null 2>&1; then
      links="${links} --find-links ${dir}"
    fi
  done
  echo "${links}"
}

if ! PYTHON="$(resolve_python_with_pip)"; then
  print_err "控制面未找到带 pip 的 Python"
  exit 1
fi

FIND_LINKS="$(collect_build_cache_find_links)"
print_step "Downloading AI bundle=${BUNDLE_TYPE} wheels for Python ${TARGET_PYTHON}..."

# shellcheck disable=SC2086
"${PYTHON}" -m pip download pip setuptools wheel \
  -d "${WHEELS_DIR}" \
  --python-version "${TARGET_PYTHON}" \
  --platform "${TARGET_PLATFORM}" \
  --only-binary=:all: \
  --timeout 120 --retries 3 \
  --find-links "${WHEELS_DIR}" ${FIND_LINKS} \
  -i "${PYPI_INDEX}"

if [[ ! -f "${GET_PIP_LOCAL}" ]]; then
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "${GET_PIP_URL}" -o "${GET_PIP_LOCAL}"
  elif command -v wget >/dev/null 2>&1; then
    wget -q -O "${GET_PIP_LOCAL}" "${GET_PIP_URL}"
  fi
fi

# shellcheck disable=SC2086
"${PYTHON}" -m pip download \
  -r "${REQ_FILE}" \
  -d "${WHEELS_DIR}" \
  --python-version "${TARGET_PYTHON}" \
  --platform "${TARGET_PLATFORM}" \
  --only-binary=:all: \
  --timeout 120 --retries 3 \
  --find-links "${WHEELS_DIR}" ${FIND_LINKS} \
  -i "${PYPI_INDEX}"

echo "${TARGET_PYTHON}" > "${TARGET_MARKER}"
count="$(find "${WHEELS_DIR}" -maxdepth 1 -type f \( -name '*.whl' -o -name '*.tar.gz' -o -name '*.zip' \) | wc -l | tr -d ' ')"
print_ok "Downloaded ${count} wheels to ${WHEELS_DIR} (bundle=${BUNDLE_TYPE}, Python ${TARGET_PYTHON})"
