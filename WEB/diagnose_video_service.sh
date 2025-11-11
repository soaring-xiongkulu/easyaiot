#!/bin/bash
# ============================================
# Video服务连接诊断脚本
# 用于诊断nginx 499错误问题
# ============================================

echo "============================================"
echo "Video服务连接诊断工具"
echo "============================================"
echo ""

# 1. 检查nginx容器是否运行
echo "1. 检查nginx容器状态..."
if docker ps | grep -q web-service; then
    echo "   ✅ nginx容器 (web-service) 正在运行"
else
    echo "   ❌ nginx容器 (web-service) 未运行"
    exit 1
fi

# 2. 检查video-service容器是否运行
echo ""
echo "2. 检查video-service容器状态..."
if docker ps | grep -q video-service; then
    echo "   ✅ video-service容器正在运行"
else
    echo "   ❌ video-service容器未运行"
    exit 1
fi

# 3. 检查nginx容器内是否能解析video-host
echo ""
echo "3. 检查nginx容器内video-host解析..."
NGINX_CONTAINER=$(docker ps | grep web-service | awk '{print $1}')
if [ -z "$NGINX_CONTAINER" ]; then
    echo "   ❌ 无法找到nginx容器"
    exit 1
fi

VIDEO_HOST_IP=$(docker exec $NGINX_CONTAINER getent hosts video-host | awk '{print $1}')
if [ -z "$VIDEO_HOST_IP" ]; then
    echo "   ❌ video-host无法解析（host-gateway可能不工作）"
    echo "   💡 解决方案：需要在docker-compose.yaml中手动配置宿主机IP"
else
    echo "   ✅ video-host解析为: $VIDEO_HOST_IP"
fi

# 4. 检查宿主机上的video-service是否可访问
echo ""
echo "4. 检查宿主机上的video-service健康状态..."
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:6000/actuator/health 2>/dev/null || echo "000")
if [ "$HEALTH_CHECK" = "200" ]; then
    echo "   ✅ video-service健康检查通过 (http://localhost:6000/actuator/health)"
else
    echo "   ❌ video-service健康检查失败 (HTTP状态码: $HEALTH_CHECK)"
    echo "   💡 请检查video-service是否正常运行"
fi

# 5. 从nginx容器内测试连接到video-host
echo ""
echo "5. 从nginx容器内测试连接到video-host:6000..."
if [ -n "$VIDEO_HOST_IP" ]; then
    CONNECT_TEST=$(docker exec $NGINX_CONTAINER sh -c "timeout 5 curl -s -o /dev/null -w '%{http_code}' http://video-host:6000/actuator/health 2>/dev/null || echo '000'")
    if [ "$CONNECT_TEST" = "200" ]; then
        echo "   ✅ nginx容器可以连接到video-host:6000"
    else
        echo "   ❌ nginx容器无法连接到video-host:6000 (HTTP状态码: $CONNECT_TEST)"
        echo "   💡 可能原因："
        echo "      - host-gateway不工作"
        echo "      - 防火墙阻止了连接"
        echo "      - video-service未正确监听端口"
    fi
else
    echo "   ⚠️  跳过测试（video-host无法解析）"
fi

# 6. 获取宿主机IP建议
echo ""
echo "6. 获取宿主机IP地址（用于手动配置）..."
HOST_IP=$(hostname -I | awk '{print $1}')
DOCKER_GATEWAY=$(ip addr show docker0 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d/ -f1)
if [ -z "$DOCKER_GATEWAY" ]; then
    DOCKER_GATEWAY=$(ip route | grep default | awk '{print $3}' | head -1)
fi

echo "   建议使用的IP地址："
if [ -n "$HOST_IP" ]; then
    echo "   - 宿主机IP: $HOST_IP"
fi
if [ -n "$DOCKER_GATEWAY" ]; then
    echo "   - Docker网关IP: $DOCKER_GATEWAY"
fi

# 7. 提供解决方案
echo ""
echo "============================================"
echo "解决方案"
echo "============================================"
if [ -z "$VIDEO_HOST_IP" ] || [ "$CONNECT_TEST" != "200" ]; then
    echo ""
    echo "如果host-gateway不工作，请按以下步骤操作："
    echo ""
    echo "1. 编辑 WEB/docker-compose.yaml 文件"
    echo "2. 找到 extra_hosts 配置部分"
    echo "3. 取消注释并修改以下行："
    echo ""
    if [ -n "$HOST_IP" ]; then
        echo "   - \"video-host:$HOST_IP\""
    elif [ -n "$DOCKER_GATEWAY" ]; then
        echo "   - \"video-host:$DOCKER_GATEWAY\""
    else
        echo "   - \"video-host:YOUR_HOST_IP\"  # 请替换为实际宿主机IP"
    fi
    echo ""
    echo "4. 重启nginx容器："
    echo "   cd WEB && docker-compose restart web-service"
    echo ""
else
    echo ""
    echo "✅ 所有检查通过，连接正常！"
    echo "   如果仍然遇到499错误，请检查："
    echo "   - nginx错误日志: docker exec $NGINX_CONTAINER tail -f /var/log/nginx/video_error.log"
    echo "   - video-service日志: docker logs -f video-service"
fi

echo ""
echo "============================================"
echo "诊断完成"
echo "============================================"

