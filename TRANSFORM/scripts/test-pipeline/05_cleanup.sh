#!/usr/bin/env bash
# 步骤 05：清理本轮旁路/测试拉起的进程（默认保留自动拉起的本机默认）
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/_common.sh"

FORCE="${1:-}"
if [[ "$PIPELINE_CLEANUP" != "1" && "$FORCE" != "--force" ]]; then
  log "跳过清理（PIPELINE_CLEANUP=$PIPELINE_CLEANUP）"
  exit 0
fi

log "=== [05] 清理测试产物 ==="

# mock：仅清理本轮拉起的
if [[ -f "$MOCK_OWNED_FILE" && "$(cat "$MOCK_OWNED_FILE" 2>/dev/null || echo 0)" == "1" ]]; then
  if [[ -f "$MOCK_PID_FILE" ]]; then
    pid="$(cat "$MOCK_PID_FILE")"
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      sleep 0.5
      kill -9 "$pid" 2>/dev/null || true
      ok "stopped mock pid=$pid"
    fi
  fi
fi

# 旁路 docker / jar
if [[ -f "$INSTANCES_FILE" ]]; then
  py="$(resolve_python)"
  mapfile -t names < <("$py" - "$INSTANCES_FILE" <<'PY'
import json, sys
rows = json.loads(open(sys.argv[1], encoding="utf-8").read() or "[]")
for r in rows:
    if r.get("runtime") == "docker" and r.get("name"):
        if int(r.get("port") or 0) == 48096:
            continue
        print(r["name"])
PY
)
  for name in "${names[@]:-}"; do
    [[ -z "$name" ]] && continue
    if docker_ok && docker ps -a --format '{{.Names}}' | grep -qx "$name"; then
      docker rm -f "$name" >/dev/null && ok "removed container $name"
    fi
  done
fi

if docker_ok; then
  while read -r name; do
    [[ -z "$name" ]] && continue
    docker rm -f "$name" >/dev/null 2>&1 && ok "removed container $name" || true
  done < <(docker ps -a --format '{{.Names}}' | grep "^${PIPELINE_NAME_PREFIX}-" || true)
fi

if [[ -f "$PIDS_FILE" ]]; then
  while read -r pid; do
    [[ -z "$pid" ]] && continue
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      sleep 1
      kill -9 "$pid" 2>/dev/null || true
      ok "killed worker pid $pid"
    fi
  done < "$PIDS_FILE"
fi

# 本机默认：仅当测试拉起且 KEEP_LOCAL_DEFAULT=0 时停止
if [[ "${KEEP_LOCAL_DEFAULT}" != "1" \
   && -f "$LOCAL_OWNED_FILE" \
   && "$(cat "$LOCAL_OWNED_FILE" 2>/dev/null || echo 0)" == "1" ]]; then
  if [[ -f "$LOCAL_PID_FILE" ]]; then
    pid="$(cat "$LOCAL_PID_FILE")"
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      sleep 1
      kill -9 "$pid" 2>/dev/null || true
      ok "stopped local-default pid=$pid"
    fi
  fi
else
  if [[ -f "$LOCAL_OWNED_FILE" && "$(cat "$LOCAL_OWNED_FILE" 2>/dev/null || echo 0)" == "1" ]]; then
    ok "保留本机默认 TRANSFORM（KEEP_LOCAL_DEFAULT=1）→ ${LOCAL_TRANSFORM_API}"
  fi
fi

ok "cleanup done"
