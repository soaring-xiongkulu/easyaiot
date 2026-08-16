#!/usr/bin/env bash
# update 流程共用：兼容「无 git 命令」的安装包 / 精简环境
# 由各模块 install_linux.sh source（需已定义 print_* 或可无）

# shellcheck disable=SC2034
[[ -n "${MODULE_UPDATE_HELPERS_LOADED:-}" ]] && return 0
MODULE_UPDATE_HELPERS_LOADED=1

easyaiot_have_git() {
    command -v git >/dev/null 2>&1
}

_easyaiot_update_msg() {
    local level="$1"
    shift
    if declare -F "print_${level}" >/dev/null 2>&1; then
        "print_${level}" "$*"
    else
        echo "[update][$level] $*" >&2
    fi
}

# 是否应跳过 git pull、仅用本地/预构建镜像 recreate。
# 条件：镜像存在，且 (EASYAIOT_SKIP_BUILD=1 或 系统无 git)
# 返回 0=应 recreate；1=继续走 git/构建逻辑
# 用法: easyaiot_update_should_recreate_only <image[:tag]>
easyaiot_update_should_recreate_only() {
    local image="${1:-}"
    [ -n "$image" ] || return 1
    docker image inspect "$image" >/dev/null 2>&1 || return 1

    if [ "${EASYAIOT_SKIP_BUILD:-0}" = "1" ]; then
        _easyaiot_update_msg success "预构建镜像已就绪（EASYAIOT_SKIP_BUILD=1），跳过 git pull 与构建，仅 recreate"
        return 0
    fi
    if ! easyaiot_have_git; then
        _easyaiot_update_msg warning "未检测到 git 命令，跳过代码拉取，使用本地镜像 recreate"
        _easyaiot_update_msg info "如需最新版本：一键 update 选「拉取预构建镜像」，或安装 git 后本地重建"
        return 0
    fi
    return 1
}

# 安全 git pull；无 git 时跳过（返回 0）。$1=strict 时 pull 失败返回 1
easyaiot_git_pull_ff_only() {
    local strict="${1:-}"
    if ! easyaiot_have_git; then
        _easyaiot_update_msg warning "未安装 git，跳过 git pull"
        return 0
    fi
    if git pull --ff-only; then
        return 0
    fi
    if [ "$strict" = "strict" ]; then
        _easyaiot_update_msg error "Git pull 失败，已停止更新"
        return 1
    fi
    _easyaiot_update_msg warning "Git pull 失败，继续使用当前代码"
    return 0
}

# update 拉预构建镜像时也会跳过模块内 git pull；在此单独同步仓库脚本
# （mqtt-demo vendor、install 脚本等），否则镜像更新了但宿主机 .scripts 仍是旧版。
# 关闭：EASYAIOT_SKIP_GIT_PULL=1
easyaiot_update_sync_project_scripts() {
    local root="${1:-}"
    if [ "${EASYAIOT_SKIP_GIT_PULL:-0}" = "1" ]; then
        return 0
    fi
    if [ -z "$root" ] || [ ! -d "$root/.git" ]; then
        return 0
    fi
    if ! easyaiot_have_git; then
        return 0
    fi
    _easyaiot_update_msg info "同步仓库脚本（与镜像更新独立，含 mqtt-demo 等）..."
    if git -C "$root" pull --ff-only; then
        _easyaiot_update_msg success "仓库脚本已同步到 $(git -C "$root" rev-parse --short HEAD 2>/dev/null || echo latest)"
        return 0
    fi
    _easyaiot_update_msg warning "git pull 失败，继续使用当前目录脚本"
    return 0
}

easyaiot_git_rev_parse_head() {
    if easyaiot_have_git; then
        git rev-parse HEAD 2>/dev/null || echo ""
    else
        echo ""
    fi
}

# 无 git 时视为「工作区干净」（无法判断脏文件）
easyaiot_git_worktree_clean() {
    if ! easyaiot_have_git; then
        return 0
    fi
    git diff --quiet HEAD -- . 2>/dev/null
}
