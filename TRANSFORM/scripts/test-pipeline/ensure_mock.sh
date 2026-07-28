#!/usr/bin/env bash
# 确保 mock MES/ERP/WMS 接收端 —— 没有就自动拉起
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/_common.sh"

log "=== [ensure-mock] mock receiver @ ${RECEIVER_HOST}:${RECEIVER_PORT} ==="
ensure_python_deps
PY="$(resolve_python)"
URL="http://${RECEIVER_HOST}:${RECEIVER_PORT}/health"

if curl -sf --max-time 3 "$URL" >/dev/null 2>&1; then
  ok "mock 已在运行"
  echo "0" > "$MOCK_OWNED_FILE"
  exit 0
fi

LOG_FILE="$STATE_DIR/mock_receiver.log"
"$PY" "$E2E_DIR/mock_receiver.py" --port "$RECEIVER_PORT" >"$LOG_FILE" 2>&1 &
echo $! > "$MOCK_PID_FILE"
echo "1" > "$MOCK_OWNED_FILE"
ok "已启动 mock pid=$(cat "$MOCK_PID_FILE")"

for _ in $(seq 1 40); do
  if curl -sf --max-time 2 "$URL" >/dev/null 2>&1; then
    ok "mock 就绪 $URL"
    exit 0
  fi
  sleep 0.25
done
tail -n 40 "$LOG_FILE" || true
fail "mock receiver 启动失败"
