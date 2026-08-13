#!/usr/bin/env bash
set -euo pipefail

DATA_ROOT="${HOME}/project-data"
CONTINUE_DIR="${DATA_ROOT}/continue"
CONFIG="${CONTINUE_DIR}/config.yaml"
ENV_FILE="${DATA_ROOT}/.ai-env"

TPL_CANDIDATES=(
  "${IDEA_OPEN_FOLDER:-/home/coder/easyaiot}/.continue-template/config.yaml"
  /opt/idea/workspace-template/continue/config.yaml
)

usage() {
  cat <<'EOF'
用法:
  bash scripts/idea/setup-ai.sh

将个人 OpenAI / 兼容 API Key 写入本工作区（Continue）。
密钥只保存在个人数据卷，不会上传门户。

也可非交互:
  OPENAI_API_KEY=sk-xxx bash scripts/idea/setup-ai.sh
  OPENAI_API_KEY=sk-xxx OPENAI_API_BASE=https://api.openai.com/v1 OPENAI_MODEL=gpt-4o \
    bash scripts/idea/setup-ai.sh
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

mkdir -p "${CONTINUE_DIR}"
ln -sfn "${CONTINUE_DIR}" "${HOME}/.continue"

KEY="${OPENAI_API_KEY:-}"
BASE="${OPENAI_API_BASE:-}"
MODEL="${OPENAI_MODEL:-gpt-4o}"

if [[ -z "${KEY}" ]]; then
  echo "选择接口:"
  echo "  1) OpenAI 官方"
  echo "  2) OpenAI 兼容（Azure/代理/国内兼容网关等）"
  read -r choice
  case "${choice}" in
    2)
      read -r -p "API Base (例如 https://xxx/v1): " BASE
      ;;
    *)
      BASE=""
      ;;
  esac
  read -r -p "模型名 [gpt-4o]: " MODEL_IN
  MODEL="${MODEL_IN:-gpt-4o}"
  echo "请粘贴 API Key（输入不可见）:"
  read -r -s KEY
  echo
fi

if [[ -z "${KEY}" ]]; then
  echo "API Key 不能为空" >&2
  exit 1
fi

TPL=""
for c in "${TPL_CANDIDATES[@]}"; do
  if [[ -f "$c" ]]; then
    TPL="$c"
    break
  fi
done

if [[ -n "${TPL}" ]]; then
  cp -f "${TPL}" "${CONFIG}"
else
  cat > "${CONFIG}" <<EOF
name: EasyAIoT
version: 0.0.1
schema: v1
models: []
EOF
fi

# rewrite models block simply
{
  cat <<EOF
name: EasyAIoT
version: 0.0.1
schema: v1

models:
  - name: ${MODEL}
    provider: openai
    model: ${MODEL}
    apiKey: ${KEY}
EOF
  if [[ -n "${BASE}" ]]; then
    echo "    apiBase: ${BASE}"
  fi
  cat <<'EOF'
    roles:
      - chat
      - edit
      - apply

rules:
  - |
    You are helping contribute to EasyAIoT (cloud-edge-device AIoT platform).
    Prefer small, focused changes. Respect module boundaries.
    Do not commit secrets or large binary artifacts.

prompts:
  - name: explain-module
    description: Explain current EasyAIoT module
    prompt: |
      Summarize this module, key entry files, and safe change points for the user's goal.
  - name: draft-pr
    description: Draft PR summary from git diff
    prompt: |
      Draft a PR title and body (summary, modules, test plan) from the current git diff.
EOF
} > "${CONFIG}"
chmod 600 "${CONFIG}"

{
  echo "export OPENAI_API_KEY='${KEY}'"
  [[ -n "${BASE}" ]] && echo "export OPENAI_BASE_URL='${BASE}'" && echo "export OPENAI_API_BASE='${BASE}'"
  echo "export OPENAI_MODEL='${MODEL}'"
} > "${ENV_FILE}"
chmod 600 "${ENV_FILE}"

# shell rc hook (idempotent)
for rc in "${HOME}/.bashrc" "${HOME}/.profile"; do
  touch "${rc}"
  if ! grep -q 'project-data/.ai-env' "${rc}" 2>/dev/null; then
    echo '[ -f "$HOME/project-data/.ai-env" ] && . "$HOME/project-data/.ai-env"' >> "${rc}"
  fi
done

cat <<EOF
已配置 Continue（~/.continue -> ${CONTINUE_DIR}）
模型: ${MODEL}
$([ -n "${BASE}" ] && echo "Base: ${BASE}" || echo "Base: OpenAI 默认")

下一步:
  1. 侧边栏打开 Continue
  2. 选模型 ${MODEL} 开始对话 / 改代码
  3. 终端如需 CLI: source ~/project-data/.ai-env

清除:
  bash scripts/idea/clear-ai.sh
EOF
