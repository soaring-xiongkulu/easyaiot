#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# 选取最新 easyaiot-panel-<ver>-amd64.deb（中横线命名）
DEB=""
max_ver=""
shopt -s nullglob
for f in "$ROOT/COMPILE/dist/ubuntu/easyaiot-panel"-*-amd64.deb; do
  base="$(basename "$f")"
  if [[ "$base" =~ ^easyaiot-panel-([0-9]+([.][0-9]+)*)-amd64\.deb$ ]]; then
    v="${BASH_REMATCH[1]}"
    if [ -z "$max_ver" ] || [ "$(printf '%s\n%s\n' "$max_ver" "$v" | sort -V | tail -1)" = "$v" ]; then
      if [ "$v" != "$max_ver" ] || [ -z "$DEB" ]; then
        max_ver="$v"
        DEB="$f"
      fi
    fi
  fi
done
shopt -u nullglob

if [ -z "${DEB}" ] || [ ! -f "$DEB" ]; then
  echo "未找到 deb，请先: bash COMPILE/build.sh ubuntu-x86 --deb" >&2
  exit 1
fi
echo "[force] 安装: $DEB"
echo "[force] 安装前: $(dpkg-query -W -f='${Version}' easyaiot-panel 2>/dev/null || echo 无)"
dpkg -i "$DEB"
systemctl daemon-reload || true
systemctl restart easyaiot-panel
sleep 1
echo "[force] 安装后: $(dpkg-query -W -f='${Version}' easyaiot-panel 2>/dev/null || echo 无)"
echo "[force] 二进制:"
md5sum /opt/easyaiot-panel/bin/easyaiot-panel "$ROOT/COMPILE/dist/ubuntu/easyaiot-panel"
echo "[force] 探测 UI:"
JS=$(curl -sS http://127.0.0.1:9200/ | grep -oE '/assets/index-[^"]+\.js' | head -1 || true)
echo "  js=$JS"
curl -sS "http://127.0.0.1:9200${JS}" | grep -oE '20260730-stack-menus|安装脚本界面化|拉取 · 构建 · 推送|安装 · 启停 · 更新' | sort -u || true
echo "[force] 完成。请浏览器 Ctrl+Shift+R 强制刷新 http://127.0.0.1:9200/"
