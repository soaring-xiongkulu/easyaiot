#!/usr/bin/env bash
# 在控制面下载计算节点工作负载离线 pip wheel（目标机默认无外网）
# 用法: BUNDLE_TYPE=stream_forward bash export_node_pip_wheels.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EASYAIOT_ROOT="$(cd "${ROOT}/.." && pwd)"
BUNDLE_TYPE="${BUNDLE_TYPE:-stream_forward}"
PYPI_INDEX="${PYPI_INDEX:-https://pypi.tuna.tsinghua.edu.cn/simple}"
TARGET_PYTHON="${BUNDLE_TARGET_PYTHON:-${AGENT_TARGET_PYTHON:-3.10}}"
BUNDLE_OS_FAMILY="${BUNDLE_OS_FAMILY:-linux}"
BUNDLE_TARGET_ARCH="${BUNDLE_TARGET_ARCH:-x86_64}"
TARGET_PLATFORM="${BUNDLE_TARGET_PLATFORM:-manylinux2014_x86_64}"
GET_PIP_URL="${GET_PIP_URL:-https://bootstrap.pypa.io/get-pip.py}"
GET_PIP_LOCAL="${ROOT}/get-pip.py"

case "${BUNDLE_TYPE}" in
  stream_forward) REQ_FILE="${ROOT}/requirements-node-stream-forward.txt" ;;
  algorithm_realtime) REQ_FILE="${ROOT}/requirements-node-algorithm-realtime.txt" ;;
  algorithm_snap) REQ_FILE="${ROOT}/requirements-node-algorithm-snap.txt" ;;
  algorithm_patrol) REQ_FILE="${ROOT}/requirements-node-algorithm-patrol.txt" ;;
  post_process) REQ_FILE="${ROOT}/requirements-node-post-process.txt" ;;
  *)
    echo "[ERROR] 未知 BUNDLE_TYPE=${BUNDLE_TYPE}" >&2
    exit 1
    ;;
esac

if [[ ! -f "${REQ_FILE}" ]]; then
  echo "[ERROR] requirements not found: ${REQ_FILE}" >&2
  exit 1
fi

print_step() { echo ">>> $*"; }
print_ok() { echo "[OK] $*"; }
print_err() { echo "[ERROR] $*" >&2; }

normalize_key() {
  local raw="${1:-}" fallback="${2:-unknown}"
  raw="$(echo "${raw}" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9._-]/-/g')"
  if [[ -z "${raw}" ]]; then
    echo "${fallback}"
  else
    echo "${raw}"
  fi
}

normalize_python_mm() {
  python3 - "${1:-3.10}" <<'PY'
import re, sys
raw = (sys.argv[1] or "3.10").strip().lower().replace("cp", "")
nums = re.findall(r"\d+", raw)
if len(nums) >= 2:
    print(f"{nums[0]}.{nums[1]}")
else:
    print("3.10")
PY
}

TARGET_MM="$(normalize_python_mm "${TARGET_PYTHON}")"
OS_KEY="$(normalize_key "${BUNDLE_OS_FAMILY}" "linux")"
ARCH_KEY="$(normalize_key "${BUNDLE_TARGET_ARCH}" "x86_64")"
PY_KEY="py${TARGET_MM/./}"
WHEELS_DIR="${BUNDLE_PIP_WHEELS_DIR:-${ROOT}/.bundle-wheels/${BUNDLE_TYPE}/${OS_KEY}/${ARCH_KEY}/${PY_KEY}}"

mkdir -p "${WHEELS_DIR}"
TARGET_MARKER="${WHEELS_DIR}/.target-python"
TARGET_META="${WHEELS_DIR}/.bundle-meta"

# 控制面 Python 解释 PEP508 标记；必须按目标版本展开 -r，并在目标解释器里 download。
TARGET_MAJOR="${TARGET_MM%%.*}"
TARGET_MINOR="${TARGET_MM#*.}"
TARGET_ABI="cp${TARGET_MAJOR}${TARGET_MINOR}"
REQ_FOR_DOWNLOAD="${WHEELS_DIR}/.requirements.download.txt"
{
  python3 - "${REQ_FILE}" "${TARGET_MM}" "${REQ_FOR_DOWNLOAD}" <<'PY'
import sys
from pathlib import Path

src, target, dest = Path(sys.argv[1]), sys.argv[2].strip(), Path(sys.argv[3])
try:
    target_tuple = tuple(int(p) for p in target.split(".")[:2])
except ValueError:
    target_tuple = (3, 10)
seen = set()

def walk(path: Path):
    real = path.resolve()
    if real in seen:
        return
    seen.add(real)
    for raw in real.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("-r "):
            yield from walk((real.parent / line[3:].strip()).resolve())
            continue
        if line.startswith("onnxruntime"):
            continue
        yield raw

out = list(walk(src))
if target_tuple < (3, 10):
    out.append("onnxruntime==1.16.3")
    out.append("importlib-metadata>=3.6.0")
    out.append("zipp>=3.1.0")
else:
    out.append("onnxruntime-gpu==1.20.0")
dest.write_text("\n".join(out) + "\n", encoding="utf-8")
PY
} || cp "${REQ_FILE}" "${REQ_FOR_DOWNLOAD}"

resolve_python_with_pip() {
  local candidates=() py seen=""
  if [[ -n "${PYTHON:-}" ]]; then candidates+=("${PYTHON}"); fi
  candidates+=(python3 python)
  for py in "${candidates[@]}"; do
    [[ "${seen}" == *"|${py}|"* ]] && continue
    seen="${seen}|${py}|"
    if command -v "${py}" >/dev/null 2>&1 && "${py}" -m pip --version >/dev/null 2>&1; then
      echo "${py}"
      return 0
    fi
  done
  return 1
}

collect_build_cache_find_links() {
  local links="" dir
  for dir in "${EASYAIOT_ROOT}/.build-cache"/*/pip-wheels "${EASYAIOT_ROOT}/NODE/pip-wheels"; do
    if [[ -d "${dir}" ]] && compgen -G "${dir}"/*.{whl,tar.gz,zip} >/dev/null 2>&1; then
      links="${links} --find-links ${dir}"
    fi
  done
  echo "${links}"
}

if ! PYTHON="$(resolve_python_with_pip)"; then
  print_err "控制面未找到带 pip 的 Python，请先安装 python3-pip"
  exit 1
fi

FIND_LINKS="$(collect_build_cache_find_links)"
print_step "Downloading VIDEO bundle=${BUNDLE_TYPE} wheels for Python ${TARGET_PYTHON}..."

HOST_MM="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
DOCKER_PY_IMAGE="${BUNDLE_PYTHON_IMAGE:-docker.m.daocloud.io/library/python:${TARGET_MM}-slim-bookworm}"

download_host() {
  # shellcheck disable=SC2086
  "${PYTHON}" -m pip download pip setuptools wheel \
    -d "${WHEELS_DIR}" \
    --python-version "${TARGET_MM}" \
    --implementation cp \
    --abi "${TARGET_ABI}" \
    --platform "${TARGET_PLATFORM}" \
    --only-binary=:all: \
    --timeout 120 --retries 3 \
    --find-links "${WHEELS_DIR}" ${FIND_LINKS} \
    -i "${PYPI_INDEX}"
  # shellcheck disable=SC2086
  "${PYTHON}" -m pip download \
    -r "${REQ_FOR_DOWNLOAD}" \
    -d "${WHEELS_DIR}" \
    --python-version "${TARGET_MM}" \
    --implementation cp \
    --abi "${TARGET_ABI}" \
    --platform "${TARGET_PLATFORM}" \
    --only-binary=:all: \
    --timeout 120 --retries 3 \
    --find-links "${WHEELS_DIR}" ${FIND_LINKS} \
    -i "${PYPI_INDEX}"
}

download_docker() {
  print_step "使用 Docker ${DOCKER_PY_IMAGE} 按目标 Python 解析依赖"
  docker pull "${DOCKER_PY_IMAGE}" >/dev/null
  docker run --rm \
    -v "${WHEELS_DIR}:/wheels" \
    -v "${REQ_FOR_DOWNLOAD}:/req.txt:ro" \
    -e PIP_INDEX_URL="${PYPI_INDEX}" \
    "${DOCKER_PY_IMAGE}" \
    bash -lc 'pip install -q pip setuptools wheel \
      && pip download pip setuptools wheel -d /wheels --only-binary=:all: --timeout 120 --retries 3 \
      && pip download -r /req.txt -d /wheels --only-binary=:all: --timeout 120 --retries 3'
}

if [[ "${HOST_MM}" != "${TARGET_MM}" ]] && command -v docker >/dev/null 2>&1; then
  download_docker || {
    print_err "Docker 目标 Python 下载失败，回退本机 pip --python-version（部分 PEP508 标记仍可能漏包）"
    download_host
  }
else
  download_host
fi

echo "${TARGET_MM}" > "${TARGET_MARKER}"
cat > "${TARGET_META}" <<EOF
os_family=${OS_KEY}
arch=${ARCH_KEY}
python=${TARGET_MM}
bundle=${BUNDLE_TYPE}
EOF
count="$(find "${WHEELS_DIR}" -maxdepth 1 -type f \( -name '*.whl' -o -name '*.tar.gz' -o -name '*.zip' \) | wc -l | tr -d ' ')"
print_ok "Downloaded ${count} wheels to ${WHEELS_DIR} (bundle=${BUNDLE_TYPE}, os=${OS_KEY}, arch=${ARCH_KEY}, Python ${TARGET_MM})"
