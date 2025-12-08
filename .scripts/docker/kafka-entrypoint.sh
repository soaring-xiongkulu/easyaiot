#!/bin/bash
# Kafka 容器启动脚本
# 自动获取宿主机 IP 并配置 Kafka 环境变量

set -e

# 获取宿主机 IP 地址的函数
get_host_ip() {
    local host_ip=""
    
    # 方法1: 优先使用环境变量
    if [ -n "$KAFKA_HOST_IP" ]; then
        echo "$KAFKA_HOST_IP"
        return 0
    fi
    
    # 方法2: 通过路由获取（最可靠，通常返回物理网络接口的 IP）
    if command -v ip &> /dev/null; then
        host_ip=$(ip route get 8.8.8.8 2>/dev/null | awk '{print $7}' | head -n 1)
        if [ -n "$host_ip" ] && [ "$host_ip" != "127.0.0.1" ]; then
            echo "$host_ip"
            return 0
        fi
    fi
    
    # 方法3: 通过 hostname -I 获取
    if command -v hostname &> /dev/null; then
        local all_ips=$(hostname -I 2>/dev/null)
        if [ -n "$all_ips" ]; then
            # 遍历所有 IP，找到第一个非回环地址
            for ip in $all_ips; do
                if [ "$ip" != "127.0.0.1" ] && [[ ! "$ip" =~ ^169\.254\. ]]; then
                    echo "$ip"
                    return 0
                fi
            done
        fi
    fi
    
    # 方法4: 通过 ip addr 获取
    if command -v ip &> /dev/null; then
        host_ip=$(ip addr show | grep -E "inet [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+" | grep -v "127.0.0.1" | head -n 1 | awk '{print $2}' | cut -d/ -f1)
        if [ -n "$host_ip" ]; then
            echo "$host_ip"
            return 0
        fi
    fi
    
    # 如果都失败了，返回 localhost（不推荐，但至少能启动）
    echo "127.0.0.1"
    return 1
}

# 获取宿主机 IP
HOST_IP=$(get_host_ip)
echo "[Kafka Entrypoint] 检测到宿主机 IP: $HOST_IP"

# 设置 Kafka 环境变量
export KAFKA_ADVERTISED_LISTENERS="PLAINTEXT://${HOST_IP}:9092"
export KAFKA_CONTROLLER_QUORUM_VOTERS="1@${HOST_IP}:9093"

echo "[Kafka Entrypoint] 配置 KAFKA_ADVERTISED_LISTENERS=${KAFKA_ADVERTISED_LISTENERS}"
echo "[Kafka Entrypoint] 配置 KAFKA_CONTROLLER_QUORUM_VOTERS=${KAFKA_CONTROLLER_QUORUM_VOTERS}"

# Apache Kafka 官方镜像使用环境变量配置，会自动启动
# 如果传入了命令参数，执行它们；否则让镜像使用默认的启动方式
if [ $# -gt 0 ]; then
    echo "[Kafka Entrypoint] 执行命令: $@"
    exec "$@"
else
    # 如果没有传入命令，使用 Kafka 的默认启动方式
    # Apache Kafka 3.8.0 镜像在 KRaft 模式下会自动从环境变量读取配置并启动
    echo "[Kafka Entrypoint] 使用默认启动方式（从环境变量读取配置）"
    # 查找并执行 Kafka 启动脚本
    if [ -f "/opt/kafka/bin/kafka-server-start.sh" ]; then
        exec /opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/kraft/server.properties
    elif [ -f "/usr/bin/kafka-server-start.sh" ]; then
        exec /usr/bin/kafka-server-start.sh /etc/kafka/server.properties
    else
        # 如果找不到启动脚本，尝试查找可能的启动脚本
        echo "[Kafka Entrypoint] 查找 Kafka 启动脚本..."
        KAFKA_SCRIPT=$(find /opt /usr -name "kafka-server-start.sh" 2>/dev/null | head -n 1)
        if [ -n "$KAFKA_SCRIPT" ] && [ -f "$KAFKA_SCRIPT" ]; then
            KAFKA_CONFIG="$(dirname "$(dirname "$KAFKA_SCRIPT")")/config/kraft/server.properties"
            if [ -f "$KAFKA_CONFIG" ]; then
                echo "[Kafka Entrypoint] 找到启动脚本: $KAFKA_SCRIPT"
                echo "[Kafka Entrypoint] 使用配置文件: $KAFKA_CONFIG"
                exec "$KAFKA_SCRIPT" "$KAFKA_CONFIG"
            else
                echo "[Kafka Entrypoint] 找到启动脚本: $KAFKA_SCRIPT，但配置文件不存在，使用环境变量"
                exec "$KAFKA_SCRIPT"
            fi
        else
            # 如果都找不到，尝试使用 PATH 中的命令
            if command -v kafka-server-start.sh >/dev/null 2>&1; then
                echo "[Kafka Entrypoint] 使用 PATH 中的 kafka-server-start.sh"
                exec kafka-server-start.sh
            else
                echo "[Kafka Entrypoint] 错误: 无法找到 Kafka 启动脚本"
                echo "[Kafka Entrypoint] 提示: Apache Kafka 镜像应该有一个默认的启动方式"
                echo "[Kafka Entrypoint] 环境变量已设置，请检查镜像的默认 entrypoint"
                exit 1
            fi
        fi
    fi
fi

