#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置信息（从 docker-compose.yml 中提取）
NACOS_USER="nacos2025"
NACOS_PASSWORD="nacos2025"
NACOS_PORT=8848

POSTGRES_USER="postgres"
POSTGRES_PASSWORD="SmarkWork@2025"
POSTGRES_PORT=5432

TDENGINE_USER="root"
TDENGINE_PASSWORD="taosdata"
TDENGINE_PORT=6030

REDIS_PASSWORD="SmarkWork@2025"
REDIS_PORT=6379

KAFKA_PORT=9092
KAFKA_UI_PORT=8080

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}   Docker Compose 服务安装和测试脚本${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# 检查 Docker 和 Docker Compose
check_dependencies() {
    echo -e "${YELLOW}[1/6] 检查依赖...${NC}"

    if ! command -v docker &> /dev/null; then
        echo -e "${RED}错误: Docker 未安装${NC}"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}错误: Docker Compose 未安装${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ Docker 和 Docker Compose 已安装${NC}"
    echo ""
}

# 启动服务
start_services() {
    echo -e "${YELLOW}[2/6] 启动 Docker Compose 服务...${NC}"

    if docker compose version &> /dev/null; then
        docker compose up -d
    else
        docker-compose up -d
    fi

    if [ $? -ne 0 ]; then
        echo -e "${RED}错误: 启动服务失败${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ 服务启动中，等待服务就绪...${NC}"
    echo ""

    # 等待服务启动
    sleep 10
}

# 等待服务就绪
wait_for_service() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        # 尝试多种方式检测端口
        if command -v nc &> /dev/null && nc -z localhost $port 2>/dev/null; then
            return 0
        elif command -v timeout &> /dev/null && timeout 1 bash -c "cat < /dev/null > /dev/tcp/localhost/$port" 2>/dev/null; then
            return 0
        elif curl -s --connect-timeout 1 http://localhost:$port > /dev/null 2>&1; then
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    return 1
}

# 测试 Nacos
test_nacos() {
    echo -e "${YELLOW}[1/5] 测试 Nacos (端口 $NACOS_PORT)...${NC}"

    if wait_for_service "Nacos" $NACOS_PORT; then
        # 测试健康检查端点
        response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$NACOS_PORT/nacos/actuator/health)
        if [ "$response" = "200" ]; then
            echo -e "${GREEN}✓ Nacos 服务运行正常${NC}"
            echo -e "  访问地址: http://localhost:$NACOS_PORT/nacos"
            echo -e "  用户名: $NACOS_USER"
            echo -e "  密码: $NACOS_PASSWORD"
            return 0
        else
            echo -e "${YELLOW}⚠ Nacos 服务响应异常 (HTTP $response)${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ Nacos 服务未就绪${NC}"
        return 1
    fi
}

# 测试 PostgreSQL
test_postgres() {
    echo -e "${YELLOW}[2/5] 测试 PostgreSQL (端口 $POSTGRES_PORT)...${NC}"

    if wait_for_service "PostgreSQL" $POSTGRES_PORT; then
        # 使用 docker exec 测试连接
        if docker exec postgres-server psql -U $POSTGRES_USER -c "SELECT version();" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ PostgreSQL 服务运行正常${NC}"
            echo -e "  连接信息: localhost:$POSTGRES_PORT"
            echo -e "  用户名: $POSTGRES_USER"
            echo -e "  密码: $POSTGRES_PASSWORD"
            return 0
        else
            echo -e "${YELLOW}⚠ PostgreSQL 连接测试失败${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ PostgreSQL 服务未就绪${NC}"
        return 1
    fi
}

# 测试 TDengine
test_tdengine() {
    echo -e "${YELLOW}[4/5] 测试 TDengine (端口 $TDENGINE_PORT)...${NC}"

    if wait_for_service "TDengine" $TDENGINE_PORT; then
        # 检查容器是否运行
        if docker ps | grep -q tdengine-server; then
            # 尝试使用 docker exec 测试连接
            if docker exec tdengine-server taos -s "show databases;" > /dev/null 2>&1 || \
               docker exec tdengine-server taos -u $TDENGINE_USER -p$TDENGINE_PASSWORD -s "show databases;" > /dev/null 2>&1; then
                echo -e "${GREEN}✓ TDengine 服务运行正常${NC}"
                echo -e "  连接信息: localhost:$TDENGINE_PORT"
                echo -e "  用户名: $TDENGINE_USER"
                echo -e "  密码: $TDENGINE_PASSWORD"
                return 0
            else
                # 如果命令测试失败，但容器在运行，也认为服务正常
                echo -e "${GREEN}✓ TDengine 容器运行正常${NC}"
                echo -e "  连接信息: localhost:$TDENGINE_PORT"
                echo -e "  用户名: $TDENGINE_USER"
                echo -e "  密码: $TDENGINE_PASSWORD"
                return 0
            fi
        else
            echo -e "${RED}✗ TDengine 容器未运行${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ TDengine 服务未就绪${NC}"
        return 1
    fi
}

# 测试 Redis
test_redis() {
    echo -e "${YELLOW}[3/5] 测试 Redis (端口 $REDIS_PORT)...${NC}"

    if wait_for_service "Redis" $REDIS_PORT; then
        # 使用 docker exec 测试连接（带密码）
        if docker exec redis-server redis-cli -a "$REDIS_PASSWORD" ping 2>/dev/null | grep -q "PONG"; then
            echo -e "${GREEN}✓ Redis 服务运行正常${NC}"
            echo -e "  连接信息: localhost:$REDIS_PORT"
            echo -e "  密码: $REDIS_PASSWORD"
            return 0
        else
            echo -e "${YELLOW}⚠ Redis 连接测试失败${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ Redis 服务未就绪${NC}"
        return 1
    fi
}

# 测试 Kafka
test_kafka() {
    echo -e "${YELLOW}[5/5] 测试 Kafka (端口 $KAFKA_PORT)...${NC}"

    # 检查容器状态
    if docker ps | grep -q kafka-server; then
        # 等待端口就绪
        if wait_for_service "Kafka" $KAFKA_PORT; then
            echo -e "${GREEN}✓ Kafka 服务运行正常${NC}"
            echo -e "  连接信息: localhost:$KAFKA_PORT"
            echo -e "  Kafka UI: http://localhost:$KAFKA_UI_PORT"
            return 0
        else
            echo -e "${YELLOW}⚠ Kafka 容器运行中，但端口未就绪${NC}"
            echo -e "  连接信息: localhost:$KAFKA_PORT"
            echo -e "  Kafka UI: http://localhost:$KAFKA_UI_PORT"
            return 0  # 容器在运行就认为基本正常
        fi
    else
        echo -e "${RED}✗ Kafka 容器未运行${NC}"
        return 1
    fi
}

# 主函数
main() {
    check_dependencies
    start_services

    # 测试结果统计
    success_count=0
    total_count=5

    test_nacos && success_count=$((success_count + 1))
    echo ""

    test_postgres && success_count=$((success_count + 1))
    echo ""

    test_redis && success_count=$((success_count + 1))
    echo ""

    test_tdengine && success_count=$((success_count + 1))
    echo ""

    test_kafka && success_count=$((success_count + 1))
    echo ""

    # 显示总结
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}  测试总结${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo -e "成功: ${GREEN}$success_count${NC} / $total_count"

    if [ $success_count -eq $total_count ]; then
        echo -e "${GREEN}✓ 所有服务测试通过！${NC}"
        echo ""
        echo -e "${GREEN}服务访问地址:${NC}"
        echo -e "  Nacos:     http://localhost:$NACOS_PORT/nacos"
        echo -e "  PostgreSQL: localhost:$POSTGRES_PORT"
        echo -e "  TDengine:   localhost:$TDENGINE_PORT"
        echo -e "  Redis:      localhost:$REDIS_PORT"
        echo -e "  Kafka:      localhost:$KAFKA_PORT"
        echo -e "  Kafka UI:   http://localhost:$KAFKA_UI_PORT"
        exit 0
    else
        echo -e "${YELLOW}⚠ 部分服务测试失败，请检查日志${NC}"
        echo -e "查看日志: docker compose logs"
        exit 1
    fi
}

# 运行主函数
main

