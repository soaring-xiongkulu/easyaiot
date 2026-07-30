#!/usr/bin/env bash
set -euo pipefail

URL="${EASYAIOT_PANEL_URL:-http://127.0.0.1:9200/}"
SERVICE="easyaiot-panel"

if ! systemctl is-active --quiet "${SERVICE}" 2>/dev/null; then
  systemctl start "${SERVICE}" >/dev/null 2>&1 || true
fi

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "${URL}" >/dev/null 2>&1 &
elif command -v gio >/dev/null 2>&1; then
  gio open "${URL}" >/dev/null 2>&1 &
fi
