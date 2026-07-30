#!/usr/bin/env bash
# Desktop launcher for EasyAIoT PANEL
set -euo pipefail

URL="${EASYAIOT_PANEL_URL:-http://127.0.0.1:9200/}"
SERVICE="easyaiot-panel"

is_active() {
  systemctl is-active --quiet "${SERVICE}" 2>/dev/null
}

start_service() {
  if is_active; then
    return 0
  fi
  # Try non-interactive first (works if user already has permission)
  if systemctl start "${SERVICE}" >/dev/null 2>&1; then
    return 0
  fi
  # Fallback to polkit prompt in desktop session
  if command -v pkexec >/dev/null 2>&1; then
    pkexec systemctl start "${SERVICE}" >/dev/null 2>&1 || true
  fi
}

open_url() {
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "${URL}" >/dev/null 2>&1 &
    return 0
  fi
  if command -v gio >/dev/null 2>&1; then
    gio open "${URL}" >/dev/null 2>&1 &
    return 0
  fi
  return 1
}

start_service
if ! is_active; then
  if command -v notify-send >/dev/null 2>&1; then
    notify-send "EasyAIoT Panel" "服务未启动，请执行: sudo systemctl start easyaiot-panel" || true
  fi
fi
open_url || exit 1
