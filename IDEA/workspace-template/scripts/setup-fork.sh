#!/usr/bin/env bash
# 将官方仓 origin 改为 upstream，并添加个人 fork 为 origin（可写）
set -euo pipefail

REPO_DIR="${1:-${IDEA_OPEN_FOLDER:-$(pwd)}}"
PROVIDER="${IDEA_GIT_PROVIDER:-}"
LOGIN="${IDEA_GIT_LOGIN:-}"
FORK_URL="${IDEA_FORK_URL:-${2:-}}"
OFFICIAL_URL="${IDEA_GIT_URL:-https://gitee.com/volara/easyaiot.git}"

cd "${REPO_DIR}"

if [[ ! -d .git ]]; then
  echo "[setup-fork] not a git repo: ${REPO_DIR}" >&2
  exit 1
fi

# 从官方 URL 推断仓库名
repo_name="$(basename "${OFFICIAL_URL}" .git)"
repo_name="${repo_name:-easyaiot}"

guess_fork_url() {
  case "${PROVIDER}" in
    gitee) echo "https://gitee.com/${LOGIN}/${repo_name}.git" ;;
    github) echo "https://github.com/${LOGIN}/${repo_name}.git" ;;
    *) echo "" ;;
  esac
}

if [[ -z "${FORK_URL}" ]]; then
  FORK_URL="$(guess_fork_url)"
fi

if [[ -z "${FORK_URL}" ]]; then
  cat <<EOF
[setup-fork] 请提供 fork 地址：

  bash scripts/idea/setup-fork.sh . <你的-fork-git-url>

或设置环境变量 IDEA_FORK_URL / IDEA_GIT_PROVIDER + IDEA_GIT_LOGIN 后重试。
EOF
  exit 2
fi

# origin -> upstream（官方只读）
if git remote get-url origin >/dev/null 2>&1; then
  current_origin="$(git remote get-url origin)"
  if [[ "${current_origin}" == "${FORK_URL}" ]]; then
    echo "[setup-fork] origin 已是你的 fork: ${FORK_URL}"
  else
    if git remote get-url upstream >/dev/null 2>&1; then
      echo "[setup-fork] upstream 已存在: $(git remote get-url upstream)"
    else
      echo "[setup-fork] rename origin -> upstream (${current_origin})"
      git remote rename origin upstream
    fi
    if git remote get-url origin >/dev/null 2>&1; then
      echo "[setup-fork] set origin -> ${FORK_URL}"
      git remote set-url origin "${FORK_URL}"
    else
      echo "[setup-fork] add origin ${FORK_URL}"
      git remote add origin "${FORK_URL}"
    fi
  fi
else
  git remote add upstream "${OFFICIAL_URL}" 2>/dev/null || true
  git remote add origin "${FORK_URL}"
fi

# 确保 upstream 指向官方
if git remote get-url upstream >/dev/null 2>&1; then
  git remote set-url upstream "${OFFICIAL_URL}" || true
else
  git remote add upstream "${OFFICIAL_URL}" || true
fi

echo "[setup-fork] remotes:"
git remote -v
cat <<EOF

下一步：
  git fetch upstream
  git checkout -b feat/my-change
  # ... 改代码 ...
  git add -A && git commit -m "feat: ..."
  git push -u origin HEAD
  # 然后到官方仓网页创建 Pull Request
EOF
