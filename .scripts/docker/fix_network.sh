#!/bin/bash

# ============================================
# Docker网络修复和Compose缓存清理脚本
# 用于修复IP变化后容器无法加入网络的问题
# 并清理 DEVICE、VIDEO、AI 目录下的 compose 缓存
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
    
    print_success "网络修复完成！"
}

# 清理单个目录的 compose 缓存
clean_compose_cache() {
    local dir_path="$1"
    local compose_file=""
    
    # 查找 compose 文件
    if [ -f "$dir_path/docker-compose.yml" ]; then
        compose_file="$dir_path/docker-compose.yml"
    elif [ -f "$dir_path/docker-compose.yaml" ]; then
        compose_file="$dir_path/docker-compose.yaml"
    else
        print_warning "目录 $dir_path 中未找到 docker-compose 文件，跳过"
        return 0
    fi
    
    print_info "清理 $dir_path 的 compose 缓存..."
    
    cd "$dir_path"
    
    # 1. 停止并清理容器和网络连接
    print_info "执行 docker-compose down 清理容器和网络连接..."
    if docker-compose -f "$(basename "$compose_file")" down 2>/dev/null; then
        print_success "容器和网络连接已清理"
    else
        print_warning "docker-compose down 执行失败或没有运行的容器"
    fi
    sleep 2
    
    # 2. 强制重新读取配置（这会清除 docker-compose 的配置缓存）
    print_info "强制重新读取配置以清除缓存..."
    if docker-compose -f "$(basename "$compose_file")" config > /dev/null 2>&1; then
        print_success "配置已重新验证"
    else
        print_warning "配置验证失败，但继续执行"
    fi
    
    # 3. 清理可能的网络残留连接
    print_info "检查并清理网络残留连接..."
    local network_name="easyaiot-network"
    if docker network inspect "$network_name" &> /dev/null; then
        # 获取连接到该网络的所有容器
        local containers=$(docker network inspect "$network_name" --format '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null || echo "")
        
        # 检查是否有该目录相关的容器残留
        local dir_name=$(basename "$dir_path")
        if echo "$containers" | grep -q "$dir_name"; then
            print_info "发现残留的网络连接，正在清理..."
            echo "$containers" | tr ' ' '\n' | grep -v '^$' | grep "$dir_name" | while read -r container; do
                if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
                    print_info "断开容器网络连接: $container"
                    docker network disconnect -f "$network_name" "$container" 2>/dev/null || true
                fi
            done
        fi
    fi
    
    # 4. 清理 docker-compose 的临时文件（如果存在）
    print_info "清理 docker-compose 临时文件..."
    # docker-compose 可能会在项目目录下创建一些临时文件
    find . -name ".docker-compose.*" -type f -delete 2>/dev/null || true
    find . -name "docker-compose.override.yml" -type f -delete 2>/dev/null || true
    find . -name "docker-compose.override.yaml" -type f -delete 2>/dev/null || true
    
    print_success "$dir_path 的 compose 缓存已清理完成"
}

# 清理所有 compose 目录的缓存
clean_all_compose_cache() {
    # 获取脚本所在目录的父目录的父目录（项目根目录）
    local script_dir="$(cd "$(dirname "$0")" && pwd)"
    local project_root="${1:-$(dirname "$(dirname "$script_dir")")}"
    
    print_section "清理 DEVICE、VIDEO、AI 的 compose 缓存"
    
    # 清理各个目录
    local dirs=("$project_root/DEVICE" "$project_root/VIDEO" "$project_root/AI")
    
    for dir in "${dirs[@]}"; do
        if [ -d "$dir" ]; then
            clean_compose_cache "$dir"
            echo ""
        else
            print_warning "目录 $dir 不存在，跳过"
        fi
    done
    
    # 最后清理未使用的网络
    print_info "清理未使用的网络..."
    docker network prune -f > /dev/null 2>&1 || true
    print_success "未使用的网络已清理"
    
    print_success "所有 compose 缓存清理完成！"
}

# 主函数
main() {
    check_docker
    
    # 第一步：修复网络
    fix_network
    
    echo ""
    
    # 第二步：清理 compose 缓存
    clean_all_compose_cache
    
    echo ""
    print_section "修复完成总结"
    print_success "网络修复和缓存清理全部完成！"
    print_info "建议重新启动相关服务："
    echo "  cd .scripts/docker && docker-compose up -d"
    echo "  cd DEVICE && docker-compose up -d"
    echo "  cd VIDEO && docker-compose up -d"
    echo "  cd AI && docker-compose up -d"
    echo ""
}

# 运行主函数
main "$@"
