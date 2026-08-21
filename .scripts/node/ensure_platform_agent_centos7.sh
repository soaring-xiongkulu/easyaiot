#!/bin/bash
# CentOS 7.9 手动在宿主机启动控制面 Node Agent（与 iot-node 启动解耦，需运维主动执行）
#
# 相对 ensure_platform_agent.sh 的适配:
#   - 兼容 CentOS 7 bash 4.2 / 系统自带工具
#   - 避免 Python f-string（兼容 3.6 及更早）
#   - 优先探测 python3 / python36 / SCL / pyenv
#   - 可选 --force 跳过 CentOS 7 系统检查
#
# 用法:
#   bash .scripts/node/ensure_platform_agent_centos7.sh
#   bash .scripts/node/ensure_platform_agent_centos7.sh --force
#
# 凭据来源（按优先级）:
#   1. 环境变量 NODE_ID / AGENT_TOKEN（显式指定）
#   2. Gateway bootstrap 接口（需 iot-node 已运行，容器重建后自动同步新令牌）
#   3. 工作目录下已有 agent.env（bootstrap 不可用时回退）
#
# 环境变量:
#   EASYAIOT_GATEWAY_URL              Gateway 地址，默认 http://127.0.0.1:48080
#   EASYAIOT_AGENT_CONTROL_PLANE_URL  Agent 上报地址（可选，默认由 Gateway 推导）
#   EASYAIOT_AGENT_LOCAL_INSTALL_DIR  安装目录，默认 /opt/easyaiot/node-agent
#   EASYAIOT_AGENT_SOURCE_PATH        源码目录，默认 <repo>/SENTINEL
#   EASYAIOT_AGENT_PORT               监听端口，默认 9100
#   EASYAIOT_AGENT_LOCAL_PYTHON       Python 命令，默认自动探测
#   AGENT_USE_CACHED_ENV=1            跳过 bootstrap，仅使用本地 agent.env（离线环境）
#   AGENT_BOOTSTRAP_WAIT_SECONDS=180  install 场景等待 bootstrap 就绪的最长秒数
#   AGENT_BOOTSTRAP_RETRY_INTERVAL=3  轮询间隔（秒）
set -euo pipefail

FORCE_OS_CHECK=false

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志一律走 stderr，避免被 $(...) 捕获吞掉（否则会表现为“卡住无输出”）
print_info()    { echo -e "${BLUE}[platform-agent]${NC} $1" >&2; }
print_success() { echo -e "${GREEN}[platform-agent]${NC} $1" >&2; }
print_warning() { echo -e "${YELLOW}[platform-agent]${NC} $1" >&2; }
print_error()   { echo -e "${RED}[platform-agent]${NC} $1" >&2; }

show_help() {
  cat <<'EOF'
CentOS 7.9 启动控制面 Node Agent

用法:
  ./ensure_platform_agent_centos7.sh [选项]

选项:
  -h, --help    显示此帮助
  -f, --force   跳过 CentOS 7 系统检查

环境变量与凭据优先级见脚本头部注释。
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      show_help
      exit 0
      ;;
    -f|--force)
      FORCE_OS_CHECK=true
      shift
      ;;
    *)
      print_error "未知参数: $1"
      show_help
      exit 1
      ;;
  esac
done

check_centos7() {
  if [[ "$FORCE_OS_CHECK" == "true" ]]; then
    print_warning "已跳过 CentOS 7 系统检查 (--force)"
    return 0
  fi

  local os_id="" os_version=""
  if [[ -f /etc/os-release ]]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    os_id="${ID:-}"
    os_version="${VERSION_ID:-}"
  elif [[ -f /etc/redhat-release ]]; then
    if grep -qi "centos" /etc/redhat-release 2>/dev/null; then
      os_id="centos"
    fi
    os_version="$(grep -oE '[0-9]+(\.[0-9]+)?' /etc/redhat-release 2>/dev/null | head -1 || true)"
  fi

  if [[ "$os_id" != "centos" ]]; then
    print_warning "当前系统不是 CentOS (ID=${os_id:-未知})，脚本仍可继续"
    print_info "非 CentOS 环境请使用: bash .scripts/node/ensure_platform_agent.sh"
    print_info "或加 --force: bash .scripts/node/ensure_platform_agent_centos7.sh --force"
  elif [[ "${os_version%%.*}" != "7" ]]; then
    print_warning "检测到 CentOS ${os_version}，本脚本针对 CentOS 7.9 优化"
  else
    print_success "CentOS 7.x (${os_version})"
  fi
}

# CentOS 7 默认可能无 python3，按常见路径探测
resolve_default_python() {
  local candidate
  if [[ -n "${EASYAIOT_AGENT_LOCAL_PYTHON:-}" ]]; then
    echo "$EASYAIOT_AGENT_LOCAL_PYTHON"
    return 0
  fi
  for candidate in \
    python3 \
    python36 \
    python3.6 \
    python3.8 \
    python3.9 \
    python3.10 \
    python3.11 \
    python3.12 \
    /opt/rh/rh-python36/root/usr/bin/python3 \
    /opt/rh/rh-python38/root/usr/bin/python3 \
    "${HOME:-/root}/.pyenv/shims/python3" \
    /usr/local/bin/python3; do
    if command -v "$candidate" >/dev/null 2>&1 || [[ -x "$candidate" ]]; then
      if command -v "$candidate" >/dev/null 2>&1; then
        command -v "$candidate"
      else
        echo "$candidate"
      fi
      return 0
    fi
  done
  echo "python3"
}

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
GATEWAY_URL="${EASYAIOT_GATEWAY_URL:-http://127.0.0.1:48080}"
INSTALL_DIR="${EASYAIOT_AGENT_LOCAL_INSTALL_DIR:-/opt/easyaiot/node-agent}"
SOURCE_DIR="${EASYAIOT_AGENT_SOURCE_PATH:-$ROOT/SENTINEL}"
AGENT_PORT="${EASYAIOT_AGENT_PORT:-9100}"
PYTHON="$(resolve_default_python)"
AGENT_BOOTSTRAP_WAIT_SECONDS="${AGENT_BOOTSTRAP_WAIT_SECONDS:-180}"
AGENT_BOOTSTRAP_RETRY_INTERVAL="${AGENT_BOOTSTRAP_RETRY_INTERVAL:-3}"

# CentOS 7 bash 4.2: 用 epoch 秒数代替 SECONDS，避免嵌套/重置干扰
now_epoch() {
  date +%s
}

is_port_listening() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    # CentOS 7 ss 输出可能为 *:9100 / 0.0.0.0:9100 / :::9100
    ss -ltn 2>/dev/null | grep -E "[:.]${port}([[:space:]]|$)" >/dev/null 2>&1
    return $?
  fi
  if command -v nc >/dev/null 2>&1; then
    nc -z 127.0.0.1 "$port" >/dev/null 2>&1
    return $?
  fi
  # 回退: /dev/tcp（bash 内建）
  (echo >/dev/tcp/127.0.0.1/"$port") >/dev/null 2>&1
}

agent_health_ready() {
  if command -v curl >/dev/null 2>&1; then
    curl -fsS --connect-timeout 2 "http://127.0.0.1:${AGENT_PORT}/health" >/dev/null 2>&1
    return $?
  fi
  is_port_listening "$AGENT_PORT"
}

wait_for_agent_ready() {
  local deadline
  deadline=$(($(now_epoch) + 20))
  while [[ $(now_epoch) -lt $deadline ]]; do
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
  for candidate in \
    "$PYTHON" \
    python3 \
    python36 \
    python3.6 \
    "${HOME:-/root}"/.pyenv/versions/*/bin/python \
    /root/.pyenv/versions/*/bin/python \
    /opt/rh/rh-python36/root/usr/bin/python3 \
    /opt/rh/rh-python38/root/usr/bin/python3; do
    [[ -x "$candidate" ]] || command -v "$candidate" >/dev/null 2>&1 || continue
    if ! command -v "$candidate" >/dev/null 2>&1 && [[ ! -x "$candidate" ]]; then
      continue
    fi
    if "$candidate" -m pip --version >/dev/null 2>&1; then
      if command -v "$candidate" >/dev/null 2>&1; then
        command -v "$candidate"
      else
        echo "$candidate"
      fi
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
  # shellcheck source=/dev/null
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
  # 短超时：Gateway 未起时避免 curl 长时间挂死（CentOS7 默认 TCP 超时可达数分钟）
  # 使用 .format 兼容 CentOS 7 常见 Python 3.6（及更早）
  # JSON 解析优先用轻量系统 python，避免 conda 环境每次冷启动过慢
  local json_python="$PYTHON"
  if command -v /usr/bin/python3 >/dev/null 2>&1; then
    json_python="/usr/bin/python3"
  elif command -v python36 >/dev/null 2>&1; then
    json_python="$(command -v python36)"
  fi
  curl -fsS --connect-timeout 2 --max-time 5 \
    "${GATEWAY_URL}/admin-api/node/platform-agent-bootstrap" 2>/dev/null \
    | PYTHONPATH= "$json_python" -c "
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
    print('{0}|{1}|{2}'.format(node_id, token, port))
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

  local deadline creds="" elapsed=0
  deadline=$(($(now_epoch) + AGENT_BOOTSTRAP_WAIT_SECONDS))
  print_info "等待 bootstrap 就绪（最长 ${AGENT_BOOTSTRAP_WAIT_SECONDS}s）: ${GATEWAY_URL}/admin-api/node/platform-agent-bootstrap"
  print_info "若 Gateway 未启动，可 Ctrl+C 后改用: AGENT_USE_CACHED_ENV=1 $0"
  while [[ $(now_epoch) -lt $deadline ]]; do
    creds="$(fetch_platform_node_credentials)"
    if [[ -n "$creds" ]]; then
      echo "$creds"
      return 0
    fi
    elapsed=$((elapsed + AGENT_BOOTSTRAP_RETRY_INTERVAL))
    if [[ $((elapsed % 15)) -eq 0 ]] || [[ "$elapsed" -eq "$AGENT_BOOTSTRAP_RETRY_INTERVAL" ]]; then
      print_info "仍在等待 bootstrap... (${elapsed}s/${AGENT_BOOTSTRAP_WAIT_SECONDS}s)"
    fi
    sleep "$AGENT_BOOTSTRAP_RETRY_INTERVAL"
  done
  print_warning "bootstrap 超时，将尝试使用本地 agent.env"
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
          print_warning "本地 agent.env 与平台不一致，已从 bootstrap 同步 (nodeId=${boot_id})"
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
      # shellcheck disable=SC2086
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
      print_info "已同步 ${f} -> ${INSTALL_DIR}/"
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
    print_success "已通过 systemd 重启 easyaiot-node-agent"
    if wait_for_agent_ready; then
      return 0
    fi
    print_error "systemd 服务未在 ${AGENT_PORT} 端口就绪"
    sudo systemctl status easyaiot-node-agent --no-pager -l 2>&1 | tail -30 >&2 || true
    return 1
  fi

  mkdir -p "${HOME}/logs"
  local log_file="${HOME}/logs/platform-node-agent.log"
  if [[ -x "${work_dir}/agent-python.sh" ]]; then
    if ! verify_agent_python "${work_dir}/agent-python.sh"; then
      print_error "Agent 独立 Python 环境缺少 flask/psutil/requests"
      print_error "请执行: sudo bash ${SOURCE_DIR}/install.sh install"
      return 1
    fi
    stop_running_agent
    nohup "${work_dir}/agent-python.sh" >>"$log_file" 2>&1 &
  else
    if ! verify_agent_python "$PYTHON"; then
      local repo_root target_python pip_python
      repo_root="$(cd "${SOURCE_DIR}/.." && pwd)"
      # 避免 f-string，兼容 CentOS 7 Python 3.6-
      target_python="$($PYTHON -c 'import sys; print("{0}.{1}".format(sys.version_info.major, sys.version_info.minor))' 2>/dev/null || echo '3.6')"
      pip_python="$(resolve_python_with_pip || true)"
      print_error "宿主机 ${PYTHON} 缺少 Agent 依赖（flask/psutil/requests）"
      if [[ -n "$pip_python" ]]; then
        print_info "检测到带 pip 的 Python: ${pip_python}"
        print_info "sudo -H env AGENT_TARGET_PYTHON=${target_python} PYTHON=${pip_python} bash ${SOURCE_DIR}/export_pip_wheels.sh"
      else
        print_info "CentOS 7 可先安装: sudo yum install -y python3 python3-pip"
      fi
      print_info "无宿主机 pip 时可使用 AI 镜像生成离线依赖:"
      print_info "sudo docker run --rm --entrypoint bash -v \"${repo_root}:/repo\" -w /repo/SENTINEL ai-service:latest -lc 'AGENT_TARGET_PYTHON=${target_python} PYTHON=python bash export_pip_wheels.sh'"
      print_info "然后执行: sudo bash ${SOURCE_DIR}/install.sh install"
      return 1
    fi
    stop_running_agent
    set -a
    # shellcheck source=/dev/null
    source "${work_dir}/agent.env"
    set +a
    nohup "$PYTHON" "${work_dir}/run_agent.py" >>"$log_file" 2>&1 &
  fi
  print_success "已后台启动 Agent，日志: ${log_file}"
  if wait_for_agent_ready; then
    return 0
  fi
  print_error "Agent 启动后未在 ${AGENT_PORT} 端口就绪，最近日志:"
  tail -30 "$log_file" >&2 || true
  return 1
}

main() {
  check_centos7

  if ! command -v curl >/dev/null 2>&1; then
    print_error "未找到 curl，请安装: sudo yum install -y curl"
    exit 1
  fi

  if ! command -v "$PYTHON" >/dev/null 2>&1 && [[ ! -x "$PYTHON" ]]; then
    print_error "未找到 Python3（当前: ${PYTHON}）"
    print_info "CentOS 7 安装示例: sudo yum install -y python3 python3-pip"
    print_info "或指定: EASYAIOT_AGENT_LOCAL_PYTHON=/path/to/python3 bash $0"
    exit 1
  fi
  print_info "使用 Python: ${PYTHON}"

  local work_dir
  work_dir="$(resolve_work_dir)" || {
    print_error "未找到 Agent 目录（${INSTALL_DIR} 或 ${SOURCE_DIR}）"
    print_error "请先执行 NODE/install.sh 或指定 EASYAIOT_AGENT_SOURCE_PATH"
    exit 1
  }

  local creds node_id agent_token port
  creds="$(resolve_credentials "$work_dir")" || {
    print_error "缺少 NODE_ID / AGENT_TOKEN"
    print_error "请编辑 ${work_dir}/agent.env，或确保 Gateway 可访问 bootstrap 接口"
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
      print_success "端口 ${AGENT_PORT} 已有 Agent 监听且凭据一致，跳过"
      exit 0
    fi
    print_warning "agent.env 缺少 PLATFORM_AGENT=1，将刷新并重启"
    creds_changed=1
  fi

  if [[ "$agent_running" -eq 1 ]] && [[ "$creds_changed" -eq 1 ]]; then
    print_info "检测到凭据变更，重启 Agent (nodeId=${node_id})"
  fi

  if [[ "$agent_running" -eq 1 ]] && [[ "$code_stale" -eq 1 ]]; then
    print_info "检测到 Agent 代码更新，将同步并重启"
  fi

  if [[ "$agent_running" -eq 0 ]]; then
    print_info "端口 ${AGENT_PORT} 未监听，将启动 Agent"
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
    print_success "已写入 ${work_dir}/agent.env (nodeId=${node_id})"
  fi

  if [[ "$needs_env_write" -eq 1 ]] || [[ "$code_stale" -eq 1 ]] || [[ "$agent_running" -eq 0 ]]; then
    restart_agent_service "$work_dir"
  fi

  if ! agent_health_ready; then
    print_error "Agent 健康检查失败: http://127.0.0.1:${AGENT_PORT}/health"
    exit 1
  fi
  print_success "Agent 已就绪: http://127.0.0.1:${AGENT_PORT}/health"
}

main "$@"
