#!/usr/bin/env bash
# TRANSFORM 全链路测试：本地没有也能跑通业务流程
#
# 默认 --mode full：
#   预检 → 本机默认(没有就拉起) → mock(没有就拉起)
#   → 心跳/集群 → 业务投喂(DATA/ALERT/FACE) →（可选）旁路扩容
#
# 用法:
#   bash run_all.sh                      # = --mode full
#   bash run_all.sh --mode full --count 1
#   bash run_all.sh --mode full --count 2          # 本机默认 + 1 个旁路
#   bash run_all.sh --cleanup-local                # 结束后也停掉自动拉起的本机默认
#   bash run_all.sh --skip-business                # 只验部署/心跳
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/_common.sh"

MODE="${PIPELINE_MODE:-full}"
COUNT="$PIPELINE_COUNT"
SKIP_BUILD=0
SKIP_BUSINESS=0
EXPECT_ONLINE=0
DO_CLEANUP=1
BASE_PORT="$PIPELINE_BASE_PORT"
NODE_FILTER=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode) MODE="$2"; shift 2 ;;
    --count) COUNT="$2"; shift 2 ;;
    --base-port) BASE_PORT="$2"; shift 2 ;;
    --skip-build) SKIP_BUILD=1; shift ;;
    --skip-business) SKIP_BUSINESS=1; shift ;;
    --expect-online) EXPECT_ONLINE="$2"; shift 2 ;;
    --no-cleanup) DO_CLEANUP=0; shift ;;
    --cleanup) DO_CLEANUP=1; shift ;;
    --cleanup-local) KEEP_LOCAL_DEFAULT=0; export KEEP_LOCAL_DEFAULT; shift ;;
    --keep-local) KEEP_LOCAL_DEFAULT=1; export KEEP_LOCAL_DEFAULT; shift ;;
    --node-id) NODE_FILTER="$2"; TRANSFORM_NODE_ID="$2"; export TRANSFORM_NODE_ID; shift 2 ;;
    --kafka) KAFKA_BOOTSTRAP="$2"; export KAFKA_BOOTSTRAP; shift 2 ;;
    -h|--help)
      sed -n '1,30p' "$0"
      exit 0
      ;;
    *) echo "unknown: $1" >&2; exit 1 ;;
  esac
done

export PIPELINE_COUNT="$COUNT"
export PIPELINE_BASE_PORT="$BASE_PORT"
export PIPELINE_CLEANUP="$DO_CLEANUP"
export TRANSFORM_API="${TRANSFORM_API:-$LOCAL_TRANSFORM_API}"

ensure_python_deps
PY="$(resolve_python)"

cleanup_trap() {
  local code=$?
  if [[ "$DO_CLEANUP" == "1" ]]; then
    bash "$DIR/05_cleanup.sh" --force || true
  fi
  exit "$code"
}
trap cleanup_trap EXIT

echo "============================================"
echo " TRANSFORM Full Pipeline Test"
echo " mode=$MODE count=$COUNT kafka=$KAFKA_BOOTSTRAP"
echo " localApi=$LOCAL_TRANSFORM_API keepLocal=$KEEP_LOCAL_DEFAULT"
echo " 流程: 预检 → 本机默认(可自动拉起) → mock → 心跳/集群 → 业务"
echo "============================================"

bash "$DIR/00_preflight.sh" "$MODE"

# 1) 本机默认：没有就拉起
bash "$DIR/ensure_local_default.sh"
export TRANSFORM_API="$LOCAL_TRANSFORM_API"

# 2) mock 接收端：没有就拉起（业务流程需要）
if [[ "$SKIP_BUSINESS" != "1" ]]; then
  bash "$DIR/ensure_mock.sh"
fi

# 3) 可选旁路扩容（模拟其他节点；不碰 48096）
WORKER_EXPECT=0
case "$MODE" in
  full|auto|workers|jar|docker)
    # count=1 仅本机；count>=2 再起 count-1 个旁路（或 count 全旁路+本机？）
    # 语义：count = 期望在线总数（含本机默认）
    if [[ "$COUNT" -gt 1 ]]; then
      WORKER_EXPECT=$((COUNT - 1))
      EFFECTIVE="$(resolve_mode "$MODE")"
      if [[ "$EFFECTIVE" == "docker" ]]; then
        if [[ "$SKIP_BUILD" == "1" ]]; then
          bash "$DIR/01_build_compress.sh" --skip-build
        else
          bash "$DIR/01_build_compress.sh"
        fi
      fi
      # 02 会覆盖 instances.json —— 先备份本机，再合并
      LOCAL_SNAP="$STATE_DIR/local_instances.json"
      cp "$INSTANCES_FILE" "$LOCAL_SNAP"
      bash "$DIR/02_deploy_run.sh" "$EFFECTIVE" "$WORKER_EXPECT" "$BASE_PORT"
      "$PY" - "$LOCAL_SNAP" "$INSTANCES_FILE" <<'PY'
import json, sys
local = json.loads(open(sys.argv[1], encoding="utf-8").read() or "[]")
workers = json.loads(open(sys.argv[2], encoding="utf-8").read() or "[]")
# 去掉 local 占位与 workers 合并
merged = [r for r in local if r.get("runtime") == "local"] + [
    r for r in workers if r.get("runtime") != "local"
]
open(sys.argv[2], "w", encoding="utf-8").write(json.dumps(merged, ensure_ascii=False, indent=2))
print("merged_instances", len(merged))
PY
    fi
    ;;
  local|skip-deploy|skip)
    ;;
  *)
    fail "未知 mode=$MODE（推荐 full）"
    ;;
esac

EXPECT_HB="${EXPECT_ONLINE}"
if [[ "$EXPECT_HB" -le 0 ]]; then
  EXPECT_HB="$COUNT"
fi
if [[ "$EXPECT_HB" -le 0 ]]; then
  EXPECT_HB=1
fi

sleep 2

HB_ARGS=(
  --bootstrap "$KAFKA_BOOTSTRAP"
  --expect "$EXPECT_HB"
  --timeout "${HEARTBEAT_TIMEOUT}"
  --api "$TRANSFORM_API"
  --local
)
CL_ARGS=(
  --api "$TRANSFORM_API"
  --expect-online "$EXPECT_HB"
  --timeout "${HEARTBEAT_TIMEOUT}"
  --local
)
if [[ -n "$NODE_FILTER" ]]; then
  HB_ARGS+=(--node-id "$NODE_FILTER")
  CL_ARGS+=(--node-id "$NODE_FILTER")
fi

# 4) 心跳 + 集群（本机/旁路）
# 有明确 instanceId 清单时，03/04 会按清单匹配；本机自动拉起时已写入
"$PY" "$DIR/03_assert_heartbeat.py" "${HB_ARGS[@]}"
"$PY" "$DIR/04_assert_cluster.py" "${CL_ARGS[@]}"

# 5) 业务流程
if [[ "$SKIP_BUSINESS" != "1" ]]; then
  bash "$DIR/06_assert_business.sh" "$TRANSFORM_API"
else
  log "跳过业务流程（--skip-business）"
fi

echo
ok "PIPELINE TEST PASSED mode=$MODE expectOnline=$EXPECT_HB"
echo "  本机默认: $LOCAL_TRANSFORM_API （没有时已自动拉起；KEEP_LOCAL_DEFAULT=$KEEP_LOCAL_DEFAULT）"
echo "  业务流程: sink 模拟投喂 → Outbox → MES/ERP/WMS/HTTP"
echo "  分发不含本机: 旁路实例端口 ${BASE_PORT}+"
