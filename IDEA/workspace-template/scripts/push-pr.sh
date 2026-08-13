#!/usr/bin/env bash
# 推送当前分支到 origin，并打印提 PR 的网页提示
set -euo pipefail

REPO_DIR="${1:-${IDEA_OPEN_FOLDER:-$(pwd)}}"
cd "${REPO_DIR}"

if [[ ! -d .git && ! -L . ]]; then
  echo "not a git repo" >&2
  exit 1
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "未配置 origin。请先: bash scripts/idea/setup-fork.sh" >&2
  exit 1
fi

branch="$(git rev-parse --abbrev-ref HEAD)"
if [[ "${branch}" == "HEAD" ]]; then
  echo "当前处于 detached HEAD，请先 checkout 分支" >&2
  exit 1
fi

echo "[push-pr] pushing ${branch} -> origin"
git push -u origin "HEAD:${branch}"

origin_url="$(git remote get-url origin)"
upstream_url="$(git remote get-url upstream 2>/dev/null || true)"

# 转成网页地址
to_web() {
  local u="$1"
  u="${u%.git}"
  u="${u/git@github.com:/https:\/\/github.com\/}"
  u="${u/git@gitee.com:/https:\/\/gitee.com\/}"
  echo "$u"
}

ORIGIN_WEB="$(to_web "${origin_url}")"
echo
echo "推送成功。"
echo "Fork: ${ORIGIN_WEB}"
if [[ -n "${upstream_url}" ]]; then
  UP_WEB="$(to_web "${upstream_url}")"
  echo "官方: ${UP_WEB}"
  if [[ "${UP_WEB}" == *"gitee.com"* ]]; then
    echo "创建 PR: ${UP_WEB}/pulls/new"
  elif [[ "${UP_WEB}" == *"github.com"* ]]; then
    echo "创建 PR: ${UP_WEB}/compare"
  else
    echo "创建 MR: ${ORIGIN_WEB}/-/merge_requests/new"
  fi
fi
echo
echo "请打开 PR 模板说明: docs 见仓库 .github/PULL_REQUEST_TEMPLATE.md"
echo "模块检查清单: IDEA-PR-CHECKLIST.md"
