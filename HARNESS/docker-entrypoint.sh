#!/usr/bin/env bash
# EasyAIoT HARNESS — 启动 DeepSeek Harness Web UI
set -euo pipefail

mkdir -p "${DSH_HOME:-/data/dsh-home}"

export NODE_PATH="/usr/local/lib/node_modules/@deepseek-ai/dsh/node_modules${NODE_PATH:+:${NODE_PATH}}"

WORKSPACE="${HARNESS_WORKSPACE:-/workspace/easyaiot}"
ONTOLOGY="/harness/ontology/AGENTS.md"

if [[ -d "${WORKSPACE}" && -f "${ONTOLOGY}" ]]; then
  if [[ ! -e "${WORKSPACE}/AGENTS.md" ]]; then
    ln -sf "${ONTOLOGY}" "${WORKSPACE}/AGENTS.md" 2>/dev/null \
      || cp "${ONTOLOGY}" "${WORKSPACE}/AGENTS.md"
    echo "[harness] linked ontology -> ${WORKSPACE}/AGENTS.md"
  fi
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

dsh "${LAUNCHER[@]}" &
DSH_PID=$!

for _ in $(seq 1 60); do
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
exec socat TCP-LISTEN:"${PUBLIC_PORT}",fork,reuseaddr,bind=0.0.0.0 TCP:"${HOST}:${DSH_PORT}"
