#!/usr/bin/env bash
# 确保 NFS 共享媒体栈就绪（单机 = 本机 export + 127.0.0.1 挂载；集群 = 仅客户端挂载远程 export）
# 无 sudo 单机：自动 fallback 到 $HOME/easyaiot/media，本地目录 bind（与 NFS 同契约路径）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=resolve_media_root.sh
source "${SCRIPT_DIR}/resolve_media_root.sh"

NFS_SERVER="${NFS_SERVER:-}"
NFS_EXPORT="${NFS_EXPORT:-}"
NFS_MOUNT_OPTS="${NFS_MOUNT_OPTS:-vers=3,tcp,nolock,_netdev}"

run_priv() {
    if [ "${EUID:-$(id -u)}" -eq 0 ]; then
        "$@"
    elif command -v sudo >/dev/null 2>&1; then
        sudo "$@"
    else
        "$@"
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

_nfs_mount_source_ok() {
    local server="$1"
    local export_path="$2"
    mountpoint -q "${MOUNT_ROOT}" 2>/dev/null || return 1
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

_local_bind_fallback() {
    echo "LOCAL_BIND_FALLBACK mount=${MOUNT_ROOT} (无 sudo：跳过 NFS，使用本地目录 bind 挂载)"
    mkdir -p "${MOUNT_ROOT}"
    _ensure_local_media_permissions
    echo "提示: 单机多进程/容器仍通过 compose 绑定同一宿主机目录；集群节点请配置 NFS_SERVER 或预先 mount"
    echo ENSURE_NFS_MEDIA_STACK_OK
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

    export NFS_SERVER="$server" NFS_MOUNT_OPTS

    if is_local_bind_media_mode; then
        _local_bind_fallback
        return 0
    fi

    if _nfs_mount_source_ok "$server" "$NFS_EXPORT"; then
        echo "NFS_ALREADY_MOUNTED ${server}:${NFS_EXPORT} -> ${MOUNT_ROOT}"
        _ensure_local_media_permissions
        bash "${SCRIPT_DIR}/check_nfs_health.sh" || true
        return 0
    fi

    local alt candidate
    for alt in $(_easyaiot_media_root_candidates); do
        [ "$alt" = "$MOUNT_ROOT" ] && continue
        if mountpoint -q "$alt" 2>/dev/null; then
            candidate="$(findmnt -n -o SOURCE "$alt" 2>/dev/null || true)"
            if [ -n "$candidate" ] && [[ "$candidate" == *":${NFS_EXPORT}" || "$candidate" == "${server}:${NFS_EXPORT}" ]]; then
                echo "NFS_REUSE_MOUNT ${alt} (${candidate}) — 请设置 EASYAIOT_MEDIA_ROOT=${alt}"
                export MOUNT_ROOT="$alt"
                _ensure_local_media_permissions
                bash "${SCRIPT_DIR}/check_nfs_health.sh" || true
                return 0
            fi
        fi
    done

    if [ "$install_server" -eq 1 ]; then
        echo "NFS_LOCAL_MODE install_server=1 mount=${MOUNT_ROOT} export=${NFS_EXPORT}"
        if ! run_priv env MOUNT_ROOT="$MOUNT_ROOT" NFS_EXPORT="$NFS_EXPORT" \
            bash "${SCRIPT_DIR}/install_nfs_server.sh"; then
            if ! can_run_privileged; then
                _local_bind_fallback
                return 0
            fi
            echo "NFS_SERVER_INSTALL_FAILED" >&2
            return 1
        fi
    else
        echo "NFS_CLUSTER_MODE server=${server} export=${NFS_EXPORT} mount=${MOUNT_ROOT}"
        if ! can_run_privileged; then
            echo "错误: 集群 NFS 客户端挂载需要 sudo（NFS_SERVER=${server}）。" >&2
            echo "  请管理员预先执行 mount，或 export EASYAIOT_MEDIA_ROOT 指向已挂载目录。" >&2
            return 1
        fi
    fi

    if ! run_priv env \
        MOUNT_ROOT="$MOUNT_ROOT" \
        NFS_SERVER="$server" \
        NFS_EXPORT="$NFS_EXPORT" \
        NFS_MOUNT_OPTS="$NFS_MOUNT_OPTS" \
        bash "${SCRIPT_DIR}/install_nfs_client.sh"; then
        if [ "$install_server" -eq 1 ] && ! can_run_privileged; then
            _local_bind_fallback
            return 0
        fi
        echo "NFS_CLIENT_MOUNT_FAILED" >&2
        return 1
    fi

    _ensure_local_media_permissions
    bash "${SCRIPT_DIR}/check_nfs_health.sh" || true
    echo ENSURE_NFS_MEDIA_STACK_OK
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    ensure_nfs_media_stack "$@"
fi
