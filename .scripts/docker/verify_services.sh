#!/bin/bash

# ============================================
# Docker Compose 服务验证脚本
# ============================================
# 用于验证 docker-compose.yml 中定义的所有服务是否正常启动
# 使用方法：
#   ./verify_services.sh
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 统计变量
TOTAL_SERVICES=0
RUNNING_SERVICES=0
HEALTHY_SERVICES=0
FAILED_SERVICES=0

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

# 检查端口连通性
check_port() {
    local host=$1
    local port=$2
    local service_name=$3
    
    if command -v nc &> /dev/null; then
        if nc -z -w 2 "$host" "$port" 2>/dev/null; then
            return 0
        fi
    elif command -v timeout &> /dev/null; then
        if timeout 2 bash -c "echo > /dev/tcp/$host/$port" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# 验证单个服务
verify_service() {
    local service_name=$1
    local container_name=$2
    local ports=$3
    local healthcheck_cmd=$4
    
    TOTAL_SERVICES=$((TOTAL_SERVICES + 1))
    
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}检查服务: $service_name${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # 检查容器是否存在
    if ! docker ps -a --format "{{.Names}}" | grep -q "^${container_name}$"; then
        print_error "容器 $container_name 不存在"
        print_info "请先启动服务: docker-compose up -d $service_name"
        FAILED_SERVICES=$((FAILED_SERVICES + 1))
        return 1
    fi
    
    # 检查容器运行状态
    local container_status=$(docker ps --filter "name=${container_name}" --format "{{.Status}}" 2>/dev/null | head -1 || echo "")
    if [ -z "$container_status" ]; then
        print_warning "容器 $container_name 存在但未运行"
        print_info "容器状态: $(docker ps -a --filter "name=${container_name}" --format "{{.Status}}" 2>/dev/null | head -1)"
        FAILED_SERVICES=$((FAILED_SERVICES + 1))
        return 1
    fi
    
    RUNNING_SERVICES=$((RUNNING_SERVICES + 1))
    print_success "容器正在运行"
    print_info "容器状态: $container_status"
    
    # 检查健康状态
    local health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "none")
    if [ "$health_status" = "healthy" ]; then
        HEALTHY_SERVICES=$((HEALTHY_SERVICES + 1))
        print_success "健康检查: 健康"
    elif [ "$health_status" = "starting" ]; then
        print_warning "健康检查: 启动中..."
    elif [ "$health_status" = "unhealthy" ]; then
        print_error "健康检查: 不健康"
        print_info "查看日志: docker logs $container_name"
    else
        print_info "健康检查: 未配置或不可用"
    fi
    
    # 检查端口连通性
    if [ -n "$ports" ]; then
        print_info "检查端口连通性..."
        local port_ok=0
        local port_failed=0
        IFS=',' read -ra PORT_ARRAY <<< "$ports"
        for port in "${PORT_ARRAY[@]}"; do
            port=$(echo "$port" | xargs) # 去除空格
            if [ -n "$port" ]; then
                if check_port "127.0.0.1" "$port" "$service_name"; then
                    print_success "端口 $port 可达"
                    port_ok=$((port_ok + 1))
                else
                    print_warning "端口 $port 不可达"
                    port_failed=$((port_failed + 1))
                fi
            fi
        done
        
        if [ $port_failed -gt 0 ] && [ $port_ok -eq 0 ]; then
            print_warning "所有端口都不可达，服务可能未完全启动"
        fi
    fi
    
    # 执行自定义健康检查命令（如果提供）
    if [ -n "$healthcheck_cmd" ]; then
        print_info "执行自定义健康检查..."
        if eval "$healthcheck_cmd" > /dev/null 2>&1; then
            print_success "自定义健康检查通过"
        else
            print_warning "自定义健康检查失败"
        fi
    fi
    
    return 0
}

print_section "Docker Compose 服务验证工具"

# 检查 Docker 是否运行
print_info "检查 Docker 服务状态..."
if ! docker ps &> /dev/null; then
    print_error "无法访问 Docker，请确保 Docker 服务正在运行"
    exit 1
fi
print_success "Docker 服务正在运行"

# 检查 docker-compose.yml 是否存在
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml 文件不存在"
    exit 1
fi
print_success "找到 docker-compose.yml 文件"

# 检查 Docker 网络
print_info "检查 Docker 网络..."
if docker network ls --format "{{.Name}}" | grep -q "^easyaiot-network$"; then
    print_success "网络 easyaiot-network 存在"
else
    print_warning "网络 easyaiot-network 不存在"
    print_info "创建网络: docker network create easyaiot-network"
fi

print_section "开始验证服务"

# 验证各个服务
# Nacos
verify_service "Nacos" "nacos-server" "8848,9848,9849" \
    "curl -f http://127.0.0.1:8848/nacos/actuator/health > /dev/null 2>&1"

# PostgreSQL
verify_service "PostgreSQL" "postgres-server" "5432" \
    "docker exec postgres-server pg_isready -U postgres > /dev/null 2>&1"

# TDengine
verify_service "TDengine" "tdengine-server" "6030,6041,6060" \
    "docker exec tdengine-server taos -h localhost -s 'select 1;' > /dev/null 2>&1"

# Redis
verify_service "Redis" "redis-server" "6379" \
    "docker exec redis-server redis-cli -a 'basiclab@iot975248395' ping | grep -q PONG"

# Kafka
verify_service "Kafka" "kafka-server" "9092,9093" \
    "docker exec kafka-server kafka-broker-api-versions.sh --bootstrap-server localhost:9092 > /dev/null 2>&1"

# MinIO
verify_service "MinIO" "minio-server" "9000,9001" \
    "curl -f http://127.0.0.1:9000/minio/health/live > /dev/null 2>&1"

# SRS
verify_service "SRS" "srs-server" "1935,1985,8080" \
    "curl -f http://127.0.0.1:1985/api/v1/versions > /dev/null 2>&1"

# NodeRED
verify_service "NodeRED" "nodered-server" "1880" \
    "curl -f http://127.0.0.1:1880/ > /dev/null 2>&1"

# EMQX
verify_service "EMQX" "emqx-server" "1883,8883,8083,8084,18083" \
    "docker exec emqx-server /opt/emqx/bin/emqx ctl status > /dev/null 2>&1"

# 显示总结
print_section "验证总结"

echo -e "${CYAN}服务统计:${NC}"
echo -e "  总服务数: ${TOTAL_SERVICES}"
echo -e "  运行中: ${GREEN}${RUNNING_SERVICES}${NC}"
echo -e "  健康: ${GREEN}${HEALTHY_SERVICES}${NC}"
echo -e "  失败: ${RED}${FAILED_SERVICES}${NC}"
echo ""

if [ $FAILED_SERVICES -eq 0 ] && [ $RUNNING_SERVICES -eq $TOTAL_SERVICES ]; then
    print_success "所有服务运行正常！"
    echo ""
    print_info "快速命令："
    print_info "  查看所有容器状态: docker ps"
    print_info "  查看服务日志: docker-compose logs [服务名]"
    print_info "  重启服务: docker-compose restart [服务名]"
    exit 0
else
    print_warning "部分服务存在问题"
    echo ""
    print_info "故障排查："
    print_info "  1. 查看容器状态: docker ps -a"
    print_info "  2. 查看容器日志: docker logs [容器名]"
    print_info "  3. 启动所有服务: docker-compose up -d"
    print_info "  4. 重启特定服务: docker-compose restart [服务名]"
    print_info "  5. 检查网络: docker network inspect easyaiot-network"
    exit 1
fi

