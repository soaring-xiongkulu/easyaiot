#!/bin/sh
# 动态解析服务 IP 并更新 /etc/hosts

# 需要映射的服务列表
SERVICES="iot-gateway MinIO ai-service video-service"

# 等待服务启动并解析 IP
for service in $SERVICES; do
    # 尝试解析服务 IP（最多尝试 30 次，每次等待 2 秒）
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        ip=""
        
        # 优先使用 getent 解析服务 IP
        if command -v getent >/dev/null 2>&1; then
            ip=$(getent hosts $service 2>/dev/null | awk '{print $1}' | head -1)
        fi
        
        # 如果 getent 失败，尝试使用 nslookup
        if [ -z "$ip" ] || [ "$ip" = "127.0.0.1" ]; then
            if command -v nslookup >/dev/null 2>&1; then
                ip=$(nslookup $service 2>/dev/null | grep -A1 "Name:" | grep "Address:" | awk '{print $2}' | head -1)
            fi
        fi
        
        # 如果都失败，尝试使用 ping 解析（仅获取 IP，不实际 ping）
        if [ -z "$ip" ] || [ "$ip" = "127.0.0.1" ]; then
            if command -v ping >/dev/null 2>&1; then
                ip=$(ping -c 1 -W 1 $service 2>/dev/null | grep -oP '\(\K[^)]+' | head -1)
            fi
        fi
        
        # 如果成功解析到 IP 且不是本地回环地址
        if [ -n "$ip" ] && [ "$ip" != "127.0.0.1" ]; then
            # 检查是否已存在该映射
            if ! grep -qE "^[0-9.]+[[:space:]]+.*$service" /etc/hosts; then
                echo "$ip    $service" >> /etc/hosts
                echo "Added $service -> $ip to /etc/hosts"
            else
                # 如果已存在，更新映射
                sed -i "s/^[0-9.]*[[:space:]]*.*$service/$ip    $service/" /etc/hosts 2>/dev/null || true
            fi
            break
        fi
        
        attempt=$((attempt + 1))
        if [ $attempt -lt $max_attempts ]; then
            sleep 2
        fi
    done
    
    if [ -z "$ip" ] || [ "$ip" = "127.0.0.1" ]; then
        echo "Warning: Could not resolve $service after $max_attempts attempts"
    fi
done

# 显示更新后的 /etc/hosts
echo "Updated /etc/hosts:"
cat /etc/hosts

# 启动 nginx
exec nginx -g "daemon off;"

