#!/usr/bin/env bash
# 解析 EasyAIoT 媒体根路径（NFS 挂载点或本地 bind 目录）
# 优先级：EASYAIOT_MEDIA_ROOT > 已挂载路径 > 可写 /mnt > $HOME/easyaiot/media

easyaiot_home_media_root() {
    echo "${HOME}/easyaiot/media"
}

# 是否能在无交互 sudo 或 root 下执行特权操作（安装 NFS / mount）
can_run_privileged() {
    if [ "${EUID:-$(id -u)}" -eq 0 ]; then
        return 0
    fi
    if command -v sudo >/dev/null 2>&1; then
        sudo -n true 2>/dev/null && return 0
    fi
    return 1
}

# 标准候选路径（按优先级）
_easyaiot_media_root_candidates() {
    echo /mnt/easyaiot-media
    echo /tmp/easyaiot-nfs-mount
    echo "$(easyaiot_home_media_root)"
}

resolve_easyaiot_media_root() {
    if [ -n "${EASYAIOT_MEDIA_ROOT:-}" ]; then
        echo "${EASYAIOT_MEDIA_ROOT}"
        return
    fi
    if [ -n "${MOUNT_ROOT:-}" ] && [ "${MOUNT_ROOT}" != "/mnt/easyaiot-media" ]; then
        echo "${MOUNT_ROOT}"
        return
    fi

    local candidate home_root
    home_root="$(easyaiot_home_media_root)"

    for candidate in $(_easyaiot_media_root_candidates); do
        if mountpoint -q "$candidate" 2>/dev/null; then
            echo "$candidate"
            return
        fi
    done

    # 已有本地目录（历史 ~/easyaiot/data 迁移或 prior fallback）
    for candidate in "$home_root" "${HOME}/easyaiot/data"; do
        if [ -d "${candidate}/playbacks" ] || [ -d "${candidate}/alert_images" ]; then
            echo "$candidate"
            return
        fi
    done

    # /mnt 可写则优先标准路径
    if mkdir -p /mnt/easyaiot-media 2>/dev/null && [ -w /mnt/easyaiot-media ]; then
        echo /mnt/easyaiot-media
        return
    fi

    echo "$home_root"
}

# 本地 bind 模式：无 sudo 且单机，不跑 NFS server/client，仅建目录供 compose bind
is_local_bind_media_mode() {
    [ "${EASYAIOT_MEDIA_LOCAL_BIND:-}" = "1" ] && return 0
    [ "${EASYAIOT_MEDIA_LOCAL_BIND:-}" = "0" ] && return 1
    # 未指定 NFS_SERVER 且无法特权挂载 → 本地目录
    if [ -n "${NFS_SERVER:-}" ]; then
        return 1
    fi
    if can_run_privileged; then
        return 1
    fi
    return 0
}
