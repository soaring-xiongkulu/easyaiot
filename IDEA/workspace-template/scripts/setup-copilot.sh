#!/usr/bin/env bash
set -euo pipefail

# Copilot 不在 Open VSX；若本环境已配置 VS Marketplace，可尝试补装
export EXTENSIONS_GALLERY="${EXTENSIONS_GALLERY:-{\"serviceUrl\":\"https://marketplace.visualstudio.com/_apis/public/gallery\",\"itemUrl\":\"https://marketplace.visualstudio.com/items\",\"cacheUrl\":\"https://vscode.blob.core.windows.net/gallery/index\"}}"

EXTS_DIR="${HOME}/.local/share/code-server/extensions"
need_install=0
if [[ ! -d "${EXTS_DIR}" ]] || ! ls "${EXTS_DIR}" 2>/dev/null | grep -qi 'github.copilot-'; then
  need_install=1
fi

if [[ "${need_install}" -eq 1 ]] && command -v code-server >/dev/null 2>&1; then
  echo "尝试安装 GitHub Copilot 扩展…"
  code-server --install-extension GitHub.copilot || true
  code-server --install-extension GitHub.copilot-chat || true
fi

cat <<'EOF'
GitHub Copilot（推荐，账号登录，无需 API Key）
========================================

1. 确认 GitHub 账号已开通 Copilot：
   https://github.com/settings/copilot

2. 若扩展尚未出现：Command Palette → Extensions: Install Extensions
   搜索 “GitHub Copilot” / “GitHub Copilot Chat” 并安装
   （或重新运行本脚本）

3. 左下角 Accounts（账号）→ Sign in to GitHub / Sign in to use Copilot

4. 按提示在浏览器完成授权（或输入设备码）

5. 登录成功后：
   - 侧边栏打开 Chat
   - 编辑器内行内补全（Tab 接受）

排查：
  - Command Palette → Developer: Reload Window
  - Accounts → Sign out 后重新登录
  - 仍失败：可选 Continue 自备 API → bash scripts/idea/setup-ai.sh

说明：
  - ChatGPT Plus ≠ Copilot
  - 需本人 GitHub Copilot 订阅；平台不代持账号
EOF

echo
echo "已检测到的相关扩展目录："
if [[ -d "${EXTS_DIR}" ]]; then
  ls -1 "${EXTS_DIR}" 2>/dev/null | grep -iE 'copilot|continue|claude-dev' || echo "  （暂无；请 Reload 后从扩展市场安装 GitHub.copilot）"
else
  echo "  （扩展目录尚不存在）"
fi
