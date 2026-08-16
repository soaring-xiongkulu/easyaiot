#!/usr/bin/env bash
# full 形态：并行常驻工业协议演示从站，供 Sink 轮询，让页面 Modbus TCP / RTU / OPC UA 有数据。
# 用法:
#   bash start_industrial_demo.sh
#   EASYAIOT_ENABLE_INDUSTRIAL_DEMO=0 bash start_industrial_demo.sh  # 跳过
#   INDUSTRIAL_DEMO_HOST=127.0.0.1 bash start_industrial_demo.sh    # 强制设备连接地址
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${SCRIPTS_ROOT}/.." && pwd)"
RUN_DIR="${SCRIPT_DIR}/run"
LOG_DIR="${RUN_DIR}/logs"
mkdir -p "$RUN_DIR" "$LOG_DIR"

MODBUS_TCP_DIR="${SCRIPTS_ROOT}/modbus-tcp-demo"
MODBUS_RTU_DIR="${SCRIPTS_ROOT}/modbus-rtu-demo"
MODBUS_RTU_VIRT_DIR="${SCRIPTS_ROOT}/modbus-rtu-virtual-serial"
OPC_UA_DIR="${SCRIPTS_ROOT}/opc-ua-demo"
SEED_SQL="${SCRIPTS_ROOT}/postgresql/industrial_protocol_seed.sql"

MODBUS_TCP_PORT="${MODBUS_TCP_PORT:-5020}"
OPC_UA_ENDPOINT="${OPC_UA_ENDPOINT:-opc.tcp://0.0.0.0:4840/freeopcua/server/}"
RTU_LINK="${LINK:-/tmp/easyaiot-modbus-rtu-u}"
RTU_UNIT="${UNIT:-1}"

if [ "${EASYAIOT_ENABLE_INDUSTRIAL_DEMO:-1}" = "0" ]; then
    echo "[industrial-demo] EASYAIOT_ENABLE_INDUSTRIAL_DEMO=0，跳过启动"
    exit 0
fi

is_running() {
    local pid_file="$1"
    [ -f "$pid_file" ] || return 1
    local pid
    pid="$(cat "$pid_file" 2>/dev/null || true)"
    [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

resolve_python() {
    local need_mod="${1:-}"
    if [ -n "${INDUSTRIAL_DEMO_PYTHON:-}" ] && command -v "$INDUSTRIAL_DEMO_PYTHON" >/dev/null 2>&1; then
        echo "$INDUSTRIAL_DEMO_PYTHON"
        return
    fi
    # OPC UA 优先用目录内 venv
    if [ "$need_mod" = "asyncua" ] && [ -x "${OPC_UA_DIR}/.venv/bin/python" ]; then
        if "${OPC_UA_DIR}/.venv/bin/python" -c "import asyncua" 2>/dev/null; then
            echo "${OPC_UA_DIR}/.venv/bin/python"
            return
        fi
    fi
    for cand in python3 python; do
        if command -v "$cand" >/dev/null 2>&1; then
            if [ -z "$need_mod" ] || "$cand" -c "import ${need_mod}" 2>/dev/null; then
                echo "$cand"
                return
            fi
        fi
    done
    echo ""
}

ensure_pip_mod() {
    local mod="$1" pkg="${2:-$1}"
    local py
    py="$(resolve_python "$mod")"
    if [ -n "$py" ]; then
        echo "$py"
        return 0
    fi
    if ! command -v python3 >/dev/null 2>&1; then
        echo ""
        return 1
    fi
    if [ "$mod" = "asyncua" ]; then
        python3 -m venv "${OPC_UA_DIR}/.venv" 2>/dev/null || true
        if [ -x "${OPC_UA_DIR}/.venv/bin/pip" ]; then
            "${OPC_UA_DIR}/.venv/bin/pip" install -q -r "${OPC_UA_DIR}/requirements.txt" 2>/dev/null || true
            if "${OPC_UA_DIR}/.venv/bin/python" -c "import asyncua" 2>/dev/null; then
                echo "${OPC_UA_DIR}/.venv/bin/python"
                return 0
            fi
        fi
    fi
    python3 -m pip install --user -q "$pkg" 2>/dev/null \
        || python3 -m pip install -q "$pkg" 2>/dev/null \
        || true
    if python3 -c "import ${mod}" 2>/dev/null; then
        echo "python3"
        return 0
    fi
    echo ""
    return 1
}

port_listening() {
    local port="$1"
    if command -v ss >/dev/null 2>&1; then
        ss -ltn 2>/dev/null | grep -Eq ":${port}([[:space:]]|$)"
        return $?
    fi
    python3 - <<PY >/dev/null 2>&1
import socket
s=socket.socket()
s.settimeout(0.3)
try:
    s.bind(("0.0.0.0", int("${port}")))
except OSError:
    raise SystemExit(0)
raise SystemExit(1)
PY
}

start_bg() {
    local role="$1"
    local ready_port="${2:-}"
    shift 2
    local pid_file="${RUN_DIR}/${role}.pid"
    local log_file="${LOG_DIR}/${role}.log"
    if is_running "$pid_file"; then
        echo "[industrial-demo] ${role} 已在运行 pid=$(cat "$pid_file")"
        return 0
    fi
    # 清理陈旧 pid
    rm -f "$pid_file"
    echo "[industrial-demo] 启动 ${role}: $*"
    # 脱离当前会话，避免安装脚本退出后被 SIGHUP
    PYTHONUNBUFFERED=1 nohup "$@" >>"$log_file" 2>&1 </dev/null &
    local new_pid=$!
    echo "$new_pid" >"$pid_file"
    disown "$new_pid" 2>/dev/null || true
    local i
    for i in 1 2 3 4 5 6 7 8 9 10; do
        if is_running "$pid_file"; then
            if [ -z "$ready_port" ] || port_listening "$ready_port"; then
                echo "[industrial-demo] ${role} 已启动 pid=$(cat "$pid_file") log=${log_file}"
                return 0
            fi
        elif [ -n "$ready_port" ] && port_listening "$ready_port"; then
            # 子进程可能被 systemd/容器接管，端口就绪即视为成功
            echo "[industrial-demo] ${role} 端口 ${ready_port} 已就绪 log=${log_file}"
            return 0
        fi
        sleep 0.3
    done
    echo "[industrial-demo] ${role} 启动失败，见 ${log_file}" >&2
    tail -n 30 "$log_file" 2>/dev/null || true
    return 1
}

# ---------- 1) Modbus RTU 虚拟串口从站 ----------
start_modbus_rtu_virtual() {
    if [ ! -x "${MODBUS_RTU_VIRT_DIR}/start.sh" ]; then
        chmod +x "${MODBUS_RTU_VIRT_DIR}/start.sh" "${MODBUS_RTU_VIRT_DIR}/stop.sh" 2>/dev/null || true
    fi
    if [ ! -f "${MODBUS_RTU_VIRT_DIR}/start.sh" ]; then
        echo "[industrial-demo] 缺少 ${MODBUS_RTU_VIRT_DIR}/start.sh" >&2
        return 1
    fi
    # 已有可用虚拟串口则复用（避免 PTY 耗尽时重复 openpty）
    if [ -e "$RTU_LINK" ] && pgrep -f "${MODBUS_RTU_VIRT_DIR}/00_virtual_rtu_slave.py" >/dev/null 2>&1; then
        echo "[industrial-demo] modbus-rtu-virtual-serial 已在运行（${RTU_LINK}）"
        return 0
    fi
    if LINK="$RTU_LINK" UNIT="$RTU_UNIT" bash "${MODBUS_RTU_VIRT_DIR}/start.sh"; then
        return 0
    fi
    # start 失败但链路仍可用（例如旧进程占着 PTY）
    if [ -e "$RTU_LINK" ]; then
        echo "[industrial-demo] 警告: start.sh 失败，但 ${RTU_LINK} 仍存在，继续" >&2
        return 0
    fi
    return 1
}

# ---------- 2) Modbus TCP 从站 ----------
start_modbus_tcp() {
    if port_listening "$MODBUS_TCP_PORT"; then
        echo "[industrial-demo] modbus-tcp 端口 ${MODBUS_TCP_PORT} 已在监听，跳过"
        return 0
    fi
    local py
    py="$(resolve_python)"
    [ -n "$py" ] || py="python3"
    start_bg modbus-tcp "$MODBUS_TCP_PORT" "$py" -u "${MODBUS_TCP_DIR}/00_slave_simulator.py" \
        --host 0.0.0.0 --port "$MODBUS_TCP_PORT" --unit 1
}

# ---------- 3) OPC UA 服务器 ----------
start_opc_ua() {
    if port_listening 4840; then
        echo "[industrial-demo] opc-ua 端口 4840 已在监听，跳过"
        return 0
    fi
    local py
    py="$(ensure_pip_mod asyncua asyncua)" || true
    if [ -z "${py:-}" ]; then
        echo "[industrial-demo] 缺少 asyncua，OPC UA 演示未启动（pip install asyncua）" >&2
        return 1
    fi
    start_bg opc-ua 4840 "$py" -u "${OPC_UA_DIR}/00_server_simulator.py" \
        --endpoint "$OPC_UA_ENDPOINT"
}

# ---------- 4) modbus-rtu-demo 依赖就绪（不抢占串口：Sink 独占轮询） ----------
prepare_modbus_rtu_demo() {
    local py
    py="$(ensure_pip_mod serial pyserial)" || true
    if [ -z "${py:-}" ]; then
        echo "[industrial-demo] 警告: pyserial 未就绪，modbus-rtu-demo 手动联调可能失败" >&2
        return 0
    fi
    # 轻量自检一次，确认虚拟串口可读；不常驻以免与 Sink 抢串口
    if [ -e "$RTU_LINK" ] && [ -f "${MODBUS_RTU_VIRT_DIR}/01_self_test.py" ]; then
        if "$py" "${MODBUS_RTU_VIRT_DIR}/01_self_test.py" --port "$RTU_LINK" >/dev/null 2>&1; then
            echo "[industrial-demo] modbus-rtu-demo 链路自检通过（${RTU_LINK}）"
        else
            echo "[industrial-demo] 警告: RTU 自检未通过，见 virtual-serial 日志" >&2
        fi
    fi
    # 标记“已准备”，供 status 查看
    date +%s >"${RUN_DIR}/modbus-rtu-demo.ready"
    echo "[industrial-demo] modbus-rtu-demo 工具目录就绪: ${MODBUS_RTU_DIR}"
}

# ---------- 解析 Sink 可达的宿主机地址 ----------
resolve_demo_host() {
    if [ -n "${INDUSTRIAL_DEMO_HOST:-}" ]; then
        echo "$INDUSTRIAL_DEMO_HOST"
        return
    fi
    # Sink 在 Docker 内时用 host.docker.internal；否则用 127.0.0.1（本机 IDE 跑 Sink）
    if command -v docker >/dev/null 2>&1 \
        && docker ps --format '{{.Names}}' 2>/dev/null | grep -qx 'iot-sink'; then
        echo "host.docker.internal"
        return
    fi
    if [ -n "${HOST_IP:-}" ]; then
        echo "$HOST_IP"
        return
    fi
    echo "127.0.0.1"
}

# ---------- 写入/刷新演示设备种子 ----------
apply_industrial_seed() {
    if [ "${EASYAIOT_APPLY_INDUSTRIAL_SEED:-1}" = "0" ]; then
        echo "[industrial-demo] 跳过种子写入（EASYAIOT_APPLY_INDUSTRIAL_SEED=0）"
        return 0
    fi
    if ! command -v docker >/dev/null 2>&1; then
        echo "[industrial-demo] 无 docker，跳过种子写入"
        return 0
    fi
    if ! docker ps --format '{{.Names}}' 2>/dev/null | grep -qx 'postgres-server'; then
        echo "[industrial-demo] postgres-server 未运行，跳过种子写入"
        return 0
    fi

    local host
    host="$(resolve_demo_host)"

    if [ -f "$SEED_SQL" ]; then
        echo "[industrial-demo] 写入演示种子（设备 host/endpoint -> ${host}）..."
        if ! docker exec -i postgres-server psql -U postgres -d iot-device20 -v ON_ERROR_STOP=1 <"$SEED_SQL" \
            >"${LOG_DIR}/seed.log" 2>&1; then
            echo "[industrial-demo] 种子 SQL 执行失败，见 ${LOG_DIR}/seed.log" >&2
            tail -n 40 "${LOG_DIR}/seed.log" 2>/dev/null || true
            return 1
        fi
    else
        echo "[industrial-demo] 未找到种子 ${SEED_SQL}，尝试仅刷新已有演示设备地址" >&2
        local n
        n=$(docker exec postgres-server psql -U postgres -d iot-device20 -tAc \
            "SELECT COUNT(*) FROM device WHERE id IN (920001,920002,920003) AND deleted = 0;" 2>/dev/null | tr -d '[:space:]' || echo 0)
        if [ "${n:-0}" -eq 0 ] 2>/dev/null; then
            echo "[industrial-demo] 库中无演示设备且缺少种子文件，跳过 DB 写入" >&2
            return 0
        fi
        : >"${LOG_DIR}/seed.log"
    fi

    # 将占位地址刷新为当前可达地址（Docker Sink -> host.docker.internal）
    docker exec postgres-server psql -U postgres -d iot-device20 -v ON_ERROR_STOP=1 <<SQL >>"${LOG_DIR}/seed.log" 2>&1
UPDATE device
SET ip_address = '${host}',
    extension = jsonb_set(
      jsonb_set(
        jsonb_set(extension::jsonb, '{protocolConfig,host}', '"${host}"'),
        '{protocolConfig,port}', '5020'
      ),
      '{protocolConfig,enabled}', 'true'
    )::text,
    update_time = CURRENT_TIMESTAMP
WHERE id = 920001;

UPDATE device
SET extension = jsonb_set(
      jsonb_set(
        jsonb_set(extension::jsonb, '{protocolConfig,serialPort}', '"${RTU_LINK}"'),
        '{protocolConfig,rs485Mode}', 'false'
      ),
      '{protocolConfig,enabled}', 'true'
    )::text,
    update_time = CURRENT_TIMESTAMP
WHERE id = 920002;

UPDATE device
SET ip_address = '${host}',
    extension = jsonb_set(
      jsonb_set(extension::jsonb, '{protocolConfig,endpointUrl}',
        '"opc.tcp://${host}:4840/freeopcua/server/"'),
      '{protocolConfig,enabled}', 'true'
    )::text,
    update_time = CURRENT_TIMESTAMP
WHERE id = 920003;
SQL
    echo "[industrial-demo] 演示设备已指向 ${host} / ${RTU_LINK}"
}

echo "[industrial-demo] 项目根: ${PROJECT_ROOT}"
ok=0
fail=0

if start_modbus_rtu_virtual; then ok=$((ok + 1)); else fail=$((fail + 1)); fi
if start_modbus_tcp; then ok=$((ok + 1)); else fail=$((fail + 1)); fi
if start_opc_ua; then ok=$((ok + 1)); else fail=$((fail + 1)); fi
if prepare_modbus_rtu_demo; then ok=$((ok + 1)); else fail=$((fail + 1)); fi
apply_industrial_seed || fail=$((fail + 1))

echo "[industrial-demo] 完成: 成功 ${ok}，失败 ${fail}"
echo "[industrial-demo] 停止: bash ${SCRIPT_DIR}/stop_industrial_demo.sh"
[ "$fail" -eq 0 ]
