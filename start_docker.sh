#!/bin/bash

# Docker服务启动脚本
# 使用方法: sudo bash start_docker.sh
# 注意: 如果Docker服务文件不存在，脚本会自动创建

echo "========================================="
echo "检查Docker服务状态..."
echo "========================================="

# 检查Docker是否已安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

echo "✅ Docker已安装: $(docker --version)"

# 检查Docker systemd服务文件是否存在
if [ ! -f /etc/systemd/system/docker.service ] && [ ! -f /lib/systemd/system/docker.service ]; then
    echo ""
    echo "⚠️  未找到Docker systemd服务文件"
    echo "   这通常意味着Docker是通过非标准方式安装的"
    echo ""
    echo "正在创建Docker systemd服务文件..."
    
    # 检查是否有创建脚本
    if [ -f "$(dirname "$0")/create_docker_service.sh" ]; then
        echo "   运行创建脚本: sudo bash $(dirname "$0")/create_docker_service.sh"
        if [ "$EUID" -eq 0 ]; then
            bash "$(dirname "$0")/create_docker_service.sh"
        else
            echo "   需要root权限，请运行:"
            echo "   sudo bash $(dirname "$0")/create_docker_service.sh"
            exit 1
        fi
    else
        echo "   未找到create_docker_service.sh脚本"
        echo "   请手动创建systemd服务文件或重新安装Docker"
        exit 1
    fi
    exit 0
fi

# 检查Docker服务状态
if systemctl is-active --quiet docker; then
    echo "✅ Docker服务已在运行"
    docker ps
    exit 0
fi

echo "⚠️  Docker服务未运行，正在启动..."

# 启动Docker服务
if systemctl start docker; then
    echo "✅ Docker服务启动成功"
    
    # 等待服务完全启动
    sleep 2
    
    # 验证服务状态
    if systemctl is-active --quiet docker; then
        echo "✅ Docker服务运行正常"
        echo ""
        echo "当前运行的容器:"
        docker ps
        echo ""
        echo "所有容器（包括已停止的）:"
        docker ps -a
    else
        echo "❌ Docker服务启动后状态异常"
        exit 1
    fi
    
    # 检查是否已设置开机自启
    if ! systemctl is-enabled --quiet docker 2>/dev/null; then
        echo ""
        echo "⚠️  Docker服务未设置开机自启"
        if [ "$EUID" -eq 0 ]; then
            systemctl enable docker
            echo "✅ 已设置Docker开机自启"
        else
            echo "   需要root权限设置开机自启，请运行:"
            echo "   sudo systemctl enable docker"
        fi
    fi
else
    echo "❌ Docker服务启动失败"
    echo ""
    echo "请检查以下内容:"
    echo "1. 是否有足够的权限（需要sudo）"
    echo "2. 查看详细错误信息: sudo systemctl status docker"
    echo "3. 查看日志: sudo journalctl -u docker -n 50"
    exit 1
fi

