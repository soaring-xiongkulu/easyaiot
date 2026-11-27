#!/usr/bin/env bash
# EasyAIoT HARNESS — 启动 DeepSeek Harness Web UI
set -euo pipefail

WORKSPACE="${HARNESS_WORKSPACE:-/workspace/easyaiot}"
mkdir -p "${DSH_HOME:-/data/dsh-home}" "${WORKSPACE}"

export NODE_PATH="/usr/local/lib/node_modules/@deepseek-ai/dsh/node_modules${NODE_PATH:+:${NODE_PATH}}"

# plugins 目录可经 volume 热挂载（免重建镜像）；volume 会遮蔽构建期 node_modules 符号链接，这里补齐
mkdir -p /harness/plugins/node_modules/@deepseek-ai
ln -sfn /usr/local/lib/node_modules/@deepseek-ai/dsh/node_modules/@deepseek-ai/dsh-tools \
  /harness/plugins/node_modules/@deepseek-ai/dsh-tools
ln -sfn /usr/local/lib/node_modules/@deepseek-ai/dsh/node_modules/@deepseek-ai/cordis \
  /harness/plugins/node_modules/@deepseek-ai/cordis

DSH_PATCH_SCRIPT="${HARNESS_DSH_PATCH_SCRIPT:-/harness/scripts/patch-dsh-patch-watch.sh}"
if [[ ! -f "${DSH_PATCH_SCRIPT}" ]]; then
  echo "[harness] ERROR: dsh 兼容脚本不存在: ${DSH_PATCH_SCRIPT}" >&2
  exit 1
fi
bash "${DSH_PATCH_SCRIPT}"

if [[ -x /harness/image/apply-branding.sh ]]; then
  /harness/image/apply-branding.sh
fi

ONTOLOGY="/harness/ontology/AGENTS.md"

if [[ -d "${WORKSPACE}" && -f "${ONTOLOGY}" ]]; then
  if [[ ! -e "${WORKSPACE}/AGENTS.md" ]]; then
    ln -sf "${ONTOLOGY}" "${WORKSPACE}/AGENTS.md" 2>/dev/null \
      || cp "${ONTOLOGY}" "${WORKSPACE}/AGENTS.md"
    echo "[harness] linked ontology -> ${WORKSPACE}/AGENTS.md"
  fi
fi

# 默认 Cursor Light 浅色主题
SETTINGS_FILE="${DSH_HOME:-/data/dsh-home}/settings.yaml"
if [[ ! -f "${SETTINGS_FILE}" ]]; then
  cat > "${SETTINGS_FILE}" <<'EOF'
ui-theme:
  preference: light
EOF
  echo "[harness] seeded ui-theme preference=light"
elif grep -q '^ui-theme:' "${SETTINGS_FILE}"; then
  python3 - <<'PY' "${SETTINGS_FILE}"
from pathlib import Path
import re, sys
p = Path(sys.argv[1])
t = p.read_text(encoding="utf-8")
newt = re.sub(r"(ui-theme:\n(?:  .*\n)*?  preference:\s*)\S+", r"\1light", t, count=1)
if "ui-theme:" in t and "preference:" in t:
    if newt != t:
        p.write_text(newt, encoding="utf-8")
        print("updated ui-theme preference=light")
    else:
        # ensure preference line is dark
        if re.search(r"preference:\s*light\b", t):
            print("ui-theme already light")
        else:
            t2 = re.sub(r"(preference:\s*)\S+", r"\1light", t, count=1)
            p.write_text(t2, encoding="utf-8")
            print("forced ui-theme preference=light")
else:
    p.write_text(t.rstrip() + "\n\nui-theme:\n  preference: light\n", encoding="utf-8")
    print("appended ui-theme preference=light")
PY
else
  printf '\nui-theme:\n  preference: light\n' >> "${SETTINGS_FILE}"
  echo "[harness] appended ui-theme preference=light"
fi

# 预装 / 补齐文件树侧边栏等 UX 插件（失败不阻断启动）
if [[ -x /harness/scripts/ensure-ux-plugins.sh ]]; then
  /harness/scripts/ensure-ux-plugins.sh || true
fi

# 只要 EasyAIoT 项目工作区：清掉 /harness 历史会话与其它工作区残留
if [[ -x /harness/scripts/purge-harness-workspace.sh ]]; then
  /harness/scripts/purge-harness-workspace.sh || true
fi

PUBLIC_PORT="${HARNESS_LISTEN_PORT:-3080}"
DSH_PORT="${HARNESS_DSH_INTERNAL_PORT:-3081}"
HOST="127.0.0.1"

LAUNCHER=(--profile web --host "${HOST}" --port "${DSH_PORT}")

if [[ -f /harness/cordis.patch.yml ]]; then
  LAUNCHER=(--profile web --patch /harness/cordis.patch.yml --host "${HOST}" --port "${DSH_PORT}")
fi

if [[ -n "${HARNESS_TRUSTED_HOSTS:-}" ]]; then
  IFS=',' read -ra TRUSTED <<< "${HARNESS_TRUSTED_HOSTS}"
  for th in "${TRUSTED[@]}"; do
    th="$(echo "${th}" | xargs)"
    [[ -n "${th}" ]] && LAUNCHER+=(--trusted-host "${th}")
  done
fi

echo "[harness] starting dsh internal ${HOST}:${DSH_PORT}, public 0.0.0.0:${PUBLIC_PORT}"
echo "[harness] workspace=${WORKSPACE} DSH_HOME=${DSH_HOME:-/data/dsh-home}"

CRED_FILE="${DSH_HOME:-/data/dsh-home}/.credentials.yaml"
if [[ -n "${OPENAI_API_KEY:-}" || -n "${DEEPSEEK_API_KEY:-}" ]]; then
  if [[ -f "${CRED_FILE}" && -s "${CRED_FILE}" ]]; then
    echo "[harness] ${CRED_FILE} already exists — keep Web UI key settings (env seed skipped)"
  else
    mkdir -p "$(dirname "${CRED_FILE}")"
    chmod 700 "$(dirname "${CRED_FILE}")"
    {
      echo "# auto-seeded from HARNESS/harness.env at first container start"
      [[ -n "${DEEPSEEK_API_KEY:-}" ]] && printf 'DEEPSEEK_API_KEY: "%s"\n' "${DEEPSEEK_API_KEY}"
      [[ -n "${OPENAI_API_KEY:-}" ]] && printf 'OPENAI_API_KEY: "%s"\n' "${OPENAI_API_KEY}"
    } > "${CRED_FILE}"
    chmod 600 "${CRED_FILE}"
    echo "[harness] seeded ${CRED_FILE} from environment"
  fi
fi

# 关键：必须从仓库根启动，否则新会话 cwd=/harness，侧边栏只看得到镜像内文件
if [[ ! -d "${WORKSPACE}" ]]; then
  echo "[harness] ERROR: workspace dir missing: ${WORKSPACE}" >&2
  exit 1
fi
cd "${WORKSPACE}"
echo "[harness] process cwd=$(pwd) (explorer root = session cwd)"

# 旧会话若 cwd=/harness，资源管理器只会显示镜像目录（启动时已自动清理）
if [[ -d "${DSH_HOME:-/data/dsh-home}/sessions/--harness--" ]]; then
  echo "[harness] WARN: sessions/--harness-- still present after purge"
fi

CHILD_PIDS=()
CHILD_NAMES=()

cleanup() {
  local exit_code=$?
  local pid=""
  trap - EXIT INT TERM
  for pid in "${CHILD_PIDS[@]}"; do
    kill "${pid}" >/dev/null 2>&1 || true
  done
  for pid in "${CHILD_PIDS[@]}"; do
    wait "${pid}" >/dev/null 2>&1 || true
  done
  exit "${exit_code}"
}

trap cleanup EXIT
trap 'exit 143' INT TERM

wait_for_http() {
  local label="$1"
  local url="$2"
  local attempts="$3"
  local process_pid="$4"
  local attempt=0

  for ((attempt = 1; attempt <= attempts; attempt++)); do
    if curl -fsS --connect-timeout 1 --max-time 3 "${url}" >/dev/null 2>&1; then
      echo "[harness] ${label} ready: ${url}"
      return 0
    fi
    if ! kill -0 "${process_pid}" 2>/dev/null; then
      echo "[harness] ERROR: dsh exited before ${label} became ready" >&2
      return 1
    fi
    sleep 1
  done

  echo "[harness] ERROR: timed out waiting for ${label}: ${url}" >&2
  return 1
}

container_ipv4() {
  local host_name="${HOSTNAME:-}"
  local candidate=""

  if [[ -z "${host_name}" ]]; then
    host_name="$(hostname 2>/dev/null || true)"
  fi
  if [[ -n "${host_name}" && -r /etc/hosts ]]; then
    candidate="$(awk -v host="${host_name}" '
      $1 !~ /:/ && $1 !~ /^127\./ {
        for (i = 2; i <= NF; i++) {
          if ($i == host) { print $1; exit }
        }
      }
    ' /etc/hosts)"
  fi
  if [[ -z "${candidate}" ]]; then
    for candidate in $(hostname -i 2>/dev/null || true); do
      if [[ "${candidate}" != *:* && "${candidate}" != 127.* ]]; then
        printf '%s\n' "${candidate}"
        return 0
      fi
    done
    return 1
  fi
  printf '%s\n' "${candidate}"
}

dsh "${LAUNCHER[@]}" &
DSH_PID=$!
CHILD_PIDS+=("${DSH_PID}")
CHILD_NAMES+=("dsh")

wait_for_http "Web UI" "http://${HOST}:${DSH_PORT}/" 90 "${DSH_PID}"

echo "[harness] dsh ready, socat 0.0.0.0:${PUBLIC_PORT} -> ${HOST}:${DSH_PORT}"
echo "[harness] note: standalone browser access is redirected by brand.js to IDEA portal"

# LLM 统一网关（easyaiot-llm-gateway 插件监听 127.0.0.1:LLM_GATEWAY_PORT），对外暴露同号端口
LLM_GATEWAY_PORT="${LLM_GATEWAY_PORT:-3082}"
wait_for_http "LLM gateway" "http://127.0.0.1:${LLM_GATEWAY_PORT}/api/llm/health" 60 "${DSH_PID}"

CONTAINER_IP="$(container_ipv4)" || {
  echo "[harness] ERROR: 无法确定容器 IPv4，LLM gateway 不能安全对外转发" >&2
  exit 1
}

socat TCP-LISTEN:"${PUBLIC_PORT}",fork,reuseaddr,bind=0.0.0.0 TCP:"${HOST}:${DSH_PORT}" &
PUBLIC_PROXY_PID=$!
CHILD_PIDS+=("${PUBLIC_PROXY_PID}")
CHILD_NAMES+=("Web UI proxy")

# 不能监听 0.0.0.0：插件已占用 127.0.0.1 同号端口。仅绑定容器网卡地址供 Docker 映射访问。
socat TCP-LISTEN:"${LLM_GATEWAY_PORT}",fork,reuseaddr,bind="${CONTAINER_IP}" TCP:"127.0.0.1:${LLM_GATEWAY_PORT}" &
LLM_PROXY_PID=$!
CHILD_PIDS+=("${LLM_PROXY_PID}")
CHILD_NAMES+=("LLM gateway proxy")
echo "[harness] llm-gateway socat ${CONTAINER_IP}:${LLM_GATEWAY_PORT} -> 127.0.0.1:${LLM_GATEWAY_PORT}"

sleep 1
for index in "${!CHILD_PIDS[@]}"; do
  if ! kill -0 "${CHILD_PIDS[$index]}" 2>/dev/null; then
    echo "[harness] ERROR: ${CHILD_NAMES[$index]} failed during startup" >&2
    exit 1
  fi
done

echo "[harness] all services ready; supervising dsh and TCP proxies"
while true; do
  for index in "${!CHILD_PIDS[@]}"; do
    if ! kill -0 "${CHILD_PIDS[$index]}" 2>/dev/null; then
      status=0
      wait "${CHILD_PIDS[$index]}" || status=$?
      echo "[harness] ERROR: ${CHILD_NAMES[$index]} exited unexpectedly (status=${status})" >&2
      exit 1
    fi
  done
  sleep 1
done
