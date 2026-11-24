#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTION="${1:-install}"
ACTION_ARG="${2:-}"
PREFIX="${EASYAIOT_RK3588_INSTALL_DIR:-/opt/easyaiot/RUNTIME-RK3588}"
CONFIG_DIR="${EASYAIOT_RK3588_CONFIG_DIR:-/etc/easyaiot}"
STATE_DIR="${EASYAIOT_RK3588_STATE_DIR:-${CONFIG_DIR}/runtime-rk3588}"
MANIFEST_FILE="${STATE_DIR}/tasks.json"
TASK_CONFIG_DIR="${STATE_DIR}/tasks"
TASK_STATE_FILE="${STATE_DIR}/tasks.tsv"
LEGACY_CONFIG_FILE="${EASYAIOT_RK3588_CONFIG_FILE:-${CONFIG_DIR}/runtime-rk3588.ini}"
SERVICE_BASENAME="${EASYAIOT_RK3588_SERVICE_NAME:-easyaiot-runtime-rk3588}"
UNIT_FILE="${EASYAIOT_RK3588_UNIT_FILE:-/etc/systemd/system/${SERVICE_BASENAME}@.service}"
LEGACY_UNIT_FILE="/etc/systemd/system/${SERVICE_BASENAME}.service"
BIN="${PREFIX}/bin/RUNTIME"
BENCH="${PREFIX}/bin/RUNTIME-RK3588-BENCH"
RUN_DIR="${PREFIX}/run"
LOG_DIR="${EASYAIOT_RK3588_LOG_DIR:-/var/log/easyaiot/runtime-rk3588}"
MANIFEST_TOOL="${ROOT}/scripts/standalone_manifest.py"
MANIFEST_SOURCE=""
PLAN_DIR=""
TMP_DIR=""
DOWNLOADED_MODEL=""

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
  [[ "$STATE_DIR" = /* && "$STATE_DIR" != "/" && "$STATE_DIR" != "$CONFIG_DIR" ]] \
    || fail "任务状态目录必须是安全的绝对路径: $STATE_DIR"
  [[ "$LOG_DIR" = /* && "$LOG_DIR" != "/" && "$LOG_DIR" != "/var/log" ]] \
    || fail "日志目录必须是安全的绝对路径: $LOG_DIR"
  for path in "$PREFIX" "$STATE_DIR" "$LOG_DIR"; do
    [[ "$path" != *$'\n'* && "$path" != *' '* ]] \
      || fail "路径不能包含空格或换行: $path"
  done
}

systemd_running() {
  command -v systemctl >/dev/null 2>&1 && [[ -d /run/systemd/system ]]
}

ensure_build_toolchain() {
  local missing=0
  for cmd in cmake c++ make pkg-config curl python3; do
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
    fail "缺少本机编译工具；请安装 CMake、C++ 编译器、pkg-config、curl 与 Python 3"
  fi
  command -v apt-get >/dev/null 2>&1 \
    || fail "缺少编译工具且当前系统不是 apt 系；请先安装 CMake/C++、Python 3 及 OpenCV、FFmpeg、glog、jsoncpp 开发包"

  info "首次使用，正在补齐本机编译工具与通用开发包（不会安装其他 EasyAIoT 模块）"
  as_root env DEBIAN_FRONTEND=noninteractive apt-get update
  as_root env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential cmake pkg-config curl ca-certificates python3 \
    libopencv-dev libcurl4-openssl-dev libgoogle-glog-dev libjsoncpp-dev \
    libavformat-dev libavcodec-dev libavutil-dev libinih-dev libpugixml-dev
}

preflight_build() { bash "$ROOT/scripts/rk3588_preflight.sh" --build; }
preflight_runtime() { bash "$ROOT/scripts/rk3588_preflight.sh"; }

prompt_value() {
  local prompt="$1" value=""
  if [[ -t 0 ]]; then
    read -r -p "$prompt" value
  fi
  printf '%s' "$value"
}

download_legacy_model() {
  local url="${EASYAIOT_RK3588_MODEL_URL:-}"
  [[ -n "$url" ]] || return 1
  [[ "$url" != *$'\n'* && "$url" != *$'\r'* ]] || fail "模型下载地址不能包含换行"
  DOWNLOADED_MODEL="${TMP_DIR}/legacy-model.rknn"
  info "正在下载旧版单模型参数指定的 RKNN 模型"
  curl --fail --location --retry 3 --connect-timeout 15 --output "$DOWNLOADED_MODEL" "$url"
  [[ -s "$DOWNLOADED_MODEL" ]] || fail "下载到的 RKNN 模型为空"
  if [[ -n "${EASYAIOT_RK3588_MODEL_SHA256:-}" ]]; then
    local actual
    actual="$(sha256sum "$DOWNLOADED_MODEL" | awk '{print $1}')"
    [[ "$actual" == "${EASYAIOT_RK3588_MODEL_SHA256}" ]] || fail "RKNN 模型 SHA256 校验失败"
  fi
}

create_legacy_manifest() {
  local rtsp="$1" model="$2" classes="$3"
  [[ "$rtsp" == rtsp://* || "$rtsp" == rtsps://* ]] \
    || fail "旧版 EASYAIOT_RK3588_RTSP_URL 必须使用 rtsp:// 或 rtsps://"
  [[ -s "$model" && "$model" == *.rknn ]] || fail "旧版模型路径无效: $model"
  [[ -s "$classes" ]] || fail "类别文件不存在: $classes"
  MANIFEST_SOURCE="${TMP_DIR}/legacy.tasks.json"
  python3 "$MANIFEST_TOOL" legacy \
    --output "$MANIFEST_SOURCE" \
    --rtsp "$rtsp" \
    --model "$model" \
    --classes "$classes" \
    --device-id "${EASYAIOT_RK3588_DEVICE_ID:-rk3588-camera-001}" \
    --device-name "${EASYAIOT_RK3588_DEVICE_NAME:-RK3588独立摄像头}" \
    --control-port "${EASYAIOT_RK3588_CONTROL_PORT:-8123}"
  warn "已兼容旧版单 RTSP/单模型参数；后续建议直接维护 $MANIFEST_FILE"
}

legacy_ini_value() {
  local section="$1" key="$2"
  awk -F= -v wanted_section="$section" -v wanted_key="$key" '
    /^\[/ { current=$0; gsub(/^\[|\]$/, "", current); next }
    current == wanted_section && $1 == wanted_key {
      sub(/^[^=]*=/, ""); print; exit
    }
  ' "$LEGACY_CONFIG_FILE"
}

resolve_manifest_source() {
  local explicit="${ACTION_ARG:-${EASYAIOT_RK3588_MANIFEST:-}}"
  if [[ -n "$explicit" ]]; then
    MANIFEST_SOURCE="$explicit"
  elif [[ -n "${EASYAIOT_RK3588_RTSP_URL:-}" ]]; then
    local model="${EASYAIOT_RK3588_MODEL_PATH:-}"
    if [[ -z "$model" && -n "${EASYAIOT_RK3588_MODEL_URL:-}" ]]; then
      download_legacy_model
      model="$DOWNLOADED_MODEL"
    fi
    create_legacy_manifest \
      "${EASYAIOT_RK3588_RTSP_URL}" \
      "$model" \
      "${EASYAIOT_RK3588_CLASSES_PATH:-${ROOT}/models/coco.names}"
    return 0
  elif [[ -s "$MANIFEST_FILE" ]]; then
    MANIFEST_SOURCE="$MANIFEST_FILE"
    info "使用已安装任务清单: $MANIFEST_FILE"
  elif [[ -s "$LEGACY_CONFIG_FILE" ]]; then
    local rtsp model classes
    rtsp="$(legacy_ini_value video rtsp_url)"
    model="$(legacy_ini_value ai model_path)"
    classes="$(legacy_ini_value ai classes_path)"
    create_legacy_manifest "$rtsp" "$model" "${classes:-${ROOT}/models/coco.names}"
    warn "检测到旧版单进程配置，已迁移为任务清单"
    return 0
  else
    MANIFEST_SOURCE="$(prompt_value '请输入 RK3588 任务清单路径（JSON）: ')"
  fi

  [[ -n "$MANIFEST_SOURCE" ]] || fail "未提供任务清单。先复制并编辑示例：cp RUNTIME-RK3588/config/standalone.tasks.example.json ./rk3588.tasks.json"
  if [[ "$MANIFEST_SOURCE" != /* ]]; then
    MANIFEST_SOURCE="$(pwd)/${MANIFEST_SOURCE}"
  fi
  [[ -s "$MANIFEST_SOURCE" ]] || fail "任务清单不存在或为空: $MANIFEST_SOURCE"
}

compile_task_plan() {
  command -v python3 >/dev/null 2>&1 || fail "任务清单编译需要 Python 3"
  [[ -x "$MANIFEST_TOOL" || -f "$MANIFEST_TOOL" ]] || fail "任务清单编译器不存在: $MANIFEST_TOOL"
  PLAN_DIR="${TMP_DIR}/plan"
  python3 "$MANIFEST_TOOL" compile \
    --manifest "$MANIFEST_SOURCE" \
    --output "$PLAN_DIR" \
    --prefix "$PREFIX" \
    --log-dir "$LOG_DIR" \
    --default-classes "$ROOT/models/coco.names"
}

build_runtime() {
  info "编译 RK3588 专用 MPP/RGA/RKNN 运行时"
  bash "$ROOT/scripts/build_linux.sh"
  [[ -x "$ROOT/build/RUNTIME" ]] || fail "编译完成但未找到 RUNTIME"
  [[ -x "$ROOT/build/RUNTIME-RK3588-BENCH" ]] || fail "编译完成但未找到基准程序"
}

same_path() {
  [[ "$(readlink -f "$1" 2>/dev/null || printf '%s' "$1")" == \
     "$(readlink -f "$2" 2>/dev/null || printf '%s' "$2")" ]]
}

install_runtime_files() {
  info "安装独立运行文件、共享模型与逐路任务配置"
  as_root cmake --install "$ROOT/build" --prefix "$PREFIX"
  as_root install -d "$PREFIX/config" "$PREFIX/models" "$PREFIX/scripts" \
    "$RUN_DIR" "$LOG_DIR" "$STATE_DIR" "$TASK_CONFIG_DIR"
  as_root install -m 0644 "$ROOT/config/config.example.ini" "$PREFIX/config/config.example.ini"
  as_root install -m 0644 "$ROOT/config/standalone.tasks.example.json" "$PREFIX/config/standalone.tasks.example.json"
  as_root install -m 0644 "$ROOT/README.md" "$PREFIX/README.md"
  as_root install -m 0755 "$ROOT/scripts/rk3588_preflight.sh" "$PREFIX/scripts/rk3588_preflight.sh"
  as_root install -m 0755 "$ROOT/scripts/smoke_runtime.sh" "$PREFIX/scripts/smoke_runtime.sh"
  as_root install -m 0755 "$ROOT/scripts/convert_rknn_model.py" "$PREFIX/scripts/convert_rknn_model.py"
  as_root install -m 0755 "$ROOT/scripts/prepare_yolov8n_rk3588.sh" "$PREFIX/scripts/prepare_yolov8n_rk3588.sh"
  as_root install -m 0755 "$MANIFEST_TOOL" "$PREFIX/scripts/standalone_manifest.py"

  local key source_model target_model source_classes target_classes
  while IFS=$'\t' read -r key source_model target_model source_classes target_classes; do
    [[ -n "$key" ]] || continue
    if ! same_path "$source_model" "$target_model"; then
      as_root install -m 0644 "$source_model" "$target_model"
    fi
    if ! same_path "$source_classes" "$target_classes"; then
      as_root install -m 0644 "$source_classes" "$target_classes"
    fi
    [[ -s "$target_model" ]] || fail "模型安装失败: $target_model"
    [[ -s "$target_classes" ]] || fail "类别文件安装失败: $target_classes"
    ok "模型就绪: $key → $target_model"
  done <"${PLAN_DIR}/models.tsv"

  # 这里只清理由本脚本生成的逐路 INI；用户清单、模型和日志均保留。
  as_root find "$TASK_CONFIG_DIR" -maxdepth 1 -type f -name '*.ini' -delete
  local task_id control_port
  while IFS=$'\t' read -r task_id control_port; do
    [[ -n "$task_id" ]] || continue
    as_root install -d "$LOG_DIR/$task_id" "$LOG_DIR/$task_id/alerts"
    as_root install -m 0640 "${PLAN_DIR}/tasks/${task_id}.ini" "$TASK_CONFIG_DIR/${task_id}.ini"
  done <"${PLAN_DIR}/tasks.tsv"
  as_root install -m 0640 "${PLAN_DIR}/tasks.tsv" "$TASK_STATE_FILE"
  as_root install -m 0640 "${PLAN_DIR}/manifest.json" "$MANIFEST_FILE"
  ok "任务清单已落地: $MANIFEST_FILE"
}

install_systemd_template() {
  command -v systemctl >/dev/null 2>&1 || return 0
  local generated="${TMP_DIR}/${SERVICE_BASENAME}@.service"
  cat >"$generated" <<EOF
[Unit]
Description=EasyAIoT RK3588 AI runtime stream %i
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
WorkingDirectory=${PREFIX}
ExecStart=${BIN} ${TASK_CONFIG_DIR}/%i.ini
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
  fi
}

require_task_state() {
  [[ -s "$TASK_STATE_FILE" ]] || fail "尚无已安装任务；请先执行 install <任务清单.json>"
}

task_exists() {
  local wanted="$1"
  awk -F'\t' -v wanted="$wanted" '$1 == wanted { found=1 } END { exit !found }' "$TASK_STATE_FILE"
}

validate_target_task() {
  local target="${1:-}"
  [[ -z "$target" ]] && return 0
  [[ "$target" =~ ^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$ ]] || fail "任务 ID 非法: $target"
  task_exists "$target" || fail "未找到任务: $target"
}

selected_task_rows() {
  local target="${1:-}"
  if [[ -z "$target" ]]; then
    cat "$TASK_STATE_FILE"
  else
    awk -F'\t' -v wanted="$target" '$1 == wanted' "$TASK_STATE_FILE"
  fi
}

instance_name() { printf '%s@%s.service' "$SERVICE_BASENAME" "$1"; }
pid_file() { printf '%s/%s.pid' "$RUN_DIR" "$1"; }
task_log_file() { printf '%s/%s/runtime.log' "$LOG_DIR" "$1"; }

stop_legacy_service() {
  local legacy_pid_file="${RUN_DIR}/${SERVICE_BASENAME}.pid" legacy_pid=""
  if systemd_running && [[ -f "$LEGACY_UNIT_FILE" ]]; then
    as_root systemctl stop "${SERVICE_BASENAME}.service" >/dev/null 2>&1 || true
    as_root systemctl disable "${SERVICE_BASENAME}.service" >/dev/null 2>&1 || true
  fi
  if [[ -s "$legacy_pid_file" ]]; then
    legacy_pid="$(cat "$legacy_pid_file" 2>/dev/null || true)"
    if [[ "$legacy_pid" =~ ^[0-9]+$ ]] && kill -0 "$legacy_pid" 2>/dev/null; then
      as_root kill "$legacy_pid" 2>/dev/null || true
    fi
    as_root rm -f -- "$legacy_pid_file"
  fi
  if [[ -f "$LEGACY_UNIT_FILE" ]]; then
    as_root rm -f -- "$LEGACY_UNIT_FILE"
    if systemd_running; then
      as_root systemctl daemon-reload
    fi
    warn "已移除旧版单进程服务，迁移到逐路服务实例"
  fi
}

fallback_running() {
  local file
  file="$(pid_file "$1")"
  [[ -s "$file" ]] || return 1
  local pid
  pid="$(cat "$file" 2>/dev/null || true)"
  [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null
}

stop_fallback_task() {
  local task_id="$1" file pid
  file="$(pid_file "$task_id")"
  if fallback_running "$task_id"; then
    pid="$(cat "$file")"
    as_root kill "$pid" 2>/dev/null || true
    for _ in $(seq 1 20); do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.25
    done
    if kill -0 "$pid" 2>/dev/null; then
      as_root kill -KILL "$pid" 2>/dev/null || true
    fi
  fi
  as_root rm -f -- "$file"
}

service_stop() {
  local target="${1:-}"
  [[ -s "$TASK_STATE_FILE" ]] || return 0
  validate_target_task "$target"
  local task_id control_port
  while IFS=$'\t' read -r task_id control_port; do
    [[ -n "$task_id" ]] || continue
    if systemd_running && [[ -f "$UNIT_FILE" ]]; then
      as_root systemctl stop "$(instance_name "$task_id")" >/dev/null 2>&1 || true
    fi
    stop_fallback_task "$task_id"
  done < <(selected_task_rows "$target")
}

disable_installed_instances() {
  [[ -s "$TASK_STATE_FILE" ]] || return 0
  command -v systemctl >/dev/null 2>&1 || return 0
  local task_id control_port
  while IFS=$'\t' read -r task_id control_port; do
    [[ -n "$task_id" ]] || continue
    as_root systemctl disable "$(instance_name "$task_id")" >/dev/null 2>&1 || true
  done <"$TASK_STATE_FILE"
}

service_start() {
  local target="${1:-}"
  [[ -x "$BIN" ]] || fail "运行程序不存在，请先执行 install: $BIN"
  require_task_state
  validate_target_task "$target"
  preflight_runtime
  as_root install -d "$RUN_DIR" "$LOG_DIR"

  local task_id control_port file log_file
  while IFS=$'\t' read -r task_id control_port; do
    [[ -n "$task_id" ]] || continue
    file="$TASK_CONFIG_DIR/${task_id}.ini"
    log_file="$(task_log_file "$task_id")"
    [[ -s "$file" ]] || fail "任务配置不存在: $file"
    as_root install -d "$LOG_DIR/$task_id"
    if systemd_running && [[ -f "$UNIT_FILE" ]]; then
      as_root systemctl enable --now "$(instance_name "$task_id")" >/dev/null
    else
      if fallback_running "$task_id"; then
        warn "任务 $task_id 已经运行"
        continue
      fi
      as_root bash -c 'nohup "$1" "$2" >>"$3" 2>&1 & echo $! >"$4"' \
        _ "$BIN" "$file" "$log_file" "$(pid_file "$task_id")"
    fi
    ok "任务已启动: $task_id（RTSP 独立进程，控制端口 $control_port）"
  done < <(selected_task_rows "$target")
}

service_status() {
  local target="${1:-}" failed=0 state
  require_task_state
  validate_target_task "$target"
  local task_id control_port
  while IFS=$'\t' read -r task_id control_port; do
    [[ -n "$task_id" ]] || continue
    if systemd_running && [[ -f "$UNIT_FILE" ]]; then
      state="$(systemctl is-active "$(instance_name "$task_id")" 2>/dev/null || true)"
      if [[ "$state" == "active" ]]; then
        ok "$task_id：运行中，health=http://127.0.0.1:${control_port}/health"
      else
        warn "$task_id：$state"
        failed=1
      fi
    elif fallback_running "$task_id"; then
      ok "$task_id：运行中，PID=$(cat "$(pid_file "$task_id")")，health=http://127.0.0.1:${control_port}/health"
    else
      warn "$task_id：未运行"
      failed=1
    fi
  done < <(selected_task_rows "$target")
  return "$failed"
}

service_logs() {
  local target="${1:-}"
  require_task_state
  validate_target_task "$target"
  if systemd_running && [[ -f "$UNIT_FILE" ]]; then
    local args=() task_id control_port
    while IFS=$'\t' read -r task_id control_port; do
      [[ -n "$task_id" ]] && args+=( -u "$(instance_name "$task_id")" )
    done < <(selected_task_rows "$target")
    if [[ -t 1 && "${EASYAIOT_RK3588_LOG_FOLLOW:-1}" = "1" ]]; then
      as_root journalctl "${args[@]}" -n 200 -f
    else
      as_root journalctl "${args[@]}" -n 200 --no-pager
    fi
    return 0
  fi

  local task_id control_port log_file
  while IFS=$'\t' read -r task_id control_port; do
    [[ -n "$task_id" ]] || continue
    log_file="$(task_log_file "$task_id")"
    echo "===== $task_id ====="
    [[ -f "$log_file" ]] && tail -n 200 "$log_file" || warn "日志尚未生成: $log_file"
  done < <(selected_task_rows "$target")
  if [[ -n "$target" && -t 1 && "${EASYAIOT_RK3588_LOG_FOLLOW:-1}" = "1" ]]; then
    tail -n 200 -f "$(task_log_file "$target")"
  fi
}

verify_one_task() {
  local task_id="$1" control_port="$2" health=""
  local endpoint="http://127.0.0.1:${control_port}/health"
  info "等待任务 $task_id 的硬件流水线就绪: $endpoint"
  for _ in $(seq 1 "${EASYAIOT_RK3588_VERIFY_RETRIES:-45}"); do
    health="$(curl --silent --show-error --fail --max-time 2 "$endpoint" 2>/dev/null || true)"
    [[ -n "$health" ]] && break
    sleep 1
  done
  if [[ -z "$health" ]]; then
    warn "任务 $task_id 健康接口未就绪，最近日志如下"
    EASYAIOT_RK3588_LOG_FOLLOW=0 service_logs "$task_id" || true
    return 1
  fi
  grep -Eq '"platform"[[:space:]]*:[[:space:]]*"rk3588"' <<<"$health" || return 1
  grep -Eq '"infer_ep"[[:space:]]*:[[:space:]]*"rknn-rk3588' <<<"$health" || return 1
  grep -Eq '"decode_ep"[[:space:]]*:[[:space:]]*"mpp-rk3588"' <<<"$health" || return 1
  ok "$task_id 验收通过：MPP 硬解 + RGA + RKNN 流水线在线"
}

verify_runtime() {
  local target="${1:-}" failed=0
  require_task_state
  validate_target_task "$target"
  preflight_runtime
  local task_id control_port
  while IFS=$'\t' read -r task_id control_port; do
    [[ -n "$task_id" ]] || continue
    verify_one_task "$task_id" "$control_port" || failed=1
  done < <(selected_task_rows "$target")
  [[ "$failed" -eq 0 ]] || fail "一个或多个 RK3588 任务验收失败"
}

list_tasks() {
  require_task_state
  printf '%-24s %-8s %s\n' "任务" "端口" "配置"
  local task_id control_port
  while IFS=$'\t' read -r task_id control_port; do
    printf '%-24s %-8s %s\n' "$task_id" "$control_port" "$TASK_CONFIG_DIR/${task_id}.ini"
  done <"$TASK_STATE_FILE"
}

install_all() {
  validate_paths
  TMP_DIR="$(mktemp -d)"
  command -v python3 >/dev/null 2>&1 || ensure_build_toolchain
  resolve_manifest_source
  compile_task_plan
  preflight_build
  ensure_build_toolchain
  build_runtime
  stop_legacy_service
  service_stop
  disable_installed_instances
  install_runtime_files
  install_systemd_template
  service_start
  verify_runtime
  echo ""
  ok "部署完成：每路 RTSP 一个受监管进程，模型文件按清单共享安装"
  echo "  查看任务: $0 list"
  echo "  查看状态: $0 status [任务ID]"
  echo "  查看日志: $0 logs [任务ID]"
  echo "  修改配置: 编辑 $MANIFEST_FILE 后执行 $0 update"
  echo "  性能验收: $BENCH <模型.rknn> test.jpg 30 150 <类别.names>"
}

check_manifest() {
  validate_paths
  TMP_DIR="$(mktemp -d)"
  resolve_manifest_source
  compile_task_plan
  ok "任务清单可部署；未改动系统、未启动服务"
}

uninstall_runtime() {
  validate_paths
  stop_legacy_service
  service_stop
  disable_installed_instances
  if command -v systemctl >/dev/null 2>&1 && [[ -f "$UNIT_FILE" ]]; then
    as_root rm -f -- "$UNIT_FILE"
    systemd_running && as_root systemctl daemon-reload
  fi
  as_root rm -f -- "$BIN" "$BENCH"
  warn "程序与服务模板已移除；任务清单、逐路配置、模型和日志仍保留，避免误删现场数据"
  echo "  清单: $MANIFEST_FILE"
  echo "  配置: $TASK_CONFIG_DIR"
  echo "  模型: $PREFIX/models"
  echo "  日志: $LOG_DIR"
}

show_help() {
  cat <<EOF
RUNTIME-RK3588 多路独立部署

用法:
  $0 install <任务清单.json>
  $0 update [任务清单.json]
  $0 config-check <任务清单.json>
  $0 {start|stop|restart|status|logs|verify} [任务ID]
  $0 {list|preflight|deps|build|uninstall|help}

推荐流程：
  cp RUNTIME-RK3588/config/standalone.tasks.example.json ./rk3588.tasks.json
  # 编辑 models（模型库）和 tasks（多路 RTSP；每路引用一个或多个模型）
  sudo bash .scripts/docker/install_linux.sh rk3588 install ./rk3588.tasks.json

约定与 RUNTIME 一致：realtime 一路 RTSP 一份 INI、一个受监管进程；一份 INI
可通过 model_path、model_path_<key> 装载多个 RKNN 模型。模型文件只安装一次，
不同视频流按 models 列表自由复用。安装后由 systemd 模板实例开机自启；无 systemd
时使用逐任务 PID 和日志文件。不会启动 WEB、AI、VIDEO、MQTT 或 Docker。

旧版 EASYAIOT_RK3588_RTSP_URL + EASYAIOT_RK3588_MODEL_PATH/MODEL_URL 仍可用，
脚本会自动转换成单任务清单；它只用于兼容，不再是推荐部署方式。
EOF
}

case "$ACTION" in
  install|update)
    install_all
    ;;
  config-check|check-config|validate-config)
    check_manifest
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
    service_start "$ACTION_ARG"
    verify_runtime "$ACTION_ARG"
    ;;
  stop)
    validate_paths
    service_stop "$ACTION_ARG"
    ok "RK3588 任务已停止${ACTION_ARG:+: $ACTION_ARG}"
    ;;
  restart)
    validate_paths
    service_stop "$ACTION_ARG"
    service_start "$ACTION_ARG"
    verify_runtime "$ACTION_ARG"
    ;;
  status)
    validate_paths
    service_status "$ACTION_ARG"
    ;;
  logs)
    validate_paths
    service_logs "$ACTION_ARG"
    ;;
  verify)
    validate_paths
    verify_runtime "$ACTION_ARG"
    ;;
  list)
    validate_paths
    list_tasks
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
