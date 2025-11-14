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
    local compose_file="$(dirname "$0")/docker-compose.yml"
    
    print_section "修复Docker网络"
    
    # 检查是否存在 docker-compose.yml
    if [ -f "$compose_file" ]; then
        print_info "检测到 docker-compose.yml，先停止所有容器并清理..."
        cd "$(dirname "$compose_file")"
        
        # 停止并删除所有容器（这会清理 docker-compose 的网络缓存）
        print_info "执行 docker-compose down 清理容器和网络连接..."
        docker-compose down 2>/dev/null || true
        sleep 2
    fi
    
    # 检查网络是否存在
    if ! docker network ls | grep -q "$network_name"; then
        print_info "网络 $network_name 不存在，正在创建..."
        if docker network create "$network_name" 2>/dev/null; then
            print_success "网络 $network_name 已创建"
            echo ""
            print_success "网络修复完成！"
            if [ -f "$compose_file" ]; then
                print_info "请重新启动相关容器："
                print_info "  cd $(dirname "$compose_file") && docker-compose up -d"
            fi
            echo ""
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
        
        # 如果已经执行了 docker-compose down，容器应该已经停止
        # 但可能还有残留连接，需要手动断开
        print_info "正在断开所有容器的网络连接..."
        echo "$containers" | tr ' ' '\n' | grep -v '^$' | while read -r container; do
            if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
                print_info "断开容器网络连接: $container"
                docker network disconnect -f "$network_name" "$container" 2>/dev/null || true
            fi
        done
        sleep 2
    fi
    
    # 删除旧网络
    print_info "删除旧网络 $network_name..."
    if docker network rm "$network_name" 2>/dev/null; then
        print_success "旧网络已删除"
    else
        print_warning "删除网络失败，可能仍有容器在使用"
        print_info "尝试强制断开所有连接并删除..."
        # 再次尝试断开所有容器
        if [ -n "$containers" ]; then
            echo "$containers" | tr ' ' '\n' | grep -v '^$' | while read -r container; do
                docker network disconnect -f "$network_name" "$container" 2>/dev/null || true
            done
        fi
        sleep 2
        
        # 尝试删除网络（可能需要多次尝试）
        local retry_count=0
        while [ $retry_count -lt 3 ]; do
            if docker network rm "$network_name" 2>/dev/null; then
                print_success "旧网络已删除"
                break
            else
                retry_count=$((retry_count + 1))
                if [ $retry_count -lt 3 ]; then
                    print_info "重试删除网络 (${retry_count}/3)..."
                    sleep 2
                else
                    print_error "无法删除网络，请手动检查并删除："
                    print_error "  docker network rm $network_name"
                    exit 1
                fi
            fi
        done
    fi
    
    sleep 2
    
    # 清理 docker-compose 的网络缓存（如果存在）
    if [ -f "$compose_file" ]; then
        print_info "清理 docker-compose 网络缓存..."
        cd "$(dirname "$compose_file")"
        # 清理未使用的网络（这会清除 docker-compose 可能缓存的网络引用）
        docker network prune -f > /dev/null 2>&1 || true
        # 强制 docker-compose 重新读取配置（通过验证配置）
        docker-compose config > /dev/null 2>&1 || true
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
    if [ -f "$compose_file" ]; then
        print_info "请重新启动相关容器："
        print_info "  cd $(dirname "$compose_file") && docker-compose up -d"
    fi
    echo ""
}

# 主函数
main() {
    check_docker
    fix_network
}

# 运行主函数
main "$@"

