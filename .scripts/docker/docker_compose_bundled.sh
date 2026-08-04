# shellcheck shell=bash
# 项目内置 Docker Compose 离线安装/升级（按宿主机架构选择二进制，无需联网）
# 调用方需提供: check_command, print_info, print_success, print_warning, print_error

COMPOSE_MIN_MAJOR=2
COMPOSE_MIN_MINOR=35
COMPOSE_MIN_PATCH=0
COMPOSE_MIN_VERSION="${COMPOSE_MIN_MAJOR}.${COMPOSE_MIN_MINOR}.${COMPOSE_MIN_PATCH}"

_docker_compose_bundled_self_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 桌面端 COMPILE 包会故意排除 .scripts/docker-compose（仅含 Linux 离线二进制）。
# 目录缺失时不可强制 cd，否则 source 本文件即在 set -e 下直接失败。
COMPOSE_BUNDLED_DIR="${_docker_compose_bundled_self_dir}/../docker-compose"
if [ -d "${COMPOSE_BUNDLED_DIR}" ]; then
    COMPOSE_BUNDLED_DIR="$(cd "${COMPOSE_BUNDLED_DIR}" && pwd)"
fi

# 按 uname -m 解析内置二进制路径
resolve_bundled_compose_binary() {
    local arch src
    arch="$(uname -m 2>/dev/null || echo "")"
    [ -d "${COMPOSE_BUNDLED_DIR}" ] || return 1
    case "$arch" in
        aarch64|arm64)
            src="${COMPOSE_BUNDLED_DIR}/docker-compose-linux-aarch64"
            ;;
        x86_64|amd64)
            src="${COMPOSE_BUNDLED_DIR}/docker-compose-linux-x86_64"
            ;;
        *)
            return 1
            ;;
    esac
    if [ -f "$src" ]; then
        echo "$src"
        return 0
    fi
    return 1
}

bundled_compose_available() {
    resolve_bundled_compose_binary &>/dev/null
}

parse_compose_version() {
    echo "$1" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -n 1
}

compose_version_meets_requirement() {
    local version_string="$1"
    local major minor patch
    [ -n "$version_string" ] || return 1
    major=$(echo "$version_string" | cut -d. -f1)
    minor=$(echo "$version_string" | cut -d. -f2)
    patch=$(echo "$version_string" | cut -d. -f3)
    if [ "$major" -gt "$COMPOSE_MIN_MAJOR" ]; then
        return 0
    fi
    if [ "$major" -eq "$COMPOSE_MIN_MAJOR" ] && [ "$minor" -gt "$COMPOSE_MIN_MINOR" ]; then
        return 0
    fi
    if [ "$major" -eq "$COMPOSE_MIN_MAJOR" ] && [ "$minor" -eq "$COMPOSE_MIN_MINOR" ] && [ "${patch:-0}" -ge "$COMPOSE_MIN_PATCH" ]; then
        return 0
    fi
    return 1
}

get_installed_compose_version() {
    local output=""
    if check_command docker-compose; then
        output=$(docker-compose --version 2>&1)
    elif docker compose version &>/dev/null; then
        output=$(docker compose version 2>&1)
    else
        return 1
    fi
    parse_compose_version "$output"
}

get_bundled_compose_version() {
    local src ver
    src=$(resolve_bundled_compose_binary) || return 1
    chmod +x "$src" 2>/dev/null || true
    ver=$(parse_compose_version "$("$src" version 2>&1)")
    [ -n "$ver" ] && echo "$ver"
}

compose_version_meets_requirement_quiet() {
    local version_string
    version_string=$(get_installed_compose_version) || return 1
    compose_version_meets_requirement "$version_string"
}

# 覆盖安装到 /usr/local/bin 与 docker cli-plugins（支持 docker-compose 与 docker compose）
install_bundled_docker_compose() {
    local src dest_bin dest_plugin bundled_ver
    if [ "${EUID:-$(id -u)}" -ne 0 ]; then
        print_warning "安装/升级 Docker Compose 需要 root 权限"
        return 1
    fi
    src=$(resolve_bundled_compose_binary) || {
        print_error "当前架构 $(uname -m) 无内置 Docker Compose 二进制包"
        return 1
    }
    chmod +x "$src" 2>/dev/null || true
    bundled_ver=$(get_bundled_compose_version 2>/dev/null || echo "未知")

    dest_bin="/usr/local/bin/docker-compose"
    dest_plugin="/usr/local/lib/docker/cli-plugins/docker-compose"

    print_info "使用内置 Docker Compose v${bundled_ver} 离线覆盖安装（架构: $(uname -m)，无需联网）..."
    print_info "  源文件: $src"

    install -m 0755 "$src" "$dest_bin" || { cp -f "$src" "$dest_bin" && chmod 0755 "$dest_bin"; }
    mkdir -p "$(dirname "$dest_plugin")"
    install -m 0755 "$src" "$dest_plugin" || { cp -f "$src" "$dest_plugin" && chmod 0755 "$dest_plugin"; }

    hash -r 2>/dev/null || true
    return 0
}

set_compose_cmd_from_system() {
    COMPOSE_CMD=""
    if docker compose version &>/dev/null; then
        COMPOSE_CMD="docker compose"
    elif check_command docker-compose; then
        COMPOSE_CMD="docker-compose"
    else
        return 1
    fi
    return 0
}

# 检查已安装版本是否符合要求（>= COMPOSE_MIN_VERSION）
check_docker_compose_version() {
    local version_string output
    if check_command docker-compose; then
        output=$(docker-compose --version 2>&1)
    elif docker compose version &>/dev/null; then
        output=$(docker compose version 2>&1)
    else
        return 1
    fi

    version_string=$(parse_compose_version "$output")
    if [ -z "$version_string" ]; then
        print_warning "无法解析 Docker Compose 版本: $output"
        return 1
    fi

    if compose_version_meets_requirement "$version_string"; then
        print_success "Docker Compose 版本符合要求: $version_string"
        return 0
    fi
    print_warning "Docker Compose 版本过低: $version_string，需要 v${COMPOSE_MIN_VERSION}+"
    return 1
}

bundled_compose_manual_hint() {
    local src
    src=$(resolve_bundled_compose_binary 2>/dev/null || echo "<内置二进制>")
    echo "  sudo cp \"${src}\" /usr/local/bin/docker-compose"
    echo "  sudo chmod +x /usr/local/bin/docker-compose"
    echo "  sudo mkdir -p /usr/local/lib/docker/cli-plugins"
    echo "  sudo cp \"${src}\" /usr/local/lib/docker/cli-plugins/docker-compose"
    echo "  sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose"
}
