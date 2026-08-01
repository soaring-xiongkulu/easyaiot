#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEB="$(ls -1 "$ROOT/COMPILE/dist/ubuntu/easyaiot-panel"_*.deb 2>/dev/null | awk -F_ '{print $2"\t"$0}' | sort -n | tail -1 | cut -f2-)"
if [ -z "${DEB}" ] || [ ! -f "$DEB" ]; then
  echo "未找到 deb，请先: bash COMPILE/build.sh ubuntu --deb" >&2
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
