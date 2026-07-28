#!/usr/bin/env bash
# TRANSFORM 镜像全链路：无镜像则构建 → 导出压缩 → 分发(load) → 部署运行 → Kafka 心跳验收
#
# 用法（本机多容器）:
#   bash scripts/pipeline-distribute-run.sh --mode local --count 2
#
# 用法（经 Agent 部署到节点）:
#   AGENT_URL=http://192.168.1.20:9100 \
#   bash scripts/pipeline-distribute-run.sh --mode agent --count 2 --node-id 12
#
# 验收不依赖固定 HTTP 端口，订阅约定 topic: iot_transform_heartbeat
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MODE=local
COUNT=1
START_PORT=48096
IMAGE="${TRANSFORM_IMAGE:-easyaiot/transform-runtime:1.0.0}"
KAFKA="${KAFKA_BOOTSTRAP:-127.0.0.1:9092}"
NODE_ID="${TRANSFORM_NODE_ID:-}"
AGENT_URL="${AGENT_URL:-http://127.0.0.1:9100}"
TIMEOUT=120
SKIP_BUILD=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode) MODE="$2"; shift 2 ;;
    --count) COUNT="$2"; shift 2 ;;
    --start-port) START_PORT="$2"; shift 2 ;;
    --image) IMAGE="$2"; shift 2 ;;
    --kafka) KAFKA="$2"; shift 2 ;;
    --node-id) NODE_ID="$2"; shift 2 ;;
    --agent) AGENT_URL="$2"; shift 2 ;;
    --timeout) TIMEOUT="$2"; shift 2 ;;
    --skip-build) SKIP_BUILD=1; shift ;;
    *) echo "unknown: $1" >&2; exit 1 ;;
  esac
done

GZ="$ROOT/dist/transform-runtime-1.0.0.tar.gz"
TAR="$ROOT/dist/transform-runtime-1.0.0.tar"

echo "=== [1/5] 打包镜像（缺失则构建） ==="
if [[ "$SKIP_BUILD" != "1" ]]; then
  if ! docker image inspect "$IMAGE" >/dev/null 2>&1 || [[ ! -f "$GZ" && ! -f "$TAR" ]]; then
    bash "$ROOT/scripts/build-image.sh"
  else
    echo "已有镜像与制品，跳过构建（可 TRANSFORM_IMAGE_FORCE=1 强制）"
    # 仍保证 gz 存在
    if [[ -f "$TAR" && ! -f "$GZ" ]]; then
      gzip -c "$TAR" > "$GZ"
    fi
  fi
fi
[[ -f "$GZ" || -f "$TAR" ]] || { echo "缺少镜像制品" >&2; exit 1; }

echo "=== [2/5] 压缩制品 ==="
if [[ -f "$GZ" ]]; then
  ls -lh "$GZ"
else
  gzip -c "$TAR" > "$GZ"
  ls -lh "$GZ"
fi

echo "=== [3/5] 本机 load（agent 模式：假定目标已由 NODE SSH 同步+load，此处确保本机可测） ==="
if docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "image exists: $IMAGE"
else
  if [[ -f "$GZ" ]]; then
    gunzip -c "$GZ" | docker load
  else
    docker load -i "$TAR"
  fi
fi

echo "=== [4/5] 部署运行 mode=$MODE count=$COUNT ==="
case "$MODE" in
  local)
    bash "$ROOT/scripts/run-multi-containers.sh" --count "$COUNT" --base-port "$START_PORT" \
      --image "$IMAGE" --kafka "$KAFKA" ${NODE_ID:+--node-id "$NODE_ID"}
    ;;
  agent)
    AGENT_URL="$AGENT_URL" TRANSFORM_IMAGE="$IMAGE" KAFKA_BOOTSTRAP="$KAFKA" \
      TRANSFORM_NODE_ID="$NODE_ID" \
      bash "$ROOT/scripts/agent-deploy-containers.sh" \
        --count "$COUNT" --start-port "$START_PORT" --image "$IMAGE" --kafka "$KAFKA" \
        ${NODE_ID:+--node-id "$NODE_ID"} --agent "$AGENT_URL"
    ;;
  *)
    echo "unknown mode: $MODE (local|agent)" >&2
    exit 1
    ;;
esac

echo "=== [5/5] Kafka 心跳验收 topic=iot_transform_heartbeat ==="
PY=python3
if [[ -x "$ROOT/scripts/e2e/.venv/bin/python" ]]; then
  PY="$ROOT/scripts/e2e/.venv/bin/python"
fi
WAIT_ARGS=(--bootstrap "$KAFKA" --expect "$COUNT" --timeout "$TIMEOUT")
if [[ -n "$NODE_ID" ]]; then
  WAIT_ARGS+=(--node-id "$NODE_ID")
fi
if ! "$PY" "$ROOT/scripts/wait-heartbeat.py" "${WAIT_ARGS[@]}"; then
  echo "心跳验收失败：请检查 Kafka、容器日志、TRANSFORM_INSTANCE_ID" >&2
  exit 1
fi

echo "PIPELINE_OK mode=$MODE count=$COUNT image=$IMAGE"
echo "NODE 维：节点分发/启停；TRANSFORM 维：系统对接集群总览（同源 PG + heartbeat/telemetry）"
