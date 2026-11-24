#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTION="${1:-install}"
PREFIX="${EASYAIOT_RK3588_INSTALL_DIR:-/opt/easyaiot/RUNTIME-RK3588}"
CONFIG_DIR="${EASYAIOT_RK3588_CONFIG_DIR:-/etc/easyaiot}"
CONFIG_FILE="${EASYAIOT_RK3588_CONFIG_FILE:-${CONFIG_DIR}/runtime-rk3588.ini}"
SERVICE_NAME="${EASYAIOT_RK3588_SERVICE_NAME:-easyaiot-runtime-rk3588}"
UNIT_FILE="${EASYAIOT_RK3588_UNIT_FILE:-/etc/systemd/system/${SERVICE_NAME}.service}"
CONTROL_PORT="${EASYAIOT_RK3588_CONTROL_PORT:-8123}"
BIN="${PREFIX}/bin/RUNTIME"
BENCH="${PREFIX}/bin/RUNTIME-RK3588-BENCH"
MODEL_DEST="${PREFIX}/models/yolov8n-rk3588-int8.rknn"
CLASSES_DEST="${PREFIX}/models/coco.names"
RUN_DIR="${PREFIX}/run"
PID_FILE="${RUN_DIR}/${SERVICE_NAME}.pid"
LOG_DIR="${EASYAIOT_RK3588_LOG_DIR:-/var/log/easyaiot/runtime-rk3588}"
LOG_FILE="${LOG_DIR}/runtime.log"
TMP_DIR=""
MODEL_SOURCE=""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[RK3588]${NC} $*"; }
ok() { echo -e "${GREEN}[RK3588 OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[RK3588 提示]${NC} $*"; }
fail() { echo -e "${RED}[RK3588 失败]${NC} $*" >&2; exit 1; }

cleanup() {
  if [[ -n "$TMP_DIR" && -d "$TMP_DIR" ]]; then
    rm -rf -- "$TMP_DIR"
  fi
}
trap cleanup EXIT

as_root() {
  if [[ "${EUID}" -eq 0 ]]; then
    "$@"
  elif command -v sudo >/dev/null 2>&1; then
    sudo "$@"
  else
    fail "该操作需要 root 权限；请使用 sudo 重新执行"
  fi
}

validate_paths() {
  [[ "$PREFIX" = /* && "$PREFIX" != "/" && "$PREFIX" != "/opt" ]] \
    || fail "安装目录必须是安全的绝对路径: $PREFIX"
  [[ "$PREFIX" != *$'\n'* && "$PREFIX" != *' '* ]] \
    || fail "安装目录不能包含空格或换行: $PREFIX"
  [[ "$CONFIG_FILE" = /* && "$CONFIG_FILE" != "/" ]] \
    || fail "配置文件必须使用绝对路径: $CONFIG_FILE"
  [[ "$CONTROL_PORT" =~ ^[0-9]+$ ]] \
    || fail "控制端口必须是数字: $CONTROL_PORT"
  (( CONTROL_PORT >= 8000 && CONTROL_PORT <= 9000 )) \
    || fail "控制端口必须位于 8000–9000: $CONTROL_PORT"
}

systemd_running() {
  command -v systemctl >/dev/null 2>&1 && [[ -d /run/systemd/system ]]
}

ensure_build_toolchain() {
  local missing=0
  for cmd in cmake c++ make pkg-config curl; do
    command -v "$cmd" >/dev/null 2>&1 || missing=1
  done
  if command -v pkg-config >/dev/null 2>&1; then
    pkg-config --exists libavformat libavcodec libavutil libcurl || missing=1
    { pkg-config --exists opencv4 || pkg-config --exists opencv; } || missing=1
    { pkg-config --exists libglog || [[ -f /usr/include/glog/logging.h || -f /usr/local/include/glog/logging.h ]]; } \
      || missing=1
    { pkg-config --exists jsoncpp || [[ -f /usr/include/jsoncpp/json/json.h || -f /usr/local/include/jsoncpp/json/json.h ]]; } \
      || missing=1
  fi
  [[ "$missing" -eq 0 ]] && return 0

  if [[ "${EASYAIOT_RK3588_INSTALL_BUILD_DEPS:-1}" = "0" ]]; then
    fail "缺少本机编译工具；请安装 cmake、C++ 编译器、make、pkg-config 与 curl"
  fi
  if ! command -v apt-get >/dev/null 2>&1; then
    fail "缺少编译工具且当前系统不是 apt 系；请先安装 CMake/C++ 及 OpenCV、FFmpeg、glog、jsoncpp 开发包"
  fi

  info "首次使用，正在补齐本机编译工具与通用开发包（不会安装其他 EasyAIoT 模块）"
  as_root env DEBIAN_FRONTEND=noninteractive apt-get update
  as_root env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential cmake pkg-config curl ca-certificates \
    libopencv-dev libcurl4-openssl-dev libgoogle-glog-dev libjsoncpp-dev \
    libavformat-dev libavcodec-dev libavutil-dev libinih-dev libpugixml-dev
}

preflight_build() {
  bash "$ROOT/scripts/rk3588_preflight.sh" --build
}

preflight_runtime() {
  bash "$ROOT/scripts/rk3588_preflight.sh"
}

prompt_value() {
  local prompt="$1" value=""
  if [[ -t 0 ]]; then
    read -r -p "$prompt" value
  fi
  printf '%s' "$value"
}

validate_single_line() {
  local label="$1" value="$2"
  [[ "$value" != *$'\n'* && "$value" != *$'\r'* ]] \
    || fail "$label 不能包含换行"
}

resolve_rtsp_url() {
  local value="${EASYAIOT_RK3588_RTSP_URL:-}"
  if [[ -z "$value" ]]; then
    value="$(prompt_value '请输入摄像头 RTSP 地址: ')"
  fi
  [[ "$value" == rtsp://* || "$value" == rtsps://* ]] \
    || fail "请通过 EASYAIOT_RK3588_RTSP_URL 提供有效的 rtsp:// 或 rtsps:// 地址"
  validate_single_line "RTSP 地址" "$value"
  printf '%s' "$value"
}

download_model() {
  local url="$1"
  validate_single_line "模型下载地址" "$url"
  mkdir -p "$TMP_DIR"
  MODEL_SOURCE="${TMP_DIR}/yolov8n-rk3588-int8.rknn"
  info "正在下载 RKNN 模型"
  curl --fail --location --retry 3 --connect-timeout 15 \
    --output "$MODEL_SOURCE" "$url"
  [[ -s "$MODEL_SOURCE" ]] || fail "下载到的 RKNN 模型为空"
  if [[ -n "${EASYAIOT_RK3588_MODEL_SHA256:-}" ]]; then
    local actual
    actual="$(sha256sum "$MODEL_SOURCE" | awk '{print $1}')"
    [[ "$actual" == "${EASYAIOT_RK3588_MODEL_SHA256}" ]] \
      || fail "RKNN 模型 SHA256 校验失败"
  fi
}

resolve_model_source() {
  local candidate="${EASYAIOT_RK3588_MODEL_PATH:-}"

  if [[ -n "${EASYAIOT_RK3588_MODEL_URL:-}" ]]; then
    download_model "${EASYAIOT_RK3588_MODEL_URL}"
    return 0
  fi

  if [[ -z "$candidate" && -s "$MODEL_DEST" ]]; then
    candidate="$MODEL_DEST"
  fi
  if [[ -z "$candidate" ]]; then
    candidate="$(find "$ROOT/models" -maxdepth 1 -type f -name '*.rknn' -print -quit 2>/dev/null || true)"
  fi
  if [[ -z "$candidate" && -d /opt/models ]]; then
    candidate="$(find /opt/models -maxdepth 1 -type f -name '*.rknn' -print -quit 2>/dev/null || true)"
  fi
  if [[ -z "$candidate" ]]; then
    candidate="$(prompt_value '请输入 YOLOv8n INT8 RKNN 模型路径: ')"
  fi
  [[ -n "$candidate" && -s "$candidate" ]] \
    || fail "未找到 RKNN 模型；请设置 EASYAIOT_RK3588_MODEL_PATH 或 EASYAIOT_RK3588_MODEL_URL"
  [[ "$candidate" == *.rknn ]] || fail "模型必须是 .rknn 文件: $candidate"
  validate_single_line "模型路径" "$candidate"
  MODEL_SOURCE="$candidate"
}

build_runtime() {
  info "编译 RK3588 专用 MPP/RGA/RKNN 运行时"
  bash "$ROOT/scripts/build_linux.sh"
  [[ -x "$ROOT/build/RUNTIME" ]] || fail "编译完成但未找到 RUNTIME"
  [[ -x "$ROOT/build/RUNTIME-RK3588-BENCH" ]] || fail "编译完成但未找到基准程序"
}

install_runtime_files() {
  info "安装独立运行文件到 $PREFIX"
  as_root cmake --install "$ROOT/build" --prefix "$PREFIX"
  as_root install -d \
    "$PREFIX/config" "$PREFIX/models" "$PREFIX/scripts" "$RUN_DIR" "$LOG_DIR" "$CONFIG_DIR"
  as_root install -m 0644 "$ROOT/config/config.example.ini" "$PREFIX/config/config.example.ini"
  as_root install -m 0644 "$ROOT/models/coco.names" "$CLASSES_DEST"
  as_root install -m 0644 "$ROOT/README.md" "$PREFIX/README.md"
  as_root install -m 0755 "$ROOT/scripts/rk3588_preflight.sh" "$PREFIX/scripts/rk3588_preflight.sh"
  as_root install -m 0755 "$ROOT/scripts/smoke_runtime.sh" "$PREFIX/scripts/smoke_runtime.sh"
  as_root install -m 0755 "$ROOT/scripts/convert_rknn_model.py" "$PREFIX/scripts/convert_rknn_model.py"
  as_root install -m 0755 "$ROOT/scripts/prepare_yolov8n_rk3588.sh" "$PREFIX/scripts/prepare_yolov8n_rk3588.sh"

  if [[ "$(readlink -f "$MODEL_SOURCE")" != "$(readlink -f "$MODEL_DEST" 2>/dev/null || printf '%s' "$MODEL_DEST")" ]]; then
    as_root install -m 0644 "$MODEL_SOURCE" "$MODEL_DEST"
  fi
  [[ -s "$MODEL_DEST" ]] || fail "RKNN 模型安装失败: $MODEL_DEST"
}

write_standalone_config() {
  if [[ -s "$CONFIG_FILE" \
        && -z "${EASYAIOT_RK3588_RTSP_URL:-}" \
        && "${EASYAIOT_RK3588_RECONFIGURE:-0}" != "1" ]]; then
    info "保留现有独立配置: $CONFIG_FILE"
    return 0
  fi

  local rtsp_url rtmp_url enable_rtmp enable_draw
  rtsp_url="$(resolve_rtsp_url)"
  rtmp_url="${EASYAIOT_RK3588_RTMP_URL:-}"
  validate_single_line "RTMP 地址" "$rtmp_url"
  enable_rtmp=false
  enable_draw=false
  if [[ -n "$rtmp_url" ]]; then
    [[ "$rtmp_url" == rtmp://* || "$rtmp_url" == rtmps://* ]] \
      || fail "EASYAIOT_RK3588_RTMP_URL 必须使用 rtmp:// 或 rtmps://"
    enable_rtmp=true
    enable_draw=true
  fi

  mkdir -p "$TMP_DIR"
  local generated="${TMP_DIR}/runtime-rk3588.ini"
  cat >"$generated" <<EOF
# 由 RUNTIME-RK3588 独立部署脚本生成；不依赖 EasyAIoT 其他模块。
[video]
rtsp_url=${rtsp_url}
rtmp_url=${rtmp_url}
width=${EASYAIOT_RK3588_VIDEO_WIDTH:-1920}
height=${EASYAIOT_RK3588_VIDEO_HEIGHT:-1080}
fps=${EASYAIOT_RK3588_VIDEO_FPS:-25}

[ai]
enable=true
model_path=${MODEL_DEST}
classes_path=${CLASSES_DEST}
threads=3
frame_skip=1

[rk3588]
npu_workers=${EASYAIOT_RK3588_NPU_WORKERS:-3}
task_queue_depth=${EASYAIOT_RK3588_TASK_QUEUE_DEPTH:-2}
frame_pool_size=${EASYAIOT_RK3588_FRAME_POOL_SIZE:-6}
mpp_buffer_count=${EASYAIOT_RK3588_MPP_BUFFER_COUNT:-8}
use_sram=true
enable_perf_query=false

[alarm]
enable=false
confidence_threshold=0.5
cooldown_time=30
image_dir=${LOG_DIR}/alerts

[task]
id=standalone-rk3588
control_port=${CONTROL_PORT}

[video_task]
device_id=${EASYAIOT_RK3588_DEVICE_ID:-rk3588_camera_001}
device_name=${EASYAIOT_RK3588_DEVICE_NAME:-RK3588独立摄像头}
task_type=realtime
algorithm_name=detection
heartbeat_url=
heartbeat_interval_sec=10
log_path=${LOG_DIR}
alert_image_dir=${LOG_DIR}/alerts
algo_bus_transport=off
headless=true

[mqtt]
broker_urls=
tenant=default
transport=off

[features]
enable_rtmp=${enable_rtmp}
enable_draw=${enable_draw}
enable_alarm=false

[regions]
EOF
  as_root install -m 0640 "$generated" "$CONFIG_FILE"
  ok "已生成无需其他模块的独立配置: $CONFIG_FILE"
}

install_systemd_unit() {
  command -v systemctl >/dev/null 2>&1 || return 0
  mkdir -p "$TMP_DIR"
  local generated="${TMP_DIR}/${SERVICE_NAME}.service"
  cat >"$generated" <<EOF
[Unit]
Description=EasyAIoT RK3588 standalone AI runtime
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
WorkingDirectory=${PREFIX}
ExecStart=${BIN} ${CONFIG_FILE}
Restart=on-failure
RestartSec=2
TimeoutStopSec=20
KillSignal=SIGTERM
LimitNOFILE=1048576
LimitMEMLOCK=infinity
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
  as_root install -m 0644 "$generated" "$UNIT_FILE"
  if systemd_running; then
    as_root systemctl daemon-reload
    as_root systemctl enable "$SERVICE_NAME" >/dev/null
  fi
}

fallback_running() {
  [[ -s "$PID_FILE" ]] || return 1
  local pid
  pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
  kill -0 "$pid" 2>/dev/null
}

service_stop() {
  if systemd_running && [[ -f "$UNIT_FILE" ]]; then
    as_root systemctl stop "$SERVICE_NAME" >/dev/null 2>&1 || true
    return 0
  fi
  if fallback_running; then
    local pid
    pid="$(cat "$PID_FILE")"
    as_root kill "$pid" 2>/dev/null || true
    for _ in $(seq 1 20); do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.25
    done
    if kill -0 "$pid" 2>/dev/null; then
      as_root kill -KILL "$pid" 2>/dev/null || true
    fi
  fi
  as_root rm -f -- "$PID_FILE"
}

service_start() {
  [[ -x "$BIN" ]] || fail "运行程序不存在，请先执行 install: $BIN"
  [[ -s "$CONFIG_FILE" ]] || fail "独立配置不存在，请先执行 install: $CONFIG_FILE"
  preflight_runtime
  as_root install -d "$RUN_DIR" "$LOG_DIR"

  if systemd_running && [[ -f "$UNIT_FILE" ]]; then
    as_root systemctl daemon-reload
    as_root systemctl enable --now "$SERVICE_NAME" >/dev/null
  else
    fallback_running && { ok "服务已经运行"; return 0; }
    as_root bash -c 'nohup "$1" "$2" >>"$3" 2>&1 & echo $! >"$4"' \
      _ "$BIN" "$CONFIG_FILE" "$LOG_FILE" "$PID_FILE"
  fi
  ok "RK3588 独立运行时已启动"
}

service_status() {
  if systemd_running && [[ -f "$UNIT_FILE" ]]; then
    as_root systemctl --no-pager --full status "$SERVICE_NAME"
  elif fallback_running; then
    ok "服务运行中，PID=$(cat "$PID_FILE")"
  else
    warn "服务未运行"
    return 1
  fi
}

service_logs() {
  if systemd_running && [[ -f "$UNIT_FILE" ]]; then
    if [[ -t 1 && "${EASYAIOT_RK3588_LOG_FOLLOW:-1}" = "1" ]]; then
      as_root journalctl -u "$SERVICE_NAME" -n 200 -f
    else
      as_root journalctl -u "$SERVICE_NAME" -n 200 --no-pager
    fi
  else
    [[ -f "$LOG_FILE" ]] || fail "日志尚未生成: $LOG_FILE"
    if [[ -t 1 && "${EASYAIOT_RK3588_LOG_FOLLOW:-1}" = "1" ]]; then
      tail -n 200 -f "$LOG_FILE"
    else
      tail -n 200 "$LOG_FILE"
    fi
  fi
}

verify_runtime() {
  preflight_runtime
  local health="" endpoint="http://127.0.0.1:${CONTROL_PORT}/health"
  info "等待硬件流水线就绪: $endpoint"
  for _ in $(seq 1 "${EASYAIOT_RK3588_VERIFY_RETRIES:-45}"); do
    health="$(curl --silent --show-error --fail --max-time 2 "$endpoint" 2>/dev/null || true)"
    if [[ -n "$health" ]]; then
      break
    fi
    sleep 1
  done
  [[ -n "$health" ]] || {
    warn "健康接口未就绪，最近日志如下"
    EASYAIOT_RK3588_LOG_FOLLOW=0 service_logs || true
    fail "RK3588 独立运行时验收失败"
  }
  grep -Eq '"platform"[[:space:]]*:[[:space:]]*"rk3588"' <<<"$health" \
    || fail "健康接口未报告 RK3588 平台: $health"
  grep -Eq '"infer_ep"[[:space:]]*:[[:space:]]*"rknn-rk3588' <<<"$health" \
    || fail "健康接口未报告 RKNN 硬件推理: $health"
  grep -Eq '"decode_ep"[[:space:]]*:[[:space:]]*"mpp-rk3588"' <<<"$health" \
    || fail "健康接口未报告 MPP 硬解: $health"
  ok "独立部署验收通过：MPP 硬解 + RGA + RKNN 三核流水线在线"
  echo "$health"
}

install_all() {
  validate_paths
  TMP_DIR="$(mktemp -d)"
  preflight_build
  ensure_build_toolchain
  resolve_model_source
  service_stop
  build_runtime
  install_runtime_files
  write_standalone_config
  install_systemd_unit
  service_start
  verify_runtime
  echo ""
  ok "部署完成，不依赖 WEB / AI / VIDEO / MQTT / Docker 等其他 EasyAIoT 模块"
  echo "  健康检查: http://127.0.0.1:${CONTROL_PORT}/health"
  echo "  查看状态: $0 status"
  echo "  查看日志: $0 logs"
  echo "  性能验收: $BENCH $MODEL_DEST test.jpg 30 150 $CLASSES_DEST"
}

uninstall_runtime() {
  validate_paths
  service_stop
  if command -v systemctl >/dev/null 2>&1 && [[ -f "$UNIT_FILE" ]]; then
    systemd_running && as_root systemctl disable "$SERVICE_NAME" >/dev/null 2>&1 || true
    as_root rm -f -- "$UNIT_FILE"
    systemd_running && as_root systemctl daemon-reload || true
  fi
  as_root rm -f -- "$BIN" "$BENCH"
  warn "程序与服务已移除；配置、模型和日志仍保留，避免误删现场数据"
  echo "  配置: $CONFIG_FILE"
  echo "  模型: $MODEL_DEST"
  echo "  日志: $LOG_DIR"
}

show_help() {
  cat <<EOF
RUNTIME-RK3588 独立部署

用法: $0 {install|update|preflight|deps|build|start|stop|restart|status|logs|verify|uninstall|help}

首次一键部署：
  EASYAIOT_RK3588_RTSP_URL='rtsp://user:pass@camera/stream' \\
  EASYAIOT_RK3588_MODEL_PATH='/path/yolov8n-rk3588-int8.rknn' \\
  sudo -E $0 install

也可设置 EASYAIOT_RK3588_MODEL_URL，由脚本下载模型；建议同时设置
EASYAIOT_RK3588_MODEL_SHA256。安装后由 systemd 开机自启；无 systemd 时使用
有 PID 与日志文件的后台进程。整个流程不启动任何其他 EasyAIoT 模块。
EOF
}

case "$ACTION" in
  install|update)
    install_all
    ;;
  preflight)
    validate_paths
    preflight_runtime
    ;;
  deps)
    validate_paths
    ensure_build_toolchain
    ;;
  build)
    validate_paths
    preflight_build
    ensure_build_toolchain
    build_runtime
    ;;
  start)
    validate_paths
    service_start
    verify_runtime
    ;;
  stop)
    validate_paths
    service_stop
    ok "RK3588 独立运行时已停止"
    ;;
  restart)
    validate_paths
    service_stop
    service_start
    verify_runtime
    ;;
  status)
    validate_paths
    service_status
    ;;
  logs)
    validate_paths
    service_logs
    ;;
  verify)
    validate_paths
    verify_runtime
    ;;
  uninstall)
    uninstall_runtime
    ;;
  help|-h|--help)
    show_help
    ;;
  *)
    show_help >&2
    exit 2
    ;;
esac
