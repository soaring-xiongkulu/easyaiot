#!/usr/bin/env bash
set -euo pipefail

OPEN_FOLDER="${IDEA_OPEN_FOLDER:-/home/coder/easyaiot}"
GIT_URL="${IDEA_GIT_URL:-https://gitee.com/volara/easyaiot.git}"
GIT_DEPTH="${IDEA_GIT_DEPTH:-}"
GIT_REF="${IDEA_GIT_REFERENCE:-}"
DATA_ROOT="${HOME}/project-data"
REPO_DIR="${OPEN_FOLDER}"
CS_USER_DIR="${HOME}/.local/share/code-server/User"
PROVIDER="${IDEA_GIT_PROVIDER:-}"
LOGIN="${IDEA_GIT_LOGIN:-}"
GIT_NAME="${IDEA_GIT_NAME:-}"
GIT_EMAIL="${IDEA_GIT_EMAIL:-}"
FORK_URL="${IDEA_FORK_URL:-}"

mkdir -p "${DATA_ROOT}" "${CS_USER_DIR}" "${HOME}/.config"

if [[ ! -w "${DATA_ROOT}" ]]; then
  echo "[idea] ERROR: ${DATA_ROOT} is not writable by uid $(id -u) gid $(id -g)." >&2
  echo "[idea] ERROR: Fix host bind ownership (portal should chown data dir to 1000:1000 when running as root)." >&2
  exit 1
fi

# 清理被中断的不完整 clone（有 .git 但无可用 HEAD）
if [[ -d "${DATA_ROOT}/easyaiot/.git" ]] && ! git -C "${DATA_ROOT}/easyaiot" rev-parse HEAD >/dev/null 2>&1; then
  echo "[idea] incomplete clone at ${DATA_ROOT}/easyaiot (no commits); removing for re-clone"
  rm -rf "${DATA_ROOT}/easyaiot"
fi

# 持久化：若数据卷已有仓库则软链/复用
if [[ -d "${DATA_ROOT}/easyaiot/.git" && ! -e "${REPO_DIR}/.git" ]]; then
  rm -rf "${REPO_DIR}"
  ln -sfn "${DATA_ROOT}/easyaiot" "${REPO_DIR}"
fi

clone_repo() {
  local target="$1"
  local args=(clone)
  if [[ -n "${GIT_DEPTH}" ]]; then
    args+=(--depth "${GIT_DEPTH}")
  fi
  if [[ -n "${GIT_REF}" && -e "${GIT_REF}" ]]; then
    args+=(--reference "${GIT_REF}")
  fi
  args+=("${GIT_URL}" "${target}")
  echo "[idea] cloning ${GIT_URL} -> ${target}"
  if ! git "${args[@]}"; then
    echo "[idea] ERROR: git clone failed for ${GIT_URL} -> ${target}" >&2
    if [[ ! -w "$(dirname "${target}")" ]]; then
      echo "[idea] ERROR: $(dirname "${target}") is not writable (permission denied)." >&2
      echo "[idea] ERROR: Host data dir must be owned by uid 1000 (coder). Restart portal as root so it can chown, or: chown -R 1000:1000 <data-dir>." >&2
    fi
    exit 1
  fi
}

if [[ ! -d "${REPO_DIR}/.git" && ! -L "${REPO_DIR}" ]]; then
  mkdir -p "${DATA_ROOT}"
  if [[ ! -w "${DATA_ROOT}" ]]; then
    echo "[idea] ERROR: ${DATA_ROOT} is not writable; cannot clone." >&2
    exit 1
  fi
  if [[ ! -d "${DATA_ROOT}/easyaiot/.git" ]]; then
    clone_repo "${DATA_ROOT}/easyaiot"
  fi
  rm -rf "${REPO_DIR}"
  ln -sfn "${DATA_ROOT}/easyaiot" "${REPO_DIR}"
elif [[ -d "${REPO_DIR}/.git" ]]; then
  if git -C "${REPO_DIR}" rev-parse HEAD >/dev/null 2>&1; then
    echo "[idea] repo already present at ${REPO_DIR}"
  else
    echo "[idea] incomplete repo at ${REPO_DIR}; removing for re-clone"
    rm -rf "${REPO_DIR}"
    if [[ -L "${DATA_ROOT}/easyaiot" || -d "${DATA_ROOT}/easyaiot" ]]; then
      rm -rf "${DATA_ROOT}/easyaiot"
    fi
    clone_repo "${DATA_ROOT}/easyaiot"
    ln -sfn "${DATA_ROOT}/easyaiot" "${REPO_DIR}"
  fi
fi

# 写入工作区模板（欢迎文档不覆盖；脚本保持可更新）
if [[ -d /opt/idea/workspace-template ]]; then
  mkdir -p "${REPO_DIR}/.vscode" "${REPO_DIR}/scripts/idea"
  if [[ ! -f "${REPO_DIR}/.vscode/extensions.json" ]]; then
    cp -n /opt/idea/workspace-template/.vscode/* "${REPO_DIR}/.vscode/" 2>/dev/null || true
  fi
  if [[ ! -f "${REPO_DIR}/IDEA-README-FIRST.md" ]]; then
    cp -n /opt/idea/workspace-template/README-FIRST.md "${REPO_DIR}/IDEA-README-FIRST.md" 2>/dev/null || true
  fi
  if [[ ! -f "${REPO_DIR}/IDEA-PR-CHECKLIST.md" ]]; then
    cp -n /opt/idea/workspace-template/PR_CHECKLIST.md "${REPO_DIR}/IDEA-PR-CHECKLIST.md" 2>/dev/null || true
  fi
  if [[ -d /opt/idea/workspace-template/scripts ]]; then
    cp -f /opt/idea/workspace-template/scripts/*.sh "${REPO_DIR}/scripts/idea/" 2>/dev/null || true
    chmod +x "${REPO_DIR}/scripts/idea/"*.sh 2>/dev/null || true
  fi
  if [[ -d /opt/idea/workspace-template/continue ]]; then
    mkdir -p "${REPO_DIR}/.continue-template"
    cp -f /opt/idea/workspace-template/continue/config.yaml "${REPO_DIR}/.continue-template/config.yaml" 2>/dev/null || true
  fi
fi

# Continue 配置落在个人数据卷
mkdir -p "${DATA_ROOT}/continue"
ln -sfn "${DATA_ROOT}/continue" "${HOME}/.continue"
if [[ ! -f "${DATA_ROOT}/continue/config.yaml" && -f /opt/idea/workspace-template/continue/config.yaml ]]; then
  cp -f /opt/idea/workspace-template/continue/config.yaml "${DATA_ROOT}/continue/config.yaml"
fi
if [[ -f "${DATA_ROOT}/.ai-env" ]]; then
  # shellcheck disable=SC1091
  . "${DATA_ROOT}/.ai-env" || true
fi

# code-server 用户设置
if [[ -f /tmp/idea-settings.json && ! -f "${CS_USER_DIR}/settings.json" ]]; then
  cp /tmp/idea-settings.json "${CS_USER_DIR}/settings.json"
fi

resolve_repo() {
  if [[ -L "${REPO_DIR}" ]]; then
    readlink -f "${REPO_DIR}"
  else
    echo "${REPO_DIR}"
  fi
}

REAL_REPO="$(resolve_repo)"

if [[ -d "${REAL_REPO}/.git" ]]; then
  git -C "${REAL_REPO}" config --local advice.detachedHead false || true

  # 官方远程固定为 upstream 友好布局：首次把 origin 标成 upstream 别名说明
  if ! git -C "${REAL_REPO}" remote get-url upstream >/dev/null 2>&1; then
    if git -C "${REAL_REPO}" remote get-url origin >/dev/null 2>&1; then
      # 保留 origin=官方，直到用户跑 setup-fork；写本地备注文件
      true
    fi
  fi

  if [[ -n "${GIT_NAME}" ]]; then
    git -C "${REAL_REPO}" config --local user.name "${GIT_NAME}"
  fi
  if [[ -n "${GIT_EMAIL}" ]]; then
    git -C "${REAL_REPO}" config --local user.email "${GIT_EMAIL}"
  elif [[ -n "${LOGIN}" && -n "${PROVIDER}" ]]; then
    # 占位邮箱，避免 commit 无 identity；用户可自行改
    git -C "${REAL_REPO}" config --local user.email "${LOGIN}@users.noreply.${PROVIDER}.local"
  fi

  # 个性化贡献备忘
  {
    echo "# 本工作区贡献备忘（自动生成）"
    echo
    echo "- 官方仓: \`${GIT_URL}\`"
    echo "- 登录身份: \`${PROVIDER:-anonymous}\` / \`${LOGIN:-guest}\`"
    if [[ -n "${FORK_URL}" ]]; then
      echo "- 建议 fork: \`${FORK_URL}\`"
    elif [[ -n "${LOGIN}" && "${PROVIDER}" == "gitee" ]]; then
      echo "- 建议 fork: \`https://gitee.com/${LOGIN}/$(basename "${GIT_URL}" .git).git\`（请先在网页 Fork）"
    elif [[ -n "${LOGIN}" && "${PROVIDER}" == "github" ]]; then
      echo "- 建议 fork: \`https://github.com/${LOGIN}/$(basename "${GIT_URL}" .git).git\`（请先在网页 Fork）"
    fi
    echo
    echo "## 一键绑定 fork"
    echo
    echo '```bash'
    echo "bash scripts/idea/setup-fork.sh"
    echo "bash scripts/idea/setup-git-auth.sh"
    echo "bash scripts/idea/setup-copilot.sh"
    echo "bash scripts/idea/push-pr.sh"
    echo '```'
    echo
    echo "## 查看状态"
    echo
    echo '```bash'
    echo "bash scripts/idea/contrib-status.sh"
    echo '```'
    echo
    echo "PR 检查清单见 \`IDEA-PR-CHECKLIST.md\`；AI：Accounts 登录 Copilot，或 \`bash scripts/idea/setup-copilot.sh\`。"
  } > "${REAL_REPO}/IDEA-CONTRIB.md"
fi

export PASSWORD="${PASSWORD:-$(openssl rand -base64 12 2>/dev/null || echo easyaiot)}"

APP_NAME="${IDEA_APP_NAME:-EasyAIoT}"
WELCOME_TEXT="${IDEA_WELCOME_TEXT:-EasyAIoT 云边端一体化智能算法应用平台}"

# Copilot 等扩展在 VS Marketplace（非默认 Open VSX）
export EXTENSIONS_GALLERY="${EXTENSIONS_GALLERY:-{\"serviceUrl\":\"https://marketplace.visualstudio.com/_apis/public/gallery\",\"itemUrl\":\"https://marketplace.visualstudio.com/items\",\"cacheUrl\":\"https://vscode.blob.core.windows.net/gallery/index\"}}"

echo "[idea] starting ${APP_NAME} on :8080, folder=${REPO_DIR}"
echo "[idea] tip: open IDEA-README-FIRST.md / IDEA-CONTRIB.md , or run bash scripts/idea/setup-fork.sh"
exec code-server \
  --bind-addr 0.0.0.0:8080 \
  --auth password \
  --disable-telemetry \
  --app-name "${APP_NAME}" \
  --welcome-text "${WELCOME_TEXT}" \
  "${REPO_DIR}"
