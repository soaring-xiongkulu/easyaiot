#!/bin/bash

# ============================================
# VIDEO服务 Docker Compose 管理脚本
# ============================================
# 使用方法：
#   ./install_all.sh [命令]
#
# 可用命令：
#   install    - 安装并启动服务（首次运行）
#   start      - 启动服务
#   stop       - 停止服务
#   restart    - 重启服务
#   status     - 查看服务状态
#   logs       - 查看服务日志
#   build      - 重新构建镜像
#   clean      - 清理容器和镜像
#   update     - 更新并重启服务
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

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

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

# 检查 Docker 是否安装
check_docker() {
    if ! check_command docker; then
        print_error "Docker 未安装，请先安装 Docker"
        echo "安装指南: https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker 已安装: $(docker --version)"
}

# 检查 Docker Compose 是否安装
check_docker_compose() {
    # 先检查 docker-compose 命令
    if check_command docker-compose; then
        COMPOSE_CMD="docker-compose"
        print_success "Docker Compose 已安装: $(docker-compose --version)"
        return 0
    fi
    
    # 再检查 docker compose 插件
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
        print_success "Docker Compose 已安装: $(docker compose version)"
        return 0
    fi
    
    # 如果都不存在，报错
    print_error "Docker Compose 未安装，请先安装 Docker Compose"
    echo "安装指南: https://docs.docker.com/compose/install/"
    exit 1
}

# 检查并创建 Docker 网络（注意：使用host网络模式后，此函数不再需要，但保留以兼容其他服务）
check_network() {
    print_info "检查 Docker 网络 easyaiot-network..."
    print_info "注意：VIDEO服务使用host网络模式，不需要加入easyaiot-network网络"
    print_info "但中间件服务仍需要此网络，检查网络是否存在..."
    if ! docker network ls | grep -q easyaiot-network; then
        print_info "网络 easyaiot-network 不存在，正在创建..."
        if docker network create easyaiot-network 2>/dev/null; then
            print_success "网络 easyaiot-network 已创建"
        else
            print_error "无法创建网络 easyaiot-network"
            exit 1
        fi
    else
        print_info "网络 easyaiot-network 已存在"
    fi
}

# 创建必要的目录
create_directories() {
    print_info "创建必要的目录..."
    mkdir -p data/uploads
    mkdir -p data/datasets
    mkdir -p data/models
    mkdir -p data/inference_results
    mkdir -p static/models
    mkdir -p temp_uploads
    mkdir -p model
    print_success "目录创建完成"
}

# 创建 .env.docker 文件（用于Docker部署）
create_env_file() {
    if [ ! -f .env.docker ]; then
        print_info ".env.docker 文件不存在，正在创建..."
        if [ -f env.example ]; then
            cp env.example .env.docker
            print_success ".env.docker 文件已从 env.example 创建"
            
            # 自动配置中间件连接信息（使用localhost，因为使用host网络模式）
            print_info "自动配置中间件连接信息（使用host网络模式，通过localhost访问中间件）..."
            
            # 更新数据库连接（使用localhost，因为使用host网络模式）
            sed -i 's|^DATABASE_URL=.*|DATABASE_URL=postgresql://postgres:iot45722414822@localhost:5432/iot-video20|' .env.docker
            
            # 更新Nacos配置（使用localhost，因为使用host网络模式）
            sed -i 's|^NACOS_SERVER=.*|NACOS_SERVER=localhost:8848|' .env.docker
            
            # 更新MinIO配置（使用localhost，因为使用host网络模式）
            sed -i 's|^MINIO_ENDPOINT=.*|MINIO_ENDPOINT=localhost:9000|' .env.docker
            sed -i 's|^MINIO_SECRET_KEY=.*|MINIO_SECRET_KEY=basiclab@iot975248395|' .env.docker
            
            # 更新Redis配置（使用localhost，因为使用host网络模式）
            sed -i 's|^REDIS_HOST=.*|REDIS_HOST=localhost|' .env.docker
            
            # 更新Kafka配置（使用localhost，因为使用host网络模式）
            sed -i 's|^KAFKA_BOOTSTRAP_SERVERS=.*|KAFKA_BOOTSTRAP_SERVERS=localhost:9092|' .env.docker
            
            # 更新TDengine配置（使用localhost，因为使用host网络模式）
            sed -i 's|^TDENGINE_HOST=.*|TDENGINE_HOST=localhost|' .env.docker
            
            # 更新Nacos密码
            sed -i 's|^NACOS_PASSWORD=.*|NACOS_PASSWORD=basiclab@iot78475418754|' .env.docker
            
            print_success "中间件连接信息已自动配置（使用host网络模式）"
            print_info "注意：使用host网络模式后，容器可以直接访问宿主机局域网，支持ONVIF摄像头发现"
            print_info "如需修改其他配置，请编辑 .env.docker 文件"
        else
            print_error "env.example 文件不存在，无法创建 .env.docker 文件"
            exit 1
        fi
    else
        print_info ".env.docker 文件已存在"
        print_info "检查并更新中间件连接信息（使用host网络模式）..."
        
        # 检查并更新数据库连接（如果还是旧的服务名，改为localhost）
        if grep -q "DATABASE_URL=.*PostgresSQL" .env.docker || grep -q "DATABASE_URL=.*postgres-server" .env.docker; then
            sed -i 's|^DATABASE_URL=.*|DATABASE_URL=postgresql://postgres:iot45722414822@localhost:5432/iot-video20|' .env.docker
            print_info "已更新数据库连接为 localhost:5432（host网络模式）"
        fi
        
        # 检查并更新Nacos配置（如果还是IP地址或旧的服务名，改为localhost）
        if grep -q "NACOS_SERVER=.*14\.18\.122\.2" .env.docker || grep -q "NACOS_SERVER=.*Nacos" .env.docker || grep -q "NACOS_SERVER=.*nacos-server" .env.docker; then
            sed -i 's|^NACOS_SERVER=.*|NACOS_SERVER=localhost:8848|' .env.docker
            print_info "已更新Nacos连接为 localhost:8848（host网络模式）"
        fi
        
        # 检查并更新MinIO配置（如果还是旧的服务名，改为localhost）
        if grep -q "MINIO_ENDPOINT=.*MinIO" .env.docker || grep -q "MINIO_ENDPOINT=.*minio-server" .env.docker; then
            sed -i 's|^MINIO_ENDPOINT=.*|MINIO_ENDPOINT=localhost:9000|' .env.docker
            print_info "已更新MinIO连接为 localhost:9000（host网络模式）"
        fi
        
        # 检查并更新Redis配置（如果还是旧的服务名，改为localhost）
        if grep -q "REDIS_HOST=.*Redis" .env.docker || grep -q "REDIS_HOST=.*redis-server" .env.docker; then
            sed -i 's|^REDIS_HOST=.*|REDIS_HOST=localhost|' .env.docker
            print_info "已更新Redis连接为 localhost（host网络模式）"
        fi
        
        # 检查并更新Kafka配置（如果还是旧的服务名，改为localhost）
        if grep -q "KAFKA_BOOTSTRAP_SERVERS=.*Kafka" .env.docker || grep -q "KAFKA_BOOTSTRAP_SERVERS=.*kafka-server" .env.docker; then
            sed -i 's|^KAFKA_BOOTSTRAP_SERVERS=.*|KAFKA_BOOTSTRAP_SERVERS=localhost:9092|' .env.docker
            print_info "已更新Kafka连接为 localhost:9092（host网络模式）"
        fi
        
        # 检查并更新TDengine配置（如果还是旧的服务名，改为localhost）
        if grep -q "TDENGINE_HOST=.*TDengine" .env.docker || grep -q "TDENGINE_HOST=.*tdengine-server" .env.docker; then
            sed -i 's|^TDENGINE_HOST=.*|TDENGINE_HOST=localhost|' .env.docker
            print_info "已更新TDengine连接为 localhost（host网络模式）"
        fi
    fi
}

# 安装服务
install_service() {
    print_info "开始安装 VIDEO 服务..."
    
    check_docker
    check_docker_compose
    check_network
    create_directories
    create_env_file
    
    print_info "构建 Docker 镜像..."
    $COMPOSE_CMD build
    
    print_info "启动服务..."
    $COMPOSE_CMD up -d
    
    print_success "服务安装完成！"
    print_info "等待服务启动..."
    sleep 5
    
    # 检查服务状态
    check_status
    
    print_info "服务访问地址: http://localhost:6000"
    print_info "健康检查地址: http://localhost:6000/actuator/health"
    print_info "查看日志: ./install.sh logs"
}

# 启动服务
start_service() {
    print_info "启动服务..."
    check_docker
    check_docker_compose
    check_network
    
    if [ ! -f .env.docker ]; then
        print_warning ".env.docker 文件不存在，正在创建..."
        create_env_file
    fi
    
    $COMPOSE_CMD up -d
    print_success "服务已启动"
    check_status
}

# 停止服务
stop_service() {
    print_info "停止服务..."
    check_docker
    check_docker_compose
    
    $COMPOSE_CMD down
    print_success "服务已停止"
}

# 重启服务
restart_service() {
    print_info "重启服务..."
    check_docker
    check_docker_compose
    
    $COMPOSE_CMD restart
    print_success "服务已重启"
    check_status
}

# 查看服务状态
check_status() {
    print_info "服务状态:"
    check_docker
    check_docker_compose
    
    $COMPOSE_CMD ps
    
    echo ""
    print_info "容器健康状态:"
    if docker ps --filter "name=video-service" --format "table {{.Names}}\t{{.Status}}" | grep -q video-service; then
        docker ps --filter "name=video-service" --format "table {{.Names}}\t{{.Status}}"
        
        # 检查健康检查
        HEALTH=$(docker inspect --format='{{.State.Health.Status}}' video-service 2>/dev/null || echo "N/A")
        if [ "$HEALTH" != "N/A" ]; then
            echo "健康状态: $HEALTH"
        fi
    else
        print_warning "服务未运行"
    fi
}

# 查看日志
view_logs() {
    check_docker
    check_docker_compose
    
    if [ "$1" == "-f" ] || [ "$1" == "--follow" ]; then
        print_info "实时查看日志（按 Ctrl+C 退出）..."
        $COMPOSE_CMD logs -f
    else
        print_info "查看最近日志..."
        $COMPOSE_CMD logs --tail=100
    fi
}

# 构建镜像
build_image() {
    print_info "重新构建 Docker 镜像..."
    check_docker
    check_docker_compose
    
    $COMPOSE_CMD build --no-cache
    print_success "镜像构建完成"
}

# 清理服务
clean_service() {
    print_warning "这将删除容器、镜像和数据卷，确定要继续吗？(y/N)"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        check_docker
        check_docker_compose
        print_info "停止并删除容器..."
        $COMPOSE_CMD down -v
        
        print_info "删除镜像..."
        docker rmi video-service:latest 2>/dev/null || true
        
        print_success "清理完成"
    else
        print_info "已取消清理操作"
    fi
}

# 更新服务
update_service() {
    print_info "更新服务..."
    check_docker
    check_docker_compose
    check_network
    
    print_info "拉取最新代码..."
    git pull || print_warning "Git pull 失败，继续使用当前代码"
    
    print_info "重新构建镜像..."
    $COMPOSE_CMD build
    
    print_info "重启服务..."
    $COMPOSE_CMD up -d
    
    print_success "服务更新完成"
    check_status
}

# 显示帮助信息
show_help() {
    echo "VIDEO服务 Docker Compose 管理脚本"
    echo ""
    echo "使用方法:"
    echo "  ./install.sh [命令]"
    echo ""
    echo "可用命令:"
    echo "  install    - 安装并启动服务（首次运行）"
    echo "  start      - 启动服务"
    echo "  stop       - 停止服务"
    echo "  restart    - 重启服务"
    echo "  status     - 查看服务状态"
    echo "  logs       - 查看服务日志"
    echo "  logs -f    - 实时查看服务日志"
    echo "  build      - 重新构建镜像"
    echo "  clean      - 清理容器和镜像"
    echo "  update     - 更新并重启服务"
    echo "  help       - 显示此帮助信息"
    echo ""
}

# 主函数
main() {
    case "${1:-help}" in
        install)
            install_service
            ;;
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        status)
            check_status
            ;;
        logs)
            view_logs "$2"
            ;;
        build)
            build_image
            ;;
        clean)
            clean_service
            ;;
        update)
            update_service
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

