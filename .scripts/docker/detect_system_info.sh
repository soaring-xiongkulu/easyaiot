#!/bin/bash

# ============================================
# EasyAIoT 系统信息检测脚本
# ============================================
# 用于检测当前服务器的操作系统类型和其他系统信息
# 使用方法：
#   ./detect_system_info.sh
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
}

print_key_value() {
    local key=$1
    local value=$2
    printf "  ${MAGENTA}%-25s${NC} : %s\n" "$key" "$value"
}

# 检测操作系统类型
detect_os() {
    print_section "操作系统信息"
    
    local os_type="未知"
    local os_name="未知"
    local os_version="未知"
    local os_codename="未知"
    
    # 检测操作系统类型
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        os_type="Linux"
        
        # 检测 Linux 发行版
        if [ -f /etc/os-release ]; then
            source /etc/os-release
            os_name="$NAME"
            os_version="$VERSION"
            if [ -n "$VERSION_CODENAME" ]; then
                os_codename="$VERSION_CODENAME"
            elif [ -n "$PRETTY_NAME" ]; then
                os_codename="$PRETTY_NAME"
            fi
        elif [ -f /etc/redhat-release ]; then
            os_name=$(cat /etc/redhat-release | sed 's/ release.*//')
            os_version=$(cat /etc/redhat-release | sed 's/.*release //' | sed 's/ .*//')
        elif [ -f /etc/debian_version ]; then
            os_name="Debian"
            os_version=$(cat /etc/debian_version)
        elif [ -f /etc/SuSE-release ]; then
            os_name="SUSE"
            os_version=$(cat /etc/SuSE-release | head -1)
        elif [ -f /etc/arch-release ]; then
            os_name="Arch Linux"
            os_version="滚动发布"
        fi
        
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        os_type="macOS"
        os_name="macOS"
        os_version=$(sw_vers -productVersion 2>/dev/null || echo "未知")
        os_codename=$(sw_vers -productName 2>/dev/null || echo "未知")
        
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        os_type="Windows"
        os_name="Windows"
        os_version=$(cmd.exe /c ver 2>/dev/null | head -1 || echo "未知")
        
    elif [[ "$OSTYPE" == "freebsd"* ]]; then
        os_type="FreeBSD"
        os_name="FreeBSD"
        os_version=$(uname -r)
    fi
    
    print_key_value "操作系统类型" "$os_type"
    print_key_value "发行版名称" "$os_name"
    print_key_value "系统版本" "$os_version"
    if [ -n "$os_codename" ] && [ "$os_codename" != "未知" ]; then
        print_key_value "代号/描述" "$os_codename"
    fi
}

# 检测内核信息
detect_kernel() {
    print_section "内核信息"
    
    local kernel_name=$(uname -s 2>/dev/null || echo "未知")
    local kernel_release=$(uname -r 2>/dev/null || echo "未知")
    local kernel_version=$(uname -v 2>/dev/null || echo "未知")
    local kernel_machine=$(uname -m 2>/dev/null || echo "未知")
    
    print_key_value "内核名称" "$kernel_name"
    print_key_value "内核版本" "$kernel_release"
    print_key_value "内核详细信息" "$kernel_version"
    print_key_value "机器架构" "$kernel_machine"
}

# 检测 CPU 信息
detect_cpu() {
    print_section "CPU 信息"
    
    local cpu_model="未知"
    local cpu_cores="未知"
    local cpu_threads="未知"
    local cpu_arch="未知"
    
    # 检测 CPU 架构
    cpu_arch=$(uname -m 2>/dev/null || echo "未知")
    
    # 检测 CPU 核心数
    if [ -f /proc/cpuinfo ]; then
        cpu_cores=$(grep -c "^processor" /proc/cpuinfo 2>/dev/null || echo "未知")
        cpu_model=$(grep -m 1 "^model name" /proc/cpuinfo 2>/dev/null | cut -d ':' -f 2 | sed 's/^[[:space:]]*//' || echo "未知")
        cpu_threads=$(grep -c "^processor" /proc/cpuinfo 2>/dev/null || echo "未知")
    elif command -v sysctl &> /dev/null; then
        # macOS
        cpu_cores=$(sysctl -n hw.physicalcpu 2>/dev/null || echo "未知")
        cpu_threads=$(sysctl -n hw.logicalcpu 2>/dev/null || echo "未知")
        cpu_model=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo "未知")
    fi
    
    print_key_value "CPU 架构" "$cpu_arch"
    print_key_value "CPU 型号" "$cpu_model"
    print_key_value "物理核心数" "$cpu_cores"
    print_key_value "逻辑核心数" "$cpu_threads"
    
    # CPU 使用率（如果可用）
    if command -v top &> /dev/null || [ -f /proc/loadavg ]; then
        if [ -f /proc/loadavg ]; then
            local load_avg=$(cat /proc/loadavg | awk '{print $1}')
            print_key_value "1分钟负载" "$load_avg"
        fi
    fi
}

# 检测内存信息
detect_memory() {
    print_section "内存信息"
    
    local total_mem="未知"
    local used_mem="未知"
    local free_mem="未知"
    local available_mem="未知"
    
    if [ -f /proc/meminfo ]; then
        # Linux
        local total_kb=$(grep "^MemTotal:" /proc/meminfo | awk '{print $2}' || echo "0")
        local free_kb=$(grep "^MemFree:" /proc/meminfo | awk '{print $2}' || echo "0")
        local available_kb=$(grep "^MemAvailable:" /proc/meminfo | awk '{print $2}' || echo "0")
        local used_kb=$((total_kb - free_kb))
        
        total_mem=$(awk "BEGIN {printf \"%.2f GB\", $total_kb/1024/1024}" || echo "未知")
        free_mem=$(awk "BEGIN {printf \"%.2f GB\", $free_kb/1024/1024}" || echo "未知")
        available_mem=$(awk "BEGIN {printf \"%.2f GB\", $available_kb/1024/1024}" || echo "未知")
        used_mem=$(awk "BEGIN {printf \"%.2f GB\", $used_kb/1024/1024}" || echo "未知")
    elif command -v vm_stat &> /dev/null; then
        # macOS
        local page_size=$(vm_stat | grep "page size" | awk '{print $8}' | sed 's/\.//')
        local free_pages=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
        local active_pages=$(vm_stat | grep "Pages active" | awk '{print $3}' | sed 's/\.//')
        local inactive_pages=$(vm_stat | grep "Pages inactive" | awk '{print $3}' | sed 's/\.//')
        local wired_pages=$(vm_stat | grep "Pages wired down" | awk '{print $4}' | sed 's/\.//')
        
        local total_bytes=$((page_size * (free_pages + active_pages + inactive_pages + wired_pages)))
        local free_bytes=$((page_size * free_pages))
        local used_bytes=$((total_bytes - free_bytes))
        
        total_mem=$(awk "BEGIN {printf \"%.2f GB\", $total_bytes/1024/1024/1024}")
        free_mem=$(awk "BEGIN {printf \"%.2f GB\", $free_bytes/1024/1024/1024}")
        used_mem=$(awk "BEGIN {printf \"%.2f GB\", $used_bytes/1024/1024/1024}")
        available_mem="$free_mem"
    fi
    
    print_key_value "总内存" "$total_mem"
    print_key_value "已用内存" "$used_mem"
    print_key_value "可用内存" "$available_mem"
    print_key_value "空闲内存" "$free_mem"
}

# 检测磁盘信息
detect_disk() {
    print_section "磁盘信息"
    
    if command -v df &> /dev/null; then
        print_info "主要挂载点磁盘使用情况："
        df -h 2>/dev/null | grep -E "^/dev/|^Filesystem" | head -10 || df -h 2>/dev/null | head -10
        
        echo ""
        print_info "根目录磁盘使用情况："
        local root_usage=$(df -h / 2>/dev/null | tail -1)
        if [ -n "$root_usage" ]; then
            echo "  $root_usage"
        fi
    else
        print_warning "无法获取磁盘信息（df 命令不可用）"
    fi
}

# 检测网络信息
detect_network() {
    print_section "网络信息"
    
    local hostname=$(hostname 2>/dev/null || echo "未知")
    local domain=$(hostname -d 2>/dev/null || echo "未知")
    
    print_key_value "主机名" "$hostname"
    if [ "$domain" != "未知" ] && [ -n "$domain" ]; then
        print_key_value "域名" "$domain"
    fi
    
    echo ""
    print_info "网络接口信息："
    if command -v ip &> /dev/null; then
        ip addr show 2>/dev/null | grep -E "^[0-9]+:|inet " | head -20 || print_warning "无法获取网络接口信息"
    elif command -v ifconfig &> /dev/null; then
        ifconfig 2>/dev/null | grep -E "^[a-z]|inet " | head -20 || print_warning "无法获取网络接口信息"
    else
        print_warning "无法获取网络接口信息（ip/ifconfig 命令不可用）"
    fi
    
    echo ""
    print_info "默认路由："
    if command -v ip &> /dev/null; then
        ip route show default 2>/dev/null | head -3 || print_warning "无法获取路由信息"
    elif command -v route &> /dev/null; then
        route -n 2>/dev/null | grep "^0.0.0.0" | head -3 || print_warning "无法获取路由信息"
    else
        print_warning "无法获取路由信息"
    fi
}

# 检测 Docker 信息
detect_docker() {
    print_section "Docker 信息"
    
    if ! command -v docker &> /dev/null; then
        print_warning "Docker 未安装"
        return
    fi
    
    local docker_version=$(docker --version 2>/dev/null | sed 's/Docker version //' || echo "未知")
    print_key_value "Docker 版本" "$docker_version"
    
    echo ""
    print_info "Docker 服务状态："
    if systemctl is-active --quiet docker 2>/dev/null || pgrep -x dockerd > /dev/null 2>&1; then
        print_success "Docker 服务正在运行"
        
        # 检查 Docker 权限
        if docker ps &> /dev/null; then
            print_success "Docker 权限正常"
            
            echo ""
            print_info "Docker 系统信息："
            docker info 2>/dev/null | grep -E "Server Version|Operating System|OSType|Architecture|Total Memory|CPUs|Kernel Version" | head -10 || true
            
            echo ""
            print_info "运行中的容器数量："
            local running_containers=$(docker ps -q 2>/dev/null | wc -l)
            print_key_value "运行中" "$running_containers"
            
            local total_containers=$(docker ps -aq 2>/dev/null | wc -l)
            print_key_value "总计" "$total_containers"
        else
            print_error "Docker 权限不足（需要 sudo 或加入 docker 组）"
        fi
    else
        print_warning "Docker 服务未运行"
    fi
    
    # 检查 Docker Compose
    echo ""
    if command -v docker-compose &> /dev/null; then
        local compose_version=$(docker-compose --version 2>/dev/null | sed 's/docker-compose version //' || echo "未知")
        print_key_value "Docker Compose 版本" "$compose_version"
    elif docker compose version &> /dev/null; then
        local compose_version=$(docker compose version 2>/dev/null | sed 's/Docker Compose version //' || echo "未知")
        print_key_value "Docker Compose 版本" "$compose_version (插件)"
    else
        print_warning "Docker Compose 未安装"
    fi
}

# 检测其他系统信息
detect_other() {
    print_section "其他系统信息"
    
    # 当前用户
    local current_user=$(whoami 2>/dev/null || echo "未知")
    print_key_value "当前用户" "$current_user"
    
    # 用户 ID
    local user_id=$(id -u 2>/dev/null || echo "未知")
    print_key_value "用户 ID" "$user_id"
    
    # 是否为 root
    if [ "$EUID" -eq 0 ]; then
        print_warning "当前以 root 权限运行"
    else
        print_info "当前以普通用户权限运行"
    fi
    
    # 系统运行时间
    echo ""
    if [ -f /proc/uptime ]; then
        local uptime_seconds=$(cat /proc/uptime | awk '{print int($1)}')
        local days=$((uptime_seconds / 86400))
        local hours=$(((uptime_seconds % 86400) / 3600))
        local minutes=$(((uptime_seconds % 3600) / 60))
        print_key_value "系统运行时间" "${days}天 ${hours}小时 ${minutes}分钟"
    elif command -v uptime &> /dev/null; then
        local uptime_info=$(uptime 2>/dev/null | sed 's/.*up //' | sed 's/,.*//' || echo "未知")
        print_key_value "系统运行时间" "$uptime_info"
    fi
    
    # 系统时区
    if [ -f /etc/timezone ]; then
        local timezone=$(cat /etc/timezone 2>/dev/null || echo "未知")
        print_key_value "系统时区" "$timezone"
    elif command -v timedatectl &> /dev/null; then
        local timezone=$(timedatectl 2>/dev/null | grep "Time zone" | awk '{print $3}' || echo "未知")
        print_key_value "系统时区" "$timezone"
    fi
    
    # 当前时间
    local current_time=$(date '+%Y-%m-%d %H:%M:%S %Z' 2>/dev/null || echo "未知")
    print_key_value "当前时间" "$current_time"
    
    # Shell 信息
    local shell_path="$SHELL"
    local shell_version="未知"
    if [ -n "$shell_path" ]; then
        if [[ "$shell_path" == *"bash"* ]]; then
            shell_version=$(bash --version 2>/dev/null | head -1 | sed 's/.*version //' | sed 's/(.*//' || echo "未知")
        elif [[ "$shell_path" == *"zsh"* ]]; then
            shell_version=$(zsh --version 2>/dev/null | sed 's/.*version //' || echo "未知")
        fi
        print_key_value "Shell" "$shell_path (${shell_version})"
    fi
    
    # Python 信息（如果可用）
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 --version 2>/dev/null | sed 's/Python //' || echo "未知")
        print_key_value "Python 版本" "$python_version"
    elif command -v python &> /dev/null; then
        local python_version=$(python --version 2>/dev/null | sed 's/Python //' || echo "未知")
        print_key_value "Python 版本" "$python_version"
    fi
    
    # Java 信息（如果可用）
    if command -v java &> /dev/null; then
        local java_version=$(java -version 2>&1 | head -1 | sed 's/.*version "//' | sed 's/".*//' || echo "未知")
        print_key_value "Java 版本" "$java_version"
    fi
}

# 生成系统摘要
generate_summary() {
    print_section "系统摘要"
    
    local os_info=""
    if [ -f /etc/os-release ]; then
        source /etc/os-release
        os_info="$PRETTY_NAME"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        os_info="macOS $(sw_vers -productVersion)"
    else
        os_info="$(uname -s) $(uname -r)"
    fi
    
    print_key_value "操作系统" "$os_info"
    print_key_value "架构" "$(uname -m)"
    print_key_value "内核" "$(uname -r)"
    print_key_value "主机名" "$(hostname 2>/dev/null || echo '未知')"
    
    if [ -f /proc/meminfo ]; then
        local total_mem_gb=$(grep "^MemTotal:" /proc/meminfo | awk '{printf "%.1f", $2/1024/1024}')
        print_key_value "总内存" "${total_mem_gb} GB"
    fi
    
    if [ -f /proc/cpuinfo ]; then
        local cpu_count=$(grep -c "^processor" /proc/cpuinfo)
        print_key_value "CPU 核心" "$cpu_count"
    fi
}

# 主函数
main() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  EasyAIoT 系统信息检测工具${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
    echo "检测时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # 执行各项检测
    detect_os
    detect_kernel
    detect_cpu
    detect_memory
    detect_disk
    detect_network
    detect_docker
    detect_other
    
    # 生成摘要
    generate_summary
    
    echo ""
    print_section "检测完成"
    echo "完成时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
}

# 运行主函数
main "$@"

