#!/usr/bin/env bash
# 供 install_linux.sh / install_business_linux.sh 在栈启动后同步控制面 Agent 凭据。

# 当前部署形态是否应启动 iot-node（mini 形态不启动，故无需同步宿主机 Agent）
_platform_agent_iot_node_enabled() {
    local project_root="$1"
    local profile_script="${project_root}/.scripts/docker/deploy_profile.sh"
    if [[ ! -f "$profile_script" ]]; then
        return 0
    fi
  # shellcheck source=/dev/null
    source "$profile_script"
    load_saved_deploy_profile
    apply_deploy_profile
    local skip
    for skip in $(device_skipped_services); do
        if [[ "$skip" == "iot-node" ]]; then
            return 1
        fi
    done
    return 0
}

_resolve_platform_agent_script() {
    local project_root="$1"
    local preferred="${EASYAIOT_PLATFORM_AGENT_SCRIPT:-}"
    local candidate=""

    # 显式指定（可为相对仓库根或绝对路径）
    if [[ -n "$preferred" ]]; then
        if [[ "$preferred" = /* ]]; then
            candidate="$preferred"
        else
            candidate="${project_root}/${preferred#./}"
        fi
        if [[ -f "$candidate" ]]; then
            echo "$candidate"
            return 0
        fi
    fi

    # CentOS 7：优先兼容脚本（bash 4.2 / 旧 Python）
    local os_id="" os_version="" os_major=""
    if [[ -f /etc/os-release ]]; then
        # shellcheck disable=SC1091
        . /etc/os-release
        os_id="${ID:-}"
        os_version="${VERSION_ID:-}"
    elif [[ -f /etc/redhat-release ]] && grep -qi centos /etc/redhat-release 2>/dev/null; then
        os_id="centos"
        os_version="$(grep -oE '[0-9]+(\.[0-9]+)?' /etc/redhat-release 2>/dev/null | head -1 || true)"
    fi
    os_major="${os_version%%.*}"
    if [[ "$os_id" == "centos" && "$os_major" == "7" ]]; then
        candidate="${project_root}/.scripts/node/ensure_platform_agent_centos7.sh"
        if [[ -f "$candidate" ]]; then
            echo "$candidate"
            return 0
        fi
    fi

    candidate="${project_root}/.scripts/node/ensure_platform_agent.sh"
    if [[ -f "$candidate" ]]; then
        echo "$candidate"
        return 0
    fi
    return 1
}

ensure_platform_agent_if_needed() {
    local project_root="${EASYAIOT_PROJECT_ROOT:-${EASYAIOT_ROOT:-}}"
    if [[ -z "$project_root" ]]; then
        project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    fi
    local script
    script="$(_resolve_platform_agent_script "$project_root")" || return 0
    if [[ ! -f "$script" ]]; then
        return 0
    fi

    if [[ "${EASYAIOT_SKIP_PLATFORM_AGENT_SYNC:-}" == "1" ]]; then
        return 0
    fi

    # mini 等形态不启动 iot-node，bootstrap 接口不可用，跳过 Agent 同步
    if ! _platform_agent_iot_node_enabled "$project_root"; then
        return 0
    fi

    local has_business_stack=false
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx 'iot-node'; then
        has_business_stack=true
    fi
    # IDEA/宿主机直启 Gateway/iot-node 时容器名检测会漏判，改以 Gateway 健康检查为准
    if [[ "$has_business_stack" != "true" ]]; then
        local gw_url="${EASYAIOT_GATEWAY_URL:-http://127.0.0.1:48080}"
        if curl -fsS --connect-timeout 2 "${gw_url}/actuator/health" >/dev/null 2>&1; then
            has_business_stack=true
        fi
    fi
    if [[ "$has_business_stack" != "true" && "${EASYAIOT_FORCE_PLATFORM_AGENT_SYNC:-}" != "1" ]]; then
        return 0
    fi

    local info_fn="${ENSURE_PLATFORM_AGENT_INFO:-echo}"
    local ok_fn="${ENSURE_PLATFORM_AGENT_OK:-echo}"
    local warn_fn="${ENSURE_PLATFORM_AGENT_WARN:-echo}"

    "$info_fn" "同步宿主机控制面 Node Agent 凭据..."
    export AGENT_BOOTSTRAP_WAIT_SECONDS="${AGENT_BOOTSTRAP_WAIT_SECONDS:-180}"
    export AGENT_BOOTSTRAP_RETRY_INTERVAL="${AGENT_BOOTSTRAP_RETRY_INTERVAL:-3}"
    if bash "$script"; then
        "$ok_fn" "控制面 Node Agent 已就绪"
        return 0
    fi
    "$warn_fn" "控制面 Node Agent 未自动同步，请手动执行: bash $script"
    return 1
}
