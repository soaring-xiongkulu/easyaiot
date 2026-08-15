#!/usr/bin/env bash
# EasyAIoT HARNESS — 启动 DeepSeek Harness Web UI
set -euo pipefail

WORKSPACE="${HARNESS_WORKSPACE:-/workspace/easyaiot}"
mkdir -p "${DSH_HOME:-/data/dsh-home}" "${WORKSPACE}"

export NODE_PATH="/usr/local/lib/node_modules/@deepseek-ai/dsh/node_modules${NODE_PATH:+:${NODE_PATH}}"

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

dsh "${LAUNCHER[@]}" &
DSH_PID=$!

for _ in $(seq 1 90); do
  if curl -fsS "http://${HOST}:${DSH_PORT}/" >/dev/null 2>&1; then
    break
  fi
  if ! kill -0 "${DSH_PID}" 2>/dev/null; then
    wait "${DSH_PID}" || true
    exit 1
  fi
  sleep 1
done

echo "[harness] dsh ready, socat 0.0.0.0:${PUBLIC_PORT} -> ${HOST}:${DSH_PORT}"
echo "[harness] note: standalone browser access is redirected by brand.js to IDEA portal"
exec socat TCP-LISTEN:"${PUBLIC_PORT}",fork,reuseaddr,bind=0.0.0.0 TCP:"${HOST}:${DSH_PORT}"
