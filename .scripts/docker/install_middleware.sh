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
    "EMQX"
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
MIDDLEWARE_PORTS["EMQX"]="1883"

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
MIDDLEWARE_HEALTH_ENDPOINTS["EMQX"]="/api/v5/status"

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
            apt update -qq > /dev/null 2>&1
            
            # 安装 OpenJDK 8
            if apt install -qq -y openjdk-8-jdk > /dev/null 2>&1; then
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
            if ! apt-get install -qq -y nodejs > /dev/null 2>&1; then
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

# 检查 Maven 是否已安装（不检查版本）
check_maven_installed() {
    if check_command mvn; then
        local maven_version_output=$(mvn -version 2>&1 | head -n 1)
        print_success "Maven 已安装: $maven_version_output"
        return 0
    fi
    return 1
}

# 安装 Maven 3.6.3
install_maven363() {
    print_section "安装 Maven 3.6.3"
    
    if [ "$EUID" -ne 0 ]; then
        print_error "安装 Maven 需要 root 权限，请使用 sudo 运行此脚本"
        return 1
    fi
    
    local maven_version="3.6.3"
    local maven_dir="/opt/apache-maven-${maven_version}"
    local maven_archive="/tmp/apache-maven-${maven_version}-bin.tar.gz"
    local maven_url="https://archive.apache.org/dist/maven/maven-3/${maven_version}/binaries/apache-maven-${maven_version}-bin.tar.gz"
    
    # 检查是否已安装
    if [ -d "$maven_dir" ] && [ -f "$maven_dir/bin/mvn" ]; then
        print_info "Maven 3.6.3 已存在于: $maven_dir"
        
        # 配置 Maven settings.xml（如果不存在或需要更新）
        print_info "检查并配置 Maven settings.xml..."
        configure_maven_settings "$maven_dir"
        
        # 配置环境变量（处理旧配置）
        configure_maven_env "$maven_dir"
        
        # 直接在当前 shell 中设置环境变量（不依赖 source）
        export MAVEN_HOME="$maven_dir"
        export PATH="$MAVEN_HOME/bin:$PATH"
        
        # 验证安装
        if check_maven_installed; then
            print_success "Maven 3.6.3 已就绪"
            return 0
        fi
    fi
    
    print_info "正在下载 Maven 3.6.3..."
    print_info "URL: $maven_url"
    
    # 使用 wget 下载 Maven
    if ! wget -O "$maven_archive" "$maven_url" 2>/dev/null; then
        print_error "下载 Maven 失败"
        return 1
    fi
    
    # 检查下载的文件是否有效
    if [ ! -s "$maven_archive" ]; then
        print_error "下载的文件为空"
        rm -f "$maven_archive"
        return 1
    fi
    
    # 创建安装目录
    mkdir -p /opt
    
    # 如果目录已存在，先备份
    if [ -d "$maven_dir" ]; then
        print_info "检测到已存在的 Maven 目录，创建备份..."
        mv "$maven_dir" "${maven_dir}.bak.$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
    fi
    
    # 解压 Maven
    print_info "正在解压 Maven..."
    if ! tar -xzf "$maven_archive" -C /opt 2>/dev/null; then
        print_error "解压 Maven 失败"
        rm -f "$maven_archive"
        return 1
    fi
    
    # 验证解压结果
    if [ ! -d "$maven_dir" ] || [ ! -f "$maven_dir/bin/mvn" ]; then
        print_error "Maven 解压后验证失败"
        rm -f "$maven_archive"
        return 1
    fi
    
    # 清理下载文件
    rm -f "$maven_archive"
    
    # 配置 Maven settings.xml
    print_info "正在配置 Maven settings.xml..."
    configure_maven_settings "$maven_dir"
    
    # 配置环境变量（处理旧配置）
    print_info "正在配置 Maven 环境变量..."
    configure_maven_env "$maven_dir"
    
    # 直接在当前 shell 中设置环境变量（不依赖 source）
    print_info "设置当前 shell 环境变量..."
    export MAVEN_HOME="$maven_dir"
    export PATH="$MAVEN_HOME/bin:$PATH"
    
    # 验证安装
    if check_maven_installed; then
        print_success "Maven 3.6.3 安装完成: $(mvn -version 2>&1 | head -n 1)"
        print_info "注意：环境变量已写入 /etc/profile，新开终端会自动生效"
        print_info "当前 shell 中已设置环境变量，mvn 命令现在可用"
        return 0
    else
        print_warning "Maven 安装完成，但验证失败，请手动检查"
        print_info "请尝试手动执行: export MAVEN_HOME=$maven_dir && export PATH=\$MAVEN_HOME/bin:\$PATH"
        return 1
    fi
}

# 配置 Maven settings.xml
configure_maven_settings() {
    local maven_dir="$1"
    local repo_dir="${maven_dir}/repo"
    local settings_file="${maven_dir}/conf/settings.xml"
    
    # 创建 repo 目录
    print_info "创建 Maven 本地仓库目录: $repo_dir"
    mkdir -p "$repo_dir"
    if [ $? -eq 0 ]; then
        print_success "Maven 本地仓库目录已创建: $repo_dir"
    else
        print_error "创建 Maven 本地仓库目录失败: $repo_dir"
        return 1
    fi
    
    # 创建 settings.xml 文件
    print_info "配置 Maven settings.xml: $settings_file"
    cat > "$settings_file" << 'SETTINGS_XML'
<?xml version="1.0" encoding="UTF-8"?>
<!--

Licensed to the Apache Software Foundation (ASF) under one

or more contributor license agreements.  See the NOTICE file

distributed with this work for additional information

regarding copyright ownership.  The ASF licenses this file

to you under the Apache License, Version 2.0 (the

"License"); you may not use this file except in compliance

with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,

software distributed under the License is distributed on an

"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY

KIND, either express or implied.  See the License for the

specific language governing permissions and limitations

under the License.

-->

<!--

 | This is the configuration file for Maven. It can be specified at two levels:

 |

 |  1. User Level. This settings.xml file provides configuration for a single user,

 |                 and is normally provided in ${user.home}/.m2/settings.xml.

 |

 |                 NOTE: This location can be overridden with the CLI option:

 |

 |                 -s /path/to/user/settings.xml

 |

 |  2. Global Level. This settings.xml file provides configuration for all Maven

 |                 users on a machine (assuming they're all using the same Maven

 |                 installation). It's normally provided in

 |                 ${maven.conf}/settings.xml.

 |

 |                 NOTE: This location can be overridden with the CLI option:

 |

 |                 -gs /path/to/global/settings.xml

 |

 | The sections in this sample file are intended to give you a running start at

 | getting the most out of your Maven installation. Where appropriate, the default

 | values (values used when the setting is not specified) are provided.

 |

 |-->

<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"

          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"

          xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0 http://maven.apache.org/xsd/settings-1.0.0.xsd">

  <!-- localRepository

   | The path to the local repository maven will use to store artifacts.

   |

   | Default: ${user.home}/.m2/repository

  <localRepository>/path/to/local/repo</localRepository>

  -->

  <localRepository>MAVEN_REPO_DIR</localRepository>

  <!-- interactiveMode

   | This will determine whether maven prompts you when it needs input. If set to false,

   | maven will use a sensible default value, perhaps based on some other setting, for

   | the parameter in question.

   |

   | Default: true

  <interactiveMode>true</interactiveMode>

  -->

  <!-- offline

   | Determines whether maven should attempt to connect to the network when executing a build.

   | This will have an effect on artifact downloads, artifact deployment, and others.

   |

   | Default: false

  <offline>false</offline>

  -->

  <!-- pluginGroups

   | This is a list of additional group identifiers that will be searched when resolving plugins by their prefix, i.e.

   | when invoking a command line like "mvn prefix:goal". Maven will automatically add the group identifiers

   | "org.apache.maven.plugins" and "org.codehaus.mojo" if these are not already contained in the list.

   |-->

  <pluginGroups>

    <!-- pluginGroup

     | Specifies a further group identifier to use for plugin lookup.

    <pluginGroup>com.your.plugins</pluginGroup>

    -->

  </pluginGroups>

  <!-- proxies

   | This is a list of proxies which can be used on this machine to connect to the network.

   | Unless otherwise specified (by system property or command-line switch), the first proxy

   | specification in this list marked as active will be used.

   |-->

  <proxies>

    <!-- proxy

     | Specification for one proxy, to be used in connecting to the network.

     |

    <proxy>

      <id>optional</id>

      <active>true</active>

      <protocol>http</protocol>

      <username>proxyuser</username>

      <password>proxypass</password>

      <host>proxy.host.net</host>

      <port>80</port>

      <nonProxyHosts>local.net|some.host.com</nonProxyHosts>

    </proxy>

    -->

  </proxies>

  <!-- servers

   | This is a list of authentication profiles, keyed by the server-id used within the system.

   | Authentication profiles can be used whenever maven must make a connection to a remote server.

   |-->

  <servers>

    <!-- server

     | Specifies the authentication information to use when connecting to a particular server, identified by

     | a unique name within the system (referred to by the 'id' attribute below).

     |

     | NOTE: You should either specify username/password OR privateKey/passphrase, since these pairings are

     |       used together.

     |

    <server>

      <id>deploymentRepo</id>

      <username>repouser</username>

      <password>repopwd</password>

    </server>

    -->

    <!-- Another sample, using keys to authenticate.

    <server>

      <id>siteServer</id>

      <privateKey>/path/to/private/key</privateKey>

      <passphrase>optional; leave empty if not used.</passphrase>

    </server>

    -->

  </servers>

  <!-- mirrors

   | This is a list of mirrors to be used in downloading artifacts from remote repositories.

   |

   | It works like this: a POM may declare a repository to use in resolving certain artifacts.

   | However, this repository may have problems with heavy traffic at times, so people have mirrored

   | it to several places.

   |

   | That repository definition will have a unique id, so we can create a mirror reference for that

   | repository, to be used as an alternate download site. The mirror site will be the preferred

   | server for that repository.

   |-->

  <mirrors>

    <!-- mirror

     | Specifies a repository mirror site to use instead of a given repository. The repository that

     | this mirror serves has an ID that matches the mirrorOf element of this mirror. IDs are used

     | for inheritance and direct lookup purposes, and must be unique across the set of mirrors.

     |

    <mirror>

      <id>mirrorId</id>

      <mirrorOf>repositoryId</mirrorOf>

      <name>Human Readable Name for this Mirror.</name>

      <url>http://my.repository.com/repo/path</url>

    </mirror>

    -->

    <mirror>

	<id>nexus-aliyun</id>

	<mirrorOf>central</mirrorOf>

	<name>Nexus aliyun</name>

	<url>http://maven.aliyun.com/nexus/content/groups/public/</url>

    </mirror>

  </mirrors>

  <!-- profiles

   | This is a list of profiles which can be activated in a variety of ways, and which can modify

   | the build process. Profiles provided in the settings.xml are intended to provide local machine-

   | specific paths and repository locations which allow the build to work in the local environment.

   |

   | For example, if you have an integration testing plugin - like cactus - that needs to know where

   | your Tomcat instance is installed, you can provide a variable here such that the variable is

   | dereferenced during the build process to configure the cactus plugin.

   |

   | As noted above, profiles can be activated in a variety of ways. One way - the activeProfiles

   | section of this document (settings.xml) - will be discussed later. Another way essentially

   | relies on the detection of a system property, either matching a particular value for the property,

   | or merely testing its existence. Profiles can also be activated by JDK version prefix, where a

   | value of '1.4' might activate a profile when the build is executed on a JDK version of '1.4.2_07'.

   | Finally, the list of active profiles can be specified directly from the command line.

   |

   | NOTE: For profiles defined in the settings.xml, you are restricted to specifying only artifact

   |       repositories, plugin repositories, and free-form properties to be used as configuration

   |       variables for plugins in the POM.

   |

   |-->

  <profiles>

    <!-- profile

     | Specifies a set of introductions to the build process, to be activated using one or more of the

     | mechanisms described above. For inheritance purposes, and to activate profiles via <activatedProfiles/>

     | or the command line, profiles have to have an ID that is unique.

     |

     | An encouraged best practice for profile identification is to use a consistent naming convention

     | for profiles, such as 'env-dev', 'env-test', 'env-production', 'user-jdcasey', 'user-brett', etc.

     | This will make it more intuitive to understand what the set of introduced profiles is attempting

     | to accomplish, particularly when you only have a list of profile id's for debug.

     |

     | This profile example uses the JDK version to trigger activation, and provides a JDK-specific repo.

    <profile>

      <id>jdk-1.4</id>

      <activation>

        <jdk>1.4</jdk>

      </activation>

      <repositories>

        <repository>

          <id>jdk14</id>

          <name>Repository for JDK 1.4 builds</name>

          <url>http://www.myhost.com/maven/jdk14</url>

          <layout>default</layout>

          <snapshotPolicy>always</snapshotPolicy>

        </repository>

      </repositories>

    </profile>

    -->

    <!--

     | Here is another profile, activated by the system property 'target-env' with a value of 'dev',

     | which provides a specific path to the Tomcat instance. To use this, your plugin configuration

     | might hypothetically look like:

     |

     | ...

     | <plugin>

     |   <groupId>org.myco.myplugins</groupId>

     |   <artifactId>myplugin</artifactId>

     |

     |   <configuration>

     |     <tomcatLocation>${tomcatPath}</tomcatLocation>

     |   </configuration>

     | </plugin>

     | ...

     |

     | NOTE: If you just wanted to inject this configuration whenever someone set 'target-env' to

     |       anything, you could just leave off the <value/> inside the activation-property.

     |

    <profile>

      <id>env-dev</id>

      <activation>

        <property>

          <name>target-env</name>

          <value>dev</value>

        </property>

      </activation>

      <properties>

        <tomcatPath>/path/to/tomcat/instance</tomcatPath>

      </properties>

    </profile>

    -->

  </profiles>

  <!-- activeProfiles

   | List of profiles that are active for all builds.

   |

  <activeProfiles>

    <activeProfile>alwaysActiveProfile</activeProfile>

    <activeProfile>anotherAlwaysActiveProfile</activeProfile>

  </activeProfiles>

  -->

</settings>
SETTINGS_XML
    
    # 替换 localRepository 路径
    sed -i "s|MAVEN_REPO_DIR|${repo_dir}|g" "$settings_file"
    
    if [ -f "$settings_file" ]; then
        print_success "Maven settings.xml 配置完成: $settings_file"
        print_info "本地仓库路径: $repo_dir"
        return 0
    else
        print_error "创建 Maven settings.xml 失败: $settings_file"
        return 1
    fi
}

# 配置 Maven 环境变量（处理旧配置）
configure_maven_env() {
    local maven_dir="$1"
    local profile_file="/etc/profile"
    local temp_file=$(mktemp)
    
    # 检查是否存在旧的 Maven 配置（只检查未注释的 export 语句）
    local has_old_maven=false
    if grep -qE "^[[:space:]]*export[[:space:]]+MAVEN_HOME|^[[:space:]]*export[[:space:]]+.*MAVEN|^[[:space:]]*MAVEN_HOME=" "$profile_file" 2>/dev/null; then
        has_old_maven=true
        print_info "检测到 /etc/profile 中存在旧的 Maven 配置，将注释掉旧配置..."
    fi
    
    # 读取现有配置并处理
    if [ -f "$profile_file" ]; then
        # 处理每一行：如果包含 MAVEN_HOME 的 export 语句且未被注释，则注释掉
        while IFS= read -r line || [ -n "$line" ]; do
            # 如果行包含 MAVEN_HOME 的 export 或赋值语句且未被注释，则注释掉
            if echo "$line" | grep -qE "^[[:space:]]*export[[:space:]]+MAVEN_HOME|^[[:space:]]*export[[:space:]]+.*MAVEN|^[[:space:]]*MAVEN_HOME=" && ! echo "$line" | grep -qE "^[[:space:]]*#"; then
                echo "# $line # Commented by install_middleware.sh" >> "$temp_file"
            else
                echo "$line" >> "$temp_file"
            fi
        done < "$profile_file"
        
        # 追加新的 Maven 配置
        cat >> "$temp_file" << EOF

# Maven 3.6.3 (configured by install_middleware.sh)
export MAVEN_HOME=$maven_dir
export PATH=\$MAVEN_HOME/bin:\$PATH
EOF
        
        # 替换原文件
        mv "$temp_file" "$profile_file"
        
        if [ "$has_old_maven" = true ]; then
            print_success "已注释旧 Maven 配置并添加新配置"
        else
            print_success "Maven 环境变量已添加到 /etc/profile"
        fi
    else
        print_error "/etc/profile 文件不存在"
        rm -f "$temp_file"
        return 1
    fi
}

# 检查并安装 Maven 3.6.3
check_and_install_maven363() {
    if check_maven_installed; then
        return 0
    fi
    
    print_warning "未检测到 Maven"
    echo ""
    print_info "Maven 是运行某些中间件服务的必需组件，将安装 Maven 3.6.3"
    echo ""
    
    while true; do
        echo -ne "${YELLOW}[提示]${NC} 是否自动安装 Maven 3.6.3？(y/N): "
        read -r response
        case "$response" in
            [yY][eE][sS]|[yY])
                if [ "$EUID" -ne 0 ]; then
                    print_error "安装 Maven 需要 root 权限，请使用 sudo 运行此脚本"
                    exit 1
                fi
                if install_maven363; then
                    # 确保环境变量在当前 shell 中已设置
                    local maven_dir="/opt/apache-maven-3.6.3"
                    if [ -d "$maven_dir" ] && [ -f "$maven_dir/bin/mvn" ]; then
                        export MAVEN_HOME="$maven_dir"
                        export PATH="$MAVEN_HOME/bin:$PATH"
                    fi
                    
                    # 再次验证 Maven 是否可用
                    if check_maven_installed; then
                        print_success "Maven 3.6.3 安装成功，环境变量已设置"
                        return 0
                    else
                        print_warning "Maven 安装成功，但环境变量可能未生效"
                        print_info "请手动执行: export MAVEN_HOME=$maven_dir && export PATH=\$MAVEN_HOME/bin:\$PATH"
                        return 0  # 仍然返回成功，因为安装已完成
                    fi
                else
                    print_error "Maven 3.6.3 安装失败，请手动安装后重试"
                    exit 1
                fi
                ;;
            [nN][oO]|[nN]|"")
                print_error "Maven 是必需的，安装流程已终止"
                exit 1
                ;;
            *)
                print_warning "请输入 y 或 N"
                ;;
        esac
    done
}

# 检查 nvidia-container-toolkit 是否已安装
check_nvidia_container_toolkit() {
    if command -v nvidia-container-runtime &> /dev/null; then
        local runtime_path=$(which nvidia-container-runtime)
        print_success "nvidia-container-toolkit 已安装: $runtime_path"
        return 0
    fi
    
    # 检查是否通过包管理器安装
    if dpkg -l | grep -q nvidia-container-toolkit 2>/dev/null || rpm -qa | grep -q nvidia-container-toolkit 2>/dev/null; then
        print_info "nvidia-container-toolkit 已通过包管理器安装"
        return 0
    fi
    
    return 1
}

# 安装 nvidia-container-toolkit
install_nvidia_container_toolkit() {
    print_section "安装 NVIDIA Container Toolkit"
    
    if [ "$EUID" -ne 0 ]; then
        print_error "安装 nvidia-container-toolkit 需要 root 权限，请使用 sudo 运行此脚本"
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
    
    # 第五步：验证安装
    print_info "验证安装..."
    sleep 2  # 等待服务启动
    
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
                    print_error "安装 nvidia-container-toolkit 需要 root 权限，请使用 sudo 运行此脚本"
                    exit 1
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
# 推荐的镜像源列表（按优先级排序）
recommended_mirrors = [
    "https://docker.m.daocloud.io",
    "https://registry.docker-cn.com",
    "https://quay.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://dockerhub.icu",
    "https://docker.1ms.run/"
]
nvidia_runtime = {
    "path": "nvidia-container-runtime",
    "runtimeArgs": []
}
# 只有在有 GPU 支持时才设置 default-runtime
required_default_runtime = "nvidia" if has_gpu else None

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
            apt-get update -qq > /dev/null 2>&1
            apt-get install -qq -y \
                ca-certificates \
                curl \
                gnupg \
                lsb-release > /dev/null 2>&1
            
            # 添加 Docker 官方 GPG 密钥
            install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/$os_id/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            chmod a+r /etc/apt/keyrings/docker.gpg
            
            # 设置仓库
            echo \
              "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$os_id \
              $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            # 安装 Docker Engine
            apt-get update -qq > /dev/null 2>&1
            apt-get install -qq -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin > /dev/null 2>&1
            
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
            apt-get update -qq > /dev/null 2>&1
            apt-get install -qq -y docker-compose-plugin > /dev/null 2>&1
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
                        print_error "Docker 安装成功但无法访问，请检查权限"
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
        
        # 检测网络是否可用（尝试创建一个临时容器测试）
        if ! docker run --rm --network easyaiot-network alpine:latest ping -c 1 8.8.8.8 > /dev/null 2>&1; then
            print_warning "检测到网络 easyaiot-network 可能存在问题（可能是IP变化导致）"
            print_info "正在尝试重新创建网络..."
            
            # 获取连接到该网络的所有容器
            local containers=$(docker network inspect easyaiot-network --format '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null || echo "")
            
            if [ -n "$containers" ]; then
                print_warning "以下容器正在使用该网络，需要先停止："
                echo "$containers" | tr ' ' '\n' | grep -v '^$' | while read -r container; do
                    echo "  - $container"
                done
                print_info "请先停止所有相关容器，然后重新运行安装脚本"
                return 1
            fi
            
            # 删除旧网络
            docker network rm easyaiot-network 2>/dev/null || true
            sleep 1
            
            # 重新创建网络
            if docker network create easyaiot-network 2>/dev/null; then
                print_success "网络 easyaiot-network 已重新创建"
            else
                print_error "无法重新创建网络 easyaiot-network"
                return 1
            fi
        else
            print_info "网络 easyaiot-network 运行正常"
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

# 获取宿主机 IP 地址（排除 Docker 网络接口）
get_host_ip() {
    local host_ip=""
    
    # 方法1: 通过路由获取（最可靠，通常返回物理网络接口的 IP）
    if command -v ip &> /dev/null; then
        host_ip=$(ip route get 8.8.8.8 2>/dev/null | awk '{print $7}' | head -n 1)
        if [ -n "$host_ip" ] && [ "$host_ip" != "127.0.0.1" ] && ! is_docker_network_ip "$host_ip"; then
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
                if [ "$ip" != "127.0.0.1" ] && [[ ! "$ip" =~ ^169\.254\. ]] && ! is_docker_network_ip "$ip"; then
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
                if [ "$ip" != "127.0.0.1" ] && [[ ! "$ip" =~ ^169\.254\. ]] && ! is_docker_network_ip "$ip"; then
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
                if [ "$ip" != "127.0.0.1" ] && [[ ! "$ip" =~ ^169\.254\. ]] && ! is_docker_network_ip "$ip"; then
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

# 创建并设置 PostgreSQL 数据目录权限
create_postgresql_directories() {
    local postgresql_data_dir="${SCRIPT_DIR}/db_data/data"
    local postgresql_log_dir="${SCRIPT_DIR}/db_data/log"
    
    print_info "创建 PostgreSQL 数据目录并设置权限..."
    
    # 创建目录
    mkdir -p "$postgresql_data_dir" "$postgresql_log_dir"
    
    # 设置目录所有者为 UID 999 (PostgreSQL 容器默认 postgres 用户)
    # 如果当前用户有权限，则设置；否则只创建目录
    if [ "$EUID" -eq 0 ]; then
        chown -R 999:999 "$postgresql_data_dir" "$postgresql_log_dir"
        chmod -R 700 "$postgresql_data_dir"
        chmod -R 755 "$postgresql_log_dir"
        print_success "PostgreSQL 数据目录权限已设置 (UID 999:999)"
    else
        # 非 root 用户尝试使用 sudo（如果可用）
        if command -v sudo &> /dev/null; then
            sudo chown -R 999:999 "$postgresql_data_dir" "$postgresql_log_dir" 2>/dev/null && \
            sudo chmod -R 700 "$postgresql_data_dir" 2>/dev/null && \
            sudo chmod -R 755 "$postgresql_log_dir" 2>/dev/null && \
            print_success "PostgreSQL 数据目录权限已设置 (UID 999:999)" || \
            print_warning "无法设置 PostgreSQL 目录权限，可能需要手动设置: sudo chown -R 999:999 $postgresql_data_dir $postgresql_log_dir"
        else
            print_warning "无法设置 PostgreSQL 目录权限，请手动执行: sudo chown -R 999:999 $postgresql_data_dir $postgresql_log_dir"
        fi
    fi
}

# 创建并设置 Redis 数据目录权限
create_redis_directories() {
    local redis_data_dir="${SCRIPT_DIR}/redis_data/data"
    local redis_log_dir="${SCRIPT_DIR}/redis_data/logs"
    
    print_info "创建 Redis 数据目录并设置权限..."
    
    # 创建目录
    mkdir -p "$redis_data_dir" "$redis_log_dir"
    
    # Redis 容器默认使用 UID 999 (redis 用户)
    # 如果当前用户有权限，则设置；否则只创建目录
    if [ "$EUID" -eq 0 ]; then
        chown -R 999:999 "$redis_data_dir" "$redis_log_dir"
        chmod -R 755 "$redis_data_dir"
        chmod -R 755 "$redis_log_dir"
        print_success "Redis 数据目录权限已设置 (UID 999:999)"
    else
        # 非 root 用户尝试使用 sudo（如果可用）
        if command -v sudo &> /dev/null; then
            sudo chown -R 999:999 "$redis_data_dir" "$redis_log_dir" 2>/dev/null && \
            sudo chmod -R 755 "$redis_data_dir" 2>/dev/null && \
            sudo chmod -R 755 "$redis_log_dir" 2>/dev/null && \
            print_success "Redis 数据目录权限已设置 (UID 999:999)" || \
            print_warning "无法设置 Redis 目录权限，可能需要手动设置: sudo chown -R 999:999 $redis_data_dir $redis_log_dir"
        else
            print_warning "无法设置 Redis 目录权限，请手动执行: sudo chown -R 999:999 $redis_data_dir $redis_log_dir"
        fi
    fi
}

# 创建所有中间件的存储目录
create_all_storage_directories() {
    print_info "创建所有中间件存储目录..."
    
    # 定义所有需要创建的存储目录及其权限设置
    # 格式: "目录路径:UID:GID:权限"
    local storage_dirs=(
        "${SCRIPT_DIR}/standalone-logs:::"              # Nacos 日志（使用默认权限）
        "${SCRIPT_DIR}/db_data/data:999:999:700"       # PostgreSQL 数据
        "${SCRIPT_DIR}/db_data/log:999:999:755"        # PostgreSQL 日志
        "${SCRIPT_DIR}/taos_data/data:::"              # TDengine 数据（使用默认权限）
        "${SCRIPT_DIR}/taos_data/log:::"               # TDengine 日志（使用默认权限）
        "${SCRIPT_DIR}/redis_data/data:999:999:755"   # Redis 数据
        "${SCRIPT_DIR}/redis_data/logs:999:999:755"    # Redis 日志
        "${SCRIPT_DIR}/mq_data/data:::"                # Kafka 数据（使用默认权限）
        "${SCRIPT_DIR}/minio_data/data:::"             # MinIO 数据（使用默认权限）
        "${SCRIPT_DIR}/minio_data/config:::"           # MinIO 配置（使用默认权限）
        "${SCRIPT_DIR}/srs_data/conf:::"               # SRS 配置（使用默认权限）
        "${SCRIPT_DIR}/srs_data/data:::"              # SRS 数据（使用默认权限）
        "${SCRIPT_DIR}/srs_data/playbacks:::"          # SRS 回放（使用默认权限）
        "${SCRIPT_DIR}/nodered_data/data:1000:1000:755" # NodeRED 数据
    )
    
    local created_count=0
    local total_count=${#storage_dirs[@]}
    
    for dir_spec in "${storage_dirs[@]}"; do
        # 解析目录规格
        IFS=':' read -r dir_path uid gid perms <<< "$dir_spec"
        
        if [ -z "$dir_path" ]; then
            continue
        fi
        
        # 创建目录
        if mkdir -p "$dir_path" 2>/dev/null; then
            # 如果指定了 UID/GID，尝试设置权限
            if [ -n "$uid" ] && [ -n "$gid" ]; then
                if [ "$EUID" -eq 0 ]; then
                    chown -R "${uid}:${gid}" "$dir_path" 2>/dev/null || true
                    if [ -n "$perms" ]; then
                        chmod -R "$perms" "$dir_path" 2>/dev/null || true
                    fi
                elif command -v sudo &> /dev/null; then
                    sudo chown -R "${uid}:${gid}" "$dir_path" 2>/dev/null || true
                    if [ -n "$perms" ]; then
                        sudo chmod -R "$perms" "$dir_path" 2>/dev/null || true
                    fi
                fi
            fi
            created_count=$((created_count + 1))
        else
            print_warning "创建目录失败: $dir_path"
        fi
    done
    
    if [ $created_count -eq $total_count ]; then
        print_success "所有存储目录已创建（${created_count}/${total_count}）"
    else
        print_warning "部分存储目录创建失败（${created_count}/${total_count}）"
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

# 准备 SRS 配置文件
# 强制更新模式：无论配置文件是否存在，都重新生成并自动替换 IP 地址
prepare_srs_config() {
    local srs_config_source="${SCRIPT_DIR}/../srs/conf"
    local srs_config_target="${SCRIPT_DIR}/srs_data/conf"
    local srs_config_file="${srs_config_target}/docker.conf"
    
    print_info "准备 SRS 配置文件..."
    
    # 获取宿主机 IP 地址
    local host_ip=$(get_host_ip)
    if [ -z "$host_ip" ]; then
        print_warning "无法获取宿主机 IP，将使用 127.0.0.1（可能导致 VIDEO 模块回调失败）"
        host_ip="127.0.0.1"
    else
        print_info "检测到宿主机 IP: $host_ip"
    fi
    
    # 创建目标目录
    mkdir -p "$srs_config_target"
    
    # 强制更新模式：无论配置文件是否存在，都重新生成
    print_info "重新获取宿主机 IP 并重新生成配置文件..."
    
    # 尝试从源目录复制配置文件
    if [ -d "$srs_config_source" ] && [ -f "$srs_config_source/docker.conf" ]; then
        print_info "从源目录复制 SRS 配置文件..."
        if cp -f "$srs_config_source/docker.conf" "$srs_config_file" 2>/dev/null; then
            # 替换配置文件中的所有 IP 地址为宿主机 IP
            # 匹配模式: http://IP:6000 或 http://IP:6000/...
            sed -i -E "s|http://([0-9]{1,3}\.){3}[0-9]{1,3}:6000|http://${host_ip}:6000|g" "$srs_config_file"
            print_info "已将配置文件中的 IP 地址更新为宿主机 IP: $host_ip"
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
        on_dvr              http://${host_ip}:6000/video/camera/callback/on_dvr;
        on_publish          http://${host_ip}:6000/video/camera/callback/on_publish;
    }
}
EOF
    
    # 验证文件是否创建成功
    if [ -f "$srs_config_file" ]; then
        print_success "默认 SRS 配置文件已创建: $srs_config_file (使用宿主机 IP: $host_ip)"
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
        print_info "正在配置 pip 以允许安装系统包..."
        # 配置 pip 允许安装系统包，避免某些系统上的权限错误
        python3 -m pip config set global.break-system-packages true > /dev/null 2>&1 || true
        
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

# 检查并拉取缺失的镜像
check_and_pull_images() {
    print_info "检查所需镜像是否存在..."
    
    # 获取 docker-compose.yml 中定义的所有服务
    local services=$($COMPOSE_CMD -f "$COMPOSE_FILE" config --services 2>/dev/null || echo "")
    
    if [ -z "$services" ]; then
        print_warning "无法获取服务列表，将直接启动服务（会自动拉取缺失镜像）"
        return 0
    fi
    
    local missing_images=0
    local existing_images=0
    local images_to_check=()
    
    # 从 docker-compose 配置中提取所有镜像信息
    local compose_config=$($COMPOSE_CMD -f "$COMPOSE_FILE" config 2>/dev/null || echo "")
    
    if [ -z "$compose_config" ]; then
        print_warning "无法读取 docker-compose 配置，将直接启动服务"
        return 0
    fi
    
    # 提取所有镜像名称（处理多种格式）
    while IFS= read -r line; do
        # 匹配 image: 行，支持多种格式
        if echo "$line" | grep -qE "^\s*image:"; then
            local image=$(echo "$line" | sed -E 's/^\s*image:\s*//' | sed -E "s/^['\"]//" | sed -E "s/['\"]$//" | tr -d ' ')
            if [ -n "$image" ] && [[ ! " ${images_to_check[@]} " =~ " ${image} " ]]; then
                images_to_check+=("$image")
            fi
        fi
    done <<< "$compose_config"
    
    # 检查每个镜像是否存在
    for image in "${images_to_check[@]}"; do
        if docker image inspect "$image" &> /dev/null; then
            print_info "镜像已存在: $image"
            existing_images=$((existing_images + 1))
        else
            print_warning "镜像不存在: $image"
            missing_images=$((missing_images + 1))
        fi
    done
    
    # 如果有缺失的镜像，才执行拉取
    if [ $missing_images -gt 0 ]; then
        print_info "发现 $missing_images 个缺失镜像，开始拉取..."
        print_info "已存在 $existing_images 个镜像，跳过拉取"
        $COMPOSE_CMD -f "$COMPOSE_FILE" pull 2>&1 | tee -a "$LOG_FILE"
        print_success "镜像拉取完成"
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
            "EMQX")
                ports=("1883" "8883" "8083" "8084" "18083")
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
            "EMQX") container_name="emqx-server" ;;
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
            
            # 检查是否还有 Docker 容器占用端口
            local docker_using_port=$(docker ps --format "{{.Ports}}" 2>/dev/null | grep -E ":$port->|0\.0\.0\.0:$port|:::$port" || echo "")
            if [ -n "$docker_using_port" ]; then
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
    
    if [ $wait_count -ge $max_wait ]; then
        print_warning "等待端口释放超时，继续检查..."
    else
        print_success "端口已释放"
    fi
    
    sleep 1
    
    # 检查所有中间件端口（包括所有映射的端口）
    for service in "${MIDDLEWARE_SERVICES[@]}"; do
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
        for port in "${conflict_ports[@]}"; do
            local docker_using=$(docker ps --format "{{.Ports}}" 2>/dev/null | grep -E ":$port->|0\.0\.0\.0:$port|:::$port" || echo "")
            if [ -z "$docker_using" ]; then
                # 检查是否是宿主机进程
                if command -v ss &> /dev/null && ss -tlnp 2>/dev/null | grep -qE ":$port[[:space:]]|:$port$"; then
                    has_host_process=1
                    break
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
                    
                    for port in "${conflict_ports[@]}"; do
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
                                    "EMQX") container_name="emqx-server" ;;
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
                "SRS") container_names+=("srs-server") ;;
                "NodeRED") container_names+=("nodered-server") ;;
                "EMQX") container_names+=("emqx-server") ;;
            esac
        fi
    done
    
    # 检查是否有停止的容器需要清理
    local stale_containers=$(docker ps -a --filter "status=exited" --format "{{.Names}}" 2>/dev/null | grep -E "(nacos-server|postgres-server|tdengine-server|redis-server|kafka-server|minio-server|srs-server|nodered-server|emqx-server)" || echo "")
    
    if [ -n "$stale_containers" ]; then
        print_info "发现残留的停止容器，正在清理..."
        echo "$stale_containers" | while read -r container; do
            print_info "删除残留容器: $container"
            docker rm "$container" 2>/dev/null || true
        done
        sleep 1
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
    
    # 检查并安装 Maven 3.6.3
    check_and_install_maven363
    
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
    
    # 强制更新 SRS 配置文件（重新获取宿主机 IP）
    prepare_srs_config
    prepare_emqx_volumes
    
    # 检查并拉取缺失的镜像（如果镜像已存在则跳过拉取）
    echo ""
    check_and_pull_images
    
    # 清理残留容器
    cleanup_stale_containers
    
    # 检查端口占用
    check_and_clean_ports
    
    print_info "启动所有中间件服务..."
    if $COMPOSE_CMD -f "$COMPOSE_FILE" up -d 2>&1 | tee -a "$LOG_FILE"; then
        print_success "容器启动命令执行完成"
    else
        print_error "容器启动过程中出现错误"
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
            "EMQX") container_name="emqx-server" ;;
        esac
        
        if [ -n "$container_name" ]; then
            local container_status=$(docker ps -a --filter "name=^${container_name}$" --format "{{.Status}}" 2>/dev/null | head -1 || echo "")
            if [ -n "$container_status" ]; then
                if echo "$container_status" | grep -qE "Exited|Dead|Restarting"; then
                    print_warning "$service ($container_name) 容器状态异常: $container_status"
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
                *) print_info "  docker-compose logs $service" ;;
            esac
        done
        echo ""
    fi
    
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
    
    # 创建所有中间件的存储目录（如果不存在则创建新的）
    create_all_storage_directories
    
    # 确保关键目录的权限正确
    create_postgresql_directories
    create_redis_directories
    create_nodered_directories
    
    prepare_srs_config
    prepare_emqx_volumes
    
    # 清理残留容器
    cleanup_stale_containers
    
    # 检查端口占用
    check_and_clean_ports
    
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
    
    # 创建所有中间件的存储目录（如果不存在则创建新的）
    create_all_storage_directories
    
    # 确保关键目录的权限正确
    create_postgresql_directories
    create_redis_directories
    create_nodered_directories
    
    prepare_srs_config
    prepare_emqx_volumes
    
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

# 检查并重新加载环境变量
reload_environment() {
    # 检查 /etc/profile 中是否有环境变量配置
    if [ ! -f /etc/profile ]; then
        print_warning "/etc/profile 文件不存在"
        return 1
    fi
    
    if ! grep -q "JAVA_HOME\|JRE_HOME" /etc/profile 2>/dev/null; then
        print_info "/etc/profile 中未找到 JAVA_HOME 或 JRE_HOME 配置"
        
        # 检查 Java 是否已安装但未配置环境变量
        if ! check_command java; then
            print_warning "Java 未安装，将触发 Java 安装流程"
            # 触发 Java 安装检查（但不强制安装，让用户选择）
            if ! check_java_version; then
                print_info "将检查并安装 JDK8..."
                # 注意：这里不直接调用 check_and_install_jdk8，因为它在 install_middleware 中已经调用
                # 如果是在其他命令中调用，则提示用户
                return 0
            fi
        else
            # Java 已安装但环境变量未配置，提示用户
            print_warning "检测到 Java 已安装但环境变量未配置"
            print_info "建议运行安装命令以配置 Java 环境变量"
        fi
        return 0
    fi
    
    print_info "检测到 /etc/profile 中有环境变量配置，正在重新加载..."
    
    # 检查文件权限
    if [ ! -r /etc/profile ]; then
        print_warning "/etc/profile 文件不可读，尝试使用 sudo..."
        # 尝试通过 sudo 读取并执行
        if command -v sudo &> /dev/null; then
            # 使用 sudo 读取文件内容，然后通过 eval 执行
            local profile_content=$(sudo cat /etc/profile 2>/dev/null)
            if [ -n "$profile_content" ]; then
                # 提取 JAVA_HOME 相关的环境变量设置
                local java_vars=$(echo "$profile_content" | grep -E "^export (JAVA_HOME|JRE_HOME|CLASSPATH|PATH)" | grep -v "^#")
                if [ -n "$java_vars" ]; then
                    # 执行这些 export 命令
                    eval "$java_vars" 2>/dev/null
                    if [ $? -eq 0 ]; then
                        print_success "环境变量已重新加载（通过 sudo）"
                        if [ -n "$JAVA_HOME" ]; then
                            print_info "JAVA_HOME: $JAVA_HOME"
                        fi
                        return 0
                    fi
                fi
            fi
        fi
        print_error "无法读取 /etc/profile，请手动执行: sudo bash -c 'source /etc/profile'"
        return 1
    fi
    
    # 直接 source /etc/profile（在当前 shell 中）
    # 注意：不能使用命令替换 $(source ...)，因为那样会在子shell中执行
    # 使用临时文件捕获错误输出
    local error_file=$(mktemp)
    if source /etc/profile > "$error_file" 2>&1; then
        rm -f "$error_file"
        print_success "环境变量已重新加载"
        
        # 验证 JAVA_HOME 是否已设置
        if [ -n "$JAVA_HOME" ]; then
            print_info "JAVA_HOME: $JAVA_HOME"
            # 验证 java 命令是否可用
            if command -v java &> /dev/null; then
                local java_version=$(java -version 2>&1 | head -n 1)
                print_info "Java 版本: $java_version"
            fi
            return 0
        else
            print_warning "JAVA_HOME 未设置，可能环境变量配置有问题"
            print_info "请检查 /etc/profile 中的 JAVA_HOME 配置"
            return 1
        fi
    else
        local source_error=$(cat "$error_file" 2>/dev/null || echo "")
        rm -f "$error_file"
        print_warning "source /etc/profile 执行失败"
        if [ -n "$source_error" ]; then
            print_info "错误信息: $source_error"
        fi
        print_info "请手动执行以下命令之一："
        print_info "  1. source /etc/profile"
        print_info "  2. . /etc/profile"
        print_info "  3. 如果权限不足，请使用: sudo bash -c 'source /etc/profile && exec bash'"
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
        
        # 第三步：删除容器和 Docker 具名卷（不删除镜像）
        print_info "删除所有容器和 Docker 具名卷（镜像将保留）..."
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
        
        # 第五步：删除所有 bind mount 的宿主机存储目录
        print_info "删除所有 bind mount 存储目录..."
        
        # 定义所有需要删除的存储目录（相对于脚本目录）
        local data_dirs=(
            "standalone-logs"           # Nacos 日志
            "db_data"                   # PostgreSQL 数据和日志
            "taos_data"                 # TDengine 数据和日志
            "redis_data"                # Redis 数据和日志
            "mq_data"                   # Kafka 数据
            "minio_data"                 # MinIO 数据和配置
            "srs_data"                  # SRS 配置、数据和回放
            "nodered_data"              # NodeRED 数据
        )
        
        # 删除每个存储目录
        local deleted_count=0
        local total_count=${#data_dirs[@]}
        
        for dir_name in "${data_dirs[@]}"; do
            local full_path="${SCRIPT_DIR}/${dir_name}"
            if [ -d "$full_path" ]; then
                print_info "删除存储目录: $full_path"
                if rm -rf "$full_path" 2>/dev/null; then
                    print_success "已删除: $dir_name"
                    deleted_count=$((deleted_count + 1))
                else
                    print_warning "删除失败（可能需要 root 权限）: $dir_name"
                    # 尝试使用 sudo（如果可用）
                    if command -v sudo &> /dev/null; then
                        if sudo rm -rf "$full_path" 2>/dev/null; then
                            print_success "已删除（使用 sudo）: $dir_name"
                            deleted_count=$((deleted_count + 1))
                        else
                            print_error "无法删除: $dir_name，请手动删除: sudo rm -rf $full_path"
                        fi
                    else
                        print_error "无法删除: $dir_name，请手动删除: rm -rf $full_path"
                    fi
                fi
            else
                print_info "目录不存在，跳过: $dir_name"
                deleted_count=$((deleted_count + 1))
            fi
        done
        
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
        
        print_success "清理完成"
        
        # 清理完成后，自动检查并重新加载环境变量
        echo ""
        if [ -f /etc/profile ] && grep -q "JAVA_HOME\|JRE_HOME" /etc/profile 2>/dev/null; then
            print_info "检测到 /etc/profile 中有环境变量配置，正在自动重新加载..."
            if reload_environment; then
                print_success "环境变量已自动重新加载"
            else
                print_warning "自动加载失败，请手动执行: source /etc/profile"
            fi
        fi
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
    
    # 创建所有中间件的存储目录（如果不存在则创建新的）
    create_all_storage_directories
    
    # 确保关键目录的权限正确
    create_postgresql_directories
    create_redis_directories
    create_nodered_directories
    
    prepare_srs_config
    prepare_emqx_volumes
    
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
    # 在执行任何命令之前（除了 help），先检查 Git
    if [ "${1:-help}" != "help" ] && [ "${1:-help}" != "--help" ] && [ "${1:-help}" != "-h" ]; then
        check_and_require_git
        # 然后尝试加载环境变量
        reload_environment
    fi
    
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
