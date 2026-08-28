#!/usr/bin/env bash
# ============================================================
# FLOW 工作流 —— 初始化 + Demo 数据一键重放
# 由 .scripts/docker/install_linux.sh 部署完成后自动调用；也可手动执行。
# 用法：bash .scripts/flow/flow_demo_replay.sh [--seed-only]
# 行为：
#   1) 应用 SQL（全部幂等）：
#      patches/flow_menu.sql           WEB 管理端菜单 → ruoyi-vue-pro20
#      patches/flow_notify_template.sql 待办提醒模板 flow_task_todo → ruoyi-vue-pro20
#      patches/flow_demo_seed.sql      烟感会签模型 + 路由规则 → iot-flow20
#   2) 向 Kafka topic iot-alert-created 发送 8 条真实形状告警快照（#40001-#40008）；
#   3) 以 admin 登录网关，用管理端 API 驱动出多种状态：
#      通过(#40001)/拒绝(#40002)/取消(#40003)/会签通过(#40004)/退回重审(#40005)/
#      会签半审(#40007: IoT 已过、测试号待审)/留待办(#40006、#40008)，含 3 条抄送。
# 幂等：SQL 全部 UPSERT/DO NOTHING；告警按 flow_alert_record.alert_id 判断，已存在自动跳过。
# 前置：docker 环境已启动（postgres-server / kafka-server / iot-gateway / iot-flow）；
#       本脚本会等待网关与 flow-server 就绪（约 2 分钟超时）。
# 依赖：docker、curl、python3；告警截图随 APP 源码提交（APP/src/static/images/demo-alert-*.png）。
# ============================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SEED_SQL="$ROOT/.scripts/flow/patches/flow_demo_seed.sql"
MENU_SQL="$ROOT/.scripts/flow/patches/flow_menu.sql"
NOTIFY_SQL="$ROOT/.scripts/flow/patches/flow_notify_template.sql"

GATEWAY="${FLOW_GATEWAY:-http://localhost:48080}"
TENANT_ID="${FLOW_TENANT_ID:-1}"
FLOW_USER="${FLOW_USER:-admin}"
FLOW_PASS="${FLOW_PASS:-admin123}"
TOPIC="${FLOW_ALERT_TOPIC:-iot-alert-created}"
PG() { docker exec -i postgres-server psql -U postgres -d iot-flow20 "$@"; }
PG_SYS() { docker exec -i postgres-server psql -U postgres -d ruoyi-vue-pro20 "$@"; }

log()  { echo "[demo-replay] $*"; }
fail() { echo "[demo-replay] ERROR: $*" >&2; exit 1; }

for c in docker curl python3; do
  command -v "$c" >/dev/null || fail "缺少依赖命令: $c"
done
docker ps --format '{{.Names}}' | grep -qx postgres-server || fail "postgres-server 容器未运行"
docker ps --format '{{.Names}}' | grep -qx kafka-server   || fail "kafka-server 容器未运行"

# ---------- 1. SQL 初始化（菜单 / 通知模板 / 模型 / 路由规则） ----------
log "应用 FLOW SQL（幂等）"
[ -f "$SEED_SQL" ] || fail "未找到 $SEED_SQL"
if [ -f "$MENU_SQL" ]; then
    PG_SYS -v ON_ERROR_STOP=1 -q < "$MENU_SQL"
    log "  菜单 flow_menu.sql -> ruoyi-vue-pro20"
fi
if [ -f "$NOTIFY_SQL" ]; then
    PG_SYS -v ON_ERROR_STOP=1 -q < "$NOTIFY_SQL"
    log "  通知模板 flow_notify_template.sql -> ruoyi-vue-pro20"
fi
PG -v ON_ERROR_STOP=1 -q < "$SEED_SQL"
log "  会签模型 + 路由规则 flow_demo_seed.sql -> iot-flow20"
if [ "${1:-}" = "--seed-only" ]; then
    log "仅应用种子 SQL，跳过实例重放"
    exit 0
fi

# ---------- 2. 等待服务就绪并登录 ----------
log "等待网关/flow-server 就绪并登录（最长约 2 分钟）..."
TOKEN=""
for _ in $(seq 1 30); do
    TOKEN=$(curl -s -X POST "$GATEWAY/admin-api/system/auth/login" \
        -H "Content-Type: application/json" -H "tenant-id: $TENANT_ID" \
        -d "{\"username\":\"$FLOW_USER\",\"password\":\"$FLOW_PASS\"}" \
        | python3 -c "
import sys, json
try:
    print(json.load(sys.stdin)['data']['accessToken'])
except Exception:
    pass" 2>/dev/null) || true
    [ -n "$TOKEN" ] && break
    sleep 4
done
[ -n "$TOKEN" ] || fail "登录失败（$GATEWAY，用户 $FLOW_USER）：请确认 iot-gateway / iot-flow 已启动"
AUTH=(-H "Authorization: Bearer $TOKEN" -H "tenant-id: $TENANT_ID" -H "Content-Type: application/json")

api() { # api METHOD PATH [JSON_BODY] -> stdout: data JSON；失败时报错退出
  curl -s -X "$1" "$GATEWAY/admin-api$2" "${AUTH[@]}" ${3:+-d "$3"} | python3 -c "
import sys, json
r = json.loads(sys.stdin.read() or '{}')
assert r.get('code') == 0, 'API 失败: %s (%s)' % (r.get('msg'), r.get('code'))
print(json.dumps(r.get('data')))
"
}

# 告警是否已生成实例（幂等判断）
alert_pid() {
  PG -tAc "SELECT process_instance_id FROM flow_alert_record WHERE alert_id=$1 AND process_instance_id IS NOT NULL LIMIT 1" | tr -d '[:space:]'
}

todo_task_id() { # todo_task_id INSTANCE_ID -> 打印当前待办任务 id（无则空）
  local pid=$1
  api GET "/flow/task/todo-page?pageNo=1&pageSize=50" \
    | python3 -c "
import sys, json
pid = '$pid'
tasks = (json.load(sys.stdin) or {}).get('list') or []
hit = next((t for t in tasks if t.get('processInstanceId') == pid), None)
print(hit['id'] if hit else '')
"
}

approve() { # approve INSTANCE_ID REASON
  local id; id=$(todo_task_id "$1"); [ -n "$id" ] || { log "  跳过：无待办任务"; return 0; }
  api PUT /flow/task/approve "{\"id\":\"$id\",\"reason\":\"$2\"}" >/dev/null
  log "  已通过任务 $id"
}
reject() { # reject INSTANCE_ID REASON
  local id; id=$(todo_task_id "$1"); [ -n "$id" ] || { log "  跳过：无待办任务"; return 0; }
  api PUT /flow/task/reject "{\"id\":\"$id\",\"reason\":\"$2\"}" >/dev/null
  log "  已拒绝任务 $id（按节点拒绝策略生效）"
}
copy_to() { # copy_to TASK_ID USER_IDS REASON
  api PUT /flow/task/copy "{\"id\":\"$1\",\"userIds\":$2,\"reason\":\"$3\"}" >/dev/null
  log "  已抄送 -> $2"
}
cancel_instance() { # cancel_instance INSTANCE_ID REASON
  api DELETE /flow/process-instance/cancel-by-start-user "{\"id\":\"$1\",\"reason\":\"$2\"}" >/dev/null
  log "  已取消实例 $1"
}

# ---------- 3. 组装并发送 Kafka 告警快照 ----------
IMG_BASE="http://localhost:9003/static/images"
msgs=$(python3 - "$IMG_BASE" <<'PY'
import json, subprocess, sys
img = sys.argv[1]

def now_off(minutes):
    t = subprocess.run(["date", "+%Y-%m-%d %H:%M:%S", "-d", f"{minutes} min ago"],
                       capture_output=True, text=True).stdout.strip()
    return t

def msg(aid, task, dev_id, dev, event, obj, region, info, image, minutes):
    t = now_off(minutes)
    return {"alertId": aid, "taskId": 50000 + aid % 1000, "taskName": task,
            "deviceId": dev_id, "deviceName": dev, "nodeId": 12, "edgeNodeId": 3,
            "eventId": f"evt-{aid}", "timestamp": t,
            "alert": {"object": obj, "event": event, "region": region,
                      "information": info, "imagePath": f"{img}/{image}", "recordPath": "",
                      "time": t, "taskType": "realtime"}}

alerts = [
    msg(40001, "周界入侵检测", "cam-east-001", "东门摄像头-01", "intrusion", "person", "周界围栏A段", {"confidence": 0.94, "count": 1}, "demo-alert-intrusion.png", 26),
    msg(40002, "周界入侵检测", "cam-south-003", "南墙摄像头-03", "intrusion", "person", "南墙绿化带", {"confidence": 0.71, "remark": "疑似动物轮廓"}, "demo-alert-intrusion.png", 22),
    msg(40003, "周界入侵检测", "cam-west-002", "西门摄像头-02", "intrusion", "person", "西门岗亭旁", {"confidence": 0.88, "count": 2}, "demo-alert-intrusion.png", 18),
    msg(40004, "烟感火情识别", "smoke-wh-a", "仓库A烟感探头", "smoke_fire", "smoke", "货架B排", {"confidence": 0.97, "temperature": "58.3C"}, "demo-alert-smoke.png", 15),
    msg(40005, "烟感火情识别", "smoke-power-01", "配电房烟感探头", "smoke_fire", "smoke", "配电室2号柜", {"confidence": 0.82, "temperature": "41.0C"}, "demo-alert-smoke.png", 12),
    msg(40006, "车辆违停检测", "cam-park-in", "停车场入口摄像头", "illegal_parking", "car", "车位 Z-017", {"confidence": 0.9, "staySeconds": 1820}, "demo-alert-parking.png", 9),
    msg(40007, "烟感火情识别", "smoke-wh-b", "仓库B烟感探头", "smoke_fire", "smoke", "货架D排", {"confidence": 0.93, "temperature": "52.1C"}, "demo-alert-smoke.png", 6),
    msg(40008, "夜间徘徊检测", "cam-yard-004", "后院摄像头-04", "loitering", "person", "后院器材区", {"confidence": 0.86, "staySeconds": 640}, "demo-alert-intrusion.png", 3),
]
sys.stdout.write("\n".join(json.dumps(m, ensure_ascii=False) for m in alerts) + "\n")
PY
)

# ---------- 4. 逐条告警：发送 + 驱动状态 ----------
send_kafka() {
  docker exec -i kafka-server /opt/kafka/bin/kafka-console-producer.sh \
    --bootstrap-server localhost:9092 --topic "$TOPIC" <<<"$1" >/dev/null 2>&1
}
wait_record() { # wait_record ALERT_ID [TRIES]
  local tries=${2:-15}
  for _ in $(seq 1 "$tries"); do
    [ -n "$(alert_pid "$1")" ] && return 0
    sleep 2
  done
  return 1
}

drain() { # drain ALERT_ID：对本次新生成的实例执行状态场景
  local aid=$1
  local pid; pid=$(alert_pid "$aid")
  log "  实例 $pid"

  case $aid in
    40001)
      local tid; tid=$(todo_task_id "$pid")
      approve "$pid" "确认告警属实，已通知安保前往东门处置"
      [ -n "$tid" ] && { copy_to "$tid" "[100]" "请知悉东门入侵处理结果"; true; } || true
      ;;
    40002)
      local tid2; tid2=$(todo_task_id "$pid")
      reject "$pid" "复核为误报：画面为动物轮廓，非人员闯入"
      [ -n "$tid2" ] && { copy_to "$tid2" "[1]" "误报记录归档备查"; true; } || true
      ;;
    40003)
      cancel_instance "$pid" "重复告警，与东门事件为同一人员，合并处理"
      ;;
    40004)
      approve "$pid" "已调取实时画面，确认烟雾，启动消防预案"
      approve "$pid" "现场复核确认，明火已扑灭，无人员伤亡"
      ;;
    40005)
      approve "$pid" "转主管会签复核"
      reject "$pid" "配电房例行检修粉尘误报，退回重新核实"
      ;;
    40007)
      approve "$pid" "画面确认有烟雾，转主管会签"
      local mid; mid=$(todo_task_id "$pid")
      [ -n "$mid" ] && { copy_to "$mid" "[1]" "仓库B火情会签进展抄送，请关注"; true; } || true
      approve "$pid" "已安排值守，等待测试号复核"
      ;;
    *) log "  留待办，不做处理" ;;
  esac
}

SENT=0
FAILED=0
while IFS= read -r line; do
  aid=$(python3 -c "import sys,json;print(json.loads(sys.argv[1])['alertId'])" "$line" 2>/dev/null || echo "")
  if [ -n "$(alert_pid "$aid")" ]; then
    log "告警 #$aid 已存在实例，跳过"
    continue
  fi
  log "告警 #$aid"
  send_kafka "$line"
  SENT=$((SENT + 1))
  if ! wait_record "$aid"; then
    log "  警告：未生成流程实例（检查 flow-server 消费组），跳过驱动"
    FAILED=$((FAILED + 1))
    continue
  fi
  drain "$aid"
done <<EOF
$msgs
EOF

# ---------- 5. 汇总 ----------
if [ "$SENT" -eq 0 ]; then
  log "全部告警均已有实例，无需重放（幂等）。"
else
  log "共发送 $SENT 条告警（$FAILED 条未生成实例）。当前实例状态："
fi
PG -c "SELECT alert_id, process_definition_key AS 流程, process_instance_status AS 状态,
       current_task_name AS 当前节点, current_assignees AS 责任人
       FROM flow_alert_record WHERE alert_id BETWEEN 40001 AND 40008 ORDER BY alert_id"
log "完成。APP：流程审批页（待办/已办/处理记录/抄送）；PC：告警管理 → 告警工单（工单列表/待办/路由规则/流程模型）。"
