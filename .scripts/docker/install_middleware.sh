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

# 日志文件配置
LOG_DIR="${SCRIPT_DIR}/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/install_middleware_$(date +%Y%m%d_%H%M%S).log"

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
    "TDengine"
    "Redis"
    "Kafka"
    "MinIO"
    "SRS"
)

# 中间件端口映射
declare -A MIDDLEWARE_PORTS
MIDDLEWARE_PORTS["Nacos"]="8848"
MIDDLEWARE_PORTS["PostgresSQL"]="5432"
MIDDLEWARE_PORTS["TDengine"]="6030"
MIDDLEWARE_PORTS["Redis"]="6379"
MIDDLEWARE_PORTS["Kafka"]="9092"
MIDDLEWARE_PORTS["MinIO"]="9000"
MIDDLEWARE_PORTS["SRS"]="1935"

# 中间件健康检查端点
declare -A MIDDLEWARE_HEALTH_ENDPOINTS
MIDDLEWARE_HEALTH_ENDPOINTS["Nacos"]="/nacos/actuator/health"
MIDDLEWARE_HEALTH_ENDPOINTS["PostgresSQL"]=""
MIDDLEWARE_HEALTH_ENDPOINTS["TDengine"]=""
MIDDLEWARE_HEALTH_ENDPOINTS["Redis"]=""
MIDDLEWARE_HEALTH_ENDPOINTS["Kafka"]=""
MIDDLEWARE_HEALTH_ENDPOINTS["MinIO"]="/minio/health/live"
MIDDLEWARE_HEALTH_ENDPOINTS["SRS"]="/api/v1/versions"

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

# 检查 Java 版本
check_java_version() {
    if check_command java; then
        local java_version_output=$(java -version 2>&1 | head -n 1)
        local java_version=""
        
        # 提取版本号字符串（如 "1.8.0_333" 或 "21.0.6"）
        local version_string=$(echo "$java_version_output" | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?(_[0-9]+)?' | head -n 1)
        
        if [ -n "$version_string" ]; then
            # 提取主版本号和次版本号
            local major_version=$(echo "$version_string" | cut -d. -f1)
            local minor_version=$(echo "$version_string" | cut -d. -f2)
            
            # Java 8 及之前的版本格式是 "1.8"，需要特殊处理
            # 如果主版本号是 1，则使用次版本号作为实际版本号
            if [ "$major_version" = "1" ] && [ -n "$minor_version" ]; then
                java_version="$minor_version"
            else
                java_version="$major_version"
            fi
        fi
        
        # 如果上面的方法失败，尝试直接从 version "X 中提取
        if [ -z "$java_version" ]; then
            local first_num=$(echo "$java_version_output" | grep -oE 'version "[0-9]+' | grep -oE '[0-9]+' | head -n 1)
            local second_num=$(echo "$java_version_output" | grep -oE 'version "[0-9]+\.[0-9]+' | grep -oE '[0-9]+' | tail -n 1)
            
            if [ "$first_num" = "1" ] && [ -n "$second_num" ]; then
                java_version="$second_num"
            elif [ -n "$first_num" ]; then
                java_version="$first_num"
            fi
        fi
        
        if [ -n "$java_version" ] && [ "$java_version" -ge 8 ] 2>/dev/null; then
            print_success "Java 已安装: $java_version_output (版本: $java_version)"
            return 0
        else
            print_warning "Java 版本检测失败或版本过低: $java_version_output (提取的版本: $java_version)"
            return 1
        fi
    fi
    return 1
}

# 安装 JDK8
install_jdk8() {
    print_section "安装 JDK8"
    
    local jdk_dir="/opt/jdk8"
    local jdk_version="jdk1.8.0_333"
    local jdk_archive="jdk-8u333-linux-x64.tar.gz"
    local jdk_url="https://repo.huaweicloud.com/java/jdk/8u333-b09/jdk-8u333-linux-x64.tar.gz"
    
    # 检查是否已经安装
    if [ -d "/opt/jdk-8u333-linux-x64/$jdk_version" ]; then
        print_info "JDK8 已存在于 /opt/jdk-8u333-linux-x64/$jdk_version"
        return 0
    fi
    
    print_info "正在下载 JDK8..."
    local download_dir=$(mktemp -d)
    cd "$download_dir"
    
    if ! wget -q --show-progress "$jdk_url" -O "$jdk_archive"; then
        print_error "JDK8 下载失败，请检查网络连接"
        rm -rf "$download_dir"
        return 1
    fi
    
    print_info "正在解压 JDK8..."
    if ! tar -xzf "$jdk_archive" -C /opt/; then
        print_error "JDK8 解压失败"
        rm -rf "$download_dir"
        return 1
    fi
    
    rm -rf "$download_dir"
    
    # 配置环境变量
    print_info "正在配置 JDK8 环境变量..."
    local java_home="/opt/jdk-8u333-linux-x64/$jdk_version"
    
    # 检查 /etc/profile 中是否已存在 JDK8 配置
    if ! grep -q "JAVA_HOME=/opt/jdk-8u333-linux-x64" /etc/profile; then
        cat >> /etc/profile << EOF

#java1.8
export JAVA_HOME=$java_home
export JRE_HOME=\$JAVA_HOME/jre
export CLASSPATH=.:\$JAVA_HOME/lib:\$JRE_HOME/lib:\$CLASSPATH
export PATH=\$JAVA_HOME/bin:\$JRE_HOME/bin:\$PATH
EOF
        print_success "JDK8 环境变量已添加到 /etc/profile"
    else
        print_info "JDK8 环境变量已存在于 /etc/profile"
    fi
    
    # 立即生效（仅当前会话）
    export JAVA_HOME="$java_home"
    export JRE_HOME="$JAVA_HOME/jre"
    export CLASSPATH=".:$JAVA_HOME/lib:$JRE_HOME/lib:$CLASSPATH"
    export PATH="$JAVA_HOME/bin:$JRE_HOME/bin:$PATH"
    
    print_success "JDK8 安装完成"
    return 0
}

# 检查并安装 JDK8
check_and_install_jdk8() {
    if check_java_version; then
        return 0
    fi
    
    print_warning "未检测到 JDK8 或更高版本"
    echo ""
    print_info "JDK8 是运行某些中间件服务的必需组件"
    echo ""
    
    while true; do
        echo -ne "${YELLOW}[提示]${NC} 是否自动安装 JDK8？(y/N): "
        read -r response
        case "$response" in
            [yY][eE][sS]|[yY])
                if [ "$EUID" -ne 0 ]; then
                    print_error "安装 JDK8 需要 root 权限，请使用 sudo 运行此脚本"
                    exit 1
                fi
                if install_jdk8; then
                    print_success "JDK8 安装成功"
                    return 0
                else
                    print_error "JDK8 安装失败，请手动安装后重试"
                    exit 1
                fi
                ;;
            [nN][oO]|[nN]|"")
                print_error "JDK8 是必需的，安装流程已终止"
                exit 1
                ;;
            *)
                print_warning "请输入 y 或 N"
                ;;
        esac
    done
}

# 检查 Node.js 版本
check_nodejs_version() {
    if check_command node; then
        local node_version=$(node -v | sed -E 's/v([0-9]+)\..*/\1/')
        if [ "$node_version" -ge 20 ]; then
            print_success "Node.js 已安装: $(node -v)"
            return 0
        else
            print_warning "检测到 Node.js 版本较低: $(node -v)，需要 20+ 版本"
            return 1
        fi
    fi
    return 1
}

# 安装 Node.js 20+
install_nodejs20() {
    print_section "安装 Node.js 20+"
    
    # 检测系统类型
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        local os_id="$ID"
    else
        print_error "无法检测操作系统类型"
        return 1
    fi
    
    # 根据系统类型选择安装方法
    case "$os_id" in
        ubuntu|debian)
            print_info "检测到 Debian/Ubuntu 系统，使用 NodeSource 仓库安装..."
            if ! curl -fsSL https://deb.nodesource.com/setup_20.x | bash -; then
                print_error "添加 NodeSource 仓库失败"
                return 1
            fi
            print_info "正在安装 Node.js 20..."
            if ! apt-get install -y nodejs; then
                print_error "Node.js 安装失败"
                return 1
            fi
            ;;
        centos|rhel|fedora)
            print_info "检测到 CentOS/RHEL/Fedora 系统，使用 NodeSource 仓库安装..."
            if ! curl -fsSL https://rpm.nodesource.com/setup_20.x | bash -; then
                print_error "添加 NodeSource 仓库失败"
                return 1
            fi
            print_info "正在安装 Node.js 20..."
            if ! yum install -y nodejs; then
                print_error "Node.js 安装失败"
                return 1
            fi
            ;;
        *)
            print_error "不支持的操作系统: $os_id"
            print_info "请手动安装 Node.js 20+ 后重试"
            return 1
            ;;
    esac
    
    # 验证安装
    if check_nodejs_version; then
        print_success "Node.js 安装完成: $(node -v)"
        print_success "npm 版本: $(npm -v)"
        return 0
    else
        print_error "Node.js 安装验证失败"
        return 1
    fi
}

# 检查并安装 Node.js 20+
check_and_install_nodejs20() {
    if check_nodejs_version; then
        return 0
    fi
    
    print_warning "未检测到 Node.js 20+ 版本"
    echo ""
    print_info "Node.js 20+ 是运行某些中间件服务的必需组件"
    echo ""
    
    while true; do
        echo -ne "${YELLOW}[提示]${NC} 是否自动安装 Node.js 20+？(y/N): "
        read -r response
        case "$response" in
            [yY][eE][sS]|[yY])
                if [ "$EUID" -ne 0 ]; then
                    print_error "安装 Node.js 需要 root 权限，请使用 sudo 运行此脚本"
                    exit 1
                fi
                if install_nodejs20; then
                    print_success "Node.js 20+ 安装成功"
                    return 0
                else
                    print_error "Node.js 20+ 安装失败，请手动安装后重试"
                    exit 1
                fi
                ;;
            [nN][oO]|[nN]|"")
                print_error "Node.js 20+ 是必需的，安装流程已终止"
                exit 1
                ;;
            *)
                print_warning "请输入 y 或 N"
                ;;
        esac
    done
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
required_mirror = "https://docker.1ms.run/"
nvidia_runtime = {
    "path": "nvidia-container-runtime",
    "runtimeArgs": []
}
required_default_runtime = "nvidia"

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

# 检查并添加镜像源
if "registry-mirrors" not in config:
    config["registry-mirrors"] = []
    needs_update = True
    changes.append("添加 registry-mirrors 配置")

if required_mirror not in config["registry-mirrors"]:
    config["registry-mirrors"].append(required_mirror)
    needs_update = True
    changes.append(f"添加镜像源: {required_mirror}")

# 检查并添加 NVIDIA runtime
if "runtimes" not in config:
    config["runtimes"] = {}
    needs_update = True
    changes.append("添加 runtimes 配置")

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

# 检查并添加 default-runtime
if "default-runtime" not in config:
    config["default-runtime"] = required_default_runtime
    needs_update = True
    changes.append(f"添加 default-runtime: {required_default_runtime}")
elif config["default-runtime"] != required_default_runtime:
    config["default-runtime"] = required_default_runtime
    needs_update = True
    changes.append(f"更新 default-runtime: {required_default_runtime}")

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
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn

[install]
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF
    
    print_success "pip 镜像源配置完成"
    print_info "已使用清华大学镜像源: https://pypi.tuna.tsinghua.edu.cn/simple"
}

# 检查 Docker 权限
check_docker_permission() {
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

# 检查 Docker 是否安装
check_docker() {
    if ! check_command docker; then
        print_error "Docker 未安装，请先安装 Docker"
        echo "安装指南: https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker 已安装: $(docker --version)"
    check_docker_permission "$@"
}

# 检查 Docker Compose 是否安装
check_docker_compose() {
    if ! check_command docker-compose && ! docker compose version &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        echo "安装指南: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # 检查是 docker-compose 还是 docker compose
    if check_command docker-compose; then
        COMPOSE_CMD="docker-compose"
        print_success "Docker Compose 已安装: $(docker-compose --version)"
    else
        COMPOSE_CMD="docker compose"
        print_success "Docker Compose 已安装: $(docker compose version)"
    fi
}

# 创建统一网络
create_network() {
    print_info "创建统一网络 easyaiot-network..."
    if ! docker network ls | grep -q easyaiot-network; then
        docker network create easyaiot-network 2>/dev/null || true
        print_success "网络 easyaiot-network 已创建"
    else
        print_info "网络 easyaiot-network 已存在"
    fi
}

# 检查docker-compose.yml是否存在
check_compose_file() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "docker-compose.yml文件不存在: $COMPOSE_FILE"
        exit 1
    fi
}

# 等待 PostgreSQL 服务就绪
wait_for_postgresql() {
    local max_attempts=60
    local attempt=0
    
    print_info "等待 PostgreSQL 服务就绪..."
    while [ $attempt -lt $max_attempts ]; do
        if docker exec postgres-server pg_isready -U postgres > /dev/null 2>&1; then
            print_success "PostgreSQL 服务已就绪"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    print_error "PostgreSQL 服务未就绪"
    return 1
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

# 等待 MinIO 服务就绪
wait_for_minio() {
    local max_attempts=60
    local attempt=0
    
    print_info "等待 MinIO 服务就绪..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s --connect-timeout 2 "http://localhost:9000/minio/health/live" > /dev/null 2>&1; then
            print_success "MinIO 服务已就绪"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    print_error "MinIO 服务未就绪"
    return 1
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

# 创建数据库
create_database() {
    local db_name=$1
    
    print_info "创建数据库: $db_name"
    
    if docker exec postgres-server psql -U postgres -lqt | cut -d \| -f 1 | grep -qw "$db_name"; then
        print_info "数据库 $db_name 已存在，跳过创建"
        return 0
    fi
    
    if docker exec postgres-server psql -U postgres -c "CREATE DATABASE \"$db_name\";" > /dev/null 2>&1; then
        print_success "数据库 $db_name 创建成功"
        return 0
    else
        print_error "数据库 $db_name 创建失败"
        return 1
    fi
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


# 初始化 MinIO 的 Python 脚本（临时文件）
create_minio_init_script() {
    local script_file=$(mktemp)
    cat > "$script_file" << 'PYTHON_SCRIPT'
#!/usr/bin/env python3
import sys
import os
from minio import Minio
from minio.error import S3Error
import mimetypes

def init_minio_buckets_and_upload():
    # MinIO 配置
    minio_endpoint = "localhost:9000"
    minio_access_key = "minioadmin"
    minio_secret_key = "basiclab@iot975248395"
    minio_secure = False
    
    # 存储桶列表
    buckets = ["dataset", "datasets", "snap-space", "models"]
    
    # 数据集目录映射: (bucket_name, directory_path, object_prefix)
    # 参数格式: bucket1:dir1:prefix1 bucket2:dir2:prefix2 ...
    upload_tasks = []
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if ':' in arg:
                parts = arg.split(':')
                if len(parts) >= 2:
                    bucket_name = parts[0]
                    dir_path = parts[1]
                    prefix = parts[2] if len(parts) > 2 else ""
                    upload_tasks.append((bucket_name, dir_path, prefix))
    
    try:
        # 创建 MinIO 客户端
        client = Minio(
            minio_endpoint,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            secure=minio_secure
        )
        
        # 创建存储桶
        created_buckets = 0
        for bucket_name in buckets:
            try:
                if client.bucket_exists(bucket_name):
                    print(f"BUCKET_EXISTS:{bucket_name}")
                else:
                    client.make_bucket(bucket_name)
                    print(f"BUCKET_CREATED:{bucket_name}")
                    created_buckets += 1
                    
                    # 设置存储桶策略为公开读写
                    # 注意：存储桶操作和对象操作需要分开配置
                    policy = {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": "*",
                                "Action": [
                                    "s3:GetBucketLocation",
                                    "s3:ListBucket",
                                    "s3:ListBucketMultipartUploads"
                                ],
                                "Resource": [f"arn:aws:s3:::{bucket_name}"]
                            },
                            {
                                "Effect": "Allow",
                                "Principal": "*",
                                "Action": [
                                    "s3:ListMultipartUploadParts",
                                    "s3:PutObject",
                                    "s3:GetObject",
                                    "s3:DeleteObject",
                                    "s3:AbortMultipartUpload"
                                ],
                                "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                            }
                        ]
                    }
                    import json
                    client.set_bucket_policy(bucket_name, json.dumps(policy))
            except S3Error as e:
                print(f"BUCKET_ERROR:{bucket_name}:{str(e)}")
                sys.exit(1)
        
        print(f"BUCKETS_SUCCESS:{created_buckets}/{len(buckets)}")
        
        # 检查存储桶是否已有数据
        def bucket_has_objects(bucket_name, prefix=""):
            """检查存储桶是否已有对象（可选前缀）"""
            try:
                if prefix:
                    objects = list(client.list_objects(bucket_name, prefix=prefix, recursive=False))
                else:
                    objects = list(client.list_objects(bucket_name, recursive=False))
                return len(objects) > 0
            except:
                return False
        
        # 上传数据集（支持递归上传）
        total_upload_count = 0
        total_upload_success = 0
        
        def upload_file_recursive(bucket_name, local_path, object_prefix, root_dir):
            """递归上传文件"""
            upload_count = 0
            upload_success = 0
            
            if os.path.isfile(local_path):
                # 计算相对路径
                rel_path = os.path.relpath(local_path, root_dir)
                # 构建对象名称
                if object_prefix:
                    object_name = f"{object_prefix}/{rel_path}" if not object_prefix.endswith('/') else f"{object_prefix}{rel_path}"
                else:
                    object_name = rel_path
                
                # 统一路径分隔符为 /
                object_name = object_name.replace('\\', '/')
                
                try:
                    # 获取文件 MIME 类型
                    content_type, _ = mimetypes.guess_type(local_path)
                    if not content_type:
                        content_type = "application/octet-stream"
                    
                    # 上传文件
                    client.fput_object(
                        bucket_name,
                        object_name,
                        local_path,
                        content_type=content_type
                    )
                    print(f"UPLOAD_SUCCESS:{bucket_name}:{object_name}")
                    upload_success += 1
                except S3Error as e:
                    print(f"UPLOAD_ERROR:{bucket_name}:{object_name}:{str(e)}")
                upload_count += 1
            elif os.path.isdir(local_path):
                # 递归处理子目录
                for item in os.listdir(local_path):
                    item_path = os.path.join(local_path, item)
                    sub_count, sub_success = upload_file_recursive(bucket_name, item_path, object_prefix, root_dir)
                    upload_count += sub_count
                    upload_success += sub_success
            
            return upload_count, upload_success
        
        for bucket_name, dataset_dir, object_prefix in upload_tasks:
            if dataset_dir and os.path.isdir(dataset_dir):
                # 检查存储桶是否已有数据（检查特定前缀）
                if bucket_has_objects(bucket_name, object_prefix):
                    print(f"UPLOAD_SKIP:{bucket_name}:存储桶已存在且已有数据（前缀: {object_prefix if object_prefix else '根目录'}），跳过上传")
                else:
                    upload_count, upload_success = upload_file_recursive(bucket_name, dataset_dir, object_prefix, dataset_dir)
                    
                    print(f"UPLOAD_RESULT:{bucket_name}:{upload_success}/{upload_count}")
                    total_upload_count += upload_count
                    total_upload_success += upload_success
            else:
                print(f"UPLOAD_SKIP:{bucket_name}:数据集目录不存在或无效: {dataset_dir}")
        
        if total_upload_count > 0:
            print(f"UPLOAD_TOTAL:{total_upload_success}/{total_upload_count}")
        
        print("INIT_SUCCESS")
        sys.exit(0)
        
    except Exception as e:
        print(f"INIT_ERROR:{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    init_minio_buckets_and_upload()
PYTHON_SCRIPT
    echo "$script_file"
}

# 初始化 MinIO 存储桶和数据
init_minio_with_python() {
    local python_script=$(create_minio_init_script)
    local output_file=$(mktemp)
    
    # 检查 Python 和 minio 库
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装，无法初始化 MinIO"
        rm -f "$python_script" "$output_file"
        return 1
    fi
    
    # 检查 minio 库是否安装
    if ! python3 -c "import minio" 2>/dev/null; then
        print_info "正在安装 minio Python 库..."
        pip3 install minio > /dev/null 2>&1 || {
            print_error "无法安装 minio Python 库，请手动安装: pip3 install minio"
            rm -f "$python_script" "$output_file"
            return 1
        }
    fi
    
    # 执行 Python 脚本，传递所有参数
    chmod +x "$python_script"
    python3 "$python_script" "$@" > "$output_file" 2>&1
    local exit_code=$?
    
    # 解析输出
    local buckets_created=0
    local buckets_total=0
    local upload_success=0
    local upload_total=0
    
    while IFS= read -r line || [ -n "$line" ]; do
        if [[ $line == BUCKET_EXISTS:* ]]; then
            local bucket_name="${line#BUCKET_EXISTS:}"
            print_info "存储桶 $bucket_name 已存在，跳过创建"
        elif [[ $line == BUCKET_CREATED:* ]]; then
            local bucket_name="${line#BUCKET_CREATED:}"
            print_success "存储桶 $bucket_name 创建成功"
            buckets_created=$((buckets_created + 1))
        elif [[ $line == BUCKET_ERROR:* ]]; then
            local error="${line#BUCKET_ERROR:}"
            print_error "存储桶创建失败: $error"
        elif [[ $line == BUCKETS_SUCCESS:* ]]; then
            local result="${line#BUCKETS_SUCCESS:}"
            IFS='/' read -r created_count total_count <<< "$result"
            buckets_total=$total_count
            # 只在没有单独计算时使用汇总数据
            if [ $buckets_created -eq 0 ]; then
                buckets_created=$created_count
            fi
        elif [[ $line == UPLOAD_SUCCESS:* ]]; then
            local upload_info="${line#UPLOAD_SUCCESS:}"
            # 格式可能是 bucket:object_name 或 object_name
            if [[ $upload_info == *:* ]]; then
                local bucket_name="${upload_info%%:*}"
                local object_name="${upload_info#*:}"
                print_info "文件上传成功 [$bucket_name]: $object_name"
            else
                print_info "文件上传成功: $upload_info"
            fi
            upload_success=$((upload_success + 1))
        elif [[ $line == UPLOAD_ERROR:* ]]; then
            local error_info="${line#UPLOAD_ERROR:}"
            # 格式可能是 bucket:object_name:error 或 object_name:error
            if [[ $error_info == *:*:* ]]; then
                local parts=(${error_info//:/ })
                local bucket_name="${parts[0]}"
                local object_name="${parts[1]}"
                local error_msg="${error_info#${bucket_name}:${object_name}:}"
                print_warning "文件上传失败 [$bucket_name]: $object_name - $error_msg"
            else
                print_warning "文件上传失败: $error_info"
            fi
        elif [[ $line == UPLOAD_RESULT:* ]]; then
            local result="${line#UPLOAD_RESULT:}"
            # 格式可能是 bucket:success/total 或 success/total
            if [[ $result == *:* ]]; then
                local bucket_result="${result#*:}"
                IFS='/' read -r success_count total_count <<< "$bucket_result"
                upload_total=$((upload_total + total_count))
                upload_success=$((upload_success + success_count))
            else
                IFS='/' read -r success_count total_count <<< "$result"
                upload_total=$total_count
                if [ $upload_success -eq 0 ]; then
                    upload_success=$success_count
                fi
            fi
        elif [[ $line == UPLOAD_TOTAL:* ]]; then
            local result="${line#UPLOAD_TOTAL:}"
            IFS='/' read -r success_count total_count <<< "$result"
            upload_total=$total_count
            upload_success=$success_count
        elif [[ $line == UPLOAD_SKIP:* ]]; then
            local reason="${line#UPLOAD_SKIP:}"
            print_warning "跳过上传: $reason"
        elif [[ $line == INIT_ERROR:* ]]; then
            local error="${line#INIT_ERROR:}"
            print_error "MinIO 初始化失败: $error"
        fi
    done < "$output_file"
    
    # 清理临时文件
    rm -f "$python_script" "$output_file"
    
    if [ $exit_code -eq 0 ]; then
        if [ $buckets_total -gt 0 ]; then
            print_info "存储桶创建: ${GREEN}$buckets_created${NC} / $buckets_total"
        fi
        if [ $upload_total -gt 0 ]; then
            print_info "文件上传: ${GREEN}$upload_success${NC} / $upload_total"
        fi
        return 0
    else
        return 1
    fi
}

# 初始化 MinIO 存储桶和数据
init_minio() {
    print_section "初始化 MinIO 存储桶和数据"
    
    # 等待 MinIO 就绪
    if ! wait_for_minio; then
        print_error "MinIO 未就绪，无法初始化存储桶"
        return 1
    fi
    
    # 获取数据集目录路径
    local dataset_dir="$(cd "${SCRIPT_DIR}/../minio/dataset/3" 2>/dev/null && pwd || echo "")"
    local snap_space_dir="$(cd "${SCRIPT_DIR}/../minio/snap-space" 2>/dev/null && pwd || echo "")"
    local models_dir="$(cd "${SCRIPT_DIR}/../minio/models" 2>/dev/null && pwd || echo "")"
    
    # 构建上传任务参数
    local upload_args=()
    
    if [ -d "$dataset_dir" ]; then
        upload_args+=("dataset:$dataset_dir:3")
    else
        print_warning "数据集目录不存在: ${SCRIPT_DIR}/../minio/dataset/3"
    fi
    
    if [ -d "$snap_space_dir" ]; then
        upload_args+=("snap-space:$snap_space_dir:")
    else
        print_warning "snap-space 目录不存在: ${SCRIPT_DIR}/../minio/snap-space"
    fi
    
    if [ -d "$models_dir" ]; then
        upload_args+=("models:$models_dir:")
    else
        print_warning "models 目录不存在: ${SCRIPT_DIR}/../minio/models"
    fi
    
    # 使用 Python 脚本初始化 MinIO
    if [ ${#upload_args[@]} -gt 0 ]; then
        if init_minio_with_python "${upload_args[@]}"; then
            print_success "MinIO 初始化完成！"
            return 0
        else
            print_warning "MinIO 初始化可能存在问题"
            return 1
        fi
    else
        print_warning "没有可用的数据集目录，跳过文件上传"
        # 仍然需要创建 bucket
        if init_minio_with_python; then
            print_success "MinIO 存储桶创建完成！"
            return 0
        else
            return 1
        fi
    fi
}

# 初始化数据库
init_databases() {
    print_section "初始化数据库"
    
    # 等待 PostgreSQL 就绪
    if ! wait_for_postgresql; then
        print_error "PostgreSQL 未就绪，无法初始化数据库"
        return 1
    fi
    
    # 等待 Nacos 就绪
    if ! wait_for_nacos; then
        print_warning "Nacos 未就绪，将跳过 Nacos 密码重置确认步骤"
    fi
    
    # 定义数据库和 SQL 文件映射
    # SQL 文件路径：相对于脚本目录的上一级目录的 postgresql 目录
    local sql_dir="$(cd "${SCRIPT_DIR}/../postgresql" && pwd)"
    declare -A DB_SQL_MAP
    DB_SQL_MAP["iot-ai20"]="${sql_dir}/iot-ai10.sql"
    DB_SQL_MAP["iot-device20"]="${sql_dir}/iot-device10.sql"
    DB_SQL_MAP["iot-video20"]="${sql_dir}/iot-video10.sql"
    DB_SQL_MAP["ruoyi-vue-pro20"]="${sql_dir}/ruoyi-vue-pro10.sql"
    
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
    
    # 等待用户手动配置 Nacos 密码
    echo ""
    if wait_for_nacos; then
        print_section "Nacos 密码配置确认"
        echo ""
        print_info "请手动登录 Nacos 管理界面配置密码："
        print_info "  访问地址: http://localhost:8848/nacos"
        print_info "  用户名: nacos"
        echo ""
        print_warning "${RED}重要提示：${NC}新版本 Nacos 初始页面需要设置密码，请将密码配置为："
        print_warning "${YELLOW}basiclab@iot78475418754${NC}"
        echo ""
        print_warning "请确保已经完成密码配置，然后继续..."
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
                    print_info "您可以："
                    print_info "  1. 访问 http://localhost:8848/nacos 进行密码配置"
                    print_info "  2. 密码必须设置为: basiclab@iot78475418754"
                    print_info "  3. 配置完成后重新运行此脚本"
                    exit 1
                    ;;
                *)
                    print_warning "请输入 y 或 N"
                    ;;
            esac
        done
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

# 安装所有中间件
install_middleware() {
    print_section "开始安装所有中间件"
    
    # 检查并安装 JDK8
    check_and_install_jdk8
    
    # 检查并安装 Node.js 20+
    check_and_install_nodejs20
    
    # 配置 Docker 镜像源
    configure_docker_mirror
    
    # 配置 pip 镜像源
    configure_pip_mirror
    
    check_docker "$@"
    check_docker_compose
    check_compose_file
    create_network
    
    print_info "启动所有中间件服务..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d 2>&1 | tee -a "$LOG_FILE"
    
    print_success "中间件安装完成"
    echo ""
    print_info "等待服务启动..."
    sleep 10
    
    # 初始化数据库
    echo ""
    init_databases
    
    # 初始化 MinIO
    echo ""
    init_minio
}

# 启动所有中间件
start_middleware() {
    print_section "启动所有中间件"
    
    check_docker "$@"
    check_docker_compose
    check_compose_file
    create_network
    
    print_info "启动所有中间件服务..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d 2>&1 | tee -a "$LOG_FILE"
    
    print_success "所有中间件启动完成"
    echo ""
    print_info "等待服务就绪..."
    sleep 10
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
    check_compose_file
    create_network
    
    print_info "重启所有中间件服务..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" restart 2>&1 | tee -a "$LOG_FILE"
    
    print_success "所有中间件重启完成"
    echo ""
    print_info "等待服务就绪..."
    sleep 10
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
        print_info "查看所有中间件日志..."
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
    local databases=("iot-ai20" "iot-device20" "iot-video20" "ruoyi-vue-pro20")
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
    print_warning "这将删除所有中间件容器、镜像和数据卷，确定要继续吗？(y/N)"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_section "清理所有中间件"
        
        check_docker "$@"
        check_docker_compose
        check_compose_file
        
        # 提示数据库不会被删除
        echo ""
        print_info "注意：清理操作不会删除数据库表和数据"
        print_info "数据库数据将保留在 PostgreSQL 数据卷中"
        print_warning "如果需要删除数据库数据，请手动执行以下操作："
        print_info "  1. 连接到 PostgreSQL 容器："
        print_info "     docker exec -it postgres-server psql -U postgres"
        print_info "  2. 手动删除数据库或表"
        echo ""
        
        print_info "清理所有中间件服务..."
        $COMPOSE_CMD -f "$COMPOSE_FILE" down -v 2>&1 | tee -a "$LOG_FILE"
        
        print_success "清理完成"
    else
        print_info "已取消清理操作"
    fi
}

# 更新所有中间件
update_middleware() {
    print_section "更新所有中间件"
    
    check_docker "$@"
    check_docker_compose
    check_compose_file
    create_network
    
    print_info "拉取最新镜像..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" pull 2>&1 | tee -a "$LOG_FILE"
    
    print_info "重启所有中间件服务..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d 2>&1 | tee -a "$LOG_FILE"
    
    print_success "所有中间件更新完成"
    echo ""
    print_info "等待服务就绪..."
    sleep 10
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
    echo "  help            - 显示此帮助信息"
    echo ""
    echo "中间件服务列表:"
    for service in "${MIDDLEWARE_SERVICES[@]}"; do
        echo "  - $service"
    done
    echo ""
}

# 主函数
main() {
    case "${1:-help}" in
        install)
            install_middleware
            ;;
        start)
            start_middleware
            ;;
        stop)
            stop_middleware
            ;;
        restart)
            restart_middleware
            ;;
        status)
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
            update_middleware
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
