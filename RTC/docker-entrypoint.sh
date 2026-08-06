#!/usr/bin/env bash
# EasyAIoT RTC 容器入口：渲染 go2rtc 配置 → 启动 go2rtc → 启动 Python 管理服务
set -euo pipefail

CONFIG_DIR="${GO2RTC_CONFIG_DIR:-/config}"
CONFIG_FILE="${GO2RTC_CONFIG:-${CONFIG_DIR}/go2rtc.yaml}"
TEMPLATE="${GO2RTC_CONFIG_TEMPLATE:-/app/config/go2rtc.yaml.template}"

mkdir -p "$CONFIG_DIR"

export GO2RTC_API_LISTEN="${GO2RTC_API_LISTEN:-:1984}"
export GO2RTC_RTSP_LISTEN="${GO2RTC_RTSP_LISTEN:-:8554}"
export GO2RTC_WEBRTC_LISTEN="${GO2RTC_WEBRTC_LISTEN:-:8555}"

# 渲染配置模板（envsubst 替换 ${VAR} 占位符）
if [ -f "$TEMPLATE" ]; then
  envsubst < "$TEMPLATE" > "$CONFIG_FILE"
  echo "[RTC] go2rtc 配置已渲染: $CONFIG_FILE"
fi

# 若不存在配置文件则创建最小配置
if [ ! -f "$CONFIG_FILE" ]; then
  cat > "$CONFIG_FILE" <<EOF
api:
  listen: ":1984"
  origin: "*"
rtsp:
  listen: ":8554"
webrtc:
  listen: ":8555"
log:
  level: info
EOF
  echo "[RTC] 已创建默认 go2rtc 配置"
fi

# 启动 go2rtc（后台）
echo "[RTC] 启动 go2rtc ..."
go2rtc -config "$CONFIG_FILE" &
GO2RTC_PID=$!

# 等待 go2rtc API 就绪
GO2RTC_URL="${GO2RTC_API_URL:-http://127.0.0.1:1984}"
for i in $(seq 1 30); do
  if curl -sf "${GO2RTC_URL}/api" >/dev/null 2>&1; then
    echo "[RTC] go2rtc 已就绪 (${GO2RTC_URL})"
    break
  fi
  if ! kill -0 "$GO2RTC_PID" 2>/dev/null; then
    echo "[RTC] go2rtc 进程异常退出" >&2
    exit 1
  fi
  sleep 1
done

# 启动 Python 管理服务（前台）
echo "[RTC] 启动管理服务 :${FLASK_RUN_PORT:-6100} ..."
exec python run.py
