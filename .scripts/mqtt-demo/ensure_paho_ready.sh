#!/usr/bin/env bash
# 确保当前 shell 能 import paho.mqtt（供 start_mqtt_demo / 一键 install 调用）
# 用法: source ensure_paho_ready.sh   或  bash ensure_paho_ready.sh && export ...
# 成功: 退出 0，并可能设置 PYTHONPATH / MQTT_DEMO_PYTHON / PATH
set -euo pipefail

_MQTT_DEMO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_MQTT_VENDOR="${_MQTT_DEMO_DIR}/vendor"
_MQTT_VENV="${MQTT_DEMO_VENV:-${_MQTT_DEMO_DIR}/.venv}"

_mqtt_paho_ok() {
    local py="${1:-python3}"
    command -v "$py" >/dev/null 2>&1 || [ -x "$py" ] || return 1
    "$py" -c "import paho.mqtt.client" >/dev/null 2>&1
}

_mqtt_ensure_paho_ready() {
    if [ -d "${_MQTT_VENDOR}/paho" ]; then
        export PYTHONPATH="${_MQTT_VENDOR}${PYTHONPATH:+:$PYTHONPATH}"
    fi

    if [ -n "${MQTT_DEMO_PYTHON:-}" ] && _mqtt_paho_ok "$MQTT_DEMO_PYTHON"; then
        return 0
    fi
    if _mqtt_paho_ok python3 || _mqtt_paho_ok python; then
        return 0
    fi

    echo "[mqtt-demo] 正在准备 paho-mqtt..." >&2

    # 系统 pip（含 PEP 668 突破）
    if command -v python3 >/dev/null 2>&1; then
        python3 -m pip install --user -q paho-mqtt >/dev/null 2>&1 \
            || python3 -m pip install --break-system-packages -q paho-mqtt >/dev/null 2>&1 \
            || python3 -m pip install -q paho-mqtt >/dev/null 2>&1 \
            || true
        if _mqtt_paho_ok python3; then
            return 0
        fi
    fi

    # 本地 venv：写入 PATH 前缀，兼容仍只认 python3 的旧版 start 脚本
    local base_py=""
    for cand in /usr/bin/python3 /bin/python3 python3; do
        if [ -x "$cand" ] || command -v "$cand" >/dev/null 2>&1; then
            if "$cand" -c "import sys" >/dev/null 2>&1; then
                base_py="$cand"
                break
            fi
        fi
    done
    if [ -n "$base_py" ]; then
        if [ ! -x "${_MQTT_VENV}/bin/python" ]; then
            "$base_py" -m venv "$_MQTT_VENV" >/dev/null 2>&1 \
                || "$base_py" -m venv --without-pip "$_MQTT_VENV" >/dev/null 2>&1 \
                || true
        fi
        if [ -x "${_MQTT_VENV}/bin/pip" ]; then
            "${_MQTT_VENV}/bin/pip" install -q paho-mqtt >/dev/null 2>&1 || true
        elif [ -x "${_MQTT_VENV}/bin/python" ]; then
            "${_MQTT_VENV}/bin/python" -m pip install -q paho-mqtt >/dev/null 2>&1 || true
        fi
        if [ -x "${_MQTT_VENV}/bin/python" ] && _mqtt_paho_ok "${_MQTT_VENV}/bin/python"; then
            export MQTT_DEMO_PYTHON="${_MQTT_VENV}/bin/python"
            export PATH="${_MQTT_VENV}/bin:${PATH}"
            return 0
        fi
    fi

    # vendor 已在 PYTHONPATH 时再测一次
    if _mqtt_paho_ok python3 || _mqtt_paho_ok python; then
        return 0
    fi
    return 1
}

if _mqtt_ensure_paho_ready; then
    if [ "${1:-}" = "print-env" ]; then
        [ -n "${PYTHONPATH:-}" ] && echo "export PYTHONPATH=$(printf %q "$PYTHONPATH")"
        [ -n "${MQTT_DEMO_PYTHON:-}" ] && echo "export MQTT_DEMO_PYTHON=$(printf %q "$MQTT_DEMO_PYTHON")"
        echo "export PATH=$(printf %q "$PATH")"
    fi
    exit 0
fi
echo "[mqtt-demo] 无法准备 paho-mqtt。请执行: python3 -m pip install --break-system-packages paho-mqtt" >&2
exit 1
