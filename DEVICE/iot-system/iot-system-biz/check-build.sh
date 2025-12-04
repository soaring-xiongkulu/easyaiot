#!/bin/bash

# iot-system-biz Docker构建诊断脚本

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  iot-system-biz Docker构建诊断${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查Dockerfile
echo -e "${YELLOW}[1/6] 检查Dockerfile...${NC}"
if [ -f "Dockerfile" ]; then
    echo -e "${GREEN}✓ Dockerfile存在${NC}"
    echo "  内容预览:"
    head -5 Dockerfile | sed 's/^/  /'
else
    echo -e "${RED}✗ Dockerfile不存在${NC}"
    exit 1
fi
echo ""

# 检查JAR文件
echo -e "${YELLOW}[2/6] 检查JAR文件...${NC}"
if [ -f "target/jars/iot-system-biz.jar" ]; then
    echo -e "${GREEN}✓ JAR文件存在${NC}"
    echo "  文件信息:"
    ls -lh target/jars/iot-system-biz.jar | awk '{print "  大小:", $5, "权限:", $1, "所有者:", $3":"$4}'
    
    # 检查文件类型
    if file target/jars/iot-system-biz.jar | grep -q "Java archive"; then
        echo -e "${GREEN}✓ JAR文件格式正确${NC}"
    else
        echo -e "${RED}✗ JAR文件格式可能不正确${NC}"
    fi
    
    # 检查文件权限
    if [ -r "target/jars/iot-system-biz.jar" ]; then
        echo -e "${GREEN}✓ JAR文件可读${NC}"
    else
        echo -e "${RED}✗ JAR文件不可读${NC}"
    fi
else
    echo -e "${RED}✗ JAR文件不存在${NC}"
    echo "  请先运行: mvn clean package"
    exit 1
fi
echo ""

# 检查Docker
echo -e "${YELLOW}[3/6] 检查Docker...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker已安装${NC}"
    docker --version | sed 's/^/  /'
    
    # 检查Docker权限
    if docker ps &> /dev/null; then
        echo -e "${GREEN}✓ Docker权限正常${NC}"
    else
        echo -e "${RED}✗ Docker权限问题${NC}"
        echo "  请运行: sudo usermod -aG docker $USER"
        echo "  然后重新登录或运行: newgrp docker"
    fi
else
    echo -e "${RED}✗ Docker未安装${NC}"
    exit 1
fi
echo ""

# 检查Docker Compose
echo -e "${YELLOW}[4/6] 检查Docker Compose...${NC}"
if docker compose version &> /dev/null; then
    echo -e "${GREEN}✓ Docker Compose已安装${NC}"
    docker compose version | sed 's/^/  /'
elif docker-compose version &> /dev/null; then
    echo -e "${GREEN}✓ Docker Compose已安装（旧版本）${NC}"
    docker-compose --version | sed 's/^/  /'
else
    echo -e "${RED}✗ Docker Compose未安装${NC}"
    exit 1
fi
echo ""

# 检查构建上下文
echo -e "${YELLOW}[5/6] 检查构建上下文...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
echo "  当前目录: $SCRIPT_DIR"
echo "  构建上下文: $SCRIPT_DIR"
echo "  Dockerfile路径: $SCRIPT_DIR/Dockerfile"
echo "  JAR文件路径: $SCRIPT_DIR/target/jars/iot-system-biz.jar"
echo ""

# 检查docker-compose.yml配置
echo -e "${YELLOW}[6/6] 检查docker-compose.yml配置...${NC}"
COMPOSE_FILE="../../docker-compose.yml"
if [ -f "$COMPOSE_FILE" ]; then
    echo -e "${GREEN}✓ docker-compose.yml存在${NC}"
    echo "  iot-system配置:"
    grep -A 5 "iot-system:" "$COMPOSE_FILE" | grep -E "(context|dockerfile|image)" | sed 's/^/  /'
else
    echo -e "${YELLOW}⚠ docker-compose.yml不存在或路径不正确${NC}"
fi
echo ""

# 总结
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  诊断完成${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "如果所有检查都通过，可以尝试构建:"
echo "  cd /projects/easyaiot/DEVICE"
echo "  docker compose build iot-system"
echo ""

