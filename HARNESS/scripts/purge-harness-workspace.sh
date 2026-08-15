#!/usr/bin/env bash
# 只保留 EasyAIoT 项目工作区：删除 cwd=/harness 的历史会话与其它工作区残留
set -euo pipefail

DSH_HOME="${DSH_HOME:-/data/dsh-home}"
WORKSPACE="${HARNESS_WORKSPACE:-/workspace/easyaiot}"
SESSIONS_ROOT="${DSH_HOME}/sessions"
WS_JSON="${DSH_HOME}/storages/workspace.json"

say() { printf '[harness-ws] %s\n' "$*"; }

# 解析真实路径，便于和 registry 里 realpath 后的 path 对齐
KEEP_PATH="${WORKSPACE}"
if [[ -d "${WORKSPACE}" ]]; then
  KEEP_PATH="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "${WORKSPACE}")"
fi

# 1) 删掉镜像目录会话（资源管理器只会显示 harness/）
if [[ -d "${SESSIONS_ROOT}/--harness--" ]]; then
  rm -rf "${SESSIONS_ROOT}/--harness--"
  say "removed sessions/--harness--"
fi

shopt -s nullglob
for d in "${SESSIONS_ROOT}"/*; do
  [[ -d "$d" ]] || continue
  base="$(basename "$d")"
  # 保留 easyaiot 工作区会话目录
  if [[ "$base" == "--workspace-easyaiot--" || "$base" == *"easyaiot"* ]]; then
    continue
  fi
  # 删掉明显属于 /harness 或其它非项目 cwd 的会话桶
  if [[ "$base" == "--harness--" || "$base" == *harness* || "$base" == "_no-cwd" ]]; then
    rm -rf "$d"
    say "removed sessions/${base}"
  fi
done
shopt -u nullglob

# 2) workspace.json：只保留 EasyAIoT 路径
if [[ -f "${WS_JSON}" ]]; then
  python3 - <<'PY' "${WS_JSON}" "${KEEP_PATH}" "${WORKSPACE}"
import json, os, sys
from pathlib import Path
path = Path(sys.argv[1])
keep_real = os.path.realpath(sys.argv[2])
keep_raw = os.path.realpath(sys.argv[3]) if sys.argv[3] else keep_real
allowed = {keep_real.rstrip("/"), keep_raw.rstrip("/"), "/workspace/easyaiot"}

data = json.loads(path.read_text(encoding="utf-8"))
workspaces = (data.get("tables") or {}).get("workspaces") or {}
kept, removed = {}, []
for wid, rec in workspaces.items():
    p = os.path.realpath(str(rec.get("path") or "")).rstrip("/")
    if p in allowed or p.endswith("/workspace/easyaiot"):
        rec = dict(rec)
        rec["path"] = keep_real
        rec["title"] = "EasyAIoT"
        kept[wid] = rec
    else:
        removed.append(f"{wid}:{rec.get('path')}")

data.setdefault("tables", {})["workspaces"] = kept
data.setdefault("global", {})
data["global"]["workspaceIds"] = list(kept.keys())
data["global"]["initialized"] = True
# 清掉可能指向已删会话的投影缓存标记由 dsh 自行重建
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"kept={len(kept)} removed={len(removed)}")
if removed:
    print("removed: " + ", ".join(removed))
PY
fi

# 3) 投影缓存若存在可删，避免左侧仍刷出旧会话
if [[ -f "${DSH_HOME}/storages/session_projcache.json" ]]; then
  rm -f "${DSH_HOME}/storages/session_projcache.json"
  say "cleared session projection cache"
fi

say "only EasyAIoT workspace retained (path=${KEEP_PATH})"
