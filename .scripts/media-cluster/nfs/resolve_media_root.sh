#!/usr/bin/env bash
# 解析 EasyAIoT 媒体根路径（NFS 挂载点或本地 bind 目录）
# 优先级：EASYAIOT_MEDIA_ROOT > 已挂载路径 > 可写 /mnt > $HOME/easyaiot/media
#
# Docker bind 注意：宿主机源路径必须是「真实目录」。若误建成普通文件 / 坏 symlink，
# daemon 会报：error while creating mount source path '...': mkdir ...: file exists

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

_media_run_priv() {
    if [ "${EUID:-$(id -u)}" -eq 0 ]; then
        "$@"
    elif can_run_privileged; then
        sudo -n "$@"
    else
        "$@"
    fi
}

# Snap 版 Docker 对 /mnt 等路径常出现 bind mkdir: file exists，优先家目录
is_snap_confined_docker() {
    local bin root_dir
    bin="$(command -v docker 2>/dev/null || true)"
    [ -z "$bin" ] && return 1
    case "$bin" in
        /snap/*) return 0 ;;
    esac
    if command -v readlink >/dev/null 2>&1; then
        case "$(readlink -f "$bin" 2>/dev/null || true)" in
            /snap/*) return 0 ;;
        esac
    fi
    root_dir="$(docker info 2>/dev/null | awk -F': ' '/Docker Root Dir/{print $2; exit}' || true)"
    case "$root_dir" in
        /var/snap/docker/*) return 0 ;;
    esac
    return 1
}

# 标准候选路径（按优先级）
_easyaiot_media_root_candidates() {
    if ! is_snap_confined_docker; then
        echo /mnt/easyaiot-media
    fi
    echo /tmp/easyaiot-nfs-mount
    echo "$(easyaiot_home_media_root)"
}

# 路径是否可作为 Docker bind 源（必须是目录；挂载点也算目录）
_is_usable_media_bind_dir() {
    local path="$1"
    [ -d "$path" ] || return 1
    # 拒绝指向非目录的 symlink（Docker MkdirAll 同样会失败）
    if [ -L "$path" ]; then
        local target
        target="$(readlink -f "$path" 2>/dev/null || true)"
        [ -n "$target" ] && [ -d "$target" ] || return 1
    fi
    [ -w "$path" ] || return 1
    return 0
}

# 若路径存在但不是目录（普通文件 / 坏链路），挪走后重建目录
_repair_non_dir_media_path() {
    local path="$1"
    [ -e "$path" ] || [ -L "$path" ] || return 0
    if [ -d "$path" ] && ! [ -L "$path" ]; then
        return 0
    fi
    if [ -d "$path" ] && [ -L "$path" ]; then
        # 目录 symlink：若目标仍是目录则可用
        _is_usable_media_bind_dir "$path" && return 0
    fi
    local bak="${path}.notadir.bak.$(date +%s)"
    echo "MEDIA_BIND_REPAIR: ${path} 不是可用目录，移至 ${bak}" >&2
    if ! _media_run_priv mv "$path" "$bak" 2>/dev/null; then
        _media_run_priv rm -f "$path" 2>/dev/null || rm -f "$path" 2>/dev/null || true
    fi
    _media_run_priv mkdir -p "$path" 2>/dev/null || mkdir -p "$path" 2>/dev/null || true
    _is_usable_media_bind_dir "$path"
}

_ensure_media_subdirs() {
    local root="$1"
    mkdir -p \
        "${root}/alert_images" \
        "${root}/playbacks/live" \
        "${root}/playbacks/ai" \
        "${root}/playbacks/gb28181" \
        "${root}/snaps" \
        "${root}/logs" 2>/dev/null || \
    _media_run_priv mkdir -p \
        "${root}/alert_images" \
        "${root}/playbacks/live" \
        "${root}/playbacks/ai" \
        "${root}/playbacks/gb28181" \
        "${root}/snaps" \
        "${root}/logs" 2>/dev/null || true
    chmod 777 "${root}" "${root}/playbacks" 2>/dev/null || \
        _media_run_priv chmod 777 "${root}" "${root}/playbacks" 2>/dev/null || true
}

resolve_easyaiot_media_root() {
    local candidate home_root
    home_root="$(easyaiot_home_media_root)"

    # 显式指定：若已损坏（文件/坏链路）则忽略并继续自动解析
    if [ -n "${EASYAIOT_MEDIA_ROOT:-}" ]; then
        candidate="${EASYAIOT_MEDIA_ROOT}"
        if _is_usable_media_bind_dir "$candidate"; then
            echo "$candidate"
            return
        fi
        if [ -e "$candidate" ] || [ -L "$candidate" ]; then
            if _repair_non_dir_media_path "$candidate" && _is_usable_media_bind_dir "$candidate"; then
                echo "$candidate"
                return
            fi
            echo "MEDIA_BIND_WARN: EASYAIOT_MEDIA_ROOT=${candidate} 不可用，改用自动解析" >&2
        elif mkdir -p "$candidate" 2>/dev/null || _media_run_priv mkdir -p "$candidate" 2>/dev/null; then
            if _is_usable_media_bind_dir "$candidate"; then
                echo "$candidate"
                return
            fi
        fi
    fi

    if [ -n "${MOUNT_ROOT:-}" ] && [ "${MOUNT_ROOT}" != "/mnt/easyaiot-media" ]; then
        if _is_usable_media_bind_dir "${MOUNT_ROOT}" || \
            { mkdir -p "${MOUNT_ROOT}" 2>/dev/null && _is_usable_media_bind_dir "${MOUNT_ROOT}"; }; then
            echo "${MOUNT_ROOT}"
            return
        fi
    fi

    for candidate in $(_easyaiot_media_root_candidates); do
        if mountpoint -q "$candidate" 2>/dev/null && _is_usable_media_bind_dir "$candidate"; then
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

    # /mnt 可写则优先标准路径（Snap Docker 已在 candidates 中跳过）
    if ! is_snap_confined_docker; then
        if [ -e /mnt/easyaiot-media ] || [ -L /mnt/easyaiot-media ]; then
            _repair_non_dir_media_path /mnt/easyaiot-media || true
        fi
        if mkdir -p /mnt/easyaiot-media 2>/dev/null || _media_run_priv mkdir -p /mnt/easyaiot-media 2>/dev/null; then
            if _is_usable_media_bind_dir /mnt/easyaiot-media; then
                echo /mnt/easyaiot-media
                return
            fi
        fi
    fi

    echo "$home_root"
}

# 确保媒体根是 Docker 可 bind 的目录；输出最终路径并 export EASYAIOT_MEDIA_ROOT
# 用法：ensure_easyaiot_media_bind_source [--force-home]
#   --force-home  强制改用 $HOME/easyaiot/media（compose 报 mkdir file exists 时的回退）
ensure_easyaiot_media_bind_source() {
    local force_home=0
    local root
    case "${1:-}" in
        --force-home|force-home|1) force_home=1 ;;
    esac

    if [ "$force_home" -eq 1 ]; then
        export EASYAIOT_MEDIA_LOCAL_BIND=1
        unset EASYAIOT_MEDIA_ROOT
        root="$(easyaiot_home_media_root)"
    else
        root="$(resolve_easyaiot_media_root)"
    fi

    if [ -e "$root" ] || [ -L "$root" ]; then
        if ! _is_usable_media_bind_dir "$root"; then
            _repair_non_dir_media_path "$root" || true
        fi
    fi

    if ! mkdir -p "$root" 2>/dev/null && ! _media_run_priv mkdir -p "$root" 2>/dev/null; then
        root="$(easyaiot_home_media_root)"
        mkdir -p "$root" 2>/dev/null || true
    fi

    if ! _is_usable_media_bind_dir "$root"; then
        local alt
        alt="$(easyaiot_home_media_root)"
        if [ "$root" != "$alt" ]; then
            echo "MEDIA_BIND_FALLBACK: ${root} 不可写/不是目录 → ${alt}" >&2
            root="$alt"
            mkdir -p "$root" 2>/dev/null || true
        fi
    fi

    _ensure_media_subdirs "$root"
    export EASYAIOT_MEDIA_ROOT="$root"
    export MOUNT_ROOT="$root"
    echo "$root"
}

# 判断 compose/daemon 日志是否为媒体 bind 源 mkdir file exists
is_media_bind_source_mkdir_error() {
    local text="${1:-}"
    echo "$text" | grep -Eqi 'creating mount source path.*(easyaiot-media|easyaiot/media|easyaiot/data|easyaiot-nfs-mount).*file exists' \
        || echo "$text" | grep -Eqi "mkdir .*(easyaiot-media|easyaiot/media).*file exists"
}

# 本地 bind 模式：无 sudo 且单机，不跑 NFS server/client，仅建目录供 compose bind
is_local_bind_media_mode() {
    [ "${EASYAIOT_MEDIA_LOCAL_BIND:-}" = "1" ] && return 0
    [ "${EASYAIOT_MEDIA_LOCAL_BIND:-}" = "0" ] && return 1
    # Snap Docker：默认本地 bind，避免 /mnt 上的 daemon mkdir 冲突
    if is_snap_confined_docker && [ -z "${NFS_SERVER:-}" ]; then
        return 0
    fi
    # 未指定 NFS_SERVER 且无法特权挂载 → 本地目录
    if [ -n "${NFS_SERVER:-}" ]; then
        return 1
    fi
    if can_run_privileged; then
        return 1
    fi
    return 0
}
