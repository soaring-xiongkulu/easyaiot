#!/usr/bin/env bash
set -euo pipefail

# 在工作区提示：发布按钮在 IDEA 门户，不在 WEB 管控台
PORTAL="${IDEA_PORTAL_URL:-http://127.0.0.1:9300}"
MODULE="${1:-}"

cat <<EOF
发布到本机
==========
请打开 IDEA 门户（与 WEB 解耦）：
  ${PORTAL}

在「发布到本机」勾选模块（会按 git 改动建议），确认后构建并替换本机正在跑的容器。

命令行如需指定模块，仍请用门户 API：
  curl -X POST ${PORTAL}/api/publish \\
    -H "Content-Type: application/json" \\
    -H "X-IDEA-Session: <登录会话>" \\
    -d '{"modules":["${MODULE:-WEB}"],"action":"publish"}'

IDEA 门户和工作区不会随业务模块重启而停止。
EOF
