#!/bin/bash

# ============================================
# EasyAIoT 统一安装脚本 (CentOS / RHEL 系 · ARM)
# ============================================
# 针对 CentOS 7/8/Stream、Rocky、Alma、RHEL 等 aarch64/arm64 的一键部署入口：
#   1) 检测发行版 / ARM 架构 / SELinux / firewalld
#   2) 自动安装或升级 Docker CE（解决 CentOS 7 自带 docker 1.13 无法拉新镜像）
#   3) 配置国内镜像源、放行常用业务端口
#   4) 转交 install_linux_arm.sh 完成 ARM 平台部署（命令与交互菜单完全一致）
#
# 使用方法：
#   sudo ./install_linux_centos_arm.sh              # 交互引导
#   sudo ./install_linux_centos_arm.sh install      # 首次安装
#   sudo ./install_linux_centos_arm.sh start|stop|restart|status|verify|update
#   ./install_linux_centos_arm.sh check|profile|help
#
# CentOS ARM 专用选项（须写在子命令之前）：
#   -f, --force              跳过 CentOS/RHEL 与 ARM 架构检查
#   --no-upgrade-docker      不自动安装/升级 Docker CE
#   --upgrade-docker-only    仅安装/升级 Docker CE 后退出
#   --no-firewall            不自动放行 firewalld 端口
#   --skip-mirror            跳过 Docker 国内镜像源配置
#
# 示例：
#   sudo ./install_linux_centos_arm.sh --upgrade-docker-only
#   sudo ./install_linux_centos_arm.sh --no-firewall install
#   sudo EASYAIOT_DEPLOY_PROFILE=full ./install_linux_centos_arm.sh install
# ============================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
INSTALL_LINUX_ARM="${SCRIPT_DIR}/install_linux_arm.sh"

FORCE_OS_CHECK=false
SKIP_DOCKER_UPGRADE=false
UPGRADE_DOCKER_ONLY=false
SKIP_FIREWALL=false
SKIP_MIRROR=false
MIN_DOCKER_MAJOR=20
DOCKER_MIRROR="${DOCKER_MIRROR:-https://docker.m.daocloud.io/}"

# 对外常用端口（firewalld 放行；UDP 含媒体相关）
FIREWALL_TCP_PORTS=(
    8888 48080 5000 6000 6100 1984 8554 8555 9010 8002 48096 9200 9300 13338-13437
    8848 9000 9001 5432 6379 1880 1881 1883
    8080 1985 1935 9100
)
FIREWALL_UDP_PORTS=(
    8555 30000-30500 10000-20000
)

print_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

print_section() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
}

show_centos_arm_help() {
    cat <<'EOF'
EasyAIoT 统一安装脚本 (CentOS / RHEL 系 · ARM)

用法:
  sudo ./install_linux_centos_arm.sh [CentOS ARM选项...] [命令] [参数...]

CentOS ARM 专用选项（须写在子命令之前）:
  -h, --help              显示此帮助
  -f, --force             跳过 CentOS/RHEL 与 ARM 架构检查
  --no-upgrade-docker     不自动安装/升级 Docker CE
  --upgrade-docker-only   仅安装/升级 Docker CE 后退出
  --no-firewall           不自动放行 firewalld 端口
  --skip-mirror           跳过 Docker 国内镜像源配置

子命令（与 install_linux_arm.sh 完全一致）:
  install / start / stop / restart / status / logs / build
  build-runtime / pull / clean / clean-build-runtime / update
  verify / check / profile / menu / diagnose / analyze-logs / analyze-disk / help

示例:
  sudo ./install_linux_centos_arm.sh
  sudo ./install_linux_centos_arm.sh install
  sudo ./install_linux_centos_arm.sh --upgrade-docker-only
  sudo EASYAIOT_DEPLOY_PROFILE=edge ./install_linux_centos_arm.sh install
  sudo EASYAIOT_DEPLOY_PROFILE=mini ./install_linux_centos_arm.sh install

说明:
  - 仅面向 aarch64/arm64 上的 CentOS/RHEL 系发行版
  - CentOS 7 会自动卸载系统自带 docker 1.13，并安装 docker-ce 20+
  - CentOS 8+ / Rocky / Alma / RHEL 使用 yum 或 dnf 安装 docker-ce
  - 平台业务部署逻辑委托给 install_linux_arm.sh（ARM 镜像与 Dockerfile）
  - x86_64 CentOS 请使用: install_linux_centos.sh
  - 通用 ARM（非 EL 系）请使用: install_linux_arm.sh
EOF
}

# ---------- 参数解析（仅消费 CentOS ARM 专用选项，其余原样转交） ----------
FORWARD_ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_centos_arm_help
            exit 0
            ;;
        -f|--force)
            FORCE_OS_CHECK=true
            shift
            ;;
        --no-upgrade-docker)
            SKIP_DOCKER_UPGRADE=true
            shift
            ;;
        --upgrade-docker-only)
            UPGRADE_DOCKER_ONLY=true
            shift
            ;;
        --no-firewall)
            SKIP_FIREWALL=true
            shift
            ;;
        --skip-mirror)
            SKIP_MIRROR=true
            shift
            ;;
        --)
            shift
            FORWARD_ARGS+=("$@")
            break
            ;;
        *)
            FORWARD_ARGS+=("$@")
            break
            ;;
    esac
done

# ---------- 发行版 / 架构检测 ----------
detect_el_family() {
    OS_ID=""
    OS_VERSION=""
    OS_LIKE=""
    OS_PRETTY=""
    OS_MAJOR=""

    if [ -f /etc/os-release ]; then
        # shellcheck source=/dev/null
        . /etc/os-release
        OS_ID="${ID:-}"
        OS_VERSION="${VERSION_ID:-}"
        OS_LIKE="${ID_LIKE:-}"
        OS_PRETTY="${PRETTY_NAME:-$OS_ID $OS_VERSION}"
    elif [ -f /etc/redhat-release ]; then
        OS_PRETTY=$(cat /etc/redhat-release)
        if grep -qi "centos" /etc/redhat-release; then
            OS_ID="centos"
        elif grep -qi "red hat\|rhel" /etc/redhat-release; then
            OS_ID="rhel"
        elif grep -qi "rocky" /etc/redhat-release; then
            OS_ID="rocky"
        elif grep -qi "alma" /etc/redhat-release; then
            OS_ID="almalinux"
        else
            OS_ID="rhel"
        fi
        OS_VERSION=$(grep -oE '[0-9]+(\.[0-9]+)?' /etc/redhat-release | head -1 || true)
    fi

    OS_MAJOR="${OS_VERSION%%.*}"
}

is_el_family() {
    case "$OS_ID" in
        centos|rhel|rocky|almalinux|ol|anolis|opencloudos|tencentos|kylin|uos)
            return 0
            ;;
    esac
    echo " ${OS_LIKE} " | grep -qiE '[[:space:]](rhel|centos|fedora)[[:space:]]' && return 0
    return 1
}

is_arm_arch() {
    local arch
    arch=$(uname -m)
    case "$arch" in
        aarch64|arm64|armv7l|armv6l|armhf|armel)
            return 0
            ;;
    esac
    return 1
}

check_centos_arm() {
    detect_el_family

    if [ "$FORCE_OS_CHECK" = true ]; then
        print_warning "已跳过 CentOS/RHEL 与 ARM 架构检查 (--force)"
        return 0
    fi

    print_section "系统环境检查 (CentOS / RHEL · ARM)"

    if ! is_el_family; then
        print_error "当前系统不是 CentOS/RHEL 系 (ID=${OS_ID:-未知})"
        print_info "通用 ARM Linux 请使用: sudo .scripts/docker/install_linux_arm.sh"
        print_info "x86 CentOS/RHEL 请使用: sudo .scripts/docker/install_linux_centos.sh"
        print_info "或加 --force 强制继续: sudo ./install_linux_centos_arm.sh --force $*"
        exit 1
    fi

    print_success "检测到: ${OS_PRETTY:-$OS_ID $OS_VERSION}"

    local arch
    arch=$(uname -m)
    case "$arch" in
        aarch64|arm64)
            print_success "架构: $arch (ARM64)"
            ;;
        armv7l|armv6l|armhf|armel)
            print_warning "架构: $arch（32 位 ARM，可能不完全支持，建议 aarch64）"
            ;;
        x86_64|amd64)
            print_error "当前为 x86_64 架构，本脚本仅用于 CentOS ARM"
            print_info "请改用: sudo .scripts/docker/install_linux_centos.sh"
            exit 1
            ;;
        *)
            print_error "未识别或不支持的架构: $arch（需要 aarch64/arm64）"
            print_info "或加 --force 强制继续"
            exit 1
            ;;
    esac

    if command -v getenforce >/dev/null 2>&1; then
        local selinux_status
        selinux_status=$(getenforce 2>/dev/null || echo "未知")
        print_info "SELinux: $selinux_status"
        if [ "$selinux_status" = "Enforcing" ]; then
            print_warning "SELinux Enforcing 时，若容器挂载目录权限异常，可临时: setenforce 0"
            print_info "或给数据目录打标签: chcon -Rt svirt_sandbox_file_t <data_dir>"
        fi
    fi

    if systemctl is-active firewalld >/dev/null 2>&1; then
        print_info "firewalld 正在运行（安装时将自动放行常用端口，可用 --no-firewall 跳过）"
    fi
}

pkg_mgr() {
    if command -v dnf >/dev/null 2>&1; then
        echo "dnf"
    else
        echo "yum"
    fi
}

# ---------- Docker 版本检测 / 安装 ----------
get_docker_server_version() {
    local ver
    ver=$(docker version 2>/dev/null | awk '
        /^Server:/ { in_server=1; next }
        in_server && /^Version:/ { print $2; exit }
        in_server && /^[A-Z]/ && $1 !~ /^Version:/ { in_server=0 }
    ')
    if [ -n "$ver" ]; then
        echo "$ver"
        return 0
    fi
    docker -v 2>/dev/null | sed -n 's/.*[Vv]ersion \([^, ]*\).*/\1/p' | head -1
}

is_docker_too_old() {
    local ver="${1:-}"
    if [ -z "$ver" ]; then
        return 0
    fi
    local major minor
    major=$(echo "$ver" | cut -d. -f1)
    minor=$(echo "$ver" | cut -d. -f2)
    major=${major:-0}
    minor=${minor:-0}
    if [ "$major" -le 1 ] 2>/dev/null && [ "$minor" -lt 20 ] 2>/dev/null; then
        return 0
    fi
    if [ "$major" -lt "$MIN_DOCKER_MAJOR" ] 2>/dev/null; then
        return 0
    fi
    return 1
}

install_docker_ce_el() {
    local pm
    pm=$(pkg_mgr)
    print_section "安装 / 升级 Docker CE (${OS_ID:-el}${OS_MAJOR} · ARM)"

    if [ "$EUID" -ne 0 ]; then
        print_error "安装 Docker CE 需要 root 权限"
        print_info "请执行: sudo $0 --upgrade-docker-only"
        return 1
    fi

    print_info "卸载可能存在的旧版 docker..."
    $pm remove -y docker \
        docker-client docker-client-latest docker-common \
        docker-latest docker-latest-logrotate docker-logrotate \
        docker-selinux docker-engine-selinux docker-engine \
        2>/dev/null || true

    print_info "安装依赖..."
    $pm install -y yum-utils device-mapper-persistent-data lvm2 2>/dev/null \
        || $pm install -y yum-utils 2>/dev/null \
        || true

    print_info "添加 Docker CE 仓库（华为云镜像优先）..."
    local repo_ok=false
    if yum-config-manager --add-repo https://mirrors.huaweicloud.com/docker-ce/linux/centos/docker-ce.repo 2>/dev/null; then
        repo_ok=true
    elif command -v dnf >/dev/null 2>&1 && dnf config-manager --add-repo https://mirrors.huaweicloud.com/docker-ce/linux/centos/docker-ce.repo 2>/dev/null; then
        repo_ok=true
    fi
    if [ "$repo_ok" != true ]; then
        print_warning "华为云仓库添加失败，尝试官方源..."
        yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo 2>/dev/null \
            || dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo 2>/dev/null \
            || true
    fi

    print_info "安装 docker-ce / cli / containerd / compose-plugin (aarch64)..."
    set +e
    $pm install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    local yum_rc=$?
    set -e
    if [ "$yum_rc" -ne 0 ]; then
        print_warning "带 compose-plugin 安装失败，尝试仅安装 docker-ce..."
        $pm install -y docker-ce docker-ce-cli containerd.io || {
            print_error "Docker CE 安装失败"
            print_info "请确认当前仓库提供 aarch64 包，或手动安装后加 --no-upgrade-docker"
            return 1
        }
    fi

    systemctl daemon-reload
    systemctl enable docker
    systemctl start docker
    sleep 2

    if ! docker info >/dev/null 2>&1; then
        print_error "Docker CE 启动失败，请检查: journalctl -u docker -n 50"
        return 1
    fi

    local new_ver
    new_ver=$(get_docker_server_version)
    print_success "Docker 已就绪: ${new_ver:-$(docker -v)}"

    if is_docker_too_old "$new_ver"; then
        print_error "升级后版本仍过旧: ${new_ver}（需要 ${MIN_DOCKER_MAJOR}+）"
        return 1
    fi
    return 0
}

ensure_modern_docker() {
    if [ "$SKIP_DOCKER_UPGRADE" = true ]; then
        print_warning "已跳过 Docker 自动安装/升级 (--no-upgrade-docker)"
        if ! command -v docker >/dev/null 2>&1; then
            print_error "Docker 未安装"
            exit 1
        fi
        return 0
    fi

    if ! command -v docker >/dev/null 2>&1; then
        print_warning "未检测到 Docker，将自动安装 Docker CE"
        install_docker_ce_el || exit 1
        return 0
    fi

    # 尝试启动
    if ! docker info >/dev/null 2>&1; then
        if [ "$EUID" -eq 0 ]; then
            systemctl start docker 2>/dev/null || true
        fi
    fi

    local ver
    ver=$(get_docker_server_version)
    print_info "当前 Docker 版本: ${ver:-未知}"

    if ! is_docker_too_old "$ver"; then
        print_success "Docker 版本满足要求 (>= ${MIN_DOCKER_MAJOR})"
        return 0
    fi

    print_warning "Docker ${ver:-未知} 过旧（CentOS 7 常见为 1.13），无法拉取 postgres:18 等新镜像"
    print_info "将自动升级为 Docker CE ${MIN_DOCKER_MAJOR}+..."
    install_docker_ce_el || exit 1
}

# ---------- 镜像源 / 防火墙 ----------
configure_docker_mirror_centos() {
    if [ "$SKIP_MIRROR" = true ]; then
        print_info "已跳过 Docker 镜像源配置 (--skip-mirror)"
        return 0
    fi
    if [ "$EUID" -ne 0 ]; then
        print_warning "配置镜像源需要 root，已跳过"
        return 0
    fi

    print_info "配置 Docker 国内镜像源: $DOCKER_MIRROR"
    mkdir -p /etc/docker
    local config_file="/etc/docker/daemon.json"
    local need_restart=false

    if [ ! -f "$config_file" ]; then
        printf '{\n  "registry-mirrors": ["%s"]\n}\n' "$DOCKER_MIRROR" > "$config_file"
        need_restart=true
        print_success "已写入 $config_file"
    elif grep -q 'docker\.m\.daocloud\.io' "$config_file" 2>/dev/null; then
        print_success "Docker 镜像源已配置"
        return 0
    elif command -v python3 >/dev/null 2>&1; then
        local rc=0
        python3 - "$config_file" "$DOCKER_MIRROR" <<'PYEOF' || rc=$?
import json, sys
path, mirror = sys.argv[1], sys.argv[2]
try:
    cfg = json.load(open(path))
except Exception:
    sys.exit(1)
mirrors = cfg.get("registry-mirrors", [])
if not isinstance(mirrors, list):
    mirrors = []
normalized = [m.rstrip("/") for m in mirrors if isinstance(m, str)]
if mirror.rstrip("/") in normalized:
    sys.exit(0)
mirrors.append(mirror)
cfg["registry-mirrors"] = mirrors
json.dump(cfg, open(path, "w"), indent=2, ensure_ascii=False)
sys.exit(3)
PYEOF
        case $rc in
            0) print_success "Docker 镜像源已就绪" ;;
            3) need_restart=true; print_success "Docker 镜像源已更新" ;;
            *) print_warning "无法自动合并 $config_file，请手动添加 registry-mirrors" ;;
        esac
    else
        print_warning "已有 $config_file 且无 python3，跳过自动合并"
        return 0
    fi

    if [ "$need_restart" = true ] && systemctl is-active --quiet docker 2>/dev/null; then
        print_info "重启 Docker 使镜像源生效..."
        systemctl daemon-reload
        systemctl restart docker
        sleep 2
        print_success "Docker 已重启"
    fi
}

configure_firewalld_ports() {
    if [ "$SKIP_FIREWALL" = true ]; then
        print_info "已跳过 firewalld 端口放行 (--no-firewall)"
        return 0
    fi
    if [ "$EUID" -ne 0 ]; then
        print_warning "放行 firewalld 端口需要 root，已跳过"
        return 0
    fi
    if ! systemctl is-active firewalld >/dev/null 2>&1; then
        print_info "firewalld 未运行，跳过端口放行"
        return 0
    fi
    if ! command -v firewall-cmd >/dev/null 2>&1; then
        return 0
    fi

    print_section "配置 firewalld 端口"
    local changed=false
    local p
    for p in "${FIREWALL_TCP_PORTS[@]}"; do
        if firewall-cmd --permanent --add-port="${p}/tcp" >/dev/null 2>&1; then
            changed=true
            print_info "已放行 TCP ${p}"
        fi
    done
    for p in "${FIREWALL_UDP_PORTS[@]}"; do
        if firewall-cmd --permanent --add-port="${p}/udp" >/dev/null 2>&1; then
            changed=true
            print_info "已放行 UDP ${p}"
        fi
    done
    if [ "$changed" = true ]; then
        firewall-cmd --reload >/dev/null 2>&1 || true
        print_success "firewalld 规则已刷新"
    else
        print_info "firewalld 端口规则无变更"
    fi
}

prepare_centos_arm_environment() {
    check_centos_arm
    ensure_modern_docker
    configure_docker_mirror_centos
    configure_firewalld_ports
}

# ---------- 转交 install_linux_arm.sh ----------
delegate_to_install_linux_arm() {
    if [ ! -f "$INSTALL_LINUX_ARM" ]; then
        print_error "未找到 $INSTALL_LINUX_ARM"
        exit 1
    fi
    chmod +x "$INSTALL_LINUX_ARM" 2>/dev/null || true

    export EASYAIOT_INSTALL_LABEL="${EASYAIOT_INSTALL_LABEL:-EasyAIoT 统一安装脚本 (CentOS / RHEL · ARM)}"
    export EASYAIOT_INSTALL_SCRIPT=".scripts/docker/install_linux_centos_arm.sh"
    export DOCKER_MIRROR
    export DOCKER_PLATFORM="${DOCKER_PLATFORM:-linux/arm64}"

    # CentOS 7 优先走兼容脚本（bash 4.2 / 旧 python）
    if [ "${OS_MAJOR:-}" = "7" ]; then
        export EASYAIOT_PLATFORM_AGENT_SCRIPT="${EASYAIOT_PLATFORM_AGENT_SCRIPT:-.scripts/node/ensure_platform_agent_centos7.sh}"
    fi

    print_section "转交 ARM 平台统一安装脚本"
    print_info "执行: bash $INSTALL_LINUX_ARM ${FORWARD_ARGS[*]:-}"
    cd "$PROJECT_ROOT"
    exec bash "$INSTALL_LINUX_ARM" "${FORWARD_ARGS[@]}"
}

# ---------- main ----------
main() {
    if [ "$UPGRADE_DOCKER_ONLY" = true ]; then
        check_centos_arm
        SKIP_DOCKER_UPGRADE=false
        ensure_modern_docker
        configure_docker_mirror_centos
        print_success "Docker CE 准备完成 (CentOS ARM)"
        exit 0
    fi

    local cmd="${FORWARD_ARGS[0]:-}"
    case "$cmd" in
        help|--help|-h)
            show_centos_arm_help
            echo ""
            print_info "以下为 install_linux_arm.sh 完整帮助："
            echo ""
            bash "$INSTALL_LINUX_ARM" help
            exit 0
            ;;
        profile)
            # 纯查询，无需 Docker 升级
            delegate_to_install_linux_arm
            ;;
        *)
            # 无参数（交互菜单）或其它部署命令：先做 CentOS ARM 环境准备
            prepare_centos_arm_environment
            delegate_to_install_linux_arm
            ;;
    esac
}

main
