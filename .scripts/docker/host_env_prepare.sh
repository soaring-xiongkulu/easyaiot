#!/bin/bash
# EasyAIoT 部署前主机环境检查与自动补齐
# 供 install_linux.sh / install_linux_arm.sh / install_linux_kylin.sh /
#    install_business_linux.sh / install_desktop_common.sh source。
# 调用方需已提供: print_info/print_success/print_warning/print_error、
#   check_command、LOG_FILE（可选）、SCRIPT_DIR、PROJECT_ROOT（可选）
#
# shellcheck shell=bash

[[ -n "${HOST_ENV_PREPARE_LOADED:-}" ]] && return 0
HOST_ENV_PREPARE_LOADED=1

# 将诊断信息同时打到终端与 LOG_FILE
_host_env_log() {
    local level="$1" msg="$2"
    case "$level" in
        info) print_info "$msg" ;;
        ok) print_success "$msg" ;;
        warn) print_warning "$msg" ;;
        error) print_error "$msg" ;;
        *) echo "$msg" ;;
    esac
}

# 磁盘可用空间（GiB），失败返回空
_host_env_free_gib() {
    local path="${1:-/}"
    df -BG "$path" 2>/dev/null | awk 'NR==2 {gsub(/G/,"",$4); print $4}'
}

# 环境检查失败时的详细诊断
host_env_dump_failure() {
    local context="${1:-prepare}"
    echo ""
    _host_env_log error "========================================"
    _host_env_log error "  主机环境检查失败 — 详细诊断 (${context})"
    _host_env_log error "========================================"
    _host_env_log error "时间: $(date '+%Y-%m-%d %H:%M:%S')"
    _host_env_log error "系统: $(uname -s) $(uname -m) $(uname -r 2>/dev/null || true)"
    if [ -f /etc/os-release ]; then
        # shellcheck disable=SC1091
        . /etc/os-release
        _host_env_log error "发行版: ${PRETTY_NAME:-$ID $VERSION_ID}"
    fi
    _host_env_log error "用户: $(id -un 2>/dev/null || echo ?) (uid=$(id -u)) EUID=${EUID:-?}"
    _host_env_log error "PATH: ${PATH:-}"

    if command -v docker >/dev/null 2>&1; then
        _host_env_log error "docker: $(command -v docker)"
        _host_env_log error "docker version:"
        while IFS= read -r line; do
            _host_env_log error "  ${line}"
        done < <(docker version 2>&1 | head -n 40 || true)
        _host_env_log error "docker info (摘要):"
        while IFS= read -r line; do
            _host_env_log error "  ${line}"
        done < <(docker info 2>&1 | head -n 50 || true)
    else
        _host_env_log error "docker: 未安装或不在 PATH"
    fi

    if docker compose version >/dev/null 2>&1; then
        _host_env_log error "compose: $(docker compose version 2>&1 | head -1)"
    elif command -v docker-compose >/dev/null 2>&1; then
        _host_env_log error "compose: $(docker-compose --version 2>&1 | head -1)"
    else
        _host_env_log error "compose: 未检测到"
    fi

    local free_root free_var
    free_root=$(_host_env_free_gib /)
    free_var=$(_host_env_free_gib /var)
    _host_env_log error "磁盘可用: /=${free_root:-?}GiB  /var=${free_var:-?}GiB"

    if [ -n "${LOG_FILE:-}" ] && [ -f "$LOG_FILE" ]; then
        _host_env_log error "完整日志: ${LOG_FILE}"
        _host_env_log error "日志末尾:"
        while IFS= read -r line; do
            _host_env_log error "  ${line}"
        done < <(tail -n 60 "$LOG_FILE" 2>/dev/null || true)
    fi
    echo ""
}

# 非交互判定
_host_env_noninteractive() {
    [ "${EASYAIOT_NONINTERACTIVE:-0}" = "1" ] && return 0
    [ ! -t 0 ] && return 0
    return 1
}

# 尝试自动安装 Docker（Linux；桌面端不走此路径）
host_env_auto_install_docker() {
    if [ "$(uname -s)" != "Linux" ]; then
        _host_env_log warn "非 Linux，跳过 Docker 自动安装（请安装 Docker Desktop）"
        return 1
    fi
    if [ "${EUID:-$(id -u)}" -ne 0 ]; then
        _host_env_log error "自动安装 Docker 需要 root：请使用 sudo 重试，或手动安装后继续"
        _host_env_log error "  curl -fsSL https://get.docker.com | sudo sh"
        _host_env_log error "  sudo usermod -aG docker \"\$USER\" && newgrp docker"
        return 1
    fi

    _host_env_log info "开始自动安装 Docker..."
    local install_log="${LOG_FILE:-/tmp/easyaiot_docker_install_$$.log}"
    {
        echo "==== host_env_auto_install_docker $(date '+%Y-%m-%d %H:%M:%S') ===="
    } >> "$install_log" 2>/dev/null || true

    local rc=0
    if [ -f /etc/os-release ]; then
        # shellcheck disable=SC1091
        . /etc/os-release
        case "${ID:-}" in
            ubuntu|debian)
                _host_env_log info "检测到 ${ID}，使用 get.docker.com 官方脚本安装..."
                if ! curl -fsSL https://get.docker.com 2>>"$install_log" | sh 2>>"$install_log"; then
                    rc=1
                fi
                ;;
            centos|rhel|rocky|almalinux|anolis|openEuler|kylin|uos)
                _host_env_log info "检测到 ${ID}，使用 get.docker.com 官方脚本安装..."
                if ! curl -fsSL https://get.docker.com 2>>"$install_log" | sh 2>>"$install_log"; then
                    rc=1
                fi
                ;;
            *)
                _host_env_log info "发行版 ${ID:-unknown}，尝试 get.docker.com..."
                if ! curl -fsSL https://get.docker.com 2>>"$install_log" | sh 2>>"$install_log"; then
                    rc=1
                fi
                ;;
        esac
    else
        _host_env_log error "无法识别操作系统（缺少 /etc/os-release）"
        return 1
    fi

    if [ "$rc" -ne 0 ]; then
        _host_env_log error "Docker 自动安装失败，安装日志末尾:"
        while IFS= read -r line; do
            _host_env_log error "  ${line}"
        done < <(tail -n 40 "$install_log" 2>/dev/null || true)
        return 1
    fi

    systemctl enable docker >/dev/null 2>&1 || true
    systemctl start docker >/dev/null 2>&1 || true
    if ! command -v docker >/dev/null 2>&1; then
        _host_env_log error "安装脚本已执行，但 docker 命令仍不可用"
        return 1
    fi
    _host_env_log ok "Docker 已安装: $(docker --version 2>/dev/null || echo ok)"
    return 0
}

# 确保 Docker 可用（缺失则自动装）
host_env_ensure_docker() {
    if command -v docker >/dev/null 2>&1; then
        if docker info >/dev/null 2>&1; then
            _host_env_log ok "Docker 可用: $(docker --version 2>/dev/null || true)"
            return 0
        fi
        _host_env_log warn "已安装 docker 但无法连接 daemon，尝试启动..."
        if [ "${EUID:-$(id -u)}" -eq 0 ]; then
            systemctl start docker >/dev/null 2>&1 || service docker start >/dev/null 2>&1 || true
        fi
        if docker info >/dev/null 2>&1; then
            _host_env_log ok "Docker daemon 已就绪"
            return 0
        fi
        _host_env_log error "Docker daemon 不可用"
        docker info 2>&1 | while IFS= read -r line; do _host_env_log error "  ${line}"; done || true
        return 1
    fi

    _host_env_log warn "未检测到 Docker，尝试自动安装..."
    if _host_env_noninteractive || [ "${EASYAIOT_AUTO_INSTALL_DEPS:-1}" = "1" ]; then
        host_env_auto_install_docker || return 1
    else
        echo -ne "${YELLOW:-[提示]}${NC:-} 是否自动安装 Docker？(Y/n): "
        local resp=""
        read -r resp || resp="Y"
        case "${resp:-Y}" in
            n|N|no|NO) _host_env_log error "用户取消安装 Docker"; return 1 ;;
            *) host_env_auto_install_docker || return 1 ;;
        esac
    fi

    if ! docker info >/dev/null 2>&1; then
        _host_env_log error "Docker 安装后仍无法连接 daemon"
        return 1
    fi
    return 0
}

# 确保 Docker Compose 可用（优先内置离线包）
host_env_ensure_compose() {
    if docker compose version >/dev/null 2>&1 || command -v docker-compose >/dev/null 2>&1; then
        if declare -F compose_version_meets_requirement_quiet >/dev/null 2>&1; then
            if compose_version_meets_requirement_quiet; then
                _host_env_log ok "Docker Compose 可用"
                return 0
            fi
            _host_env_log warn "Docker Compose 版本过低，尝试用内置包升级..."
        else
            _host_env_log ok "Docker Compose 可用"
            return 0
        fi
    else
        _host_env_log warn "未检测到 Docker Compose，尝试安装..."
    fi

    if declare -F bundled_compose_available >/dev/null 2>&1 && bundled_compose_available; then
        if declare -F install_bundled_compose >/dev/null 2>&1; then
            if [ "${EUID:-$(id -u)}" -ne 0 ]; then
                _host_env_log error "安装/升级 Docker Compose 需要 root（sudo）"
                if declare -F bundled_compose_manual_hint >/dev/null 2>&1; then
                    bundled_compose_manual_hint
                fi
                return 1
            fi
            if install_bundled_compose; then
                _host_env_log ok "Docker Compose 已用内置包安装/升级"
                return 0
            fi
        fi
    fi

    # 回退：docker compose 插件可能随 docker 引擎已有
    if docker compose version >/dev/null 2>&1; then
        _host_env_log ok "Docker Compose 插件可用"
        return 0
    fi
    _host_env_log error "Docker Compose 不可用且无法自动安装"
    return 1
}

# 磁盘空间粗检（默认要求根分区 ≥ 10GiB 可用）
host_env_ensure_disk() {
    local min_gib="${EASYAIOT_MIN_FREE_GIB:-10}"
    local free
    free=$(_host_env_free_gib /)
    if [ -z "$free" ]; then
        _host_env_log warn "无法探测磁盘可用空间，跳过检查"
        return 0
    fi
    if [ "$free" -lt "$min_gib" ] 2>/dev/null; then
        _host_env_log error "根分区可用空间不足: ${free}GiB < ${min_gib}GiB"
        _host_env_log error "请清理磁盘或调整 EASYAIOT_MIN_FREE_GIB 后重试"
        df -h / /var 2>/dev/null | while IFS= read -r line; do _host_env_log error "  ${line}"; done || true
        return 1
    fi
    _host_env_log ok "磁盘空间充足: / 可用 ${free}GiB"
    return 0
}

# 模块失败时打印日志尾部（供 install 循环调用）
host_env_dump_module_failure() {
    local module_name="${1:-模块}"
    local log="${2:-${LOG_FILE:-}}"
    _host_env_log error "${module_name} 部署失败，已跳过并继续后续模块"
    if [ -n "$log" ] && [ -f "$log" ]; then
        _host_env_log error "日志文件: ${log}"
        _host_env_log error "日志末尾 (tail -40):"
        while IFS= read -r line; do
            _host_env_log error "  ${line}"
        done < <(tail -n 40 "$log" 2>/dev/null || true)
    fi
}

# 主入口：部署前环境检查 + 自动补齐
# 返回 0=就绪；1=失败（已输出详细诊断）
prepare_host_environment() {
    local context="${1:-deploy}"
    if [ "${_HOST_ENV_PREPARED:-0}" = "1" ]; then
        return 0
    fi

    if declare -F print_section >/dev/null 2>&1; then
        print_section "部署前环境检查与自动补齐"
    else
        echo ""
        _host_env_log info "======== 部署前环境检查与自动补齐 ========"
    fi

    local fail=0

    # 基础工具
    local tool
    for tool in curl tar; do
        if command -v "$tool" >/dev/null 2>&1; then
            _host_env_log ok "工具就绪: ${tool}"
        else
            _host_env_log warn "缺少工具: ${tool}（部分自动安装步骤可能受影响）"
        fi
    done

    host_env_ensure_disk || fail=1

    if [ "$(uname -s)" = "Linux" ]; then
        host_env_ensure_docker || fail=1
        # compose 依赖 docker；docker 失败时仍尝试报告 compose 状态
        if [ "$fail" -eq 0 ]; then
            host_env_ensure_compose || fail=1
        else
            host_env_ensure_compose || true
        fi
    else
        # 桌面端：仅检测，自动安装由各 OS bootstrap 负责
        if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
            _host_env_log ok "Docker Desktop 可用"
        else
            _host_env_log error "Docker Desktop 未运行或未安装"
            fail=1
        fi
        if docker compose version >/dev/null 2>&1 || command -v docker-compose >/dev/null 2>&1; then
            _host_env_log ok "Docker Compose 可用"
        else
            _host_env_log error "Docker Compose 不可用"
            fail=1
        fi
    fi

    if [ "$fail" -ne 0 ]; then
        host_env_dump_failure "$context"
        return 1
    fi

    _host_env_log ok "主机环境检查通过，开始后续部署"
    _HOST_ENV_PREPARED=1
    export _HOST_ENV_PREPARED
    return 0
}
