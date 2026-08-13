#!/usr/bin/env bash
# 贡献状态一览：远程、分支、与 upstream 差异提示
set -euo pipefail

REPO_DIR="${1:-${IDEA_OPEN_FOLDER:-$(pwd)}}"
cd "${REPO_DIR}"

echo "=== EasyAIoT IDEA 贡献状态 ==="
echo "目录: ${REPO_DIR}"
echo "用户: ${IDEA_GIT_LOGIN:--} (${IDEA_GIT_PROVIDER:-anonymous})"
echo

if [[ ! -d .git ]]; then
  echo "未检测到 git 仓库"
  exit 1
fi

echo "-- remotes --"
git remote -v || true
echo
echo "-- branch --"
git status -sb || true
echo

if git remote get-url upstream >/dev/null 2>&1; then
  echo "-- vs upstream (fetch 可选) --"
  if git rev-parse --abbrev-ref HEAD >/dev/null 2>&1; then
    branch="$(git rev-parse --abbrev-ref HEAD)"
    if git show-ref --verify --quiet "refs/remotes/upstream/master"; then
      base=upstream/master
    elif git show-ref --verify --quiet "refs/remotes/upstream/main"; then
      base=upstream/main
    else
      base=""
    fi
    if [[ -n "${base}" ]]; then
      ahead="$(git rev-list --count "${base}..HEAD" 2>/dev/null || echo '?')"
      behind="$(git rev-list --count "HEAD..${base}" 2>/dev/null || echo '?')"
      echo "当前分支 ${branch} | ahead=${ahead} behind=${behind} (相对 ${base})"
    else
      echo "尚未 fetch upstream，可执行: git fetch upstream"
    fi
  fi
else
  echo "尚未配置 upstream。运行: bash scripts/idea/setup-fork.sh"
fi

echo
echo "-- 常用命令 --"
echo "  bash scripts/idea/setup-fork.sh          # 绑定个人 fork"
echo "  git fetch upstream && git rebase upstream/master"
echo "  git push -u origin HEAD"
