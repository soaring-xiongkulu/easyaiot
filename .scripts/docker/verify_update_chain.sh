#!/usr/bin/env bash
# 验证一键 update 链路：不卡死、SKIP_BUILD 生效、模块 update 入口可用
# 用法: bash .scripts/docker/verify_update_chain.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
pass=0; fail=0; warn=0
ok()   { echo -e "${GREEN}[PASS]${NC} $1"; pass=$((pass+1)); }
bad()  { echo -e "${RED}[FAIL]${NC} $1"; fail=$((fail+1)); }
note() { echo -e "${BLUE}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; warn=$((warn+1)); }

echo "========================================"
echo "  EasyAIoT update 链路验证"
echo "========================================"

# 1) ensure_deploy_profile 限时
note "1) ensure_deploy_profile 限时 15s..."
if timeout 15 bash -c '
  source '"$ROOT"'/.scripts/docker/deploy_profile.sh
  ensure_deploy_profile
  echo PROFILE=$EASYAIOT_DEPLOY_PROFILE
  echo MEDIA=$EASYAIOT_MEDIA_ROOT
' >/tmp/easyaiot-verify-profile.out 2>&1; then
  ok "ensure_deploy_profile 在时限内完成"
  cat /tmp/easyaiot-verify-profile.out | sed 's/^/    /'
else
  bad "ensure_deploy_profile 超时或失败"
  cat /tmp/easyaiot-verify-profile.out 2>/dev/null | sed 's/^/    /' || true
fi

# 2) SKIP_PROFILE 路径：acquire 不得再弹 profile/tag（非交互）
note "2) runtime_images_acquire_for_update 在 SKIP_* 下不得阻塞交互..."
if timeout 20 bash -c '
  set -e
  SCRIPT_DIR="'"$ROOT"'/.scripts/docker"
  # shellcheck source=/dev/null
  source "$SCRIPT_DIR/deploy_profile.sh"
  # shellcheck source=/dev/null
  source "$SCRIPT_DIR/runtime_image_common.sh"
  export EASYAIOT_SKIP_IMAGE_PROMPT=1
  export EASYAIOT_SKIP_BUILD=1
  export EASYAIOT_SKIP_PROFILE_PROMPT=1
  export EASYAIOT_DEPLOY_PROFILE=full
  runtime_images_acquire_for_update
' >/tmp/easyaiot-verify-acquire.out 2>&1; then
  ok "acquire_for_update (SKIP_BUILD=1) 快速返回"
else
  bad "acquire_for_update 超时/失败"
  cat /tmp/easyaiot-verify-acquire.out 2>/dev/null | sed 's/^/    /' || true
fi

# 3) 各模块 install_linux.sh update 入口存在
note "3) 模块 update 入口..."
for m in DEVICE AI VIDEO WEB APP RTC VISUALIZE TRANSFORM HARNESS IDEA PANEL; do
  entry="$ROOT/$m/install_linux.sh"
  [ -f "$entry" ] || { bad "$m 缺少 install_linux.sh"; continue; }
  # 包装脚本或真实脚本应能接受 update
  if grep -Eq 'update|exec .*install\.sh' "$entry" \
      || { [ -f "$ROOT/$m/install.sh" ] && grep -Eq 'update' "$ROOT/$m/install.sh"; }; then
    ok "$m 支持 update"
  else
    bad "$m 不支持 update"
  fi
done
if grep -Eq 'update_middleware|^\s*update\)' "$ROOT/.scripts/docker/install_middleware_linux.sh"; then
  ok "middleware 支持 update"
else
  bad "middleware 不支持 update"
fi

# 4) SKIP_BUILD 在关键模块 update 中被尊重（静态检查）
note "4) SKIP_BUILD 静态检查..."
check_skip() {
  local file="$1" label="$2"
  if grep -q 'EASYAIOT_SKIP_BUILD' "$file"; then
    ok "$label 含 EASYAIOT_SKIP_BUILD 分支"
  else
    bad "$label 缺少 EASYAIOT_SKIP_BUILD 分支"
  fi
}
check_skip "$ROOT/IDEA/install.sh" "IDEA"
check_skip "$ROOT/HARNESS/install.sh" "HARNESS"
check_skip "$ROOT/PANEL/install.sh" "PANEL"
check_skip "$ROOT/AI/install_linux.sh" "AI"
check_skip "$ROOT/VIDEO/install_linux.sh" "VIDEO"
check_skip "$ROOT/WEB/install_linux.sh" "WEB"
check_skip "$ROOT/DEVICE/install_linux.sh" "DEVICE"
check_skip "$ROOT/RTC/install_linux.sh" "RTC"

# 5) update_all 进度输出与 SKIP_PROFILE 导出
note "5) update_all 防卡死改动..."
if grep -q '准备更新环境' "$ROOT/.scripts/docker/install_linux.sh" \
  && grep -q 'EASYAIOT_SKIP_PROFILE_PROMPT=1' "$ROOT/.scripts/docker/install_linux.sh"; then
  ok "update_all 含进度输出与 SKIP_PROFILE_PROMPT"
else
  bad "update_all 缺少防卡死改动"
fi
if grep -q 'timeout 20 docker info' "$ROOT/.scripts/docker/install_linux.sh"; then
  ok "docker info 有超时保护"
else
  bad "docker info 缺少超时"
fi
if grep -q '_is_media_mountpoint_safe\|禁止调用 docker info' "$ROOT/.scripts/media-cluster/nfs/resolve_media_root.sh"; then
  ok "媒体根解析避免 docker info / NFS 卡死"
else
  bad "媒体根解析仍可能卡死"
fi

# 6) 业务链路探活（本机有则测，无则 WARN）
note "6) 业务 HTTP 探活（可选）..."
probe() {
  local name="$1" url="$2"
  if curl -sf --connect-timeout 2 --max-time 5 "$url" >/dev/null 2>&1; then
    ok "$name 可达 ($url)"
  else
    warn "$name 不可达 ($url) — 本机可能未部署完整栈"
  fi
}
probe "iot-gateway health" "http://127.0.0.1:48080/actuator/health"
probe "WEB" "http://127.0.0.1:8888/"
probe "VIDEO health" "http://127.0.0.1:6000/actuator/health"
probe "AI" "http://127.0.0.1:5000/"
probe "IDEA health" "http://127.0.0.1:9300/health"
probe "HARNESS" "http://127.0.0.1:3080/"

# 7) 干跑：模拟 update 前半段（不真正 pull 全量镜像）
note "7) 干跑 update 前半段（ensure + docker check，60s 限时）..."
if timeout 60 bash -c '
  set -e
  cd '"$ROOT"'
  SCRIPT_DIR="'"$ROOT"'/.scripts/docker"
  export EASYAIOT_FROM_MENU=1
  export EASYAIOT_SKIP_IMAGE_PROMPT=1
  export EASYAIOT_SKIP_BUILD=1
  export EASYAIOT_SKIP_PROFILE_PROMPT=1
  export EASYAIOT_DEPLOY_PROFILE=full
  # shellcheck source=/dev/null
  source "$SCRIPT_DIR/deploy_profile.sh"
  # shellcheck source=/dev/null
  source "$SCRIPT_DIR/runtime_image_common.sh"
  echo "[dry] ensure_deploy_profile..."
  ensure_deploy_profile
  echo "[dry] profile=$EASYAIOT_DEPLOY_PROFILE media=$EASYAIOT_MEDIA_ROOT"
  echo "[dry] acquire (skip build)..."
  runtime_images_acquire_for_update
  echo "[dry] DONE"
' >/tmp/easyaiot-verify-dry.out 2>&1; then
  ok "update 前半段干跑成功"
  tail -n 15 /tmp/easyaiot-verify-dry.out | sed 's/^/    /'
else
  bad "update 前半段干跑失败/超时"
  cat /tmp/easyaiot-verify-dry.out 2>/dev/null | sed 's/^/    /' || true
fi

# 8) 无 git 命令兼容（安装包常见）
note "8) 无 git 兼容..."
HELPER="$ROOT/.scripts/docker/module_update_helpers.sh"
if [ -f "$HELPER" ] && grep -q 'easyaiot_have_git' "$HELPER"; then
  ok "module_update_helpers.sh 存在"
else
  bad "缺少 module_update_helpers.sh"
fi
for f in \
  AI/install_linux.sh VIDEO/install_linux.sh WEB/install_linux.sh APP/install_linux.sh VISUALIZE/install_linux.sh RTC/install_linux.sh \
  AI/install_linux_arm.sh VIDEO/install_linux_arm.sh \
  AI/install_linux_kylin.sh VIDEO/install_linux_kylin.sh \
  AI/install_mac.sh VIDEO/install_mac.sh WEB/install_mac.sh APP/install_mac.sh VISUALIZE/install_mac.sh
do
  if grep -q 'module_update_helpers\|easyaiot_have_git\|easyaiot_git_pull\|easyaiot_update_should_recreate' "$ROOT/$f"; then
    ok "$f 已接入无 git helper"
  else
    bad "$f 未接入无 git helper"
  fi
done
if grep -q 'EASYAIOT_SKIP_BUILD' "$ROOT/DEVICE/install_mac.sh" \
  && grep -q 'command -v git' "$ROOT/DEVICE/install_mac.sh"; then
  ok "DEVICE/install_mac.sh 无 git / SKIP_BUILD recreate"
else
  bad "DEVICE/install_mac.sh 缺少无 git / SKIP_BUILD 分支"
fi
# 统一入口：桌面端强制 SKIP_BUILD；发行版包装转交 linux
if grep -q 'EASYAIOT_SKIP_BUILD=1' "$ROOT/.scripts/docker/install_desktop_common.sh"; then
  ok "mac/windows 桌面入口强制 SKIP_BUILD=1"
else
  bad "桌面入口未强制 SKIP_BUILD"
fi
for wrap in install_linux_openeuler.sh install_linux_centos.sh; do
  if grep -q 'install_linux.sh' "$ROOT/.scripts/docker/$wrap"; then
    ok "$wrap 转交 install_linux.sh"
  else
    bad "$wrap 未转交 install_linux.sh"
  fi
done
if grep -q 'install_linux_arm.sh' "$ROOT/.scripts/docker/install_linux_centos_arm.sh"; then
  ok "install_linux_centos_arm.sh 转交 install_linux_arm.sh"
else
  bad "install_linux_centos_arm.sh 未转交 arm 入口"
fi

# 9) iot-node 样例清空跨 OS
note "9) iot-node 样例数据清空跨 OS..."
if [ -f "$ROOT/.scripts/docker/clear_iot_node_seed_data.sh" ] \
  && grep -q 'clear_iot_node_seed_data' "$ROOT/.scripts/docker/install_middleware_linux.sh" \
  && grep -q 'clear_iot_node_seed_data' "$ROOT/.scripts/docker/install_middleware_desktop.sh" \
  && grep -q 'clear_iot_node_seed_data_initdb' "$ROOT/.scripts/docker/init-databases.sh"; then
  ok "Linux + 桌面中间件 + initdb 均接入样例节点清空"
else
  bad "iot-node 样例清空未覆盖全平台"
fi
if grep -q '_count_iot_node_seed_fingerprints\|66009735168\|NFS-Storage-01' \
    "$ROOT/.scripts/docker/clear_iot_node_seed_data.sh"; then
  ok "样例清空支持 host 改写后的指纹识别"
else
  bad "样例清空仍仅依赖 192.168.1.x host"
fi
# update 路径也必须清空（不能只靠首次 initdb）
if awk '/^update_middleware\(\)/,/^}/ { if (/clear_iot_node_seed_data/) found=1 } END { exit !found }' \
    "$ROOT/.scripts/docker/install_middleware_linux.sh"; then
  ok "Linux update_middleware 会清空 iot-node 样例"
else
  bad "Linux update_middleware 缺少 clear_iot_node_seed_data"
fi
if grep -A20 '^cmd_update()' "$ROOT/.scripts/docker/install_middleware_desktop.sh" | grep -q 'post_start_hooks' \
  && grep -A15 '^post_start_hooks()' "$ROOT/.scripts/docker/install_middleware_desktop.sh" | grep -q 'clear_iot_node_seed_data'; then
  ok "桌面 cmd_update → post_start_hooks 会清空 iot-node 样例"
else
  bad "桌面 update 未清空 iot-node 样例"
fi

# 10) update 同步脚本 + mqtt-demo paho 兜底
note "10) update 同步仓库脚本与 mqtt-demo paho..."
if grep -q 'easyaiot_update_sync_project_scripts' "$ROOT/.scripts/docker/module_update_helpers.sh" \
  && grep -q 'easyaiot_update_sync_project_scripts' "$ROOT/.scripts/docker/install_linux.sh"; then
  ok "update_all 会 git pull 同步宿主机脚本"
else
  bad "update 未同步仓库脚本"
fi
if [ -f "$ROOT/.scripts/mqtt-demo/vendor/paho/mqtt/client.py" ] \
  && [ -f "$ROOT/.scripts/mqtt-demo/ensure_paho_ready.sh" ] \
  && grep -q 'PYTHONPATH' "$ROOT/.scripts/mqtt-demo/start_mqtt_demo.sh"; then
  ok "mqtt-demo 含 vendor/paho 与 ensure_paho_ready"
else
  bad "mqtt-demo paho 兜底不完整"
fi

# PATH 去掉 git：helper 不得调用真实 git 失败
if timeout 15 bash -c '
  set -e
  _nogit=$(mktemp -d)
  # 仅保留空目录，确保 command -v git 失败
  export PATH="$_nogit"
  # shellcheck source=/dev/null
  source "'"$ROOT"'/.scripts/docker/module_update_helpers.sh"
  if easyaiot_have_git; then exit 2; fi
  out=$(easyaiot_git_rev_parse_head)
  [ -z "$out" ] || exit 3
  easyaiot_git_pull_ff_only
  easyaiot_git_worktree_clean
  /bin/rm -rf "$_nogit"
' >/tmp/easyaiot-verify-nogit.out 2>&1; then
  ok "PATH 无 git 时 helper 安全返回"
else
  bad "PATH 无 git 时 helper 失败"
  cat /tmp/easyaiot-verify-nogit.out 2>/dev/null | sed 's/^/    /' || true
fi

echo ""
echo "========================================"
echo -e "结果: ${GREEN}PASS=$pass${NC}  ${RED}FAIL=$fail${NC}  ${YELLOW}WARN=$warn${NC}"
echo "========================================"
[ "$fail" -eq 0 ]
