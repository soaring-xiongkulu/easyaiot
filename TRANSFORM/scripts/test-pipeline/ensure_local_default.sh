#!/usr/bin/env bash
# 确保本机默认 TRANSFORM 在 :48096 —— 没有就自动拉起（jar）
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/_common.sh"

log "=== [ensure-local] 本机默认 TRANSFORM @ ${LOCAL_TRANSFORM_API} ==="
mkdir -p "$TRANSFORM_BACKUP_DIR" "$STATE_DIR"

if curl -sf --max-time 3 "${LOCAL_TRANSFORM_API}/transform/overview" >/dev/null 2>&1; then
  ok "本机默认已在运行"
  echo "0" > "$LOCAL_OWNED_FILE"
  # 尽量从 API 取真实 instanceId
  PY="$(resolve_python)"
  "$PY" - "$LOCAL_TRANSFORM_API" "$INSTANCES_FILE" <<'PY'
import json, sys, urllib.request
api, path = sys.argv[1], sys.argv[2]
with urllib.request.urlopen(api.rstrip("/") + "/transform/cluster/instances", timeout=5) as r:
    body = json.load(r)
data = body.get("data") if isinstance(body, dict) else body
rows = data if isinstance(data, list) else []
picked = None
for row in rows:
    if row.get("online") or str(row.get("status") or "") in ("ONLINE", "READY"):
        picked = row
        break
if picked is None and rows:
    picked = rows[0]
out = [{
    "instanceId": (picked or {}).get("instanceId") or "local-default",
    "port": 48096,
    "name": "local-default",
    "runtime": "local",
    "nodeId": (picked or {}).get("nodeId") or "platform",
    "owned": False,
}]
open(path, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=2))
print("instances", out)
PY
  exit 0
fi

log "本机默认不存在，自动拉起 jar @ :${LOCAL_TRANSFORM_PORT}"
ensure_jar

if ! port_free "$LOCAL_TRANSFORM_PORT"; then
  fail "端口 ${LOCAL_TRANSFORM_PORT} 被占用但 /transform/overview 不可达，请检查冲突进程"
fi

IID="${LOCAL_INSTANCE_ID}"
LOG_FILE="$STATE_DIR/local-default.log"
nohup env \
  TRANSFORM_INSTANCE_ID="$IID" \
  TRANSFORM_NODE_ID="$LOCAL_NODE_ID" \
  TRANSFORM_ROLE="$TRANSFORM_ROLE" \
  KAFKA_BOOTSTRAP="$KAFKA_BOOTSTRAP" \
  POSTGRES_URL="$POSTGRES_URL" \
  POSTGRES_USERNAME="$POSTGRES_USERNAME" \
  POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
  SERVER_PORT="$LOCAL_TRANSFORM_PORT" \
  java -jar "$JAR" \
    --spring.profiles.active=local \
    --server.port="$LOCAL_TRANSFORM_PORT" \
    --spring.kafka.bootstrap-servers="$KAFKA_BOOTSTRAP" \
    --spring.datasource.dynamic.datasource.master.url="$POSTGRES_URL" \
    --spring.datasource.dynamic.datasource.master.username="$POSTGRES_USERNAME" \
    --spring.datasource.dynamic.datasource.master.password="$POSTGRES_PASSWORD" \
    --transform.instance-id="$IID" \
    --transform.node-id="$LOCAL_NODE_ID" \
    --transform.role="$TRANSFORM_ROLE" \
    --transform.backup-dir="$TRANSFORM_BACKUP_DIR" \
    >"$LOG_FILE" 2>&1 &
echo $! > "$LOCAL_PID_FILE"
echo "1" > "$LOCAL_OWNED_FILE"
ok "已启动本机默认 pid=$(cat "$LOCAL_PID_FILE") log=$LOG_FILE"

if ! wait_http_ok "${LOCAL_TRANSFORM_API}/transform/overview" 120; then
  log "启动失败，日志尾部:"
  tail -n 80 "$LOG_FILE" || true
  fail "本机默认 TRANSFORM 启动超时"
fi

cat > "$INSTANCES_FILE" <<EOF
[
  {
    "instanceId": "$IID",
    "port": $LOCAL_TRANSFORM_PORT,
    "name": "local-default",
    "runtime": "local",
    "nodeId": "$LOCAL_NODE_ID",
    "owned": true
  }
]
EOF
ok "本机默认已就绪 instanceId=$IID"
cat "$INSTANCES_FILE"
