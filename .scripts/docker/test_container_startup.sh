#!/bin/bash

# ============================================
# Docker 容器启动测试脚本
# ============================================
# 用于测试 docker-compose.yml 中定义的服务是否能正常启动
# 使用方法：
#   ./test_container_startup.sh [选项] [服务名]
#
# 选项：
#   -a, --all           测试所有服务（默认）
#   -s, --service       测试指定服务
#   -c, --cleanup       测试后清理（停止并删除容器）
#   -t, --timeout       设置启动超时时间（秒，默认120）
#   -v, --verbose       详细输出模式
#   -h, --help          显示帮助信息
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

# 默认选项
TEST_ALL=true
SERVICE_NAME=""
CLEANUP_AFTER_TEST=false
TIMEOUT=120
VERBOSE=false

# 统计变量
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# 测试结果数组
declare -a TEST_RESULTS

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

print_verbose() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}[VERBOSE]${NC} $1"
    fi
}

# 显示帮助信息
show_help() {
    echo "Docker 容器启动测试脚本"
    echo ""
    echo "用法: $0 [选项] [服务名]"
    echo ""
    echo "选项:"
    echo "  -a, --all           测试所有服务（默认）"
    echo "  -s, --service NAME  测试指定服务"
    echo "  -c, --cleanup       测试后清理（停止并删除容器）"
    echo "  -t, --timeout SEC   设置启动超时时间（秒，默认120）"
    echo "  -v, --verbose       详细输出模式"
    echo "  -h, --help          显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                          # 测试所有服务"
    echo "  $0 -s Redis                  # 只测试 Redis 服务"
    echo "  $0 -s PostgresSQL -c         # 测试 PostgreSQL 并在测试后清理"
    echo "  $0 -a -t 180                 # 测试所有服务，超时时间180秒"
    exit 0
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--all)
            TEST_ALL=true
            shift
            ;;
        -s|--service)
            TEST_ALL=false
            SERVICE_NAME="$2"
            shift 2
            ;;
        -c|--cleanup)
            CLEANUP_AFTER_TEST=true
            shift
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            ;;
        *)
            if [ -z "$SERVICE_NAME" ] && [ "$TEST_ALL" = false ]; then
                SERVICE_NAME="$1"
            else
                echo "未知选项: $1"
                echo "使用 -h 或 --help 查看帮助信息"
                exit 1
            fi
            shift
            ;;
    esac
done

# 检查 Docker 是否运行
check_docker() {
    print_info "检查 Docker 服务状态..."
    if ! docker ps &> /dev/null; then
        print_error "无法访问 Docker，请确保 Docker 服务正在运行"
        exit 1
    fi
    print_success "Docker 服务正在运行"
}

# 检查 Docker Compose
check_docker_compose() {
    print_info "检查 Docker Compose..."
    
    # 检查 docker compose (v2)
    if docker compose version &> /dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
        print_success "Docker Compose v2 可用"
        return 0
    fi
    
    # 检查 docker-compose (v1)
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
        print_success "Docker Compose v1 可用"
        return 0
    fi
    
    print_error "Docker Compose 未安装或不可用"
    exit 1
}

# 检查 docker-compose.yml 文件
check_compose_file() {
    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml 文件不存在"
        exit 1
    fi
    print_success "找到 docker-compose.yml 文件"
}

# 检查并创建 Docker 网络
check_network() {
    print_info "检查 Docker 网络..."
    if docker network ls --format "{{.Name}}" | grep -q "^easyaiot-network$"; then
        print_success "网络 easyaiot-network 已存在"
    else
        print_warning "网络 easyaiot-network 不存在，正在创建..."
        if docker network create easyaiot-network &> /dev/null; then
            print_success "网络 easyaiot-network 创建成功"
        else
            print_error "网络创建失败"
            exit 1
        fi
    fi
}

# 获取服务列表
get_service_list() {
    if [ "$TEST_ALL" = true ]; then
        # 获取所有服务名称（排除 init 服务）
        $COMPOSE_CMD config --services 2>/dev/null | grep -v "init$" || echo ""
    else
        echo "$SERVICE_NAME"
    fi
}

# 测试单个服务启动
test_service_startup() {
    local service_name=$1
    local container_name=""
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}测试服务: $service_name${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # 获取容器名称（从 docker-compose.yml 配置中提取）
    container_name=$($COMPOSE_CMD config 2>/dev/null | \
        awk -v service="$service_name" '
        BEGIN { in_service=0 }
        /^  [A-Za-z-]+:/ { 
            current_service=$1; 
            gsub(/:/, "", current_service); 
            in_service=(current_service==service ? 1 : 0);
            next
        }
        in_service && /container_name:/ { 
            gsub(/container_name:/, "", $0);
            gsub(/[" ]/, "", $0);
            print $0;
            exit
        }' | head -1)
    
    # 如果还是找不到，根据服务名推断容器名（基于 docker-compose.yml 的命名规则）
    if [ -z "$container_name" ]; then
        case "$service_name" in
            Nacos) container_name="nacos-server" ;;
            PostgresSQL) container_name="postgres-server" ;;
            TDengine) container_name="tdengine-server" ;;
            Redis) container_name="redis-server" ;;
            Kafka) container_name="kafka-server" ;;
            MinIO) container_name="minio-server" ;;
            SRS) container_name="srs-server" ;;
            NodeRED) container_name="nodered-server" ;;
            EMQX) container_name="emqx-server" ;;
            *) container_name="${service_name,,}-server" ;;  # 转换为小写并添加 -server
        esac
        print_verbose "无法从配置中获取容器名，使用推断名称: $container_name"
    fi
    
    print_verbose "容器名称: $container_name"
    
    # 检查容器是否已存在
    local existing_container=$(docker ps -a --filter "name=^${container_name}$" --format "{{.Names}}" 2>/dev/null | head -1)
    if [ -n "$existing_container" ]; then
        print_warning "容器 $container_name 已存在"
        print_info "停止并删除现有容器..."
        $COMPOSE_CMD stop "$service_name" 2>/dev/null || true
        $COMPOSE_CMD rm -f "$service_name" 2>/dev/null || true
        sleep 2
    fi
    
    # 尝试启动服务
    print_info "启动服务 $service_name..."
    local start_result=0
    local start_output=""
    
    if [ "$VERBOSE" = true ]; then
        start_output=$($COMPOSE_CMD up -d "$service_name" 2>&1)
        start_result=$?
        echo "$start_output"
    else
        start_output=$($COMPOSE_CMD up -d "$service_name" 2>&1)
        start_result=$?
    fi
    
    if [ $start_result -ne 0 ]; then
        print_error "服务启动失败"
        print_verbose "启动输出: $start_output"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        TEST_RESULTS+=("FAIL: $service_name - 启动命令失败")
        return 1
    fi
    
    print_success "启动命令执行成功"
    
    # 等待容器启动
    print_info "等待容器启动（最多 ${TIMEOUT} 秒）..."
    local elapsed=0
    local interval=2
    local container_running=false
    
    while [ $elapsed -lt $TIMEOUT ]; do
        if docker ps --filter "name=^${container_name}$" --format "{{.Names}}" | grep -q "^${container_name}$"; then
            local status=$(docker ps --filter "name=^${container_name}$" --format "{{.Status}}" 2>/dev/null | head -1)
            if [ -n "$status" ]; then
                container_running=true
                print_success "容器已启动"
                print_info "容器状态: $status"
                break
            fi
        fi
        
        sleep $interval
        elapsed=$((elapsed + interval))
        
        if [ "$VERBOSE" = true ]; then
            echo -ne "\r${BLUE}[INFO]${NC} 等待中... ${elapsed}/${TIMEOUT} 秒"
        fi
    done
    
    if [ "$VERBOSE" = true ]; then
        echo ""
    fi
    
    if [ "$container_running" = false ]; then
        print_error "容器启动超时"
        print_info "检查容器状态..."
        local container_status=$(docker ps -a --filter "name=^${container_name}$" --format "{{.Status}}" 2>/dev/null | head -1)
        if [ -n "$container_status" ]; then
            print_info "容器状态: $container_status"
            print_info "查看日志: docker logs $container_name"
        fi
        FAILED_TESTS=$((FAILED_TESTS + 1))
        TEST_RESULTS+=("FAIL: $service_name - 启动超时")
        return 1
    fi
    
    # 检查容器是否在运行（不是退出状态）
    local exit_code=$(docker inspect --format='{{.State.ExitCode}}' "$container_name" 2>/dev/null || echo "1")
    if [ "$exit_code" != "0" ]; then
        print_error "容器已退出，退出码: $exit_code"
        print_info "查看日志: docker logs $container_name"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        TEST_RESULTS+=("FAIL: $service_name - 容器退出（退出码: $exit_code）")
        return 1
    fi
    
    # 检查健康状态（如果配置了健康检查）
    local health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "none")
    if [ "$health_status" = "healthy" ]; then
        print_success "健康检查: 健康"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        TEST_RESULTS+=("PASS: $service_name - 启动成功且健康")
    elif [ "$health_status" = "starting" ]; then
        print_warning "健康检查: 启动中（容器已运行）"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        TEST_RESULTS+=("PASS: $service_name - 启动成功（健康检查进行中）")
    elif [ "$health_status" = "unhealthy" ]; then
        print_warning "健康检查: 不健康（但容器在运行）"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        TEST_RESULTS+=("WARN: $service_name - 启动成功但健康检查失败")
    else
        print_success "容器运行正常（未配置健康检查）"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        TEST_RESULTS+=("PASS: $service_name - 启动成功")
    fi
    
    return 0
}

# 清理测试环境
cleanup_test() {
    if [ "$CLEANUP_AFTER_TEST" = false ]; then
        return 0
    fi
    
    print_section "清理测试环境"
    
    local services=$(get_service_list)
    for service in $services; do
        print_info "停止并删除服务: $service"
        $COMPOSE_CMD stop "$service" 2>/dev/null || true
        $COMPOSE_CMD rm -f "$service" 2>/dev/null || true
    done
    
    print_success "清理完成"
}

# 显示测试总结
show_summary() {
    print_section "测试总结"
    
    echo -e "${CYAN}测试统计:${NC}"
    echo -e "  总测试数: ${TOTAL_TESTS}"
    echo -e "  通过: ${GREEN}${PASSED_TESTS}${NC}"
    echo -e "  失败: ${RED}${FAILED_TESTS}${NC}"
    echo -e "  跳过: ${YELLOW}${SKIPPED_TESTS}${NC}"
    echo ""
    
    if [ ${#TEST_RESULTS[@]} -gt 0 ]; then
        echo -e "${CYAN}详细结果:${NC}"
        for result in "${TEST_RESULTS[@]}"; do
            if [[ "$result" == PASS:* ]]; then
                echo -e "  ${GREEN}✓${NC} $result"
            elif [[ "$result" == WARN:* ]]; then
                echo -e "  ${YELLOW}⚠${NC} $result"
            elif [[ "$result" == FAIL:* ]]; then
                echo -e "  ${RED}✗${NC} $result"
            else
                echo -e "  $result"
            fi
        done
        echo ""
    fi
    
    if [ $FAILED_TESTS -eq 0 ] && [ $PASSED_TESTS -gt 0 ]; then
        print_success "所有测试通过！"
        echo ""
        print_info "快速命令："
        print_info "  查看所有容器: docker ps"
        print_info "  查看服务日志: $COMPOSE_CMD logs [服务名]"
        print_info "  停止所有服务: $COMPOSE_CMD down"
        return 0
    elif [ $FAILED_TESTS -gt 0 ]; then
        print_error "部分测试失败"
        echo ""
        print_info "故障排查："
        print_info "  1. 查看容器状态: docker ps -a"
        print_info "  2. 查看容器日志: docker logs [容器名]"
        print_info "  3. 检查端口占用: netstat -tuln | grep [端口]"
        print_info "  4. 检查磁盘空间: df -h"
        print_info "  5. 检查 Docker 日志: journalctl -u docker"
        return 1
    else
        print_warning "没有执行任何测试"
        return 1
    fi
}

# 主函数
main() {
    print_section "Docker 容器启动测试工具"
    
    # 检查前置条件
    check_docker
    check_docker_compose
    check_compose_file
    check_network
    
    # 获取要测试的服务列表
    local services=$(get_service_list)
    
    if [ -z "$services" ]; then
        print_error "没有找到要测试的服务"
        if [ "$TEST_ALL" = false ] && [ -n "$SERVICE_NAME" ]; then
            print_info "服务 '$SERVICE_NAME' 不存在于 docker-compose.yml 中"
            print_info "可用的服务列表："
            $COMPOSE_CMD config --services 2>/dev/null | sed 's/^/  - /' || true
        fi
        exit 1
    fi
    
    print_section "开始测试服务启动"
    
    if [ "$TEST_ALL" = true ]; then
        print_info "测试模式: 所有服务"
    else
        print_info "测试模式: 单个服务 ($SERVICE_NAME)"
    fi
    print_info "超时时间: ${TIMEOUT} 秒"
    print_info "清理模式: $([ "$CLEANUP_AFTER_TEST" = true ] && echo "启用" || echo "禁用")"
    echo ""
    
    # 测试每个服务
    for service in $services; do
        test_service_startup "$service"
    done
    
    # 显示总结
    show_summary
    local exit_code=$?
    
    # 清理测试环境
    cleanup_test
    
    exit $exit_code
}

# 执行主函数
main "$@"

