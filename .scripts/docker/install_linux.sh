#!/bin/bash

# ============================================
# EasyAIoT 统一安装脚本
# ============================================
# 使用方法：
#   ./install_linux.sh              # 无参数：打开两层交互引导（部署 / 分析）
#   ./install_linux.sh [命令]       # 直接执行命令（适合脚本/automation）
#
# 可用命令：
#   install    - 安装并启动所有服务（首次运行，交互选择部署形态）
#   start      - 启动所有服务
#   stop       - 停止所有服务
#   restart    - 重启所有服务
#   status     - 查看所有服务状态
#   logs       - 查看服务日志
#   build           - 重新构建所有镜像（各模块本地构建）
#   build-runtime [模块] - 构建/推送运行时镜像到远程仓库（推送成功后删除本地镜像；可选 DEVICE|AI|VIDEO|WEB|APP|VISUALIZE|TRANSFORM|PANEL）
#   pull            - 从远程仓库拉取预构建运行时镜像（等同 runtime_image.sh pull）
#   clean      - 清理所有容器和镜像
#   clean-build-runtime - 清理 build-runtime 构建产物（先停业务服务，再删运行时镜像/构建缓存；保留跨架构基础镜像；不停中间件）
#   update     - 更新镜像并重启所有服务（交互可选拉取/本地重建）
#   verify     - 验证所有服务是否启动成功
#   check      - 检查 Docker 和 Docker Compose 安装状态
#   profile    - 显示当前部署形态与服务范围
#   site [子命令] - 官方网站 SITE 独立部署
#   menu       - 打开两层交互引导（同无参数）
#   diagnose       - 问题分析定位（进入【分析】子菜单）
#   analyze-logs   - 多模块日志合并分析（各模块约 500 行，带分割线）
#   analyze-disk   - 项目关键目录磁盘占用分析
#
# 部署形态（EASYAIOT_DEPLOY_PROFILE）：
#   mini(1)     - 4G：iot-system + VIDEO/AI/WEB + 最小中间件（无 Kafka/iot-sink/Nacos/Gateway/Infra/可视化）
#   standard(2) - 16G：不含 TDengine/iot-device/iot-tdengine/NodeRED/iot-visualize（含 EMQX）
#   full(3)     - 全量（默认，约 20G）；含 iot-visualize/VISUALIZE、TRANSFORM；启动后自动拉起工业协议演示（Modbus TCP/RTU + OPC UA）；PANEL 全形态启用
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本所在目录（必须在 cd 之前计算：相对路径调用时，cd 后 dirname 会解析错位，
# 曾导致日志目录落到项目根 /logs 而非 .scripts/docker/logs）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EASYAIOT_INSTALL_LABEL="${EASYAIOT_INSTALL_LABEL:-EasyAIoT 统一安装脚本 (AMD64/x86_64)}"

# 项目根目录（从.scripts/docker回到项目根目录）
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "$PROJECT_ROOT"

# shellcheck source=deploy_profile.sh
source "${SCRIPT_DIR}/deploy_profile.sh"

# shellcheck source=runtime_image_common.sh
source "${SCRIPT_DIR}/runtime_image_common.sh"

# shellcheck source=diagnose_tools.sh
source "${SCRIPT_DIR}/diagnose_tools.sh"

# shellcheck source=node/ensure_platform_agent_invoke.sh
source "${PROJECT_ROOT}/.scripts/node/ensure_platform_agent_invoke.sh"

_ensure_platform_agent_info() { print_info "$1"; }
_ensure_platform_agent_ok() { print_success "$1"; }
_ensure_platform_agent_warn() { print_warning "$1"; }

ensure_platform_agent_after_stack() {
    ENSURE_PLATFORM_AGENT_INFO=_ensure_platform_agent_info \
    ENSURE_PLATFORM_AGENT_OK=_ensure_platform_agent_ok \
    ENSURE_PLATFORM_AGENT_WARN=_ensure_platform_agent_warn \
    ensure_platform_agent_if_needed || true
}

# 部署完成后并行常驻 mqtt-demo（01/02/03 独立 clientId），让设备详情各 Tab 有实时数据。
# 关闭：EASYAIOT_ENABLE_MQTT_DEMO=0；仅部分：MQTT_DEMO_SCRIPTS=up,down
ensure_mqtt_demo_after_stack() {
    local demo_dir="${PROJECT_ROOT}/.scripts/mqtt-demo"
    local starter="${demo_dir}/start_mqtt_demo.sh"
    if [ "${EASYAIOT_ENABLE_MQTT_DEMO:-1}" = "0" ]; then
        print_info "跳过 mqtt-demo 自动启动（EASYAIOT_ENABLE_MQTT_DEMO=0）"
        return 0
    fi
    if [ "${EASYAIOT_ENABLE_EMQX:-1}" = "0" ]; then
        print_info "跳过 mqtt-demo 自动启动（EMQX 未启用）"
        return 0
    fi
    if [ ! -x "$starter" ] && [ -f "$starter" ]; then
        chmod +x "$starter" "${demo_dir}/stop_mqtt_demo.sh" 2>/dev/null || true
    fi
    if [ ! -f "$starter" ]; then
        print_warning "未找到 ${starter}，跳过 mqtt-demo"
        return 0
    fi
    print_section "启动 MQTT 演示设备（01/02/03 并行）"
    if bash "$starter"; then
        print_success "mqtt-demo 已启动（日志: ${demo_dir}/run/logs/）"
    else
        print_warning "mqtt-demo 启动未完全成功，可稍后手动: bash ${starter}"
    fi
}

# full 形态：启动工业协议演示从站（Modbus TCP/RTU + OPC UA），让页面有采集数据。
# 关闭：EASYAIOT_ENABLE_INDUSTRIAL_DEMO=0；跳过种子：EASYAIOT_APPLY_INDUSTRIAL_SEED=0
ensure_industrial_demo_after_stack() {
    local demo_dir="${PROJECT_ROOT}/.scripts/industrial-demo"
    local starter="${demo_dir}/start_industrial_demo.sh"
    ensure_deploy_profile
    if ! is_full_deploy_profile; then
        print_info "跳过工业协议演示（仅 full 形态自动启动，当前: ${EASYAIOT_DEPLOY_PROFILE}）"
        return 0
    fi
    if [ "${EASYAIOT_ENABLE_INDUSTRIAL_DEMO:-1}" = "0" ]; then
        print_info "跳过工业协议演示自动启动（EASYAIOT_ENABLE_INDUSTRIAL_DEMO=0）"
        return 0
    fi
    if [ ! -x "$starter" ] && [ -f "$starter" ]; then
        chmod +x "$starter" "${demo_dir}/stop_industrial_demo.sh" 2>/dev/null || true
    fi
    if [ ! -f "$starter" ]; then
        print_warning "未找到 ${starter}，跳过工业协议演示"
        return 0
    fi
    print_section "启动工业协议演示（Modbus TCP / RTU / OPC UA）"
    if bash "$starter"; then
        print_success "industrial-demo 已启动（日志: ${demo_dir}/run/logs/）"
    else
        print_warning "industrial-demo 启动未完全成功，可稍后手动: bash ${starter}"
    fi
}

stop_industrial_demo_before_stack() {
    local stopper="${PROJECT_ROOT}/.scripts/industrial-demo/stop_industrial_demo.sh"
    [ -f "$stopper" ] || return 0
    ensure_deploy_profile
    if ! is_full_deploy_profile && [ "${EASYAIOT_ENABLE_INDUSTRIAL_DEMO:-1}" != "1" ]; then
        return 0
    fi
    chmod +x "$stopper" 2>/dev/null || true
    print_info "停止工业协议演示进程..."
    bash "$stopper" || true
}

# 日志文件配置
LOG_DIR="${SCRIPT_DIR}/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/install_linux_$(date +%Y%m%d_%H%M%S).log"

# 初始化日志文件
echo "=========================================" >> "$LOG_FILE"
echo "EasyAIoT 统一安装脚本日志" >> "$LOG_FILE"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "命令: $*" >> "$LOG_FILE"
echo "=========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 模块列表（按依赖顺序）
MODULES=(
    ".scripts/docker"  # 基础服务（Nacos、PostgreSQL、Redis等）
    "DEVICE"           # Device服务（网关和微服务）
    "AI"               # AI服务
    "VIDEO"            # Video服务
    "WEB"              # Web前端服务
    "APP"              # App移动端H5（仅 full 全量形态）
    "VISUALIZE"        # 可视化编辑器（仅 full 全量形态）
    "TRANSFORM"        # 系统对接（仅 full 全量形态）
    "PANEL"            # 运维控制台：源码/Docker 可装；安装包本身即为 PANEL，部署默认跳过
)

# 模块名称映射
declare -A MODULE_NAMES
MODULE_NAMES[".scripts/docker"]="基础服务"
MODULE_NAMES["DEVICE"]="Device服务"
MODULE_NAMES["AI"]="AI服务"
MODULE_NAMES["VIDEO"]="Video服务"
MODULE_NAMES["WEB"]="Web前端服务"
MODULE_NAMES["APP"]="App移动端H5"
MODULE_NAMES["VISUALIZE"]="可视化编辑器"
MODULE_NAMES["TRANSFORM"]="系统对接"
MODULE_NAMES["PANEL"]="运维控制台"

# 模块端口映射
declare -A MODULE_PORTS
MODULE_PORTS[".scripts/docker"]="8848"  # Nacos端口
MODULE_PORTS["DEVICE"]="48080"           # Gateway端口
MODULE_PORTS["AI"]="5000"
MODULE_PORTS["VIDEO"]="6000"
MODULE_PORTS["WEB"]="8888"
MODULE_PORTS["APP"]="9010"
MODULE_PORTS["VISUALIZE"]="8002"
MODULE_PORTS["TRANSFORM"]="48096"
MODULE_PORTS["PANEL"]="9200"

# 模块健康检查端点
declare -A MODULE_HEALTH_ENDPOINTS
MODULE_HEALTH_ENDPOINTS[".scripts/docker"]="/nacos/actuator/health"
MODULE_HEALTH_ENDPOINTS["DEVICE"]="/actuator/health"  # Gateway健康检查
MODULE_HEALTH_ENDPOINTS["AI"]="/actuator/health"
MODULE_HEALTH_ENDPOINTS["VIDEO"]="/actuator/health"
MODULE_HEALTH_ENDPOINTS["WEB"]="/health"
MODULE_HEALTH_ENDPOINTS["APP"]="/health"
MODULE_HEALTH_ENDPOINTS["VISUALIZE"]="/health"
MODULE_HEALTH_ENDPOINTS["TRANSFORM"]="/actuator/health"
MODULE_HEALTH_ENDPOINTS["PANEL"]="/health"

# 统计当前部署形态下参与 install 汇总的模块数（已启用且存在安装脚本）
_count_installable_modules() {
    local count=0 module _inst_script
    for module in "${MODULES[@]}"; do
        module_enabled_for_deploy_profile "$module" || continue
        _inst_script="${PROJECT_ROOT}/${module}/$(module_install_script "$module")"
        [ -f "$_inst_script" ] || continue
        count=$((count + 1))
    done
    echo "$count"
}

# 统计当前部署形态下参与 verify 汇总的模块数
_count_verifiable_modules() {
    local count=0 module
    for module in "${MODULES[@]}"; do
        module_enabled_for_deploy_profile "$module" && count=$((count + 1))
    done
    echo "$count"
}

# 日志输出函数（去掉颜色代码后写入日志文件）
log_to_file() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    # 去掉 ANSI 颜色代码
    local clean_message=$(echo "$message" | sed -r "s/\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[mGK]//g")
    echo "[$timestamp] $clean_message" >> "$LOG_FILE"
}

# 打印带颜色的消息（同时输出到日志文件）
print_info() {
    local message="${BLUE}[INFO]${NC} $1"
    echo -e "$message"
    log_to_file "[INFO] $1"
}

print_success() {
    local message="${GREEN}[SUCCESS]${NC} $1"
    echo -e "$message"
    log_to_file "[SUCCESS] $1"
}

print_warning() {
    local message="${YELLOW}[WARNING]${NC} $1"
    echo -e "$message"
    log_to_file "[WARNING] $1"
}

print_error() {
    local message="${RED}[ERROR]${NC} $1"
    echo -e "$message"
    log_to_file "[ERROR] $1"
}

print_section() {
    local section="$1"
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}  $section${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    log_to_file ""
    log_to_file "========================================="
    log_to_file "  $section"
    log_to_file "========================================="
    log_to_file ""
}

# 是否运行在容器内（PANEL Docker 版等：无 systemd/sysctl，且网卡 IP 为桥接地址）
_running_in_container() {
    [ -f /.dockerenv ] && return 0
    if [ -r /proc/1/cgroup ] && grep -Eq '(docker|containerd|kubepods|/libpod)' /proc/1/cgroup 2>/dev/null; then
        return 0
    fi
    return 1
}

# Docker 默认桥接网段（容器内自动探测到的 172.17–31.x 通常不是宿主机 LAN IP）
_is_likely_docker_bridge_ip() {
    case "${1:-}" in
        172.1[7-9].*|172.2[0-9].*|172.3[0-1].*) return 0 ;;
        *) return 1 ;;
    esac
}

# 经 docker.sock + --network=host 探测真实宿主机出口 IP（PANEL 容器场景）
_detect_host_ip_via_docker_host_net() {
    check_command docker || return 1
    docker info >/dev/null 2>&1 || return 1

    local probe_img=""
    for probe_img in alpine:latest docker.m.daocloud.io/library/alpine:latest busybox:latest; do
        if docker image inspect "$probe_img" >/dev/null 2>&1; then
            break
        fi
        probe_img=""
    done
    [ -n "$probe_img" ] || return 1

    docker run --rm --network=host --entrypoint sh "$probe_img" -c \
        "ip -4 route get 1.1.1.1 2>/dev/null | sed -n 's/.*src \([0-9.]*\).*/\1/p'" \
        2>/dev/null
}

# 检测宿主机 IPv4 地址，并导出给子模块安装脚本和 docker compose 使用
detect_host_ip() {
    # 已显式导出 HOST_IP 时直接采用（错误提示承诺的逃生通道；也天然避免重复探测）
    if [ -n "${HOST_IP:-}" ]; then
        print_info "使用已设置的宿主机 IP: $HOST_IP"
        return 0
    fi

    local host_ip=""

    # PANEL 等容器内：本机网卡是 Docker 桥接地址，需经 --network=host 探测宿主机
    if _running_in_container; then
        host_ip=$(_detect_host_ip_via_docker_host_net | head -n 1 | tr -d '[:space:]')
        if [ -n "$host_ip" ] && ! _is_likely_docker_bridge_ip "$host_ip"; then
            export HOST_IP="$host_ip"
            print_info "检测到宿主机 IP（容器经 docker host 网络）: $HOST_IP"
            return 0
        fi
        host_ip=""
    fi

    if check_command ip; then
        host_ip=$(ip route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src"){print $(i+1); exit}}')
    fi

    if [ -z "$host_ip" ] && check_command hostname; then
        host_ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    fi

    if [ -z "$host_ip" ] && check_command ip; then
        host_ip=$(ip -4 addr show scope global 2>/dev/null | awk '/inet /{print $2}' | cut -d/ -f1 | head -n 1)
    fi

    if [ -z "$host_ip" ]; then
        print_error "无法自动检测宿主机 IP，无法为 GB28181/ZLM 注入正确的媒体地址"
        print_info "请检查 iproute2/hostname 命令是否可用，或手动导出 HOST_IP 后重新执行脚本"
        return 1
    fi

    if _is_likely_docker_bridge_ip "$host_ip"; then
        print_warning "检测到疑似 Docker 桥接 IP: $host_ip（媒体地址可能不正确）"
        print_warning "请在 panel.env / 环境变量中设置 HOST_IP=<宿主机局域网 IP> 后重试"
    fi

    export HOST_IP="$host_ip"
    print_info "检测到宿主机 IP: $HOST_IP"
    return 0
}

# 预留 ZLM RTP 端口段，避免被 Linux 临时端口抢占导致 ZLM 启动或收流异常
configure_rtp_port_reservation() {
    local sysctl_file="/etc/sysctl.d/99-zlm-rtp.conf"
    local expected_config="net.ipv4.ip_local_reserved_ports = 30000-30500"

    if [ "$(uname -s)" != "Linux" ]; then
        return 0
    fi

    # PANEL 容器内写 /etc/sysctl.d 与 sysctl 只作用于容器，对宿主机无效
    if _running_in_container; then
        print_warning "容器环境无法配置宿主机 RTP 端口预留，已跳过"
        print_info "建议在宿主机执行: echo '$expected_config' | sudo tee $sysctl_file && sudo sysctl --system"
        return 0
    fi

    if [ "$EUID" -ne 0 ]; then
        print_warning "配置 RTP 端口预留需要 root 权限，已跳过"
        print_warning "建议使用 sudo 运行安装脚本，以固化 30000-30500 端口预留"
        return 0
    fi

    if ! check_command sysctl; then
        print_warning "未找到 sysctl，跳过 RTP 端口预留（可稍后手动写入 $sysctl_file）"
        return 0
    fi

    mkdir -p /etc/sysctl.d

    if [ -f "$sysctl_file" ] && grep -Fxq "$expected_config" "$sysctl_file"; then
        print_info "RTP 端口预留已配置: 30000-30500"
        return 0
    fi

    print_info "配置 Linux RTP 端口预留: 30000-30500"
    cat > "$sysctl_file" << EOF
$expected_config
EOF
    if ! sysctl --system > /dev/null 2>&1; then
        print_warning "已写入 $sysctl_file，但 sysctl --system 未成功（配置将在下次重启后生效）"
        return 0
    fi
    print_success "RTP 端口预留已生效"
}

# 检查 /dev/null 设备节点状态，返回 0 正常、1 异常。
_verify_dev_null_node() {
    if [ ! -e /dev/null ]; then
        print_error "/dev/null 不存在，Docker 容器将无法启动（修复: sudo mknod -m 666 /dev/null c 1 3）"
        return 1
    elif [ ! -c /dev/null ]; then
        local _ftype; _ftype=$(stat -c '%F' /dev/null 2>/dev/null || echo '未知类型')
        print_error "/dev/null 不是字符设备（${_ftype}），Docker 容器将无法启动"
        print_info "修复: sudo rm -f /dev/null && sudo mknod -m 666 /dev/null c 1 3"
        return 1
    fi
    return 0
}

# 检测 Docker 是否为 rootless 模式（runc 在 rootless 下可能间歇性无法创建 /dev/null）
_detect_docker_rootless() {
    docker info --format '{{.SecurityOptions}}' 2>/dev/null | grep -q "rootless"
}

# 容器创建实测用的探测镜像（按优先级）。
# 注：registry-mirrors 代理拉取时，错误/日志里仍会显示 docker.io/library/...，属 Docker 正常行为，不代表未走镜像源。
_DOCKER_PROBE_IMAGES=(
    "alpine:latest"
    "docker.m.daocloud.io/library/alpine:latest"
)

# 确保探测镜像在本地可用；本地已有则跳过拉取。
_ensure_docker_probe_image() {
    local _img="$1"
    docker image inspect "$_img" >/dev/null 2>&1 && return 0
    docker pull "$_img" >/dev/null 2>&1
}

# 用最简单的容器实测 Docker 是否当前能成功创建容器。
# 成功返回 0，失败返回 1 并设置 _DOCKER_CREATE_FAIL_MSG。
_verify_docker_create() {
    local _img _test_output _pull_failed=0
    for _img in "${_DOCKER_PROBE_IMAGES[@]}"; do
        if ! _ensure_docker_probe_image "$_img"; then
            _pull_failed=1
            continue
        fi
        _test_output=$(docker run --rm "$_img" echo "docker_create_test" 2>&1) && return 0
        _DOCKER_CREATE_FAIL_MSG="$_test_output"

        # 尝试用 io.containerd.runc.v2 运行时（部分环境与 runc 行为不同）
        _test_output=$(docker run --rm --runtime io.containerd.runc.v2 "$_img" echo "docker_create_test" 2>&1) && return 0
        _DOCKER_CREATE_FAIL_MSG="$_test_output"
    done

    if [ "$_pull_failed" -eq 1 ]; then
        _DOCKER_CREATE_FAIL_MSG="${_DOCKER_CREATE_FAIL_MSG:-探测镜像拉取失败}"
        _DOCKER_CREATE_FAIL_MSG="${_DOCKER_CREATE_FAIL_MSG}

提示：错误里出现 docker.io 是 Docker 的镜像引用写法；若已配置 registry-mirrors，实际请求可能经镜像站转发。
请确认: docker info | grep -A5 'Registry Mirrors'；或手动拉取: docker pull docker.m.daocloud.io/library/alpine:latest"
    fi

    return 1
}

# 验证 /dev/null 设备节点（Docker 容器创建的硬性前提）
# /dev/null 缺失或不是字符设备时，runc 报：
#   "error reopening /dev/null inside container: open /dev/null: operation not permitted"
# 此时所有新容器都无法启动，必须在编排前尽早检测并给出修复指引。
_verify_dev_null() {
    # 第一步：节点存在性与类型检查
    _verify_dev_null_node || return 1

    # 第二步：权限检查（仅告警，不阻断：部分发行版使用 ACL 扩展权限，stat %a 可能不反映实际可访问性）
    local _null_perm
    _null_perm=$(stat -c '%a' /dev/null 2>/dev/null || echo "")
    if [ -n "$_null_perm" ] && [ "$_null_perm" != "666" ]; then
        print_warning "/dev/null 权限异常（当前 ${_null_perm}，通常应为 666），可能导致容器启动失败"
        if [ "$EUID" -eq 0 ]; then
            chmod 666 /dev/null 2>/dev/null && print_success "/dev/null 权限已修复为 666" \
                || print_warning "自动修复 /dev/null 权限失败，请手动执行: sudo chmod 666 /dev/null"
        else
            print_info "请以 root 执行: sudo chmod 666 /dev/null"
        fi
    fi

    # 第三步：容器创建实测（关键：节点正常≠Docker 能创建容器）
    if _verify_docker_create; then
        return 0
    fi

    # 容器创建失败 → 根因诊断（详细信息请查看日志或咨询文档）
    print_error "Docker 无法创建容器: $_DOCKER_CREATE_FAIL_MSG"
    if _detect_docker_rootless; then
        print_info "rootless Docker 可能间歇性 OCI 错误，推荐安装 crun 替代 runc，或参考文档排查"
    else
        print_info "请检查: systemctl status docker / df -h / dmesg | grep -i denied"
    fi

    return 1
}

prepare_runtime_environment() {
    _verify_dev_null || exit 1
    detect_host_ip
    configure_rtp_port_reservation
}

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

# shellcheck source=docker_compose_bundled.sh
source "${SCRIPT_DIR}/docker_compose_bundled.sh"

# 检查 Docker 权限
check_docker_permission() {
    if ! docker info &> /dev/null; then
        local error_msg=$(docker info 2>&1)
        
        if echo "$error_msg" | grep -qi "permission denied\|cannot connect"; then
            print_error "没有权限访问 Docker daemon（执行: sudo usermod -aG docker \$USER 后重新登录，或用 sudo 运行此脚本）"
        elif echo "$error_msg" | grep -qi "Is the docker daemon running"; then
            print_error "Docker daemon 未运行（执行: sudo systemctl start docker）"
            if systemctl is-failed docker.service &> /dev/null 2>&1; then
                print_info "若启动失败，运行诊断: sudo .scripts/docker/diagnose_docker_systemd.sh diagnose"
            fi
        else
            print_error "无法连接 Docker daemon: $error_msg"
        fi
        exit 1
    fi
    
    if ! docker ps &> /dev/null; then
        print_error "Docker 命令执行失败"
        exit 1
    fi
}

# 检查 Docker 是否安装（进程内幂等：同一次运行重复调用直接返回）
check_docker() {
    [ "${_DOCKER_CHECKED:-0}" = "1" ] && return 0
    print_info "检查 Docker..."
    
    if ! check_command docker; then
        print_error "Docker 未安装，请执行: curl -fsSL https://get.docker.com | sudo sh"
        exit 1
    fi
    
    local docker_version=$(docker --version 2>/dev/null || echo "未知版本")
    print_success "Docker: $docker_version"
    check_docker_permission "$@"
    _DOCKER_CHECKED=1
}

# 探测 Docker Compose（v1/v2 通用实现，check_docker_compose 与 check_environment 共用）
# 设置全局：COMPOSE_CMD（v2 优先）、COMPOSE_V1_VERSION、COMPOSE_V2_VERSION（未安装为空）
# 返回 0 表示至少一个版本可用
detect_compose() {
    COMPOSE_CMD=""
    COMPOSE_V1_VERSION=""
    COMPOSE_V2_VERSION=""

    if check_command docker-compose; then
        COMPOSE_V1_VERSION=$(docker-compose --version 2>/dev/null || true)
        if [ -n "$COMPOSE_V1_VERSION" ]; then
            COMPOSE_CMD="docker-compose"
        fi
    fi

    if docker compose version &> /dev/null; then
        COMPOSE_V2_VERSION=$(docker compose version --short 2>/dev/null || true)
        if [ -z "$COMPOSE_V2_VERSION" ]; then
            COMPOSE_V2_VERSION=$(docker compose version 2>&1 | grep -iE "version|docker compose" | head -1 | sed 's/^[[:space:]]*//' || true)
        fi
        # 个别版本输出帮助信息而非版本号：只标记可用
        if [ -z "$COMPOSE_V2_VERSION" ] || echo "$COMPOSE_V2_VERSION" | grep -qiE "usage|command|options"; then
            COMPOSE_V2_VERSION="命令可用"
        fi
        COMPOSE_CMD="docker compose"
    fi

    [ -n "$COMPOSE_CMD" ]
}

# 检查 Docker Compose 是否安装（进程内幂等；版本不足时自动用内置离线包覆盖升级）
check_docker_compose() {
    [ "${_COMPOSE_CHECKED:-0}" = "1" ] && return 0
    print_info "检查 Docker Compose..."

    local _need_fix=false _reason=""
    if ! detect_compose; then
        _need_fix=true
        _reason="未安装"
    elif ! compose_version_meets_requirement_quiet; then
        _need_fix=true
        _reason="版本过低（需要 v${COMPOSE_MIN_VERSION}+）"
    fi

    if [ "$_need_fix" = true ]; then
        if bundled_compose_available; then
            local _bundled_ver
            _bundled_ver=$(get_bundled_compose_version 2>/dev/null || echo "未知")
            print_warning "Docker Compose ${_reason}"
            print_info "将使用项目内置 Docker Compose v${_bundled_ver} 离线安装/升级（架构: $(uname -m)）"
            if [ "$EUID" -ne 0 ]; then
                print_error "请使用 sudo 运行以自动安装/升级 Docker Compose"
                echo ""
                echo "或手动执行："
                bundled_compose_manual_hint
                exit 1
            fi
            if ! install_bundled_docker_compose || ! compose_version_meets_requirement_quiet; then
                print_error "内置 Docker Compose 安装/升级失败或版本仍不符合要求"
                exit 1
            fi
            detect_compose
        else
            print_error "Docker Compose ${_reason}，且当前架构 $(uname -m) 无内置离线包"
            exit 1
        fi
    fi

    local _ver_display=""
    [ -n "$COMPOSE_V2_VERSION" ] && _ver_display="$COMPOSE_V2_VERSION"
    [ -n "$COMPOSE_V1_VERSION" ] && _ver_display="${_ver_display:+$_ver_display, }$COMPOSE_V1_VERSION"
    print_success "Docker Compose: ${_ver_display:-已安装}"
    _COMPOSE_CHECKED=1
}

# Docker 镜像源（唯一允许的源，规整后用于比较与写入）
DOCKER_MIRROR="https://docker.m.daocloud.io/"

# 配置变更后按需重启 Docker（仅服务在运行时）
# 容器 / 无 systemd 环境：静默跳过，避免 set -e 下 command not found 干扰日志
restart_docker_if_active() {
    if ! check_command systemctl; then
        print_warning "未找到 systemctl，跳过重启 Docker（容器或非 systemd 环境）"
        return 0
    fi
    if systemctl is-active --quiet docker 2>/dev/null; then
        print_info "正在重启 Docker 服务以使配置生效..."
        systemctl daemon-reload 2>/dev/null || true
        if systemctl restart docker 2>/dev/null; then
            print_success "Docker 服务已重启"
        else
            print_warning "Docker 重启失败，请稍后手动执行: sudo systemctl restart docker"
        fi
    fi
}

# 配置 Docker 镜像源
# 优先用 jq（纯进程内 JSON 编辑，无解释器启动开销）；无 jq 退回精简版 python3；
# 两者皆无时：文件不存在则直写最小配置，已存在则跳过（不敢盲改未知 JSON）。
configure_docker_mirror() {
    print_info "配置 Docker 镜像源..."

    local config_file="/etc/docker/daemon.json"

    # PANEL 容器内写 /etc/docker 不影响宿主机 dockerd
    if _running_in_container; then
        print_info "容器环境跳过写入宿主机 Docker 镜像源（请在宿主机配置 /etc/docker/daemon.json）"
        return 0
    fi

    if [ "$EUID" -ne 0 ]; then
        print_warning "配置 Docker 镜像源需要 root 权限，跳过此步骤"
        return 0
    fi
    mkdir -p /etc/docker

    # 文件不存在：无需任何 JSON 工具，直接写入最小配置
    if [ ! -f "$config_file" ]; then
        printf '{\n  "registry-mirrors": ["%s"]\n}\n' "$DOCKER_MIRROR" > "$config_file"
        print_success "已写入 Docker 镜像源配置: $DOCKER_MIRROR"
        restart_docker_if_active
        return 0
    fi

    if check_command jq; then
        # 已恰为目标镜像源（忽略尾斜杠差异）→ 零写入零重启
        if jq -e --arg m "${DOCKER_MIRROR%/}" \
            '(.["registry-mirrors"] // []) | map(rtrimstr("/")) == [$m]' \
            "$config_file" > /dev/null 2>&1; then
            print_success "Docker 镜像源配置已就绪（$DOCKER_MIRROR）"
            return 0
        fi
        local tmp_json
        tmp_json=$(mktemp)
        if jq --arg m "$DOCKER_MIRROR" '.["registry-mirrors"] = [$m]' "$config_file" > "$tmp_json" 2>/dev/null; then
            mv "$tmp_json" "$config_file"
            print_success "Docker 镜像源已更新为 $DOCKER_MIRROR"
            restart_docker_if_active
            return 0
        fi
        rm -f "$tmp_json"
        print_error "解析 $config_file 失败（非法 JSON？），请手动检查"
        return 1
    fi

    if check_command python3; then
        # 退出码约定：0=已就绪 3=已更新 其它=失败（|| 捕获以兼容 set -e）
        local rc=0
        python3 - "$config_file" "$DOCKER_MIRROR" <<'PYEOF' || rc=$?
import json, sys
path, mirror = sys.argv[1], sys.argv[2]
cfg = json.load(open(path))
cur = [m.rstrip('/') for m in cfg.get('registry-mirrors', []) if isinstance(m, str)]
if cur == [mirror.rstrip('/')]:
    sys.exit(0)
cfg['registry-mirrors'] = [mirror]
json.dump(cfg, open(path, 'w'), indent=2, ensure_ascii=False)
sys.exit(3)
PYEOF
        case $rc in
            0) print_success "Docker 镜像源配置已就绪（$DOCKER_MIRROR）" ;;
            3) print_success "Docker 镜像源已更新为 $DOCKER_MIRROR"; restart_docker_if_active ;;
            *) print_error "解析 $config_file 失败（非法 JSON？），请手动检查"; return 1 ;;
        esac
        return 0
    fi

    print_warning "未安装 jq/python3 且 $config_file 已存在，跳过自动配置（请手动确认 registry-mirrors 含 $DOCKER_MIRROR）"
}

# 创建统一网络（已存在则跳过；FORCE_NETWORK_RECREATE=true 可强制重建）
create_network() {
    print_info "检查网络 easyaiot-network..."

    if docker network inspect easyaiot-network > /dev/null 2>&1; then
        if [ "${FORCE_NETWORK_RECREATE:-false}" != "true" ]; then
            return 0
        fi
        print_warning "FORCE_NETWORK_RECREATE=true：重建网络..."
        local containers
        containers=$(docker network inspect easyaiot-network --format '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null || echo "")
        for container in $containers; do
            docker network disconnect -f easyaiot-network "$container" 2>/dev/null || true
        done
        if ! docker network rm easyaiot-network 2>/dev/null; then
            print_error "旧网络删除失败，请确认无容器占用: docker network inspect easyaiot-network"
            return 1
        fi
    fi

    local create_output
    if create_output=$(docker network create easyaiot-network 2>&1); then
        print_success "网络 easyaiot-network 已创建"
    else
        echo "$create_output" | grep -qi "already exists" && return 0
        print_error "创建网络失败: $create_output"
        return 1
    fi
}

# 修复脚本换行符（CRLF → LF）并确保可执行位
fix_line_endings() {
    local script_file="$1"
    [ -f "$script_file" ] || return 1

    if grep -q $'\r' "$script_file" 2>/dev/null; then
        print_info "修复 $script_file 的换行符..."
        if ! sed -i 's/\r$//' "$script_file" 2>/dev/null; then
            local temp_file
            temp_file=$(mktemp)
            if tr -d '\r' < "$script_file" > "$temp_file" 2>/dev/null; then
                mv "$temp_file" "$script_file"
            else
                rm -f "$temp_file"
                print_warning "$script_file 换行符修复失败"
                return 1
            fi
        fi
    fi

    [ -x "$script_file" ] || chmod u+x "$script_file" 2>/dev/null || true
}

# 模块对应的安装脚本名（仅此一处差异：基础服务用 install_middleware_linux.sh）
module_install_script() {
    case "$1" in
        ".scripts/docker") echo "install_middleware_linux.sh" ;;
        *)                 echo "install_linux.sh" ;;
    esac
}

# 检查模块是否存在安装脚本
_module_has_install_script() {
    local _s="${PROJECT_ROOT}/${1}/$(module_install_script "$1")"
    [ -f "$_s" ]
}

# 执行模块命令（统一流程：定位脚本 -> 修换行符 -> 执行 -> 记录日志）
# 注：原版在基础模块的【任何】命令后固定 sleep 5（包括 stop/status/logs），
# 已移除——安装/重启/更新流程改在调用侧用 wait_for_base_services 做精确就绪轮询。
execute_module_command() {
    local module=$1
    local command=$2
    local module_name=${MODULE_NAMES[$module]}
    local install_file
    install_file=$(module_install_script "$module")

    if [ ! -d "$PROJECT_ROOT/$module" ]; then
        if [ "$module" = "TRANSFORM" ]; then
            print_info "未检测到 TRANSFORM 目录，跳过系统对接部署"
            return 0
        fi
        if [ "$module" = "PANEL" ]; then
            print_info "跳过运维控制台（PANEL）：$(panel_skip_deploy_reason)（runtime 无 PANEL 目录）"
            return 0
        fi
        print_warning "模块 $module 不存在，跳过"
        return 1
    fi
    cd "$PROJECT_ROOT/$module"

    if [ ! -f "$install_file" ]; then
        if [ "$module" = "TRANSFORM" ]; then
            print_info "未检测到 TRANSFORM/install_linux.sh，跳过系统对接部署"
            return 0
        fi
        if [ "$module" = "PANEL" ]; then
            print_info "跳过运维控制台（PANEL）：$(panel_skip_deploy_reason)（无 install_linux.sh）"
            return 0
        fi
        print_warning "模块 $module 没有 $install_file 文件，跳过"
        return 1
    fi

    fix_line_endings "$install_file"
    print_info "执行 $module_name: $command"

    local defer_agent_sync=0
    case "$module" in
        DEVICE|AI|VIDEO|WEB|APP|VISUALIZE|TRANSFORM) defer_agent_sync=1 ;;
    esac
    if [ "$defer_agent_sync" -eq 1 ]; then
        export EASYAIOT_DEFER_PLATFORM_AGENT_SYNC=1
    fi

    ensure_deploy_profile
    export EASYAIOT_DEPLOY_PROFILE
    export EASYAIOT_SKIP_PROFILE_PROMPT
    export EASYAIOT_SKIP_IMAGE_PROMPT
    export EASYAIOT_SKIP_BUILD

    # ⚠️ 失败判定必须取 PIPESTATUS[0]（子脚本退出码）：
    # 脚本未开 pipefail（全局开会让 `docker ps | grep -q` 类管道误报），
    # `if 子脚本 | tee` 取到的是 tee 的退出码（恒 0），曾导致所有模块失败都被报成"成功"。
    # 不加 || true：本函数所有调用点均处于 if/|| 守卫上下文，set -e 不会触发；
    # 若 tee 写盘失败（磁盘满），加 || true 反而会把 PIPESTATUS 冲成 0、掩盖模块失败。
    local rc
    bash "$install_file" "$command" 2>&1 | tee -a "$LOG_FILE"
    rc=${PIPESTATUS[0]}

    if [ "$defer_agent_sync" -eq 1 ]; then
        unset EASYAIOT_DEFER_PLATFORM_AGENT_SYNC
    fi

    if [ "$rc" -eq 0 ]; then
        print_success "$module_name: $command 执行成功"
        return 0
    else
        print_error "$module_name: $command 执行失败 (exit $rc)"
        return 1
    fi
}

# 等待服务就绪
wait_for_service() {
    local service_name=$1
    local port=$2
    local health_endpoint=$3
    local max_attempts=60
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        # 尝试多种方式检测服务
        if [ -n "$health_endpoint" ]; then
            # 使用健康检查端点
            if curl -s --connect-timeout 2 "http://localhost:$port$health_endpoint" > /dev/null 2>&1; then
                return 0
            fi
        else
            # 使用端口检测
            if command -v nc &> /dev/null && nc -z localhost $port 2>/dev/null; then
                return 0
            elif command -v timeout &> /dev/null && timeout 1 bash -c "cat < /dev/null > /dev/tcp/localhost/$port" 2>/dev/null; then
                return 0
            elif curl -s --connect-timeout 1 "http://localhost:$port" > /dev/null 2>&1; then
                return 0
            fi
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    return 1
}

# 验证服务健康状态
verify_service_health() {
    local module=$1
    local module_name=${MODULE_NAMES[$module]}
    local port=${MODULE_PORTS[$module]}
    local health_endpoint=${MODULE_HEALTH_ENDPOINTS[$module]}
    
    print_info "验证 $module_name (端口: $port)..."
    
    if wait_for_service "$module_name" "$port" "$health_endpoint"; then
        # 检查HTTP响应
        if [ -n "$health_endpoint" ]; then
            response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port$health_endpoint" 2>/dev/null || echo "000")
            if [ "$response" = "200" ] || [ "$response" = "000" ]; then
                print_success "$module_name 运行正常"
                return 0
            else
                print_warning "$module_name 响应异常 (HTTP $response)"
                return 1
            fi
        else
            print_success "$module_name 运行正常"
            return 0
        fi
    else
        print_error "$module_name 未就绪"
        return 1
    fi
}

# 安装所有服务
install_linux() {
    print_section "开始安装所有服务"

    select_deploy_profile_for_install
    export EASYAIOT_INSTALL_SCRIPT="${EASYAIOT_INSTALL_SCRIPT:-.scripts/docker/install_linux.sh}"
    if ! runtime_images_acquire; then
        print_error "预构建镜像获取失败，已中止安装"
        return 1
    fi

    check_docker "$@"
    check_docker_compose
    configure_docker_mirror
    prepare_runtime_environment
    create_network

    # 若已拉取预构建镜像，业务模块跳过 docker build
    local _skip_build=0
    if runtime_images_should_skip_build; then
        _skip_build=1
    else
        if runtime_is_source_free_runtime; then
            print_error "当前为 PANEL 无源码 runtime，禁止本地 docker build"
            print_error "请先确保预构建镜像拉取成功后再安装（bash .scripts/docker/install_linux.sh pull）"
            return 1
        fi
        print_info "将进行本地构建（各模块 docker build，耗时较长）"
    fi
    
    local success_count=0
    local total_count
    total_count=$(_count_installable_modules)
    local -a failed_modules=()
    local -a succeeded_modules=()
    
    for module in "${MODULES[@]}"; do
        if ! module_enabled_for_deploy_profile "$module"; then
            if [ "$module" = "PANEL" ]; then
                print_info "跳过运维控制台（PANEL）：$(panel_skip_deploy_reason)"
            else
                print_info "跳过 ${MODULE_NAMES[$module]}（当前部署形态 ${EASYAIOT_DEPLOY_PROFILE} 不包含此模块）"
            fi
            continue
        fi
        print_section "安装 ${MODULE_NAMES[$module]}"

        # 检查模块是否存在安装脚本，无安装脚本的模块直接跳过
        local _inst_script
        _inst_script="${PROJECT_ROOT}/${module}/$(module_install_script "$module")"
        if [ ! -f "$_inst_script" ]; then
            print_info "${MODULE_NAMES[$module]} 无需安装（无安装脚本），跳过"
            continue
        fi

        if [ "$_skip_build" -eq 1 ] && [ "$module" != ".scripts/docker" ]; then
            print_info "镜像已从远程拉取，跳过 docker build，直接启动 ${MODULE_NAMES[$module]}"
        fi
        if execute_module_command "$module" "install"; then
            success_count=$((success_count + 1))
            succeeded_modules+=("${MODULE_NAMES[$module]}")
            # 基础服务装完后精确等待 PostgreSQL/Nacos/Redis 就绪（取代原固定 sleep 5）
            if [ "$module" = ".scripts/docker" ]; then
                wait_for_base_services
            fi
            # DEVICE 装完后等待 iot-gateway 就绪，避免 WEB 启动时 gateway 未就绪导致 /dev-api/ 503
            if [ "$module" = "DEVICE" ]; then
                wait_for_device_gateway || print_warning "iot-gateway 未就绪，WEB 服务 /dev-api/ 接口可能返回 503（待 gateway 就绪后重启 WEB 即可）"
            fi
        else
            print_error "${MODULE_NAMES[$module]} 安装失败"
            failed_modules+=("${MODULE_NAMES[$module]}")
        fi
        echo ""
    done
    
    print_section "安装完成"
    echo "成功安装: $success_count / $total_count 个模块"
    
    if [ ${#succeeded_modules[@]} -gt 0 ]; then
        echo "  已成功: ${succeeded_modules[*]}"
    fi
    if [ ${#failed_modules[@]} -gt 0 ]; then
        echo "  已失败: ${failed_modules[*]}"
    fi
    
    if [ $success_count -eq $total_count ]; then
        print_success "所有模块安装成功！"
        ensure_platform_agent_after_stack
        ensure_mqtt_demo_after_stack
        ensure_industrial_demo_after_stack
    else
        echo ""
        print_warning "部分模块安装失败，请检查日志"
        echo ""
        print_info "诊断建议："
        for failed in "${failed_modules[@]}"; do
            case "$failed" in
                "基础服务")
                    print_info "  - 基础服务：检查 Nacos/PostgreSQL/Redis 等中间件容器是否正常启动"
                    print_info "    docker ps --filter 'name=nacos|postgres|redis'"
                    ;;
                "Device服务")
                    print_info "  - Device服务：检查 Maven 编译是否成功、JAR 包是否生成"
                    print_info "    ls DEVICE/target/jars/"
                    print_info "    检查日志: cat ${LOG_DIR}/install_linux_*.log | grep -i 'error\|failed\|失败'"
                    ;;
                "AI服务")
                    print_info "  - AI服务：检查 PyTorch 镜像拉取和 Python 依赖安装"
                    print_info "    docker images | grep ai-service"
                    ;;
                "Video服务")
                    print_info "  - Video服务：检查视频服务镜像构建"
                    print_info "    docker images | grep video-service"
                    ;;
                "Web前端服务")
                    print_info "  - Web前端服务：检查 pnpm install/build 和 nginx 镜像构建"
                    print_info "    docker images | grep web-service"
                    print_info "    cat WEB/docker-build-logs/pnpm-build.log | tail -50"
                    ;;
            esac
        done
        echo ""
        print_info "完整日志文件: ${LOG_FILE}"
        exit 1
    fi
}

# 通用容器就绪等待：wait_for_container_ready <显示名> <最大次数> <间隔秒> <检测命令...>
# 检测命令退出码 0 即就绪；短间隔精确轮询，就绪即刻返回（无固定长 sleep）
wait_for_container_ready() {
    local name=$1 max_attempts=$2 interval=$3
    shift 3
    local attempt=0
    local elapsed=0
    local progress_interval=10  # 每 10 次检测输出一次友好提示
    print_info "等待 ${name} 服务就绪..."
    while [ $attempt -lt $max_attempts ]; do
        if "$@" > /dev/null 2>&1; then
            print_success "${name} 服务已就绪"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep "$interval"
        elapsed=$((elapsed + interval))
        # 每 progress_interval 次检测输出友好提示，让用户知道没有卡死
        if [ $((attempt % progress_interval)) -eq 0 ] && [ $attempt -lt $max_attempts ]; then
            print_info "  ${name} 仍在启动中...（已等待 ${elapsed}s，将继续等待）"
        fi
    done
    print_warning "${name} 服务未在预期时间内就绪（已等待 ${elapsed}s），继续执行..."
    return 1
}

# Nacos / MinIO：宿主机端口映射滞后时，容器内探测或 Docker healthy 亦算就绪
_check_nacos_ready() {
    curl -sf --connect-timeout 2 --max-time 5 "http://127.0.0.1:8848/nacos/actuator/health" >/dev/null 2>&1 && return 0
    docker exec nacos-server curl -sf --connect-timeout 2 --max-time 5 \
        "http://127.0.0.1:8848/nacos/actuator/health" >/dev/null 2>&1 && return 0
    [ "$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' nacos-server 2>/dev/null || echo none)" = "healthy" ]
}

_check_minio_ready() {
    curl -sf --connect-timeout 2 --max-time 5 "http://127.0.0.1:9000/minio/health/live" >/dev/null 2>&1 && return 0
    docker exec minio-server curl -sf --connect-timeout 2 --max-time 5 \
        "http://127.0.0.1:9000/minio/health/live" >/dev/null 2>&1 && return 0
    [ "$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' minio-server 2>/dev/null || echo none)" = "healthy" ]
}

# 仅当容器在运行时才等待（容器未启动直接跳过）
container_running() {
    docker ps --filter "name=$1" --format "{{.Names}}" | grep -q "$1"
}

# 容器是否存在（含 Created 状态，即 compose up 创建了但 OCI 运行时未能启动）
container_exists() {
    docker ps -a --filter "name=$1" --format "{{.Names}}" | grep -q "$1"
}

# 获取容器状态字符串（running / created / exited / 空）
container_status() {
    docker inspect --format '{{.State.Status}}' "$1" 2>/dev/null || echo ""
}

# 自动修复 Created 状态的容器（compose up 创建但 runc 启动失败，如 OCI /dev/null 错误）。
# 先尝试 docker start，失败则通过 compose 重建（保留完整配置）。
_repair_created_containers() {
    local names n status rc=0 _svc _compose_file _up_log _up_rc _retry _delay
    names=$(docker ps -a --filter "status=created" --format '{{.Names}}' 2>/dev/null || true)
    [ -z "$names" ] && return 0

    for n in $names; do
        status=$(container_status "$n")
        [ "$status" = "created" ] || continue
        print_warning "容器 $n 处于 Created 状态，尝试修复..."

        # 策略1：直接 docker start
        if docker start "$n" >/dev/null 2>&1; then
            print_success "容器 $n 已重新启动"
            continue
        fi

        # 策略2：通过 compose 重建
        _svc=$(docker inspect --format '{{index .Config.Labels "com.docker.compose.service"}}' "$n" 2>/dev/null || echo "")
        _compose_file=$(docker inspect --format '{{index .Config.Labels "com.docker.compose.file"}}' "$n" 2>/dev/null || echo "")
        if [ -n "$_svc" ] && [ -n "$_compose_file" ] && [ -f "$_compose_file" ]; then
            print_warning "通过 compose 重建 $n ($_svc)..."
            docker rm -f "$n" >/dev/null 2>&1 || true
            sleep 1
            _up_log=$(mktemp)
            docker compose -f "$_compose_file" up -d "$_svc" > "$_up_log" 2>&1 || true
            cat "$_up_log" >> "${LOG_FILE:-/dev/null}" 2>/dev/null || true
            rm -f "$_up_log"

            sleep 2
            if docker ps --filter "name=$n" --filter "status=running" --format '{{.Names}}' 2>/dev/null | grep -q "$n"; then
                print_success "容器 $n ($_svc) 已重建并运行"
                continue
            fi
        fi

        print_error "容器 $n 修复失败"
        rc=1
    done
    return $rc
}

# 等待基础服务就绪（PostgreSQL / Nacos / Redis）
# 增强：容器 Created 但未 Running 时自动尝试修复，避免静默失败导致后续业务服务 DNS 解析失败
wait_for_base_services() {
    print_info "等待基础服务就绪..."

    # 第一步：修复所有 Created 状态的容器（如 OCI /dev/null 导致的启动失败）
    _repair_created_containers || print_warning "部分 Created 容器未能自动修复，基础服务可能不可用"

    # 第二步：对每个关键基础服务，确认 Running 后才做健康检查
    local _redis_ok=false _pg_ok=false _nacos_ok=false

    if container_exists postgres-server; then
        if container_running postgres-server; then
            wait_for_container_ready "PostgreSQL" 180 2 docker exec postgres-server pg_isready -U postgres || true
            wait_for_container_ready "PostgreSQL (查询就绪)" 180 2 \
                bash -c 'docker exec postgres-server psql -U postgres -d postgres -tAc "SELECT 1" >/dev/null 2>&1 && [ "$(docker exec postgres-server psql -U postgres -d postgres -tAc "SELECT pg_is_in_recovery();" 2>/dev/null)" = "f" ]' || true
            _pg_ok=true
        else
            print_error "PostgreSQL 容器已创建但未运行，请检查: docker logs postgres-server"
        fi
    fi

    if container_exists nacos-server; then
        if container_running nacos-server; then
            wait_for_container_ready "Nacos" 90 2 _check_nacos_ready || true
            _nacos_ok=true
        else
            print_error "Nacos 容器已创建但未运行，请检查: docker logs nacos-server"
        fi
    fi

    if container_exists redis-server; then
        if container_running redis-server; then
            wait_for_container_ready "Redis" 30 1 docker exec redis-server redis-cli ping || true
            _redis_ok=true
        else
            print_error "Redis 容器已创建但未运行！后续业务服务将无法解析 'Redis' 主机名"
            print_info "请检查: docker logs redis-server"
            print_info "常见原因：rootless Docker 下 runc 无法创建 /dev/null（OCI 错误）"
        fi
    else
        print_warning "Redis 容器不存在，业务服务将无法连接 Redis"
    fi

    if container_exists minio-server; then
        if container_running minio-server; then
            wait_for_container_ready "MinIO" 60 2 _check_minio_ready || true
        else
            print_error "MinIO 容器已创建但未运行！WEB 服务 nginx 将无法解析 'MinIO' 主机名"
            print_info "请检查: docker logs minio-server"
        fi
    else
        print_warning "MinIO 容器不存在，WEB 服务对 /api/v1/buckets 代理将不可用"
    fi

    # 关键基础服务缺失时给出明确警告（不中断，让用户看到后续错误的完整上下文）
    if ! $_redis_ok || ! $_pg_ok || ! $_nacos_ok; then
        print_warning "部分基础服务未就绪，后续业务模块可能启动失败"
    fi
}

# 等待 DEVICE 模块的 iot-gateway 就绪（仅非 mini 形态）
# 必须在 WEB 模块启动前调用，否则 nginx 代理到 gateway:48080 将返回 502→503
_check_iot_gateway_ready() {
    # 只探 health（根路径常 404，curl -f 会失败）；加 max-time 避免半开连接挂死
    curl -sf --connect-timeout 2 --max-time 5 \
        "http://127.0.0.1:48080/actuator/health" >/dev/null 2>&1 && return 0
    # host 网络下 docker exec 与宿主机等价，但可绕过 localhost→::1 解析问题
    docker exec iot-gateway curl -sf --connect-timeout 2 --max-time 5 \
        "http://127.0.0.1:48080/actuator/health" >/dev/null 2>&1 && return 0
    [ "$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' iot-gateway 2>/dev/null || echo none)" = "healthy" ]
}

wait_for_device_gateway() {
    # mini 形态无 iot-gateway，直连 iot-system，无需等待
    if is_mini_deploy_profile; then
        print_info "当前为 mini 部署形态，跳过 iot-gateway 就绪检查（直连 iot-system:48099）"
        return 0
    fi

    print_info "等待 iot-gateway 就绪（Gateway API 网关，端口 48080）..."

    # 检查容器是否存在
    if ! container_exists iot-gateway 2>/dev/null; then
        print_warning "iot-gateway 容器不存在，API 请求将返回 503"
        print_info "可能原因：DEVICE 模块未安装或部署形态不包含 iot-gateway"
        print_info "手动检查: docker ps -a | grep iot-gateway"
        return 1
    fi

    # 等待容器 Running
    if ! container_running iot-gateway 2>/dev/null; then
        print_warning "iot-gateway 容器未运行，尝试等待启动..."
        local _gw_wait=0
        while [ $_gw_wait -lt 30 ]; do
            if container_running iot-gateway 2>/dev/null; then
                break
            fi
            sleep 1
            _gw_wait=$((_gw_wait + 1))
        done
        if ! container_running iot-gateway 2>/dev/null; then
            print_error "iot-gateway 容器未能启动，请检查日志: docker logs iot-gateway"
            return 1
        fi
    fi

    # 等待健康检查通过（最长约 180s；Java 冷启动可能较慢）
    local _gw_port_ready=0
    local _gw_log_ready=0
    local _poll_attempt=0
    local _poll_elapsed=0
    local _poll_max="${IOT_GATEWAY_READY_MAX_ATTEMPTS:-180}"
    local _poll_interval=1
    print_info "等待 iot-gateway (48080) 服务就绪..."
    while [ $_poll_attempt -lt $_poll_max ]; do
        if _check_iot_gateway_ready; then
            _gw_port_ready=1
            break
        fi
        # 检测 Spring Boot 是否已打印启动成功（提示用户只差端口绑定这一步了）
        if [ $_gw_log_ready -eq 0 ] && docker logs iot-gateway --tail 30 2>/dev/null | grep -qE '(项目启动成功|Started .* in |JVM running for)'; then
            _gw_log_ready=1
            print_info "  Spring Boot 已初始化完成，正在等待健康检查通过..."
        fi
        _poll_attempt=$((_poll_attempt + 1))
        sleep "$_poll_interval"
        _poll_elapsed=$((_poll_elapsed + _poll_interval))
        # 每 10 秒输出友好进度提示
        if [ $((_poll_attempt % 10)) -eq 0 ] && [ $_poll_attempt -lt $_poll_max ]; then
            local _health
            _health=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' iot-gateway 2>/dev/null || echo unknown)
            print_info "  iot-gateway 仍在启动中...（已等待 ${_poll_elapsed}s，健康: ${_health}）"
        fi
    done

    if [ $_gw_port_ready -eq 1 ]; then
        print_success "iot-gateway 已就绪（端口 48080 响应正常），WEB 服务可以安全启动"
    else
        print_warning "iot-gateway 在 ${_poll_elapsed}s 内未就绪，WEB 服务启动后 /dev-api/ 可能返回 503"
        print_info "手动检查: curl -v http://127.0.0.1:48080/actuator/health"
        print_info "查看日志: docker logs iot-gateway --tail 50"
        # 如果日志显示启动成功但端口不通，给出明确提示
        if docker logs iot-gateway --tail 20 2>/dev/null | grep -qE '(项目启动成功|Started .* in )'; then
            print_warning "Spring Boot 日志显示启动成功，但健康检查仍未通过，请检查端口 48080 / 防火墙"
        fi
        return 1
    fi
}

# 业务模块清单（MODULES 去掉基础服务，并按部署形态过滤），结果写入全局数组 BIZ_MODULES
# PANEL 纳入启停/更新；stop_runtime_modules 单独排除（build-runtime 清理不关控制台）
collect_biz_modules() {
    ensure_deploy_profile
    BIZ_MODULES=()
    local module
    for module in "${MODULES[@]}"; do
        [ "$module" = ".scripts/docker" ] && continue
        module_enabled_for_deploy_profile "$module" || continue
        BIZ_MODULES+=("$module")
    done
}

# 并行执行一批模块命令：run_modules_parallel <command> <module...>
# 各模块在子 shell 中执行、输出写入独立日志（避免终端交叉错行），
# 全部结束后按模块顺序回放结果，失败的展示日志尾部。返回失败模块数。
run_modules_parallel() {
    local command=$1; shift
    local pids=() logs=() mods=()
    local module
    for module in "$@"; do
        local mlog="${LOG_DIR}/${command}_$(echo "$module" | tr '/' '_')_$$.log"
        : > "$mlog"  # 截断可能残留的同名旧文件（$$ 复用场景），避免 tee -a 回放陈旧内容
        ( LOG_FILE="$mlog"; execute_module_command "$module" "$command" > /dev/null 2>&1 ) &
        pids+=($!); logs+=("$mlog"); mods+=("$module")
    done
    # Ctrl-C/终止时清理临时日志，避免 logs/ 目录残留
    trap 'rm -f "${logs[@]}" 2>/dev/null' INT TERM

    local i fail=0
    for i in "${!pids[@]}"; do
        if wait "${pids[$i]}"; then
            print_success "${MODULE_NAMES[${mods[$i]}]}: $command 完成"
        else
            fail=$((fail + 1))
            print_error "${MODULE_NAMES[${mods[$i]}]}: $command 失败，日志尾部："
            tail -n 40 "${logs[$i]}" 2>/dev/null || true
        fi
        # 回放进主日志后清理临时文件
        cat "${logs[$i]}" >> "$LOG_FILE" 2>/dev/null || true
        rm -f "${logs[$i]}"
    done
    trap - INT TERM
    return $fail
}

# 启动所有服务
start_all() {
    print_section "启动所有服务"
    
    ensure_deploy_profile
    print_info "部署形态: $(_deploy_profile_desc) (EASYAIOT_DEPLOY_PROFILE=${EASYAIOT_DEPLOY_PROFILE})"
    check_docker "$@"
    check_docker_compose
    configure_docker_mirror
    prepare_runtime_environment
    create_network
    
    # 先启动基础服务（.scripts/docker）
    print_section "启动基础服务"
    if ! execute_module_command ".scripts/docker" "start"; then
        print_error "基础服务启动失败，中止后续模块启动"
        return 1
    fi
    echo ""

    # 等待基础服务就绪
    wait_for_base_services
    echo ""

    # 再启动其他服务。DEVICE/AI/VIDEO/WEB 启动期互不依赖（各自只连基础服务），
    # 默认并行启动（仅 compose up，无构建负载）；PARALLEL_MODULES=false 可回退串行。
    collect_biz_modules
    if [ "${PARALLEL_MODULES:-true}" = "true" ]; then
        print_info "并行启动业务模块: ${BIZ_MODULES[*]}（PARALLEL_MODULES=false 可回退串行）"
        run_modules_parallel "start" "${BIZ_MODULES[@]}" || print_warning "部分模块启动失败，详见上方日志"
    else
        for module in "${BIZ_MODULES[@]}"; do
            execute_module_command "$module" "start" || print_warning "${MODULE_NAMES[$module]} 启动失败，继续其余模块"
            # DEVICE 启动后等待 gateway 就绪，确保后续 WEB 启动时 /dev-api/ 可达
            if [ "$module" = "DEVICE" ]; then
                wait_for_device_gateway || print_warning "iot-gateway 未就绪，WEB 服务 /dev-api/ 接口可能返回 503"
            fi
            echo ""
        done
    fi

    # 并行启动后仍需确保 gateway 就绪（DEVICE/WEB 同时启动时 WEB nginx 可能比 gateway 先就绪）
    if module_enabled_for_deploy_profile "DEVICE" 2>/dev/null; then
        wait_for_device_gateway || print_warning "iot-gateway 未就绪，WEB 服务 /dev-api/ 接口可能返回 503（待 gateway 就绪后重启 WEB 即可）"
    fi
    
    print_success "所有服务启动完成"
    ensure_platform_agent_after_stack
    ensure_mqtt_demo_after_stack
    ensure_industrial_demo_after_stack
}

# 停止所有服务
stop_all() {
    print_section "停止所有服务"
    
    check_docker "$@"
    check_docker_compose

    stop_industrial_demo_before_stack
    
    # 逆序停止（尽力而为：单个失败不阻断其余模块停止）
    for ((idx=${#MODULES[@]}-1 ; idx>=0 ; idx--)); do
        execute_module_command "${MODULES[idx]}" "stop" || print_warning "${MODULE_NAMES[${MODULES[idx]}]} 停止失败，继续其余模块"
        echo ""
    done

    print_success "所有服务已停止"
}

# 仅停止业务运行时模块（不含 Nacos/PostgreSQL 等中间件），便于释放 build-runtime 镜像占用
stop_runtime_modules() {
    print_section "停止业务运行时服务（保留中间件）"

    check_docker
    check_docker_compose

    collect_biz_modules
    local -a stop_modules=("${BIZ_MODULES[@]}")
    local idx module
    for ((idx=${#stop_modules[@]}-1 ; idx>=0 ; idx--)); do
        module="${stop_modules[$idx]}"
        # build-runtime 清理业务镜像时保留运维控制台
        [ "$module" = "PANEL" ] && continue
        execute_module_command "$module" "stop" || print_warning "${MODULE_NAMES[$module]} 停止失败，继续其余模块"
        echo ""
    done

    # PANEL 不在 MODULES 列表中，单独停止以便释放 easyaiot/panel 镜像
    if [ -f "${PROJECT_ROOT}/PANEL/install.sh" ] && [ "${EASYAIOT_ENABLE_PANEL:-1}" != "0" ]; then
        print_info "停止 PANEL 独立运维控制台..."
        bash "${PROJECT_ROOT}/PANEL/install.sh" stop || print_warning "PANEL 停止失败，继续清理"
        echo ""
    fi

    print_success "业务运行时服务已停止（中间件未停止）"
}

# 重启所有服务
restart_all() {
    print_section "重启所有服务"
    
    ensure_deploy_profile
    print_info "部署形态: $(_deploy_profile_desc) (EASYAIOT_DEPLOY_PROFILE=${EASYAIOT_DEPLOY_PROFILE})"
    check_docker "$@"
    check_docker_compose
    configure_docker_mirror
    prepare_runtime_environment
    create_network
    
    for module in "${MODULES[@]}"; do
        if ! module_enabled_for_deploy_profile "$module"; then
            continue
        fi
        if execute_module_command "$module" "restart"; then
            # 基础服务重启后精确等待就绪，再重启依赖它的业务模块（取代原固定 sleep 5）
            if [ "$module" = ".scripts/docker" ]; then
                wait_for_base_services
            fi
            # DEVICE 重启后等待 gateway 就绪，确保后续模块（WEB）的 /dev-api/ 可达
            if [ "$module" = "DEVICE" ]; then
                wait_for_device_gateway || print_warning "iot-gateway 未就绪，WEB 服务 /dev-api/ 接口可能返回 503"
            fi
        else
            print_warning "${MODULE_NAMES[$module]} 重启失败，继续其余模块"
        fi
        echo ""
    done

    print_success "所有服务重启完成"
    ensure_platform_agent_after_stack
    ensure_mqtt_demo_after_stack
    ensure_industrial_demo_after_stack
}

# 查看所有服务状态
status_all() {
    print_section "所有服务状态"
    
    check_docker "$@"
    check_docker_compose
    
    for module in "${MODULES[@]}"; do
        print_section "${MODULE_NAMES[$module]} 状态"
        execute_module_command "$module" "status" || true
        echo ""
    done
}

# 查看日志
# 参数改名 target_module：原版 local module 与下方 for module 循环变量同名，
# 循环会覆盖参数值（遮蔽），靠"恰好不再使用"才没出错，易引入回归。
view_logs() {
    local target_module=${1:-""}

    check_docker
    check_docker_compose

    if [ -z "$target_module" ]; then
        print_info "查看所有服务日志..."
        local module
        for module in "${MODULES[@]}"; do
            print_section "${MODULE_NAMES[$module]} 日志"
            execute_module_command "$module" "logs" || true
            echo ""
        done
    else
        print_info "查看 $target_module 服务日志..."
        execute_module_command "$target_module" "logs" || true
    fi
}

# 构建所有镜像
# 各模块构建互不依赖，PARALLEL_BUILD=true 时并行执行：
#   - 每个模块在子 shell 中构建，输出写入独立日志（避免终端交叉错行）
#   - 全部结束后按模块顺序回放结果，失败的展示日志尾部
# 默认串行：Java/Node/Python 构建内存峰值高，小内存服务器并行易 OOM，由使用者显式选择。
build_all() {
    print_section "构建所有镜像"

    check_docker "$@"
    check_docker_compose

    if [ "${PARALLEL_BUILD:-false}" = "true" ]; then
        print_info "并行构建模式（PARALLEL_BUILD=true），各模块日志将在结束后汇总展示"
        local active_modules=()
        local module
        for module in "${MODULES[@]}"; do
            module_enabled_for_deploy_profile "$module" && active_modules+=("$module")
        done
        if ! run_modules_parallel "build" "${active_modules[@]}"; then
            print_error "部分模块构建失败，请检查日志: $LOG_FILE"
            exit 1
        fi
    else
        local module
        for module in "${MODULES[@]}"; do
            module_enabled_for_deploy_profile "$module" || continue
            execute_module_command "$module" "build" || print_warning "${MODULE_NAMES[$module]} 构建失败，继续其余模块"
            echo ""
        done
    fi

    print_success "所有镜像构建完成"
}

# 从远程仓库拉取预构建运行时镜像（交互式，默认 full）
pull_runtime_images() {
    check_docker "$@"
    runtime_images_prepare_pull_interactive
    runtime_images_export_for_invoke
    runtime_images_invoke pull || exit 1
    export EASYAIOT_SKIP_BUILD=1
    export EASYAIOT_SKIP_IMAGE_PROMPT=1
}

# 构建并可选推送运行时镜像到远程仓库（交互式；第二参数可指定单模块）
build_runtime_images() {
    check_docker "$@"
    runtime_apply_build_module_arg "${2:-}" || exit 1
    runtime_images_prepare_build_interactive
    runtime_images_export_for_invoke
    runtime_images_invoke build || exit 1
}


# 清理所有服务
clean_all() {
    print_warning "这将删除所有容器、镜像和数据卷，确定要继续吗？(y/N)"
    # 非交互 stdin(EOF) 下 read 返回非 0，set -e 会无声退出——兜底为空(等同取消)
    read -r response || response=""
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_section "清理所有服务"
        
        check_docker "$@"
        check_docker_compose
        
        # 逆序清理（尽力而为：单个失败不阻断其余模块清理）
        for ((idx=${#MODULES[@]}-1 ; idx>=0 ; idx--)); do
            execute_module_command "${MODULES[idx]}" "clean" || print_warning "${MODULE_NAMES[${MODULES[idx]}]} 清理失败，继续其余模块"
            echo ""
        done
        
        # 清理网络
        print_info "清理网络..."
        docker network rm easyaiot-network 2>/dev/null || true
        
        print_success "清理完成"
    else
        print_info "已取消清理操作"
    fi
}

# 清理 build-runtime 构建产物：先停止服务，再调用 cleanup_build_runtime.sh
clean_build_runtime() {
    shift
    local -a cleanup_args=("$@")

    print_section "清理 build-runtime 构建产物"
    check_docker

    print_info "步骤 1/2: 停止业务运行时服务（保留中间件）..."
    stop_runtime_modules

    print_info "步骤 2/2: 清理 build-runtime 镜像与构建缓存..."
    if [ "${EASYAIOT_FROM_MENU:-0}" = "1" ] && [ ${#cleanup_args[@]} -eq 0 ]; then
        bash "${SCRIPT_DIR}/cleanup_build_runtime.sh"
    elif [ ${#cleanup_args[@]} -eq 0 ]; then
        bash "${SCRIPT_DIR}/cleanup_build_runtime.sh" -y
    else
        bash "${SCRIPT_DIR}/cleanup_build_runtime.sh" "${cleanup_args[@]}"
    fi
}

# 更新所有服务
update_all() {
    print_section "更新所有服务"
    
    ensure_deploy_profile
    print_info "部署形态: $(_deploy_profile_desc) (EASYAIOT_DEPLOY_PROFILE=${EASYAIOT_DEPLOY_PROFILE})"
    check_docker "$@"
    check_docker_compose
    configure_docker_mirror
    export EASYAIOT_INSTALL_SCRIPT="${EASYAIOT_INSTALL_SCRIPT:-.scripts/docker/install_linux.sh}"
    runtime_images_acquire_for_update
    prepare_runtime_environment
    create_network

    if runtime_images_should_skip_build; then
        print_info "镜像已从远程拉取，业务模块将跳过 docker build"
    else
        print_info "将进行本地重建更新（各模块 docker build，耗时较长）"
    fi
    
    # 基础服务先更新并等就绪，业务模块随后
    if execute_module_command ".scripts/docker" "update"; then
        wait_for_base_services
    else
        print_warning "${MODULE_NAMES[".scripts/docker"]} 更新失败，继续其余模块"
    fi
    echo ""

    # 业务模块更新：update 可能包含重建镜像（构建内存峰值高），默认串行；
    # 机器内存充裕时可 PARALLEL_MODULES=true 并行提速
    collect_biz_modules
    if [ "${PARALLEL_MODULES:-false}" = "true" ]; then
        print_info "并行更新业务模块: ${BIZ_MODULES[*]}"
        run_modules_parallel "update" "${BIZ_MODULES[@]}" || print_warning "部分模块更新失败，详见上方日志"
    else
        for module in "${BIZ_MODULES[@]}"; do
            execute_module_command "$module" "update" || print_warning "${MODULE_NAMES[$module]} 更新失败，继续其余模块"
            # DEVICE 更新后等待 gateway 就绪，确保后续 WEB 更新时 /dev-api/ 可达
            if [ "$module" = "DEVICE" ]; then
                wait_for_device_gateway || print_warning "iot-gateway 未就绪，WEB 服务 /dev-api/ 接口可能返回 503"
            fi
            echo ""
        done
    fi

    # 并行更新后仍需确保 gateway 就绪
    if module_enabled_for_deploy_profile "DEVICE" 2>/dev/null; then
        wait_for_device_gateway || print_warning "iot-gateway 未就绪，/dev-api/ 接口可能返回 503（待 gateway 就绪后重启 WEB 即可）"
    fi

    print_success "所有服务更新完成"
    ensure_platform_agent_after_stack
    ensure_mqtt_demo_after_stack
    ensure_industrial_demo_after_stack
}

# 验证所有服务
verify_all() {
    print_section "验证所有服务"
    
    check_docker "$@"
    
    local success_count=0
    local total_count
    total_count=$(_count_verifiable_modules)
    local failed_modules=()
    
    for module in "${MODULES[@]}"; do
        module_enabled_for_deploy_profile "$module" || continue
        if verify_service_health "$module"; then
            success_count=$((success_count + 1))
        else
            failed_modules+=("${MODULE_NAMES[$module]}")
        fi
        echo ""
    done
    
    print_section "验证结果"
    echo "成功: ${GREEN}$success_count${NC} / $total_count"
    
    if [ $success_count -eq $total_count ]; then
        print_success "所有服务运行正常！"
        echo ""
        echo -e "${GREEN}服务访问地址:${NC}"
        echo -e "  基础服务 (Nacos):     http://localhost:8848/nacos"
        echo -e "  基础服务 (MinIO):     http://localhost:9000 (API), http://localhost:9001 (Console)"
        echo -e "  基础服务 (Milvus):    http://localhost:9091 (Health), localhost:19530 (gRPC)"
        echo -e "  Device服务 (Gateway):  http://localhost:48080"
        echo -e "  AI服务:                http://localhost:5000"
        echo -e "  Video服务:             http://localhost:6000"
        echo -e "  Web前端:               http://localhost:8888"
        if module_enabled_for_deploy_profile APP; then
            echo -e "  App移动端H5:           http://localhost:9010"
        fi
        if module_enabled_for_deploy_profile VISUALIZE; then
            echo -e "  可视化编辑器:           http://localhost:8002"
        fi
        if module_enabled_for_deploy_profile TRANSFORM; then
            echo -e "  系统对接 (TRANSFORM):   http://localhost:48096"
        fi
        if module_enabled_for_deploy_profile PANEL; then
            echo -e "  运维控制台 (PANEL):     http://localhost:9200"
        fi
        echo ""
        return 0
    else
        print_warning "部分服务未就绪:"
        for failed in "${failed_modules[@]}"; do
            echo -e "  ${RED}✗ $failed${NC}"
        done
        echo ""
        print_info "查看日志: ./install_linux.sh logs"
        return 1
    fi
}

# 检查 Docker 和 Docker Compose 安装状态
check_environment() {
    print_section "检查运行环境"
    
    echo ""
    print_info "=== 检查 Docker ==="
    if check_command docker; then
        local docker_version=$(docker --version 2>/dev/null || echo "未知版本")
        print_success "Docker 已安装: $docker_version"
        
        # 检查 Docker 服务状态
        if systemctl is-active --quiet docker.service 2>/dev/null; then
            print_info "Docker 服务状态: 运行中"
        elif systemctl is-enabled --quiet docker.service 2>/dev/null; then
            print_warning "Docker 服务已启用但未运行"
        else
            print_warning "Docker 服务未启用"
        fi
        
        # 检查 Docker daemon 是否可访问
        if docker info &> /dev/null; then
            print_success "Docker daemon 可访问"
            
            # 显示 Docker 信息
            local docker_root=$(docker info 2>/dev/null | grep "Docker Root Dir" | awk '{print $4}' || echo "未知")
            print_info "Docker 根目录: $docker_root"
        else
            local error_msg=$(docker info 2>&1)
            if echo "$error_msg" | grep -qi "permission denied"; then
                print_error "Docker daemon 权限不足"
            elif echo "$error_msg" | grep -qi "Is the docker daemon running"; then
                print_error "Docker daemon 未运行"
            else
                print_error "无法连接到 Docker daemon"
            fi
        fi
    else
        print_error "Docker 未安装"
    fi
    
    echo ""
    print_info "=== 检查 Docker Compose ==="
    if detect_compose; then
        if [ -n "$COMPOSE_V1_VERSION" ]; then
            print_success "Docker Compose v1 已安装: $COMPOSE_V1_VERSION"
        fi
        if [ -n "$COMPOSE_V2_VERSION" ]; then
            print_success "Docker Compose v2 已安装: $COMPOSE_V2_VERSION"
        fi
    else
        print_error "Docker Compose 未安装"
    fi
    
    echo ""
    print_info "=== 系统信息 ==="
    print_info "操作系统: $(uname -s) $(uname -r)"
    print_info "架构: $(uname -m)"
    print_info "用户: $(whoami)"
    
    echo ""
    print_section "检查完成"
}

# 显示帮助信息
show_help() {
    echo "EasyAIoT 统一安装脚本"
    echo ""
    echo "使用方法:"
    echo "  ./install_linux.sh                 - 打开交互式引导（推荐新手）"
    echo "  ./install_linux.sh menu            - 同上"
    echo "  ./install_linux.sh [命令] [模块]"
    echo ""
    echo "交互引导两层结构:"
    echo "  1) 部署 — 安装/启停/更新/状态/日志等"
    echo "  2) 分析 — 日志合并/磁盘占用/健康检查等"
    echo "  3) 官网 — SITE 官方网站独立部署"
    echo ""
    echo "可用命令:"
    echo "  install         - 安装并启动所有服务（首次运行）"
    echo "  start           - 启动所有服务"
    echo "  stop            - 停止所有服务"
    echo "  restart         - 重启所有服务"
    echo "  status          - 查看所有服务状态"
    echo "  logs            - 查看所有服务日志"
    echo "  logs [模块]     - 查看指定模块日志"
    echo "  build           - 重新构建所有镜像（各模块本地构建）"
    echo "  build-runtime [模块] - 构建/推送运行时镜像（推送成功后删本地镜像；可选 DEVICE|AI|VIDEO|WEB|APP|VISUALIZE|TRANSFORM|PANEL）"
    echo "  pull            - 从远程仓库拉取预构建运行时镜像（交互式，默认 full）"
    echo "  clean           - 清理所有容器和镜像"
    echo "  clean-build-runtime - 清理 build-runtime 构建产物（先停业务服务，默认删运行时镜像+构建缓存；保留跨架构基础镜像）"
    echo "  update          - 更新镜像并重启所有服务（交互可选拉取/本地重建）"
    echo "  verify          - 验证所有服务是否启动成功"
    echo "  check           - 检查 Docker 和 Docker Compose 安装状态"
    echo "  profile         - 显示当前部署形态与服务范围"
    echo "  site [子命令]   - 官方网站 SITE 独立部署（默认 install）"
    echo "  menu            - 打开两层交互引导（部署 / 分析 / 官网）"
    echo "  diagnose        - 进入【分析】子菜单"
    echo "  analyze-logs    - 多模块日志合并分析（各模块约 500 行，带分割线）"
    echo "  analyze-disk    - 项目关键目录磁盘占用分析"
    echo "  help            - 显示此帮助信息"
    echo ""
    echo "SITE 子命令（./install_linux.sh site <子命令>）:"
    echo "  install | start | stop | restart | status | logs | build | clean | update"
    echo "  也可直接: cd SITE && ./install_linux.sh <子命令>"
    echo "  默认端口: http://localhost:8090"
    echo ""
    echo "模块列表:"
    for module in "${MODULES[@]}"; do
        echo "  - ${MODULE_NAMES[$module]} ($module)"
    done
    echo ""
    echo "可选环境变量:"
    echo "  EASYAIOT_DEPLOY_PROFILE      - 部署形态: mini(1) | standard(2) | full(3，默认 full)"
    echo "  PARALLEL_MODULES=true|false  - 业务模块并行开关：start 默认并行；update 默认串行(可能含重建镜像)"
    echo "  PARALLEL_BUILD=true          - build 时并行构建各模块（默认串行，防小内存并行 OOM）"
    echo "  FORCE_NETWORK_RECREATE=true  - 启动时强制重建 easyaiot-network（宿主机 IP 变更后使用）"
    echo "  HOST_IP=<ip>                 - 跳过自动探测，强制指定宿主机 IP"
    echo "  EASYAIOT_ENABLE_INDUSTRIAL_DEMO=0 - full 形态下跳过工业协议演示（Modbus/OPC UA）自动启动"
    echo "  EASYAIOT_APPLY_INDUSTRIAL_SEED=0   - 启动演示时不写入/刷新工业协议演示设备种子"
    echo "  EASYAIOT_RUNTIME_REGISTRY    - 运行时镜像仓库（默认见 runtime_registry.conf）"
    echo "  EASYAIOT_RUNTIME_BUILD_ARCH  - build-runtime 目标架构: all(默认) | amd64 | arm64"
    echo "  EASYAIOT_RUNTIME_BUILD_MODULE - build-runtime 目标模块: all(默认) | DEVICE | AI | VIDEO | WEB | APP | VISUALIZE | TRANSFORM | PANEL"
    echo "  SITE_PORT                    - 官网宿主机端口（默认 8090）"
    echo ""
}

# 官方网站 SITE：委托 SITE/install_linux.sh
run_site_module() {
    local site_cmd="${1:-install}"
    local site_dir="${PROJECT_ROOT}/SITE"
    local site_script="${site_dir}/install_linux.sh"

    if [ ! -f "$site_script" ]; then
        print_error "未找到官网模块脚本: ${site_script}"
        return 1
    fi
    if [ ! -x "$site_script" ]; then
        chmod +x "$site_script" || true
    fi

    case "$site_cmd" in
        install|start|stop|restart|status|logs|build|clean|update|help|-h|--help)
            print_section "SITE 官方网站（独立部署）"
            print_info "执行: SITE/install_linux.sh ${site_cmd}"
            (cd "$site_dir" && bash ./install_linux.sh "$site_cmd")
            ;;
        "")
            print_section "SITE 官方网站（独立部署）"
            print_info "执行: SITE/install_linux.sh install"
            (cd "$site_dir" && bash ./install_linux.sh install)
            ;;
        *)
            print_error "未知 SITE 子命令: ${site_cmd}"
            echo "可用: install | start | stop | restart | status | logs | build | clean | update"
            return 1
            ;;
    esac
}

# 主函数
main() {
    local cmd="${1:-}"

    if [ -z "$cmd" ] || [ "$cmd" = "menu" ] || [ "$cmd" = "interactive" ]; then
        if [ "${EASYAIOT_FROM_MENU:-}" != "1" ]; then
            run_install_root_menu
            return 0
        fi
        cmd="help"
    fi

    case "$cmd" in
        install)
            install_linux
            ;;
        start)
            start_all
            ;;
        stop)
            stop_all
            ;;
        restart)
            restart_all
            ;;
        status)
            status_all
            ;;
        logs)
            view_logs "$2"
            ;;
        build)
            build_all
            ;;
        build-runtime|images-build)
            build_runtime_images "$@"
            ;;
        pull|images-pull)
            pull_runtime_images
            ;;
        clean)
            clean_all
            ;;
        clean-build-runtime|clean-runtime)
            clean_build_runtime "$@"
            ;;
        update)
            update_all
            ;;
        verify)
            verify_all
            ;;
        check)
            check_environment
            ;;
        profile)
            ensure_deploy_profile
            print_deploy_profile_summary
            ;;
        site|website|官网)
            run_site_module "${2:-install}"
            ;;
        diagnose|diagnose-tools)
            run_analyze_interactive_menu
            ;;
        analyze-logs|analyze-log|merge-logs)
            invoke_analyze_merge_logs "${@:2}"
            ;;
        analyze-disk|analyze-disk-usage|disk-usage)
            invoke_analyze_disk_usage "${@:2}"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"

# 脚本结束时记录日志文件路径
if [ -n "$LOG_FILE" ] && [ -f "$LOG_FILE" ]; then
    echo "" >> "$LOG_FILE"
    echo "=========================================" >> "$LOG_FILE"
    echo "脚本结束时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
    echo "=========================================" >> "$LOG_FILE"
    echo ""
    print_info "日志文件已保存到: $LOG_FILE"
fi
