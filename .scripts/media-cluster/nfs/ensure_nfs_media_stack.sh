#!/usr/bin/env bash
# 确保 NFS 共享媒体栈就绪（单机 = 本机 export + 127.0.0.1 挂载；集群 = 仅客户端挂载远程 export）
# 无 sudo 单机：自动 fallback 到 $HOME/easyaiot/media，本地目录 bind（与 NFS 同契约路径）
# 单机有 sudo 但挂载超时/失败：同样 fallback，避免一键部署卡死
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=resolve_media_root.sh
source "${SCRIPT_DIR}/resolve_media_root.sh"

NFS_SERVER="${NFS_SERVER:-}"
NFS_EXPORT="${NFS_EXPORT:-}"
# soft 选项防止挂载后 I/O 永久阻塞；安装阶段另有 timeout 包裹 mount
NFS_MOUNT_OPTS="${NFS_MOUNT_OPTS:-vers=3,tcp,nolock,_netdev,soft,timeo=50,retrans=2,retry=1}"
NFS_MOUNT_TIMEOUT="${NFS_MOUNT_TIMEOUT:-45}"
NFS_STACK_TIMEOUT="${NFS_STACK_TIMEOUT:-180}"

run_priv() {
    # 仅用 sudo -n，避免 IDEA/无人值守启动时卡在密码提示
    if [ "${EUID:-$(id -u)}" -eq 0 ]; then
        "$@"
    elif can_run_privileged; then
        sudo -n "$@"
    else
        return 1
    fi
}

_run_with_timeout() {
    local secs="$1"
    shift
    if ! command -v timeout >/dev/null 2>&1; then
        "$@"
        return $?
    fi
    # GNU timeout：优先 --foreground；不支持则普通 timeout
    if timeout --help 2>&1 | grep -q -- '--foreground'; then
        timeout --foreground -k 5 "${secs}" "$@"
    else
        timeout -k 5 "${secs}" "$@"
    fi
}

# timeout 不能直接包 shell 函数；对特权脚本用 sudo/env 可执行形式
_run_priv_script_timeout() {
    local secs="$1"
    shift
    if [ "${EUID:-$(id -u)}" -eq 0 ]; then
        _run_with_timeout "$secs" env "$@"
    elif can_run_privileged; then
        _run_with_timeout "$secs" sudo -n env "$@"
    else
        return 1
    fi
}

_nfs_local_ips() {
    hostname -I 2>/dev/null | tr ' ' '\n' | grep -v '^$' || true
}

_is_local_nfs_server() {
    local server="$1"
    server="$(echo "$server" | tr -d '[:space:]')"
    [ -z "$server" ] && return 0
    case "$server" in
        127.0.0.1|localhost|::1) return 0 ;;
    esac
    _nfs_local_ips | grep -Fxq "$server"
}

# 用 findmnt/mountinfo 判断挂载，避免 mountpoint/stat 在僵死 NFS 上卡死
_is_mountpoint_safe() {
    local path="$1"
    if command -v findmnt >/dev/null 2>&1; then
        [ "$(findmnt -n -o TARGET "$path" 2>/dev/null || true)" = "$path" ]
        return $?
    fi
    awk -v p="$path" '$5 == p { found=1 } END { exit found ? 0 : 1 }' /proc/self/mountinfo 2>/dev/null
}

_nfs_mount_source_ok() {
    local server="$1"
    local export_path="$2"
    _is_mountpoint_safe "${MOUNT_ROOT}" || return 1
    local current
    current="$(findmnt -n -o SOURCE "${MOUNT_ROOT}" 2>/dev/null || true)"
    [ -n "$current" ] || return 1
    case "$current" in
        "${server}:${export_path}"|*":${export_path}") return 0 ;;
    esac
    return 1
}

_ensure_subdirs() {
    mkdir -p \
        "${MOUNT_ROOT}/alert_images" \
        "${MOUNT_ROOT}/playbacks/live" \
        "${MOUNT_ROOT}/playbacks/ai" \
        "${MOUNT_ROOT}/playbacks/gb28181" \
        "${MOUNT_ROOT}/snaps" \
        "${MOUNT_ROOT}/logs" 2>/dev/null || true
}

_ensure_local_media_permissions() {
    _ensure_subdirs
    chmod 777 "${MOUNT_ROOT}" "${MOUNT_ROOT}/playbacks" 2>/dev/null || true
}

_emit_media_root_final() {
    export EASYAIOT_MEDIA_ROOT="${MOUNT_ROOT}"
    echo "MEDIA_ROOT_FINAL=${MOUNT_ROOT}"
}

_local_bind_fallback() {
    local reason="${1:-无 sudo / NFS 不可用}"
    # 若仍指向可能僵死的 NFS 挂载点，改用家目录，避免后续 mkdir/touch 卡死
    if _is_mountpoint_safe "${MOUNT_ROOT}" 2>/dev/null; then
        local fstype
        fstype="$(findmnt -n -o FSTYPE "${MOUNT_ROOT}" 2>/dev/null || true)"
        if [[ "$fstype" == nfs* ]]; then
            MOUNT_ROOT="$(easyaiot_home_media_root)"
            export MOUNT_ROOT
        fi
    elif [[ "${MOUNT_ROOT}" == /mnt/* ]] || [[ "${MOUNT_ROOT}" == /tmp/easyaiot-nfs-mount* ]]; then
        # 标准挂载点但未就绪：fallback 到可写家目录
        if ! mkdir -p "${MOUNT_ROOT}" 2>/dev/null || [ ! -w "${MOUNT_ROOT}" ]; then
            MOUNT_ROOT="$(easyaiot_home_media_root)"
            export MOUNT_ROOT
        fi
    fi
    echo "LOCAL_BIND_FALLBACK mount=${MOUNT_ROOT} (${reason})"
    mkdir -p "${MOUNT_ROOT}"
    _ensure_local_media_permissions
    echo "提示: 单机多进程/容器仍通过 compose 绑定同一宿主机目录；集群节点请配置 NFS_SERVER 或预先 mount"
    _emit_media_root_final
    echo ENSURE_NFS_MEDIA_STACK_OK
}

_run_health_check() {
    _run_with_timeout 20 env \
        MOUNT_ROOT="$MOUNT_ROOT" \
        NFS_SERVER="${NFS_SERVER:-127.0.0.1}" \
        NFS_EXPORT="${NFS_EXPORT:-$MOUNT_ROOT}" \
        bash "${SCRIPT_DIR}/check_nfs_health.sh" || true
}

ensure_nfs_media_stack() {
    MOUNT_ROOT="$(resolve_easyaiot_media_root)"
    export MOUNT_ROOT

    if [ -z "${NFS_EXPORT}" ]; then
        if [ -n "${NFS_SERVER:-}" ] && ! _is_local_nfs_server "${NFS_SERVER}"; then
            NFS_EXPORT="/mnt/easyaiot-media"
        else
            NFS_EXPORT="${MOUNT_ROOT}"
        fi
    fi
    export NFS_EXPORT

    local install_server=0
    local server="${NFS_SERVER}"

    if _is_local_nfs_server "$server"; then
        install_server=1
        server="127.0.0.1"
    fi

    export NFS_SERVER="$server" NFS_MOUNT_OPTS NFS_MOUNT_TIMEOUT

    if is_local_bind_media_mode; then
        if [ "${EASYAIOT_MEDIA_LOCAL_BIND:-}" = "1" ]; then
            _local_bind_fallback "EASYAIOT_MEDIA_LOCAL_BIND=1：强制本地目录"
        else
            _local_bind_fallback "无 sudo：跳过 NFS，使用本地目录 bind 挂载"
        fi
        return 0
    fi

    if _nfs_mount_source_ok "$server" "$NFS_EXPORT"; then
        echo "NFS_ALREADY_MOUNTED ${server}:${NFS_EXPORT} -> ${MOUNT_ROOT}"
        _ensure_local_media_permissions
        _run_health_check
        _emit_media_root_final
        return 0
    fi

    local alt candidate
    for alt in $(_easyaiot_media_root_candidates); do
        [ "$alt" = "$MOUNT_ROOT" ] && continue
        if _is_mountpoint_safe "$alt" 2>/dev/null; then
            candidate="$(findmnt -n -o SOURCE "$alt" 2>/dev/null || true)"
            if [ -n "$candidate" ] && [[ "$candidate" == *":${NFS_EXPORT}" || "$candidate" == "${server}:${NFS_EXPORT}" ]]; then
                echo "NFS_REUSE_MOUNT ${alt} (${candidate}) — 请设置 EASYAIOT_MEDIA_ROOT=${alt}"
                export MOUNT_ROOT="$alt"
                _ensure_local_media_permissions
                _run_health_check
                _emit_media_root_final
                return 0
            fi
        fi
    done

    if [ "$install_server" -eq 1 ]; then
        echo "NFS_LOCAL_MODE install_server=1 mount=${MOUNT_ROOT} export=${NFS_EXPORT}"
        if ! _run_priv_script_timeout "${NFS_STACK_TIMEOUT}" \
            MOUNT_ROOT="$MOUNT_ROOT" \
            NFS_EXPORT="$NFS_EXPORT" \
            NFS_SERVER_READY_TIMEOUT="${NFS_SERVER_READY_TIMEOUT:-30}" \
            bash "${SCRIPT_DIR}/install_nfs_server.sh"; then
            _local_bind_fallback "本机 NFS server 安装/启动失败或超时，回退本地目录"
            return 0
        fi
    else
        echo "NFS_CLUSTER_MODE server=${server} export=${NFS_EXPORT} mount=${MOUNT_ROOT}"
        if ! can_run_privileged; then
            echo "错误: 集群 NFS 客户端挂载需要 sudo（NFS_SERVER=${server}）。" >&2
            echo "  请管理员预先执行 mount，或 export EASYAIOT_MEDIA_ROOT 指向已挂载目录。" >&2
            return 1
        fi
    fi

    echo "NFS_CLIENT_MOUNT begin timeout=${NFS_MOUNT_TIMEOUT}s stack_timeout=${NFS_STACK_TIMEOUT}s"
    if ! _run_priv_script_timeout "${NFS_STACK_TIMEOUT}" \
        MOUNT_ROOT="$MOUNT_ROOT" \
        NFS_SERVER="$server" \
        NFS_EXPORT="$NFS_EXPORT" \
        NFS_MOUNT_OPTS="$NFS_MOUNT_OPTS" \
        NFS_MOUNT_TIMEOUT="$NFS_MOUNT_TIMEOUT" \
        NFS_PROBE_TIMEOUT="${NFS_PROBE_TIMEOUT:-8}" \
        bash "${SCRIPT_DIR}/install_nfs_client.sh"; then
        if [ "$install_server" -eq 1 ]; then
            _local_bind_fallback "本机 NFS 客户端挂载失败/超时，回退本地目录（部署可继续）"
            return 0
        fi
        echo "NFS_CLIENT_MOUNT_FAILED" >&2
        echo "  已超时或失败，不会无限等待。可检查: NFS_SERVER=${server} NFS_EXPORT=${NFS_EXPORT}" >&2
        echo "  或设置 EASYAIOT_MEDIA_LOCAL_BIND=1 强制本地目录。" >&2
        return 1
    fi

    _ensure_local_media_permissions
    _run_health_check
    _emit_media_root_final
    echo ENSURE_NFS_MEDIA_STACK_OK
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    ensure_nfs_media_stack "$@"
fi
