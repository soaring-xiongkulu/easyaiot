#!/bin/bash

# ============================================
# AI服务 Docker Compose 管理脚本
# ============================================
# 使用方法：
#   ./install_linux.sh [命令]
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

# 检查 GPU 支持
GPU_AVAILABLE=false
GPU_HARDWARE_DETECTED=false

# 架构检测
ARCH=""
DOCKER_PLATFORM=""
BASE_IMAGE=""

# 检测服务器架构并验证是否支持
detect_architecture() {
    print_info "检测服务器架构..."
    ARCH=$(uname -m)
    
    case "$ARCH" in
        x86_64|amd64)
            ARCH="x86_64"
            DOCKER_PLATFORM="linux/amd64"
            BASE_IMAGE="pytorch/pytorch:2.9.0-cuda12.8-cudnn9-runtime"
            print_success "检测到架构: $ARCH (x86_64)"
            print_info "使用 PyTorch CUDA 镜像: $BASE_IMAGE"
            ;;
        aarch64|arm64|armv7l|armv6l)
            print_error "检测到 ARM 架构 ($ARCH)"
            print_error "NVIDIA 官方的 CUDA 容器化只支持 x86_64 架构"
            print_error "ARM 服务器不支持容器化部署，部署已终止"
            echo ""
            print_info "如需在 ARM 服务器上运行，请考虑："
            print_info "1. 使用原生 Python 环境直接运行（非容器化）"
            print_info "2. 使用支持 ARM 的 CPU 版本 PyTorch（性能较低）"
            exit 1
            ;;
        *)
            print_error "未识别的架构: $ARCH"
            print_error "本服务仅支持 x86_64 架构，部署已终止"
            exit 1
            ;;
    esac
    
    # 导出环境变量供docker-compose使用
    export DOCKER_PLATFORM
    export BASE_IMAGE
}

# 配置架构相关的docker-compose设置
configure_architecture() {
    print_info "配置 Docker Compose 架构设置..."
    
    # 创建或更新 .env.arch 文件来存储架构配置
    if [ ! -f .env.arch ] || ! grep -q "DOCKER_PLATFORM=" .env.arch 2>/dev/null; then
        echo "# 架构配置（由install_linux.sh自动生成）" > .env.arch
        echo "DOCKER_PLATFORM=$DOCKER_PLATFORM" >> .env.arch
        echo "BASE_IMAGE=$BASE_IMAGE" >> .env.arch
        print_success "已创建架构配置文件 .env.arch"
    else
        # 更新现有配置
        sed -i "s|^DOCKER_PLATFORM=.*|DOCKER_PLATFORM=$DOCKER_PLATFORM|" .env.arch
        sed -i "s|^BASE_IMAGE=.*|BASE_IMAGE=$BASE_IMAGE|" .env.arch
        print_info "已更新架构配置文件 .env.arch"
    fi
    
    print_success "架构配置完成: $ARCH -> $DOCKER_PLATFORM"
}

# 检查 NVIDIA Container Toolkit 是否安装
check_nvidia_container_toolkit() {
    if dpkg -l | grep -q nvidia-container-toolkit; then
        return 0
    else
        return 1
    fi
}

# 安装 NVIDIA Container Toolkit
install_nvidia_container_toolkit() {
    print_info "开始安装 NVIDIA Container Toolkit..."
    
    # 检查是否有 sudo 权限
    if ! sudo -n true 2>/dev/null; then
        print_error "需要 sudo 权限来安装 NVIDIA Container Toolkit"
        print_info "请手动运行以下命令安装："
        echo ""
        echo "distribution=\$(. /etc/os-release;echo \$ID\$VERSION_ID) \\"
        echo "    && curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add - \\"
        echo "    && curl -s -L https://nvidia.github.io/nvidia-docker/\$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list"
        echo ""
        echo "sudo apt update"
        echo "sudo apt install -y nvidia-container-toolkit"
        echo "sudo systemctl restart docker"
        echo ""
        return 1
    fi
    
    # 添加 NVIDIA Docker 仓库
    print_info "添加 NVIDIA Docker 仓库..."
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
        && curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add - \
        && curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
    
    if [ $? -ne 0 ]; then
        print_error "添加 NVIDIA Docker 仓库失败"
        return 1
    fi
    
    # 更新软件包列表
    print_info "更新软件包列表..."
    sudo apt update -qq > /dev/null 2>&1
    
    # 安装 nvidia-container-toolkit
    print_info "安装 nvidia-container-toolkit..."
    sudo apt install -qq -y nvidia-container-toolkit > /dev/null 2>&1
    
    if [ $? -ne 0 ]; then
        print_error "安装 nvidia-container-toolkit 失败"
        return 1
    fi
    
    # 配置 Docker daemon.json
    print_info "配置 Docker daemon.json..."
    DOCKER_DAEMON_JSON="/etc/docker/daemon.json"
    
    # 检查文件是否存在
    if [ -f "$DOCKER_DAEMON_JSON" ]; then
        # 备份原文件
        sudo cp "$DOCKER_DAEMON_JSON" "${DOCKER_DAEMON_JSON}.bak"
        print_info "已备份原 daemon.json 为 ${DOCKER_DAEMON_JSON}.bak"
        
        # 检查是否已有 nvidia runtime 配置
        if grep -q "nvidia" "$DOCKER_DAEMON_JSON"; then
            print_info "daemon.json 中已存在 nvidia 配置"
        else
            # 使用 Python 或 jq 来添加配置（如果可用）
            if command -v python3 &> /dev/null; then
                sudo python3 << EOF
import json
import sys

try:
    with open('$DOCKER_DAEMON_JSON', 'r') as f:
        config = json.load(f)
except:
    config = {}

# 添加 nvidia runtime 配置
if 'runtimes' not in config:
    config['runtimes'] = {}

config['runtimes']['nvidia'] = {
    "path": "nvidia-container-runtime",
    "runtimeArgs": []
}

# 设置默认 runtime（可选）
if 'default-runtime' not in config:
    config['default-runtime'] = 'nvidia'

with open('$DOCKER_DAEMON_JSON', 'w') as f:
    json.dump(config, f, indent=2)
EOF
            else
                # 如果没有 Python，使用简单的方法
                print_warning "未找到 Python3，将手动配置 daemon.json"
                print_info "请手动编辑 $DOCKER_DAEMON_JSON，添加以下内容："
                echo ""
                echo '{'
                echo '  "default-runtime": "nvidia",'
                echo '  "runtimes": {'
                echo '    "nvidia": {'
                echo '      "path": "nvidia-container-runtime",'
                echo '      "runtimeArgs": []'
                echo '    }'
                echo '  }'
                echo '}'
                echo ""
                print_warning "配置完成后，请运行: sudo systemctl restart docker"
                return 1
            fi
        fi
    else
        # 文件不存在，创建新文件
        sudo tee "$DOCKER_DAEMON_JSON" > /dev/null << EOF
{
  "default-runtime": "nvidia",
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  }
}
EOF
    fi
    
    # 重启 Docker 服务
    print_info "重启 Docker 服务..."
    sudo systemctl restart docker
    
    if [ $? -eq 0 ]; then
        print_success "NVIDIA Container Toolkit 安装完成"
        return 0
    else
        print_error "重启 Docker 服务失败"
        return 1
    fi
}

check_gpu() {
    if check_command nvidia-smi; then
        GPU_HARDWARE_DETECTED=true
        print_info "检测到 NVIDIA GPU:"
        nvidia-smi --query-gpu=name,driver_version --format=csv,noheader,nounits 2>/dev/null | while IFS=, read -r name version; do
            echo "  - GPU: $name (驱动版本: $version)"
        done
        
        # 检查 nvidia-container-toolkit 是否安装
        print_info "检查 NVIDIA Container Toolkit..."
        
        if check_nvidia_container_toolkit; then
            print_success "NVIDIA Container Toolkit 已安装"
        else
            print_warning "NVIDIA Container Toolkit 未安装"
            # 获取GPU名称用于提示
            GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader,nounits 2>/dev/null | head -1 | xargs)
            print_info "检测到 GPU 硬件（${GPU_NAME}），但 NVIDIA Container Toolkit 未安装"
            echo ""
            print_info "是否自动安装 NVIDIA Container Toolkit？(Y/n)"
            read -t 15 -r response || response="Y"
            
            if [[ ! "$response" =~ ^([nN][oO]|[nN])$ ]]; then
                if install_nvidia_container_toolkit; then
                    print_success "NVIDIA Container Toolkit 安装成功"
                else
                    print_error "NVIDIA Container Toolkit 安装失败，将使用 CPU 模式"
                    GPU_AVAILABLE=false
                    return
                fi
            else
                print_info "跳过安装，将使用 CPU 模式运行"
                GPU_AVAILABLE=false
                return
            fi
        fi
        
        # 检查 docker info 中是否有 nvidia runtime
        print_info "检查 Docker NVIDIA runtime 配置..."
        if docker info --format '{{.Runtimes}}' 2>/dev/null | grep -q "nvidia"; then
            print_success "检测到 Docker 支持 NVIDIA runtime"
            # 再测试实际运行
            if docker run --rm --gpus all nvidia/cuda:11.7.0-base-ubuntu22.04 nvidia-smi >/dev/null 2>&1; then
                print_success "NVIDIA Container Toolkit 已正确配置"
                GPU_AVAILABLE=true
            else
                print_warning "Docker 支持 NVIDIA，但测试运行失败"
                print_info "可能是镜像下载问题或权限问题，尝试启用 GPU 配置"
                GPU_AVAILABLE=true
            fi
        else
            print_warning "Docker daemon.json 中未配置 NVIDIA runtime"
            print_info "尝试配置 Docker daemon.json..."
            if install_nvidia_container_toolkit; then
                # 重新检查
                sleep 2
                if docker info --format '{{.Runtimes}}' 2>/dev/null | grep -q "nvidia"; then
                    print_success "Docker NVIDIA runtime 配置成功"
                    GPU_AVAILABLE=true
                else
                    print_warning "配置后仍无法检测到 NVIDIA runtime，尝试强制启用 GPU 配置"
                    GPU_AVAILABLE=true
                fi
            else
                print_warning "配置失败，尝试强制启用 GPU 配置"
                GPU_AVAILABLE=true
            fi
        fi
    else
        print_warning "未检测到 NVIDIA GPU，将使用 CPU 模式运行"
        GPU_HARDWARE_DETECTED=false
        GPU_AVAILABLE=false
    fi
}

# 配置 GPU 支持（如果可用）
configure_gpu() {
    if [ "$GPU_AVAILABLE" = true ]; then
        print_info "启用 GPU 支持..."
        # 取消注释 GPU 配置（从 "# deploy:" 到 "#           capabilities: [gpu]"）
        if grep -q "^    # deploy:" docker-compose.yaml; then
            # 使用 sed 取消注释 GPU 配置部分（移除行首的 "    # "）
            sed -i '/^    # deploy:/,/^    #           capabilities: \[gpu\]/s/^    # /    /' docker-compose.yaml
            print_success "GPU 配置已启用"
        fi
    else
        print_info "使用 CPU 模式（GPU 配置已禁用）"
        # 确保 GPU 配置被注释（如果未被注释，则注释掉）
        if grep -q "^    deploy:" docker-compose.yaml && ! grep -q "^    # deploy:" docker-compose.yaml; then
            # 使用 sed 注释掉 GPU 配置部分（在行首添加 "    # "）
            sed -i '/^    deploy:/,/^           capabilities: \[gpu\]/s/^    /    # /' docker-compose.yaml
        fi
    fi
}

# 检查并创建 Docker 网络
check_network() {
    print_info "检查 Docker 网络 easyaiot-network..."
    
    # 检查网络是否已存在（使用网络名称而不是ID）
    if docker network ls --format "{{.Name}}" 2>/dev/null | grep -q "^easyaiot-network$"; then
        print_info "网络 easyaiot-network 已存在"
        return 0
    fi
    
    # 网络不存在，尝试创建
    print_info "网络 easyaiot-network 不存在，正在创建..."
    local create_output=$(docker network create easyaiot-network 2>&1)
    local create_exit_code=$?
    
    if [ $create_exit_code -eq 0 ]; then
        print_success "网络 easyaiot-network 已创建"
        return 0
    else
        # 检查错误原因
        if echo "$create_output" | grep -qi "already exists"; then
            print_info "网络 easyaiot-network 已存在（可能在检查后创建）"
            return 0
        elif echo "$create_output" | grep -qi "permission denied"; then
            print_error "没有权限创建 Docker 网络"
            print_info "请确保当前用户在 docker 组中，或使用 sudo 运行脚本"
            print_info "解决方案："
            echo "  1. 将当前用户添加到 docker 组："
            echo "     sudo usermod -aG docker $USER"
            echo "     然后重新登录或运行: newgrp docker"
            echo ""
            echo "  2. 或者使用 sudo 运行此脚本："
            echo "     sudo ./install_linux.sh $*"
            exit 1
        elif echo "$create_output" | grep -qi "network with name.*already exists"; then
            print_warning "网络名称冲突，但网络已存在，继续使用现有网络"
            return 0
        else
            print_error "无法创建网络 easyaiot-network"
            print_error "错误信息: $create_output"
            print_info "诊断建议："
            print_info "  1. 检查 Docker 服务是否正常运行: sudo systemctl status docker"
            print_info "  2. 检查当前用户是否有权限: docker network ls"
            print_info "  3. 查看 Docker 日志: sudo journalctl -u docker.service"
            exit 1
        fi
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
            
            # 自动配置中间件连接信息（使用localhost，因为docker-compose.yaml使用host网络模式）
            print_info "自动配置中间件连接信息..."
            
            # 更新数据库连接（使用localhost，因为使用host网络模式，中间件端口已映射到宿主机）
            sed -i 's|^DATABASE_URL=.*|DATABASE_URL=postgresql://postgres:iot45722414822@localhost:5432/iot-ai20|' .env.docker
            
            # 更新Nacos配置（使用localhost，因为使用host网络模式）
            sed -i 's|^NACOS_SERVER=.*|NACOS_SERVER=localhost:8848|' .env.docker
            
            # 更新MinIO配置（使用localhost，因为使用host网络模式）
            sed -i 's|^MINIO_ENDPOINT=.*|MINIO_ENDPOINT=localhost:9000|' .env.docker
            sed -i 's|^MINIO_SECRET_KEY=.*|MINIO_SECRET_KEY=basiclab@iot975248395|' .env.docker
            
            # 更新Nacos密码
            sed -i 's|^NACOS_PASSWORD=.*|NACOS_PASSWORD=basiclab@iot78475418754|' .env.docker
            
            # 确保Nacos命名空间为空（使用默认命名空间）
            sed -i 's|^NACOS_NAMESPACE=.*|NACOS_NAMESPACE=|' .env.docker
            
            print_success "中间件连接信息已自动配置"
            print_info "如需修改其他配置，请编辑 .env.docker 文件"
        else
            print_error "env.example 文件不存在，无法创建 .env.docker 文件"
            exit 1
        fi
    else
        print_info ".env.docker 文件已存在"
        print_info "检查并更新中间件连接信息..."
        
        # 检查并更新数据库连接（如果使用Docker服务名，改为localhost，因为使用host网络模式）
        if grep -q "DATABASE_URL=.*PostgresSQL" .env.docker || grep -q "DATABASE_URL=.*postgres-server" .env.docker; then
            sed -i 's|^DATABASE_URL=.*|DATABASE_URL=postgresql://postgres:iot45722414822@localhost:5432/iot-ai20|' .env.docker
            print_info "已更新数据库连接为 localhost:5432（host网络模式）"
        fi
        
        # 检查并更新Nacos配置（如果使用Docker服务名或IP地址，改为localhost，因为使用host网络模式）
        if grep -q "NACOS_SERVER=.*Nacos" .env.docker || grep -q "NACOS_SERVER=.*14\.18\.122\.2" .env.docker || grep -q "NACOS_SERVER=.*nacos-server" .env.docker; then
            sed -i 's|^NACOS_SERVER=.*|NACOS_SERVER=localhost:8848|' .env.docker
            print_info "已更新Nacos连接为 localhost:8848（host网络模式）"
        fi
        
        # 检查并更新MinIO配置（如果使用Docker服务名，改为localhost，因为使用host网络模式）
        if grep -q "MINIO_ENDPOINT=.*MinIO" .env.docker || grep -q "MINIO_ENDPOINT=.*minio-server" .env.docker; then
            sed -i 's|^MINIO_ENDPOINT=.*|MINIO_ENDPOINT=localhost:9000|' .env.docker
            print_info "已更新MinIO连接为 localhost:9000（host网络模式）"
        fi
        
        # 检查并更新Nacos命名空间（如果设置为local或其他非空值，则重置为空，使用默认命名空间）
        if grep -q "^NACOS_NAMESPACE=.*" .env.docker && ! grep -q "^NACOS_NAMESPACE=$" .env.docker; then
            sed -i 's|^NACOS_NAMESPACE=.*|NACOS_NAMESPACE=|' .env.docker
            print_info "已更新Nacos命名空间为空（使用默认命名空间）"
        fi
    fi
}

# 安装服务
install_service() {
    print_info "开始安装 AI 服务..."
    
    check_docker
    check_docker_compose
    detect_architecture
    configure_architecture
    check_network
    check_gpu
    configure_gpu
    create_directories
    create_env_file
    
    print_info "构建 Docker 镜像..."
    print_info "架构: $ARCH, 平台: $DOCKER_PLATFORM, 基础镜像: $BASE_IMAGE"
    print_warning "首次构建可能需要较长时间（10-30分钟），请耐心等待..."
    print_info "正在下载基础镜像和安装依赖..."
    print_info "构建进度将实时显示，请勿中断..."
    echo ""
    
    # 使用环境变量传递架构配置给docker-compose
    # 注意：Docker会自动检测当前架构，无需指定--platform参数
    # 实时显示构建输出，同时捕获错误
    BUILD_LOG="/tmp/docker_build_$$.log"
    set +e  # 暂时关闭错误退出，以便捕获构建状态
    BASE_IMAGE=$BASE_IMAGE $COMPOSE_CMD build 2>&1 | tee "$BUILD_LOG"
    BUILD_STATUS=${PIPESTATUS[0]}
    set -e  # 重新开启错误退出
    
    if [ $BUILD_STATUS -ne 0 ]; then
        print_error "镜像构建失败"
        print_info "查看详细错误信息:"
        grep -iE "(error|warning|failed|失败|警告)" "$BUILD_LOG" | tail -20 || true
        rm -f "$BUILD_LOG"
        exit 1
    fi
    
    rm -f "$BUILD_LOG"
    echo ""
    print_success "镜像构建完成！"
    
    print_info "启动服务..."
    $COMPOSE_CMD up -d --quiet-pull 2>&1 | grep -v "^Creating\|^Starting\|^Pulling\|^Waiting\|^Container" || true
    
    print_success "服务安装完成！"
    print_info "等待服务启动..."
    sleep 5
    
    # 检查服务状态
    check_status
    
    print_info "服务访问地址: http://localhost:5000"
    print_info "健康检查地址: http://localhost:5000/actuator/health"
    print_info "查看日志: ./install_linux.sh logs"
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
    
    $COMPOSE_CMD up -d --quiet-pull 2>&1 | grep -v "^Creating\|^Starting\|^Pulling\|^Waiting\|^Container" || true
    print_success "服务已启动"
    check_status
}

# 停止服务
stop_service() {
    print_info "停止服务..."
    check_docker
    check_docker_compose
    
    $COMPOSE_CMD down --remove-orphans 2>&1 | grep -v "^Stopping\|^Removing\|^Network" || true
    print_success "服务已停止"
}

# 重启服务
restart_service() {
    print_info "重启服务..."
    check_docker
    check_docker_compose
    
    $COMPOSE_CMD restart 2>&1 | grep -v "^Restarting" || true
    print_success "服务已重启"
    check_status
}

# 查看服务状态
check_status() {
    print_info "服务状态:"
    check_docker
    check_docker_compose
    
    $COMPOSE_CMD ps 2>/dev/null | head -20
    
    echo ""
    print_info "容器健康状态:"
    if docker ps --filter "name=ai-service" --format "{{.Names}}" 2>/dev/null | grep -q ai-service; then
        docker ps --filter "name=ai-service" --format "table {{.Names}}\t{{.Status}}" 2>/dev/null
        
        # 检查健康检查
        HEALTH=$(docker inspect --format='{{.State.Health.Status}}' ai-service 2>/dev/null || echo "N/A")
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
    detect_architecture
    configure_architecture
    
    print_info "架构: $ARCH, 平台: $DOCKER_PLATFORM, 基础镜像: $BASE_IMAGE"
    print_warning "重新构建可能需要较长时间（10-30分钟），请耐心等待..."
    print_info "正在重新下载基础镜像和安装依赖..."
    print_info "构建进度将实时显示，请勿中断..."
    echo ""
    
    # 使用环境变量传递架构配置给docker-compose
    # 注意：Docker会自动检测当前架构，无需指定--platform参数
    # 实时显示构建输出，同时捕获错误
    BUILD_LOG="/tmp/docker_build_$$.log"
    set +e  # 暂时关闭错误退出，以便捕获构建状态
    BASE_IMAGE=$BASE_IMAGE $COMPOSE_CMD build --no-cache 2>&1 | tee "$BUILD_LOG"
    BUILD_STATUS=${PIPESTATUS[0]}
    set -e  # 重新开启错误退出
    
    if [ $BUILD_STATUS -ne 0 ]; then
        print_error "镜像构建失败"
        print_info "查看详细错误信息:"
        grep -iE "(error|warning|failed|失败|警告)" "$BUILD_LOG" | tail -20 || true
        rm -f "$BUILD_LOG"
        exit 1
    fi
    
    rm -f "$BUILD_LOG"
    echo ""
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
        $COMPOSE_CMD down -v --remove-orphans 2>&1 | grep -v "^Stopping\|^Removing\|^Network" || true
        
        print_info "删除镜像..."
        docker rmi ai-service:latest >/dev/null 2>&1 || true
        
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
    detect_architecture
    configure_architecture
    check_network
    
    print_info "拉取最新代码..."
    git pull || print_warning "Git pull 失败，继续使用当前代码"
    
    print_info "重新构建镜像..."
    print_info "架构: $ARCH, 平台: $DOCKER_PLATFORM, 基础镜像: $BASE_IMAGE"
    print_warning "构建可能需要较长时间（10-30分钟），请耐心等待..."
    print_info "正在构建镜像..."
    print_info "构建进度将实时显示，请勿中断..."
    echo ""
    
    # 使用环境变量传递架构配置给docker-compose
    # 注意：Docker会自动检测当前架构，无需指定--platform参数
    # 实时显示构建输出，同时捕获错误
    BUILD_LOG="/tmp/docker_build_$$.log"
    set +e  # 暂时关闭错误退出，以便捕获构建状态
    BASE_IMAGE=$BASE_IMAGE $COMPOSE_CMD build 2>&1 | tee "$BUILD_LOG"
    BUILD_STATUS=${PIPESTATUS[0]}
    set -e  # 重新开启错误退出
    
    if [ $BUILD_STATUS -ne 0 ]; then
        print_error "镜像构建失败"
        print_info "查看详细错误信息:"
        grep -iE "(error|warning|failed|失败|警告)" "$BUILD_LOG" | tail -20 || true
        rm -f "$BUILD_LOG"
        exit 1
    fi
    
    rm -f "$BUILD_LOG"
    echo ""
    print_success "镜像构建完成！"
    
    print_info "重启服务..."
    $COMPOSE_CMD up -d --quiet-pull 2>&1 | grep -v "^Creating\|^Starting\|^Pulling\|^Waiting\|^Container" || true
    
    print_success "服务更新完成"
    check_status
}

# 显示帮助信息
show_help() {
    echo "AI服务 Docker Compose 管理脚本"
    echo ""
    echo "使用方法:"
    echo "  ./install_linux.sh [命令]"
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

