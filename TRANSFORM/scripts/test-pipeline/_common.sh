#!/usr/bin/env bash
# 公共环境：被各步骤 source
set -euo pipefail

_TP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$(cd "$_TP_DIR/.." && pwd)"
ROOT="$(cd "$SCRIPTS_DIR/.." && pwd)"
E2E_DIR="$SCRIPTS_DIR/e2e"
STATE_DIR="${PIPELINE_STATE_DIR:-$_TP_DIR/.state}"
mkdir -p "$STATE_DIR"

if [[ -f "$_TP_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$_TP_DIR/.env"
  set +a
fi

export KAFKA_BOOTSTRAP="${KAFKA_BOOTSTRAP:-127.0.0.1:9092}"
export POSTGRES_URL="${POSTGRES_URL:-jdbc:postgresql://127.0.0.1:5432/iot-transform20}"
export POSTGRES_USERNAME="${POSTGRES_USERNAME:-postgres}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-iot45722414822}"
export TRANSFORM_IMAGE="${TRANSFORM_IMAGE:-easyaiot/transform-runtime:1.0.0}"
export TRANSFORM_NODE_ID="${TRANSFORM_NODE_ID:-}"
export TRANSFORM_ROLE="${TRANSFORM_ROLE:-full}"
export PIPELINE_COUNT="${PIPELINE_COUNT:-1}"
export PIPELINE_BASE_PORT="${PIPELINE_BASE_PORT:-48110}"
export LOCAL_TRANSFORM_PORT="${LOCAL_TRANSFORM_PORT:-48096}"
export LOCAL_TRANSFORM_API="${LOCAL_TRANSFORM_API:-http://127.0.0.1:${LOCAL_TRANSFORM_PORT}}"
export LOCAL_NODE_ID="${LOCAL_NODE_ID:-platform}"
export LOCAL_INSTANCE_ID="${LOCAL_INSTANCE_ID:-local-default}"
export HEARTBEAT_TIMEOUT="${HEARTBEAT_TIMEOUT:-120}"
export BUSINESS_TIMEOUT="${BUSINESS_TIMEOUT:-60}"
export TRANSFORM_API="${TRANSFORM_API:-}"
export PIPELINE_CLEANUP="${PIPELINE_CLEANUP:-1}"
# 测试若自动拉起本机默认：默认保留（成为机器上的默认实例）；--cleanup-local 可关掉
export KEEP_LOCAL_DEFAULT="${KEEP_LOCAL_DEFAULT:-1}"
export RECEIVER_HOST="${RECEIVER_HOST:-127.0.0.1}"
export RECEIVER_PORT="${RECEIVER_PORT:-18080}"
export PIPELINE_NAME_PREFIX="${PIPELINE_NAME_PREFIX:-tf-pipe-test}"
export TRANSFORM_BACKUP_DIR="${TRANSFORM_BACKUP_DIR:-$ROOT/data/transform-backup}"
export PG_CONTAINER="${PG_CONTAINER:-postgres-server}"

TAR="$ROOT/dist/transform-runtime-1.0.0.tar"
GZ="$ROOT/dist/transform-runtime-1.0.0.tar.gz"
JAR="$ROOT/transform-runtime/target/transform-runtime-1.0.0.jar"
INSTANCES_FILE="$STATE_DIR/instances.json"
PIDS_FILE="$STATE_DIR/pids.txt"
LOCAL_PID_FILE="$STATE_DIR/local.pid"
LOCAL_OWNED_FILE="$STATE_DIR/local.owned"
MOCK_PID_FILE="$STATE_DIR/mock.pid"
MOCK_OWNED_FILE="$STATE_DIR/mock.owned"

log() { echo "[$(date +%H:%M:%S)] $*"; }
ok() { log "OK $*"; }
fail() { log "FAIL $*"; exit 1; }

resolve_python() {
  if [[ -x "$E2E_DIR/.venv/bin/python" ]]; then
    echo "$E2E_DIR/.venv/bin/python"
  else
    echo "python3"
  fi
}

docker_ok() {
  docker info >/dev/null 2>&1
}

resolve_mode() {
  local mode="${1:-auto}"
  case "$mode" in
    auto|workers|full)
      if docker_ok; then echo docker; else echo jar; fi
      ;;
    *)
      echo "$mode"
      ;;
  esac
}

port_free() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ! ss -lnt 2>/dev/null | awk '{print $4}' | grep -qE "[:.]${port}$"
  else
    ! (echo >/dev/tcp/127.0.0.1/"$port") 2>/dev/null
  fi
}

wait_http_ok() {
  local url="$1"
  local timeout="${2:-90}"
  local deadline=$((SECONDS + timeout))
  while (( SECONDS < deadline )); do
    if curl -sf --max-time 2 "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  return 1
}

ensure_jar() {
  if [[ -f "$JAR" ]]; then
    return 0
  fi
  log "缺少 jar，开始 mvn package …"
  (cd "$ROOT" && mvn -pl transform-runtime -am package -DskipTests -q)
  [[ -f "$JAR" ]] || fail "缺少 $JAR"
  ok "jar 已打包"
}

ensure_python_deps() {
  local py
  py="$(resolve_python)"
  if "$py" -c "import kafka, requests" 2>/dev/null; then
    return 0
  fi
  log "安装 Python 依赖到 e2e/.venv …"
  if [[ ! -x "$E2E_DIR/.venv/bin/python" ]]; then
    python3 -m venv "$E2E_DIR/.venv"
  fi
  "$E2E_DIR/.venv/bin/pip" -q install -r "$E2E_DIR/requirements.txt"
}
