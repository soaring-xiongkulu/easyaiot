#!/bin/bash

# ============================================
# Docker 磁盘空间清理脚本
# ============================================
# 用于清理 Docker 未使用的资源，释放磁盘空间
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}  $1${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
}

# 检查 Docker 是否可用
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装"
        exit 1
    fi
    
    if ! docker ps &> /dev/null; then
        print_error "无法访问 Docker daemon"
        echo ""
        echo "解决方案："
        echo "  1. 将当前用户添加到 docker 组："
        echo "     sudo usermod -aG docker $USER"
        echo "     然后重新登录或运行: newgrp docker"
        echo ""
        echo "  2. 或者使用 sudo 运行此脚本："
        echo "     sudo ./cleanup_docker_space.sh"
        echo ""
        exit 1
    fi
}

# 显示磁盘使用情况
show_disk_usage() {
    print_section "当前磁盘使用情况"
    
    # 检查 Docker 数据目录
    local docker_data_root=""
    if [ -f /etc/docker/daemon.json ]; then
        docker_data_root=$(python3 -c "import json; f=open('/etc/docker/daemon.json'); d=json.load(f); print(d.get('data-root', ''))" 2>/dev/null || echo "")
    fi
    
    if [ -z "$docker_data_root" ]; then
        if [ -d "/var/lib/docker" ]; then
            docker_data_root="/var/lib/docker"
        elif [ -d "/var/snap/docker/common/var-lib-docker" ]; then
            docker_data_root="/var/snap/docker/common/var-lib-docker"
        fi
    fi
    
    if [ -n "$docker_data_root" ]; then
        print_info "Docker 数据目录: $docker_data_root"
        df -h "$docker_data_root" 2>/dev/null | tail -1 | awk '{print "  总空间: " $2 ", 已用: " $3 " (" $5 "), 可用: " $4}'
    fi
    
    # 检查 /run (tmpfs)
    if [ -d "/run" ]; then
        print_info "/run (tmpfs):"
        df -h "/run" 2>/dev/null | tail -1 | awk '{print "  总空间: " $2 ", 已用: " $3 " (" $5 "), 可用: " $4}'
    fi
    
    # 检查根文件系统
    print_info "根文件系统 (/):"
    df -h "/" 2>/dev/null | tail -1 | awk '{print "  总空间: " $2 ", 已用: " $3 " (" $5 "), 可用: " $4}'
}

# 显示 Docker 资源使用情况
show_docker_usage() {
    print_section "Docker 资源使用情况"
    
    # 镜像
    local image_count=$(docker images -q | wc -l)
    local image_size=$(docker images --format "{{.Size}}" | awk '{sum+=$1} END {print sum}' 2>/dev/null || echo "未知")
    print_info "镜像数量: $image_count"
    print_info "镜像总大小: $image_size"
    
    # 容器
    local container_count=$(docker ps -aq | wc -l)
    local running_count=$(docker ps -q | wc -l)
    print_info "容器数量: $container_count (运行中: $running_count)"
    
    # 卷
    local volume_count=$(docker volume ls -q | wc -l)
    print_info "数据卷数量: $volume_count"
    
    # 网络
    local network_count=$(docker network ls -q | wc -l)
    print_info "网络数量: $network_count"
    
    # 系统磁盘使用
    print_info "Docker 系统磁盘使用:"
    docker system df 2>/dev/null || print_warning "无法获取 Docker 系统磁盘使用情况"
}

# 清理未使用的容器
cleanup_containers() {
    print_section "清理未使用的容器"
    
    local stopped_containers=$(docker ps -a -f "status=exited" -q | wc -l)
    if [ "$stopped_containers" -eq 0 ]; then
        print_info "没有已停止的容器需要清理"
        return 0
    fi
    
    print_info "发现 $stopped_containers 个已停止的容器"
    print_warning "这将删除所有已停止的容器"
    
    while true; do
        echo -ne "${YELLOW}[提示]${NC} 是否继续？(y/N): "
        read -r response
        case "$response" in
            [yY][eE][sS]|[yY])
                if docker container prune -f; then
                    print_success "已清理未使用的容器"
                    return 0
                else
                    print_error "清理容器失败"
                    return 1
                fi
                ;;
            [nN][oO]|[nN]|"")
                print_info "已跳过容器清理"
                return 0
                ;;
            *)
                print_warning "请输入 y 或 N"
                ;;
        esac
    done
}

# 清理未使用的镜像
cleanup_images() {
    print_section "清理未使用的镜像"
    
    local dangling_images=$(docker images -f "dangling=true" -q | wc -l)
    if [ "$dangling_images" -eq 0 ]; then
        print_info "没有悬空镜像需要清理"
    else
        print_info "发现 $dangling_images 个悬空镜像"
    fi
    
    print_warning "这将删除所有未使用的镜像（包括所有未使用的镜像，不仅仅是悬空镜像）"
    print_warning "注意：这可能会删除一些正在使用的镜像的旧版本"
    
    while true; do
        echo -ne "${YELLOW}[提示]${NC} 是否继续？(y/N): "
        read -r response
        case "$response" in
            [yY][eE][sS]|[yY])
                if docker image prune -a -f; then
                    print_success "已清理未使用的镜像"
                    return 0
                else
                    print_error "清理镜像失败"
                    return 1
                fi
                ;;
            [nN][oO]|[nN]|"")
                print_info "已跳过镜像清理"
                return 0
                ;;
            *)
                print_warning "请输入 y 或 N"
                ;;
        esac
    done
}

# 清理未使用的卷
cleanup_volumes() {
    print_section "清理未使用的数据卷"
    
    local unused_volumes=$(docker volume ls -f "dangling=true" -q | wc -l)
    if [ "$unused_volumes" -eq 0 ]; then
        print_info "没有未使用的数据卷需要清理"
        return 0
    fi
    
    print_info "发现 $unused_volumes 个未使用的数据卷"
    print_warning "注意：删除数据卷会永久删除其中的数据，请确保没有重要数据"
    
    while true; do
        echo -ne "${YELLOW}[提示]${NC} 是否继续？(y/N): "
        read -r response
        case "$response" in
            [yY][eE][sS]|[yY])
                if docker volume prune -f; then
                    print_success "已清理未使用的数据卷"
                    return 0
                else
                    print_error "清理数据卷失败"
                    return 1
                fi
                ;;
            [nN][oO]|[nN]|"")
                print_info "已跳过数据卷清理"
                return 0
                ;;
            *)
                print_warning "请输入 y 或 N"
                ;;
        esac
    done
}

# 清理未使用的网络
cleanup_networks() {
    print_section "清理未使用的网络"
    
    if docker network prune -f; then
        print_success "已清理未使用的网络"
        return 0
    else
        print_error "清理网络失败"
        return 1
    fi
}

# 全面清理（一键清理所有未使用的资源）
cleanup_all() {
    print_section "全面清理 Docker 资源"
    
    print_warning "这将清理所有未使用的 Docker 资源："
    print_info "  - 已停止的容器"
    print_info "  - 未使用的镜像"
    print_info "  - 未使用的数据卷"
    print_info "  - 未使用的网络"
    print_info "  - 构建缓存"
    echo ""
    print_warning "注意：这可能会删除一些数据，请确保没有重要数据"
    
    while true; do
        echo -ne "${YELLOW}[提示]${NC} 是否继续？(y/N): "
        read -r response
        case "$response" in
            [yY][eE][sS]|[yY])
                print_info "开始全面清理..."
                if docker system prune -a --volumes -f; then
                    print_success "全面清理完成"
                    return 0
                else
                    print_error "全面清理失败"
                    return 1
                fi
                ;;
            [nN][oO]|[nN]|"")
                print_info "已取消全面清理"
                return 0
                ;;
            *)
                print_warning "请输入 y 或 N"
                ;;
        esac
    done
}

# 清理构建缓存
cleanup_build_cache() {
    print_section "清理构建缓存"
    
    if docker builder prune -a -f; then
        print_success "已清理构建缓存"
        return 0
    else
        print_error "清理构建缓存失败"
        return 1
    fi
}

# 主函数
main() {
    print_section "Docker 磁盘空间清理工具"
    
    check_docker
    
    show_disk_usage
    show_docker_usage
    
    echo ""
    print_info "请选择清理操作："
    echo "  1. 清理未使用的容器"
    echo "  2. 清理未使用的镜像"
    echo "  3. 清理未使用的数据卷"
    echo "  4. 清理未使用的网络"
    echo "  5. 清理构建缓存"
    echo "  6. 全面清理（推荐，清理所有未使用的资源）"
    echo "  7. 退出"
    echo ""
    
    while true; do
        echo -ne "${YELLOW}[提示]${NC} 请输入选项 (1-7): "
        read -r choice
        
        case "$choice" in
            1)
                cleanup_containers
                show_docker_usage
                ;;
            2)
                cleanup_images
                show_docker_usage
                ;;
            3)
                cleanup_volumes
                show_docker_usage
                ;;
            4)
                cleanup_networks
                show_docker_usage
                ;;
            5)
                cleanup_build_cache
                show_docker_usage
                ;;
            6)
                cleanup_all
                show_disk_usage
                show_docker_usage
                ;;
            7)
                print_info "退出清理工具"
                exit 0
                ;;
            *)
                print_warning "无效选项，请输入 1-7"
                ;;
        esac
        echo ""
    done
}

# 运行主函数
main "$@"

