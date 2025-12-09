#!/bin/bash

# 创建Docker systemd服务文件
# 使用方法: sudo bash create_docker_service.sh

set -e

echo "========================================="
echo "创建Docker systemd服务文件"
echo "========================================="

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo "❌ 此脚本需要root权限运行"
    echo "请使用: sudo bash create_docker_service.sh"
    exit 1
fi

# 检查dockerd是否存在
if [ ! -f /usr/bin/dockerd ]; then
    echo "❌ dockerd未找到: /usr/bin/dockerd"
    exit 1
fi

echo "✅ 找到dockerd: /usr/bin/dockerd"

# 检查containerd是否存在
if [ ! -f /usr/bin/containerd ]; then
    echo "⚠️  containerd未找到: /usr/bin/containerd"
    echo "   将使用dockerd内置的containerd"
fi

# 确保systemd服务目录存在
if [ ! -d /etc/systemd/system ]; then
    echo "❌ /etc/systemd/system 目录不存在"
    exit 1
fi

# 创建systemd服务目录
mkdir -p /etc/systemd/system/docker.service.d

# 检查containerd是否存在
HAS_CONTAINERD=false
if [ -f /usr/bin/containerd ]; then
    HAS_CONTAINERD=true
    echo "✅ 找到containerd: /usr/bin/containerd"
else
    echo "⚠️  containerd未找到，Docker将使用内置的containerd"
fi

# 创建Docker服务文件
echo "创建Docker服务文件..."
if [ "$HAS_CONTAINERD" = true ]; then
    # 如果containerd存在，使用外部containerd
    tee /etc/systemd/system/docker.service > /dev/null << 'EOF'
[Unit]
Description=Docker Application Container Engine
Documentation=https://docs.docker.com
After=network-online.target firewalld.service containerd.service
Wants=network-online.target
Requires=docker.socket containerd.service

[Service]
Type=notify
# 默认情况下，Docker使用systemd来管理容器的cgroup
ExecStart=/usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock
ExecReload=/bin/kill -s HUP $MAINPID
TimeoutStartSec=300
TimeoutStopSec=60
Restart=on-failure
RestartSec=5
LimitNOFILE=infinity
LimitNPROC=infinity
LimitCORE=infinity
TasksMax=infinity
Delegate=yes
KillMode=process
OOMScoreAdjust=-500

[Install]
WantedBy=multi-user.target
EOF
else
    # 如果containerd不存在，让Docker使用内置的containerd
    tee /etc/systemd/system/docker.service > /dev/null << 'EOF'
[Unit]
Description=Docker Application Container Engine
Documentation=https://docs.docker.com
After=network-online.target firewalld.service
Wants=network-online.target
Requires=docker.socket

[Service]
Type=notify
# Docker使用内置的containerd
ExecStart=/usr/bin/dockerd -H fd://
ExecReload=/bin/kill -s HUP $MAINPID
TimeoutStartSec=300
TimeoutStopSec=60
Restart=on-failure
RestartSec=5
LimitNOFILE=infinity
LimitNPROC=infinity
LimitCORE=infinity
TasksMax=infinity
Delegate=yes
KillMode=process
OOMScoreAdjust=-500

[Install]
WantedBy=multi-user.target
EOF
fi

# 检查docker组是否存在，如果不存在则创建
if ! getent group docker > /dev/null 2>&1; then
    echo "创建docker用户组..."
    groupadd docker || true
fi

# 创建Docker socket文件
echo "创建Docker socket文件..."
tee /etc/systemd/system/docker.socket > /dev/null << 'EOF'
[Unit]
Description=Docker Socket for the API

[Socket]
ListenStream=/var/run/docker.sock
SocketMode=0660
SocketUser=root
SocketGroup=docker

[Install]
WantedBy=sockets.target
EOF

# 创建containerd服务文件（如果containerd存在且服务文件不存在）
if [ "$HAS_CONTAINERD" = true ] && [ ! -f /etc/systemd/system/containerd.service ] && [ ! -f /lib/systemd/system/containerd.service ]; then
    echo "创建containerd服务文件..."
    tee /etc/systemd/system/containerd.service > /dev/null << 'EOF'
[Unit]
Description=containerd container runtime
Documentation=https://containerd.io
After=network.target local-fs.target

[Service]
ExecStartPre=-/sbin/modprobe overlay
ExecStart=/usr/bin/containerd
Type=notify
Delegate=yes
KillMode=process
Restart=always
RestartSec=5
LimitNPROC=infinity
LimitCORE=infinity
LimitNOFILE=1048576
TasksMax=infinity
OOMScoreAdjust=-999

[Install]
WantedBy=multi-user.target
EOF
fi

# 重新加载systemd配置
echo "重新加载systemd配置..."
systemctl daemon-reload

# 启用containerd服务（如果存在）
if [ "$HAS_CONTAINERD" = true ] && systemctl list-unit-files | grep -q containerd.service; then
    echo "启用containerd服务..."
    systemctl enable containerd.service || true
fi

# 启用Docker socket
echo "启用Docker socket..."
systemctl enable docker.socket

# 启用Docker服务
echo "启用Docker服务..."
systemctl enable docker.service

# 启动containerd（如果存在）
if [ "$HAS_CONTAINERD" = true ] && systemctl list-unit-files | grep -q containerd.service; then
    echo "启动containerd服务..."
    systemctl start containerd.service || true
    sleep 1
fi

# 启动Docker socket
echo "启动Docker socket..."
systemctl start docker.socket

# 启动Docker服务
echo "启动Docker服务..."
if systemctl start docker.service; then
    echo "✅ Docker服务启动成功"
    sleep 2
    
    # 验证服务状态
    if systemctl is-active --quiet docker.service; then
        echo "✅ Docker服务运行正常"
        echo ""
        echo "Docker版本信息:"
        docker --version
        echo ""
        echo "当前运行的容器:"
        docker ps
    else
        echo "⚠️  Docker服务启动后状态异常"
        echo "查看状态: sudo systemctl status docker"
        exit 1
    fi
else
    echo "❌ Docker服务启动失败"
    echo ""
    echo "查看详细错误信息:"
    systemctl status docker.service --no-pager -l
    echo ""
    echo "查看日志:"
    journalctl -u docker.service --no-pager -n 50
    exit 1
fi

echo ""
echo "========================================="
echo "✅ Docker服务配置完成！"
echo "========================================="
echo ""
echo "常用命令:"
echo "  查看状态: sudo systemctl status docker"
echo "  启动服务: sudo systemctl start docker"
echo "  停止服务: sudo systemctl stop docker"
echo "  重启服务: sudo systemctl restart docker"
echo "  查看日志: sudo journalctl -u docker -f"
echo ""

