#!/bin/bash

# ============================================
# Docker网络修复脚本
# 用于修复IP变化后容器无法加入网络的问题
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 检查Docker是否运行
check_docker() {
    if ! docker info &> /dev/null; then
        print_error "Docker daemon 未运行或无法访问"
        exit 1
    fi
}

# 修复网络
fix_network() {
    local network_name="easyaiot-network"
    
    print_section "修复Docker网络"
    
    # 检查网络是否存在
    if ! docker network ls | grep -q "$network_name"; then
        print_info "网络 $network_name 不存在，正在创建..."
        if docker network create "$network_name" 2>/dev/null; then
            print_success "网络 $network_name 已创建"
            return 0
        else
            print_error "无法创建网络 $network_name"
            return 1
        fi
    fi
    
    print_info "网络 $network_name 已存在，检查网络状态..."
    
    # 获取连接到该网络的所有容器
    local containers=$(docker network inspect "$network_name" --format '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null || echo "")
    
    if [ -n "$containers" ]; then
        print_warning "以下容器正在使用该网络："
        echo "$containers" | tr ' ' '\n' | grep -v '^$' | while read -r container; do
            echo "  - $container"
        done
        echo ""
        
        print_warning "需要先停止这些容器才能重新创建网络"
        echo ""
        echo "请选择操作："
        echo "  1. 自动停止所有相关容器并重新创建网络（推荐）"
        echo "  2. 手动停止容器后重新运行此脚本"
        echo "  3. 取消操作"
        echo ""
        read -p "请输入选项 (1/2/3): " choice
        
        case "$choice" in
            1)
                print_info "正在停止所有相关容器..."
                echo "$containers" | tr ' ' '\n' | grep -v '^$' | while read -r container; do
                    if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
                        print_info "停止容器: $container"
                        docker stop "$container" 2>/dev/null || true
                    fi
                done
                sleep 2
                ;;
            2)
                print_info "请手动停止所有容器后重新运行此脚本"
                exit 0
                ;;
            3)
                print_info "已取消操作"
                exit 0
                ;;
            *)
                print_error "无效选项"
                exit 1
                ;;
        esac
    fi
    
    # 删除旧网络
    print_info "删除旧网络 $network_name..."
    if docker network rm "$network_name" 2>/dev/null; then
        print_success "旧网络已删除"
    else
        print_warning "删除网络失败，可能仍有容器在使用"
        print_info "尝试强制删除..."
        # 尝试断开所有容器
        echo "$containers" | tr ' ' '\n' | grep -v '^$' | while read -r container; do
            docker network disconnect -f "$network_name" "$container" 2>/dev/null || true
        done
        sleep 1
        docker network rm "$network_name" 2>/dev/null || {
            print_error "无法删除网络，请手动检查"
            exit 1
        }
    fi
    
    sleep 1
    
    # 重新创建网络
    print_info "重新创建网络 $network_name..."
    if docker network create "$network_name" 2>/dev/null; then
        print_success "网络 $network_name 已重新创建"
    else
        print_error "无法重新创建网络 $network_name"
        exit 1
    fi
    
    # 验证网络
    print_info "验证网络..."
    if docker run --rm --network "$network_name" alpine:latest ping -c 1 8.8.8.8 > /dev/null 2>&1; then
        print_success "网络验证成功"
    else
        print_warning "网络验证失败，但网络已创建"
    fi
    
    echo ""
    print_success "网络修复完成！"
    print_info "请重新启动相关容器："
    print_info "  cd .scripts/docker && docker-compose up -d"
    echo ""
}

# 主函数
main() {
    check_docker
    fix_network
}

# 运行主函数
main "$@"

