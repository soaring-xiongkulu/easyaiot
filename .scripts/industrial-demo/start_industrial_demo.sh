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

# 解释器可用且能 import 指定模块（避免把损坏的 .venv/bin/python 当成功）
python_has_mod() {
    local py="$1" mod="${2:-}"
    [ -n "$py" ] || return 1
    [ -x "$py" ] || command -v "$py" >/dev/null 2>&1 || return 1
    if [ -z "$mod" ]; then
        "$py" -c "import sys" >/dev/null 2>&1
        return $?
    fi
    "$py" -c "import ${mod}" >/dev/null 2>&1
}

# 损坏的 venv：ensurepip 失败后常留下不可用的 bin/python*
opcua_venv_is_broken() {
    local vpy="${OPC_UA_DIR}/.venv/bin/python"
    local vpy3="${OPC_UA_DIR}/.venv/bin/python3"
    [ -d "${OPC_UA_DIR}/.venv" ] || return 1
    if [ -x "$vpy" ] && python_has_mod "$vpy"; then
        return 1
    fi
    if [ -x "$vpy3" ] && python_has_mod "$vpy3"; then
        return 1
    fi
    # 目录存在但解释器不可用
    return 0
}

purge_broken_opcua_venv() {
    if opcua_venv_is_broken; then
        echo "[industrial-demo] 清理损坏的 opc-ua .venv（常见于缺少 python3-venv/ensurepip）" >&2
        rm -rf "${OPC_UA_DIR}/.venv"
    fi
}

# 尝试安装 python3-venv（仅 root + apt；版本化包如 python3.14-venv）
try_install_python_venv_pkg() {
    if [ "$(id -u)" -ne 0 ] 2>/dev/null; then
        return 1
    fi
    if ! command -v apt-get >/dev/null 2>&1; then
        return 1
    fi
    local ver=""
    ver="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)"
    local -a pkgs=(python3-venv)
    [ -n "$ver" ] && pkgs+=("python${ver}-venv")
    echo "[industrial-demo] 尝试安装: ${pkgs[*]}" >&2
    DEBIAN_FRONTEND=noninteractive apt-get install -y "${pkgs[@]}" >/dev/null 2>&1
}

bootstrap_opcua_venv() {
    local venv_dir="${OPC_UA_DIR}/.venv"
    local vpy="${venv_dir}/bin/python"
    mkdir -p "$OPC_UA_DIR"
    purge_broken_opcua_venv

    # 1) 标准 venv
    if ! python3 -m venv "$venv_dir" >/dev/null 2>&1; then
        try_install_python_venv_pkg || true
        rm -rf "$venv_dir"
        if ! python3 -m venv "$venv_dir" >/dev/null 2>&1; then
            # 2) 无 ensurepip 时先建空 venv，再 get-pip
            rm -rf "$venv_dir"
            if python3 -m venv --without-pip "$venv_dir" >/dev/null 2>&1 \
                && [ -x "$vpy" ]; then
                if command -v curl >/dev/null 2>&1; then
                    curl -fsSL https://bootstrap.pypa.io/get-pip.py -o /tmp/easyaiot-get-pip.py 2>/dev/null \
                        && "$vpy" /tmp/easyaiot-get-pip.py -q 2>/dev/null \
                        || true
                    rm -f /tmp/easyaiot-get-pip.py
                fi
            fi
        fi
    fi

    if [ ! -x "$vpy" ] || ! python_has_mod "$vpy"; then
        rm -rf "$venv_dir"
        return 1
    fi

    if ! python_has_mod "$vpy" asyncua; then
        if [ -x "${venv_dir}/bin/pip" ]; then
            "${venv_dir}/bin/pip" install -q -r "${OPC_UA_DIR}/requirements.txt" >/dev/null 2>&1 \
                || "${venv_dir}/bin/pip" install -q asyncua >/dev/null 2>&1 \
                || true
        else
            "$vpy" -m pip install -q -r "${OPC_UA_DIR}/requirements.txt" >/dev/null 2>&1 \
                || "$vpy" -m pip install -q asyncua >/dev/null 2>&1 \
                || true
        fi
    fi
    if python_has_mod "$vpy" asyncua; then
        echo "$vpy"
        return 0
    fi
    return 1
}

install_mod_system_python() {
    local mod="$1" pkg="${2:-$1}"
    # 用户目录 → 系统 → PEP 668 break-system-packages
    python3 -m pip install --user -q "$pkg" >/dev/null 2>&1 \
        || python3 -m pip install -q "$pkg" >/dev/null 2>&1 \
        || python3 -m pip install --break-system-packages -q "$pkg" >/dev/null 2>&1 \
        || true
    python_has_mod python3 "$mod"
}

resolve_python() {
    local need_mod="${1:-}"
    if [ -n "${INDUSTRIAL_DEMO_PYTHON:-}" ] && command -v "$INDUSTRIAL_DEMO_PYTHON" >/dev/null 2>&1; then
        if [ -z "$need_mod" ] || python_has_mod "$INDUSTRIAL_DEMO_PYTHON" "$need_mod"; then
            echo "$INDUSTRIAL_DEMO_PYTHON"
            return
        fi
    fi
    # OPC UA：仅在 venv 真正可用时使用
    if [ "$need_mod" = "asyncua" ]; then
        purge_broken_opcua_venv
        if python_has_mod "${OPC_UA_DIR}/.venv/bin/python" asyncua; then
            echo "${OPC_UA_DIR}/.venv/bin/python"
            return
        fi
    fi
    for cand in python3 python; do
        if command -v "$cand" >/dev/null 2>&1; then
            if [ -z "$need_mod" ] || python_has_mod "$cand" "$need_mod"; then
                echo "$cand"
                return
            fi
        fi
    done
    echo ""
}

ensure_pip_mod() {
    local mod="$1" pkg="${2:-$1}"
    local py=""
    py="$(resolve_python "$mod")"
    if [ -n "$py" ] && python_has_mod "$py" "$mod"; then
        echo "$py"
        return 0
    fi
    if ! command -v python3 >/dev/null 2>&1; then
        echo ""
        return 1
    fi
    if [ "$mod" = "asyncua" ]; then
        # 仅捕获最后一行路径；诊断信息走 stderr
        py="$(bootstrap_opcua_venv | tail -n 1)" || true
        if [ -n "$py" ] && python_has_mod "$py" asyncua; then
            echo "$py"
            return 0
        fi
    fi
    if install_mod_system_python "$mod" "$pkg"; then
        echo "python3"
        return 0
    fi
    echo ""
    return 1
}

port_listening() {
    local port="$1"
    # 优先 TCP 探活（比解析 ss 更可靠）
    if command -v python3 >/dev/null 2>&1; then
        if python3 - <<PY >/dev/null 2>&1
import socket
s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(0.4)
try:
    s.connect(("127.0.0.1", int("${port}")))
except Exception:
    raise SystemExit(1)
finally:
    try:
        s.close()
    except Exception:
        pass
raise SystemExit(0)
PY
        then
            return 0
        fi
    fi
    if command -v ss >/dev/null 2>&1; then
        ss -ltn 2>/dev/null | grep -Eq ":${port}([[:space:]]|$)"
        return $?
    fi
    # 回退：本机能 bind 该端口则认为无人监听
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

# start_bg <role> <ready_port|""> [max_wait_sec] -- <cmd...>
# 兼容旧调用: start_bg role port cmd...（第3参若不是纯数字则视为命令开头）
start_bg() {
    local role="$1"
    local ready_port="${2:-}"
    shift 2
    local max_wait=8
    if [ "${1:-}" = "--" ]; then
        shift
    elif [[ "${1:-}" =~ ^[0-9]+$ ]]; then
        max_wait="$1"
        shift
        [ "${1:-}" = "--" ] && shift
    fi
    local ready_marker="${START_BG_READY_MARKER:-}"
    local pid_file="${RUN_DIR}/${role}.pid"
    local log_file="${LOG_DIR}/${role}.log"
    if is_running "$pid_file"; then
        echo "[industrial-demo] ${role} 已在运行 pid=$(cat "$pid_file")"
        return 0
    fi
    # 清理陈旧 pid / 日志尾，便于探测 READY
    rm -f "$pid_file"
    : >"$log_file"
    echo "[industrial-demo] 启动 ${role}: $*"
    # 脱离当前会话，避免安装脚本退出后被 SIGHUP
    PYTHONUNBUFFERED=1 nohup "$@" >>"$log_file" 2>&1 </dev/null &
    local new_pid=$!
    echo "$new_pid" >"$pid_file"
    disown "$new_pid" 2>/dev/null || true
    local i elapsed=0
    local steps=$((max_wait * 2))
    [ "$steps" -lt 1 ] && steps=1
    for i in $(seq 1 "$steps"); do
        if [ -n "$ready_marker" ] && grep -qF "$ready_marker" "$log_file" 2>/dev/null; then
            if is_running "$pid_file" || { [ -n "$ready_port" ] && port_listening "$ready_port"; }; then
                echo "[industrial-demo] ${role} 已启动 pid=$(cat "$pid_file" 2>/dev/null || echo '?') log=${log_file}"
                return 0
            fi
        fi
        if is_running "$pid_file"; then
            if [ -z "$ready_port" ] || port_listening "$ready_port"; then
                echo "[industrial-demo] ${role} 已启动 pid=$(cat "$pid_file") log=${log_file}"
                return 0
            fi
        elif [ -n "$ready_port" ] && port_listening "$ready_port"; then
            # 子进程可能被 systemd/容器接管，端口就绪即视为成功
            echo "[industrial-demo] ${role} 端口 ${ready_port} 已就绪 log=${log_file}"
            return 0
        elif ! is_running "$pid_file"; then
            # 进程已退出：尽早失败，避免空等
            if [ "$i" -ge 4 ]; then
                break
            fi
        fi
        sleep 0.5
        elapsed=$((elapsed + 1))
    done
    echo "[industrial-demo] ${role} 启动失败，见 ${log_file}" >&2
    if [ -f "$pid_file" ] && ! is_running "$pid_file"; then
        echo "[industrial-demo] ${role} 进程已退出（pid 文件残留）" >&2
    fi
    tail -n 40 "$log_file" 2>/dev/null || true
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
    start_bg modbus-tcp "$MODBUS_TCP_PORT" 8 -- "$py" -u "${MODBUS_TCP_DIR}/00_slave_simulator.py" \
        --host 0.0.0.0 --port "$MODBUS_TCP_PORT" --unit 1
}

# ---------- 3) OPC UA 服务器 ----------
start_opc_ua() {
    if port_listening 4840; then
        echo "[industrial-demo] opc-ua 端口 4840 已在监听，跳过"
        return 0
    fi
    local py=""
    py="$(ensure_pip_mod asyncua asyncua)" || true
    # 防止把 ensurepip 报错文本当成解释器路径
    if [ -z "${py:-}" ] || [[ "$py" == *$'\n'* ]] || [[ "$py" == *"ensurepip"* ]]; then
        echo "[industrial-demo] 缺少可用的 asyncua 环境，OPC UA 演示未启动" >&2
        echo "[industrial-demo] 请安装: apt install python3-venv python3.\$(python3 -c 'import sys;print(sys.version_info.minor)')-venv" >&2
        echo "[industrial-demo] 或: python3 -m pip install --user asyncua" >&2
        return 1
    fi
    if ! python_has_mod "$py" asyncua; then
        echo "[industrial-demo] 解释器不可用或无 asyncua: ${py}" >&2
        return 1
    fi
    START_BG_READY_MARKER="OPC UA READY" \
        start_bg opc-ua 4840 25 -- "$py" -u "${OPC_UA_DIR}/00_server_simulator.py" \
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
