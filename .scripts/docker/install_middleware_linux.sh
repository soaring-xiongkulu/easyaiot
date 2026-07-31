#!/bin/bash

# ============================================
# EasyAIoT 中间件部署脚本
# ============================================
# 使用方法：
#   ./install_all.sh [命令]
#
# 可用命令：
#   install    - 安装并启动所有中间件（首次运行）
#   start      - 启动所有中间件
#   stop       - 停止所有中间件
#   restart    - 重启所有中间件
#   status     - 查看所有中间件状态
#   logs       - 查看中间件日志
#   build      - 重新构建所有镜像
#   clean      - 清理所有容器和镜像
#   update     - 更新并重启所有中间件
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"

# shellcheck source=deploy_profile.sh
source "${SCRIPT_DIR}/deploy_profile.sh"
COMPOSE_PROFILE_ARGS=()

refresh_compose_profile_args() {
    apply_deploy_profile
    COMPOSE_PROFILE_ARGS=()
    local flags
    flags=$(compose_profile_flags)
    if [ -n "$flags" ]; then
        # shellcheck disable=SC2206
        COMPOSE_PROFILE_ARGS=($flags)
    fi
}

prepare_kafka_if_enabled() {
    if ! middleware_service_enabled "Kafka"; then
        print_info "当前部署形态未启用 Kafka，跳过 Kafka 目录与 hosts 配置"
        return 0
    fi
    create_kafka_directories
    configure_kafka_hosts
}

init_kafka_topics_if_enabled() {
    if ! middleware_service_enabled "Kafka"; then
        print_info "当前部署形态未启用 Kafka，跳过 Kafka 主题初始化"
        return 0
    fi
    init_kafka_iot_topics || print_warning "IoT Kafka 主题初始化未完成，可稍后手动执行: init_kafka_iot_topics"
}

mw_compose() {
    $COMPOSE_CMD -f "$COMPOSE_FILE" ${COMPOSE_PROFILE_ARGS[@]+"${COMPOSE_PROFILE_ARGS[@]}"} "$@"
}

# 强制对所有已存在的存储目录做完整递归 chmod/chown（兜底用）。
# 默认 false：已存在目录只设顶层权限，避免对海量数据文件递归导致卡顿（容器自身写的数据权限本就正确）。
# 仅当怀疑既有数据目录权限损坏、容器读写报错时，导出 FORCE_CHMOD=true 跑一次强制修复。
FORCE_CHMOD="${FORCE_CHMOD:-false}"

# 日志文件配置
LOG_DIR="${SCRIPT_DIR}/logs"
_LOG_TS="$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"
chmod -R 777 "$LOG_DIR" 2>/dev/null || sudo chmod -R 777 "$LOG_DIR" 2>/dev/null || true
LOG_FILE="${LOG_DIR}/install_middleware_${_LOG_TS}.log"

# 初始化日志文件
echo "=========================================" >> "$LOG_FILE"
echo "EasyAIoT 中间件部署脚本日志" >> "$LOG_FILE"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "命令: $*" >> "$LOG_FILE"
echo "=========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"


# 中间件服务列表
MIDDLEWARE_SERVICES=(
    "Nacos"
    "PostgresSQL"
    "Redis"
    "Kafka"
    "MinIO"
    "Milvus"
    "SRS"
    "NodeRED"
    "FUXA"
    "ZLMediaKit"
)

# 默认不启动（省内存）；TDengine 仅 full 自动开启，EMQX 在 standard/full 自动开启
# 也可显式设置 EASYAIOT_ENABLE_TDENGINE=1 / EASYAIOT_ENABLE_EMQX=1
DISABLED_BY_DEFAULT_MIDDLEWARE_SERVICES=(
    "TDengine"
    "TDengine-init"
    "EMQX"
)

# 可选中间件：镜像拉取失败或启动失败时不阻塞其余核心服务启动
# ZLMediaKit 是流媒体服务器（用于视频推拉流），启动失败不影响核心业务
# FUXA 依赖第三方镜像源（1panel/1ms 等常 403/401），缺失时不应拖垮 Postgres/Redis/Nacos
OPTIONAL_MIDDLEWARE_SERVICES=(
    "ZLMediaKit"
    "FUXA"
)

# 中间件端口映射
declare -A MIDDLEWARE_PORTS
MIDDLEWARE_PORTS["Nacos"]="8848"
MIDDLEWARE_PORTS["PostgresSQL"]="5432"
MIDDLEWARE_PORTS["TDengine"]="6030"
MIDDLEWARE_PORTS["Redis"]="6379"
MIDDLEWARE_PORTS["Kafka"]="9092"
MIDDLEWARE_PORTS["MinIO"]="9000"
MIDDLEWARE_PORTS["Milvus"]="9091"
MIDDLEWARE_PORTS["SRS"]="1935"
MIDDLEWARE_PORTS["NodeRED"]="1880"
MIDDLEWARE_PORTS["FUXA"]="1881"
MIDDLEWARE_PORTS["EMQX"]="1883"
MIDDLEWARE_PORTS["ZLMediaKit"]="6080"

# 中间件健康检查端点
declare -A MIDDLEWARE_HEALTH_ENDPOINTS
MIDDLEWARE_HEALTH_ENDPOINTS["Nacos"]="/nacos/actuator/health"
MIDDLEWARE_HEALTH_ENDPOINTS["PostgresSQL"]=""
MIDDLEWARE_HEALTH_ENDPOINTS["TDengine"]=""
MIDDLEWARE_HEALTH_ENDPOINTS["Redis"]=""
MIDDLEWARE_HEALTH_ENDPOINTS["Kafka"]=""
MIDDLEWARE_HEALTH_ENDPOINTS["MinIO"]="/minio/health/live"
MIDDLEWARE_HEALTH_ENDPOINTS["Milvus"]="/healthz"
MIDDLEWARE_HEALTH_ENDPOINTS["SRS"]="/api/v1/versions"
MIDDLEWARE_HEALTH_ENDPOINTS["NodeRED"]="/"
MIDDLEWARE_HEALTH_ENDPOINTS["FUXA"]="/"
MIDDLEWARE_HEALTH_ENDPOINTS["EMQX"]="/api/v5/status"
MIDDLEWARE_HEALTH_ENDPOINTS["ZLMediaKit"]="/index/api/getServerConfig"


# 以特权执行命令：root 直接执行；非 root 且有 sudo 走 sudo；两者皆无则原样尝试。
# 统一全文反复出现的 EUID/sudo 三分支样板（语义与原三分支完全一致）。
run_priv() {
    if [ "$EUID" -eq 0 ]; then
        "$@"
    elif command -v sudo &> /dev/null; then
        sudo "$@"
    else
        "$@"
    fi
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


# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

# shellcheck source=docker_compose_bundled.sh
source "${SCRIPT_DIR}/docker_compose_bundled.sh"

# shellcheck source=docker_mirror_common.sh
source "${SCRIPT_DIR}/docker_mirror_common.sh"

# 容器运行状态检查（供 wait_for_postgresql / post-install 等待逻辑使用）
container_running() {
    docker ps --filter "name=$1" --format "{{.Names}}" 2>/dev/null | grep -q "$1"
}

container_exists() {
    docker ps -a --filter "name=$1" --format "{{.Names}}" 2>/dev/null | grep -q "$1"
}

container_status() {
    docker inspect --format '{{.State.Status}}' "$1" 2>/dev/null || echo ""
}

# 检查 Git 是否已安装
check_git() {
    if check_command git; then
        local git_version=$(git --version 2>&1)
        print_success "Git 已安装: $git_version"
        return 0
    fi
    return 1
}

# 检查并提示安装 Git
check_and_require_git() {
    if check_git; then
        return 0
    fi
    
    print_error "未检测到 Git"
    echo ""
    print_info "Git 是运行此项目的必需组件"
    echo ""
    
    # 检测系统类型
    local os_id=""
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        os_id="$ID"
    fi
    
    # 根据系统类型提供安装指导
    echo ""
    print_warning "请按照以下步骤安装 Git："
    echo ""
    
    case "$os_id" in
        ubuntu|debian)
            print_info "Debian/Ubuntu 系统安装命令："
            print_info "  sudo apt update"
            print_info "  sudo apt install -y git"
            ;;
        centos|rhel|fedora)
            print_info "CentOS/RHEL/Fedora 系统安装命令："
            print_info "  sudo yum install -y git"
            ;;
        *)
            print_info "请访问 Git 官网获取安装指南："
            print_info "  https://git-scm.com/download/linux"
            ;;
    esac
    
    echo ""
    print_error "Git 是必需的，安装流程已终止"
    print_info "安装 Git 后，请重新运行此脚本"
    exit 1
}


# 检查 nvidia-container-toolkit 是否已安装
check_nvidia_container_toolkit() {
    if command -v nvidia-container-runtime &> /dev/null; then
        local runtime_path=$(which nvidia-container-runtime)
        print_success "nvidia-container-toolkit 已安装: $runtime_path"
        return 0
    fi
    
    # 检查是否通过包管理器安装
    if dpkg -l 2>/dev/null | grep -q nvidia-container-toolkit 2>/dev/null; then
        print_info "nvidia-container-toolkit 已通过包管理器安装"
        return 0
    fi
    if command -v rpm >/dev/null 2>&1 && rpm -qa 2>/dev/null | grep -q nvidia-container-toolkit; then
        print_info "nvidia-container-toolkit 已通过包管理器安装"
        return 0
    fi
    
    return 1
}

# 安装 nvidia-container-toolkit
install_nvidia_container_toolkit() {
    print_section "安装 NVIDIA Container Toolkit"
    
    if [ "$EUID" -ne 0 ]; then
        print_warning "安装 nvidia-container-toolkit 需要 root 权限，跳过自动安装"
        print_info "如果后续需要使用 GPU，请手动安装 nvidia-container-toolkit"
        print_info "安装指南: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
        return 1
    fi
    
    # 检测系统类型
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        local os_id="$ID"
    else
        print_error "无法检测操作系统类型"
        return 1
    fi
    
    # 第一步：卸载旧版本（如果存在）
    print_info "检查并卸载旧版本..."
    case "$os_id" in
        ubuntu|debian)
            apt-get purge -y nvidia-docker2 nvidia-container-toolkit 2>/dev/null || true
            rm -rf /etc/nvidia-container-runtime 2>/dev/null || true
            ;;
        centos|rhel|fedora)
            yum remove -y nvidia-docker2 nvidia-container-toolkit 2>/dev/null || true
            rm -rf /etc/nvidia-container-runtime 2>/dev/null || true
            ;;
        *)
            print_warning "不支持的操作系统: $os_id，尝试通用卸载方法"
            rm -rf /etc/nvidia-container-runtime 2>/dev/null || true
            ;;
    esac
    
    # 第二步：添加 NVIDIA 仓库并安装
    print_info "添加 NVIDIA 仓库..."
    case "$os_id" in
        ubuntu|debian)
            # 添加密钥和仓库（添加重试机制）
            local gpg_key_added=0
            local max_retries=3
            local retry_count=0
            
            while [ $retry_count -lt $max_retries ] && [ $gpg_key_added -eq 0 ]; do
                if curl -fsSL --connect-timeout 10 --max-time 30 https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg 2>/dev/null; then
                    gpg_key_added=1
                    print_success "NVIDIA GPG 密钥添加成功"
                else
                    retry_count=$((retry_count + 1))
                    if [ $retry_count -lt $max_retries ]; then
                        print_warning "添加 NVIDIA GPG 密钥失败，正在重试 ($retry_count/$max_retries)..."
                        sleep 2
                    else
                        print_error "添加 NVIDIA GPG 密钥失败（已重试 $max_retries 次）"
                        print_warning "可能是网络问题，将尝试使用备用方法或跳过此步骤"
                        
                        # 尝试使用备用方法：直接下载密钥文件
                        print_info "尝试使用备用方法添加 GPG 密钥..."
                        if curl -fsSL --connect-timeout 10 --max-time 30 "https://nvidia.github.io/libnvidia-container/gpgkey" -o /tmp/nvidia-gpgkey 2>/dev/null && \
                           gpg --dearmor /tmp/nvidia-gpgkey -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg 2>/dev/null; then
                            rm -f /tmp/nvidia-gpgkey
                            gpg_key_added=1
                            print_success "使用备用方法成功添加 NVIDIA GPG 密钥"
                        else
                            rm -f /tmp/nvidia-gpgkey
                            print_error "备用方法也失败，nvidia-container-toolkit 安装将跳过"
                            print_info "如果后续需要使用 GPU，请手动安装 nvidia-container-toolkit"
                            print_info "安装指南: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
                            return 1
                        fi
                    fi
                fi
            done
            
            # 如果 GPG 密钥添加失败，直接返回
            if [ $gpg_key_added -eq 0 ]; then
                return 1
            fi
            
            # 添加仓库列表（添加重试机制）
            local repo_added=0
            local max_retries=3
            local retry_count=0
            
            while [ $retry_count -lt $max_retries ] && [ $repo_added -eq 0 ]; do
                if curl -fsSL --connect-timeout 10 --max-time 30 https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
                   sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
                   tee /etc/apt/sources.list.d/nvidia-container-toolkit.list > /dev/null; then
                    repo_added=1
                    print_success "NVIDIA 仓库添加成功"
                else
                    retry_count=$((retry_count + 1))
                    if [ $retry_count -lt $max_retries ]; then
                        print_warning "添加 NVIDIA 仓库失败，正在重试 ($retry_count/$max_retries)..."
                        sleep 2
                    else
                        print_error "添加 NVIDIA 仓库失败（已重试 $max_retries 次）"
                        return 1
                    fi
                fi
            done
            
            # 更新包列表
            if ! apt-get update -qq > /dev/null 2>&1; then
                print_error "更新包列表失败"
                return 1
            fi
            
            # 安装 nvidia-container-toolkit
            print_info "正在安装 nvidia-container-toolkit..."
            if ! apt-get install -qq -y nvidia-container-toolkit > /dev/null 2>&1; then
                print_error "安装 nvidia-container-toolkit 失败"
                return 1
            fi
            ;;
        centos|rhel|fedora)
            # 添加仓库
            if ! curl -fsSL https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo | \
                tee /etc/yum.repos.d/nvidia-container-toolkit.repo > /dev/null; then
                print_error "添加 NVIDIA 仓库失败"
                return 1
            fi
            
            # 安装 nvidia-container-toolkit
            print_info "正在安装 nvidia-container-toolkit..."
            if ! yum install -y nvidia-container-toolkit; then
                print_error "安装 nvidia-container-toolkit 失败"
                return 1
            fi
            ;;
        *)
            print_error "不支持的操作系统: $os_id"
            print_info "请手动安装 nvidia-container-toolkit 后重试"
            print_info "安装指南: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
            return 1
            ;;
    esac
    
    # 第三步：配置 Docker 使用 NVIDIA 作为默认运行时
    print_info "配置 Docker 使用 NVIDIA 作为默认运行时..."
    if ! nvidia-ctk runtime configure --runtime=docker; then
        print_error "配置 Docker runtime 失败"
        return 1
    fi
    
    # 第四步：重启 Docker
    print_info "重启 Docker 服务以使配置生效..."
    systemctl daemon-reload
    if ! systemctl restart docker; then
        print_error "重启 Docker 服务失败"
        return 1
    fi
    
    # 第五步：验证安装（轮询 docker daemon 就绪，最长 15s，就绪即继续）
    print_info "验证安装..."
    local _dw=0
    while [ $_dw -lt 15 ] && ! docker info > /dev/null 2>&1; do
        sleep 1
        _dw=$((_dw + 1))
    done
    
    if command -v nvidia-container-runtime &> /dev/null; then
        local runtime_path=$(which nvidia-container-runtime)
        print_success "nvidia-container-runtime 已安装: $runtime_path"
    else
        print_warning "nvidia-container-runtime 未在 PATH 中找到，但包已安装"
    fi
    
    # 测试运行 GPU 容器（可选，如果系统有 GPU）
    if command -v nvidia-smi &> /dev/null; then
        print_info "检测到 NVIDIA GPU，测试 GPU 容器..."
        if docker run --rm --gpus all nvidia/cuda:11.8.0-base nvidia-smi &> /dev/null; then
            print_success "GPU 容器测试成功"
        else
            print_warning "GPU 容器测试失败，但 nvidia-container-toolkit 已安装"
            print_info "请检查 NVIDIA 驱动是否正确安装"
        fi
    else
        print_info "未检测到 NVIDIA GPU，跳过 GPU 容器测试"
    fi
    
    print_success "NVIDIA Container Toolkit 安装完成"
    return 0
}

# 检查并安装 nvidia-container-toolkit
check_and_install_nvidia_container_toolkit() {
    if check_nvidia_container_toolkit; then
        return 0
    fi
    
    print_warning "未检测到 nvidia-container-toolkit"
    echo ""
    print_info "nvidia-container-toolkit 是 Docker 容器使用 GPU 的必需组件"
    print_info "如果没有 NVIDIA GPU 或不需要 GPU 支持，可以跳过此步骤"
    echo ""
    
    while true; do
        echo -ne "${YELLOW}[提示]${NC} 是否自动安装 nvidia-container-toolkit？(y/N): "
        read -r response
        case "$response" in
            [yY][eE][sS]|[yY])
                if [ "$EUID" -ne 0 ]; then
                    print_warning "安装 nvidia-container-toolkit 需要 root 权限，跳过自动安装"
                    print_info "如果后续需要使用 GPU，请手动安装 nvidia-container-toolkit"
                    print_info "安装指南: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
                    return 0
                fi
                if install_nvidia_container_toolkit; then
                    print_success "nvidia-container-toolkit 安装成功"
                    return 0
                else
                    print_warning "nvidia-container-toolkit 安装失败"
                    print_info "这可能是由于网络问题导致的，不影响其他服务的安装"
                    print_info "如果后续需要使用 GPU，请手动安装 nvidia-container-toolkit"
                    print_info "安装指南: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
                    echo ""
                    print_warning "是否继续安装其他服务？(y/N): "
                    read -r continue_response
                    case "$continue_response" in
                        [yY][eE][sS]|[yY])
                            print_info "继续安装其他服务..."
                            return 0
                            ;;
                        *)
                            print_info "已取消安装"
                            exit 1
                            ;;
                    esac
                fi
                ;;
            [nN][oO]|[nN]|"")
                print_info "跳过 nvidia-container-toolkit 安装"
                print_info "如果后续需要使用 GPU，请手动安装 nvidia-container-toolkit"
                return 0
                ;;
            *)
                print_warning "请输入 y 或 N"
                ;;
        esac
    done
}

# 检测系统是否有 NVIDIA GPU 支持
check_nvidia_gpu_support() {
    # 方法1: 检查 nvidia-smi 命令
    if command -v nvidia-smi &> /dev/null; then
        if nvidia-smi &> /dev/null; then
            return 0  # 有 GPU 支持
        fi
    fi
    
    # 方法2: 检查 /dev/nvidia* 设备文件
    if ls /dev/nvidia* &> /dev/null; then
        return 0  # 有 GPU 支持
    fi
    
    # 方法3: 检查 nvidia-container-toolkit 是否已安装且可用
    if check_nvidia_container_toolkit; then
        # 如果已安装，尝试测试 GPU 容器
        if docker run --rm --gpus all nvidia/cuda:11.8.0-base nvidia-smi &> /dev/null 2>&1; then
            return 0  # 有 GPU 支持
        fi
    fi
    
    return 1  # 没有 GPU 支持
}

# 配置 Docker 镜像源
configure_docker_mirror() {
    print_section "配置 Docker 镜像源和 NVIDIA Runtime"
    
    local docker_config_dir="/etc/docker"
    local docker_config_file="$docker_config_dir/daemon.json"
    
    if [ "$EUID" -ne 0 ]; then
        print_warning "配置 Docker 镜像源需要 root 权限，跳过此步骤"
        return 0
    fi
    
    # 检测是否有 GPU 支持
    local has_gpu=0
    if check_nvidia_gpu_support; then
        has_gpu=1
        print_info "检测到 NVIDIA GPU 支持，将配置 NVIDIA runtime"
    else
        print_info "未检测到 NVIDIA GPU 支持，将跳过 default-runtime 配置"
        print_info "如果后续需要 GPU 支持，请安装 nvidia-container-toolkit 后重新运行此脚本"
    fi
    
    # 创建 docker 配置目录
    mkdir -p "$docker_config_dir"
    
    # 使用 Python 精确检查和配置
    print_info "正在检查并配置 Docker 配置..."
    
    local output_file=$(mktemp)
    local python_exit_code=0
    
    python3 << EOF > "$output_file" 2>&1
import json
import sys
import os

config_file = "$docker_config_file"
has_gpu = $has_gpu
# 推荐的镜像源列表（DaoCloud 公共镜像：https://github.com/DaoCloud/public-image-mirror）
recommended_mirrors = [
    "https://docker.m.daocloud.io/"
]
# 国内公网 DNS：麒麟等系统 resolv.conf 常指向 ::1/127.0.0.53，Docker 无法使用导致拉镜像失败
recommended_dns = [x.strip() for x in os.environ.get("DOCKER_DNS", "223.5.5.5,119.29.29.29").split(",") if x.strip()]
nvidia_runtime = {
    "path": "nvidia-container-runtime",
    "runtimeArgs": []
}
# 只有在有 GPU 支持时才设置 default-runtime
required_default_runtime = "nvidia" if has_gpu else None

def _host_uses_loopback_dns():
    try:
        with open("/etc/resolv.conf") as rf:
            for line in rf:
                s = line.strip().lower()
                if s.startswith("nameserver"):
                    ns = s.split(None, 1)[-1] if " " in s else ""
                    if ns.startswith("127.") or ns == "::1":
                        return True
    except Exception:
        pass
    return False

def _is_kylin_like():
    try:
        with open("/etc/os-release") as of:
            text = of.read().lower()
            return any(x in text for x in ("kylin", "uos", "openeuler", "uniontech"))
    except Exception:
        return False

want_dns = (
    os.environ.get("EASYAIOT_FORCE_DOCKER_DNS", "0") == "1"
    or _host_uses_loopback_dns()
    or _is_kylin_like()
)

# 读取现有配置
config = {}
if os.path.exists(config_file):
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"CONFIG_ERROR:读取配置文件失败: {e}", file=sys.stderr)
        sys.exit(1)

needs_update = False
changes = []

# 检查并添加镜像源（保留用户已有的，只添加缺失的）
if "registry-mirrors" not in config:
    config["registry-mirrors"] = []
    needs_update = True
    changes.append("添加 registry-mirrors 配置")

# 获取现有镜像源列表
existing_mirrors = config.get("registry-mirrors", [])
# 确保是列表类型
if not isinstance(existing_mirrors, list):
    existing_mirrors = []

# 添加缺失的推荐镜像源（保留用户已有的配置）
added_mirrors = []
for mirror in recommended_mirrors:
    # 检查镜像源是否已存在（支持带/和不带/的匹配）
    mirror_normalized = mirror.rstrip('/')
    exists = False
    for existing in existing_mirrors:
        existing_normalized = existing.rstrip('/')
        if mirror_normalized == existing_normalized:
            exists = True
            break
    
    if not exists:
        existing_mirrors.append(mirror)
        added_mirrors.append(mirror)
        needs_update = True

if added_mirrors:
    config["registry-mirrors"] = existing_mirrors
    changes.append(f"添加镜像源: {', '.join(added_mirrors)}")

# DNS：宿主机 loopback / 国产系统时写入公网 DNS，避免 lookup on [::1]:53 connection refused
if want_dns and recommended_dns:
    existing_dns = config.get("dns") if isinstance(config.get("dns"), list) else []
    existing_dns_norm = [str(x).strip() for x in existing_dns]
    loopback_dns = any(x.startswith("127.") or x == "::1" for x in existing_dns_norm)
    if not existing_dns_norm or loopback_dns or existing_dns_norm != recommended_dns:
        if existing_dns_norm != recommended_dns:
            config["dns"] = recommended_dns
            needs_update = True
            changes.append(f"配置 Docker DNS: {', '.join(recommended_dns)}")

# 检查并添加 NVIDIA runtime
# 注意：即使没有 GPU，也保留 runtime 配置（如果 nvidia-container-toolkit 已安装）
# 这样后续安装 GPU 后可以直接使用，不需要重新配置
if "runtimes" not in config:
    config["runtimes"] = {}
    needs_update = True
    changes.append("添加 runtimes 配置")

# 检查 nvidia-container-toolkit 是否已安装
nvidia_toolkit_installed = False
try:
    import subprocess
    result = subprocess.run(["which", "nvidia-container-runtime"], 
                          capture_output=True, timeout=2)
    nvidia_toolkit_installed = (result.returncode == 0)
except:
    pass

# 只有在 nvidia-container-toolkit 已安装或检测到 GPU 时才配置 runtime
# 这样可以避免在没有工具包的情况下配置无效的 runtime
if nvidia_toolkit_installed or has_gpu:
    if "nvidia" not in config["runtimes"]:
        config["runtimes"]["nvidia"] = nvidia_runtime
        needs_update = True
        changes.append("添加 NVIDIA runtime 配置")
    else:
        # 检查现有配置是否正确
        nvidia_config = config["runtimes"]["nvidia"]
        if nvidia_config.get("path") != nvidia_runtime["path"]:
            config["runtimes"]["nvidia"] = nvidia_runtime
            needs_update = True
            changes.append("更新 NVIDIA runtime 配置")

# 检查并添加 default-runtime（只有在有 GPU 支持时才设置）
if required_default_runtime is not None:
    # 有 GPU 支持，需要设置 default-runtime
    if "default-runtime" not in config:
        config["default-runtime"] = required_default_runtime
        needs_update = True
        changes.append(f"添加 default-runtime: {required_default_runtime}")
    elif config["default-runtime"] != required_default_runtime:
        config["default-runtime"] = required_default_runtime
        needs_update = True
        changes.append(f"更新 default-runtime: {required_default_runtime}")
else:
    # 没有 GPU 支持，如果现有配置是 nvidia，需要移除或改为默认
    if "default-runtime" in config and config["default-runtime"] == "nvidia":
        # 移除 default-runtime 配置，让 Docker 使用默认运行时
        del config["default-runtime"]
        needs_update = True
        changes.append("移除 default-runtime 配置（系统无 GPU 支持）")

# 写入配置文件
if needs_update:
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print("CONFIG_UPDATED")
        for change in changes:
            print(f"CHANGE:{change}")
    except Exception as e:
        print(f"CONFIG_ERROR:{e}", file=sys.stderr)
        sys.exit(1)
else:
    print("CONFIG_OK")
EOF
    
    python_exit_code=$?
    local config_updated=false
    local config_ok=false
    
    # 解析 Python 输出
    while IFS= read -r line || [ -n "$line" ]; do
        if [[ $line == CONFIG_UPDATED ]]; then
            config_updated=true
        elif [[ $line == CONFIG_OK ]]; then
            config_ok=true
        elif [[ $line == CHANGE:* ]]; then
            local change="${line#CHANGE:}"
            print_info "配置变更: $change"
        elif [[ $line == CONFIG_ERROR:* ]]; then
            local error="${line#CONFIG_ERROR:}"
            print_error "配置失败: $error"
            rm -f "$output_file"
            return 1
        fi
    done < "$output_file"
    
    rm -f "$output_file"
    
    if [ $python_exit_code -ne 0 ]; then
        print_error "Docker 配置检查失败"
        return 1
    fi
    
    if [ "$config_ok" = true ]; then
        print_success "Docker 配置已完整（镜像源、NVIDIA runtime、default-runtime 均已配置）"
    elif [ "$config_updated" = true ]; then
        print_success "Docker 配置已更新"
        
        # 重启 Docker 服务使配置生效
        if systemctl is-active --quiet docker; then
            print_info "正在重启 Docker 服务以使配置生效..."
            systemctl daemon-reload
            systemctl restart docker
            print_success "Docker 服务已重启"
        fi
    else
        print_warning "Docker 配置检查完成，但未发现需要更新的配置"
    fi
}

# 配置 pip 镜像源
configure_pip_mirror() {
    print_section "配置 pip 镜像源"
    
    local pip_config_dir="$HOME/.pip"
    local pip_config_file="$pip_config_dir/pip.conf"
    
    # 创建 pip 配置目录
    mkdir -p "$pip_config_dir"
    
    # 检查是否已配置
    if [ -f "$pip_config_file" ]; then
        if grep -q "index-url" "$pip_config_file"; then
            print_info "pip 镜像源已配置，跳过"
            return 0
        fi
    fi
    
    print_info "正在配置 pip 镜像源..."
    
    # 创建或更新配置文件
    cat > "$pip_config_file" << EOF
[global]
index-url = https://mirrors.huaweicloud.com/repository/pypi/simple
trusted-host = mirrors.huaweicloud.com

[install]
trusted-host = mirrors.huaweicloud.com
EOF
    
    print_success "pip 镜像源配置完成"
    print_info "已使用华为云镜像源: https://mirrors.huaweicloud.com/repository/pypi/simple"
}

# 配置 apt 国内源
configure_apt_mirror() {
    print_section "配置 apt 国内源"
    
    # 检测系统类型
    if [ ! -f /etc/os-release ]; then
        print_warning "无法检测操作系统类型，跳过 apt 源配置"
        return 0
    fi
    
    . /etc/os-release
    local os_id="$ID"
    
    # 只处理 Debian/Ubuntu 系统
    if [ "$os_id" != "ubuntu" ] && [ "$os_id" != "debian" ]; then
        print_info "当前系统不是 Debian/Ubuntu，跳过 apt 源配置"
        return 0
    fi
    
    # 检查是否有 root 权限
    if [ "$EUID" -ne 0 ]; then
        print_warning "配置 apt 源需要 root 权限，跳过此步骤"
        print_info "如需配置 apt 源，请使用 sudo 运行此脚本"
        return 0
    fi
    
    # 检查用户是否已经选择过（通过标记文件）
    local apt_mirror_marker="/etc/apt/.easyaiot_mirror_configured"
    
    # 先检查当前系统是否已配置国内 apt 源（完整检查，包括 sources.list 和 sources.list.d）
    local current_sources_list="/etc/apt/sources.list"
    local current_sources_content=""
    local is_current_domestic=false
    
    # 读取当前系统的 apt 源配置
    if [ -f "$current_sources_list" ]; then
        current_sources_content=$(cat "$current_sources_list")
        # 检查是否已经是国内源（包含常见国内镜像关键词）
        # 匹配模式：tuna、aliyun、163、ustc、huawei、tencent 等国内镜像站
        if echo "$current_sources_content" | grep -qiE "(mirrors\.(tuna|aliyun|163|ustc|huawei|tencent)|tuna\.tsinghua|aliyun\.com|163\.com|ustc\.edu|huawei\.com|tencent\.com|mirror\.nju\.edu\.cn|mirrors\.bfsu\.edu\.cn)"; then
            is_current_domestic=true
        fi
    fi
    
    # 如果主配置文件不是国内源，检查 sources.list.d 目录下的文件
    if [ "$is_current_domestic" = false ] && [ -d "/etc/apt/sources.list.d" ]; then
        for list_file in /etc/apt/sources.list.d/*.list; do
            if [ -f "$list_file" ]; then
                local file_content=$(cat "$list_file")
                if echo "$file_content" | grep -qiE "(mirrors\.(tuna|aliyun|163|ustc|huawei|tencent)|tuna\.tsinghua|aliyun\.com|163\.com|ustc\.edu|huawei\.com|tencent\.com|mirror\.nju\.edu\.cn|mirrors\.bfsu\.edu\.cn)"; then
                    is_current_domestic=true
                    break
                fi
            fi
        done
    fi
    
    # 如果当前系统已经配置了国内源，直接跳过，不提示用户，并记录标记
    if [ "$is_current_domestic" = true ]; then
        print_info "检测到系统已配置国内 apt 源，跳过配置步骤"
        echo "configured" > "$apt_mirror_marker" 2>/dev/null || true
        return 0
    fi
    
    # 如果系统未配置国内源，检查标记文件
    if [ -f "$apt_mirror_marker" ]; then
        local user_choice=$(cat "$apt_mirror_marker" 2>/dev/null || echo "")
        if [ "$user_choice" = "skip" ]; then
            print_info "检测到用户已选择跳过 apt 源配置，跳过此步骤"
            return 0
        elif [ "$user_choice" = "configured" ]; then
            # 标记文件显示已配置，但实际检查未发现国内源，说明配置可能被删除了
            # 清除标记文件，让用户重新选择
            print_warning "检测到标记文件显示已配置，但实际未发现国内源配置，清除标记文件"
            rm -f "$apt_mirror_marker"
        fi
    fi
    
    # 读取本地 apt 源配置（用于替换）
    local local_sources_list="/etc/apt/sources.list"
    local local_sources_content=""
    local has_local_source=false
    local is_domestic_mirror=false
    
    if [ -f "$local_sources_list" ]; then
        local_sources_content=$(cat "$local_sources_list")
        has_local_source=true
        # 检查是否是国内源（包含常见国内镜像关键词）
        if echo "$local_sources_content" | grep -qiE "(mirrors\.(tuna|aliyun|163|ustc|huawei|tencent)|tuna\.tsinghua|aliyun\.com|163\.com|ustc\.edu|huawei\.com|tencent\.com)"; then
            is_domestic_mirror=true
        fi
    fi
    
    # 询问用户是否替换 apt 源
    echo ""
    print_warning "为了加快软件包下载速度，建议使用国内 apt 源"
    if [ "$has_local_source" = true ]; then
        if [ "$is_domestic_mirror" = true ]; then
            print_info "检测到本地已配置国内 apt 源，可以使用本地配置替换当前系统 apt 源"
        else
            print_info "检测到本地 apt 源配置，将使用本地配置替换当前系统 apt 源"
        fi
    else
        print_info "当前系统 apt 源可能下载较慢，建议替换为国内镜像源"
    fi
    echo ""
    
    while true; do
        echo -ne "${YELLOW}[提示]${NC} 是否替换 apt 源为国内源？(y/N): "
        read -r response
        case "$response" in
            [yY][eE][sS]|[yY])
                # 用户选择替换
                print_info "正在配置 apt 国内源..."
                
                # 备份现有的 sources.list
                local sources_list="/etc/apt/sources.list"
                local backup_file="${sources_list}.bak.$(date +%Y%m%d_%H%M%S)"
                
                if [ -f "$sources_list" ]; then
                    cp "$sources_list" "$backup_file"
                    print_success "已备份现有 apt 源配置到: $backup_file"
                fi
                
                # 如果本地有 apt 源配置，使用本地配置
                if [ "$has_local_source" = true ] && [ -n "$local_sources_content" ]; then
                    print_info "使用本地 apt 源配置..."
                    echo "$local_sources_content" > "$sources_list"
                    print_success "已使用本地 apt 源配置替换系统 apt 源"
                else
                    # 否则使用默认的国内源配置
                    print_info "使用默认国内 apt 源配置..."
                    
                    # 检测系统版本
                    local codename=""
                    if [ -n "$VERSION_CODENAME" ]; then
                        codename="$VERSION_CODENAME"
                    elif [ -n "$UBUNTU_CODENAME" ]; then
                        codename="$UBUNTU_CODENAME"
                    else
                        # 尝试从 lsb_release 获取
                        if command -v lsb_release &> /dev/null; then
                            codename=$(lsb_release -cs 2>/dev/null || echo "")
                        fi
                    fi
                    
                    if [ -z "$codename" ]; then
                        print_error "无法检测系统版本代号，跳过 apt 源配置"
                        return 1
                    fi
                    
                    print_info "检测到系统版本代号: $codename"
                    
                    # 根据系统类型配置国内源
                    if [ "$os_id" = "ubuntu" ]; then
                        # Ubuntu 使用清华大学镜像源
                        cat > "$sources_list" << EOF
# 清华大学 Ubuntu 镜像源
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ $codename main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ $codename-updates main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ $codename-backports main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ $codename-security main restricted universe multiverse

# 源码仓库（可选）
# deb-src https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ $codename main restricted universe multiverse
# deb-src https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ $codename-updates main restricted universe multiverse
# deb-src https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ $codename-backports main restricted universe multiverse
# deb-src https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ $codename-security main restricted universe multiverse
EOF
                        print_success "已配置 Ubuntu 清华大学镜像源"
                    elif [ "$os_id" = "debian" ]; then
                        # Debian 使用清华大学镜像源
                        local debian_version=""
                        if [ -n "$VERSION_ID" ]; then
                            debian_version=$(echo "$VERSION_ID" | cut -d. -f1)
                        fi
                        
                        if [ -z "$debian_version" ]; then
                            # 尝试从 codename 推断版本
                            case "$codename" in
                                bookworm)
                                    debian_version="12"
                                    ;;
                                bullseye)
                                    debian_version="11"
                                    ;;
                                buster)
                                    debian_version="10"
                                    ;;
                                *)
                                    debian_version="12"
                                    print_warning "无法确定 Debian 版本，使用默认版本 12"
                                    ;;
                            esac
                        fi
                        
                        cat > "$sources_list" << EOF
# 清华大学 Debian 镜像源
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ $codename main contrib non-free non-free-firmware
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ $codename-updates main contrib non-free non-free-firmware
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ $codename-backports main contrib non-free non-free-firmware
deb https://mirrors.tuna.tsinghua.edu.cn/debian-security $codename-security main contrib non-free non-free-firmware

# 源码仓库（可选）
# deb-src https://mirrors.tuna.tsinghua.edu.cn/debian/ $codename main contrib non-free non-free-firmware
# deb-src https://mirrors.tuna.tsinghua.edu.cn/debian/ $codename-updates main contrib non-free non-free-firmware
# deb-src https://mirrors.tuna.tsinghua.edu.cn/debian/ $codename-backports main contrib non-free non-free-firmware
# deb-src https://mirrors.tuna.tsinghua.edu.cn/debian-security $codename-security main contrib non-free non-free-firmware
EOF
                        print_success "已配置 Debian 清华大学镜像源"
                    fi
                fi
                
                # 更新 apt 缓存
                print_info "正在更新 apt 缓存..."
                if apt update -qq > /dev/null 2>&1; then
                    print_success "apt 源配置完成并已更新缓存"
                    # 记录已配置标记
                    echo "configured" > "$apt_mirror_marker" 2>/dev/null || true
                else
                    print_warning "apt 源配置完成，但更新缓存时出现问题"
                    print_info "您可以稍后手动运行: apt update"
                    # 即使更新失败，也记录已配置标记（因为源文件已修改）
                    echo "configured" > "$apt_mirror_marker" 2>/dev/null || true
                fi
                
                return 0
                ;;
            [nN][oO]|[nN]|"")
                # 用户选择不替换，继续执行，并记录标记
                print_info "保持当前 apt 源配置，继续执行..."
                echo "skip" > "$apt_mirror_marker" 2>/dev/null || true
                return 0
                ;;
            *)
                print_warning "请输入 y 或 N"
                ;;
        esac
    done
}


# 检查 Docker 权限
check_docker_permission() {
    # 先检查 Docker 是否安装
    if ! check_command docker; then
        print_error "Docker 未安装"
        return 1
    fi
    
    # 检查是否有权限访问 Docker daemon
    if ! docker ps &> /dev/null; then
        print_error "没有权限访问 Docker daemon"
        echo ""
        echo "解决方案："
        echo "  1. 将当前用户添加到 docker 组："
        echo "     sudo usermod -aG docker $USER"
        echo "     然后重新登录或运行: newgrp docker"
        echo ""
        echo "  2. 或者使用 sudo 运行此脚本："
        echo "     sudo ./install_middleware.sh $*"
        echo ""
        exit 1
    fi
}

# 安装 Docker
install_docker() {
    print_section "安装 Docker"
    
    if [ "$EUID" -ne 0 ]; then
        print_warning "安装 Docker 需要 root 权限，跳过自动安装"
        print_info "请手动安装 Docker 后继续，或使用 sudo 运行此脚本"
        print_info "安装指南: https://docs.docker.com/get-docker/"
        return 1
    fi
    
    # 询问用户 Docker data-root 路径
    echo ""
    print_warning "Docker 默认会将数据存储在系统盘（/var/lib/docker），如果系统盘空间较小，建议指定其他路径"
    echo ""
    print_info "请输入 Docker 数据存储路径（data-root）："
    print_info "  直接回车将使用默认路径: /var/lib/docker"
    print_info "  建议使用大容量磁盘路径，例如: /data/docker 或 /mnt/docker"
    echo ""
    
    local docker_data_root=""
    while true; do
        echo -ne "${YELLOW}[提示]${NC} 请输入 Docker data-root 路径（直接回车使用默认路径）: "
        read -r docker_data_root
        
        # 如果用户直接回车，使用默认路径
        if [ -z "$docker_data_root" ]; then
            docker_data_root="/var/lib/docker"
            print_info "使用默认路径: $docker_data_root"
            break
        fi
        
        # 验证路径格式（必须是绝对路径）
        if [[ ! "$docker_data_root" =~ ^/ ]]; then
            print_error "请输入绝对路径（以 / 开头）"
            continue
        fi
        
        # 检查路径是否已存在且可写
        if [ -d "$docker_data_root" ]; then
            if [ ! -w "$docker_data_root" ]; then
                print_error "路径 $docker_data_root 不可写，请选择其他路径"
                continue
            fi
        else
            # 尝试创建目录
            if ! mkdir -p "$docker_data_root" 2>/dev/null; then
                print_error "无法创建路径 $docker_data_root，请检查权限或选择其他路径"
                continue
            fi
        fi
        
        print_success "将使用路径: $docker_data_root"
        break
    done
    
    # 检测系统类型
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        local os_id="$ID"
    else
        print_error "无法检测操作系统类型"
        return 1
    fi
    
    # 根据系统类型安装 Docker（使用华为云镜像源）
    case "$os_id" in
        ubuntu|debian)
            print_info "检测到 Debian/Ubuntu 系统，开始安装 Docker（使用华为云镜像源）..."
            
            # 卸载旧版本
            apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
            
            # 安装依赖
            apt-get update -qq > /dev/null 2>&1
            apt-get install -qq -y \
                ca-certificates \
                curl \
                gnupg \
                lsb-release > /dev/null 2>&1
            
            # 添加 Docker 官方 GPG 密钥（使用华为云镜像加速）
            install -m 0755 -d /etc/apt/keyrings
            # 尝试使用华为云镜像加速下载 GPG 密钥，如果失败则使用官方源
            if ! curl -fsSL --connect-timeout 10 --max-time 30 https://mirrors.huaweicloud.com/docker-ce/linux/$os_id/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg 2>/dev/null; then
                print_warning "华为云镜像下载 GPG 密钥失败，使用官方源..."
                curl -fsSL https://download.docker.com/linux/$os_id/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            fi
            chmod a+r /etc/apt/keyrings/docker.gpg
            
            # 设置仓库（使用华为云镜像源）
            echo \
              "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://mirrors.huaweicloud.com/docker-ce/linux/$os_id \
              $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            # 安装 Docker Engine（包含 docker-compose-plugin）
            apt-get update -qq > /dev/null 2>&1
            apt-get install -qq -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin > /dev/null 2>&1
            
            print_success "Docker 和 Docker Compose 已通过华为云镜像源安装完成"
            
            ;;
        centos|rhel|fedora)
            print_info "检测到 CentOS/RHEL/Fedora 系统，开始安装 Docker（使用华为云镜像源）..."
            
            # 卸载旧版本
            yum remove -y docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine 2>/dev/null || true
            
            # 安装依赖
            yum install -y yum-utils
            
            # 添加 Docker 仓库（使用华为云镜像源）
            if ! yum-config-manager --add-repo https://mirrors.huaweicloud.com/docker-ce/linux/centos/docker-ce.repo 2>/dev/null; then
                print_warning "华为云镜像添加仓库失败，使用官方源..."
                yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            fi
            
            # 安装 Docker Engine（包含 docker-compose-plugin）
            yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            
            print_success "Docker 和 Docker Compose 已通过华为云镜像源安装完成"
            
            ;;
        *)
            print_error "不支持的操作系统: $os_id"
            print_info "请手动安装 Docker 后重试"
            print_info "安装指南: https://docs.docker.com/get-docker/"
            return 1
            ;;
    esac
    
    # 配置 Docker data-root（在启动服务之前）
    if [ "$docker_data_root" != "/var/lib/docker" ]; then
        print_info "配置 Docker data-root 为: $docker_data_root"
        
        local docker_config_dir="/etc/docker"
        local docker_config_file="$docker_config_dir/daemon.json"
        
        mkdir -p "$docker_config_dir"
        
        # 读取或创建配置文件
        local config_content="{}"
        if [ -f "$docker_config_file" ]; then
            config_content=$(cat "$docker_config_file")
        fi
        
        # 使用 Python 更新配置
        python3 << EOF
import json
import sys

config_file = "$docker_config_file"
data_root = "$docker_data_root"

try:
    config = json.loads('''$config_content''')
except:
    config = {}

config["data-root"] = data_root

try:
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print("CONFIG_UPDATED")
except Exception as e:
    print(f"CONFIG_ERROR:{e}", file=sys.stderr)
    sys.exit(1)
EOF
        
        if [ $? -ne 0 ]; then
            print_error "配置 Docker data-root 失败"
            return 1
        fi
        
        print_success "Docker data-root 已配置为: $docker_data_root"
        print_warning "注意：如果 /var/lib/docker 已有数据，需要手动迁移到新路径"
    fi
    
    # 启动 Docker 服务
    print_info "启动 Docker 服务..."
    systemctl daemon-reload
    systemctl enable docker
    systemctl start docker
    
    # 验证安装
    if check_command docker; then
        print_success "Docker 安装完成: $(docker --version)"
        return 0
    else
        print_error "Docker 安装验证失败"
        return 1
    fi
}

# 安装 Docker Compose（使用项目内置二进制离线覆盖，无需联网）
install_docker_compose() {
    print_section "安装 Docker Compose"
    
    if [ "$EUID" -ne 0 ]; then
        print_warning "安装 Docker Compose 需要 root 权限，跳过自动安装"
        print_info "请使用 sudo 运行此脚本，或手动执行："
        bundled_compose_manual_hint
        return 1
    fi

    if ! bundled_compose_available; then
        print_error "当前架构 $(uname -m) 无内置 Docker Compose 离线包"
        return 1
    fi

    if ! install_bundled_docker_compose; then
        print_error "Docker Compose 离线安装失败"
        return 1
    fi

    if check_command docker-compose; then
        print_success "Docker Compose 安装完成: $(docker-compose --version)"
    elif docker compose version &> /dev/null; then
        print_success "Docker Compose 安装完成: $(docker compose version)"
    else
        print_error "Docker Compose 安装验证失败"
        return 1
    fi
    return 0
}

# 检查并安装 Docker
check_and_install_docker() {
    if check_command docker; then
        if check_docker_permission "$@"; then
            return 0
        else
            # Docker 未安装，继续安装流程
            print_warning "Docker 未安装"
        fi
    else
        print_warning "未检测到 Docker"
    fi
    
    echo ""
    print_info "Docker 是运行中间件服务的必需组件"
    echo ""
    
    while true; do
        echo -ne "${YELLOW}[提示]${NC} 是否自动安装 Docker？(y/N): "
        read -r response
        case "$response" in
            [yY][eE][sS]|[yY])
                if install_docker; then
                    print_success "Docker 安装成功"
                    # 安装后再次检查权限
                    if check_docker_permission "$@"; then
                        return 0
                    else
                        print_warning "Docker 安装成功但无法访问，请检查权限"
                        print_info "请确保当前用户在 docker 组中: sudo usermod -aG docker $USER"
                        return 1
                    fi
                else
                    print_warning "Docker 安装失败，请手动安装后重试"
                    print_info "安装指南: https://docs.docker.com/get-docker/"
                    return 1
                fi
                ;;
            [nN][oO]|[nN]|"")
                print_warning "Docker 是必需的，但安装流程将继续"
                print_info "请确保已安装 Docker，否则无法继续"
                print_info "安装指南: https://docs.docker.com/get-docker/"
                return 1
                ;;
            *)
                print_warning "请输入 y 或 N"
                ;;
        esac
    done
}

# 检查并安装 Docker Compose
check_and_install_docker_compose() {
    if check_command docker-compose || docker compose version &> /dev/null; then
        # 检查版本是否符合要求
        if check_docker_compose_version; then
            # 检查是 docker-compose 还是 docker compose
            if check_command docker-compose; then
                COMPOSE_CMD="docker-compose"
                print_success "Docker Compose 已安装: $(docker-compose --version)"
            else
                COMPOSE_CMD="docker compose"
                print_success "Docker Compose 已安装: $(docker compose version)"
            fi
            return 0
        else
            # 版本不符合要求，提示升级
            local current_version=""
            if check_command docker-compose; then
                current_version=$(docker-compose --version 2>&1)
            else
                current_version=$(docker compose version 2>&1)
            fi
            
            print_warning "Docker Compose 版本不符合要求（需要 v2.35.0+）"
            echo ""
            print_info "当前版本: $current_version"
            print_info "要求版本: v2.35.0 或更高"
            echo ""
            
            while true; do
                echo -ne "${YELLOW}[提示]${NC} 是否升级 Docker Compose？(y/N): "
                read -r response
                case "$response" in
                    [yY][eE][sS]|[yY])
                        if [ "$EUID" -ne 0 ]; then
                            print_warning "升级 Docker Compose 需要 root 权限，跳过自动升级"
                            print_info "请使用 sudo 运行此脚本，或手动执行："
                            bundled_compose_manual_hint
                            return 1
                        fi
                        if ! bundled_compose_available; then
                            print_error "当前架构 $(uname -m) 无内置 Docker Compose 离线包"
                            return 1
                        fi
                        if install_bundled_docker_compose && check_docker_compose_version; then
                            set_compose_cmd_from_system
                            print_success "Docker Compose 离线升级成功"
                            return 0
                        fi
                        print_warning "Docker Compose 离线升级后版本仍不符合要求"
                        return 1
                        ;;
                    [nN][oO]|[nN]|"")
                        print_warning "Docker Compose 版本不符合要求，但安装流程将继续"
                        print_info "请手动使用项目内置包升级到 v${COMPOSE_MIN_VERSION}+："
                        bundled_compose_manual_hint
                        return 1
                        ;;
                    *)
                        print_warning "请输入 y 或 N"
                        ;;
                esac
            done
        fi
    fi
    
    print_warning "未检测到 Docker Compose"
    echo ""
    print_info "Docker Compose 是运行中间件服务的必需组件"
    print_info "要求版本: v2.35.0 或更高"
    print_info "Docker Compose 将使用项目内置离线包安装（按当前系统架构，无需联网）"
    echo ""
    
    while true; do
        echo -ne "${YELLOW}[提示]${NC} 是否自动安装 Docker Compose？(y/N): "
        read -r response
        case "$response" in
            [yY][eE][sS]|[yY])
                if install_docker_compose; then
                    if check_docker_compose_version; then
                        print_success "Docker Compose 安装成功"
                        # 重新检查并设置 COMPOSE_CMD
                        if check_command docker-compose; then
                            COMPOSE_CMD="docker-compose"
                        else
                            COMPOSE_CMD="docker compose"
                        fi
                        return 0
                    else
                        print_warning "Docker Compose 安装后版本不符合要求"
                        return 1
                    fi
                else
                    print_warning "Docker Compose 安装失败，请手动安装后重试"
                    return 1
                fi
                ;;
            [nN][oO]|[nN]|"")
                print_warning "Docker Compose 是必需的，但安装流程将继续"
                print_info "请确保已安装 Docker Compose v2.35.0+"
                print_info "安装方法（离线，按架构覆盖）："
                bundled_compose_manual_hint
                return 1
                ;;
            *)
                print_warning "请输入 y 或 N"
                ;;
        esac
    done
}

# 检查 Docker 是否安装（保持向后兼容）
check_docker() {
    check_and_install_docker "$@"
}

# 检查 Docker Compose 是否安装（保持向后兼容）
check_docker_compose() {
    check_and_install_docker_compose
}

# 创建统一网络
create_network() {
    print_info "创建统一网络 easyaiot-network..."
    
    # 检查网络是否已存在
    if docker network ls | grep -q easyaiot-network; then
        print_info "网络 easyaiot-network 已存在，跳过创建"
        # 简化处理：如果网络已存在，直接使用，不进行任何测试（避免卡住）
        # 如果网络真的有问题，后续启动容器时会报错，届时再处理
        return 0
    fi
    
    # 创建网络（如果不存在或已删除）
    print_info "正在创建网络 easyaiot-network..."
    local create_output=$(docker network create easyaiot-network 2>&1)
    local create_exit_code=$?
    
    if [ $create_exit_code -eq 0 ]; then
        print_success "网络 easyaiot-network 已创建"
        return 0
    else
        # 检查错误原因
        if echo "$create_output" | grep -qi "already exists"; then
            print_info "网络 easyaiot-network 已存在（可能在检查后创建）"
            return 0
        elif echo "$create_output" | grep -qi "permission denied"; then
            print_error "没有权限创建 Docker 网络"
            print_info "请确保当前用户在 docker 组中，或使用 sudo 运行脚本"
            return 1
        elif echo "$create_output" | grep -qi "network with name.*already exists"; then
            print_warning "网络名称冲突，尝试使用不同的方法..."
            # 再次检查网络是否存在
            if docker network ls | grep -q easyaiot-network; then
                print_info "网络已存在，继续使用现有网络"
                return 0
            else
                print_error "无法创建网络: $create_output"
                return 1
            fi
        else
            print_error "无法创建网络 easyaiot-network"
            print_error "错误信息: $create_output"
            print_info "诊断建议："
            print_info "  1. 检查 Docker 服务是否正常运行: sudo systemctl status docker"
            print_info "  2. 检查当前用户是否有权限: docker network ls"
            print_info "  3. 查看 Docker 日志: sudo journalctl -u docker.service"
            return 1
        fi
    fi
}

# 检查 IP 地址是否为 Docker 网络 IP
is_docker_network_ip() {
    local ip="$1"
    if [ -z "$ip" ]; then
        return 1
    fi
    
    # Docker 默认网段：172.17.0.0/16 到 172.31.0.0/16
    # 这些是 Docker 自动分配的桥接网络网段
    if [[ "$ip" =~ ^172\.(1[7-9]|2[0-9]|3[0-1])\.[0-9]+\.[0-9]+$ ]]; then
        return 0  # 是 Docker 网络 IP
    fi
    
    return 1  # 不是 Docker 网络 IP
}

# 检查网络接口是否为 Docker 相关接口
is_docker_interface() {
    local iface="$1"
    if [ -z "$iface" ]; then
        return 1
    fi
    
    # Docker 相关接口名称模式
    if [[ "$iface" =~ ^(docker|br-|veth|br[0-9]+) ]]; then
        return 0  # 是 Docker 接口
    fi
    
    return 1  # 不是 Docker 接口
}

# 校验 IPv4 字面量（拒绝 metric/table 等被误当成 IP 的纯数字，如 2022）
is_valid_ipv4() {
    local ip="$1" o
    [[ "$ip" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]] || return 1
    IFS='.' read -r -a _octets <<< "$ip"
    for o in "${_octets[@]}"; do
        [ "$o" -le 255 ] 2>/dev/null || return 1
    done
    return 0
}

# 从「ip route get」输出中提取 src 地址（禁止用固定字段号，避免误取 metric/table）
_extract_route_src_ip() {
    local route_line="$1"
    if [[ "$route_line" =~ [[:space:]]src[[:space:]]+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) ]]; then
        echo "${BASH_REMATCH[1]}"
    fi
}

# 获取宿主机 IP 地址（排除 Docker 网络接口）
get_host_ip() {
    local host_ip=""
    
    # 方法1: 通过路由获取（最可靠，通常返回物理网络接口的 IP）
    if command -v ip &> /dev/null; then
        local route_line
        route_line=$(ip route get 8.8.8.8 2>/dev/null | head -n 1)
        host_ip=$(_extract_route_src_ip "$route_line")
        # 必须含 src 字段才是源地址；无 src 时 awk $7 可能误取 metric 2022 / table 2022
        if is_valid_ipv4 "$host_ip" && [ "$host_ip" != "127.0.0.1" ] && ! is_docker_network_ip "$host_ip"; then
            echo "$host_ip"
            return 0
        fi
    fi
    
    # 方法2: 通过 hostname -I 获取，过滤 Docker 网络 IP
    if command -v hostname &> /dev/null; then
        local all_ips=$(hostname -I 2>/dev/null)
        if [ -n "$all_ips" ]; then
            # 遍历所有 IP，找到第一个非 Docker 网络的 IP
            for ip in $all_ips; do
                if is_valid_ipv4 "$ip" && [ "$ip" != "127.0.0.1" ] && [[ ! "$ip" =~ ^169\.254\. ]] && ! is_docker_network_ip "$ip"; then
                    echo "$ip"
                    return 0
                fi
            done
        fi
    fi
    
    # 方法3: 通过 ip addr 获取，排除 Docker 接口和 Docker 网络 IP
    if command -v ip &> /dev/null; then
        # 获取所有网络接口的 IP，优先选择物理接口（eth*, enp*, ens*, eno*）
        local physical_ips=""
        local other_ips=""
        local current_iface=""
        
        while IFS= read -r line; do
            # 提取接口名称（格式：1: eth0: <...>）
            if [[ "$line" =~ ^[0-9]+:[[:space:]]+([^:]+): ]]; then
                current_iface="${BASH_REMATCH[1]}"
                # 跳过 Docker 接口
                if is_docker_interface "$current_iface"; then
                    current_iface=""
                    continue
                fi
            fi
            
            # 提取 IP 地址（格式：    inet 192.168.1.100/24 ...）
            if [ -n "$current_iface" ] && [[ "$line" =~ inet[[:space:]]+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) ]]; then
                local ip="${BASH_REMATCH[1]}"
                if is_valid_ipv4 "$ip" && [ "$ip" != "127.0.0.1" ] && [[ ! "$ip" =~ ^169\.254\. ]] && ! is_docker_network_ip "$ip"; then
                    # 检查是否是物理接口
                    if [[ "$current_iface" =~ ^(eth|enp|ens|eno|wlan|wlp) ]]; then
                        physical_ips="$physical_ips $ip"
                    else
                        other_ips="$other_ips $ip"
                    fi
                fi
            fi
        done < <(ip addr show 2>/dev/null)
        
        # 优先使用物理接口的 IP
        if [ -n "$physical_ips" ]; then
            host_ip=$(echo "$physical_ips" | awk '{print $1}')
            if [ -n "$host_ip" ]; then
                echo "$host_ip"
                return 0
            fi
        fi
        
        # 如果没有物理接口 IP，使用其他接口的 IP
        if [ -n "$other_ips" ]; then
            host_ip=$(echo "$other_ips" | awk '{print $1}')
            if [ -n "$host_ip" ]; then
                echo "$host_ip"
                return 0
            fi
        fi
    fi
    
    # 方法4: 通过 ifconfig 获取（兼容旧系统），排除 Docker 接口
    if command -v ifconfig &> /dev/null; then
        local current_iface=""
        while IFS= read -r line; do
            # 检测接口名称
            if [[ "$line" =~ ^([^[:space:]]+)[[:space:]]+ ]]; then
                current_iface="${BASH_REMATCH[1]}"
                # 跳过 Docker 接口
                if is_docker_interface "$current_iface"; then
                    current_iface=""
                    continue
                fi
            fi
            
            # 提取 IP 地址
            if [ -n "$current_iface" ] && [[ "$line" =~ inet[[:space:]]+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) ]]; then
                local ip="${BASH_REMATCH[1]}"
                if is_valid_ipv4 "$ip" && [ "$ip" != "127.0.0.1" ] && [[ ! "$ip" =~ ^169\.254\. ]] && ! is_docker_network_ip "$ip"; then
                    echo "$ip"
                    return 0
                fi
            fi
        done < <(ifconfig 2>/dev/null)
    fi
    
    # 如果所有方法都失败，返回空字符串
    echo ""
    return 1
}

# 在宿主机 /etc/hosts 中将 Kafka 解析为本机回环（供宿主机进程使用 Kafka:9092）
# Kafka 容器已映射 0.0.0.0:9092，127.0.0.1 最稳定；勿用 get_host_ip()（会误取 metric/VPN/tunnel 如 28.0.0.1）
# 跨机部署可导出 KAFKA_HOSTS_IP=中间件内网IP 覆盖
KAFKA_HOSTS_MARKER="# EasyAIoT Kafka (install_middleware_linux.sh)"
configure_kafka_hosts() {
    local host_ip hosts_file="/etc/hosts"
    local entry_line

    host_ip="${KAFKA_HOSTS_IP:-127.0.0.1}"
    if ! is_valid_ipv4 "$host_ip"; then
        host_ip="127.0.0.1"
        print_warning "KAFKA_HOSTS_IP 无效，Kafka hosts 将使用 127.0.0.1"
    fi

    print_info "配置宿主机 hosts：Kafka -> ${host_ip}（供宿主机进程连接 Kafka:9092）"
    entry_line="${host_ip}	Kafka ${KAFKA_HOSTS_MARKER}"

    if [ ! -f "$hosts_file" ]; then
        print_warning "未找到 $hosts_file，请手动添加: ${entry_line%%$'\t'*} Kafka"
        return 1
    fi

    if grep -qF "$KAFKA_HOSTS_MARKER" "$hosts_file" 2>/dev/null; then
        local current_ip
        current_ip=$(grep -F "$KAFKA_HOSTS_MARKER" "$hosts_file" | awk '{print $1}' | head -n 1)
        if [ "$current_ip" = "$host_ip" ]; then
            print_success "宿主机 hosts 已配置: Kafka -> $host_ip"
            return 0
        fi
    fi

    _apply_kafka_hosts_entry() {
        local tmp_hosts
        tmp_hosts=$(mktemp)
        grep -vF "$KAFKA_HOSTS_MARKER" "$hosts_file" 2>/dev/null \
            | grep -Ev '^[[:space:]]*([0-9]{1,3}\.){3}[0-9]{1,3}[[:space:]]+Kafka([[:space:]]|$)' \
            > "$tmp_hosts"
        printf '%s\n' "$entry_line" >> "$tmp_hosts"
        if cp "$tmp_hosts" "$hosts_file" 2>/dev/null; then
            rm -f "$tmp_hosts"
            return 0
        fi
        if command -v sudo &> /dev/null && sudo cp "$tmp_hosts" "$hosts_file" 2>/dev/null; then
            rm -f "$tmp_hosts"
            return 0
        fi
        rm -f "$tmp_hosts"
        return 1
    }

    if _apply_kafka_hosts_entry; then
        print_success "宿主机 hosts 已更新: Kafka -> $host_ip"
        return 0
    fi

    print_warning "无法写入 $hosts_file（需要 root 权限），请手动添加:"
    print_warning "  $entry_line"
    return 1
}


# 创建目录并智能设置 777 权限（owner 非空时一并 chown）。
# 已存在目录只设顶层权限，避免对海量数据递归 chmod 卡顿；新建目录或 FORCE_CHMOD=true 时递归。
# 用法: set_data_dir_perms <owner|""> <dir> [dir2 ...]  返回 0=成功 1=无权限/失败
set_data_dir_perms() {
    local owner="$1"; shift
    local d R SUDO rc=0
    for d in "$@"; do
        R="-R"
        [ -d "$d" ] && [ "$FORCE_CHMOD" != "true" ] && R=""
        mkdir -p "$d" 2>/dev/null || true
        SUDO=""
        if [ "$EUID" -ne 0 ]; then
            command -v sudo &>/dev/null && SUDO="sudo" || { rc=1; continue; }
        fi
        [ -z "$owner" ] || $SUDO chown $R "$owner" "$d" 2>/dev/null || true
        $SUDO chmod $R 777 "$d" 2>/dev/null || rc=1
    done
    return $rc
}

# 创建并设置 NodeRED 数据目录权限
create_nodered_directories() {
    local nodered_data_dir="${SCRIPT_DIR}/nodered_data/data"
    print_info "创建 NodeRED 数据目录并设置权限..."
    if set_data_dir_perms "1000:1000" "$nodered_data_dir"; then
        print_success "NodeRED 数据目录权限已设置 (UID 1000:1000, 777)"
    else
        print_warning "无法设置 NodeRED 目录权限，请手动执行: sudo chmod -R 777 $nodered_data_dir"
    fi
}

# 创建并设置 FUXA 数据目录权限（工程 / 历史 / 日志 / 图片）
create_fuxa_directories() {
    local fuxa_root="${SCRIPT_DIR}/fuxa_data"
    local dirs=(
        "${fuxa_root}/appdata"
        "${fuxa_root}/db"
        "${fuxa_root}/logs"
        "${fuxa_root}/images"
    )
    print_info "创建 FUXA 数据目录并设置权限..."
    local ok=true
    for d in "${dirs[@]}"; do
        if ! set_data_dir_perms "1000:1000" "$d"; then
            ok=false
            print_warning "无法设置 FUXA 目录权限，请手动执行: sudo chmod -R 777 $d"
        fi
    done
    if [ "$ok" = true ]; then
        print_success "FUXA 数据目录权限已设置 (UID 1000:1000, 777)"
    fi
}

# 创建并设置 PostgreSQL 数据目录权限
create_postgresql_directories() {
    local postgresql_data_dir="${SCRIPT_DIR}/db_data/data"
    local postgresql_log_dir="${SCRIPT_DIR}/db_data/log"
    print_info "创建 PostgreSQL 数据目录并设置权限..."
    if set_data_dir_perms "999:999" "$postgresql_data_dir" "$postgresql_log_dir"; then
        print_success "PostgreSQL 数据目录权限已设置 (UID 999:999, 777)"
    else
        print_warning "无法设置 PostgreSQL 目录权限，请手动执行: sudo chmod -R 777 $postgresql_data_dir $postgresql_log_dir"
    fi
}

# 创建并设置 Redis 数据目录权限
create_redis_directories() {
    local redis_data_dir="${SCRIPT_DIR}/redis_data/data"
    local redis_log_dir="${SCRIPT_DIR}/redis_data/logs"
    print_info "创建 Redis 数据目录并设置权限..."
    if set_data_dir_perms "999:999" "$redis_data_dir" "$redis_log_dir"; then
        print_success "Redis 数据目录权限已设置 (UID 999:999, 777)"
    else
        print_warning "无法设置 Redis 目录权限，请手动执行: sudo chmod -R 777 $redis_data_dir $redis_log_dir"
    fi
}

# 创建并设置 Kafka 数据目录权限
create_kafka_directories() {
    local kafka_data_dir="${SCRIPT_DIR}/mq_data/data"
    
    print_info "创建 Kafka 数据目录并设置权限..."
    
    # 检查文件系统是否可写
    local parent_dir=$(dirname "$kafka_data_dir")
    if ! check_filesystem_writable "$parent_dir"; then
        print_error "无法创建 Kafka 数据目录: $kafka_data_dir"
        print_error "原因: 父目录 $parent_dir 所在文件系统不可写"
        print_error "请检查文件系统挂载状态并解决只读问题"
        return 1
    fi
    
    # 创建目录（带只读文件系统错误检测）
    local mkdir_output=""
    mkdir_output=$(mkdir -p "$kafka_data_dir" 2>&1)
    local mkdir_exit_code=$?
    
    if [ $mkdir_exit_code -ne 0 ]; then
        print_error "创建 Kafka 数据目录失败: $kafka_data_dir"
        print_error "错误信息: $mkdir_output"
        
        # 检查是否是只读文件系统错误
        if echo "$mkdir_output" | grep -qiE "read-only|readonly|read only|permission denied"; then
            print_error "检测到文件系统只读错误"
            echo ""
            print_error "文件系统挂载信息:"
            df -h "$parent_dir" 2>/dev/null || true
            echo ""
            print_error "请检查文件系统挂载状态并解决只读问题"
        fi
        return 1
    fi
    
    # Kafka 容器默认使用 UID 1000, GID 1000 (appuser 用户)
    if set_data_dir_perms "1000:1000" "$kafka_data_dir"; then
        print_success "Kafka 数据目录权限已设置 (UID 1000:1000, 777)"
    else
        print_warning "无法设置 Kafka 目录权限，请手动执行: sudo chmod -R 777 $kafka_data_dir"
    fi
}

# 检查文件系统是否可写
check_filesystem_writable() {
    local test_path="$1"
    local test_file=""
    
    # 如果路径是目录，在目录内创建测试文件
    if [ -d "$test_path" ]; then
        test_file="${test_path}/.write_test_$$"
    else
        # 如果路径不存在，尝试创建父目录并测试
        local parent_dir=$(dirname "$test_path")
        if [ ! -d "$parent_dir" ]; then
            # 尝试创建父目录
            if ! mkdir -p "$parent_dir" 2>/dev/null; then
                return 1
            fi
        fi
        test_file="${parent_dir}/.write_test_$$"
    fi
    
    # 尝试创建测试文件
    if touch "$test_file" 2>/dev/null; then
        rm -f "$test_file" 2>/dev/null
        return 0
    else
        return 1
    fi
}

# 检查文件系统挂载状态
check_filesystem_mount_status() {
    local path="$1"
    
    # 获取路径所在的挂载点
    local mount_point=$(df "$path" 2>/dev/null | tail -1 | awk '{print $6}')
    local mount_info=$(df -h "$path" 2>/dev/null | tail -1)
    local filesystem=$(echo "$mount_info" | awk '{print $1}')
    local mount_options=""
    
    # 获取挂载选项
    if [ -f /proc/mounts ]; then
        mount_options=$(grep -E "^${filesystem}[[:space:]]" /proc/mounts 2>/dev/null | awk '{print $4}' | head -1 || echo "")
    fi
    
    # 检查是否包含 ro (read-only)
    if echo "$mount_options" | grep -qE "(^|,)ro(,|$)"; then
        return 1  # 只读
    fi
    
    return 0  # 可写
}

# 创建所有中间件的存储目录
create_all_storage_directories() {
    print_info "创建所有中间件存储目录..."
    
    # 首先检查脚本目录所在文件系统是否可写
    if ! check_filesystem_writable "$SCRIPT_DIR"; then
        print_error "文件系统只读错误：无法在 $SCRIPT_DIR 创建目录"
        echo ""
        print_error "检测到文件系统为只读状态，无法创建数据目录"
        echo ""
        
        # 检查挂载状态
        if ! check_filesystem_mount_status "$SCRIPT_DIR"; then
            print_error "文件系统挂载为只读模式"
            print_info "挂载信息:"
            df -h "$SCRIPT_DIR" 2>/dev/null | tail -1 || true
            echo ""
        fi
        
        print_warning "解决方案："
        echo ""
        print_info "1. 检查文件系统挂载状态："
        print_info "   mount | grep $(df "$SCRIPT_DIR" 2>/dev/null | tail -1 | awk '{print $1}')"
        echo ""
        print_info "2. 如果是只读挂载，需要重新挂载为可写："
        print_info "   sudo mount -o remount,rw $(df "$SCRIPT_DIR" 2>/dev/null | tail -1 | awk '{print $1}')"
        echo ""
        print_info "3. 或者将项目部署到可写的文件系统，例如："
        print_info "   - /home/用户名/easyaiot"
        print_info "   - /data/easyaiot"
        print_info "   - /var/lib/easyaiot"
        echo ""
        print_info "4. 检查磁盘空间是否已满："
        print_info "   df -h"
        echo ""
        print_error "无法继续安装，请先解决文件系统只读问题"
        exit 1
    fi
    
    # 定义所有需要创建的存储目录及其权限设置
    # 格式: "目录路径:UID:GID:权限"
    local storage_dirs=(
        "${SCRIPT_DIR}/standalone-logs:::"              # Nacos 日志（使用默认权限）
        "${SCRIPT_DIR}/db_data/data:999:999:777"       # PostgreSQL 数据
        "${SCRIPT_DIR}/db_data/log:999:999:777"        # PostgreSQL 日志
        "${SCRIPT_DIR}/taos_data/data:::"              # TDengine 数据（使用默认权限）
        "${SCRIPT_DIR}/taos_data/log:::"               # TDengine 日志（使用默认权限）
        "${SCRIPT_DIR}/redis_data/data:999:999:777"   # Redis 数据
        "${SCRIPT_DIR}/redis_data/logs:999:999:777"    # Redis 日志
        "${SCRIPT_DIR}/mq_data/data:1000:1000:777"    # Kafka 数据（uid=1000, gid=1000）
        "${SCRIPT_DIR}/minio_data/data:::"             # MinIO 数据（使用默认权限）
        "${SCRIPT_DIR}/minio_data/config:::"           # MinIO 配置（使用默认权限）
        "${SCRIPT_DIR}/milvus_data:::"                 # Milvus 数据（使用默认权限）
        "${SCRIPT_DIR}/milvus_config:::"               # Milvus 嵌入式 etcd 配置
        "${SCRIPT_DIR}/srs_data/conf:::"               # SRS 配置（使用默认权限）
        "${SCRIPT_DIR}/srs_data/data:::"              # SRS 数据（使用默认权限）
        "${SCRIPT_DIR}/srs_data/playbacks:::"          # SRS 回放（使用默认权限）
        "${SCRIPT_DIR}/nodered_data/data:1000:1000:777" # NodeRED 数据
        "${SCRIPT_DIR}/fuxa_data/appdata:1000:1000:777" # FUXA 工程数据
        "${SCRIPT_DIR}/fuxa_data/db:1000:1000:777"      # FUXA 历史库
        "${SCRIPT_DIR}/fuxa_data/logs:1000:1000:777"    # FUXA 日志
        "${SCRIPT_DIR}/fuxa_data/images:1000:1000:777"  # FUXA 图片
        "${SCRIPT_DIR}/../zlmediakit/www:::"         # ZLMediaKit Web 目录（使用默认权限）
        "${SCRIPT_DIR}/../zlmediakit/log:::"         # ZLMediaKit 日志（使用默认权限）
        "${SCRIPT_DIR}/../zlmediakit/conf:::"        # ZLMediaKit 配置（使用默认权限）
    )
    local created_count=0
    local total_count=${#storage_dirs[@]}
    local failed_dirs=()

    if [ "$FORCE_CHMOD" = "true" ]; then
        print_info "FORCE_CHMOD=true：对所有已存在目录做完整递归 chmod 修复（数据量大时会较慢）..."
    fi

    for dir_spec in "${storage_dirs[@]}"; do
        # 解析目录规格
        IFS=':' read -r dir_path uid gid perms <<< "$dir_spec"
        
        if [ -z "$dir_path" ]; then
            continue
        fi
        
        # 检查父目录是否可写
        local parent_dir=$(dirname "$dir_path")
        if ! check_filesystem_writable "$parent_dir"; then
            print_error "无法创建目录: $dir_path"
            print_error "原因: 父目录 $parent_dir 所在文件系统不可写"
            failed_dirs+=("$dir_path")
            continue
        fi
        
        # 创建目录（记录是否为已存在的目录：已存在则只设置顶层权限，避免对海量数据文件做递归 chmod 导致卡顿）
        local pre_existing="false"
        [ -d "$dir_path" ] && pre_existing="true"
        local R="-R"
        # 已存在目录默认只设顶层权限（去掉 -R）；FORCE_CHMOD=true 时强制递归兜底修复
        [ "$pre_existing" = "true" ] && [ "$FORCE_CHMOD" != "true" ] && R=""

        local mkdir_output=""
        mkdir_output=$(mkdir -p "$dir_path" 2>&1)
        local mkdir_exit_code=$?

        if [ $mkdir_exit_code -eq 0 ]; then
            # 如果指定了 UID/GID，尝试设置权限
            if [ -n "$uid" ] && [ -n "$gid" ]; then
                run_priv chown $R "${uid}:${gid}" "$dir_path" 2>/dev/null || true
                run_priv chmod $R 777 "$dir_path" 2>/dev/null || true
            else
                # 即使没有指定 UID/GID，也设置777权限
                run_priv chmod $R 777 "$dir_path" 2>/dev/null || true
            fi
            created_count=$((created_count + 1))
        else
            print_error "创建目录失败: $dir_path"
            print_error "错误信息: $mkdir_output"
            failed_dirs+=("$dir_path")
            
            # 检查是否是只读文件系统错误
            if echo "$mkdir_output" | grep -qiE "read-only|readonly|read only|permission denied"; then
                print_error "检测到文件系统只读错误"
                echo ""
                print_error "文件系统挂载信息:"
                df -h "$parent_dir" 2>/dev/null || true
                echo ""
                print_error "请检查文件系统挂载状态并解决只读问题"
                echo ""
            fi
        fi
    done
    
    # 注意：上面的创建循环已对每个目录设置好权限（新建目录递归、已存在目录仅顶层），
    # 此处不再重复递归 chmod，避免对已存在的海量数据目录做无意义的全量扫描导致卡顿。

    # 同时设置所有父目录为777权限（仅顶层，父目录的数据子目录已在上面单独处理）
    local parent_dirs=(
        "${SCRIPT_DIR}/standalone-logs"
        "${SCRIPT_DIR}/db_data"
        "${SCRIPT_DIR}/taos_data"
        "${SCRIPT_DIR}/redis_data"
        "${SCRIPT_DIR}/mq_data"
        "${SCRIPT_DIR}/minio_data"
        "${SCRIPT_DIR}/milvus_data"
        "${SCRIPT_DIR}/milvus_config"
        "${SCRIPT_DIR}/srs_data"
        "${SCRIPT_DIR}/nodered_data"
        "${SCRIPT_DIR}/fuxa_data"
        "${SCRIPT_DIR}/../zlmediakit"
        "${SCRIPT_DIR}/logs"
    )
    # 默认只设父目录顶层权限；FORCE_CHMOD=true 时递归兜底修复
    local PR=""
    [ "$FORCE_CHMOD" = "true" ] && PR="-R"
    for parent_dir in "${parent_dirs[@]}"; do
        if [ -d "$parent_dir" ]; then
            run_priv chmod $PR 777 "$parent_dir" 2>/dev/null || true
        fi
    done

    # SRS 容器绑定宿主机 ~/easyaiot/data -> 容器 /data（与 docker-compose.yml 一致）
    # 注意：只对数据根目录顶层和 playbacks 设权限，绝不对整个目录树递归
    local _host_data_dir="${EASYAIOT_HOST_DATA_DIR:-$HOME/easyaiot/data}"
    run_priv mkdir -p "${_host_data_dir}/playbacks" 2>/dev/null || true
    run_priv chmod 777 "${_host_data_dir}" "${_host_data_dir}/playbacks" 2>/dev/null || true
    
    if [ $created_count -eq $total_count ]; then
        print_success "所有存储目录已创建并设置为777权限（${created_count}/${total_count}）"
    else
        print_error "部分存储目录创建失败（${created_count}/${total_count}）"
        if [ ${#failed_dirs[@]} -gt 0 ]; then
            echo ""
            print_error "失败的目录列表:"
            for failed_dir in "${failed_dirs[@]}"; do
                print_error "  - $failed_dir"
            done
            echo ""
            print_error "这可能导致容器启动失败，请先解决文件系统问题"
            exit 1
        fi
    fi
}

# 准备 EMQX 容器和数据卷
prepare_emqx_volumes() {
    print_info "准备 EMQX 容器和数据卷..."
    
    # 检查 Docker 是否可用
    if ! docker ps &> /dev/null; then
        print_warning "无法访问 Docker，跳过 EMQX 容器清理"
        return 0
    fi
    
    # 检查是否存在旧的 EMQX 容器
    local old_container=$(docker ps -a --filter "name=emqx-server" --format "{{.Names}}" 2>/dev/null | head -n 1)
    
    if [ -n "$old_container" ]; then
        print_info "发现旧的 EMQX 容器: $old_container"
        
        # 停止容器
        if docker stop "$old_container" &> /dev/null; then
            print_info "已停止旧容器: $old_container"
        fi
        
        # 删除容器
        if docker rm -f "$old_container" &> /dev/null; then
            print_success "已删除旧容器: $old_container"
        else
            print_warning "删除旧容器失败: $old_container"
        fi
    else
        print_info "未发现旧的 EMQX 容器"
    fi
    
    # 清理旧的宿主机目录（如果存在，现在使用具名卷不再需要）
    local old_data_dir="${SCRIPT_DIR}/emqx_data"
    if [ -d "$old_data_dir" ]; then
        print_info "发现旧的 EMQX 数据目录: $old_data_dir"
        print_warning "注意：现在使用 Docker 具名卷，旧的宿主机目录可以删除"
        print_info "如需保留数据，请手动备份后再删除"
        
        # 询问是否删除旧目录（可选）
        # 为了自动化，这里默认不删除，只提示
        print_info "旧数据目录保留在: $old_data_dir（如需删除请手动执行: rm -rf $old_data_dir）"
    fi
    
    # 确保 Docker 具名卷已创建（Docker Compose 会自动创建）
    print_info "EMQX 将使用 Docker 具名卷存储数据（自动创建）"
    print_success "EMQX 容器和数据卷准备完成"
}

# 获取 Docker 网络网关 IP（用于容器访问宿主机服务）
get_docker_network_gateway() {
    local network_name="${1:-easyaiot-network}"
    local gateway_ip=""
    
    # 方法1: 如果网络已存在，直接获取网关IP
    if docker network inspect "$network_name" >/dev/null 2>&1; then
        gateway_ip=$(docker network inspect "$network_name" --format='{{range .IPAM.Config}}{{.Gateway}}{{end}}' 2>/dev/null | head -n 1)
        if [ -n "$gateway_ip" ] && [[ "$gateway_ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "$gateway_ip"
            return 0
        fi
    fi
    
    # 方法2: 如果网络不存在，尝试创建网络后获取
    if ! docker network inspect "$network_name" >/dev/null 2>&1; then
        if docker network create "$network_name" >/dev/null 2>&1; then
            gateway_ip=$(docker network inspect "$network_name" --format='{{range .IPAM.Config}}{{.Gateway}}{{end}}' 2>/dev/null | head -n 1)
            if [ -n "$gateway_ip" ] && [[ "$gateway_ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
                echo "$gateway_ip"
                return 0
            fi
        fi
    fi
    
    # 方法3: 使用默认Docker网关IP（通常是172.17.0.1或172.18.0.1）
    if command -v ip &> /dev/null; then
        gateway_ip=$(ip addr show docker0 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d/ -f1)
        if [ -n "$gateway_ip" ] && [[ "$gateway_ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "$gateway_ip"
            return 0
        fi
    fi
    
    # 方法4: 使用常见的Docker网络网关IP
    echo "172.18.0.1"
    return 0
}

# 准备 ZLMediaKit 配置文件
prepare_zlmediakit_config() {
    local zlm_config_dir="${SCRIPT_DIR}/../zlmediakit/conf"
    local zlm_config_file="${zlm_config_dir}/config.ini"
    
    print_info "准备 ZLMediaKit 配置文件..."
    
    # 创建目标目录
    mkdir -p "$zlm_config_dir"
    
    # 检查配置文件是否已存在
    if [ -f "$zlm_config_file" ]; then
        print_success "ZLMediaKit 配置文件已存在: $zlm_config_file"
        # 确保关闭 ZLM 录像（录像由 SRS 负责）
        if grep -q '^enableFmp4=1' "$zlm_config_file" 2>/dev/null; then
            sed -i 's/^enableFmp4=1/enableFmp4=0/' "$zlm_config_file"
            print_info "已关闭 ZLMediaKit fmp4 录像: enableFmp4=0"
        fi
        if grep -q '^enable_mp4=1' "$zlm_config_file" 2>/dev/null; then
            sed -i 's/^enable_mp4=1/enable_mp4=0/' "$zlm_config_file"
            print_info "已关闭 ZLMediaKit mp4 录像: enable_mp4=0"
        fi
        return 0
    else
        print_warning "ZLMediaKit 配置文件不存在，将创建默认配置"
    fi
    
    # 如果复制失败或源文件不存在，创建默认配置文件
    print_info "创建默认 ZLMediaKit 配置文件..."
    cat > "$zlm_config_file" << 'EOF'
[api]
apiDebug=1
defaultSnap=./www/logo.png
downloadRoot=./www;
secret=AdJQu9CMnwZvCc139s8lF0F9dhk6sNXG
snapRoot=./www/snap/

[cluster]
origin_url=
retry_count=3
timeout_sec=15

[ffmpeg]
bin=/usr/bin/ffmpeg
cmd=%s -re -i %s -c:a aac -strict -2 -ar 44100 -ab 48k -c:v libx264 -f flv %s
log=./ffmpeg/ffmpeg.log
restart_sec=0
snap=%s -rtsp_transport tcp -i %s -y -f mjpeg -frames:v 1 %s

[general]
broadcast_player_count_changed=0
check_nvidia_dev=1
enableVhost=0
enable_ffmpeg_log=0
flowThreshold=1024
listen_ip=::
maxStreamWaitMS=15000
mediaServerId=zlmediakit-local
mergeWriteMS=0
resetWhenRePlay=1
streamNoneReaderDelayMS=20000
unready_frame_cache=100
wait_add_track_ms=3000
wait_audio_track_data_ms=1000
wait_track_ready_ms=10000

[hls]
broadcastRecordTs=0
deleteDelaySec=10
fastRegister=0
fileBufSize=65536
segDelay=0
segDur=2
segKeep=0
segNum=3
segRetain=5

[hook]
alive_interval=10.0
enable=0
on_flow_report=
on_http_access=
on_play=
on_publish=
on_record_mp4=
on_record_ts=
on_rtp_server_timeout=
on_rtsp_auth=
on_rtsp_realm=
on_send_rtp_stopped=
on_server_exited=
on_server_keepalive=
on_server_started=
on_shell_login=
on_stream_changed=
on_stream_none_reader=
on_stream_not_found=
retry=1
retry_delay=3.0
stream_changed_schemas=rtsp/rtmp/fmp4/ts/hls/hls.fmp4
timeoutSec=30

[http]
allow_cross_domains=1
allow_ip_range=
charSet=utf-8
dirMenu=1
forbidCacheSuffix=
forwarded_ip_header=
keepAliveSecond=30
maxReqSize=40960
port=80
rootPath=./www
sendBufSize=65536
sslport=443
virtualPath=

[multicast]
addrMax=239.255.255.255
addrMin=239.0.0.0
udpTTL=64

[protocol]
add_mute_audio=1
auto_close=0
continue_push_ms=3000
enable_audio=1
enable_fmp4=1
enable_hls=0
enable_hls_fmp4=0
enable_mp4=0
enable_rtmp=1
enable_rtsp=1
enable_ts=1
fmp4_demand=0
hls_demand=0
hls_save_path=./www
modify_stamp=2
mp4_as_player=0
mp4_max_second=3600
mp4_save_path=./www
paced_sender_ms=0
rtmp_demand=0
rtsp_demand=0
ts_demand=0

[record]
appName=record
enableFmp4=0
fastStart=0
fileBufSize=65536
fileRepeat=0
sampleMS=500

[rtc]
bfilter=0
datachannel_echo=0
externIP=
maxRtpCacheMS=5000
maxRtpCacheSize=2048
max_bitrate=0
min_bitrate=0
nackIntervalRatio=1.0
nackMaxCount=15
nackMaxMS=3000
nackMaxSize=2048
nackRtpSize=8
port=8000
preferredCodecA=PCMA,PCMU,opus,mpeg4-generic
preferredCodecV=H264,H265,AV1,VP9,VP8
rembBitRate=0
start_bitrate=0
tcpPort=8000
timeoutSec=30

[rtmp]
directProxy=1
enhanced=0
handshakeSecond=15
keepAliveSecond=15
port=10001
sslport=0

[rtp]
audioMtuSize=600
h264_stap_a=1
lowLatency=0
rtpMaxSize=10
videoMtuSize=1400

[rtp_proxy]
dumpDir=
gop_cache=1
h264_pt=98
h265_pt=99
merge_frame=1
opus_pt=100
port=10003
port_range=30000-30500
ps_pt=96
rtp_g711_dur_ms=100
timeoutSec=15
udp_recv_socket_buffer=4194304

[rtsp]
authBasic=0
directProxy=1
handshakeSecond=15
keepAliveSecond=15
lowLatency=0
port=10002
rtpTransportType=-1
sslport=0

[shell]
maxReqSize=1024
port=0

[srt]
latencyMul=4
passPhrase=
pktBufSize=8192
port=9000
timeoutSec=5
EOF
    
    # 验证文件是否创建成功
    if [ -f "$zlm_config_file" ]; then
        print_success "默认 ZLMediaKit 配置文件已创建: $zlm_config_file"
        return 0
    else
        print_error "无法创建 ZLMediaKit 配置文件: $zlm_config_file"
        return 1
    fi
}

# 从 ZLM 配置文件中读取 api.secret（ZLM HTTP API 必须带 secret，否则报 Required parameter missed: "secret"）
get_zlm_api_secret() {
    local conf="$SCRIPT_DIR/../zlmediakit/conf/config.ini"
    if [ -f "$conf" ]; then
        awk -F= '/^\[api\]/ { in_api=1; next } /^\[/ { in_api=0 } in_api && $1=="secret" { gsub(/^[ \t]+|[ \t]+$/,"",$2); print $2; exit }' "$conf"
    fi
}

# 等待 ZLMediaKit 服务就绪
wait_for_zlmediakit() {
    local max_attempts=60
    local attempt=0
    local zlm_secret
    zlm_secret=$(get_zlm_api_secret)
    
    print_info "等待 ZLMediaKit 服务就绪..."
    while [ $attempt -lt $max_attempts ]; do
        if [ -n "$zlm_secret" ]; then
            if curl -s --connect-timeout 2 "http://localhost:6080/index/api/getServerConfig?secret=$zlm_secret" > /dev/null 2>&1; then
                print_success "ZLMediaKit 服务已就绪"
                return 0
            fi
        else
            if curl -s --connect-timeout 2 "http://localhost:6080/index/api/getServerConfig" > /dev/null 2>&1; then
                print_success "ZLMediaKit 服务已就绪"
                return 0
            fi
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    print_error "ZLMediaKit 服务未就绪"
    return 1
}

# 在安装 SRS 之前创建宿主机 ~/easyaiot/data（SRS 配置中 srs_log_file、dvr_path 使用容器内 /data）
ensure_host_data_directory_before_srs() {
    local _host_data_dir="${EASYAIOT_HOST_DATA_DIR:-$HOME/easyaiot/data}"
    print_info "安装 SRS 前检查宿主机目录 ${_host_data_dir} ..."
    # 注意：只对数据根目录顶层和 playbacks 设权限，绝不对整个目录树递归
    local created=0
    if run_priv mkdir -p "${_host_data_dir}/playbacks" 2>/dev/null; then
        run_priv chmod 777 "${_host_data_dir}" "${_host_data_dir}/playbacks" 2>/dev/null || true
        created=1
    fi
    if [ "$created" -eq 1 ]; then
        print_success "宿主机目录已就绪: ${_host_data_dir}（含 playbacks 子目录）"
    else
        print_warning "无法在宿主机创建 ${_host_data_dir}（请使用 root/sudo 执行安装，或手动: mkdir -p ${_host_data_dir}/playbacks && chmod 777 ${_host_data_dir} ${_host_data_dir}/playbacks）。"
    fi
}

# 按部署形态写入 SRS http_hooks（SRS 使用 host 网络）
_apply_srs_http_hooks() {
    local srs_config_file="$1"
    local gateway_ip="$2"
    local on_publish_url on_dvr_url

    if is_mini_deploy_profile; then
        local video_port="${FLASK_RUN_PORT:-6000}"
        local host_ip=$(get_host_ip)
        on_publish_url="http://${host_ip}:${video_port}/video/camera/callback/on_publish"
        on_dvr_url="http://${host_ip}:${video_port}/video/camera/callback/on_dvr"
        print_info "mini 形态：SRS Hook 直连 VIDEO 服务 ${on_publish_url}（无 Gateway）"
    else
        on_publish_url="http://${gateway_ip}:48080/admin-api/video/camera/callback/on_publish"
        on_dvr_url="http://${gateway_ip}:48080/admin-api/video/camera/callback/on_dvr"
        print_info "SRS Hook 经 Gateway: http://${gateway_ip}:48080/admin-api/video/camera/callback/*"
    fi

    sed -i -E "s|on_dvr[[:space:]]+http://[^;]+;|on_dvr              ${on_dvr_url};|g" "$srs_config_file"
    sed -i -E "s|on_publish[[:space:]]+http://[^;]+;|on_publish          ${on_publish_url};|g" "$srs_config_file"
}

# 准备 SRS 配置文件
# 强制更新模式：无论配置文件是否存在，都重新生成并自动替换 IP 地址
prepare_srs_config() {
    ensure_host_data_directory_before_srs

    local srs_config_source="${SCRIPT_DIR}/../srs/conf"
    local srs_config_target="${SCRIPT_DIR}/srs_data/conf"
    local srs_config_file="${srs_config_target}/docker.conf"
    
    print_info "准备 SRS 配置文件..."
    
    # 获取宿主机 IP 地址（用于VIDEO服务，如果VIDEO在宿主机运行）
    local host_ip=$(get_host_ip)
    if [ -z "$host_ip" ]; then
        print_warning "无法获取宿主机 IP，将使用 127.0.0.1（可能导致 VIDEO 模块回调失败）"
        host_ip="127.0.0.1"
    else
        print_info "检测到宿主机 IP: $host_ip"
    fi
    
    # 获取 Docker 网络网关 IP（用于Gateway服务，如果Gateway在宿主机运行）
    local gateway_ip=$(get_docker_network_gateway "easyaiot-network")
    if [ -z "$gateway_ip" ]; then
        print_warning "无法获取 Docker 网络网关 IP，将使用 172.18.0.1"
        gateway_ip="172.18.0.1"
    else
        print_info "检测到 Docker 网络网关 IP: $gateway_ip"
    fi
    
    # 创建目标目录
    mkdir -p "$srs_config_target"
    
    # 强制更新模式：无论配置文件是否存在，都重新生成
    print_info "重新获取 IP 地址并重新生成配置文件..."
    
    # 尝试从源目录复制配置文件
    if [ -d "$srs_config_source" ] && [ -f "$srs_config_source/docker.conf" ]; then
        print_info "从源目录复制 SRS 配置文件..."
        if cp -f "$srs_config_source/docker.conf" "$srs_config_file" 2>/dev/null; then
            _apply_srs_http_hooks "$srs_config_file" "$gateway_ip"
            print_success "SRS 配置文件已复制并更新: $srs_config_source/docker.conf -> $srs_config_file"
            # 验证文件确实存在
            if [ -f "$srs_config_file" ]; then
                return 0
            fi
        else
            print_warning "无法复制 SRS 配置文件，将创建默认配置"
        fi
    else
        print_warning "源配置文件不存在: $srs_config_source/docker.conf，将创建默认配置"
    fi
    
    # 如果复制失败或源文件不存在，创建默认配置文件
    print_info "创建默认 SRS 配置文件..."
    local on_publish_url on_dvr_url
    if is_mini_deploy_profile; then
        local video_port="${FLASK_RUN_PORT:-6000}"
        on_publish_url="http://${host_ip}:${video_port}/video/camera/callback/on_publish"
        on_dvr_url="http://${host_ip}:${video_port}/video/camera/callback/on_dvr"
    else
        on_publish_url="http://${gateway_ip}:48080/admin-api/video/camera/callback/on_publish"
        on_dvr_url="http://${gateway_ip}:48080/admin-api/video/camera/callback/on_dvr"
    fi
    cat > "$srs_config_file" << EOF
# SRS Docker 配置文件
# 用于 Docker 容器部署的 SRS 配置

listen              1935;
max_connections     1000;
daemon              on;
srs_log_tank        file;
srs_log_file        /data/srs.log;

http_server {
    enabled         on;
    listen          8080;
    dir             ./objs/nginx/html;
}

http_api {
    enabled         on;
    listen          1985;
    raw_api {
        enabled             on;
        allow_reload        on;
    }
}
stats {
    network         0;
}
rtc_server {
    enabled on;
    listen 8000;
    candidate *;
}

vhost __defaultVhost__ {
    http_remux {
        enabled     on;
        mount       [vhost]/[app]/[stream].flv;
    }
    rtc {
        enabled     on;
        rtmp_to_rtc on;
        rtc_to_rtmp on;
    }
    dvr {
        enabled             on;
        dvr_path            /data/playbacks/[app]/[stream]/[2006]/[01]/[02]/[timestamp].flv;
        dvr_plan            segment;
        dvr_duration        30;
        dvr_wait_keyframe   on;
    }
    http_hooks {
        enabled             on;
        on_dvr              ${on_dvr_url};
        on_publish          ${on_publish_url};
    }
}
EOF
    
    # 验证文件是否创建成功
    if [ -f "$srs_config_file" ]; then
        print_success "默认 SRS 配置文件已创建: $srs_config_file"
        if is_mini_deploy_profile; then
            print_info "  - VIDEO 回调地址: ${on_publish_url}"
        else
            print_info "  - Gateway 回调地址: http://${gateway_ip}:48080/admin-api/video/camera/callback/*"
        fi
        return 0
    else
        print_error "无法创建 SRS 配置文件: $srs_config_file"
        return 1
    fi
}

# 检查docker-compose.yml是否存在
check_compose_file() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "docker-compose.yml文件不存在: $COMPOSE_FILE"
        exit 1
    fi
}

# PostgreSQL 是否已结束 docker-entrypoint 首次初始化（空数据目录时会先跑 initdb.d 再重启）
_postgresql_entrypoint_init_done() {
    local logs
    logs=$(docker logs postgres-server 2>&1 || true)
    if echo "$logs" | grep -q "Skipping initialization"; then
        return 0
    fi
    if echo "$logs" | grep -q "PostgreSQL init process complete"; then
        return 0
    fi
    return 1
}

# 确认 PostgreSQL 可执行业务 SQL（非恢复中、非启动中）
_postgresql_accepts_queries() {
    docker exec postgres-server pg_isready -U postgres > /dev/null 2>&1 \
        || return 1
    docker exec postgres-server psql -U postgres -d postgres -tAc "SELECT 1" > /dev/null 2>&1 \
        || return 1
    # WAL 恢复或未达一致状态时 pg_isready 可能已通过，但查询会失败
    local _in_recovery
    _in_recovery=$(docker exec postgres-server psql -U postgres -d postgres -tAc "SELECT pg_is_in_recovery();" 2>/dev/null || echo "t")
    [ "$_in_recovery" = "f" ]
}

# 等待 PostgreSQL 服务就绪
wait_for_postgresql() {
    # 首次安装需导入约 20MB SQL，entrypoint init 可能超过 2 分钟
    local max_attempts=180
    local attempt=0
    local stable_checks=0
    local required_stable=3
    
    print_info "等待 PostgreSQL 服务就绪..."

    # 容器不存在 → 快速失败，不浪费轮询
    if ! docker ps -a --filter "name=^postgres-server$" --format "{{.Names}}" | grep -q "^postgres-server$"; then
        print_error "PostgreSQL 容器不存在（postgres-server），无法等待"
        return 1
    fi

    while [ $attempt -lt $max_attempts ]; do
        # 检查容器是否在运行
        if ! docker ps --filter "name=postgres-server" --format "{{.Names}}" | grep -q "postgres-server"; then
            stable_checks=0
            if [ $attempt -eq 0 ]; then
                print_warning "PostgreSQL 容器未运行，等待启动..."
            fi
            # 容器不存在（已退出）且重试超过 10 次 → 失败
            if [ $attempt -gt 10 ]; then
                local _pg_status; _pg_status=$(container_status postgres-server 2>/dev/null || echo "missing")
                if [ "$_pg_status" = "exited" ] || [ "$_pg_status" = "dead" ]; then
                    print_error "PostgreSQL 容器已退出/死亡（状态: ${_pg_status}），不会自动恢复"
                    print_info "查看日志: docker logs postgres-server --tail 50"
                    return 1
                fi
            fi
            attempt=$((attempt + 1))
            sleep 2
            continue
        fi

        # 首次启动：entrypoint 仍在执行 initdb.d（含 init-databases.sh）时不可建库
        if ! _postgresql_entrypoint_init_done; then
            stable_checks=0
            if [ $((attempt % 5)) -eq 0 ]; then
                print_info "PostgreSQL 首次初始化中（entrypoint 正在执行 initdb.d 脚本），继续等待..."
            fi
            attempt=$((attempt + 1))
            sleep 2
            continue
        fi
        
        # pg_isready 仅检查 socket 是否监听；需实际查询 + 非 recovery + 连续稳定
        if _postgresql_accepts_queries; then
            stable_checks=$((stable_checks + 1))
            if [ $stable_checks -ge $required_stable ]; then
                print_success "PostgreSQL 服务已就绪"
                return 0
            fi
        else
            if [ $stable_checks -gt 0 ]; then
                print_info "PostgreSQL 连接不稳定（可能正在重启或 WAL 恢复），继续等待..."
            elif docker exec postgres-server pg_isready -U postgres > /dev/null 2>&1; then
                print_info "PostgreSQL 正在崩溃恢复或启动中（pg_isready 已通过但查询尚未可用），继续等待..."
            fi
            stable_checks=0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    print_error "PostgreSQL 服务未就绪（已等待 $((max_attempts * 2))s）"
    print_info "查看日志: docker logs postgres-server --tail 80"
    return 1
}

# 重置 PostgreSQL 密码（确保密码与配置一致）
reset_postgresql_password() {
    print_section "重置 PostgreSQL 密码"
    
    # 等待 PostgreSQL 就绪（增加等待时间，确保数据库完全初始化）
    if ! wait_for_postgresql; then
        print_warning "PostgreSQL 未就绪，跳过密码重置"
        return 1
    fi
    
    # wait_for_postgresql 已用 pg_isready 确认可接受连接，无需再固定等待 5s
    
    # 从 docker-compose.yml 中读取配置的密码
    local target_password="iot45722414822"
    
    print_info "正在重置 postgres 用户密码为: $target_password"
    
    # 尝试通过容器内部重置密码
    # 方法1: 使用本地连接（不需要密码，通过 Unix socket）
    local reset_attempts=0
    local max_reset_attempts=10
    local reset_success=0
    
    while [ $reset_attempts -lt $max_reset_attempts ] && [ $reset_success -eq 0 ]; do
        # 尝试重置密码（使用本地连接，不需要密码）
        local reset_output=$(docker exec postgres-server psql -U postgres -d postgres -c "ALTER USER postgres WITH PASSWORD '$target_password';" 2>&1)
        local reset_exit_code=$?
        
        if [ $reset_exit_code -eq 0 ]; then
            print_success "PostgreSQL 密码重置成功"
            reset_success=1
            
            # 重新加载配置
            docker exec postgres-server psql -U postgres -d postgres -c "SELECT pg_reload_conf();" > /dev/null 2>&1 || true
            
            # 验证密码是否正确设置（使用新密码测试）
            sleep 3
            local verify_output=$(docker exec postgres-server psql -U postgres -d postgres -c "SELECT version();" 2>&1)
            local verify_exit_code=$?
            
            if [ $verify_exit_code -eq 0 ]; then
                print_success "PostgreSQL 密码验证通过"
                return 0
            else
                print_warning "密码重置成功，但验证时出现问题"
                print_info "验证输出: $verify_output"
                # 即使验证失败，也认为重置成功（可能是其他原因导致的验证失败）
                return 0
            fi
        else
            reset_attempts=$((reset_attempts + 1))
            if [ $reset_attempts -lt $max_reset_attempts ]; then
                print_warning "密码重置失败，正在重试 ($reset_attempts/$max_reset_attempts)..."
                print_info "错误信息: $reset_output"
                sleep 5
            fi
        fi
    done
    
    if [ $reset_success -eq 0 ]; then
        print_error "PostgreSQL 密码重置失败（已重试 $max_reset_attempts 次）"
        print_info "可能的原因："
        print_info "  1. 数据库正在初始化中，请稍后重试"
        print_info "  2. 容器权限问题"
        print_info "  3. 数据库数据目录损坏"
        echo ""
        print_info "手动修复命令："
        print_info "  docker exec postgres-server psql -U postgres -d postgres -c \"ALTER USER postgres WITH PASSWORD '$target_password';\""
        print_info "或者重启容器后重试："
        print_info "  docker restart postgres-server"
        print_info "  sleep 10"
        print_info "  docker exec postgres-server psql -U postgres -d postgres -c \"ALTER USER postgres WITH PASSWORD '$target_password';\""
        return 1
    fi
    
    return 0
}

# 确保 PostgreSQL 密码正确（可以在任何时候调用，用于修复密码问题）
ensure_postgresql_password() {
    print_section "确保 PostgreSQL 密码正确"
    
    # 检查容器是否在运行
    if ! docker ps --filter "name=postgres-server" --format "{{.Names}}" | grep -q "postgres-server"; then
        print_warning "PostgreSQL 容器未运行，无法检查密码"
        return 1
    fi
    
    # 等待 PostgreSQL 就绪
    if ! wait_for_postgresql; then
        print_warning "PostgreSQL 未就绪，无法检查密码"
        return 1
    fi
    
    local target_password="iot45722414822"
    
    # 测试当前密码是否正确
    print_info "测试当前 PostgreSQL 密码..."
    
    # 方法1: 使用环境变量测试密码（如果容器支持）
    local test_result=$(docker exec -e PGPASSWORD="$target_password" postgres-server psql -U postgres -d postgres -c "SELECT 1;" 2>&1)
    local test_exit_code=$?
    
    if [ $test_exit_code -eq 0 ]; then
        print_success "PostgreSQL 密码正确，无需重置"
        return 0
    fi
    
    # 方法2: 使用本地连接测试（不需要密码）
    local local_test=$(docker exec postgres-server psql -U postgres -d postgres -c "SELECT 1;" 2>&1)
    local local_test_exit_code=$?
    
    if [ $local_test_exit_code -eq 0 ]; then
        # 本地连接成功，说明可以通过本地连接重置密码
        print_info "可以通过本地连接重置密码，正在重置..."
        if reset_postgresql_password; then
            return 0
        else
            return 1
        fi
    else
        print_warning "无法通过本地连接访问数据库"
        print_info "错误信息: $local_test"
        print_info "尝试重置密码..."
        if reset_postgresql_password; then
            return 0
        else
            return 1
        fi
    fi
}

# 配置 PostgreSQL pg_hba.conf 允许从宿主机连接
configure_postgresql_pg_hba() {
    print_section "配置 PostgreSQL pg_hba.conf"
    
    # 等待 PostgreSQL 就绪
    if ! wait_for_postgresql; then
        print_warning "PostgreSQL 未就绪，跳过 pg_hba.conf 配置"
        return 1
    fi
    
    print_info "配置 pg_hba.conf 以允许从宿主机连接..."
    
    # 在容器内读取当前的 pg_hba.conf
    local pg_hba_path="/var/lib/postgresql/data/pg_hba.conf"
    local pg_hba_backup_path="/var/lib/postgresql/data/pg_hba.conf.backup"
    
    # 先备份原文件
    if docker exec postgres-server cp "$pg_hba_path" "$pg_hba_backup_path" 2>/dev/null; then
        print_info "已备份 pg_hba.conf"
    fi
    
    # 检查是否已经配置了允许所有主机连接的规则
    local has_host_all=$(docker exec postgres-server grep -E "^host\s+all\s+all\s+0\.0\.0\.0/0\s+md5" "$pg_hba_path" 2>/dev/null || echo "")
    
    if [ -n "$has_host_all" ]; then
        print_info "pg_hba.conf 已包含允许所有主机连接的配置"
    else
        print_info "添加允许所有主机连接的配置..."
        
        # 在容器内添加配置（使用 echo 命令）
        if docker exec postgres-server sh -c "echo '' >> $pg_hba_path && echo '# 允许从宿主机和所有网络连接（由安装脚本自动添加）' >> $pg_hba_path && echo 'host    all             all             0.0.0.0/0               md5' >> $pg_hba_path && echo 'host    all             all             ::/0                    md5' >> $pg_hba_path" 2>/dev/null; then
            print_success "已添加允许所有主机连接的配置"
        else
            print_warning "添加配置时出现问题，尝试使用另一种方法..."
            
            # 备用方法：使用临时文件
            local temp_file=$(mktemp)
            cat > "$temp_file" << 'EOF'

# 允许从宿主机和所有网络连接（由安装脚本自动添加）
host    all             all             0.0.0.0/0               md5
host    all             all             ::/0                    md5
EOF
            if docker cp "$temp_file" postgres-server:/tmp/pg_hba_append.conf 2>/dev/null && \
               docker exec postgres-server sh -c "cat /tmp/pg_hba_append.conf >> $pg_hba_path && rm /tmp/pg_hba_append.conf" 2>/dev/null; then
                print_success "已通过临时文件添加配置"
            else
                print_error "无法添加配置，请手动检查 pg_hba.conf"
                rm -f "$temp_file"
                return 1
            fi
            rm -f "$temp_file"
        fi
    fi
    
    # 检查 postgresql.conf 配置（注意：listen_addresses 的修改需要重启容器才能生效）
    print_info "检查 postgresql.conf 配置..."
    local postgresql_conf_path="/var/lib/postgresql/data/postgresql.conf"
    local listen_addresses=$(docker exec postgres-server grep -E "^listen_addresses\s*=" "$postgresql_conf_path" 2>/dev/null | head -1 || echo "")
    
    # PostgreSQL 容器默认应该已经配置为监听所有接口
    # 这里只做检查，不修改（因为修改需要重启容器）
    if [ -n "$listen_addresses" ]; then
        if echo "$listen_addresses" | grep -q "'\*'"; then
            print_info "listen_addresses 已正确配置为 '*'"
        else
            print_warning "listen_addresses 配置可能不正确: $listen_addresses"
            print_info "PostgreSQL 容器默认应该监听所有接口，如果连接有问题，请检查容器配置"
        fi
    else
        print_info "未找到 listen_addresses 配置（将使用默认值，通常为 '*'）"
    fi
    
    # 重新加载配置
    print_info "重新加载 PostgreSQL 配置..."
    if docker exec postgres-server psql -U postgres -d postgres -c "SELECT pg_reload_conf();" > /dev/null 2>&1; then
        print_success "PostgreSQL 配置已重新加载"
        
        # 验证配置是否生效（等待一下让配置生效）
        sleep 2
        
        # 测试从宿主机连接（如果 psql 可用）
        if command -v psql &> /dev/null; then
            local test_password="iot45722414822"
            export PGPASSWORD="$test_password"
            if psql -h 127.0.0.1 -p 5432 -U postgres -d postgres -c "SELECT 1;" > /dev/null 2>&1; then
                print_success "宿主机连接测试成功"
                unset PGPASSWORD
                return 0
            else
                print_warning "宿主机连接测试失败（可能需要检查防火墙或网络配置）"
                unset PGPASSWORD
            fi
        else
            print_info "未安装 psql 客户端，跳过连接测试"
        fi
        
        return 0
    else
        print_warning "无法重新加载 PostgreSQL 配置（可能需要重启容器）"
        print_info "如果连接仍有问题，请重启 PostgreSQL 容器: docker restart postgres-server"
        return 1
    fi
}

# 配置 PostgreSQL max_connections（最大连接数）
configure_postgresql_max_connections() {
    print_section "配置 PostgreSQL 最大连接数"
    
    # 等待 PostgreSQL 就绪
    if ! wait_for_postgresql; then
        print_warning "PostgreSQL 未就绪，跳过 max_connections 配置"
        return 1
    fi
    
    # 目标最大连接数（可根据需要调整）
    local target_max_connections=10240
    
    print_info "配置 PostgreSQL max_connections 为: $target_max_connections"
    
    # 检查当前 max_connections 配置
    local current_max_conn=$(docker exec postgres-server psql -U postgres -d postgres -t -c "SHOW max_connections;" 2>/dev/null | tr -d ' ' || echo "")
    
    if [ -n "$current_max_conn" ] && [ "$current_max_conn" = "$target_max_connections" ]; then
        print_success "PostgreSQL max_connections 已正确配置为: $target_max_connections"
        return 0
    fi
    
    if [ -n "$current_max_conn" ]; then
        print_info "当前 max_connections: $current_max_conn，将更新为: $target_max_connections"
    fi
    
    # 方法1: 通过修改 postgresql.conf 文件（需要重启容器才能生效）
    local postgresql_conf_path="/var/lib/postgresql/data/postgresql.conf"
    local pgdata_dir="/var/lib/postgresql/data/pgdata"
    
    # 如果使用 PGDATA 子目录，配置文件路径需要调整
    if docker exec postgres-server test -f "$pgdata_dir/postgresql.conf" 2>/dev/null; then
        postgresql_conf_path="$pgdata_dir/postgresql.conf"
    fi
    
    # 备份配置文件
    if docker exec postgres-server test -f "$postgresql_conf_path" 2>/dev/null; then
        docker exec postgres-server cp "$postgresql_conf_path" "${postgresql_conf_path}.backup.$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
        print_info "已备份 postgresql.conf"
    fi
    
    # 检查配置文件中是否已有 max_connections 设置
    local has_max_conn=$(docker exec postgres-server grep -E "^max_connections\s*=" "$postgresql_conf_path" 2>/dev/null || echo "")
    
    if [ -n "$has_max_conn" ]; then
        # 更新现有配置
        print_info "更新现有 max_connections 配置..."
        if docker exec postgres-server sed -i "s/^max_connections\s*=.*/max_connections = $target_max_connections/" "$postgresql_conf_path" 2>/dev/null; then
            print_success "已更新 postgresql.conf 中的 max_connections 配置"
        else
            print_warning "更新配置文件失败，尝试使用 SQL 命令设置..."
            # 使用 ALTER SYSTEM 命令（PostgreSQL 9.4+）
            if docker exec postgres-server psql -U postgres -d postgres -c "ALTER SYSTEM SET max_connections = $target_max_connections;" > /dev/null 2>&1; then
                print_success "已通过 ALTER SYSTEM 命令设置 max_connections"
                # 重新加载配置
                docker exec postgres-server psql -U postgres -d postgres -c "SELECT pg_reload_conf();" > /dev/null 2>&1 || true
                print_warning "注意：max_connections 的修改需要重启 PostgreSQL 容器才能完全生效"
            else
                print_error "无法设置 max_connections"
                return 1
            fi
        fi
    else
        # 添加新配置
        print_info "添加 max_connections 配置到 postgresql.conf..."
        if docker exec postgres-server sh -c "echo '' >> $postgresql_conf_path && echo '# 最大连接数配置（由安装脚本自动添加）' >> $postgresql_conf_path && echo 'max_connections = $target_max_connections' >> $postgresql_conf_path" 2>/dev/null; then
            print_success "已添加 max_connections 配置到 postgresql.conf"
        else
            # 使用 ALTER SYSTEM 命令作为备用方案
            print_warning "添加配置到文件失败，尝试使用 ALTER SYSTEM 命令..."
            if docker exec postgres-server psql -U postgres -d postgres -c "ALTER SYSTEM SET max_connections = $target_max_connections;" > /dev/null 2>&1; then
                print_success "已通过 ALTER SYSTEM 命令设置 max_connections"
                # 重新加载配置
                docker exec postgres-server psql -U postgres -d postgres -c "SELECT pg_reload_conf();" > /dev/null 2>&1 || true
                print_warning "注意：max_connections 的修改需要重启 PostgreSQL 容器才能完全生效"
            else
                print_error "无法设置 max_connections"
                return 1
            fi
        fi
    fi
    
    # 注意：max_connections 需要重启容器才能生效
    print_warning "重要提示：max_connections 的修改需要重启 PostgreSQL 容器才能完全生效"
    print_info "当前配置已更新，但新值将在容器重启后生效"
    print_info "如需立即生效，请执行: docker restart postgres-server"
    
    # 验证配置（虽然需要重启才能生效，但可以检查配置是否正确写入）
    sleep 2
    local verify_max_conn=$(docker exec postgres-server psql -U postgres -d postgres -t -c "SHOW max_connections;" 2>/dev/null | tr -d ' ' || echo "")
    
    if [ -n "$verify_max_conn" ]; then
        if [ "$verify_max_conn" = "$target_max_connections" ]; then
            print_success "max_connections 配置已生效: $verify_max_conn"
        else
            print_info "当前 max_connections: $verify_max_conn（配置已更新，重启容器后将变为: $target_max_connections）"
        fi
    fi
    
    return 0
}

# 等待 Nacos 服务就绪
wait_for_nacos() {
    local max_attempts=60
    local attempt=0
    
    print_info "等待 Nacos 服务就绪..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s --connect-timeout 2 "http://localhost:8848/nacos/actuator/health" > /dev/null 2>&1; then
            print_success "Nacos 服务已就绪"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    print_error "Nacos 服务未就绪"
    return 1
}

# 准备 Milvus 嵌入式 etcd 配置（v2.6+ standalone 模式必需）
prepare_milvus_config() {
    local config_dir="${SCRIPT_DIR}/milvus_config"
    mkdir -p "$config_dir"

    if [ ! -f "${config_dir}/embedEtcd.yaml" ]; then
        print_info "生成 Milvus 嵌入式 etcd 配置: ${config_dir}/embedEtcd.yaml"
        cat > "${config_dir}/embedEtcd.yaml" << 'EOF'
listen-client-urls: http://0.0.0.0:2379
advertise-client-urls: http://0.0.0.0:2379
quota-backend-bytes: 4294967296
auto-compaction-mode: revision
auto-compaction-retention: '1000'
EOF
    fi

    if [ ! -f "${config_dir}/user.yaml" ]; then
        print_info "生成 Milvus 用户配置: ${config_dir}/user.yaml"
        cat > "${config_dir}/user.yaml" << 'EOF'
# Extra config to override default milvus.yaml
EOF
    fi
}

# 等待 Milvus 向量数据库就绪
wait_for_milvus() {
    local max_attempts=90
    local attempt=0

    print_info "等待 Milvus 向量数据库就绪..."

    if ! docker ps -a --filter "name=^milvus-server$" --format "{{.Names}}" | grep -q "^milvus-server$"; then
        print_error "Milvus 容器 milvus-server 不存在"
        return 1
    fi

    while [ $attempt -lt $max_attempts ]; do
        if ! docker ps --filter "name=^milvus-server$" --format "{{.Names}}" | grep -q "^milvus-server$"; then
            local container_status
            container_status=$(docker ps -a --filter "name=^milvus-server$" --format "{{.Status}}" 2>/dev/null | head -1 || echo "未知")
            if [ $((attempt % 10)) -eq 0 ]; then
                print_warning "Milvus 容器未运行，当前状态: $container_status"
            fi
            attempt=$((attempt + 1))
            sleep 2
            continue
        fi

        if curl -sf --connect-timeout 2 "http://localhost:9091/healthz" > /dev/null 2>&1; then
            print_success "Milvus 向量数据库已就绪"
            print_info "  健康检查: http://localhost:9091/healthz"
            print_info "  gRPC 端口: localhost:19530"
            return 0
        fi

        if [ $((attempt % 10)) -eq 0 ] && [ $attempt -gt 0 ]; then
            local health_status
            health_status=$(docker inspect --format='{{.State.Health.Status}}' milvus-server 2>/dev/null || echo "none")
            print_info "等待 Milvus 就绪... ($attempt/$max_attempts)，容器健康状态: $health_status"
        fi

        attempt=$((attempt + 1))
        sleep 2
    done

    print_error "Milvus 向量数据库未在预期时间内就绪"
    local final_status
    final_status=$(docker ps -a --filter "name=^milvus-server$" --format "{{.Status}}" 2>/dev/null | head -1 || echo "未知")
    print_info "容器状态: $final_status"
    print_info "Milvus 容器日志（最近 30 行）:"
    docker logs --tail 30 milvus-server 2>&1 | while IFS= read -r line; do
        print_info "  $line"
    done || print_warning "无法获取 Milvus 容器日志"
    echo ""
    print_warning "诊断建议："
    print_info "1. 查看完整日志: docker logs milvus-server"
    print_info "2. 或: ./install_middleware_linux.sh logs Milvus"
    print_info "3. 确认 docker-compose.yml 含 DEPLOY_MODE=STANDALONE 与 milvus_config 挂载"
    return 1
}

# 等待 Kafka 服务就绪
wait_for_kafka() {
    local max_attempts=90  # 增加等待次数（从60增加到90，总共3分钟）
    local attempt=0
    
    print_info "等待 Kafka 服务就绪..."
    
    # 首先检查容器是否存在
    if ! docker ps -a --filter "name=kafka-server" --format "{{.Names}}" | grep -q "kafka-server"; then
        print_error "Kafka 容器 kafka-server 不存在"
        return 1
    fi
    
    # 检查容器是否在运行
    local container_status=$(docker ps --filter "name=kafka-server" --format "{{.Status}}" 2>/dev/null | head -1 || echo "")
    if [ -z "$container_status" ]; then
        print_warning "Kafka 容器未运行，尝试启动..."
        docker start kafka-server > /dev/null 2>&1 || true
        # 无需固定 sleep：下方 while 循环本身就是就绪轮询
    fi
    
    while [ $attempt -lt $max_attempts ]; do
        # 检查容器是否在运行
        if ! docker ps --filter "name=kafka-server" --format "{{.Names}}" | grep -q "kafka-server"; then
            if [ $attempt -eq 0 ]; then
                print_warning "Kafka 容器未运行，等待启动..."
            fi
            attempt=$((attempt + 1))
            sleep 2
            continue
        fi
        
        # 方法1: 使用 kafka-broker-api-versions 命令测试（与 docker-compose healthcheck 一致）
        local check_result=""
        local check_error=""
        check_result=$(docker exec kafka-server /opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server localhost:9092 2>&1)
        local check_exit_code=$?
        
        if [ $check_exit_code -eq 0 ]; then
            print_success "Kafka 服务已就绪"
            return 0
        fi
        
        # 方法2: 如果方法1失败，尝试使用 kafka-topics.sh 命令
        if [ $check_exit_code -ne 0 ]; then
            check_result=$(docker exec kafka-server /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list 2>&1)
            check_exit_code=$?
            if [ $check_exit_code -eq 0 ]; then
                print_success "Kafka 服务已就绪（通过 topics 命令验证）"
                return 0
            fi
        fi
        
        # 显示进度（每10次显示一次）
        if [ $((attempt % 10)) -eq 0 ] && [ $attempt -gt 0 ]; then
            print_info "等待中... ($attempt/$max_attempts) - 检查容器状态..."
            # 显示容器状态
            local container_info=$(docker ps --filter "name=kafka-server" --format "{{.Status}}" 2>/dev/null || echo "未运行")
            print_info "容器状态: $container_info"
        fi
        
        attempt=$((attempt + 1))
        sleep 2
    done
    
    # 超时后输出详细错误信息
    print_error "Kafka 服务未就绪（等待超时）"
    
    # 检查容器状态
    local container_status=$(docker ps -a --filter "name=kafka-server" --format "{{.Status}}" 2>/dev/null | head -1 || echo "")
    if [ -n "$container_status" ]; then
        print_info "容器状态: $container_status"
    else
        print_error "无法获取容器状态"
    fi
    
    # 输出容器日志的最后几行
    print_info "查看 Kafka 容器日志（最后20行）..."
    docker logs --tail 20 kafka-server 2>&1 | while IFS= read -r line; do
        print_info "  $line"
    done || print_warning "无法获取容器日志"
    
    # 提供诊断建议
    echo ""
    print_warning "诊断建议："
    print_info "1. 检查容器是否正常运行: docker ps | grep kafka"
    print_info "2. 查看完整日志: docker logs kafka-server"
    print_info "3. 检查端口是否被占用: ss -tlnp | grep 9092"
    print_info "4. 尝试手动启动: docker start kafka-server"
    print_info "5. 检查数据目录权限: ls -la .scripts/docker/mq_data/data"
    
    return 1
}

# IoT 业务 Kafka 主题（分区数，与 docker-compose KAFKA_NUM_PARTITIONS 一致）
KAFKA_IOT_TOPIC_PARTITIONS="${KAFKA_IOT_TOPIC_PARTITIONS:-${KAFKA_ALERT_TOPIC_PARTITIONS:-64}}"
KAFKA_ALERT_TOPIC_PARTITIONS="${KAFKA_IOT_TOPIC_PARTITIONS}"
KAFKA_IOT_TOPICS=(
    "iot-alert-notification"
    "iot-alert-notification-send"
    "iot-snapshot-alert"
    "iot-snapshot-alert-notification-send"
    "iot-face-matching"
    "iot-face-matching-result"
    "iot-plate-matching"
    "iot-plate-matching-result"
    "iot-post-process-request"
    "iot-post-process-result"
)
# 兼容旧变量名
KAFKA_ALERT_TOPICS=("${KAFKA_IOT_TOPICS[@]}")

# 创建或扩容 IoT Kafka 主题至指定分区数（告警 / 人脸匹配 / 车牌匹配）
init_kafka_iot_topics() {
    local topic partitions current_partitions alter_output create_output describe_output

    if ! docker ps --filter "name=kafka-server" --format "{{.Names}}" | grep -q "kafka-server"; then
        print_warning "Kafka 容器未运行，跳过 IoT 主题初始化"
        return 1
    fi

    wait_for_kafka || {
        print_warning "Kafka 未就绪，跳过 IoT 主题初始化"
        return 1
    }

    partitions="${KAFKA_IOT_TOPIC_PARTITIONS}"
    print_info "初始化 IoT Kafka 主题（目标分区数: ${partitions}）..."

    for topic in "${KAFKA_IOT_TOPICS[@]}"; do
        describe_output=$(docker exec kafka-server /opt/kafka/bin/kafka-topics.sh \
            --bootstrap-server localhost:9092 \
            --describe --topic "$topic" 2>&1) || true

        if echo "$describe_output" | grep -q "Topic: ${topic}"; then
            current_partitions=$(echo "$describe_output" | grep -E "PartitionCount:|Partition:" | head -n 1 | grep -oE '[0-9]+' | head -n 1)
            if [ -z "$current_partitions" ]; then
                current_partitions=$(echo "$describe_output" | grep -c "Partition:" || echo "0")
            fi
            if [ -n "$current_partitions" ] && [ "$current_partitions" -ge "$partitions" ] 2>/dev/null; then
                print_success "主题 ${topic} 已存在，分区数 ${current_partitions}（>= ${partitions}）"
                continue
            fi
            print_info "扩容主题 ${topic}: ${current_partitions:-未知} -> ${partitions} 分区"
            alter_output=$(docker exec kafka-server /opt/kafka/bin/kafka-topics.sh \
                --bootstrap-server localhost:9092 \
                --alter --topic "$topic" --partitions "$partitions" 2>&1) || true
            if echo "$alter_output" | grep -qiE "error|exception|failed"; then
                print_warning "主题 ${topic} 扩容失败: ${alter_output}"
            else
                print_success "主题 ${topic} 已扩容至 ${partitions} 分区"
            fi
        else
            print_info "创建主题 ${topic}（${partitions} 分区）..."
            create_output=$(docker exec kafka-server /opt/kafka/bin/kafka-topics.sh \
                --bootstrap-server localhost:9092 \
                --create --if-not-exists \
                --topic "$topic" \
                --partitions "$partitions" \
                --replication-factor 1 2>&1) || true
            if echo "$create_output" | grep -qiE "error|exception|failed"; then
                if echo "$create_output" | grep -qi "already exists"; then
                    print_success "主题 ${topic} 已存在"
                else
                    print_warning "主题 ${topic} 创建失败: ${create_output}"
                fi
            else
                print_success "主题 ${topic} 已创建（${partitions} 分区）"
            fi
        fi
    done

    print_info "IoT Kafka 主题列表:"
    docker exec kafka-server /opt/kafka/bin/kafka-topics.sh \
        --bootstrap-server localhost:9092 --list 2>/dev/null | grep -E '^iot-(alert|snapshot|face-matching|plate-matching)' || true
    return 0
}

# 兼容旧函数名
init_kafka_alert_topics() {
    init_kafka_iot_topics "$@"
}


# 等待 TDengine 服务就绪
wait_for_tdengine() {
    local max_attempts=90
    local attempt=0
    
    print_info "等待 TDengine 服务就绪..."
    
    # 首先检查容器是否在运行
    if ! docker ps --format "{{.Names}}" | grep -q "^tdengine-server$"; then
        print_error "TDengine 容器未运行"
        return 1
    fi
    
    while [ $attempt -lt $max_attempts ]; do
        # 检查容器健康状态
        local health_status=$(docker inspect --format='{{.State.Health.Status}}' tdengine-server 2>/dev/null || echo "none")
        
        # 检查进程是否在运行
        if ! docker exec tdengine-server pgrep -f taosd > /dev/null 2>&1; then
            if [ $attempt -gt 10 ]; then
                print_error "TDengine 进程未运行"
                print_info "检查容器日志:"
                docker logs --tail 20 tdengine-server 2>&1 | head -n 10
                return 1
            fi
        fi
        
        # 使用 taos 命令测试连接（带超时）
        local test_result=$(timeout 5 docker exec tdengine-server taos -h localhost -s "select 1;" 2>&1)
        local exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            # 再次确认，检查集群状态（避免 cluster_id 为 0 的情况）
            local cluster_check=$(timeout 5 docker exec tdengine-server taos -h localhost -s "show dnodes;" 2>&1 | grep -c "localhost\|online" || echo "0")
            if [ "$cluster_check" -gt 0 ]; then
                print_success "TDengine 服务已就绪（连接测试通过，集群状态正常）"
                return 0
            else
                if [ $attempt -gt 30 ]; then
                    print_warning "TDengine 连接成功但集群状态异常（cluster_id可能为0），继续等待..."
                fi
            fi
        elif [ $exit_code -eq 124 ]; then
            if [ $attempt -gt 20 ]; then
                print_warning "TDengine 连接超时，继续等待..."
            fi
        fi
        
        attempt=$((attempt + 1))
        if [ $((attempt % 10)) -eq 0 ]; then
            print_info "  等待中... ($attempt/$max_attempts)"
            if [ "$health_status" != "none" ]; then
                print_info "  容器健康状态: $health_status"
            fi
        fi
        sleep 2
    done
    
    print_error "TDengine 服务未就绪（等待了 $((max_attempts * 2)) 秒）"
    print_info "检查容器状态:"
    docker ps -a --filter "name=tdengine-server" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    print_info "检查容器日志（最后20行）:"
    docker logs --tail 20 tdengine-server 2>&1
    return 1
}

# 检查 TDengine 数据库是否存在
check_tdengine_database() {
    local db_name=$1
    
    # 检查数据库是否存在（通过查询系统数据库）
    local result=$(docker exec tdengine-server taos -h localhost -s "show databases;" 2>/dev/null | grep -w "$db_name" || echo "")
    if [ -n "$result" ]; then
        return 0  # 数据库存在
    else
        return 1  # 数据库不存在
    fi
}

# 创建 TDengine 数据库
create_tdengine_database() {
    local db_name=$1
    
    print_info "创建 TDengine 数据库: $db_name"
    
    # 首先验证 TDengine 服务是否就绪
    if ! timeout 5 docker exec tdengine-server taos -h localhost -s "select 1;" > /dev/null 2>&1; then
        print_error "TDengine 服务未就绪，无法创建数据库"
        return 1
    fi
    
    # 检查数据库是否已存在
    if check_tdengine_database "$db_name"; then
        print_info "TDengine 数据库 $db_name 已存在，跳过创建"
        return 0
    fi
    
    # 创建数据库（使用 if not exists 避免重复创建错误，添加超时）
    local output=$(timeout 30 docker exec tdengine-server taos -h localhost -s "create database if not exists $db_name;" 2>&1)
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_success "TDengine 数据库 $db_name 创建成功"
        return 0
    elif [ $exit_code -eq 124 ]; then
        print_error "TDengine 数据库 $db_name 创建超时"
        return 1
    else
        # 检查是否是因为数据库已存在（某些情况下可能检测不到）
        if echo "$output" | grep -qiE "(already exists|exist)"; then
            print_info "TDengine 数据库 $db_name 已存在（检测到已存在消息）"
            return 0
        else
            # 检查是否是连接错误
            if echo "$output" | grep -qiE "(Unable to establish connection|Operation timeout|connection refused)"; then
                print_error "TDengine 数据库 $db_name 创建失败: 连接错误"
                print_info "请检查 TDengine 服务状态: docker logs tdengine-server"
                return 1
            else
                print_error "TDengine 数据库 $db_name 创建失败: $output"
                return 1
            fi
        fi
    fi
}

# 执行 TDengine SQL 脚本
execute_tdengine_sql_script() {
    local db_name=$1
    local sql_file=$2
    local error_log=$(mktemp)
    local timeout_seconds=300  # 5分钟超时
    
    if [ ! -f "$sql_file" ]; then
        print_error "SQL 文件不存在: $sql_file"
        return 1
    fi
    
    print_info "执行 TDengine SQL 脚本: $sql_file -> 数据库: $db_name (超时: ${timeout_seconds}秒)"
    
    # 首先验证 TDengine 服务是否真正就绪
    if ! timeout 5 docker exec tdengine-server taos -h localhost -s "select 1;" > /dev/null 2>&1; then
        print_error "TDengine 服务未就绪，无法执行 SQL 脚本"
        rm -f "$error_log"
        return 1
    fi
    
    # TDengine 执行 SQL 脚本的方式：
    # 方法1: 将 SQL 文件复制到容器内执行（推荐）
    # 方法2: 通过标准输入传递 SQL 内容
    
    # 使用标准输入方式执行 SQL 脚本
    # 注意：SQL 文件中已经包含了 CREATE DATABASE IF NOT EXISTS 语句
    # 但为了确保在正确的数据库中执行，我们在开头添加 USE 语句
    
    # 创建临时 SQL 内容，添加 USE 语句（如果 SQL 文件中没有指定数据库）
    local temp_sql_content=$(mktemp)
    {
        echo "USE $db_name;"
        cat "$sql_file"
    } > "$temp_sql_content"
    
    # 通过标准输入执行 SQL 脚本，添加超时机制避免卡住
    # TDengine 的 taos 命令可以通过标准输入读取 SQL
    print_info "开始导入 SQL 脚本（这可能需要一些时间）..."
    local output=$(timeout $timeout_seconds docker exec -i tdengine-server taos -h localhost < "$temp_sql_content" 2>"$error_log")
    local exit_code=$?
    
    # 清理临时文件
    rm -f "$temp_sql_content"
    
    if [ $exit_code -eq 0 ]; then
        print_success "TDengine SQL 脚本执行成功: $sql_file"
        rm -f "$error_log"
        return 0
    elif [ $exit_code -eq 124 ]; then
        # 超时
        local error_content=$(cat "$error_log" 2>/dev/null || echo "")
        rm -f "$error_log"
        print_error "TDengine SQL 脚本执行超时（超过 ${timeout_seconds} 秒）"
        print_info "这通常表示 TDengine 服务未正常启动或响应缓慢"
        print_info "错误信息: ${error_content:0:500}"
        print_info "请检查 TDengine 服务状态: docker logs tdengine-server"
        return 1
    else
        # 检查错误日志，忽略常见的非致命错误
        local error_content=$(cat "$error_log" 2>/dev/null || echo "")
        rm -f "$error_log"
        
        # TDengine 常见的非致命错误信息
        if [ -z "$error_content" ] || echo "$error_content" | grep -qiE "(warning|notice|already exists|does not exist|DB already exists|Table already exists|STable already exists)"; then
            print_success "TDengine SQL 脚本执行完成: $sql_file (可能有警告，但已忽略)"
            return 0
        else
            # 检查是否是连接错误
            if echo "$error_content" | grep -qiE "(Unable to establish connection|Operation timeout|connection refused)"; then
                print_error "TDengine SQL 脚本执行失败: 连接错误"
                print_info "错误信息: ${error_content:0:500}"
                print_info "请检查 TDengine 服务是否正常运行: docker logs tdengine-server"
                return 1
            else
                print_warning "TDengine SQL 脚本执行可能有问题: $sql_file"
                print_info "错误信息: ${error_content:0:500}"
                # 即使有错误也继续，因为某些 SQL 文件可能包含错误处理
                return 0
            fi
        fi
    fi
}

# 初始化 TDengine 数据库和超级表
init_tdengine() {
    print_section "初始化 TDengine 数据库和超级表"
    
    # 等待 TDengine 就绪
    if ! wait_for_tdengine; then
        print_error "TDengine 未就绪，无法初始化数据库"
        return 1
    fi
    
    # 定义需要创建的数据库列表
    local databases=("iot_device")
    local success_count=0
    local total_count=${#databases[@]}
    
    # 创建数据库
    for db_name in "${databases[@]}"; do
        if create_tdengine_database "$db_name"; then
            success_count=$((success_count + 1))
        fi
        echo ""
    done
    
    echo ""
    print_section "TDengine 初始化结果"
    echo "成功: ${GREEN}$success_count${NC} / $total_count"
    
    if [ $success_count -eq $total_count ]; then
        print_success "所有 TDengine 数据库初始化完成！"
        
        # 执行超级表初始化 SQL 脚本
        echo ""
        print_section "初始化 TDengine 超级表"
        
        # 查找 SQL 脚本文件路径
        # SCRIPT_DIR 是 .scripts/docker/，SQL 文件在 .scripts/tdengine/
        local sql_file=""
        
        # 方法1: 从脚本目录的父目录查找（.scripts/tdengine/）
        local script_parent_dir=$(cd "${SCRIPT_DIR}/.." && pwd 2>/dev/null || echo "")
        if [ -n "$script_parent_dir" ]; then
            sql_file="${script_parent_dir}/tdengine/tdengine_super_tables.sql"
        fi
        
        # 方法2: 如果方法1失败，尝试从项目根目录查找
        if [ -z "$sql_file" ] || [ ! -f "$sql_file" ]; then
            local project_root=$(cd "${SCRIPT_DIR}/../.." && pwd 2>/dev/null || echo "")
            if [ -n "$project_root" ]; then
                sql_file="${project_root}/.scripts/tdengine/tdengine_super_tables.sql"
            fi
        fi
        
        # 方法3: 尝试其他可能的路径
        if [ -z "$sql_file" ] || [ ! -f "$sql_file" ]; then
            local possible_paths=(
                "${SCRIPT_DIR}/../tdengine/tdengine_super_tables.sql"
                "${SCRIPT_DIR}/../../.scripts/tdengine/tdengine_super_tables.sql"
                "$(dirname "${SCRIPT_DIR}")/tdengine/tdengine_super_tables.sql"
            )
            
            for path in "${possible_paths[@]}"; do
                if [ -f "$path" ]; then
                    sql_file="$path"
                    break
                fi
            done
        fi
        
        if [ -f "$sql_file" ]; then
            print_info "找到 SQL 脚本文件: $sql_file"
            
            # 为每个数据库执行 SQL 脚本
            for db_name in "${databases[@]}"; do
                if execute_tdengine_sql_script "$db_name" "$sql_file"; then
                    print_success "数据库 $db_name 的超级表初始化完成"
                else
                    print_warning "数据库 $db_name 的超级表初始化可能存在问题"
                fi
            done
        else
            print_warning "未找到 TDengine 超级表 SQL 脚本文件"
            print_info "尝试的路径:"
            for path in "${possible_paths[@]}"; do
                print_info "  - $path"
            done
            print_info "  - $sql_file"
            print_warning "将跳过超级表初始化，超级表将在应用启动时根据产品服务动态创建"
        fi
        
        return 0
    else
        print_warning "部分 TDengine 数据库初始化失败"
        return 1
    fi
}

# 检查数据库是否已初始化（通过检查表数量）
check_database_initialized() {
    local db_name=$1
    
    # 检查数据库是否存在
    if ! docker exec postgres-server psql -U postgres -lqt | cut -d \| -f 1 | grep -qw "$db_name"; then
        return 1  # 数据库不存在
    fi
    
    # 检查数据库中是否有表（表数量 > 0 表示已初始化）
    local table_count=$(docker exec postgres-server psql -U postgres -d "$db_name" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')
    
    if [ -n "$table_count" ] && [ "$table_count" -gt 0 ] 2>/dev/null; then
        return 0  # 数据库已初始化
    else
        return 1  # 数据库未初始化
    fi
}

# 创建数据库（带重试：entrypoint 重启或 WAL 恢复间隙可能短暂不可连）
create_database() {
    local db_name=$1
    local max_attempts=15
    local attempt=0
    
    print_info "创建数据库: $db_name"
    
    while [ $attempt -lt $max_attempts ]; do
        if docker exec postgres-server psql -U postgres -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$db_name"; then
            print_info "数据库 $db_name 已存在，跳过创建"
            return 0
        fi
        
        if docker exec postgres-server psql -U postgres -c "CREATE DATABASE \"$db_name\";" > /dev/null 2>&1; then
            print_success "数据库 $db_name 创建成功"
            return 0
        fi
        
        attempt=$((attempt + 1))
        if [ $attempt -lt $max_attempts ]; then
            print_info "数据库 $db_name 创建失败，等待 PostgreSQL 稳定后重试 ($attempt/$max_attempts)..."
            sleep 3
        fi
    done
    
    print_error "数据库 $db_name 创建失败"
    docker exec postgres-server psql -U postgres -c "CREATE DATABASE \"$db_name\";" 2>&1 | head -3 || true
    return 1
}

# 执行 SQL 初始化脚本
execute_sql_script() {
    local db_name=$1
    local sql_file=$2
    local error_log=$(mktemp)
    
    if [ ! -f "$sql_file" ]; then
        print_error "SQL 文件不存在: $sql_file"
        return 1
    fi
    
    print_info "执行 SQL 脚本: $sql_file -> 数据库: $db_name"
    
    # 执行 SQL 脚本，捕获错误输出
    if docker exec -i postgres-server psql -U postgres -d "$db_name" < "$sql_file" > /dev/null 2>"$error_log"; then
        print_success "SQL 脚本执行成功: $sql_file"
        rm -f "$error_log"
        return 0
    else
        # 检查错误日志，忽略常见的非致命错误
        local error_content=$(cat "$error_log" 2>/dev/null || echo "")
        rm -f "$error_log"
        
        # 如果错误日志为空或只包含警告，认为成功
        if [ -z "$error_content" ] || echo "$error_content" | grep -qiE "(warning|notice|already exists|does not exist)"; then
            print_success "SQL 脚本执行完成: $sql_file (可能有警告，但已忽略)"
            return 0
        else
            print_warning "SQL 脚本执行可能有问题: $sql_file"
            print_info "错误信息: $error_content"
            # 即使有错误也继续，因为某些 SQL 文件可能包含错误处理
            return 0
        fi
    fi
}


# 初始化 MinIO 存储桶和数据（统一走 Docker mc，不依赖宿主机 Python/minio 包）
init_minio() {
    if ! middleware_service_enabled "MinIO"; then
        print_info "MinIO 未启用（当前部署形态: ${EASYAIOT_DEPLOY_PROFILE:-full}），跳过 MinIO 初始化"
        return 0
    fi

    print_section "初始化 MinIO 存储桶和数据"

    local init_result=0
    if bash "${SCRIPT_DIR}/upload_minio_data.sh" --non-interactive --force-mc; then
        print_success "MinIO 初始化完成（Docker mc）！"
        init_result=0
    else
        print_warning "MinIO 初始化可能存在问题（Docker mc）"
        init_result=1
    fi

    return $init_result
}

# 初始化数据库
init_databases() {
    print_section "初始化数据库"
    
    # 等待 PostgreSQL 就绪
    if ! wait_for_postgresql; then
        print_error "PostgreSQL 未就绪，无法初始化数据库"
        return 1
    fi
    
    # 等待 Nacos 就绪（mini 形态跳过 Nacos）
    if middleware_service_enabled Nacos; then
        if ! wait_for_nacos; then
            print_warning "Nacos 未就绪，将跳过 Nacos 密码重置确认步骤"
        fi
    else
        print_info "当前部署形态 (${EASYAIOT_DEPLOY_PROFILE}) 跳过 Nacos，不等待注册中心"
    fi
    
    # 数据库清单按命名规约自动发现：<名字>10.sql -> 库 <名字>20
    # （与 schema-sync/sync_schema_migra.sh 同一规约）。新增模块只需在
    # .scripts/postgresql/（或 .scripts/go-view/）放一个 *10.sql，无需再改本脚本硬编码清单。
    local sql_dir="$(cd "${SCRIPT_DIR}/../postgresql" && pwd)"
    local go_view_sql_dir="$(cd "${SCRIPT_DIR}/../go-view" && pwd)"
    declare -A DB_SQL_MAP
    local _sqlf _base
    for _sqlf in "$sql_dir"/*10.sql "$go_view_sql_dir"/*10.sql; do
        [ -e "$_sqlf" ] || continue
        _base="$(basename "$_sqlf" .sql)"
        case "$_base" in
            *10) DB_SQL_MAP["${_base%10}20"]="$_sqlf" ;;
        esac
    done
    if [ ${#DB_SQL_MAP[@]} -eq 0 ]; then
        print_warning "未在 $sql_dir 或 $go_view_sql_dir 发现任何 *10.sql 文件，跳过数据库初始化"
        return 0
    fi
    print_info "自动发现 ${#DB_SQL_MAP[@]} 个库: ${!DB_SQL_MAP[*]}"

    # mini / standard 不部署可视化模块，跳过 iot-visualize20
    if is_visualize_disabled_deploy_profile && [ -n "${DB_SQL_MAP[iot-visualize20]+x}" ]; then
        unset 'DB_SQL_MAP[iot-visualize20]'
        print_info "当前部署形态 (${EASYAIOT_DEPLOY_PROFILE}) 跳过数据库 iot-visualize20"
    fi
    if ! module_enabled_for_deploy_profile TRANSFORM && [ -n "${DB_SQL_MAP[iot-transform20]+x}" ]; then
        unset 'DB_SQL_MAP[iot-transform20]'
        print_info "当前部署形态 (${EASYAIOT_DEPLOY_PROFILE}) 跳过数据库 iot-transform20"
    fi
    
    local success_count=0
    local total_count=${#DB_SQL_MAP[@]}
    
    # 创建数据库并执行 SQL 脚本
    for db_name in "${!DB_SQL_MAP[@]}"; do
        local sql_file="${DB_SQL_MAP[$db_name]}"
        
        if create_database "$db_name"; then
            # 检查数据库是否已初始化
            if check_database_initialized "$db_name"; then
                print_info "数据库 $db_name 已存在且已初始化，跳过 SQL 脚本执行"
                success_count=$((success_count + 1))
            else
                if execute_sql_script "$db_name" "$sql_file"; then
                    success_count=$((success_count + 1))
                fi
            fi
        fi
        echo ""
    done
    
    # Nacos 账号配置：先自动初始化 admin（新库无内置账号），再用 API 实测登录验证；
    # 全部通过则零人工介入。仅当验证失败（已有 admin 但密码与预期不一致）才回退人工确认。
    echo ""
    if middleware_service_enabled Nacos && wait_for_nacos; then
        ensure_nacos_admin_user || print_warning "Nacos 账号初始化未完成，继续尝试验证..."
        if curl -s -m 5 -X POST "http://localhost:8848/nacos/v1/auth/login" \
            --data-urlencode "username=nacos" --data-urlencode "password=${NACOS_INIT_PASSWORD}" 2>/dev/null \
            | grep -q '"accessToken"'; then
            print_success "Nacos 账号验证通过（用户 nacos，密码与各服务 bootstrap 一致）"
        else
            print_section "Nacos 密码配置确认"
            print_warning "自动验证未通过：Nacos 已有 admin 账号但密码与预期不一致"
            print_info "请登录 http://localhost:8848/nacos 将 nacos 用户密码改为："
            print_warning "${YELLOW}basiclab@iot78475418754${NC}"
            echo ""
            while true; do
                echo -ne "${YELLOW}[提示]${NC} 是否已经完成 Nacos 密码配置（密码必须为: basiclab@iot78475418754）？(y/N): "
                read -r response
                case "$response" in
                    [yY][eE][sS]|[yY])
                        print_success "确认已配置 Nacos 密码，继续执行..."
                        break
                        ;;
                    [nN][oO]|[nN]|"")
                        print_error "请先完成 Nacos 密码配置后再继续"
                        print_info "配置完成后重新运行此脚本"
                        exit 1
                        ;;
                    *)
                        print_warning "请输入 y 或 N"
                        ;;
                esac
            done
        fi
    fi
    
    echo ""
    print_section "数据库初始化结果"
    echo "成功: ${GREEN}$success_count${NC} / $total_count"
    
    if [ $success_count -eq $total_count ]; then
        print_success "所有数据库初始化完成！"
        return 0
    else
        print_warning "部分数据库初始化失败"
        return 1
    fi
}

# 从 docker-compose 配置中提取指定服务的镜像名
# 注意：系统 awk 多为 mawk，不支持 \s，须用 [[:space:]] / [ \t]
_get_service_image_from_compose() {
    local service_name="$1"
    mw_compose config 2>/dev/null | awk -v svc="$service_name" '
        $0 ~ "^  " svc ":" { found=1; next }
        found && /^  [^[:space:]]/ { exit }
        found && /^[ \t]+image:[ \t]*/ {
            sub(/^[ \t]+image:[ \t]*/, "")
            gsub(/["'\'']/, "")
            print
            exit
        }
    '
}

# 核心中间件是否至少有一部分在跑（用于区分「OCI 修复成功」与「compose up 完全失败」）
_middleware_core_containers_running() {
    local n
    for n in postgres-server redis-server nacos-server; do
        if docker ps --filter "name=^${n}$" --filter "status=running" --format '{{.Names}}' 2>/dev/null | grep -qx "$n"; then
            return 0
        fi
        # name 过滤器在部分 Docker 上是子串匹配，再兜底精确名
        if docker inspect --format '{{.State.Status}}' "$n" 2>/dev/null | grep -qx running; then
            return 0
        fi
    done
    return 1
}

# 判断 compose up 输出是否包含 OCI /dev/null 错误（rootless runc 间歇性失败）
_is_dev_null_oci_error() {
    grep -q "error reopening /dev/null inside container" "$1" 2>/dev/null
}

# 将服务名格式化为中文顿号分隔的可读列表
_format_service_list() {
    local -a services=("$@")
    local result="" svc
    for svc in "${services[@]}"; do
        [ -n "$result" ] && result+="、"
        result+="$svc"
    done
    echo "$result"
}

# 启动中间件容器；可选服务镜像缺失时自动跳过，避免阻塞核心中间件
# 遇到 rootless Docker 的 /dev/null OCI 错误时自动重试（最多 3 次，退避 3/6/12s）
compose_up_middleware() {
    local -a skip_services=("$@")
    local -a up_services=()
    local svc should_skip

    while IFS= read -r svc; do
        [ -z "$svc" ] && continue
        should_skip=0
        for skip in "${skip_services[@]}"; do
            if [ "$svc" = "$skip" ]; then
                should_skip=1
                break
            fi
        done
        if [ "$should_skip" -eq 0 ]; then
            up_services+=("$svc")
        fi
    done < <(mw_compose config --services 2>/dev/null)

    if [ ${#up_services[@]} -eq 0 ]; then
        print_error "没有可启动的中间件服务"
        return 1
    fi

    if [ ${#skip_services[@]} -gt 0 ]; then
        print_warning "以下中间件因镜像缺失等原因暂不启动：$(_format_service_list "${skip_services[@]}")"
        # compose up 指定服务列表不会停掉未列出但仍在 compose 中定义的旧容器；
        # 从 full/standard 切到 mini 时需主动停掉 Nacos/Kafka/MinIO 等残留。
        local -a lingering_skips=()
        local skip_svc
        for skip_svc in "${skip_services[@]}"; do
            [ -z "$skip_svc" ] && continue
            if mw_compose ps -q "$skip_svc" 2>/dev/null | grep -q .; then
                lingering_skips+=("$skip_svc")
            fi
        done
        if [ ${#lingering_skips[@]} -gt 0 ]; then
            print_info "停止并移除当前形态不部署的中间件: $(_format_service_list "${lingering_skips[@]}")"
            mw_compose stop "${lingering_skips[@]}" >/dev/null 2>&1 || true
            mw_compose rm -f "${lingering_skips[@]}" >/dev/null 2>&1 || true
        fi
    fi

    # ★ 自动检测并设置 NACOS_PLATFORM，避免 ARM/AMD64 跨架构问题
    if [ -z "${NACOS_PLATFORM:-}" ]; then
        local _host_arch
        _host_arch=$(uname -m)
        case "$_host_arch" in
            x86_64)  export NACOS_PLATFORM="linux/amd64" ;;
            aarch64) export NACOS_PLATFORM="linux/arm64" ;;
        esac
    fi

    local _svc_count=${#up_services[@]} _svc_list
    _svc_list=$(_format_service_list "${up_services[@]}")
    print_info "正在启动 ${_svc_count} 个中间件容器：${_svc_list}"
    local _up_log _up_rc _retry _delay
    _up_log=$(mktemp)
    mw_compose up -d "${up_services[@]}" > "$_up_log" 2>&1
    _up_rc=$?
    cat "$_up_log" >> "$LOG_FILE"

    # rootless runc /dev/null 间歇性错误 → 退避重试（等待 Docker daemon 状态恢复）
    for _retry in 1 2 3; do
        [ "$_up_rc" -eq 0 ] && break
        _is_dev_null_oci_error "$_up_log" || break
        case $_retry in
            1) _delay=3 ;;
            2) _delay=6 ;;
            3) _delay=12 ;;
        esac
        print_warning "检测到间歇性 OCI /dev/null 错误，${_delay}s 后重试（第 ${_retry}/3 次）..."
        sleep "$_delay"
        : > "$_up_log"
        mw_compose up -d "${up_services[@]}" > "$_up_log" 2>&1
        _up_rc=$?
        cat "$_up_log" >> "$LOG_FILE"
    done

    # 可选服务镜像拉取失败（如 FUXA 403）会导致整批 compose up 失败；
    # 从待启动列表剔除仍缺镜像的可选服务后重试，避免拖垮 Postgres/Redis/Nacos。
    if [ "$_up_rc" -ne 0 ]; then
        local -a _retry_services=()
        local -a _drop_optional=()
        local _opt _img _is_opt _keep
        for svc in "${up_services[@]}"; do
            _is_opt=0
            for _opt in "${OPTIONAL_MIDDLEWARE_SERVICES[@]}"; do
                if [ "$svc" = "$_opt" ]; then
                    _is_opt=1
                    break
                fi
            done
            _keep=1
            if [ "$_is_opt" -eq 1 ]; then
                _img="$(_get_service_image_from_compose "$svc")"
                if [ -n "$_img" ] && ! docker image inspect "$_img" &>/dev/null; then
                    _keep=0
                    _drop_optional+=("$svc")
                elif grep -qE "failed to resolve reference|403 Forbidden|manifest unknown|not found" "$_up_log" 2>/dev/null \
                    && [ -n "$_img" ] && grep -qF "$_img" "$_up_log" 2>/dev/null; then
                    _keep=0
                    _drop_optional+=("$svc")
                fi
            fi
            [ "$_keep" -eq 1 ] && _retry_services+=("$svc")
        done
        if [ ${#_drop_optional[@]} -gt 0 ] && [ ${#_retry_services[@]} -gt 0 ] \
            && [ ${#_retry_services[@]} -lt ${#up_services[@]} ]; then
            print_warning "因镜像不可用跳过可选中间件后重试：$(_format_service_list "${_drop_optional[@]}")"
            : > "$_up_log"
            mw_compose up -d "${_retry_services[@]}" > "$_up_log" 2>&1
            _up_rc=$?
            cat "$_up_log" >> "$LOG_FILE"
            up_services=("${_retry_services[@]}")
        fi
    fi
    rm -f "$_up_log"

    # compose up 返回成功（exit 0）但部分容器可能处于 Created 状态（OCI 启动失败）。
    # 这些容器存在于 Docker 但未运行，后续依赖它们的服务将无法解析 DNS 主机名。
    # 如 Redis 处于 Created → iot-system 解析 "Redis" 失败 → UnknownHostException → unhealthy。
    _repair_created_middleware_containers
    local _repair_rc=$?

    # 仅当 compose up 失败、Created 已修干净、且核心容器确实在跑时，才覆盖错误码。
    # 切勿把「没有任何容器被创建」(repair 直接 return 0) 误判为启动成功。
    if [ "$_up_rc" -ne 0 ]; then
        if [ "$_repair_rc" -eq 0 ] && _middleware_core_containers_running; then
            print_success "Created 容器已修复，中间件启动成功"
            _up_rc=0
        else
            print_error "中间件 compose up 失败（exit=${_up_rc}），核心容器未就绪"
            print_info "请查看日志中的 Image Pulling / Error 行（常见：FUXA 镜像源 403）"
        fi
    fi

    return "$_up_rc"
}

# 检测并修复 Created 状态的中间件容器（compose up 成功但 OCI 启动失败）。
# 关键容器（Redis/Nacos/PostgresSQL/Kafka 等）若 Created 会导致业务服务 DNS 解析失败。
# 返回 0=无 Created 容器或已全部修复；1=仍有 Created 容器未修复。
_repair_created_middleware_containers() {
    local _created _n _status _svc _rc=0 _up_log _up_rc _retry _delay
    local -a _mw_names=(
        nacos-server postgres-server postgres-init redis-server kafka-server
        minio-server milvus-server srs-server nodered-server fuxa-server
        emqx-server zlmediakit-server tdengine-server tdengine-init
    )
    _created=$(docker ps -a --filter "status=created" --format '{{.Names}}' 2>/dev/null || true)
    [ -z "$_created" ] && return 0

    for _n in $_created; do
        # 只处理中间件容器，忽略业务服务（iot-* 等）的 Created 残留
        local _is_mw=0 _mw
        for _mw in "${_mw_names[@]}"; do
            if [ "$_n" = "$_mw" ]; then
                _is_mw=1
                break
            fi
        done
        [ "$_is_mw" -eq 1 ] || continue

        _status=$(docker inspect --format '{{.State.Status}}' "$_n" 2>/dev/null || echo "")
        [ "$_status" = "created" ] || continue
        print_warning "中间件容器 $_n 处于 Created 状态（OCI 启动失败，如 /dev/null 错误），尝试修复..."

        # 策略1：直接 docker start（简单重试，/dev/null 问题可能已自愈）
        if docker start "$_n" >/dev/null 2>&1; then
            print_success "容器 $_n 已重新启动"
            continue
        fi

        # 策略2：docker rm + 单服务 compose up（重建 OCI 上下文）
        # 对 compose up 也加入 OCI /dev/null 错误重试，因为重建时也可能遇到同样问题
        print_warning "docker start $_n 失败，删除后通过 compose 重建..."
        _svc=$(docker inspect --format '{{index .Config.Labels "com.docker.compose.service"}}' "$_n" 2>/dev/null || echo "")
        docker rm -f "$_n" >/dev/null 2>&1 || true
        sleep 1
        if [ -n "$_svc" ]; then
            _up_log=$(mktemp)
            mw_compose up -d "$_svc" > "$_up_log" 2>&1
            _up_rc=$?
            cat "$_up_log" >> "$LOG_FILE"

            # 对 OCI /dev/null 错误退避重试（与 compose_up_middleware 一致）
            for _retry in 1 2 3; do
                [ "$_up_rc" -eq 0 ] && break
                _is_dev_null_oci_error "$_up_log" || break
                case $_retry in
                    1) _delay=3 ;;
                    2) _delay=6 ;;
                    3) _delay=12 ;;
                esac
                print_warning "修复 $_n ($_svc) 时检测到 OCI /dev/null 错误，${_delay}s 后重试..."
                sleep "$_delay"
                : > "$_up_log"
                mw_compose up -d "$_svc" > "$_up_log" 2>&1
                _up_rc=$?
                cat "$_up_log" >> "$LOG_FILE"
            done
            rm -f "$_up_log"

            if [ $_up_rc -eq 0 ]; then
                # 等待容器进入 running 状态（OCI 启动需要一点时间）
                local _wait=0
                while [ $_wait -lt 10 ]; do
                    if docker ps --filter "name=$_n" --filter "status=running" --format '{{.Names}}' 2>/dev/null | grep -q "$_n"; then
                        print_success "容器 $_n ($_svc) 已通过 compose 重建并运行"
                        continue 2  # 跳出内层 if 和外层 for 的本次循环
                    fi
                    sleep 1
                    _wait=$((_wait + 1))
                done
                # 超时：容器可能又进入了 Created 状态
                local _new_status
                _new_status=$(docker inspect --format '{{.State.Status}}' "$_n" 2>/dev/null || echo "")
                if [ "$_new_status" = "created" ]; then
                    print_warning "容器 $_n ($_svc) 重建后仍处于 Created 状态，OCI 启动持续失败"
                else
                    print_warning "容器 $_n ($_svc) 重建后状态: $_new_status（非 running）"
                fi
            else
                print_warning "mw_compose up -d $_svc 返回错误码 $_up_rc"
            fi
        fi

        print_error "容器 $_n 修复失败，后续业务服务可能无法解析其主机名"
        _rc=1
    done
    return $_rc
}

# 收集默认不启动 / 镜像不可用的服务列表（供 compose_up_middleware 跳过）
collect_skippable_optional_services() {
    local -a skip_services=()
    local svc img
    for svc in "${DISABLED_BY_DEFAULT_MIDDLEWARE_SERVICES[@]}"; do
        case "$svc" in
            TDengine|TDengine-init)
                [ "${EASYAIOT_ENABLE_TDENGINE:-0}" = "1" ] && continue
                ;;
            EMQX)
                [ "${EASYAIOT_ENABLE_EMQX:-0}" = "1" ] && continue
                ;;
        esac
        skip_services+=("$svc")
    done
    for svc in "${OPTIONAL_MIDDLEWARE_SERVICES[@]}"; do
        img="$(_get_service_image_from_compose "$svc")"
        if [ -n "$img" ] && ! docker image inspect "$img" &>/dev/null; then
            print_warning "可选服务 $svc 镜像不可用 ($img)，将跳过启动"
            skip_services+=("$svc")
        fi
    done
    local profile_skip
    for profile_skip in $(middleware_skipped_services); do
        skip_services+=("$profile_skip")
    done
    echo "${skip_services[@]}"
}

# 检查并拉取缺失的镜像（按当前部署形态跳过不启动的服务，如 mini/standard 不拉 FUXA）
check_and_pull_images() {
    print_info "检查所需镜像是否存在..."
    
    # 获取 docker-compose.yml 中定义的所有服务
    local services=$(mw_compose config --services 2>/dev/null || echo "")
    
    if [ -z "$services" ]; then
        print_warning "无法获取服务列表，将直接启动服务（会自动拉取缺失镜像）"
        return 0
    fi
    
    local missing_images=0
    local existing_images=0
    local images_to_check=()
    local skipped_images=0

    # 当前形态不部署 / 默认关闭的服务：不检查、不拉取其镜像
    local -a skip_services=()
    local skip_svc img svc
    for skip_svc in $(middleware_skipped_services); do
        [ -n "$skip_svc" ] && skip_services+=("$skip_svc")
    done
    for skip_svc in "${DISABLED_BY_DEFAULT_MIDDLEWARE_SERVICES[@]}"; do
        case "$skip_svc" in
            TDengine|TDengine-init)
                [ "${EASYAIOT_ENABLE_TDENGINE:-0}" = "1" ] && continue
                ;;
            EMQX)
                [ "${EASYAIOT_ENABLE_EMQX:-0}" = "1" ] && continue
                ;;
        esac
        skip_services+=("$skip_svc")
    done

    _middleware_service_is_skipped() {
        local name="$1" s
        for s in "${skip_services[@]}"; do
            [ "$s" = "$name" ] && return 0
        done
        return 1
    }

    # 按服务收集镜像，跳过形态外服务（避免仍拉取 FUXA 等）
    for svc in $services; do
        [ -z "$svc" ] && continue
        if _middleware_service_is_skipped "$svc"; then
            skipped_images=$((skipped_images + 1))
            continue
        fi
        img="$(_get_service_image_from_compose "$svc")"
        [ -z "$img" ] && continue
        if [[ ! " ${images_to_check[*]} " =~ " ${img} " ]]; then
            images_to_check+=("$img")
        fi
    done

    if [ "$skipped_images" -gt 0 ]; then
        print_info "当前部署形态 (${EASYAIOT_DEPLOY_PROFILE:-full}) 跳过 ${skipped_images} 个中间件服务的镜像拉取"
    fi

    if [ ${#images_to_check[@]} -eq 0 ]; then
        print_warning "当前形态无可拉取的中间件镜像"
        return 0
    fi
    
    # 检查每个镜像是否存在（记录缺失清单，后面只拉缺失的）
    local missing_list=()
    for image in "${images_to_check[@]}"; do
        if docker image inspect "$image" &> /dev/null; then
            existing_images=$((existing_images + 1))
        else
            print_warning "镜像不存在: $image"
            missing_list+=("$image")
        fi
    done
    missing_images=${#missing_list[@]}

    # ★ 检测本地架构，用于多架构镜像（如 nacos）的显式 platform 拉取
    local _host_arch
    _host_arch=$(uname -m)
    case "$_host_arch" in
        x86_64)  _host_arch="linux/amd64" ;;
        aarch64) _host_arch="linux/arm64" ;;
        armv7l)  _host_arch="linux/arm/v7" ;;
        *)       _host_arch="" ;;  # 未知架构，不传 --platform，由 Docker 自动选择
    esac

    # 只拉缺失的镜像：原先缺 1 个就全量 compose pull，会为已存在的十几个镜像逐一联源比对，
    # 慢且被镜像源网络质量绑架（源端一个 blob 超时即整体失败）
    # 拉取失败时经 docker_pull_with_mirror_fallback 多源回退（含已带镜像站前缀的 FUXA）
    if [ $missing_images -gt 0 ]; then
        print_info "已存在 $existing_images 个镜像；缺失 $missing_images 个，仅拉取缺失镜像: ${missing_list[*]}"
        local _pull_img _pull_fail=0
        for _pull_img in "${missing_list[@]}"; do
            # ★ nacos 镜像显式指定 platform，避免在 ARM 主机上拉取 amd64 版本导致 QEMU 模拟性能极差
            local _pull_args=()
            if [ -n "$_host_arch" ] && echo "$_pull_img" | grep -q "nacos/nacos-server"; then
                print_info "检测到 nacos 镜像，使用平台架构: ${_host_arch}"
                _pull_args=(--platform "$_host_arch")
            fi
            export DOCKER_CONTENT_TRUST=0
            local _pull_ok=0
            if declare -f docker_pull_with_mirror_fallback >/dev/null 2>&1; then
                docker_pull_with_mirror_fallback "${_pull_args[@]}" "$_pull_img" 2>&1 | tee -a "$LOG_FILE" || true
            else
                docker pull "${_pull_args[@]}" "$_pull_img" 2>&1 | tee -a "$LOG_FILE" || true
            fi
            docker image inspect "$_pull_img" &>/dev/null && _pull_ok=1
            # FUXA：专用多源脚本再试一次
            if [ "$_pull_ok" -ne 1 ] && echo "$_pull_img" | grep -qi 'frangoteam/fuxa'; then
                if [ -f "${SCRIPT_DIR}/pull_fuxa.sh" ]; then
                    print_info "尝试 pull_fuxa.sh 多源拉取 FUXA..."
                    FUXA_IMAGE_LOCAL="$_pull_img" bash "${SCRIPT_DIR}/pull_fuxa.sh" 2>&1 | tee -a "$LOG_FILE" || true
                    docker image inspect "$_pull_img" &>/dev/null && _pull_ok=1
                fi
            fi
            if [ "$_pull_ok" -ne 1 ]; then
                print_warning "镜像拉取失败: $_pull_img"
                _pull_fail=1
            fi
        done
        if [ "$_pull_fail" -eq 0 ]; then
            print_success "缺失镜像拉取完成"
        else
            print_warning "部分镜像拉取失败；可选服务（如 FUXA）将跳过，核心中间件仍会启动"
            print_info "FUXA 可稍后手动: bash ${SCRIPT_DIR}/pull_fuxa.sh && docker compose -f ${COMPOSE_FILE} up -d FUXA"
            print_info "并确认 /etc/docker/daemon.json 含 dns: [\"223.5.5.5\",\"119.29.29.29\"] 后 systemctl restart docker"
        fi
    else
        if [ ${#images_to_check[@]} -gt 0 ]; then
            print_success "所有所需镜像已存在（${#images_to_check[@]} 个），跳过拉取步骤（节省时间）"
        else
            print_info "未检测到需要拉取的镜像，将直接启动服务"
        fi
    fi
}

# 从 docker-compose.yml 提取所有端口映射
extract_ports_from_compose() {
    local service_name=$1
    local ports=()
    
    # 使用 docker-compose config 获取端口映射
    local port_mappings=$($COMPOSE_CMD -f "$COMPOSE_FILE" config 2>/dev/null | grep -A 20 "^  ${service_name}:" | grep -E "^\s+- \"[0-9]+:" | sed 's/.*"\([0-9]*\):.*/\1/' || echo "")
    
    if [ -n "$port_mappings" ]; then
        while IFS= read -r port; do
            if [ -n "$port" ]; then
                ports+=("$port")
            fi
        done <<< "$port_mappings"
    fi
    
    # 如果没有找到，使用默认端口
    if [ ${#ports[@]} -eq 0 ]; then
        case "$service_name" in
            "TDengine")
                ports=("6030" "6041" "6060" "6043" "6044" "6045" "6046" "6047" "6048" "6049")
                ;;
            "Redis")
                ports=("6379")
                ;;
            "PostgresSQL")
                ports=("5432")
                ;;
            "Nacos")
                ports=("8848" "9848" "9849")
                ;;
            "Kafka")
                ports=("9092" "9093")
                ;;
            "MinIO")
                ports=("9000" "9001")
                ;;
            "SRS")
                ports=("1935" "1985" "8080" "8000")
                ;;
            "NodeRED")
                ports=("1880")
                ;;
            "FUXA")
                ports=("1881")
                ;;
            "EMQX")
                ports=("1883" "8883" "8083" "8084" "18083")
                ;;
            "ZLMediaKit")
                ports=("6080" "4443" "10935" "5540" "10000" "8000" "9000")
                ;;
            "Milvus")
                ports=("19530" "9091")
                ;;
        esac
    fi
    
    echo "${ports[@]}"
}

# 检查端口占用并清理
check_and_clean_ports() {
    print_info "检查端口占用情况..."
    local has_conflict=0
    local conflict_ports=()
    local conflict_containers=()
    
    # 先执行 docker-compose down 清理所有残留容器和端口绑定
    print_info "清理 docker-compose 管理的容器和端口绑定..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" down 2>/dev/null || true
    sleep 2
    
    # 强制清理所有可能占用端口的容器（包括停止状态的）
    print_info "清理所有可能占用端口的残留容器..."
    for service in "${MIDDLEWARE_SERVICES[@]}"; do
        local container_name=""
        case "$service" in
            "Nacos") container_name="nacos-server" ;;
            "PostgresSQL") container_name="postgres-server" ;;
            "TDengine") container_name="tdengine-server" ;;
            "Redis") container_name="redis-server" ;;
            "Kafka") container_name="kafka-server" ;;
            "MinIO") container_name="minio-server" ;;
            "SRS") container_name="srs-server" ;;
            "NodeRED") container_name="nodered-server" ;;
            "FUXA") container_name="fuxa-server" ;;
            "EMQX") container_name="emqx-server" ;;
            "ZLMediaKit") container_name="zlmediakit-server" ;;
            "Milvus") container_name="milvus-server" ;;
        esac
        
        if [ -n "$container_name" ]; then
            # 查找所有状态（运行中、已停止）的容器
            local existing_containers=$(docker ps -a --filter "name=^${container_name}$" --format "{{.ID}}" 2>/dev/null || echo "")
            if [ -n "$existing_containers" ]; then
                echo "$existing_containers" | while read -r container_id; do
                    if [ -n "$container_id" ]; then
                        print_info "强制清理残留容器: $container_name ($container_id)"
                        docker stop -t 0 "$container_id" 2>/dev/null || true
                        docker rm -f "$container_id" 2>/dev/null || true
                    fi
                done
            fi
        fi
    done
    
    # 特别处理 ZLMediaKit 的 UDP 端口范围（30000-30500）
    print_info "检查并清理 ZLMediaKit UDP 端口范围（30000-30500）占用..."
    local zlm_udp_ports_conflict=0
    # 检查 UDP 端口范围中是否有被占用的端口（采样检查，避免检查所有端口）
    for test_port in 30000 30100 30200 30300 30400 30454 30500; do
        if command -v ss &> /dev/null; then
            if ss -ulnp 2>/dev/null | grep -qE ":$test_port[[:space:]]|:$test_port$"; then
                local port_info=$(ss -ulnp 2>/dev/null | grep -E ":$test_port[[:space:]]|:$test_port$" | head -1)
                print_warning "检测到 UDP 端口 $test_port 被占用: $port_info"
                zlm_udp_ports_conflict=1
            fi
        elif command -v netstat &> /dev/null; then
            if netstat -ulnp 2>/dev/null | grep -qE ":$test_port[[:space:]]|:$test_port$"; then
                local port_info=$(netstat -ulnp 2>/dev/null | grep -E ":$test_port[[:space:]]|:$test_port$" | head -1)
                print_warning "检测到 UDP 端口 $test_port 被占用: $port_info"
                zlm_udp_ports_conflict=1
            fi
        fi
    done
    
    # 如果检测到 UDP 端口冲突，尝试清理
    if [ $zlm_udp_ports_conflict -eq 1 ]; then
        print_info "尝试清理占用 ZLMediaKit UDP 端口的进程..."
        
        # 方法1: 查找并停止所有 zlmediakit 相关进程
        local zlm_pids=$(pgrep -f "zlmediakit\|MediaServer" 2>/dev/null || echo "")
        if [ -n "$zlm_pids" ]; then
            echo "$zlm_pids" | while read -r pid; do
                if [ -n "$pid" ]; then
                    local proc_name=$(ps -p "$pid" -o comm= 2>/dev/null || echo "")
                    print_info "发现 ZLMediaKit 进程: $proc_name (PID: $pid)，尝试停止..."
                    kill -TERM "$pid" 2>/dev/null || true
                    sleep 1
                    if kill -0 "$pid" 2>/dev/null; then
                        print_info "强制停止进程 PID: $pid"
                        kill -KILL "$pid" 2>/dev/null || true
                    fi
                fi
            done
            sleep 2
        fi
        
        # 方法2: 再次检查 ZLMediaKit 容器
        local zlm_containers=$(docker ps -a --filter "name=zlmediakit" --format "{{.ID}}" 2>/dev/null || echo "")
        if [ -n "$zlm_containers" ]; then
            echo "$zlm_containers" | while read -r container_id; do
                if [ -n "$container_id" ]; then
                    print_info "强制停止并删除 ZLMediaKit 容器: $container_id"
                    docker stop -t 0 "$container_id" 2>/dev/null || true
                    docker rm -f "$container_id" 2>/dev/null || true
                fi
            done
            sleep 2
        fi
        
        # 方法3: 查找占用 UDP 端口的进程并提示用户
        if command -v lsof &> /dev/null; then
            for test_port in 30000 30100 30200 30300 30400 30454 30500; do
                local udp_process=$(lsof -i UDP:$test_port 2>/dev/null | grep -v COMMAND | head -1 || echo "")
                if [ -n "$udp_process" ]; then
                    local pid=$(echo "$udp_process" | awk '{print $2}')
                    if [ -n "$pid" ] && [ "$pid" != "PID" ]; then
                        print_warning "UDP 端口 $test_port 仍被进程占用 (PID: $pid)"
                        print_info "进程信息: $udp_process"
                        print_info "如需手动停止，请执行: sudo kill -9 $pid"
                    fi
                fi
            done
        fi
    fi
    
    # 等待端口释放（Docker 需要时间释放端口绑定）
    print_info "等待端口释放（最多等待 10 秒）..."
    local wait_count=0
    local max_wait=10
    while [ $wait_count -lt $max_wait ]; do
        local ports_still_in_use=0
        for service in "${MIDDLEWARE_SERVICES[@]}"; do
            local port="${MIDDLEWARE_PORTS[$service]}"
            if [ -z "$port" ]; then
                continue
            fi
            
            # 检查是否还有 Docker 容器占用端口（TCP）
            local docker_using_port=$(docker ps --format "{{.Ports}}" 2>/dev/null | grep -E ":$port->|0\.0\.0\.0:$port|:::$port" || echo "")
            if [ -n "$docker_using_port" ]; then
                ports_still_in_use=1
                break
            fi
        done
        
        # 检查 ZLMediaKit UDP 端口范围是否仍被占用
        if [ $ports_still_in_use -eq 0 ]; then
            for test_port in 30000 30100 30200 30300 30400 30454 30500; do
                if command -v ss &> /dev/null; then
                    if ss -ulnp 2>/dev/null | grep -qE ":$test_port[[:space:]]|:$test_port$"; then
                        ports_still_in_use=1
                        break
                    fi
                elif command -v netstat &> /dev/null; then
                    if netstat -ulnp 2>/dev/null | grep -qE ":$test_port[[:space:]]|:$test_port$"; then
                        ports_still_in_use=1
                        break
                    fi
                fi
            done
        fi
        
        if [ $ports_still_in_use -eq 0 ]; then
            break
        fi
        
        wait_count=$((wait_count + 1))
        sleep 1
        echo -n "."
    done
    echo ""
    
    if [ $wait_count -ge $max_wait ]; then
        print_warning "等待端口释放超时，继续检查..."
    else
        print_success "端口已释放"
    fi
    
    sleep 1
    
    # 检查所有中间件端口（包括所有映射的端口）
    for service in "${MIDDLEWARE_SERVICES[@]}"; do
        # 特别处理 ZLMediaKit 的 UDP 端口范围
        if [ "$service" = "ZLMediaKit" ]; then
            print_info "检查 ZLMediaKit UDP 端口范围（30000-30500）..."
            local zlm_udp_conflict=0
            for test_port in 30000 30100 30200 30300 30400 30454 30500; do
                local udp_port_in_use=0
                if command -v ss &> /dev/null; then
                    if ss -ulnp 2>/dev/null | grep -qE ":$test_port[[:space:]]|:$test_port$"; then
                        udp_port_in_use=1
                        local udp_info=$(ss -ulnp 2>/dev/null | grep -E ":$test_port[[:space:]]|:$test_port$" | head -1)
                        print_warning "UDP 端口 $test_port 被占用: $udp_info"
                    fi
                elif command -v netstat &> /dev/null; then
                    if netstat -ulnp 2>/dev/null | grep -qE ":$test_port[[:space:]]|:$test_port$"; then
                        udp_port_in_use=1
                        local udp_info=$(netstat -ulnp 2>/dev/null | grep -E ":$test_port[[:space:]]|:$test_port$" | head -1)
                        print_warning "UDP 端口 $test_port 被占用: $udp_info"
                    fi
                fi
                
                if [ $udp_port_in_use -eq 1 ]; then
                    zlm_udp_conflict=1
                    conflict_ports+=("$test_port/udp")
                fi
            done
            
            if [ $zlm_udp_conflict -eq 1 ]; then
                has_conflict=1
                print_warning "ZLMediaKit UDP 端口范围存在冲突"
            fi
        fi
        
        # 获取该服务的所有端口映射
        local service_ports=($(extract_ports_from_compose "$service"))
        
        if [ ${#service_ports[@]} -eq 0 ]; then
            # 如果没有找到，使用默认主端口
            local port="${MIDDLEWARE_PORTS[$service]}"
            if [ -z "$port" ]; then
                continue
            fi
            service_ports=("$port")
        fi
        
        # 检查该服务的所有端口
        for port in "${service_ports[@]}"; do
            if [ -z "$port" ]; then
                continue
            fi
            
            # 检查端口是否被占用（使用多种方法）
            local port_in_use=0
            local port_user=""
            
            # 方法1: 使用 ss 命令（最可靠）
            if command -v ss &> /dev/null; then
                if ss -tlnp 2>/dev/null | grep -qE ":$port[[:space:]]|:$port$"; then
                    port_in_use=1
                    port_user=$(ss -tlnp 2>/dev/null | grep -E ":$port[[:space:]]|:$port$" | head -1)
                fi
            # 方法2: 使用 netstat 命令
            elif command -v netstat &> /dev/null; then
                if netstat -tlnp 2>/dev/null | grep -qE ":$port[[:space:]]|:$port$"; then
                    port_in_use=1
                    port_user=$(netstat -tlnp 2>/dev/null | grep -E ":$port[[:space:]]|:$port$" | head -1)
                fi
            # 方法3: 使用 lsof 命令
            elif command -v lsof &> /dev/null; then
                if lsof -i :$port 2>/dev/null | grep -q LISTEN; then
                    port_in_use=1
                    port_user=$(lsof -i :$port 2>/dev/null | grep LISTEN | head -1)
                fi
            # 方法4: 使用 /proc/net/tcp (Linux)
            elif [ -f /proc/net/tcp ]; then
                local hex_port=$(printf "%04X" $port | tr '[:lower:]' '[:upper:]')
                if grep -qE ":$hex_port[[:space:]]|:$hex_port$" /proc/net/tcp 2>/dev/null; then
                    port_in_use=1
                fi
            fi
            
            # 方法5: 通过 Docker 直接检查端口映射
            local docker_port_check=$(docker ps --format "{{.ID}}\t{{.Ports}}" 2>/dev/null | grep -E ":$port->|0\.0\.0\.0:$port|:::$port" || echo "")
            if [ -n "$docker_port_check" ]; then
                port_in_use=1
                if [ -z "$port_user" ]; then
                    port_user="Docker容器: $docker_port_check"
                fi
            fi
            
            if [ $port_in_use -eq 1 ]; then
                # 检查是否是 Docker 容器占用的
                local container_id=""
                local container_name=""
                local is_docker_process=0
                
                # 通过 docker ps 查找占用端口的容器（多种格式匹配）
                while IFS= read -r line; do
                    if echo "$line" | grep -qE ":$port->|0\.0\.0\.0:$port|:::$port"; then
                        container_id=$(echo "$line" | awk '{print $1}')
                        container_name=$(echo "$line" | awk '{print $NF}')
                        is_docker_process=1
                        break
                    fi
                done < <(docker ps --format "{{.ID}}\t{{.Ports}}\t{{.Names}}" 2>/dev/null || true)
                
                # 如果没找到，尝试通过容器名称查找
                if [ -z "$container_id" ]; then
                    case "$service" in
                        "TDengine") 
                            container_id=$(docker ps --filter "name=tdengine" --format "{{.ID}}" 2>/dev/null | head -1)
                            container_name=$(docker ps --filter "name=tdengine" --format "{{.Names}}" 2>/dev/null | head -1)
                            if [ -n "$container_id" ]; then
                                is_docker_process=1
                            fi
                            ;;
                        "Redis")
                            container_id=$(docker ps --filter "name=redis" --format "{{.ID}}" 2>/dev/null | head -1)
                            container_name=$(docker ps --filter "name=redis" --format "{{.Names}}" 2>/dev/null | head -1)
                            if [ -n "$container_id" ]; then
                                is_docker_process=1
                            fi
                            ;;
                    esac
                fi
                
                if [ $is_docker_process -eq 1 ] && [ -n "$container_id" ]; then
                    # 检查是否是当前 compose 项目的容器
                    local compose_project=$(docker inspect "$container_id" --format '{{index .Config.Labels "com.docker.compose.project"}}' 2>/dev/null || echo "")
                    local compose_service=$(docker inspect "$container_id" --format '{{index .Config.Labels "com.docker.compose.service"}}' 2>/dev/null || echo "")
                    
                    # 如果不是当前项目的容器，或者容器名称不匹配，则认为是冲突
                    if [ -z "$compose_project" ] || [ "$compose_service" != "$service" ]; then
                        print_warning "端口 $port ($service) 被 Docker 容器 $container_name ($container_id) 占用"
                        conflict_ports+=("$port")
                        conflict_containers+=("$container_id")
                        has_conflict=1
                    fi
                else
                    # 非 Docker 进程占用（宿主机上的进程）
                    print_warning "端口 $port ($service) 被宿主机进程占用（非 Docker 容器）"
                    print_info "占用信息: $port_user"
                    
                    # 尝试识别进程信息
                    local process_info=""
                    if command -v lsof &> /dev/null; then
                        process_info=$(lsof -i :$port 2>/dev/null | grep LISTEN | head -1 || echo "")
                    elif command -v ss &> /dev/null; then
                        process_info=$(ss -tlnp 2>/dev/null | grep ":$port " | head -1 || echo "")
                    fi
                    
                    if [ -n "$process_info" ]; then
                        print_info "进程详情: $process_info"
                    fi
                    
                    conflict_ports+=("$port")
                    has_conflict=1
                fi
            fi
        done
    done
    
    # 再次验证所有端口（清理后）
    if [ $has_conflict -eq 0 ]; then
        print_info "二次验证端口状态..."
        sleep 1
        for service in "${MIDDLEWARE_SERVICES[@]}"; do
            local port="${MIDDLEWARE_PORTS[$service]}"
            if [ -z "$port" ]; then
                continue
            fi
            
            if command -v ss &> /dev/null && ss -tlnp 2>/dev/null | grep -qE ":$port[[:space:]]|:$port$"; then
                print_warning "端口 $port ($service) 在清理后仍被占用"
                conflict_ports+=("$port")
                has_conflict=1
            fi
        done
    fi
    
    if [ $has_conflict -eq 1 ]; then
        echo ""
        print_warning "发现端口冲突！"
        print_warning "冲突端口: ${conflict_ports[*]}"
        echo ""
        
        # 检查是否有宿主机进程占用
        local has_host_process=0
        for port_entry in "${conflict_ports[@]}"; do
            # 处理端口格式（可能是 "port" 或 "port/udp"）
            local port="${port_entry%%/*}"
            local port_type="${port_entry##*/}"
            
            local docker_using=$(docker ps --format "{{.Ports}}" 2>/dev/null | grep -E ":$port->|0\.0\.0\.0:$port|:::$port" || echo "")
            if [ -z "$docker_using" ]; then
                # 检查是否是宿主机进程（TCP 或 UDP）
                if [ "$port_type" = "udp" ]; then
                    if command -v ss &> /dev/null && ss -ulnp 2>/dev/null | grep -qE ":$port[[:space:]]|:$port$"; then
                        has_host_process=1
                        break
                    fi
                else
                    if command -v ss &> /dev/null && ss -tlnp 2>/dev/null | grep -qE ":$port[[:space:]]|:$port$"; then
                        has_host_process=1
                        break
                    fi
                fi
            fi
        done
        
        if [ $has_host_process -eq 1 ]; then
            print_error "检测到宿主机进程占用端口，这可能导致容器启动失败！"
            echo ""
            echo "请选择操作："
            echo "  1. 尝试停止宿主机上的 Redis/TDengine 服务（如果存在）"
            echo "  2. 手动处理端口冲突（推荐：停止占用端口的服务或修改 docker-compose.yml 端口映射）"
            echo "  3. 继续启动（可能会失败）"
            echo ""
            read -p "请输入选项 (1/2/3): " choice
        else
            echo "请选择操作："
            echo "  1. 自动强制清理所有冲突容器和进程（推荐）"
            echo "  2. 手动处理端口冲突"
            echo "  3. 继续启动（可能失败）"
            echo ""
            read -p "请输入选项 (1/2/3): " choice
        fi
        
        case "$choice" in
            1)
                if [ $has_host_process -eq 1 ]; then
                    # 尝试停止宿主机服务
                    print_info "尝试停止宿主机上的服务..."
                    
                    for port_entry in "${conflict_ports[@]}"; do
                        # 处理端口格式（可能是 "port" 或 "port/udp"）
                        local port="${port_entry%%/*}"
                        local port_type="${port_entry##*/}"
                        
                        # 检查是否是 ZLMediaKit UDP 端口范围
                        if [ "$port_type" = "udp" ] && [[ "$port" =~ ^30[0-5][0-9][0-9]$ ]]; then
                            print_info "检测到 ZLMediaKit UDP 端口 $port 被占用，尝试清理..."
                            
                            # 查找并停止所有 zlmediakit 相关进程
                            local zlm_pids=$(pgrep -f "zlmediakit\|MediaServer" 2>/dev/null || echo "")
                            if [ -n "$zlm_pids" ]; then
                                echo "$zlm_pids" | while read -r pid; do
                                    if [ -n "$pid" ]; then
                                        local proc_name=$(ps -p "$pid" -o comm= 2>/dev/null || echo "")
                                        print_info "发现 ZLMediaKit 进程: $proc_name (PID: $pid)，尝试停止..."
                                        sudo kill -TERM "$pid" 2>/dev/null || true
                                        sleep 1
                                        if kill -0 "$pid" 2>/dev/null; then
                                            print_info "强制停止进程 PID: $pid"
                                            sudo kill -KILL "$pid" 2>/dev/null || true
                                        fi
                                    fi
                                done
                                sleep 2
                            fi
                            
                            # 查找并停止所有 ZLMediaKit 容器
                            local zlm_containers=$(docker ps -a --filter "name=zlmediakit" --format "{{.ID}}" 2>/dev/null || echo "")
                            if [ -n "$zlm_containers" ]; then
                                echo "$zlm_containers" | while read -r container_id; do
                                    if [ -n "$container_id" ]; then
                                        print_info "强制停止并删除 ZLMediaKit 容器: $container_id"
                                        docker stop -t 0 "$container_id" 2>/dev/null || true
                                        docker rm -f "$container_id" 2>/dev/null || true
                                    fi
                                done
                                sleep 2
                            fi
                            
                            # 查找占用 UDP 端口的进程
                            if command -v lsof &> /dev/null; then
                                local udp_process=$(lsof -i UDP:$port 2>/dev/null | grep -v COMMAND | head -1 || echo "")
                                if [ -n "$udp_process" ]; then
                                    local pid=$(echo "$udp_process" | awk '{print $2}')
                                    if [ -n "$pid" ] && [ "$pid" != "PID" ]; then
                                        print_info "发现占用 UDP 端口 $port 的进程 (PID: $pid)，尝试停止..."
                                        sudo kill -TERM "$pid" 2>/dev/null || true
                                        sleep 1
                                        if kill -0 "$pid" 2>/dev/null; then
                                            print_info "强制停止进程 PID: $pid"
                                            sudo kill -KILL "$pid" 2>/dev/null || true
                                        fi
                                    fi
                                fi
                            fi
                            continue
                        fi
                        
                        # 检查是否是 Redis 端口
                        if [ "$port" = "6379" ]; then
                            print_info "检测到 Redis 端口 6379 被占用，尝试停止系统 Redis 服务..."
                            # 尝试停止常见的 Redis 服务
                            if systemctl is-active --quiet redis 2>/dev/null || systemctl is-active --quiet redis-server 2>/dev/null; then
                                print_info "停止 Redis 系统服务..."
                                sudo systemctl stop redis 2>/dev/null || sudo systemctl stop redis-server 2>/dev/null || true
                                sleep 2
                            fi
                            
                            # 尝试通过进程名查找并停止
                            local redis_pid=$(pgrep -f "redis-server" 2>/dev/null | head -1 || echo "")
                            if [ -n "$redis_pid" ]; then
                                print_info "发现 Redis 进程 (PID: $redis_pid)，尝试停止..."
                                sudo kill "$redis_pid" 2>/dev/null || true
                                sleep 2
                            fi
                        fi
                        
                        # 检查是否是 TDengine 端口（6030, 6041, 6060, 6043-6049）
                        if [[ "$port" =~ ^60[34][0-9]$ ]] || [ "$port" = "6030" ] || [ "$port" = "6041" ] || [ "$port" = "6060" ]; then
                            print_info "检测到 TDengine 端口 $port 被占用，尝试彻底停止所有 TDengine 相关服务..."
                            
                            # 1. 停止 systemd 服务（如果存在）
                            if systemctl is-active --quiet taosd 2>/dev/null; then
                                print_info "停止 TDengine systemd 服务..."
                                sudo systemctl stop taosd 2>/dev/null || true
                                sudo systemctl disable taosd 2>/dev/null || true
                                sleep 2
                            fi
                            
                            # 2. 停止所有 TDengine 相关进程（包括容器中的）
                            print_info "查找并停止所有 TDengine 相关进程..."
                            
                            # 查找所有 taos 相关进程（包括 taosd, taosadapter, taoskeeper, taos-explorer, udfd）
                            local taos_pids=$(pgrep -f "taos" 2>/dev/null || echo "")
                            if [ -n "$taos_pids" ]; then
                                echo "$taos_pids" | while read -r pid; do
                                    if [ -n "$pid" ]; then
                                        local proc_name=$(ps -p "$pid" -o comm= 2>/dev/null || echo "")
                                        print_info "发现 TDengine 进程: $proc_name (PID: $pid)，尝试停止..."
                                        sudo kill -TERM "$pid" 2>/dev/null || true
                                        sleep 1
                                        # 如果进程仍在运行，强制杀死
                                        if kill -0 "$pid" 2>/dev/null; then
                                            print_info "强制停止进程 PID: $pid"
                                            sudo kill -KILL "$pid" 2>/dev/null || true
                                        fi
                                    fi
                                done
                                sleep 2
                            fi
                            
                            # 3. 停止所有包含 taos 的 Docker 容器
                            print_info "查找并停止所有 TDengine 相关 Docker 容器..."
                            local taos_containers=$(docker ps -a --filter "name=taos" --format "{{.ID}}" 2>/dev/null || echo "")
                            if [ -n "$taos_containers" ]; then
                                echo "$taos_containers" | while read -r cid; do
                                    if [ -n "$cid" ]; then
                                        local container_name=$(docker ps -a --filter "id=$cid" --format "{{.Names}}" 2>/dev/null || echo "")
                                        print_info "停止 TDengine 容器: $container_name ($cid)"
                                        docker stop -t 0 "$cid" 2>/dev/null || true
                                        docker rm -f "$cid" 2>/dev/null || true
                                    fi
                                done
                                sleep 2
                            fi
                            
                            # 4. 再次检查并强制清理残留进程
                            sleep 2
                            local remaining_pids=$(pgrep -f "taos" 2>/dev/null || echo "")
                            if [ -n "$remaining_pids" ]; then
                                print_warning "仍有 TDengine 进程残留，强制清理..."
                                echo "$remaining_pids" | while read -r pid; do
                                    if [ -n "$pid" ]; then
                                        sudo kill -KILL "$pid" 2>/dev/null || true
                                    fi
                                done
                                sleep 1
                            fi
                            
                            # 5. 检查端口是否已释放
                            sleep 2
                            if command -v ss &> /dev/null && ss -tlnp 2>/dev/null | grep -qE ":$port[[:space:]]|:$port$"; then
                                print_warning "端口 $port 仍被占用，可能不是 TDengine 进程"
                                print_info "占用端口的进程信息:"
                                ss -tlnp 2>/dev/null | grep -E ":$port[[:space:]]|:$port$" || true
                            else
                                print_success "TDengine 端口 $port 已释放"
                            fi
                        fi
                    done
                    
                    # 等待端口释放
                    print_info "等待端口释放..."
                    sleep 3
                    
                    # 再次检查端口
                    local still_occupied=0
                    for port in "${conflict_ports[@]}"; do
                        if command -v ss &> /dev/null && ss -tlnp 2>/dev/null | grep -qE ":$port[[:space:]]|:$port$"; then
                            print_warning "端口 $port 仍被占用"
                            still_occupied=1
                        fi
                    done
                    
                    if [ $still_occupied -eq 1 ]; then
                        print_error "无法自动释放端口，请手动处理"
                        print_info "检查命令: sudo lsof -i :端口号 或 sudo ss -tlnp | grep 端口号"
                        print_info "停止服务命令示例:"
                        print_info "  sudo systemctl stop redis  # Redis"
                        print_info "  sudo systemctl stop taosd  # TDengine"
                        print_info "或修改 docker-compose.yml 中的端口映射（如 6379 改为 6380）"
                        echo ""
                        read -p "是否继续启动（可能会失败）？(y/N): " continue_choice
                        if [ "$continue_choice" != "y" ] && [ "$continue_choice" != "Y" ]; then
                            print_info "已取消启动"
                            exit 1
                        fi
                    else
                        print_success "端口已释放"
                    fi
                else
                    # 清理 Docker 容器
                    print_info "正在强制清理冲突的容器..."
                    for container_id in "${conflict_containers[@]}"; do
                        if [ -n "$container_id" ]; then
                            print_info "强制停止并删除容器: $container_id"
                            docker stop -t 0 "$container_id" 2>/dev/null || true
                            docker rm -f "$container_id" 2>/dev/null || true
                        fi
                    done
                    
                    # 清理所有相关容器（按名称）
                    for port in "${conflict_ports[@]}"; do
                        for service in "${MIDDLEWARE_SERVICES[@]}"; do
                            if [ "${MIDDLEWARE_PORTS[$service]}" = "$port" ]; then
                                local container_name=""
                                case "$service" in
                                    "TDengine") container_name="tdengine-server" ;;
                                    "Redis") container_name="redis-server" ;;
                                    "PostgresSQL") container_name="postgres-server" ;;
                                    "Nacos") container_name="nacos-server" ;;
                                    "Kafka") container_name="kafka-server" ;;
                                    "MinIO") container_name="minio-server" ;;
                                    "SRS") container_name="srs-server" ;;
                                    "NodeRED") container_name="nodered-server" ;;
                                    "FUXA") container_name="fuxa-server" ;;
                                    "EMQX") container_name="emqx-server" ;;
                                    "ZLMediaKit") container_name="zlmediakit-server" ;;
                                    "Milvus") container_name="milvus-server" ;;
                                esac
                                
                                if [ -n "$container_name" ]; then
                                    docker ps -a --filter "name=^${container_name}$" --format "{{.ID}}" 2>/dev/null | while read -r cid; do
                                        if [ -n "$cid" ]; then
                                            print_info "清理容器: $container_name ($cid)"
                                            docker stop -t 0 "$cid" 2>/dev/null || true
                                            docker rm -f "$cid" 2>/dev/null || true
                                        fi
                                    done
                                fi
                                break
                            fi
                        done
                    done
                fi
                
                sleep 3
                print_success "容器清理完成"
                
                # 等待端口释放
                print_info "等待端口释放（最多等待 5 秒）..."
                local wait_count=0
                local max_wait=5
                while [ $wait_count -lt $max_wait ]; do
                    local ports_still_in_use=0
                    for port in "${conflict_ports[@]}"; do
                        # 检查是否还有 Docker 容器占用
                        local docker_using=$(docker ps --format "{{.Ports}}" 2>/dev/null | grep -E ":$port->|0\.0\.0\.0:$port|:::$port" || echo "")
                        if [ -n "$docker_using" ]; then
                            ports_still_in_use=1
                            break
                        fi
                    done
                    
                    if [ $ports_still_in_use -eq 0 ]; then
                        break
                    fi
                    
                    wait_count=$((wait_count + 1))
                    sleep 1
                    echo -n "."
                done
                echo ""
                
                # 再次检查端口（区分 Docker 和宿主机进程）
                print_info "再次检查端口状态..."
                local still_conflict=0
                local host_process_conflict=0
                for port in "${conflict_ports[@]}"; do
                    # 先检查是否是 Docker 容器占用
                    local docker_using=$(docker ps --format "{{.ID}}\t{{.Names}}\t{{.Ports}}" 2>/dev/null | grep -E ":$port->|0\.0\.0\.0:$port|:::$port" || echo "")
                    
                    if [ -n "$docker_using" ]; then
                        print_error "端口 $port 仍被 Docker 容器占用:"
                        echo "$docker_using" | while read -r line; do
                            print_info "  $line"
                        done
                        still_conflict=1
                    elif command -v ss &> /dev/null && ss -tlnp 2>/dev/null | grep -qE ":$port[[:space:]]|:$port$"; then
                        # 检查是否是宿主机进程占用
                        local host_process=$(ss -tlnp 2>/dev/null | grep -E ":$port[[:space:]]|:$port$" | head -1 || echo "")
                        if [ -n "$host_process" ]; then
                            print_error "端口 $port 被宿主机进程占用（非 Docker）:"
                            print_info "  $host_process"
                            print_info "  这可能是系统服务，需要手动停止或修改配置"
                            host_process_conflict=1
                        fi
                    fi
                done
                
                if [ $still_conflict -eq 1 ]; then
                    print_error "部分端口仍被 Docker 容器占用，启动可能会失败"
                    print_info "建议手动检查并清理: docker ps | grep 端口号"
                elif [ $host_process_conflict -eq 1 ]; then
                    print_error "部分端口被宿主机进程占用，启动可能会失败"
                    print_info "建议手动检查: sudo lsof -i :端口号 或 sudo ss -tlnp | grep 端口号"
                    print_info "如果是系统服务，可能需要停止服务或修改 docker-compose.yml 中的端口映射"
                fi
                ;;
            2)
                print_info "请手动处理端口冲突后重新运行此脚本"
                print_info "冲突端口: ${conflict_ports[*]}"
                print_info "检查命令: sudo lsof -i :端口号 或 sudo ss -tlnp | grep 端口号"
                exit 1
                ;;
            3)
                print_warning "继续启动，可能会失败..."
                ;;
            *)
                print_error "无效选项"
                exit 1
                ;;
        esac
    else
        print_success "所有端口检查通过"
    fi
}

# 清理残留的容器（与 compose 项目相关的）
cleanup_stale_containers() {
    print_info "检查并清理残留容器..."
    
    # 获取所有中间件容器名称
    local container_names=()
    for service in "${MIDDLEWARE_SERVICES[@]}"; do
        local container_name=$(docker-compose -f "$COMPOSE_FILE" ps -q "$service" 2>/dev/null || echo "")
        if [ -z "$container_name" ]; then
            # 尝试通过容器名称查找
            case "$service" in
                "Nacos") container_names+=("nacos-server") ;;
                "PostgresSQL") container_names+=("postgres-server") ;;
                "TDengine") container_names+=("tdengine-server") ;;
                "Redis") container_names+=("redis-server") ;;
                "Kafka") container_names+=("kafka-server") ;;
                "MinIO") container_names+=("minio-server") ;;
                "Milvus") container_names+=("milvus-server") ;;
                "SRS") container_names+=("srs-server") ;;
                "NodeRED") container_names+=("nodered-server") ;;
                "FUXA") container_names+=("fuxa-server") ;;
                "EMQX") container_names+=("emqx-server") ;;
                "ZLMediaKit") container_names+=("zlmediakit-server") ;;
            esac
        fi
    done
    
    # 检查是否有停止的容器需要清理
    local stale_containers=$(docker ps -a --filter "status=exited" --format "{{.Names}}" 2>/dev/null | grep -E "(nacos-server|postgres-server|tdengine-server|redis-server|kafka-server|minio-server|milvus-server|srs-server|nodered-server|fuxa-server|emqx-server|zlmediakit-server)" || echo "")
    
    if [ -n "$stale_containers" ]; then
        print_info "发现残留的停止容器，正在清理..."
        echo "$stale_containers" | while read -r container; do
            print_info "删除残留容器: $container"
            docker rm "$container" 2>/dev/null || true
        done
        sleep 1
    fi

    cleanup_renamed_containers
    fix_nacos_startup_failure
}

# 清理 compose recreate 被中断后遗留的「改名孤儿容器」（形如 <12位hex>_postgres-server）。
# recreate 时 compose 先把旧容器改名让出 container_name，中途被打断旧容器就残留；
# 它的服务标签仍在 compose 文件中，下次 up 会把它当正主——若仍在运行还占着端口/数据目录。
# 上面的 cleanup_stale_containers 只清 exited 容器，覆盖不到「仍在运行」的改名孤儿，故单列。
cleanup_renamed_containers() {
    local names
    names=$(docker ps -a --format '{{.Names}}' 2>/dev/null | grep -E '^[0-9a-f]{12}_[a-z]+-(server|init|worker)$' || true)
    [ -z "$names" ] && return 0
    print_warning "清理上次中断遗留的改名孤儿容器: $(echo "$names" | tr '\n' ' ')"
    echo "$names" | xargs -r docker rm -f >/dev/null 2>&1 || true
}

# Nacos 官方镜像（不用 slim：cgroup v2 宿主机上 slim 内嵌 Derby 会 NPE 崩溃）
NACOS_IMAGE="${NACOS_IMAGE:-nacos/nacos-server:v2.5.1}"

# 删除 nacos-server 及其匿名卷后按 compose 重建（Derby 损坏 / cgroup 崩溃等场景共用）
_recreate_nacos_container() {
    local reason="$1"
    print_warning "$reason"
    print_info "删除 nacos-server 容器及匿名数据卷并重建（镜像: ${NACOS_IMAGE}）..."
    docker rm -f -v nacos-server >/dev/null 2>&1 || true
    local _host_arch _nacos_platform=""
    _host_arch=$(uname -m)
    case "$_host_arch" in
        x86_64)  _nacos_platform="linux/amd64" ;;
        aarch64) _nacos_platform="linux/arm64" ;;
    esac
    if [ -n "$_nacos_platform" ]; then
        print_info "拉取 Nacos 镜像 (${NACOS_IMAGE}, ${_nacos_platform})..."
        docker pull --platform "$_nacos_platform" "$NACOS_IMAGE" 2>&1 | tee -a "$LOG_FILE" || true
        export NACOS_PLATFORM="$_nacos_platform"
    fi
    mw_compose up -d Nacos 2>&1 | tee -a "$LOG_FILE" || true
    unset NACOS_PLATFORM
}

# Nacos 启动失败自愈：Derby 半成品损坏、cgroup v2 + slim 镜像崩溃、容器 Restarting 等
fix_nacos_startup_failure() {
    middleware_service_enabled Nacos || return 0
    docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q '^nacos-server$' || return 0

    local status health
    status=$(container_status nacos-server)
    health=$(docker inspect -f '{{.State.Health.Status}}' nacos-server 2>/dev/null) || health=""

    if [ "$status" = "running" ]; then
        if curl -s -m 2 "http://localhost:8848/nacos/actuator/health" >/dev/null 2>&1; then
            return 0
        fi
        [ "$health" = "healthy" ] && return 0
    fi

    local logs reason=""
    logs=$(docker logs --tail 200 nacos-server 2>&1 || true)

    if echo "$logs" | grep -q "does not contain the expected 'service.properties'"; then
        reason="检测到 Nacos 内嵌 Derby 半成品损坏（初始化曾被中断）"
    elif echo "$logs" | grep -qE "CgroupV2Subsystem\.getInstance|cgroupv2\.CgroupV2Subsystem"; then
        reason="检测到 Nacos Derby 在 cgroup v2 宿主机启动失败（已切换为标准版镜像 ${NACOS_IMAGE}）"
    elif echo "$status" | grep -qiE "restarting|exited|created"; then
        reason="检测到 Nacos 容器状态异常: ${status}"
    else
        return 0
    fi

    _recreate_nacos_container "${reason}，正在自愈..."
}

fix_nacos_derby_corruption() {
    fix_nacos_startup_failure
}

# Nacos 2.2.1+ 开启鉴权后不再内置默认账号：全新数据卷（首次安装或 Derby 修复重建后）里
# 没有任何用户，业务服务登录会报 "User nacos not found"。
# Nacos 2.2+ 在 auth 开启后 /v1/auth/users/admin 可能不支持匿名调用，需用默认 nacos/nacos 登录后创建。
# 密码必须与各服务 bootstrap-*.yaml 的 spring.cloud.nacos.*.password 一致。
NACOS_INIT_PASSWORD="${NACOS_INIT_PASSWORD:-basiclab@iot78475418754}"
NACOS_DEFAULT_PASSWORD="${NACOS_DEFAULT_PASSWORD:-nacos}"
ensure_nacos_admin_user() {
    docker ps --format '{{.Names}}' 2>/dev/null | grep -q '^nacos-server$' || return 0

    print_info "初始化 Nacos 管理员账号与 dev 命名空间（用户 nacos，密码与各服务 bootstrap 一致）..."

    if ! wait_for_nacos; then
        print_error "Nacos 服务未就绪，无法自动初始化账号"
        print_info "排查: docker logs nacos-server --tail 80"
        return 1
    fi

    local resp token

    # 先用目标密码尝试登录；成功说明 admin 已正确初始化
    if curl -s -m 5 -X POST "http://localhost:8848/nacos/v1/auth/login" \
        --data-urlencode "username=nacos" --data-urlencode "password=${NACOS_INIT_PASSWORD}" 2>/dev/null \
        | grep -q '"accessToken"'; then
        # admin 已存在且密码正确，确保 dev 命名空间存在
        token=$(curl -s -m 5 -X POST "http://localhost:8848/nacos/v1/auth/login" \
            --data-urlencode "username=nacos" --data-urlencode "password=${NACOS_INIT_PASSWORD}" 2>/dev/null \
            | sed -n 's/.*"accessToken":"\([^"]*\)".*/\1/p')
        if [ -n "$token" ]; then
            curl -s -m 5 -X POST "http://localhost:8848/nacos/v1/console/namespaces?accessToken=${token}" \
                -d "customNamespaceId=dev&namespaceName=dev&namespaceDesc=dev" >/dev/null 2>&1 || true
        fi
        return 0
    fi

    # 目标密码登录失败，尝试旧版匿名 /v1/auth/users/admin 接口（兼容 Nacos <2.2）
    resp=$(curl -s -m 5 -X POST "http://localhost:8848/nacos/v1/auth/users/admin" \
        --data-urlencode "password=${NACOS_INIT_PASSWORD}" 2>/dev/null || true)
    if echo "$resp" | grep -q '"username"'; then
        print_success "Nacos admin 用户已初始化（匿名接口，用户 nacos，密码与服务 bootstrap 一致）"
        token=$(curl -s -m 5 -X POST "http://localhost:8848/nacos/v1/auth/login" \
            --data-urlencode "username=nacos" --data-urlencode "password=${NACOS_INIT_PASSWORD}" 2>/dev/null \
            | sed -n 's/.*"accessToken":"\([^"]*\)".*/\1/p')
        [ -n "$token" ] && curl -s -m 5 -X POST "http://localhost:8848/nacos/v1/console/namespaces?accessToken=${token}" \
            -d "customNamespaceId=dev&namespaceName=dev&namespaceDesc=dev" >/dev/null 2>&1 || true
        print_info "Nacos 命名空间 dev 已创建"
        return 0
    fi

    # 匿名接口也失败，尝试用默认密码 nacos/nacos 登录（Nacos 2.5 首次启动默认账号）
    token=$(curl -s -m 5 -X POST "http://localhost:8848/nacos/v1/auth/login" \
        --data-urlencode "username=nacos" --data-urlencode "password=${NACOS_DEFAULT_PASSWORD}" 2>/dev/null \
        | sed -n 's/.*"accessToken":"\([^"]*\)".*/\1/p')
    if [ -n "$token" ]; then
        print_info "使用 Nacos 默认密码登录成功，正在修改密码..."
        # 修改密码为目标密码
        local change_resp
        change_resp=$(curl -s -m 5 -X PUT "http://localhost:8848/nacos/v1/auth/users?accessToken=${token}" \
            --data-urlencode "username=nacos" \
            --data-urlencode "newPassword=${NACOS_INIT_PASSWORD}" 2>/dev/null || true)
        if echo "$change_resp" | grep -qE '"code":200|"ok":true'; then
            print_success "Nacos admin 密码已更新为目标密码"
            # 确保 dev 命名空间
            curl -s -m 5 -X POST "http://localhost:8848/nacos/v1/console/namespaces?accessToken=${token}" \
                -d "customNamespaceId=dev&namespaceName=dev&namespaceDesc=dev" >/dev/null 2>&1 || true
            print_info "Nacos 命名空间 dev 已创建"
            return 0
        fi
        print_warning "Nacos 密码修改失败（PUT 接口返回: ${change_resp}），尝试直接创建用户..."
    fi

    # 最后兜底：用默认密码登录后直接 POST 创建用户（覆盖已存在的）
    if [ -z "$token" ]; then
        token=$(curl -s -m 5 -X POST "http://localhost:8848/nacos/v1/auth/login" \
            --data-urlencode "username=nacos" --data-urlencode "password=${NACOS_DEFAULT_PASSWORD}" 2>/dev/null \
            | sed -n 's/.*"accessToken":"\([^"]*\)".*/\1/p')
    fi
    if [ -n "$token" ]; then
        curl -s -m 5 -X POST "http://localhost:8848/nacos/v1/auth/users?accessToken=${token}" \
            --data-urlencode "username=nacos" \
            --data-urlencode "password=${NACOS_INIT_PASSWORD}" >/dev/null 2>&1 || true
        # 再验证
        if curl -s -m 5 -X POST "http://localhost:8848/nacos/v1/auth/login" \
            --data-urlencode "username=nacos" --data-urlencode "password=${NACOS_INIT_PASSWORD}" 2>/dev/null \
            | grep -q '"accessToken"'; then
            print_success "Nacos admin 用户已创建并验证通过（用户 nacos，密码与服务 bootstrap 一致）"
            curl -s -m 5 -X POST "http://localhost:8848/nacos/v1/console/namespaces?accessToken=${token}" \
                -d "customNamespaceId=dev&namespaceName=dev&namespaceDesc=dev" >/dev/null 2>&1 || true
            print_info "Nacos 命名空间 dev 已创建"
            return 0
        fi
    fi

    print_error "Nacos admin 用户自动初始化失败，请手动配置"
    print_info "1. 登录 http://localhost:8848/nacos（默认账号 nacos/nacos）"
    print_info "2. 将 nacos 用户密码改为: ${NACOS_INIT_PASSWORD}"
    print_info "3. 创建命名空间: namespaceId=dev, namespaceName=dev"
    print_info "4. 配置完成后可重新运行: ./install_middleware_linux.sh install"
    return 1
}

# up 失败时自动展示 unhealthy 容器：健康检查最后输出 + 容器日志尾部，免手动逐个排查。
# 健康检查输出很关键——部分服务（如 TDengine 的 taos CLI 探测）失败原因只出现在这里，容器日志里看不到。
show_unhealthy_containers() {
    local names n
    names=$(docker ps --filter "health=unhealthy" --format '{{.Names}}' 2>/dev/null || true)
    [ -z "$names" ] && return 0
    for n in $names; do
        print_warning "unhealthy 容器: $n —— 健康检查最后输出："
        docker inspect --format '{{range .State.Health.Log}}[exit={{.ExitCode}}] {{.Output}}{{end}}' "$n" 2>/dev/null | tail -n 5 || true
        print_warning "$n 日志尾部："
        docker logs --tail 30 "$n" 2>&1 | tail -30 || true
        echo ""
    done
}

# 安装所有中间件
install_middleware() {
    print_section "开始安装所有中间件"
    
    # 配置 apt 国内源（在安装依赖之前）
    configure_apt_mirror
    
    # 配置 pip 镜像源
    configure_pip_mirror
    
    check_docker "$@"
    check_docker_compose
    
    # 检查并安装 nvidia-container-toolkit（在配置 Docker 镜像源之前）
    check_and_install_nvidia_container_toolkit
    
    # 配置 Docker 镜像源（需要在 nvidia-container-toolkit 安装之后）
    configure_docker_mirror
    check_compose_file
    create_network
    
    # 创建所有中间件的存储目录（如果不存在则创建新的）
    create_all_storage_directories
    
    # 确保关键目录的权限正确（这些函数会检查并设置权限）
    create_postgresql_directories
    create_redis_directories
    create_nodered_directories
    create_fuxa_directories
    prepare_kafka_if_enabled
    
    # 强制更新 SRS 配置文件（重新获取宿主机 IP）
    prepare_srs_config
    prepare_emqx_volumes
    prepare_milvus_config
    
    # 准备 ZLMediaKit 配置文件
    prepare_zlmediakit_config

    
    # 检查并拉取缺失的镜像（如果镜像已存在则跳过拉取）
    echo ""
    check_and_pull_images
    
    # 清理残留容器
    cleanup_stale_containers
    
    # 检查端口占用
    check_and_clean_ports
    
    print_section "启动中间件容器"
    # 取 PIPESTATUS[0] 判定（tee 恒 0，`if 管道` 永远走成功分支，失败会被掩盖）
    local -a _skip_optional=()
    read -r -a _skip_optional <<< "$(collect_skippable_optional_services)"
    # 用 if 包裹以防止 compose_up 返回非零时触发 set -e（如 ZLMediaKit rlimit 等非致命错误）
    if compose_up_middleware "${_skip_optional[@]}"; then
        _up_rc=0
        print_success "容器启动命令执行完成"
    else
        _up_rc=$?
        print_error "容器启动过程中出现错误（compose 退出码 ${_up_rc}），unhealthy 容器自动诊断："
        show_unhealthy_containers
    fi

    # 如果 SRS 容器已经在运行，重启它以重新加载配置文件
    if docker ps --filter "name=srs-server" --format "{{.Names}}" | grep -q "srs-server"; then
        print_info "检测到 SRS 容器正在运行，重启以重新加载配置文件..."
        docker restart srs-server 2>&1 | tee -a "$LOG_FILE" || true
        print_success "SRS 容器已重启，配置文件已重新加载"
    fi
    
    # 检查启动状态
    sleep 3
    print_info "检查容器启动状态..."
    local failed_containers=()
    for service in "${MIDDLEWARE_SERVICES[@]}"; do
        middleware_service_enabled "$service" || continue
        local container_name=""
        case "$service" in
            "Nacos") container_name="nacos-server" ;;
            "PostgresSQL") container_name="postgres-server" ;;
            "TDengine") container_name="tdengine-server" ;;
            "Redis") container_name="redis-server" ;;
            "Kafka") container_name="kafka-server" ;;
            "MinIO") container_name="minio-server" ;;
            "SRS") container_name="srs-server" ;;
            "NodeRED") container_name="nodered-server" ;;
            "FUXA") container_name="fuxa-server" ;;
            "EMQX") container_name="emqx-server" ;;
            "ZLMediaKit") container_name="zlmediakit-server" ;;
            "Milvus") container_name="milvus-server" ;;
        esac
        
        if [ -n "$container_name" ]; then
            local container_status=$(docker ps -a --filter "name=^${container_name}$" --format "{{.Status}}" 2>/dev/null | head -1 || echo "")
            if [ -n "$container_status" ]; then
                if echo "$container_status" | grep -qE "Exited|Dead|Restarting|Created"; then
                    if echo "$container_status" | grep -q "Created"; then
                        print_warning "$service ($container_name) 容器处于 Created 状态（OCI 启动失败，如 /dev/null 错误）"
                    else
                        print_warning "$service ($container_name) 容器状态异常: $container_status"
                    fi
                    failed_containers+=("$service")
                fi
            fi
        fi
    done
    
    if [ ${#failed_containers[@]} -gt 0 ]; then
        echo ""
        print_error "以下容器启动失败: ${failed_containers[*]}"
        print_info "查看详细日志命令:"
        for service in "${failed_containers[@]}"; do
            case "$service" in
                "TDengine") print_info "  docker logs tdengine-server" ;;
                "Redis") print_info "  docker logs redis-server" ;;
                "Milvus") print_info "  docker logs milvus-server" ;;
                *) print_info "  docker-compose logs $service" ;;
            esac
        done
        echo ""
        # 二次修复：status 检查后可能有容器进入 Created 状态（compose_up 之后的延迟启动）
        _repair_created_middleware_containers || true
    fi

    # Nacos 启动失败自愈 + 账号初始化（非致命：不中断后续 PostgreSQL/MinIO 等步骤）
    if middleware_service_enabled Nacos; then
        print_section "配置 Nacos 注册中心"
        fix_nacos_startup_failure
        if wait_for_nacos; then
            ensure_nacos_admin_user || print_warning "Nacos 账号自动初始化未完成，init_databases 阶段将再次尝试"
        else
            print_error "Nacos 服务未就绪，业务服务将无法注册到配置中心"
            print_info "排查命令: docker logs nacos-server --tail 80"
            docker logs --tail 30 nacos-server 2>&1 | tee -a "$LOG_FILE" || true
        fi
    fi

    # 等待 Milvus 就绪并输出部署日志
    echo ""
    if middleware_service_enabled "Milvus"; then
        print_section "部署 Milvus 向量数据库"
        wait_for_milvus || print_warning "Milvus 未就绪，人脸识别等向量检索功能可能不可用"
        print_info "Milvus 向量库: http://localhost:9091/healthz, gRPC localhost:19530"
        print_info "  查看日志: ./install_middleware_linux.sh logs Milvus"
    else
        print_info "当前部署形态 (${EASYAIOT_DEPLOY_PROFILE}) 跳过 Milvus"
    fi

    print_success "中间件安装完成"
    echo ""

    # 以下均为 post-install 初始配置：任意失败不中断整体流程（set -e 下 return 1 会杀死脚本）。
    # 若此时 PostgreSQL/MinIO 仍未就绪，由外层 install_linux.sh 的 wait_for_base_services + _repair_created_containers 兜底修复后，
    # 下次重启时会通过 restart/start 流程再次执行这些初始化。

    # ★ 先等待关键基础服务就绪（PostgreSQL），再执行需要数据库连通的 post-install 步骤
    #    避免 "容器未运行" 警告淹没真正的启动失败信号
    echo ""
    if container_exists postgres-server; then
        if container_running postgres-server; then
            wait_for_postgresql || print_warning "PostgreSQL 未在预期时间内就绪，部分配置可能跳过"
        else
            local _pg_status; _pg_status=$(container_status postgres-server)
            print_warning "PostgreSQL 容器存在但未运行（状态: ${_pg_status}），尝试修复..."
            _repair_created_middleware_containers || true
            # 修复后等待 PostgreSQL 就绪（最多 30s，给它启动时间）
            if container_running postgres-server; then
                wait_for_postgresql || print_warning "PostgreSQL 修复后仍未就绪"
            else
                print_error "PostgreSQL 容器无法启动，请检查: docker logs postgres-server --tail 50"
                print_info "常见原因：数据目录权限、端口冲突、磁盘空间不足"
            fi
        fi
    else
        print_error "PostgreSQL 容器不存在！请检查 docker-compose.yml 及 compose up 日志"
        print_info "手动检查: docker ps -a | grep postgres; docker compose -f ${COMPOSE_FILE} logs postgres"
    fi

    echo ""
    ensure_postgresql_password     || print_warning "PostgreSQL 密码检查跳过（容器未就绪）"

    echo ""
    configure_postgresql_pg_hba    || print_warning "pg_hba.conf 配置跳过（容器未就绪）"

    echo ""
    configure_postgresql_max_connections || print_warning "max_connections 配置跳过（容器未就绪）"

    echo ""
    init_databases                 || print_warning "数据库初始化跳过（容器未就绪）"

    # 初始化 TDengine（仅启用 TDengine 中间件时）
    echo ""
    if [ "${EASYAIOT_ENABLE_TDENGINE:-0}" = "1" ] && docker ps --format '{{.Names}}' 2>/dev/null | grep -qx 'tdengine-server'; then
        init_tdengine || true
    else
        print_info "TDengine 未启用，跳过 TDengine 初始化（需要时: EASYAIOT_ENABLE_TDENGINE=1）"
    fi

    echo ""
    init_minio || print_warning "MinIO 初始化跳过"

    # 初始化/扩容 IoT Kafka 主题（64 分区：告警、人脸匹配、车牌匹配）
    echo ""
    init_kafka_topics_if_enabled

    
    sleep 5
    bash "${SCRIPT_DIR}/set_permanent_token.sh" >/dev/null 2>&1 || true
}

# 启动所有中间件
start_middleware() {
    print_section "启动所有中间件"
    
    check_docker "$@"
    check_docker_compose
    configure_docker_mirror
    check_compose_file
    create_network
    
    # 创建所有中间件的存储目录（如果不存在则创建新的）
    create_all_storage_directories
    
    # 确保关键目录的权限正确
    create_postgresql_directories
    create_redis_directories
    create_nodered_directories
    create_fuxa_directories
    prepare_kafka_if_enabled
    
    prepare_srs_config
    prepare_emqx_volumes
    prepare_milvus_config
    
    # 准备 ZLMediaKit 配置文件
    prepare_zlmediakit_config

    
    # 清理残留容器
    cleanup_stale_containers
    
    # 检查端口占用
    check_and_clean_ports
    
    local -a _skip_optional=()
    read -r -a _skip_optional <<< "$(collect_skippable_optional_services)"
    # 用 if 包裹以防止 compose_up 返回非零时触发 set -e（如 ZLMediaKit rlimit 等非致命错误）
    if compose_up_middleware "${_skip_optional[@]}"; then
        _up_rc=0
    else
        _up_rc=$?
    fi
    if middleware_service_enabled Nacos; then
        print_section "配置 Nacos 注册中心"
        fix_nacos_startup_failure
        wait_for_nacos || print_warning "Nacos 未就绪"
        ensure_nacos_admin_user || print_warning "Nacos 账号自动初始化未完成"
    fi

    if [ "${_up_rc:-0}" -eq 0 ]; then
        print_success "所有中间件启动完成"
    else
        print_error "部分中间件启动失败（compose 退出码 ${_up_rc}），unhealthy 容器自动诊断："
        show_unhealthy_containers
    fi
    echo ""
    init_kafka_topics_if_enabled
    echo ""
    if middleware_service_enabled "Milvus"; then
        print_section "检查 Milvus 向量数据库"
        wait_for_milvus || print_warning "Milvus 未就绪"
    else
        print_info "当前部署形态 (${EASYAIOT_DEPLOY_PROFILE}) 跳过 Milvus"
    fi

    # ★ 等待 PostgreSQL 就绪再执行需要数据库连通的 post-install 步骤
    echo ""
    if container_exists postgres-server; then
        if container_running postgres-server; then
            wait_for_postgresql || print_warning "PostgreSQL 未在预期时间内就绪，部分配置可能跳过"
        else
            local _pg_status; _pg_status=$(container_status postgres-server)
            print_warning "PostgreSQL 容器存在但未运行（状态: ${_pg_status}），尝试修复..."
            _repair_created_middleware_containers || true
            if container_running postgres-server; then
                wait_for_postgresql || print_warning "PostgreSQL 修复后仍未就绪"
            else
                print_error "PostgreSQL 容器无法启动，请检查: docker logs postgres-server --tail 50"
            fi
        fi
    else
        print_error "PostgreSQL 容器不存在！请检查 docker-compose.yml 及 compose up 日志"
    fi
    
    # 确保 PostgreSQL 密码正确（确保重启后密码正确）
    echo ""
    ensure_postgresql_password     || print_warning "PostgreSQL 密码检查跳过（容器未就绪）"

    # 配置 PostgreSQL pg_hba.conf 允许从宿主机连接
    echo ""
    configure_postgresql_pg_hba    || print_warning "pg_hba.conf 配置跳过（容器未就绪）"

    # 配置 PostgreSQL max_connections（最大连接数）
    echo ""
    configure_postgresql_max_connections || print_warning "max_connections 配置跳过（容器未就绪）"


    sleep 5
    bash "${SCRIPT_DIR}/set_permanent_token.sh" >/dev/null 2>&1 || true
}

# 停止所有中间件
stop_middleware() {
    print_section "停止所有中间件"
    
    check_docker "$@"
    check_docker_compose
    check_compose_file
    
    print_info "停止所有中间件服务..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" down 2>&1 | tee -a "$LOG_FILE"
    
    print_success "所有中间件已停止"
}

# 重启所有中间件
restart_middleware() {
    print_section "重启所有中间件"
    
    check_docker "$@"
    check_docker_compose
    configure_docker_mirror
    check_compose_file
    create_network
    
    # 创建所有中间件的存储目录（如果不存在则创建新的）
    create_all_storage_directories
    
    # 确保关键目录的权限正确
    create_postgresql_directories
    create_redis_directories
    create_nodered_directories
    create_fuxa_directories
    prepare_kafka_if_enabled
    
    prepare_srs_config
    prepare_emqx_volumes
    
    # 准备 ZLMediaKit 配置文件
    prepare_zlmediakit_config

    print_info "重启所有中间件服务..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" restart 2>&1 | tee -a "$LOG_FILE"
    
    print_success "所有中间件重启完成"
    echo ""
    # 不再固定 sleep 15：下方 init_kafka_iot_topics / ensure_postgresql_password
    # 各自带就绪轮询（Kafka while 重试、PG wait_for_postgresql），按需精确等待

    # ★ 等待 PostgreSQL 就绪再执行 post-restart 配置
    echo ""
    if container_exists postgres-server; then
        if container_running postgres-server; then
            wait_for_postgresql || print_warning "PostgreSQL 未在预期时间内就绪，部分配置可能跳过"
        else
            local _pg_status; _pg_status=$(container_status postgres-server)
            print_warning "PostgreSQL 容器存在但未运行（状态: ${_pg_status}），尝试修复..."
            _repair_created_middleware_containers || true
            if container_running postgres-server; then
                wait_for_postgresql || print_warning "PostgreSQL 修复后仍未就绪"
            else
                print_error "PostgreSQL 容器无法启动，请检查: docker logs postgres-server --tail 50"
            fi
        fi
    else
        print_error "PostgreSQL 容器不存在！请检查 docker-compose.yml 及 compose up 日志"
    fi

    echo ""
    init_kafka_topics_if_enabled
    
    # 确保 PostgreSQL 密码正确（确保重启后密码正确）
    echo ""
    ensure_postgresql_password     || print_warning "PostgreSQL 密码检查跳过（容器未就绪）"

    # 配置 PostgreSQL pg_hba.conf 允许从宿主机连接
    echo ""
    configure_postgresql_pg_hba    || print_warning "pg_hba.conf 配置跳过（容器未就绪）"

    # 配置 PostgreSQL max_connections（最大连接数）
    echo ""
    configure_postgresql_max_connections || print_warning "max_connections 配置跳过（容器未就绪）"


    sleep 5
    bash "${SCRIPT_DIR}/set_permanent_token.sh" >/dev/null 2>&1 || true
}

# 查看所有中间件状态
status_middleware() {
    print_section "所有中间件状态"
    
    check_docker "$@"
    check_docker_compose
    check_compose_file
    
    $COMPOSE_CMD -f "$COMPOSE_FILE" ps 2>&1 | tee -a "$LOG_FILE"

}

# 查看日志
view_logs() {
    local service=${1:-""}
    
    check_docker "$@"
    check_docker_compose
    check_compose_file

    if [ -z "$service" ]; then
        print_info "查看主中间件 compose 日志..."
        $COMPOSE_CMD -f "$COMPOSE_FILE" logs --tail=100 2>&1 | tee -a "$LOG_FILE"
    else
        print_info "查看 $service 服务日志..."
        $COMPOSE_CMD -f "$COMPOSE_FILE" logs --tail=100 "$service" 2>&1 | tee -a "$LOG_FILE"
    fi
}

# 构建所有镜像
build_middleware() {
    print_section "构建所有中间件镜像"
    
    check_docker "$@"
    check_docker_compose
    check_compose_file
    
    print_info "构建所有中间件镜像..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" build --no-cache 2>&1 | tee -a "$LOG_FILE"
    
    print_success "所有中间件镜像构建完成"
}

# 删除数据库
delete_databases() {
    print_section "删除数据库"
    
    # 等待 PostgreSQL 就绪
    if ! wait_for_postgresql; then
        print_warning "PostgreSQL 未就绪，无法删除数据库"
        return 1
    fi
    
    # 定义需要删除的数据库列表
    local databases=("iot-ai20" "iot-device20" "iot-video20" "iot-node20" "iot-visualize20" "ruoyi-vue-pro20")
    local deleted_count=0
    local total_count=${#databases[@]}
    
    for db_name in "${databases[@]}"; do
        if docker exec postgres-server psql -U postgres -lqt | cut -d \| -f 1 | grep -qw "$db_name"; then
            print_info "正在删除数据库: $db_name"
            if docker exec postgres-server psql -U postgres -c "DROP DATABASE \"$db_name\";" > /dev/null 2>&1; then
                print_success "数据库 $db_name 删除成功"
                deleted_count=$((deleted_count + 1))
            else
                print_error "数据库 $db_name 删除失败"
            fi
        else
            print_info "数据库 $db_name 不存在，跳过删除"
            deleted_count=$((deleted_count + 1))
        fi
    done
    
    echo ""
    print_section "数据库删除结果"
    echo "成功: ${GREEN}$deleted_count${NC} / $total_count"
    
    if [ $deleted_count -eq $total_count ]; then
        print_success "所有数据库删除完成！"
        return 0
    else
        print_warning "部分数据库删除失败"
        return 1
    fi
}


# 清理所有中间件
clean_middleware() {
    print_warning "这将删除所有中间件容器、数据卷和存储目录，确定要继续吗？(y/N)"
    print_info "注意：镜像不会被删除，以节省重新下载的时间"
    print_warning "警告：这将彻底删除所有数据，包括数据库、配置和日志！"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_section "清理所有中间件"
        
        check_docker "$@"
        check_docker_compose
        check_compose_file
        
        # 第一步：先停止所有容器（正常停止）
        print_info "正在停止所有中间件服务..."
        $COMPOSE_CMD -f "$COMPOSE_FILE" stop 2>&1 | tee -a "$LOG_FILE"
        
        # 等待容器停止
        sleep 3
        
        # 第二步：强制停止所有容器（处理重启循环中的容器）
        print_info "强制停止所有容器..."
        $COMPOSE_CMD -f "$COMPOSE_FILE" kill 2>&1 | tee -a "$LOG_FILE"
        
        # 等待容器完全停止
        sleep 2
        
        # 第三步：删除容器和 Docker 具名卷（明确不删除镜像）
        # 注意：使用 down -v 只会删除容器和卷，不会删除镜像
        # 如果要删除镜像，需要使用 down --rmi all 或 down --rmi local，这里不使用
        print_info "删除所有容器和 Docker 具名卷（镜像将保留，不会删除）..."
        $COMPOSE_CMD -f "$COMPOSE_FILE" down -v 2>&1 | tee -a "$LOG_FILE"
        
        # 第四步：检查并强制删除可能残留的容器（处理重启循环中的容器）
        print_info "检查并清理残留容器..."
        local remaining_containers=$($COMPOSE_CMD -f "$COMPOSE_FILE" ps -q 2>/dev/null || echo "")
        if [ -n "$remaining_containers" ]; then
            print_warning "发现残留容器，正在强制删除..."
            echo "$remaining_containers" | xargs -r docker rm -f 2>&1 | tee -a "$LOG_FILE"
        fi
        
        # 检查是否有通过 compose 项目名称创建的容器残留
        local project_containers=$(docker ps -a --filter "label=com.docker.compose.project" --format "{{.ID}}" 2>/dev/null || echo "")
        if [ -n "$project_containers" ]; then
            # 获取 compose 文件所在目录名作为项目名（如果使用默认项目名）
            local compose_dir=$(dirname "$COMPOSE_FILE")
            local project_name=$(basename "$compose_dir" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]//g')
            # 尝试通过项目名查找容器
            local project_containers_filtered=$(docker ps -a --filter "label=com.docker.compose.project=${project_name}" --format "{{.Names}}" 2>/dev/null || echo "")
            if [ -n "$project_containers_filtered" ]; then
                print_warning "发现项目相关残留容器，正在强制删除..."
                echo "$project_containers_filtered" | xargs -r docker rm -f 2>&1 | tee -a "$LOG_FILE"
            fi
        fi
        
        # 特别处理 SRS 容器（如果存在）
        local srs_containers=$(docker ps -a --filter "name=srs" --format "{{.Names}}" 2>/dev/null || echo "")
        if [ -n "$srs_containers" ]; then
            print_warning "发现 SRS 残留容器，正在强制删除..."
            echo "$srs_containers" | xargs -r docker rm -f 2>&1 | tee -a "$LOG_FILE"
        fi
        
        # 特别处理 ZLMediaKit 容器（如果存在）
        local zlmediakit_containers=$(docker ps -a --filter "name=zlmediakit" --format "{{.Names}}" 2>/dev/null || echo "")
        if [ -n "$zlmediakit_containers" ]; then
            print_warning "发现 ZLMediaKit 残留容器，正在强制删除..."
            echo "$zlmediakit_containers" | xargs -r docker rm -f 2>&1 | tee -a "$LOG_FILE"
        fi

        # 第五步：删除所有 bind mount 的宿主机存储目录
        print_info "删除所有 bind mount 存储目录..."
        
        # 定义所有需要删除的存储目录（相对于脚本目录）
        local data_dirs=(
            "standalone-logs"           # Nacos 日志
            "db_data"                   # PostgreSQL 数据和日志
            "taos_data"                 # TDengine 数据和日志
            "redis_data"                # Redis 数据和日志
            "mq_data"                   # Kafka 数据
            "minio_data"                # MinIO 数据和配置
            "milvus_data"               # Milvus 数据
            "milvus_config"             # Milvus 嵌入式 etcd 配置
            "srs_data"                  # SRS 配置、数据和回放
            "nodered_data"              # NodeRED 数据
        )
        
        # ZLMediaKit 目录需要特殊处理（相对路径）
        local zlmediakit_dir="${SCRIPT_DIR}/../zlmediakit"
        
        # 删除每个存储目录
        local deleted_count=0
        local total_count=${#data_dirs[@]}
        
        for dir_name in "${data_dirs[@]}"; do
            local full_path="${SCRIPT_DIR}/${dir_name}"
            if [ -d "$full_path" ]; then
                print_info "删除存储目录: $full_path"
                # 先尝试直接删除（不需要root权限）
                if rm -rf "$full_path" 2>/dev/null; then
                    print_success "已删除: $dir_name"
                    deleted_count=$((deleted_count + 1))
                else
                    # 如果直接删除失败，尝试使用 sudo（如果可用）
                    if command -v sudo &> /dev/null; then
                        print_info "尝试使用 sudo 删除: $dir_name"
                        if sudo rm -rf "$full_path" 2>/dev/null; then
                            print_success "已删除（使用 sudo）: $dir_name"
                            deleted_count=$((deleted_count + 1))
                        else
                            print_warning "无法删除: $dir_name（可能需要手动删除）"
                            print_info "手动删除命令: sudo rm -rf $full_path"
                        fi
                    else
                        print_warning "无法删除: $dir_name（可能需要 root 权限）"
                        print_info "请手动删除: rm -rf $full_path 或使用 root 权限删除"
                    fi
                fi
            else
                print_info "目录不存在，跳过: $dir_name"
                deleted_count=$((deleted_count + 1))
            fi
        done
        
        # 删除 ZLMediaKit 目录（特殊处理）
        if [ -d "$zlmediakit_dir" ]; then
            print_info "删除存储目录: $zlmediakit_dir"
            if rm -rf "$zlmediakit_dir" 2>/dev/null; then
                print_success "已删除: zlmediakit"
                deleted_count=$((deleted_count + 1))
            elif command -v sudo &> /dev/null; then
                print_info "尝试使用 sudo 删除: zlmediakit"
                if sudo rm -rf "$zlmediakit_dir" 2>/dev/null; then
                    print_success "已删除（使用 sudo）: zlmediakit"
                    deleted_count=$((deleted_count + 1))
                else
                    print_warning "无法删除: zlmediakit（可能需要手动删除）"
                    print_info "手动删除命令: sudo rm -rf $zlmediakit_dir"
                fi
            else
                print_warning "无法删除: zlmediakit（可能需要 root 权限）"
                print_info "请手动删除: rm -rf $zlmediakit_dir 或使用 root 权限删除"
            fi
        else
            print_info "目录不存在，跳过: zlmediakit"
            deleted_count=$((deleted_count + 1))
        fi
        total_count=$((total_count + 1))
        
        # 第六步：删除 Docker 具名卷（如果还有残留）
        print_info "检查并删除残留的 Docker 具名卷..."
        local named_volumes=(
            "emqx_data"
            "emqx_log"
        )
        
        for volume_name in "${named_volumes[@]}"; do
            if docker volume inspect "$volume_name" &> /dev/null; then
                print_info "删除 Docker 具名卷: $volume_name"
                if docker volume rm "$volume_name" 2>/dev/null; then
                    print_success "已删除 Docker 卷: $volume_name"
                else
                    print_warning "删除 Docker 卷失败: $volume_name（可能仍在使用中）"
                fi
            else
                print_info "Docker 卷不存在，跳过: $volume_name"
            fi
        done
        
        echo ""
        print_section "清理结果"
        print_info "存储目录清理: ${GREEN}$deleted_count${NC} / $total_count"
        
        if [ $deleted_count -eq $total_count ]; then
            print_success "所有存储目录已彻底删除"
        else
            print_warning "部分存储目录删除失败，请手动检查"
        fi
        
        echo ""
        print_success "清理完成"
        print_info "注意：所有 Docker 镜像已保留，不会被删除"
        print_info "如需删除镜像，请手动执行: docker image prune -a"
    else
        print_info "已取消清理操作"
    fi
}

# 更新所有中间件
update_middleware() {
    print_section "更新所有中间件"
    
    check_docker "$@"
    check_docker_compose
    configure_docker_mirror
    check_compose_file
    create_network
    
    # 创建所有中间件的存储目录（如果不存在则创建新的）
    create_all_storage_directories
    
    # 确保关键目录的权限正确
    create_postgresql_directories
    create_redis_directories
    create_nodered_directories
    create_fuxa_directories
    prepare_kafka_if_enabled
    
    prepare_srs_config
    prepare_emqx_volumes
    prepare_milvus_config
    
    # 准备 ZLMediaKit 配置文件
    prepare_zlmediakit_config

    
    # 检查并拉取缺失的镜像（如果镜像已存在则跳过拉取）
    echo ""
    check_and_pull_images
    
    cleanup_renamed_containers
    fix_nacos_startup_failure
    print_info "重启所有中间件服务..."
    local -a _skip_optional=()
    read -r -a _skip_optional <<< "$(collect_skippable_optional_services)"
    # 用 if 包裹以防止 compose_up 返回非零时触发 set -e（如 ZLMediaKit rlimit 等非致命错误）
    if compose_up_middleware "${_skip_optional[@]}"; then
        _up_rc=0
    else
        _up_rc=$?
    fi
    if middleware_service_enabled Nacos; then
        print_section "配置 Nacos 注册中心"
        fix_nacos_startup_failure
        wait_for_nacos || print_warning "Nacos 未就绪"
        ensure_nacos_admin_user || print_warning "Nacos 账号自动初始化未完成"
    fi

    if [ "${_up_rc}" -eq 0 ]; then
        print_success "所有中间件更新完成"
    else
        print_error "部分中间件更新失败（compose 退出码 ${_up_rc}），unhealthy 容器自动诊断："
        show_unhealthy_containers
    fi
    echo ""
    if middleware_service_enabled "Milvus"; then
        print_section "检查 Milvus 向量数据库"
        wait_for_milvus || print_warning "Milvus 未就绪"
    else
        print_info "当前部署形态 (${EASYAIOT_DEPLOY_PROFILE}) 跳过 Milvus"
    fi


}

# 显示帮助信息
show_help() {
    echo "EasyAIoT 中间件部署脚本"
    echo ""
    echo "使用方法:"
    echo "  ./install.sh [命令] [服务]"
    echo ""
    echo "可用命令:"
    echo "  install         - 安装并启动所有中间件（首次运行）"
    echo "  start           - 启动所有中间件"
    echo "  stop            - 停止所有中间件"
    echo "  restart         - 重启所有中间件"
    echo "  status          - 查看所有中间件状态"
    echo "  logs            - 查看所有中间件日志"
    echo "  logs [服务]     - 查看指定服务日志"
    echo "  build           - 重新构建所有镜像"
    echo "  clean           - 清理所有容器和镜像"
    echo "  update          - 更新并重启所有中间件"
    echo "  profile         - 显示当前部署规格与服务范围"
    echo "  analyze-memory  - 分析运行中容器内存占用与规格符合性（见 analyze_deploy_memory.sh）"
    echo "  fix-postgresql  - 修复 PostgreSQL 密码问题"
    echo "  help            - 显示此帮助信息"
    echo ""
    echo "环境变量:"
    echo "  EASYAIOT_DEPLOY_PROFILE   - 部署规格: mini(1,≥4GB) | standard(2,≥16GB) | full(3,≥20GB，默认)"
    echo "  EASYAIOT_ENABLE_TDENGINE  - 完整版自动为 1；mini/standard 为 0"
    echo "  EASYAIOT_ENABLE_EMQX      - standard/完整版自动为 1；mini 为 0"
    echo "  FORCE_CHMOD=true    - 对已存在的数据目录强制完整递归 chmod 修复（默认只设顶层，数据量大时慢）"
    echo "                        仅在怀疑既有目录权限损坏、容器读写报错时使用一次"
    echo "                        示例: FORCE_CHMOD=true ./install_middleware_linux.sh update"
    echo "                        修复示例: FORCE_CHMOD=true ./install_middleware_linux.sh update"
    echo ""
    echo "中间件服务列表:"
    for service in "${MIDDLEWARE_SERVICES[@]}"; do
        echo "  - $service"
    done
    echo ""
    echo "Milvus 向量数据库:"
    echo "  健康检查: http://localhost:9091/healthz"
    echo "  gRPC: localhost:19530"
    echo "  日志: ./install_middleware_linux.sh logs Milvus"
    echo ""
}

# 主函数
main() {
    local cmd="${1:-help}"

    # 在执行任何命令之前（除了 help/profile），先检查 Git
    if [ "$cmd" != "help" ] && [ "$cmd" != "--help" ] && [ "$cmd" != "-h" ] && [ "$cmd" != "profile" ]; then
        check_and_require_git
    fi

    case "$cmd" in
        install)
            select_deploy_profile_for_install
            refresh_compose_profile_args
            print_info "部署形态: $(_deploy_profile_desc) (EASYAIOT_DEPLOY_PROFILE=${EASYAIOT_DEPLOY_PROFILE})"
            install_middleware
            ;;
        start)
            ensure_deploy_profile
            refresh_compose_profile_args
            print_info "部署形态: $(_deploy_profile_desc) (EASYAIOT_DEPLOY_PROFILE=${EASYAIOT_DEPLOY_PROFILE})"
            start_middleware
            ;;
        stop)
            stop_middleware
            ;;
        restart)
            ensure_deploy_profile
            refresh_compose_profile_args
            print_info "部署形态: $(_deploy_profile_desc) (EASYAIOT_DEPLOY_PROFILE=${EASYAIOT_DEPLOY_PROFILE})"
            restart_middleware
            ;;
        status)
            ensure_deploy_profile
            refresh_compose_profile_args
            status_middleware
            ;;
        logs)
            view_logs "$2"
            ;;
        build)
            build_middleware
            ;;
        clean)
            clean_middleware
            ;;
        update)
            ensure_deploy_profile
            refresh_compose_profile_args
            print_info "部署形态: $(_deploy_profile_desc) (EASYAIOT_DEPLOY_PROFILE=${EASYAIOT_DEPLOY_PROFILE})"
            update_middleware
            ;;
        fix-postgresql)
            ensure_postgresql_password
            configure_postgresql_pg_hba
            configure_postgresql_max_connections
            ;;
        profile)
            ensure_deploy_profile
            print_deploy_profile_summary
            ;;
        analyze-memory)
            shift
            exec bash "${SCRIPT_DIR}/analyze_deploy_memory.sh" "$@"
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
fi
echo ""
print_info "主日志: $LOG_FILE"
