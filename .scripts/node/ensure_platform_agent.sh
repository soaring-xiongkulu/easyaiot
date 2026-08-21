#!/usr/bin/env bash
# 手动在宿主机启动控制面 Node Agent（与 iot-node 启动解耦，需运维主动执行）
#
# 用法:
#   bash .scripts/node/ensure_platform_agent.sh
#
# 凭据来源（按优先级）:
#   1. 环境变量 NODE_ID / AGENT_TOKEN（显式指定）
#   2. Gateway bootstrap 接口（需 iot-node 已运行，容器重建后自动同步新令牌）
#   3. 工作目录下已有 agent.env（bootstrap 不可用时回退）
#
# 环境变量:
#   EASYAIOT_GATEWAY_URL          Gateway 地址，默认 http://127.0.0.1:48080
#   EASYAIOT_AGENT_CONTROL_PLANE_URL  Agent 上报地址（可选，默认由 Gateway 推导）
#   EASYAIOT_AGENT_LOCAL_INSTALL_DIR  安装目录，默认 /opt/easyaiot/node-agent
#   EASYAIOT_AGENT_SOURCE_PATH        源码目录，默认 <repo>/SENTINEL
#   EASYAIOT_AGENT_PORT               监听端口，默认 9100
#   EASYAIOT_AGENT_LOCAL_PYTHON       Python 命令，默认 python3
#   AGENT_USE_CACHED_ENV=1          跳过 bootstrap，仅使用本地 agent.env（离线环境）
#   AGENT_BOOTSTRAP_WAIT_SECONDS=180  install 场景等待 bootstrap 就绪的最长秒数
#   AGENT_BOOTSTRAP_RETRY_INTERVAL=3  轮询间隔（秒）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
GATEWAY_URL="${EASYAIOT_GATEWAY_URL:-http://127.0.0.1:48080}"
INSTALL_DIR="${EASYAIOT_AGENT_LOCAL_INSTALL_DIR:-/opt/easyaiot/node-agent}"
SOURCE_DIR="${EASYAIOT_AGENT_SOURCE_PATH:-$ROOT/SENTINEL}"
AGENT_PORT="${EASYAIOT_AGENT_PORT:-9100}"
PYTHON="${EASYAIOT_AGENT_LOCAL_PYTHON:-python3}"
AGENT_BOOTSTRAP_WAIT_SECONDS="${AGENT_BOOTSTRAP_WAIT_SECONDS:-180}"
AGENT_BOOTSTRAP_RETRY_INTERVAL="${AGENT_BOOTSTRAP_RETRY_INTERVAL:-3}"

is_port_listening() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -ltn | grep -q ":${port} "
    return $?
  fi
  if command -v nc >/dev/null 2>&1; then
    nc -z 127.0.0.1 "$port" >/dev/null 2>&1
    return $?
  fi
  return 1
}

agent_health_ready() {
  if command -v curl >/dev/null 2>&1; then
    curl -fsS --connect-timeout 2 "http://127.0.0.1:${AGENT_PORT}/health" >/dev/null 2>&1
    return $?
  fi
  is_port_listening "$AGENT_PORT"
}

wait_for_agent_ready() {
  local deadline=$((SECONDS + 20))
  while [[ $SECONDS -lt $deadline ]]; do
    if agent_health_ready; then
      return 0
    fi
    sleep 1
  done
  return 1
}

verify_agent_python() {
  local runner="$1"
  "$runner" -c 'import flask, psutil, requests' >/dev/null 2>&1
}

resolve_python_with_pip() {
  local candidate
  for candidate in "$PYTHON" "${HOME:-/root}"/.pyenv/versions/*/bin/python /root/.pyenv/versions/*/bin/python; do
    [[ -x "$candidate" ]] || continue
    if "$candidate" -m pip --version >/dev/null 2>&1; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

resolve_work_dir() {
  if [[ -f "$INSTALL_DIR/run_agent.py" ]]; then
    echo "$INSTALL_DIR"
    return 0
  fi
  if [[ -f "$SOURCE_DIR/run_agent.py" ]]; then
    echo "$SOURCE_DIR"
    return 0
  fi
  return 1
}

read_env_credentials() {
  local env_file="$1"
  [[ -f "$env_file" ]] || return 1
  local node_id="" agent_token="" port=""
  # shellcheck disable=SC1090
  set -a
  source "$env_file"
  set +a
  node_id="${NODE_ID:-}"
  agent_token="${AGENT_TOKEN:-}"
  port="${AGENT_LISTEN_PORT:-$AGENT_PORT}"
  if [[ -n "$node_id" && -n "$agent_token" ]]; then
    echo "${node_id}|${agent_token}|${port}"
    return 0
  fi
  return 1
}

fetch_platform_node_credentials() {
  curl -fsS \
    "${GATEWAY_URL}/admin-api/node/platform-agent-bootstrap" 2>/dev/null \
    | PYTHONPATH= python3 -c "
import json, sys
raw = sys.stdin.read()
try:
    data = json.loads(raw)
except Exception:
    sys.exit(1)
payload = data.get('data') or data
node_id = payload.get('nodeId') or payload.get('id')
token = payload.get('agentToken')
port = payload.get('agentPort') or 9100
if node_id and token:
    print(node_id, token, port, sep='|')
" 2>/dev/null || true
}

write_agent_env() {
  local work_dir="$1" node_id="$2" agent_token="$3" port="$4"
  local cp_url="${EASYAIOT_AGENT_CONTROL_PLANE_URL:-${GATEWAY_URL%/}/admin-api/node/agent}"
  cat >"${work_dir}/agent.env" <<EOF
PLATFORM_AGENT=1
NODE_ID=${node_id}
AGENT_TOKEN=${agent_token}
CONTROL_PLANE_URL=${cp_url}
HEARTBEAT_INTERVAL=10
BOOTSTRAP_WAIT_SECONDS=${AGENT_BOOTSTRAP_WAIT_SECONDS}
BOOTSTRAP_RETRY_INTERVAL=${AGENT_BOOTSTRAP_RETRY_INTERVAL}
AGENT_LISTEN_HOST=0.0.0.0
AGENT_LISTEN_PORT=${port}
AI_ROOT=${EASYAIOT_AI_ROOT:-$ROOT/AI}
VIDEO_ROOT=${EASYAIOT_VIDEO_ROOT:-$ROOT/VIDEO}
MEDIA_CLUSTER_ROOT=/opt/easyaiot/media-cluster
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=your-secret
EOF
}

fetch_platform_node_credentials_with_wait() {
  if [[ -n "${NODE_ID:-}" && -n "${AGENT_TOKEN:-}" ]]; then
    return 1
  fi
  if [[ "${AGENT_USE_CACHED_ENV:-}" == "1" ]]; then
    return 1
  fi

  local deadline=$((SECONDS + AGENT_BOOTSTRAP_WAIT_SECONDS))
  local creds=""
  echo "[platform-agent] 等待 bootstrap 就绪（最长 ${AGENT_BOOTSTRAP_WAIT_SECONDS}s）..." >&2
  while [[ $SECONDS -lt $deadline ]]; do
    creds="$(fetch_platform_node_credentials)"
    if [[ -n "$creds" ]]; then
      echo "$creds"
      return 0
    fi
    sleep "$AGENT_BOOTSTRAP_RETRY_INTERVAL"
  done
  echo "[platform-agent] bootstrap 超时，将尝试使用本地 agent.env" >&2
  return 1
}

resolve_credentials() {
  local work_dir="$1"
  local creds=""

  if [[ -n "${NODE_ID:-}" && -n "${AGENT_TOKEN:-}" ]]; then
    echo "${NODE_ID}|${AGENT_TOKEN}|${AGENT_LISTEN_PORT:-$AGENT_PORT}"
    return 0
  fi

  if [[ "${AGENT_USE_CACHED_ENV:-}" != "1" ]]; then
    creds="$(fetch_platform_node_credentials_with_wait || true)"
    if [[ -z "$creds" ]]; then
      creds="$(fetch_platform_node_credentials)"
    fi
    if [[ -n "$creds" ]]; then
      local cached=""
      cached="$(read_env_credentials "${work_dir}/agent.env" 2>/dev/null || true)"
      if [[ -n "$cached" && "$cached" != "$creds" ]]; then
        local cached_id cached_token boot_id boot_token
        IFS='|' read -r cached_id cached_token _ <<<"$cached"
        IFS='|' read -r boot_id boot_token _ <<<"$creds"
        if [[ "$cached_id" != "$boot_id" || "$cached_token" != "$boot_token" ]]; then
          echo "[platform-agent] 本地 agent.env 与平台不一致，已从 bootstrap 同步 (nodeId=${boot_id})" >&2
        fi
      fi
      echo "$creds"
      return 0
    fi
  fi

  creds="$(read_env_credentials "${work_dir}/agent.env" 2>/dev/null || true)"
  if [[ -n "$creds" ]]; then
    echo "$creds"
    return 0
  fi
  return 1
}

stop_running_agent() {
  if pkill -f '/opt/easyaiot/node-agent/run_agent.py' 2>/dev/null; then
    sleep 1
  fi
  if pkill -f 'NODE/run_agent.py' 2>/dev/null; then
    sleep 1
  fi
  if [[ -f /etc/systemd/system/easyaiot-node-agent.service ]]; then
    if systemctl is-active easyaiot-node-agent >/dev/null 2>&1; then
      sudo systemctl stop easyaiot-node-agent 2>/dev/null || true
    fi
    return 0
  fi
  if command -v fuser >/dev/null 2>&1; then
    sudo fuser -k "${AGENT_PORT}/tcp" >/dev/null 2>&1 || true
  elif command -v lsof >/dev/null 2>&1; then
    local pids
    pids="$(lsof -ti tcp:"${AGENT_PORT}" 2>/dev/null || true)"
    if [[ -n "$pids" ]]; then
      kill $pids 2>/dev/null || true
      sleep 1
    fi
  fi
}

sync_agent_runtime_files() {
  local work_dir="$1"
  if [[ "$work_dir" != "$INSTALL_DIR" || ! -d "$SOURCE_DIR" ]]; then
    return 0
  fi
  local f
  for f in run_agent.py agent_server.py media_manager.py mqtt_manager.py workload_manager.py; do
    if [[ ! -f "${SOURCE_DIR}/${f}" ]]; then
      continue
    fi
    if [[ -f "${INSTALL_DIR}/${f}" ]] && cmp -s "${SOURCE_DIR}/${f}" "${INSTALL_DIR}/${f}"; then
      continue
    fi
    if cp "${SOURCE_DIR}/${f}" "${INSTALL_DIR}/${f}" 2>/dev/null \
      || sudo cp "${SOURCE_DIR}/${f}" "${INSTALL_DIR}/${f}" 2>/dev/null; then
      echo "[platform-agent] 已同步 ${f} -> ${INSTALL_DIR}/" >&2
    fi
  done
}

agent_code_stale() {
  [[ -f "${SOURCE_DIR}/run_agent.py" && -f "${INSTALL_DIR}/run_agent.py" ]] || return 1
  ! cmp -s "${SOURCE_DIR}/run_agent.py" "${INSTALL_DIR}/run_agent.py"
}

restart_agent_service() {
  local work_dir="$1"
  sync_agent_runtime_files "$work_dir"
  if [[ -f /etc/systemd/system/easyaiot-node-agent.service ]]; then
    if [[ -x "${INSTALL_DIR}/install.sh" ]]; then
      sudo bash "${INSTALL_DIR}/install.sh" restart
    else
      sudo systemctl daemon-reload
      sudo systemctl enable easyaiot-node-agent >/dev/null 2>&1 || true
      sudo systemctl restart easyaiot-node-agent
    fi
    echo "[platform-agent] 已通过 systemd 重启 easyaiot-node-agent"
    if wait_for_agent_ready; then
      return 0
    fi
    echo "[platform-agent] systemd 服务未在 ${AGENT_PORT} 端口就绪" >&2
    sudo systemctl status easyaiot-node-agent --no-pager -l 2>&1 | tail -30 >&2 || true
    return 1
  fi

  mkdir -p "${HOME}/logs"
  local log_file="${HOME}/logs/platform-node-agent.log"
  if [[ -x "${work_dir}/agent-python.sh" ]]; then
    if ! verify_agent_python "${work_dir}/agent-python.sh"; then
      echo "[platform-agent] Agent 独立 Python 环境缺少 flask/psutil/requests" >&2
      echo "[platform-agent] 请执行: sudo bash ${SOURCE_DIR}/install.sh install" >&2
      return 1
    fi
    stop_running_agent
    nohup "${work_dir}/agent-python.sh" >>"$log_file" 2>&1 &
  else
    if ! verify_agent_python "$PYTHON"; then
      local repo_root target_python pip_python
      repo_root="$(cd "${SOURCE_DIR}/.." && pwd)"
      target_python="$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo '3.12')"
      pip_python="$(resolve_python_with_pip || true)"
      echo "[platform-agent] 宿主机 ${PYTHON} 缺少 Agent 依赖（flask/psutil/requests）" >&2
      if [[ -n "$pip_python" ]]; then
        echo "[platform-agent] 检测到带 pip 的 Python: ${pip_python}" >&2
        echo "[platform-agent] sudo -H env AGENT_TARGET_PYTHON=${target_python} PYTHON=${pip_python} bash ${SOURCE_DIR}/export_pip_wheels.sh" >&2
      fi
      echo "[platform-agent] 无宿主机 pip 时可使用 AI 镜像生成离线依赖:" >&2
      echo "[platform-agent] sudo docker run --rm --entrypoint bash -v \"${repo_root}:/repo\" -w /repo/SENTINEL ai-service:latest -lc 'AGENT_TARGET_PYTHON=${target_python} PYTHON=python bash export_pip_wheels.sh'" >&2
      echo "[platform-agent] 然后执行: sudo bash ${SOURCE_DIR}/install.sh install" >&2
      return 1
    fi
    stop_running_agent
    set -a
    # shellcheck source=/dev/null
    source "${work_dir}/agent.env"
    set +a
    nohup "$PYTHON" "${work_dir}/run_agent.py" >>"$log_file" 2>&1 &
  fi
  echo "[platform-agent] 已后台启动 Agent，日志: ${log_file}"
  if wait_for_agent_ready; then
    return 0
  fi
  echo "[platform-agent] Agent 启动后未在 ${AGENT_PORT} 端口就绪，最近日志:" >&2
  tail -30 "$log_file" >&2 || true
  return 1
}

main() {
  local work_dir
  work_dir="$(resolve_work_dir)" || {
    echo "[platform-agent] 未找到 Agent 目录（${INSTALL_DIR} 或 ${SOURCE_DIR}）" >&2
    echo "[platform-agent] 请先执行 NODE/install.sh 或指定 EASYAIOT_AGENT_SOURCE_PATH" >&2
    exit 1
  }

  local creds node_id agent_token port
  creds="$(resolve_credentials "$work_dir")" || {
    echo "[platform-agent] 缺少 NODE_ID / AGENT_TOKEN" >&2
    echo "[platform-agent] 请编辑 ${work_dir}/agent.env，或确保 Gateway 可访问 bootstrap 接口" >&2
    exit 1
  }
  IFS='|' read -r node_id agent_token port <<<"$creds"
  AGENT_PORT="${port:-$AGENT_PORT}"

  local cached="" creds_changed=0
  cached="$(read_env_credentials "${work_dir}/agent.env" 2>/dev/null || true)"
  if [[ -n "$cached" ]]; then
    local cached_id cached_token
    IFS='|' read -r cached_id cached_token _ <<<"$cached"
    if [[ "$cached_id" != "$node_id" || "$cached_token" != "$agent_token" ]]; then
      creds_changed=1
    fi
  else
    creds_changed=1
  fi

  local agent_running=0 code_stale=0
  if agent_health_ready; then
    agent_running=1
  fi
  if agent_code_stale; then
    code_stale=1
  fi

  if [[ "$agent_running" -eq 1 ]] && [[ "$creds_changed" -eq 0 ]] && [[ "$code_stale" -eq 0 ]]; then
    if [[ -f "${work_dir}/agent.env" ]] && grep -q '^PLATFORM_AGENT=1' "${work_dir}/agent.env" 2>/dev/null; then
      echo "[platform-agent] 端口 ${AGENT_PORT} 已有 Agent 监听且凭据一致，跳过"
      exit 0
    fi
    echo "[platform-agent] agent.env 缺少 PLATFORM_AGENT=1，将刷新并重启"
    creds_changed=1
  fi

  if [[ "$agent_running" -eq 1 ]] && [[ "$creds_changed" -eq 1 ]]; then
    echo "[platform-agent] 检测到凭据变更，重启 Agent (nodeId=${node_id})"
  fi

  if [[ "$agent_running" -eq 1 ]] && [[ "$code_stale" -eq 1 ]]; then
    echo "[platform-agent] 检测到 Agent 代码更新，将同步并重启"
  fi

  if [[ "$agent_running" -eq 0 ]]; then
    echo "[platform-agent] 端口 ${AGENT_PORT} 未监听，将启动 Agent"
  fi

  local needs_env_write=0
  if [[ "$creds_changed" -eq 1 ]]; then
    needs_env_write=1
  elif [[ ! -f "${work_dir}/agent.env" ]] \
    || ! grep -q '^PLATFORM_AGENT=1' "${work_dir}/agent.env" 2>/dev/null; then
    needs_env_write=1
  fi

  if [[ "$needs_env_write" -eq 1 ]]; then
    write_agent_env "$work_dir" "$node_id" "$agent_token" "${port:-$AGENT_PORT}"
    echo "[platform-agent] 已写入 ${work_dir}/agent.env (nodeId=${node_id})"
  fi

  if [[ "$needs_env_write" -eq 1 ]] || [[ "$code_stale" -eq 1 ]] || [[ "$agent_running" -eq 0 ]]; then
    restart_agent_service "$work_dir"
  fi

  if ! agent_health_ready; then
    echo "[platform-agent] Agent 健康检查失败: http://127.0.0.1:${AGENT_PORT}/health" >&2
    exit 1
  fi
}

main "$@"