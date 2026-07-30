#!/usr/bin/env bash
# 将仓库内修复同步到已安装的 /opt/easyaiot-panel/runtime（需 root）
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OPT_RT="${EASYAIOT_PANEL_RUNTIME:-/opt/easyaiot-panel/runtime}"

if [ ! -d "$OPT_RT/.scripts/docker" ]; then
  echo "未找到已安装 runtime: $OPT_RT" >&2
  exit 1
fi

cp -a "$REPO_ROOT/.scripts/docker/runtime_image_common.sh" "$OPT_RT/.scripts/docker/"
cp -a "$REPO_ROOT/.scripts/docker/runtime_image.sh" "$OPT_RT/.scripts/docker/"
cp -a "$REPO_ROOT/.scripts/docker/deploy_profile.sh" "$OPT_RT/.scripts/docker/"
cp -a "$REPO_ROOT/.scripts/docker/install_linux.sh" "$OPT_RT/.scripts/docker/"
cp -a "$REPO_ROOT/.scripts/docker/install_linux_arm.sh" "$OPT_RT/.scripts/docker/" 2>/dev/null || true
cp -a "$REPO_ROOT/.scripts/docker/install_linux_kylin.sh" "$OPT_RT/.scripts/docker/" 2>/dev/null || true
[ -f "$REPO_ROOT/AI/install_linux.sh" ] && cp -a "$REPO_ROOT/AI/install_linux.sh" "$OPT_RT/AI/"

MARKER="$OPT_RT/.scripts/docker/.runtime_images_pulled"
if [ -f "$MARKER" ]; then
  sed -i 's/^PULL_TAG=embedded$/PULL_TAG=latest/' "$MARKER"
  grep -q '^SOURCE_FREE=1' "$MARKER" || echo 'SOURCE_FREE=1' >> "$MARKER"
fi
: > "$OPT_RT/.scripts/docker/.source_free_runtime"

echo "[hotfix] 已同步到 $OPT_RT"
echo "[hotfix] 请在 PANEL 重新执行「安装并启动」，或："
echo "  EASYAIOT_DEPLOY_PROFILE=full bash $OPT_RT/.scripts/docker/install_linux.sh install"
