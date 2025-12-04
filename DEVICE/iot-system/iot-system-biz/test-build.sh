#!/bin/bash

# iot-system-biz Docker镜像构建和运行测试脚本

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  iot-system-biz 镜像构建和运行测试${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查Docker权限
if ! docker ps &> /dev/null; then
    echo -e "${RED}✗ Docker权限问题${NC}"
    echo "  请运行: sudo usermod -aG docker $USER"
    echo "  然后重新登录或运行: newgrp docker"
    exit 1
fi

# 脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 镜像名称
IMAGE_NAME="iot-module-system-biz"
IMAGE_TAG="test-$(date +%Y%m%d-%H%M%S)"
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

# 容器名称
CONTAINER_NAME="iot-system-test-$(date +%Y%m%d-%H%M%S)"

echo -e "${YELLOW}[步骤 1/4] 检查构建环境...${NC}"
if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}✗ Dockerfile不存在${NC}"
    exit 1
fi

if [ ! -f "target/jars/iot-system-biz.jar" ]; then
    echo -e "${RED}✗ JAR文件不存在${NC}"
    echo "  请先运行: mvn clean package"
    exit 1
fi

echo -e "${GREEN}✓ 构建环境检查通过${NC}"
echo ""

# 清理旧的测试容器（如果存在）
echo -e "${YELLOW}[步骤 2/4] 清理旧的测试容器...${NC}"
if docker ps -a --format '{{.Names}}' | grep -q "^iot-system-test-"; then
    echo "  发现旧的测试容器，正在清理..."
    docker ps -a --format '{{.Names}}' | grep "^iot-system-test-" | xargs -r docker rm -f
    echo -e "${GREEN}✓ 清理完成${NC}"
else
    echo -e "${GREEN}✓ 没有需要清理的容器${NC}"
fi
echo ""

# 构建镜像
echo -e "${YELLOW}[步骤 3/4] 构建Docker镜像...${NC}"
echo "  镜像名称: ${FULL_IMAGE_NAME}"
echo "  构建上下文: ${SCRIPT_DIR}"
echo ""

if docker build -t "${FULL_IMAGE_NAME}" .; then
    echo -e "${GREEN}✓ 镜像构建成功${NC}"
    echo "  镜像ID: $(docker images -q ${FULL_IMAGE_NAME})"
else
    echo -e "${RED}✗ 镜像构建失败${NC}"
    exit 1
fi
echo ""

# 运行容器
echo -e "${YELLOW}[步骤 4/4] 运行容器进行测试...${NC}"
echo "  容器名称: ${CONTAINER_NAME}"
echo "  端口: 48099"
echo ""

# 创建日志目录（如果需要）
LOG_DIR="/docker/iot-device/logs"
if [ ! -d "$LOG_DIR" ]; then
    echo "  创建日志目录: $LOG_DIR"
    sudo mkdir -p "$LOG_DIR" || echo -e "${YELLOW}⚠ 无法创建日志目录，将跳过卷挂载${NC}"
fi

# 运行容器（使用host网络模式，与docker-compose.yml一致）
echo "  启动容器..."
if docker run -d \
    --name "${CONTAINER_NAME}" \
    --network host \
    -e TZ=Asia/Shanghai \
    -e JAVA_OPTS="-Xms512m -Xmx512m" \
    -e SPRING_PROFILES_ACTIVE=local \
    -e SPRING_CLOUD_NACOS_CONFIG_SERVER_ADDR=14.18.122.2:8848 \
    -e SPRING_CLOUD_NACOS_CONFIG_NAMESPACE=local \
    -e SPRING_CLOUD_NACOS_SERVER_ADDR=14.18.122.2:8848 \
    -e SPRING_CLOUD_NACOS_DISCOVERY_NAMESPACE=local \
    -v "${LOG_DIR}:/root/logs/" \
    "${FULL_IMAGE_NAME}"; then
    
    echo -e "${GREEN}✓ 容器启动成功${NC}"
    echo ""
    
    # 等待容器启动
    echo "  等待容器启动（最多等待120秒）..."
    MAX_WAIT=120
    WAIT_COUNT=0
    while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
        if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
            # 检查容器是否健康（检查端口是否监听）
            if netstat -tuln 2>/dev/null | grep -q ":48099 " || ss -tuln 2>/dev/null | grep -q ":48099 "; then
                echo -e "${GREEN}✓ 容器运行正常，端口48099已监听${NC}"
                break
            fi
        else
            echo -e "${RED}✗ 容器已停止${NC}"
            echo "  查看日志:"
            docker logs "${CONTAINER_NAME}" | tail -20
            exit 1
        fi
        
        sleep 2
        WAIT_COUNT=$((WAIT_COUNT + 2))
        echo -n "."
    done
    echo ""
    
    if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
        echo -e "${YELLOW}⚠ 等待超时，但容器仍在运行${NC}"
        echo "  请手动检查容器状态和日志"
    fi
    
    # 显示容器状态
    echo ""
    echo -e "${BLUE}容器状态:${NC}"
    docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    
    # 显示最近的日志
    echo -e "${BLUE}最近的容器日志:${NC}"
    docker logs --tail 30 "${CONTAINER_NAME}"
    echo ""
    
    # 测试健康检查
    echo -e "${YELLOW}测试健康检查...${NC}"
    sleep 5
    if curl -f -s http://localhost:48099/actuator/health > /dev/null 2>&1 || \
       curl -f -s http://localhost:48099 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 健康检查通过${NC}"
    else
        echo -e "${YELLOW}⚠ 健康检查失败（可能是应用尚未完全启动）${NC}"
        echo "  请稍后手动检查: curl http://localhost:48099"
    fi
    echo ""
    
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}测试完成！${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo "容器信息:"
    echo "  容器名称: ${CONTAINER_NAME}"
    echo "  镜像名称: ${FULL_IMAGE_NAME}"
    echo ""
    echo "常用命令:"
    echo "  查看日志: docker logs -f ${CONTAINER_NAME}"
    echo "  查看状态: docker ps --filter name=${CONTAINER_NAME}"
    echo "  停止容器: docker stop ${CONTAINER_NAME}"
    echo "  删除容器: docker rm -f ${CONTAINER_NAME}"
    echo "  删除镜像: docker rmi ${FULL_IMAGE_NAME}"
    echo ""
    
else
    echo -e "${RED}✗ 容器启动失败${NC}"
    exit 1
fi

