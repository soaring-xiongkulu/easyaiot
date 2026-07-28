#!/usr/bin/env bash
# 步骤 06：业务流程 —— 模拟 iot-sink 投喂 → Outbox → MES/ERP/WMS/HTTP
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/_common.sh"

API="${1:-${TRANSFORM_API:-$LOCAL_TRANSFORM_API}}"
log "=== [06] 业务流程验证 api=$API kafka=$KAFKA_BOOTSTRAP receiver=${RECEIVER_HOST}:${RECEIVER_PORT} ==="

ensure_python_deps
PY="$(resolve_python)"

export KAFKA_BOOTSTRAP
export TRANSFORM_API="$API"
export RECEIVER_PORT
export HTTP_TIMEOUT="${HTTP_TIMEOUT:-10}"

# 如果本轮存在 docker 旁路实例，合同里的 receiver 不能写 127.0.0.1（容器内是自身回环）。
# 改成 docker bridge 网关，保证「本机 runtime + 容器 runtime」都能访问到 mock。
RECEIVER_HOST_E2E="$RECEIVER_HOST"
if [[ -f "$INSTANCES_FILE" ]]; then
  if grep -q '"runtime": "docker"' "$INSTANCES_FILE"; then
    if docker_ok; then
      GW="$(docker network inspect bridge -f '{{range .IPAM.Config}}{{.Gateway}}{{end}}' 2>/dev/null || true)"
      if [[ -n "$GW" ]]; then
        RECEIVER_HOST_E2E="$GW"
      fi
    fi
  fi
fi
export RECEIVER_HOST="$RECEIVER_HOST_E2E"
log "业务投递目标 endpoint host=${RECEIVER_HOST_E2E} (mock 实际监听 ${RECEIVER_HOST}:${RECEIVER_PORT})"

# 尽量刷新 e2e/.env（common.Cfg 会读取）；不可写时回退到进程环境变量。
if [[ ! -e "$E2E_DIR/.env" || -w "$E2E_DIR/.env" ]]; then
  cat > "$E2E_DIR/.env" <<EOF
KAFKA_BOOTSTRAP=$KAFKA_BOOTSTRAP
TRANSFORM_API=$API
USE_GATEWAY=0
RECEIVER_HOST=$RECEIVER_HOST_E2E
RECEIVER_PORT=$RECEIVER_PORT
HTTP_TIMEOUT=${HTTP_TIMEOUT:-10}
EOF
else
  log "WARN: $E2E_DIR/.env 不可写，改用当前进程环境变量"
fi

cd "$E2E_DIR"
"$PY" 01_channels.py \
  --api "$API" \
  --kafka "$KAFKA_BOOTSTRAP" \
  --timeout "${BUSINESS_TIMEOUT}"

ok "业务流程验证通过（DATA→ERP / ALERT→MES+HTTP / FACE→WMS）"
