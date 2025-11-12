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
    "NodeRED"
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
MIDDLEWARE_PORTS["NodeRED"]="1880"

# 中间件健康检查端点
declare -A MIDDLEWARE_HEALTH_ENDPOINTS
MIDDLEWARE_HEALTH_ENDPOINTS["Nacos"]="/nacos/actuator/health"
MIDDLEWARE_HEALTH_ENDPOINTS["PostgresSQL"]=""
MIDDLEWARE_HEALTH_ENDPOINTS["TDengine"]=""
MIDDLEWARE_HEALTH_ENDPOINTS["Redis"]=""
MIDDLEWARE_HEALTH_ENDPOINTS["Kafka"]=""
MIDDLEWARE_HEALTH_ENDPOINTS["MinIO"]="/minio/health/live"
MIDDLEWARE_HEALTH_ENDPOINTS["SRS"]="/api/v1/versions"
MIDDLEWARE_HEALTH_ENDPOINTS["NodeRED"]="/"

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
    
    # 检测系统类型
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        local os_id="$ID"
    else
        print_error "无法检测操作系统类型"
        return 1
    fi
    
    # 查找已安装的 JDK8
    local java_home=""
    
    # 尝试使用 update-alternatives 查找（Ubuntu/Debian）
    if command -v update-alternatives &> /dev/null; then
        local java_path=$(update-alternatives --list java 2>/dev/null | head -n 1)
        if [ -n "$java_path" ]; then
            java_home=$(readlink -f "$java_path" | sed 's|/bin/java||')
        fi
    fi
    
    # 如果没找到，尝试常见路径
    if [ -z "$java_home" ] || [ ! -d "$java_home" ]; then
        local common_paths=(
            "/usr/lib/jvm/java-8-openjdk-amd64"
            "/usr/lib/jvm/java-8-openjdk"
            "/usr/lib/jvm/java-1.8.0-openjdk"
            "/usr/lib/jvm/java-1.8.0-openjdk-amd64"
            "/usr/lib/jvm/java-1.8.0"
            "/opt/jdk-8u333-linux-x64/jdk1.8.0_333"
            "/opt/jdk8u392-b08"
        )
        
        for dir in "${common_paths[@]}"; do
            if [ -d "$dir" ] && [ -f "$dir/bin/java" ]; then
                java_home="$dir"
                break
            fi
        done
    fi
    
    # 如果找到了已安装的 JDK8，配置环境变量后返回
    if [ -n "$java_home" ] && [ -d "$java_home" ] && [ -f "$java_home/bin/java" ]; then
        print_info "JDK8 已安装: $java_home"
        
        # 验证版本是否为 JDK 8
        local java_version=$(java -version 2>&1 | head -n 1)
        if echo "$java_version" | grep -qE "(1\.8|8\.)" || [ -n "$java_home" ]; then
            # 配置环境变量
            if ! grep -q "JAVA_HOME=$java_home" /etc/profile && ! grep -q "JAVA_HOME=/usr/lib/jvm/java-8" /etc/profile && ! grep -q "JAVA_HOME=/usr/lib/jvm/java-1.8" /etc/profile; then
                print_info "配置 JDK8 环境变量..."
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
            
            print_success "JDK8 已就绪"
            return 0
        fi
    fi
    
    # 如果没有找到，使用包管理器安装
    print_info "正在通过包管理器安装 JDK8..."
    
    case "$os_id" in
        ubuntu|debian)
            print_info "检测到 Debian/Ubuntu 系统，使用 apt 安装 OpenJDK 8..."
            
            # 更新包列表
            apt update
            
            # 安装 OpenJDK 8
            if apt install -y openjdk-8-jdk; then
                print_success "OpenJDK 8 安装成功"
            else
                print_error "OpenJDK 8 安装失败"
                return 1
            fi
            
            # 查找安装路径
            java_home="/usr/lib/jvm/java-8-openjdk-amd64"
            if [ ! -d "$java_home" ]; then
                java_home="/usr/lib/jvm/java-8-openjdk"
            fi
            
            # 如果还是没找到，尝试通过 update-alternatives 查找
            if [ ! -d "$java_home" ]; then
                local java_path=$(update-alternatives --list java 2>/dev/null | head -n 1)
                if [ -n "$java_path" ]; then
                    java_home=$(readlink -f "$java_path" | sed 's|/bin/java||')
                fi
            fi
            ;;
        centos|rhel|fedora)
            print_info "检测到 CentOS/RHEL/Fedora 系统，使用 yum 安装 OpenJDK 8..."
            
            # 安装 OpenJDK 8
            if yum install -y java-1.8.0-openjdk-devel; then
                print_success "OpenJDK 8 安装成功"
            else
                print_error "OpenJDK 8 安装失败"
                return 1
            fi
            
            # 查找安装路径
            java_home="/usr/lib/jvm/java-1.8.0-openjdk"
            if [ ! -d "$java_home" ]; then
                # 尝试查找实际的安装路径
                for dir in /usr/lib/jvm/java-1.8.0-openjdk*; do
                    if [ -d "$dir" ] && [ -f "$dir/bin/java" ]; then
                        java_home="$dir"
                        break
                    fi
                done
            fi
            ;;
        *)
            print_error "不支持的操作系统: $os_id"
            print_info "请手动安装 JDK8 后重试"
            return 1
            ;;
    esac
    
    # 验证安装
    if [ -z "$java_home" ] || [ ! -d "$java_home" ] || [ ! -f "$java_home/bin/java" ]; then
        print_error "无法找到 JDK8 安装目录"
        print_info "请手动配置 JAVA_HOME 环境变量"
        return 1
    fi
    
    print_info "检测到 JDK8 安装目录: $java_home"
    
    # 配置环境变量
    print_info "正在配置 JDK8 环境变量..."
    
    # 检查 /etc/profile 中是否已存在 JDK8 配置
    if ! grep -q "JAVA_HOME=$java_home" /etc/profile && ! grep -q "JAVA_HOME=/usr/lib/jvm/java-8" /etc/profile && ! grep -q "JAVA_HOME=/usr/lib/jvm/java-1.8" /etc/profile; then
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
    
    # 验证安装
    if java -version &> /dev/null; then
        print_success "JDK8 安装完成: $(java -version 2>&1 | head -n 1)"
    else
        print_warning "JDK8 安装完成，但版本验证失败，请手动检查"
    fi
    
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
    
    # 检查当前系统是否已配置国内 apt 源
    local current_sources_list="/etc/apt/sources.list"
    local current_sources_content=""
    local is_current_domestic=false
    
    # 读取当前系统的 apt 源配置
    if [ -f "$current_sources_list" ]; then
        current_sources_content=$(cat "$current_sources_list")
        # 检查是否已经是国内源（包含常见国内镜像关键词）
        # 匹配模式：tuna、aliyun、163、ustc、huawei、tencent 等国内镜像站
        if echo "$current_sources_content" | grep -qiE "(mirrors\.(tuna|aliyun|163|ustc|huawei|tencent)|tuna\.tsinghua|aliyun\.com|163\.com|ustc\.edu|huawei\.com|tencent\.com)"; then
            is_current_domestic=true
        fi
    fi
    
    # 如果主配置文件不是国内源，检查 sources.list.d 目录下的文件
    if [ "$is_current_domestic" = false ] && [ -d "/etc/apt/sources.list.d" ]; then
        for list_file in /etc/apt/sources.list.d/*.list; do
            if [ -f "$list_file" ]; then
                local file_content=$(cat "$list_file")
                if echo "$file_content" | grep -qiE "(mirrors\.(tuna|aliyun|163|ustc|huawei|tencent)|tuna\.tsinghua|aliyun\.com|163\.com|ustc\.edu|huawei\.com|tencent\.com)"; then
                    is_current_domestic=true
                    break
                fi
            fi
        done
    fi
    
    # 如果当前系统已经配置了国内源，直接跳过，不提示用户
    if [ "$is_current_domestic" = true ]; then
        print_info "检测到系统已配置国内 apt 源，跳过配置步骤"
        return 0
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
                if apt update > /dev/null 2>&1; then
                    print_success "apt 源配置完成并已更新缓存"
                else
                    print_warning "apt 源配置完成，但更新缓存时出现问题"
                    print_info "您可以稍后手动运行: apt update"
                fi
                
                return 0
                ;;
            [nN][oO]|[nN]|"")
                # 用户选择不替换，继续执行
                print_info "保持当前 apt 源配置，继续执行..."
                return 0
                ;;
            *)
                print_warning "请输入 y 或 N"
                ;;
        esac
    done
}

# 检查 Docker 版本是否符合要求（>=29.0.0）
check_docker_version() {
    if ! check_command docker; then
        return 1
    fi
    
    local docker_version_output=$(docker --version 2>&1)
    # 提取版本号，格式可能是 "Docker version 29.0.0, build xxxxx"
    local version_string=$(echo "$docker_version_output" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -n 1)
    
    if [ -z "$version_string" ]; then
        print_warning "无法解析 Docker 版本: $docker_version_output"
        return 1
    fi
    
    # 比较版本号
    local major=$(echo "$version_string" | cut -d. -f1)
    local minor=$(echo "$version_string" | cut -d. -f2)
    local patch=$(echo "$version_string" | cut -d. -f3)
    
    # 要求版本 >= 29.0.0
    if [ "$major" -gt 29 ] || ([ "$major" -eq 29 ] && [ "$minor" -ge 0 ]); then
        print_success "Docker 版本符合要求: $version_string"
        return 0
    else
        print_warning "Docker 版本过低: $version_string，需要 v29.0.0+"
        return 1
    fi
}

# 检查 Docker Compose 版本是否符合要求（>=2.35.0）
check_docker_compose_version() {
    local compose_version_output=""
    local version_string=""
    
    # 检查 docker-compose 独立版本
    if check_command docker-compose; then
        compose_version_output=$(docker-compose --version 2>&1)
        version_string=$(echo "$compose_version_output" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -n 1)
    # 检查 docker compose plugin 版本
    elif docker compose version &> /dev/null; then
        compose_version_output=$(docker compose version 2>&1)
        version_string=$(echo "$compose_version_output" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -n 1)
    else
        return 1
    fi
    
    if [ -z "$version_string" ]; then
        print_warning "无法解析 Docker Compose 版本: $compose_version_output"
        return 1
    fi
    
    # 比较版本号
    local major=$(echo "$version_string" | cut -d. -f1)
    local minor=$(echo "$version_string" | cut -d. -f2)
    local patch=$(echo "$version_string" | cut -d. -f3)
    
    # 要求版本 >= 2.35.0
    if [ "$major" -gt 2 ] || ([ "$major" -eq 2 ] && [ "$minor" -gt 35 ]) || ([ "$major" -eq 2 ] && [ "$minor" -eq 35 ] && [ "$patch" -ge 0 ]); then
        print_success "Docker Compose 版本符合要求: $version_string"
        return 0
    else
        print_warning "Docker Compose 版本过低: $version_string，需要 v2.35.0+"
        return 1
    fi
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

# 安装 Docker
install_docker() {
    print_section "安装 Docker"
    
    if [ "$EUID" -ne 0 ]; then
        print_error "安装 Docker 需要 root 权限，请使用 sudo 运行此脚本"
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
    
    # 根据系统类型安装 Docker
    case "$os_id" in
        ubuntu|debian)
            print_info "检测到 Debian/Ubuntu 系统，开始安装 Docker..."
            
            # 卸载旧版本
            apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
            
            # 安装依赖
            apt-get update
            apt-get install -y \
                ca-certificates \
                curl \
                gnupg \
                lsb-release
            
            # 添加 Docker 官方 GPG 密钥
            install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/$os_id/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            chmod a+r /etc/apt/keyrings/docker.gpg
            
            # 设置仓库
            echo \
              "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$os_id \
              $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            # 安装 Docker Engine
            apt-get update
            apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            
            ;;
        centos|rhel|fedora)
            print_info "检测到 CentOS/RHEL/Fedora 系统，开始安装 Docker..."
            
            # 卸载旧版本
            yum remove -y docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine 2>/dev/null || true
            
            # 安装依赖
            yum install -y yum-utils
            
            # 添加 Docker 仓库
            yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            
            # 安装 Docker Engine
            yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            
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

# 从 GitHub 下载 Docker Compose
download_docker_compose_from_github() {
    print_section "从 GitHub 下载 Docker Compose v2.35.1"
    
    if [ "$EUID" -ne 0 ]; then
        print_error "安装 Docker Compose 需要 root 权限，请使用 sudo 运行此脚本"
        return 1
    fi
    
    local compose_version="v2.35.1"
    local compose_path="/usr/bin/docker-compose"
    
    # 检测系统架构
    local arch=$(uname -m)
    local compose_arch=""
    
    case "$arch" in
        x86_64)
            compose_arch="x86_64"
            ;;
        aarch64|arm64)
            compose_arch="aarch64"
            ;;
        armv7l|armv6l)
            compose_arch="armv7"
            ;;
        *)
            print_error "不支持的系统架构: $arch"
            return 1
            ;;
    esac
    
    local compose_url="https://github.com/docker/compose/releases/download/${compose_version}/docker-compose-linux-${compose_arch}"
    
    print_info "正在从 GitHub 下载 Docker Compose..."
    print_info "版本: $compose_version"
    print_info "架构: $compose_arch"
    print_info "URL: $compose_url"
    
    # 下载文件到临时位置
    local temp_file=$(mktemp)
    
    if ! curl -L -f "$compose_url" -o "$temp_file" 2>/dev/null; then
        print_error "下载 Docker Compose 失败"
        rm -f "$temp_file"
        return 1
    fi
    
    # 检查下载的文件是否有效（应该是一个可执行文件）
    if [ ! -s "$temp_file" ]; then
        print_error "下载的文件为空"
        rm -f "$temp_file"
        return 1
    fi
    
    # 如果目标文件已存在，先备份
    if [ -f "$compose_path" ]; then
        print_info "检测到已存在的 docker-compose，创建备份..."
        mv "$compose_path" "${compose_path}.bak.$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
    fi
    
    # 移动文件到目标位置并设置权限
    if mv "$temp_file" "$compose_path"; then
        chmod +x "$compose_path"
        print_success "Docker Compose 已下载并安装到: $compose_path"
        
        # 验证安装
        if check_command docker-compose; then
            local installed_version=$(docker-compose --version 2>&1)
            print_success "Docker Compose 安装成功: $installed_version"
            return 0
        else
            print_warning "Docker Compose 已安装但验证失败"
            return 1
        fi
    else
        print_error "移动文件到 $compose_path 失败"
        rm -f "$temp_file"
        return 1
    fi
}

# 安装 Docker Compose
install_docker_compose() {
    print_section "安装 Docker Compose"
    
    if [ "$EUID" -ne 0 ]; then
        print_error "安装 Docker Compose 需要 root 权限，请使用 sudo 运行此脚本"
        return 1
    fi
    
    # 优先从 GitHub 下载指定版本
    print_info "从 GitHub 下载 Docker Compose v2.35.1..."
    if download_docker_compose_from_github; then
        return 0
    fi
    
    # 如果下载失败，尝试使用包管理器安装
    print_warning "从 GitHub 下载失败，尝试使用包管理器安装..."
    
    # 检测系统类型
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        local os_id="$ID"
    else
        print_error "无法检测操作系统类型"
        return 1
    fi
    
    # 根据系统类型安装 Docker Compose
    case "$os_id" in
        ubuntu|debian)
            print_info "检测到 Debian/Ubuntu 系统，安装 Docker Compose Plugin..."
            apt-get update
            apt-get install -y docker-compose-plugin
            ;;
        centos|rhel|fedora)
            print_info "检测到 CentOS/RHEL/Fedora 系统，安装 Docker Compose Plugin..."
            yum install -y docker-compose-plugin
            ;;
        *)
            print_error "不支持的操作系统: $os_id"
            return 1
            ;;
    esac
    
    # 验证安装
    if check_command docker-compose || docker compose version &> /dev/null; then
        if check_command docker-compose; then
            print_success "Docker Compose 安装完成: $(docker-compose --version)"
        else
            print_success "Docker Compose Plugin 安装完成: $(docker compose version)"
        fi
        return 0
    else
        print_error "Docker Compose 安装验证失败"
        return 1
    fi
}

# 检查并安装 Docker
check_and_install_docker() {
    if check_command docker; then
        # 检查版本是否符合要求
        if check_docker_version; then
            check_docker_permission "$@"
            return 0
        else
            # 版本不符合要求，提示升级
            print_warning "Docker 版本不符合要求（需要 v29.0.0+）"
            echo ""
            print_info "当前版本: $(docker --version)"
            print_info "要求版本: v29.0.0 或更高"
            echo ""
            
            while true; do
                echo -ne "${YELLOW}[提示]${NC} 是否升级 Docker 到最新版本？(y/N): "
                read -r response
                case "$response" in
                    [yY][eE][sS]|[yY])
                        if [ "$EUID" -ne 0 ]; then
                            print_error "升级 Docker 需要 root 权限，请使用 sudo 运行此脚本"
                            exit 1
                        fi
                        print_info "正在升级 Docker..."
                        # 卸载旧版本并安装新版本
                        if install_docker; then
                            if check_docker_version; then
                                print_success "Docker 升级成功"
                                check_docker_permission "$@"
                                return 0
                            else
                                print_error "Docker 升级后版本仍不符合要求"
                                exit 1
                            fi
                        else
                            print_error "Docker 升级失败，请手动升级后重试"
                            exit 1
                        fi
                        ;;
                    [nN][oO]|[nN]|"")
                        print_error "Docker 版本不符合要求，安装流程已终止"
                        print_info "请手动升级 Docker 到 v29.0.0+ 后重试"
                        print_info "安装指南: https://docs.docker.com/get-docker/"
                        exit 1
                        ;;
                    *)
                        print_warning "请输入 y 或 N"
                        ;;
                esac
            done
        fi
    fi
    
    print_warning "未检测到 Docker"
    echo ""
    print_info "Docker 是运行中间件服务的必需组件"
    print_info "要求版本: v29.0.0 或更高"
    echo ""
    
    while true; do
        echo -ne "${YELLOW}[提示]${NC} 是否自动安装 Docker？(y/N): "
        read -r response
        case "$response" in
            [yY][eE][sS]|[yY])
                if install_docker; then
                    if check_docker_version; then
                        print_success "Docker 安装成功"
                        check_docker_permission "$@"
                        return 0
                    else
                        print_error "Docker 安装后版本不符合要求"
                        exit 1
                    fi
                else
                    print_error "Docker 安装失败，请手动安装后重试"
                    exit 1
                fi
                ;;
            [nN][oO]|[nN]|"")
                print_error "Docker 是必需的，安装流程已终止"
                print_info "安装指南: https://docs.docker.com/get-docker/"
                exit 1
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
                echo -ne "${YELLOW}[提示]${NC} 是否升级 Docker Compose 到 v2.35.1？(y/N): "
                read -r response
                case "$response" in
                    [yY][eE][sS]|[yY])
                        if [ "$EUID" -ne 0 ]; then
                            print_error "升级 Docker Compose 需要 root 权限，请使用 sudo 运行此脚本"
                            exit 1
                        fi
                        print_info "正在升级 Docker Compose..."
                        # 从 GitHub 下载指定版本
                        if download_docker_compose_from_github; then
                            if check_docker_compose_version; then
                                COMPOSE_CMD="docker-compose"
                                print_success "Docker Compose 升级成功"
                                return 0
                            else
                                print_error "Docker Compose 升级后版本仍不符合要求"
                                exit 1
                            fi
                        else
                            print_error "Docker Compose 升级失败，请手动升级后重试"
                            exit 1
                        fi
                        ;;
                    [nN][oO]|[nN]|"")
                        print_error "Docker Compose 版本不符合要求，安装流程已终止"
                        print_info "请手动升级 Docker Compose 到 v2.35.0+ 后重试"
                        print_info "下载地址: https://github.com/docker/compose/releases/tag/v2.35.1"
                        exit 1
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
                        print_error "Docker Compose 安装后版本不符合要求"
                        exit 1
                    fi
                else
                    print_error "Docker Compose 安装失败，请手动安装后重试"
                    exit 1
                fi
                ;;
            [nN][oO]|[nN]|"")
                print_error "Docker Compose 是必需的，安装流程已终止"
                print_info "下载地址: https://github.com/docker/compose/releases/tag/v2.35.1"
                exit 1
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
    if ! docker network ls | grep -q easyaiot-network; then
        docker network create easyaiot-network 2>/dev/null || true
        print_success "网络 easyaiot-network 已创建"
    else
        print_info "网络 easyaiot-network 已存在"
    fi
}

# 创建并设置 NodeRED 数据目录权限
create_nodered_directories() {
    local nodered_data_dir="${SCRIPT_DIR}/nodered_data/data"
    
    print_info "创建 NodeRED 数据目录并设置权限..."
    
    # 创建目录
    mkdir -p "$nodered_data_dir"
    
    # 设置目录所有者为 UID 1000 (Node-RED 容器默认用户)
    # 如果当前用户有权限，则设置；否则只创建目录
    if [ "$EUID" -eq 0 ]; then
        chown -R 1000:1000 "$nodered_data_dir"
        chmod -R 755 "$nodered_data_dir"
        print_success "NodeRED 数据目录权限已设置 (UID 1000:1000)"
    else
        # 非 root 用户尝试使用 sudo（如果可用）
        if command -v sudo &> /dev/null; then
            sudo chown -R 1000:1000 "$nodered_data_dir" 2>/dev/null && \
            sudo chmod -R 755 "$nodered_data_dir" 2>/dev/null && \
            print_success "NodeRED 数据目录权限已设置 (UID 1000:1000)" || \
            print_warning "无法设置 NodeRED 目录权限，可能需要手动设置: sudo chown -R 1000:1000 $nodered_data_dir"
        else
            print_warning "无法设置 NodeRED 目录权限，请手动执行: sudo chown -R 1000:1000 $nodered_data_dir"
        fi
    fi
}

# 准备 SRS 配置文件
prepare_srs_config() {
    local srs_config_source="${SCRIPT_DIR}/../srs/conf"
    local srs_config_target="${SCRIPT_DIR}/srs_data/conf"
    
    print_info "准备 SRS 配置文件..."
    
    # 创建目标目录
    mkdir -p "$srs_config_target"
    
    # 检查源配置文件是否存在
    if [ -d "$srs_config_source" ] && [ -f "$srs_config_source/docker.conf" ]; then
        # 如果源配置文件存在，复制到目标目录
        if cp -f "$srs_config_source/docker.conf" "$srs_config_target/docker.conf" 2>/dev/null; then
            print_success "SRS 配置文件已复制: $srs_config_source/docker.conf -> $srs_config_target/docker.conf"
        else
            print_warning "无法复制 SRS 配置文件，可能需要手动复制"
        fi
    else
        # 如果源配置文件不存在，检查目标目录是否已有配置文件
        if [ ! -f "$srs_config_target/docker.conf" ]; then
            print_warning "SRS 配置文件不存在: $srs_config_source/docker.conf"
            print_info "将在容器启动后尝试从容器内复制默认配置"
        else
            print_info "SRS 配置文件已存在: $srs_config_target/docker.conf"
        fi
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
    local init_result=0
    if [ ${#upload_args[@]} -gt 0 ]; then
        if init_minio_with_python "${upload_args[@]}"; then
            print_success "MinIO 初始化完成！"
            init_result=0
        else
            print_warning "MinIO 初始化可能存在问题"
            init_result=1
        fi
    else
        print_warning "没有可用的数据集目录，跳过文件上传"
        # 仍然需要创建 bucket
        if init_minio_with_python; then
            print_success "MinIO 存储桶创建完成！"
            init_result=0
        else
            init_result=1
        fi
    fi
    
    # 如果初始化成功，提示用户登录 MinIO 管理平台
    if [ $init_result -eq 0 ]; then
        echo ""
        print_section "MinIO 管理平台登录提示"
        echo ""
        print_warning "重要提示：为了确保图像数据能够正常显示，请登录一次 MinIO 管理平台"
        print_info "  访问地址: http://localhost:9001"
        print_info "  用户名: minioadmin"
        print_info "  密码: basiclab@iot975248395"
        echo ""
        print_info "登录后，系统会自动完成必要的初始化配置，图像数据才能正常显示"
        echo ""
        
        while true; do
            echo -ne "${YELLOW}[提示]${NC} 是否已经登录过 MinIO 管理平台？(y/N): "
            read -r response
            case "$response" in
                [yY][eE][sS]|[yY])
                    print_success "确认已登录 MinIO 管理平台，继续执行..."
                    break
                    ;;
                [nN][oO]|[nN]|"")
                    print_warning "建议稍后登录 MinIO 管理平台以确保图像数据正常显示"
                    print_info "您可以稍后访问: http://localhost:9001"
                    break
                    ;;
                *)
                    print_warning "请输入 y 或 N"
                    ;;
            esac
        done
        echo ""
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
    
    # 配置 apt 国内源（在安装依赖之前）
    configure_apt_mirror
    
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
    create_nodered_directories
    prepare_srs_config
    
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
    create_nodered_directories
    prepare_srs_config
    
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
    create_nodered_directories
    prepare_srs_config
    
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
    create_nodered_directories
    prepare_srs_config
    
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
