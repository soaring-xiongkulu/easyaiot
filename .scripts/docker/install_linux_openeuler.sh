#!/bin/bash

# ============================================
# EasyAIoT 统一安装脚本 (openEuler 24.x)
# ============================================
# 针对 openEuler 24.03 LTS / 24.x 的一键部署入口：
#   1) 检测 openEuler 发行版 / SELinux / firewalld
#   2) 卸载系统自带旧版 docker-engine，安装 Docker CE 20+
#      （修复 $releasever 导致仓库 404 的问题，默认对齐 el9）
#   3) 配置国内镜像源与 DNS、放行常用业务端口
#   4) 转交 install_linux.sh 完成平台部署（命令与交互菜单完全一致）
#
# 使用方法：
#   sudo ./install_linux_openeuler.sh              # 交互引导
#   sudo ./install_linux_openeuler.sh install      # 首次安装
#   sudo ./install_linux_openeuler.sh start|stop|restart|status|verify|update
#   ./install_linux_openeuler.sh check|profile|help
#
# openEuler 专用选项（须写在子命令之前）：
#   -f, --force              跳过 openEuler 发行版检查
#   --no-upgrade-docker      不自动安装/升级 Docker CE
#   --upgrade-docker-only    仅安装/升级 Docker CE 后退出
#   --no-firewall            不自动放行 firewalld 端口
#   --skip-mirror            跳过 Docker 国内镜像源配置
#   --el-release <7|8|9>     Docker CE 仓库对齐的 CentOS 大版本（默认 9）
#
# 示例：
#   sudo ./install_linux_openeuler.sh --upgrade-docker-only
#   sudo ./install_linux_openeuler.sh --no-firewall install
#   sudo EASYAIOT_DEPLOY_PROFILE=full ./install_linux_openeuler.sh install
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
INSTALL_LINUX="${SCRIPT_DIR}/install_linux.sh"

FORCE_OS_CHECK=false
SKIP_DOCKER_UPGRADE=false
UPGRADE_DOCKER_ONLY=false
SKIP_FIREWALL=false
SKIP_MIRROR=false
MIN_DOCKER_MAJOR=20
# openEuler 24.x 对标 RHEL9；部分环境 el9 不可用时可改 --el-release 7
DOCKER_EL_RELEASE="${DOCKER_EL_RELEASE:-9}"
DOCKER_MIRROR="${DOCKER_MIRROR:-https://docker.m.daocloud.io/}"
DOCKER_DNS="${DOCKER_DNS:-223.5.5.5,119.29.29.29}"

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

show_openeuler_help() {
    cat <<'EOF'
EasyAIoT 统一安装脚本 (openEuler 24.x)

用法:
  sudo ./install_linux_openeuler.sh [openEuler选项...] [命令] [参数...]

openEuler 专用选项（须写在子命令之前）:
  -h, --help              显示此帮助
  -f, --force             跳过 openEuler 发行版检查
  --no-upgrade-docker     不自动安装/升级 Docker CE
  --upgrade-docker-only   仅安装/升级 Docker CE 后退出
  --no-firewall           不自动放行 firewalld 端口
  --skip-mirror           跳过 Docker 国内镜像源配置
  --el-release <7|8|9>    Docker CE 仓库对齐的 CentOS 大版本（默认 9）

子命令（与 install_linux.sh 完全一致）:
  install / start / stop / restart / status / logs / build
  build-runtime / pull / clean / clean-build-runtime / update
  verify / check / profile / menu / diagnose / analyze-logs / analyze-disk / help

示例:
  sudo ./install_linux_openeuler.sh
  sudo ./install_linux_openeuler.sh install
  sudo ./install_linux_openeuler.sh --upgrade-docker-only
  sudo ./install_linux_openeuler.sh --el-release 7 install
  sudo EASYAIOT_DEPLOY_PROFILE=edge ./install_linux_openeuler.sh install
  sudo EASYAIOT_DEPLOY_PROFILE=mini ./install_linux_openeuler.sh install

说明:
  - openEuler 自带 docker-engine 版本偏旧且与 docker-ce 冲突，脚本会先卸载再装 CE
  - Docker 官方源不识别 openEuler 的 $releasever，脚本会改写为 el7/8/9
  - 平台业务部署逻辑委托给 install_linux.sh，避免重复维护
EOF
}

# ---------- 参数解析（仅消费 openEuler 专用选项，其余原样转交） ----------
FORWARD_ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_openeuler_help
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
        --el-release)
            if [ -z "${2:-}" ]; then
                print_error "--el-release 需要参数 7|8|9"
                exit 1
            fi
            DOCKER_EL_RELEASE="$2"
            shift 2
            ;;
        --el-release=*)
            DOCKER_EL_RELEASE="${1#*=}"
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

case "$DOCKER_EL_RELEASE" in
    7|8|9) ;;
    *)
        print_error "不支持的 --el-release: ${DOCKER_EL_RELEASE}（仅支持 7|8|9）"
        exit 1
        ;;
esac

# ---------- 发行版检测 ----------
detect_openeuler() {
    OS_ID=""
    OS_VERSION=""
    OS_LIKE=""
    OS_PRETTY=""
    OS_MAJOR=""
    OS_ID_LOWER=""

    if [ -f /etc/os-release ]; then
        # shellcheck source=/dev/null
        . /etc/os-release
        OS_ID="${ID:-}"
        OS_VERSION="${VERSION_ID:-}"
        OS_LIKE="${ID_LIKE:-}"
        OS_PRETTY="${PRETTY_NAME:-$OS_ID $OS_VERSION}"
    elif [ -f /etc/openEuler-release ]; then
        OS_PRETTY=$(cat /etc/openEuler-release)
        OS_ID="openEuler"
        OS_VERSION=$(grep -oE '[0-9]+(\.[0-9]+)?' /etc/openEuler-release | head -1 || true)
    fi

    OS_ID_LOWER=$(echo "$OS_ID" | tr '[:upper:]' '[:lower:]')
    # VERSION_ID 形如 24.03 / 24.03LTS_SP1，取主版本号
    OS_MAJOR=$(echo "$OS_VERSION" | grep -oE '^[0-9]+' | head -1 || true)
}

is_openeuler() {
    [ "$OS_ID_LOWER" = "openeuler" ] && return 0
    [ -f /etc/openEuler-release ] && return 0
    echo " ${OS_LIKE} " | grep -qiE '[[:space:]]openeuler[[:space:]]' && return 0
    return 1
}

check_openeuler() {
    detect_openeuler

    if [ "$FORCE_OS_CHECK" = true ]; then
        print_warning "已跳过 openEuler 发行版检查 (--force)"
        return 0
    fi

    print_section "系统环境检查 (openEuler)"

    if ! is_openeuler; then
        print_error "当前系统不是 openEuler (ID=${OS_ID:-未知})"
        print_info "通用 Linux 请使用: sudo .scripts/docker/install_linux.sh"
        print_info "CentOS/RHEL 请使用: sudo .scripts/docker/install_linux_centos.sh"
        print_info "或加 --force 强制继续: sudo ./install_linux_openeuler.sh --force $*"
        exit 1
    fi

    print_success "检测到: ${OS_PRETTY:-$OS_ID $OS_VERSION}"

    if [ -n "$OS_MAJOR" ] && [ "$OS_MAJOR" -lt 22 ] 2>/dev/null; then
        print_warning "当前 openEuler 主版本为 ${OS_MAJOR}，本脚本主要验证 24.x"
        print_info "若 Docker 安装失败，可尝试: --el-release 7"
    elif [ -n "$OS_MAJOR" ] && [ "$OS_MAJOR" -ne 24 ] 2>/dev/null; then
        print_info "当前为 openEuler ${OS_VERSION}（脚本以 24.x 为主验证，继续尝试）"
    else
        print_success "openEuler 版本匹配: ${OS_VERSION:-24.x}"
    fi

    local arch
    arch=$(uname -m)
    case "$arch" in
        x86_64|amd64)
            print_success "架构: $arch"
            ;;
        aarch64|arm64)
            print_success "架构: $arch (ARM)"
            print_info "openEuler ARM 同样支持本脚本；亦可使用 install_linux_arm.sh"
            ;;
        *)
            print_warning "未识别架构: $arch，继续尝试部署"
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
    # openEuler 自带 docker-engine 常见 18.09
    if [ "$major" -le 1 ] 2>/dev/null && [ "$minor" -lt 20 ] 2>/dev/null; then
        return 0
    fi
    if [ "$major" -lt "$MIN_DOCKER_MAJOR" ] 2>/dev/null; then
        return 0
    fi
    return 1
}

fix_docker_ce_repo_releasever() {
    local el_ver="$1"
    local repo_file="/etc/yum.repos.d/docker-ce.repo"
    if [ ! -f "$repo_file" ]; then
        print_warning "未找到 $repo_file，跳过 releasever 修复"
        return 1
    fi

    # openEuler 的 $releasever 为 24.03 等，Docker 官方仓库无此路径 → 404
    # 同时把官方 download.docker.com 替换为华为云镜像（若仍是官方地址）
    sed -i \
        -e "s|\\\$releasever|${el_ver}|g" \
        -e 's|https\?://download\.docker\.com/linux/centos|https://mirrors.huaweicloud.com/docker-ce/linux/centos|g' \
        "$repo_file"

    print_success "已将 docker-ce.repo 的 releasever 固定为 ${el_ver}"
    return 0
}

add_docker_ce_repo() {
    local pm
    pm=$(pkg_mgr)
    local repo_ok=false
    local mirrors=(
        "https://mirrors.huaweicloud.com/docker-ce/linux/centos/docker-ce.repo"
        "https://repo.huaweicloud.com/docker-ce/linux/centos/docker-ce.repo"
        "https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo"
        "https://download.docker.com/linux/centos/docker-ce.repo"
    )
    local url

    rm -f /etc/yum.repos.d/docker-ce.repo 2>/dev/null || true

    for url in "${mirrors[@]}"; do
        print_info "尝试添加 Docker CE 仓库: $url"
        if command -v dnf >/dev/null 2>&1 && dnf config-manager --add-repo "$url" 2>/dev/null; then
            repo_ok=true
            break
        fi
        if command -v yum-config-manager >/dev/null 2>&1 && yum-config-manager --add-repo "$url" 2>/dev/null; then
            repo_ok=true
            break
        fi
    done

    if [ "$repo_ok" != true ]; then
        print_error "无法添加 Docker CE 仓库"
        return 1
    fi

    fix_docker_ce_repo_releasever "$DOCKER_EL_RELEASE" || return 1

    if command -v dnf >/dev/null 2>&1; then
        dnf makecache 2>/dev/null || true
    else
        $pm makecache 2>/dev/null || true
    fi
    return 0
}

install_docker_ce_openeuler() {
    local pm
    pm=$(pkg_mgr)
    print_section "安装 / 升级 Docker CE (openEuler ${OS_VERSION:-24.x} → el${DOCKER_EL_RELEASE})"

    if [ "$EUID" -ne 0 ]; then
        print_error "安装 Docker CE 需要 root 权限"
        print_info "请执行: sudo $0 --upgrade-docker-only"
        return 1
    fi

    print_info "卸载 openEuler 自带 / 冲突的旧版 docker..."
    $pm remove -y docker \
        docker-client docker-client-latest docker-common \
        docker-latest docker-latest-logrotate docker-logrotate \
        docker-selinux docker-engine-selinux docker-engine \
        docker-ce docker-ce-cli containerd.io \
        2>/dev/null || true

    print_info "安装依赖..."
    $pm install -y dnf-plugins-core 2>/dev/null \
        || $pm install -y yum-utils 2>/dev/null \
        || true
    $pm install -y device-mapper-persistent-data lvm2 2>/dev/null || true

    add_docker_ce_repo || return 1

    print_info "安装 docker-ce / cli / containerd / compose-plugin（--nogpgcheck）..."
    set +e
    $pm install -y --nogpgcheck \
        docker-ce docker-ce-cli containerd.io docker-compose-plugin docker-buildx-plugin
    local yum_rc=$?
    set -e

    if [ "$yum_rc" -ne 0 ]; then
        print_warning "完整组件安装失败，尝试不含 buildx 的组合..."
        set +e
        $pm install -y --nogpgcheck \
            docker-ce docker-ce-cli containerd.io docker-compose-plugin
        yum_rc=$?
        set -e
    fi

    if [ "$yum_rc" -ne 0 ] && [ "$DOCKER_EL_RELEASE" != "7" ]; then
        print_warning "el${DOCKER_EL_RELEASE} 安装失败，回退尝试 el7 仓库..."
        DOCKER_EL_RELEASE=7
        add_docker_ce_repo || return 1
        set +e
        $pm install -y --nogpgcheck \
            docker-ce docker-ce-cli containerd.io docker-compose-plugin
        yum_rc=$?
        set -e
    fi

    if [ "$yum_rc" -ne 0 ]; then
        print_warning "带 compose-plugin 安装失败，尝试仅安装 docker-ce..."
        $pm install -y --nogpgcheck docker-ce docker-ce-cli containerd.io || {
            print_error "Docker CE 安装失败"
            print_info "可手动尝试: sudo $0 --el-release 7 --upgrade-docker-only"
            return 1
        }
    fi

    systemctl daemon-reload
    systemctl enable docker
    systemctl start docker
    sleep 2

    if ! docker info >/dev/null 2>&1; then
        print_error "Docker CE 启动失败，请检查: journalctl -u docker -n 50"
        print_info "若为 SELinux 拦截，可临时: setenforce 0 后 systemctl restart docker"
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
        install_docker_ce_openeuler || exit 1
        return 0
    fi

    if ! docker info >/dev/null 2>&1; then
        if [ "$EUID" -eq 0 ]; then
            systemctl start docker 2>/dev/null || true
        fi
    fi

    local ver
    ver=$(get_docker_server_version)
    print_info "当前 Docker 版本: ${ver:-未知}"

    # 检测是否为 openEuler 自带的 docker-engine（包名冲突场景）
    local pkg_name=""
    if command -v rpm >/dev/null 2>&1; then
        pkg_name=$(rpm -qf "$(command -v dockerd 2>/dev/null || command -v docker)" 2>/dev/null || true)
    fi
    if echo "$pkg_name" | grep -qiE 'docker-engine|^docker-[0-9]'; then
        print_warning "检测到 openEuler 自带 docker 包 (${pkg_name})，将替换为 Docker CE"
        install_docker_ce_openeuler || exit 1
        return 0
    fi

    if ! is_docker_too_old "$ver"; then
        print_success "Docker 版本满足要求 (>= ${MIN_DOCKER_MAJOR})"
        return 0
    fi

    print_warning "Docker ${ver:-未知} 过旧（openEuler 自带常见 18.09），无法拉取新镜像"
    print_info "将自动升级为 Docker CE ${MIN_DOCKER_MAJOR}+..."
    install_docker_ce_openeuler || exit 1
}

# ---------- 镜像源 / 防火墙 ----------
configure_docker_mirror_openeuler() {
    if [ "$SKIP_MIRROR" = true ]; then
        print_info "已跳过 Docker 镜像源配置 (--skip-mirror)"
        return 0
    fi
    if [ "$EUID" -ne 0 ]; then
        print_warning "配置镜像源需要 root，已跳过"
        return 0
    fi

    print_info "配置 Docker 国内镜像源与 DNS: mirror=${DOCKER_MIRROR} dns=${DOCKER_DNS}"
    mkdir -p /etc/docker
    local config_file="/etc/docker/daemon.json"
    local need_restart=false

    # openEuler 常出现 resolv.conf 指向 loopback，一并写入公网 DNS
    if [ ! -f "$config_file" ]; then
        if command -v python3 >/dev/null 2>&1; then
            python3 - "$config_file" "$DOCKER_MIRROR" "$DOCKER_DNS" <<'PYEOF'
import json, sys
path, mirror, dns_csv = sys.argv[1], sys.argv[2], sys.argv[3]
dns = [x.strip() for x in dns_csv.split(",") if x.strip()]
cfg = {"registry-mirrors": [mirror], "dns": dns}
with open(path, "w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
    f.write("\n")
PYEOF
        else
            cat > "$config_file" <<EOF
{
  "registry-mirrors": ["${DOCKER_MIRROR}"],
  "dns": ["223.5.5.5", "119.29.29.29"]
}
EOF
        fi
        need_restart=true
        print_success "已写入 $config_file"
    elif command -v python3 >/dev/null 2>&1; then
        local rc=0
        python3 - "$config_file" "$DOCKER_MIRROR" "$DOCKER_DNS" <<'PYEOF' || rc=$?
import json, sys
path, mirror, dns_csv = sys.argv[1], sys.argv[2], sys.argv[3]
want_dns = [x.strip() for x in dns_csv.split(",") if x.strip()]
try:
    with open(path) as f:
        cfg = json.load(f)
except Exception:
    sys.exit(1)
changed = False
mirrors = cfg.get("registry-mirrors", [])
if not isinstance(mirrors, list):
    mirrors = []
normalized = [m.rstrip("/") for m in mirrors if isinstance(m, str)]
if mirror.rstrip("/") not in normalized:
    mirrors.append(mirror)
    cfg["registry-mirrors"] = mirrors
    changed = True
dns = cfg.get("dns", [])
if not isinstance(dns, list):
    dns = []
for d in want_dns:
    if d not in dns:
        dns.append(d)
        changed = True
if dns:
    cfg["dns"] = dns
if not changed:
    sys.exit(0)
with open(path, "w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
    f.write("\n")
sys.exit(3)
PYEOF
        case $rc in
            0) print_success "Docker 镜像源 / DNS 已就绪" ;;
            3) need_restart=true; print_success "Docker 镜像源 / DNS 已更新" ;;
            *) print_warning "无法自动合并 $config_file，请手动添加 registry-mirrors 与 dns" ;;
        esac
    else
        if grep -q 'docker\.m\.daocloud\.io' "$config_file" 2>/dev/null; then
            print_success "Docker 镜像源已配置"
        else
            print_warning "已有 $config_file 且无 python3，跳过自动合并"
        fi
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

prepare_openeuler_environment() {
    check_openeuler
    ensure_modern_docker
    configure_docker_mirror_openeuler
    configure_firewalld_ports
}

# ---------- 转交 install_linux.sh ----------
delegate_to_install_linux() {
    if [ ! -f "$INSTALL_LINUX" ]; then
        print_error "未找到 $INSTALL_LINUX"
        exit 1
    fi
    chmod +x "$INSTALL_LINUX" 2>/dev/null || true

    export EASYAIOT_INSTALL_LABEL="${EASYAIOT_INSTALL_LABEL:-EasyAIoT 统一安装脚本 (openEuler)}"
    export EASYAIOT_INSTALL_SCRIPT=".scripts/docker/install_linux_openeuler.sh"
    export DOCKER_MIRROR
    export DOCKER_DNS

    print_section "转交平台统一安装脚本"
    print_info "执行: bash $INSTALL_LINUX ${FORWARD_ARGS[*]:-}"
    cd "$PROJECT_ROOT"
    exec bash "$INSTALL_LINUX" "${FORWARD_ARGS[@]}"
}

# ---------- main ----------
main() {
    if [ "$UPGRADE_DOCKER_ONLY" = true ]; then
        check_openeuler
        SKIP_DOCKER_UPGRADE=false
        ensure_modern_docker
        configure_docker_mirror_openeuler
        print_success "Docker CE 准备完成"
        exit 0
    fi

    local cmd="${FORWARD_ARGS[0]:-}"
    case "$cmd" in
        help|--help|-h)
            show_openeuler_help
            echo ""
            print_info "以下为 install_linux.sh 完整帮助："
            echo ""
            bash "$INSTALL_LINUX" help
            exit 0
            ;;
        profile)
            # 纯查询，无需 Docker 升级
            delegate_to_install_linux
            ;;
        *)
            # 无参数（交互菜单）或其它部署命令：先做 openEuler 环境准备
            prepare_openeuler_environment
            delegate_to_install_linux
            ;;
    esac
}

main
