#!/bin/bash

# ============================================
# Docker Data-Root 检测脚本
# ============================================
# 用于检测 Docker 使用的 data-root 目录
# 显示存储空间、已用空间、剩余空间等信息
# 使用方法：
#   ./detect_docker_data_root.sh
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

# 格式化字节大小
format_size() {
    local bytes=$1
    if [ -z "$bytes" ] || [ "$bytes" = "0" ]; then
        echo "0 B"
        return
    fi
    
    # 使用 awk 进行浮点数计算（不依赖 bc）
    if command -v awk &> /dev/null; then
        awk -v bytes="$bytes" 'BEGIN {
            tb = bytes / 1024 / 1024 / 1024 / 1024
            gb = bytes / 1024 / 1024 / 1024
            mb = bytes / 1024 / 1024
            kb = bytes / 1024
            
            if (tb >= 1) {
                printf "%.2f TB", tb
            } else if (gb >= 1) {
                printf "%.2f GB", gb
            } else if (mb >= 1) {
                printf "%.2f MB", mb
            } else if (kb >= 1) {
                printf "%.2f KB", kb
            } else {
                printf "%d B", bytes
            }
        }'
    else
        # 如果 awk 也不可用，使用简单的整数除法
        local kb=$((bytes / 1024))
        local mb=$((kb / 1024))
        local gb=$((mb / 1024))
        local tb=$((gb / 1024))
        
        if [ $tb -gt 0 ]; then
            echo "${tb} TB"
        elif [ $gb -gt 0 ]; then
            echo "${gb} GB"
        elif [ $mb -gt 0 ]; then
            echo "${mb} MB"
        elif [ $kb -gt 0 ]; then
            echo "${kb} KB"
        else
            echo "${bytes} B"
        fi
    fi
}

# 获取目录大小（字节）
get_dir_size() {
    local dir=$1
    if [ ! -d "$dir" ]; then
        echo "0"
        return
    fi
    
    # 使用 du 命令获取目录大小（以字节为单位）
    du -sb "$dir" 2>/dev/null | awk '{print $1}' || echo "0"
}

# 检测 Docker data-root
detect_docker_data_root() {
    print_section "Docker Data-Root 检测"
    
    # 检查 Docker 是否安装
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装"
        return 1
    fi
    
    # 方法1: 从 daemon.json 读取配置
    local docker_data_root=""
    local docker_config_file="/etc/docker/daemon.json"
    
    if [ -f "$docker_config_file" ]; then
        print_info "检测到 Docker 配置文件: $docker_config_file"
        
        # 使用 Python 读取配置
        docker_data_root=$(python3 << 'EOF'
import json
import sys

try:
    with open('/etc/docker/daemon.json', 'r') as f:
        config = json.load(f)
        data_root = config.get('data-root', '')
        if data_root:
            print(data_root)
except Exception as e:
    pass
EOF
)
        
        if [ -n "$docker_data_root" ]; then
            print_key_value "配置来源" "daemon.json"
            print_key_value "Data-Root 路径" "$docker_data_root"
        fi
    fi
    
    # 方法2: 从 docker info 获取实际使用的路径
    local docker_info_data_root=""
    if docker info &> /dev/null; then
        docker_info_data_root=$(docker info 2>/dev/null | grep -i "Docker Root Dir" | awk '{print $4}' || echo "")
        
        if [ -n "$docker_info_data_root" ]; then
            if [ -z "$docker_data_root" ]; then
                print_key_value "配置来源" "docker info"
                print_key_value "Data-Root 路径" "$docker_info_data_root"
                docker_data_root="$docker_info_data_root"
            else
                # 验证配置文件和实际路径是否一致
                if [ "$docker_data_root" != "$docker_info_data_root" ]; then
                    print_warning "配置文件中的路径与实际路径不一致"
                    print_key_value "配置文件路径" "$docker_data_root"
                    print_key_value "实际使用路径" "$docker_info_data_root"
                    docker_data_root="$docker_info_data_root"
                fi
            fi
        fi
    fi
    
    # 方法3: 检查默认路径
    if [ -z "$docker_data_root" ]; then
        if [ -d "/var/lib/docker" ]; then
            docker_data_root="/var/lib/docker"
            print_key_value "配置来源" "默认路径"
            print_key_value "Data-Root 路径" "$docker_data_root"
        elif [ -d "/var/snap/docker/common/var-lib-docker" ]; then
            docker_data_root="/var/snap/docker/common/var-lib-docker"
            print_key_value "配置来源" "Snap 默认路径"
            print_key_value "Data-Root 路径" "$docker_data_root"
        else
            print_error "无法检测到 Docker data-root 目录"
            return 1
        fi
    fi
    
    # 验证目录是否存在
    if [ ! -d "$docker_data_root" ]; then
        print_error "Docker data-root 目录不存在: $docker_data_root"
        return 1
    fi
    
    print_success "Docker data-root 目录: $docker_data_root"
    
    return 0
}

# 显示存储空间信息
show_storage_info() {
    local docker_data_root=$1
    
    if [ -z "$docker_data_root" ]; then
        print_error "Docker data-root 路径为空"
        return 1
    fi
    
    print_section "存储空间信息"
    
    # 获取挂载点信息
    local mount_point=$(df "$docker_data_root" 2>/dev/null | tail -1 | awk '{print $6}')
    local filesystem=$(df -T "$docker_data_root" 2>/dev/null | tail -1 | awk '{print $2}' || echo "未知")
    
    print_key_value "文件系统类型" "$filesystem"
    print_key_value "挂载点" "$mount_point"
    
    # 使用 df 获取磁盘空间信息
    local df_output=$(df -h "$docker_data_root" 2>/dev/null | tail -1)
    if [ -n "$df_output" ]; then
        local total_space=$(echo "$df_output" | awk '{print $2}')
        local used_space=$(echo "$df_output" | awk '{print $3}')
        local available_space=$(echo "$df_output" | awk '{print $4}')
        local usage_percent=$(echo "$df_output" | awk '{print $5}')
        
        print_key_value "总存储空间" "$total_space"
        print_key_value "已用空间" "$used_space"
        print_key_value "剩余空间" "$available_space"
        print_key_value "使用率" "$usage_percent"
        
        # 使用 df 获取精确的字节数
        local df_bytes=$(df -B1 "$docker_data_root" 2>/dev/null | tail -1)
        if [ -n "$df_bytes" ]; then
            local total_bytes=$(echo "$df_bytes" | awk '{print $2}')
            local used_bytes=$(echo "$df_bytes" | awk '{print $3}')
            local available_bytes=$(echo "$df_bytes" | awk '{print $4}')
            
            echo ""
            print_info "精确空间信息（字节）:"
            print_key_value "总空间" "$(format_size $total_bytes)"
            print_key_value "已用空间" "$(format_size $used_bytes)"
            print_key_value "剩余空间" "$(format_size $available_bytes)"
        fi
    else
        print_warning "无法获取磁盘空间信息"
    fi
    
    # 计算 Docker data-root 目录实际大小
    echo ""
    print_info "正在计算 Docker data-root 目录实际大小（这可能需要一些时间）..."
    local dir_size=$(get_dir_size "$docker_data_root")
    if [ "$dir_size" != "0" ]; then
        print_key_value "目录实际大小" "$(format_size $dir_size)"
    else
        print_warning "无法计算目录大小"
    fi
}

# 显示 Docker 使用情况
show_docker_usage() {
    print_section "Docker 使用情况"
    
    if ! docker ps &> /dev/null; then
        print_warning "无法访问 Docker daemon，跳过 Docker 使用情况统计"
        return
    fi
    
    # 容器数量
    local running_containers=$(docker ps -q 2>/dev/null | wc -l)
    local total_containers=$(docker ps -aq 2>/dev/null | wc -l)
    local stopped_containers=$((total_containers - running_containers))
    
    print_key_value "运行中容器" "$running_containers"
    print_key_value "已停止容器" "$stopped_containers"
    print_key_value "总容器数" "$total_containers"
    
    # 镜像数量
    local total_images=$(docker images -q 2>/dev/null | wc -l)
    print_key_value "镜像数量" "$total_images"
    
    # 卷数量
    local total_volumes=$(docker volume ls -q 2>/dev/null | wc -l)
    print_key_value "数据卷数量" "$total_volumes"
    
    # 网络数量
    local total_networks=$(docker network ls -q 2>/dev/null | wc -l)
    print_key_value "网络数量" "$total_networks"
    
    # Docker 系统磁盘使用情况
    echo ""
    print_info "Docker 系统磁盘使用情况:"
    docker system df 2>/dev/null || print_warning "无法获取 Docker 系统磁盘使用情况"
}

# 显示详细目录信息
show_directory_details() {
    local docker_data_root=$1
    
    if [ -z "$docker_data_root" ] || [ ! -d "$docker_data_root" ]; then
        return
    fi
    
    print_section "目录详细信息"
    
    # 目录权限
    local dir_perms=$(stat -c "%a" "$docker_data_root" 2>/dev/null || stat -f "%OLp" "$docker_data_root" 2>/dev/null || echo "未知")
    local dir_owner=$(stat -c "%U:%G" "$docker_data_root" 2>/dev/null || stat -f "%Su:%Sg" "$docker_data_root" 2>/dev/null || echo "未知")
    
    print_key_value "目录权限" "$dir_perms"
    print_key_value "目录所有者" "$dir_owner"
    
    # 子目录大小（如果存在）
    echo ""
    print_info "主要子目录大小:"
    
    local subdirs=("containers" "images" "volumes" "overlay2" "network" "buildkit")
    for subdir in "${subdirs[@]}"; do
        local subdir_path="$docker_data_root/$subdir"
        if [ -d "$subdir_path" ]; then
            local subdir_size=$(get_dir_size "$subdir_path")
            if [ "$subdir_size" != "0" ]; then
                printf "  ${MAGENTA}%-20s${NC} : %s\n" "$subdir" "$(format_size $subdir_size)"
            fi
        fi
    done
}

# 主函数
main() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  Docker Data-Root 检测工具${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
    echo "检测时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # 检测 Docker data-root
    local docker_data_root=""
    if detect_docker_data_root; then
        # 从输出中提取路径（简单方法：重新检测）
        if [ -f "/etc/docker/daemon.json" ]; then
            docker_data_root=$(python3 << 'EOF'
import json
try:
    with open('/etc/docker/daemon.json', 'r') as f:
        config = json.load(f)
        print(config.get('data-root', ''))
except:
    pass
EOF
)
        fi
        
        if [ -z "$docker_data_root" ]; then
            docker_data_root=$(docker info 2>/dev/null | grep -i "Docker Root Dir" | awk '{print $4}' || echo "")
        fi
        
        if [ -z "$docker_data_root" ]; then
            if [ -d "/var/lib/docker" ]; then
                docker_data_root="/var/lib/docker"
            elif [ -d "/var/snap/docker/common/var-lib-docker" ]; then
                docker_data_root="/var/snap/docker/common/var-lib-docker"
            fi
        fi
        
        # 显示存储空间信息
        if [ -n "$docker_data_root" ]; then
            show_storage_info "$docker_data_root"
            show_docker_usage
            show_directory_details "$docker_data_root"
        fi
    else
        print_error "检测失败"
        exit 1
    fi
    
    echo ""
    print_section "检测完成"
    echo "完成时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
}

# 运行主函数
main "$@"

