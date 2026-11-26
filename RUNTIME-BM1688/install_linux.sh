#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTION="${1:-help}"
ARG1="${2:-}"
ARG2="${3:-}"
PREFIX="${EASYAIOT_BM1688_INSTALL_DIR:-/opt/easyaiot/RUNTIME-BM1688}"
CONFIG_DIR="${EASYAIOT_BM1688_CONFIG_DIR:-/etc/easyaiot/runtime-bm1688}"
SERVICE="${EASYAIOT_BM1688_SERVICE_NAME:-easyaiot-runtime-bm1688}"
UNIT="/etc/systemd/system/${SERVICE}@.service"

info() { echo "[BM1688] $*"; }
fail() { echo "[BM1688 失败] $*" >&2; exit 1; }
as_root() {
  if [[ "$EUID" -eq 0 ]]; then "$@"
  elif command -v sudo >/dev/null 2>&1; then sudo "$@"
  else fail "该操作需要 root 权限"; fi
}
safe_name() { [[ "$1" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$ ]]; }
validate_paths() {
  [[ "$PREFIX" == /* && "$PREFIX" != / && "$PREFIX" != /opt ]] || fail "安装目录不安全: $PREFIX"
  [[ "$CONFIG_DIR" == /* && "$CONFIG_DIR" != / && "$CONFIG_DIR" != /etc ]] || fail "配置目录不安全: $CONFIG_DIR"
}

build() { bash "$ROOT/scripts/build_linux.sh"; }

install_files() {
  validate_paths
  [[ -x "$ROOT/build/RUNTIME" ]] || build
  as_root install -d "$PREFIX/bin" "$PREFIX/models" "$PREFIX/config" "$CONFIG_DIR"
  as_root install -m 0755 "$ROOT/build/RUNTIME" "$PREFIX/bin/RUNTIME"
  as_root install -m 0644 "$ROOT/models/coco.names" "$PREFIX/models/coco.names"
  as_root install -m 0644 "$ROOT/config/config.example.ini" "$PREFIX/config/config.example.ini"
  as_root install -m 0644 "$ROOT/README.md" "$PREFIX/README.md"
  [[ ! -f "$ROOT/build/VERSION" ]] || as_root install -m 0644 "$ROOT/build/VERSION" "$PREFIX/VERSION"
  local unit_tmp
  unit_tmp="$(mktemp)"
  sed \
    -e "s|@PREFIX@|$PREFIX|g" \
    -e "s|@CONFIG_DIR@|$CONFIG_DIR|g" \
    "$ROOT/systemd/easyaiot-runtime-bm1688@.service" > "$unit_tmp"
  as_root install -m 0644 "$unit_tmp" "$UNIT"
  rm -f -- "$unit_tmp"
  if command -v systemctl >/dev/null 2>&1 && [[ -d /run/systemd/system ]]; then
    as_root systemctl daemon-reload
  fi
}

add_task() {
  local name="$1" source="$2"
  safe_name "$name" || fail "任务名只能包含字母、数字、点、下划线和短横线"
  [[ -s "$source" ]] || fail "配置文件不存在或为空: $source"
  grep -Eqi '^model_path(_[0-9]+)?=.*\.bmodel[[:space:]]*$' "$source" \
    || fail "配置必须包含 .bmodel；不会回退 ONNX/CPU"
  install_files
  as_root install -m 0600 "$source" "$CONFIG_DIR/$name.ini"
  if command -v systemctl >/dev/null 2>&1 && [[ -d /run/systemd/system ]]; then
    as_root systemctl enable --now "$SERVICE@$name.service"
    info "任务已启动: $SERVICE@$name"
  else
    info "systemd 不可用；手工运行: $PREFIX/bin/RUNTIME $CONFIG_DIR/$name.ini"
  fi
}

remove_task() {
  local name="$1"
  safe_name "$name" || fail "任务名无效"
  if command -v systemctl >/dev/null 2>&1 && [[ -d /run/systemd/system ]]; then
    as_root systemctl disable --now "$SERVICE@$name.service" 2>/dev/null || true
  fi
  [[ ! -f "$CONFIG_DIR/$name.ini" ]] || as_root rm -f -- "$CONFIG_DIR/$name.ini"
  info "已移除任务: $name"
}

case "$ACTION" in
  build) build ;;
  preflight) bash "$ROOT/scripts/bm1688_preflight.sh" ;;
  install)
    [[ -n "$ARG1" ]] || fail "用法: $0 install <config.ini> [task-name]"
    add_task "${ARG2:-default}" "$ARG1"
    ;;
  add)
    [[ -n "$ARG1" && -n "$ARG2" ]] || fail "用法: $0 add <task-name> <config.ini>"
    add_task "$ARG1" "$ARG2"
    ;;
  remove)
    [[ -n "$ARG1" ]] || fail "用法: $0 remove <task-name>"
    remove_task "$ARG1"
    ;;
  start|stop|restart|status)
    [[ -n "$ARG1" ]] || fail "用法: $0 $ACTION <task-name>"
    safe_name "$ARG1" || fail "任务名无效"
    as_root systemctl "$ACTION" "$SERVICE@$ARG1.service"
    ;;
  clean)
    [[ "$ROOT/build" == "$ROOT"/* ]] || fail "构建目录不安全"
    find "$ROOT/build" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} + 2>/dev/null || true
    rm -f -- "$ROOT/deploy.env"
    ;;
  help|-h|--help)
    cat <<EOF
RUNTIME-BM1688 独立部署
  $0 preflight
  $0 build
  sudo $0 install <config.ini> [task-name]
  sudo $0 add <task-name> <config.ini>   # 多 RTSP / 多任务，各进程可配置多 BModel
  sudo $0 start|stop|restart|status <task-name>
  sudo $0 remove <task-name>
EOF
    ;;
  *) fail "未知操作: $ACTION" ;;
esac
