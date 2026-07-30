#!/usr/bin/env bash
# 步骤 02：部署旁路实例（不碰本机默认 48096）
# mode: docker | jar | local | skip-deploy
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/_common.sh"

MODE="${1:-${PIPELINE_MODE:-jar}}"
COUNT="${2:-$PIPELINE_COUNT}"
BASE_PORT="${3:-$PIPELINE_BASE_PORT}"
MODE="$(resolve_mode "$MODE")"

log "=== [02] 部署运行 mode=$MODE count=$COUNT basePort=$BASE_PORT ==="
rm -f "$INSTANCES_FILE" "$PIDS_FILE"
: > "$PIDS_FILE"

# 宿主机网关：容器内访问 Kafka/PG
HOST_GATEWAY="$(docker network inspect bridge -f '{{range .IPAM.Config}}{{.Gateway}}{{end}}' 2>/dev/null || echo 172.17.0.1)"
KAFKA_EFF="$KAFKA_BOOTSTRAP"
PG_EFF="$POSTGRES_URL"
if [[ "$MODE" == "docker" ]]; then
  if [[ "$KAFKA_EFF" == *"127.0.0.1"* ]]; then
    KAFKA_EFF="${KAFKA_EFF//127.0.0.1/$HOST_GATEWAY}"
  fi
  if [[ "$PG_EFF" == *"127.0.0.1"* ]]; then
    PG_EFF="${PG_EFF//127.0.0.1/$HOST_GATEWAY}"
  fi
fi

# 旁路实例默认 nodeId，便于和本机 platform 区分
WORKER_NODE_ID="${TRANSFORM_NODE_ID:-worker-test}"

write_instances_json() {
  local rows_json="$1"
  printf '%s\n' "$rows_json" > "$INSTANCES_FILE"
  local py
  py="$(resolve_python)"
  # 校验并格式化 JSON，避免后续读到空/坏文件
  "$py" - "$INSTANCES_FILE" <<'PY'
import json, sys, pathlib
path = pathlib.Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))
path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote {len(data)} instances -> {path}")
PY
}

pick_free_port() {
  local start="$1"
  local p="$start"
  local i=0
  while (( i < 50 )); do
    if port_free "$p"; then
      echo "$p"
      return 0
    fi
    # 明确避开本机默认端口
    if [[ "$p" == "48096" ]]; then
      p=48110
    else
      p=$((p + 1))
    fi
    i=$((i + 1))
  done
  fail "找不到空闲端口（从 $start 起）"
}

case "$MODE" in
  local|skip-deploy|skip)
    log "本机默认模式：不部署、不覆盖 48096；只记录探测目标"
    # 若本机 API 可达，写入一条占位（真实 instanceId 由 03/04 从 API/心跳发现）
    if curl -sf --max-time 3 "${LOCAL_TRANSFORM_API}/transform/cluster/instances" >/dev/null 2>&1; then
      echo '[{"instanceId":"","port":48096,"name":"local-default","runtime":"local"}]' > "$INSTANCES_FILE"
      ok "本机默认 TRANSFORM API 可达: $LOCAL_TRANSFORM_API"
    else
      echo '[]' > "$INSTANCES_FILE"
      log "WARN: 本机 $LOCAL_TRANSFORM_API 暂不可达（若刚启动请稍候；03/04 会继续等心跳/API）"
    fi
    ;;

  docker)
    docker_ok || fail "Docker 不可用，请改用: bash run_all.sh --mode jar"
    docker image inspect "$TRANSFORM_IMAGE" >/dev/null 2>&1 \
      || fail "镜像不存在: $TRANSFORM_IMAGE（先跑 01_build_compress.sh）"

    rows='['
    first=1
    port="$BASE_PORT"
    for i in $(seq 1 "$COUNT"); do
      port="$(pick_free_port "$port")"
      name="${PIPELINE_NAME_PREFIX}-${i}"
      iid="${name}-$(hostname)-${port}-$$"
      if docker ps -a --format '{{.Names}}' | grep -qx "$name"; then
        docker rm -f "$name" >/dev/null
      fi
      docker run -d \
        --name "$name" \
        --restart on-failure:5 \
        -p "${port}:48096" \
        -e SERVER_PORT=48096 \
        -e TRANSFORM_INSTANCE_ID="$iid" \
        -e TRANSFORM_NODE_ID="$WORKER_NODE_ID" \
        -e TRANSFORM_ROLE="$TRANSFORM_ROLE" \
        -e KAFKA_BOOTSTRAP="$KAFKA_EFF" \
        -e POSTGRES_URL="$PG_EFF" \
        -e POSTGRES_USERNAME="$POSTGRES_USERNAME" \
        -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
        "$TRANSFORM_IMAGE" >/dev/null
      ok "container=$name hostPort=$port instanceId=$iid nodeId=$WORKER_NODE_ID"
      if [[ $first -eq 0 ]]; then rows+=','; fi
      first=0
      rows+=$(printf '{"instanceId":"%s","port":%s,"name":"%s","runtime":"docker","nodeId":"%s"}' \
        "$iid" "$port" "$name" "$WORKER_NODE_ID")
      port=$((port + 1))
    done
    rows+=']'
    write_instances_json "$rows"
    PY="$(resolve_python)"
    first_port="$("$PY" -c "import json;print(json.load(open(r'$INSTANCES_FILE'))[0]['port'])")"
    wait_http_ok "http://127.0.0.1:${first_port}/transform/overview" 90 \
      || log "WARN: HTTP 尚未就绪，继续靠心跳验收"
    ;;

  jar)
    [[ -f "$JAR" ]] || fail "缺少 $JAR"
    rows='['
    first=1
    port="$BASE_PORT"
    for i in $(seq 1 "$COUNT"); do
      port="$(pick_free_port "$port")"
      if [[ "$port" == "48096" ]]; then
        fail "拒绝占用本机默认端口 48096；请设 PIPELINE_BASE_PORT=48110"
      fi
      name="${PIPELINE_NAME_PREFIX}-jar-${i}"
      iid="${name}-$(hostname)-${port}-$$"
      log_file="$STATE_DIR/${name}.log"
      nohup env \
        TRANSFORM_INSTANCE_ID="$iid" \
        TRANSFORM_NODE_ID="$WORKER_NODE_ID" \
        TRANSFORM_ROLE="$TRANSFORM_ROLE" \
        KAFKA_BOOTSTRAP="$KAFKA_BOOTSTRAP" \
        POSTGRES_URL="$POSTGRES_URL" \
        POSTGRES_USERNAME="$POSTGRES_USERNAME" \
        POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
        SERVER_PORT="$port" \
        java -jar "$JAR" \
          --spring.profiles.active=local \
          --server.port="$port" \
          --spring.kafka.bootstrap-servers="$KAFKA_BOOTSTRAP" \
          --spring.datasource.dynamic.datasource.master.url="$POSTGRES_URL" \
          --spring.datasource.dynamic.datasource.master.username="$POSTGRES_USERNAME" \
          --spring.datasource.dynamic.datasource.master.password="$POSTGRES_PASSWORD" \
          --transform.instance-id="$iid" \
          --transform.node-id="$WORKER_NODE_ID" \
          --transform.role="$TRANSFORM_ROLE" \
          >"$log_file" 2>&1 &
      echo $! >> "$PIDS_FILE"
      ok "pid=$! port=$port instanceId=$iid log=$log_file"
      if [[ $first -eq 0 ]]; then rows+=','; fi
      first=0
      rows+=$(printf '{"instanceId":"%s","port":%s,"name":"%s","runtime":"jar","nodeId":"%s"}' \
        "$iid" "$port" "$name" "$WORKER_NODE_ID")
      port=$((port + 1))
      sleep 2
    done
    rows+=']'
    write_instances_json "$rows"
    PY="$(resolve_python)"
    first_port="$("$PY" -c "import json;print(json.load(open(r'$INSTANCES_FILE'))[0]['port'])")"
    wait_http_ok "http://127.0.0.1:${first_port}/transform/overview" 120 \
      || {
        log "jar 启动日志尾部:"
        tail -n 40 "$STATE_DIR"/${PIPELINE_NAME_PREFIX}-jar-1.log 2>/dev/null || true
        fail "HTTP 未就绪: http://127.0.0.1:${first_port}/transform/overview"
      }
    ;;

  *)
    fail "未知 mode=$MODE（local|docker|jar|auto|workers|skip-deploy）"
    ;;
esac

ok "实例清单: $INSTANCES_FILE"
cat "$INSTANCES_FILE"
