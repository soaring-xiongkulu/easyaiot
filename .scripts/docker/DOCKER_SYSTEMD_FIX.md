# Docker systemd 服务启动失败修复指南

## 问题描述

当遇到以下错误时：
```
Failed to get properties: 连接超时
Failed to start docker.service: Failed to activate service 'org.freedesktop.systemd1': timed out
```

这通常表示 systemd 无法在默认超时时间内启动 Docker 服务。

## 快速修复

### 方法 1: 使用诊断脚本（推荐）

```bash
# 1. 诊断问题
sudo .scripts/docker/diagnose_docker_systemd.sh diagnose

# 2. 执行所有修复
sudo .scripts/docker/diagnose_docker_systemd.sh fix-all
```

### 方法 2: 手动修复

#### 步骤 1: 增加 systemd 超时时间

```bash
# 创建超时配置目录
sudo mkdir -p /etc/systemd/system/docker.service.d

# 创建超时配置文件
sudo tee /etc/systemd/system/docker.service.d/timeout.conf > /dev/null << 'EOF'
[Service]
TimeoutStartSec=300
TimeoutStopSec=60
EOF

# 重新加载 systemd 配置
sudo systemctl daemon-reload
```

#### 步骤 2: 重置服务状态

```bash
# 重置失败的服务状态
sudo systemctl reset-failed docker.service

# 停止可能存在的 Docker 进程
sudo pkill -9 dockerd || true
sudo pkill -9 docker-containerd || true

# 清理 socket
sudo rm -f /var/run/docker.sock
sudo rm -f /var/run/docker.pid
```

#### 步骤 3: 启动 Docker 服务

```bash
# 启动服务
sudo systemctl start docker

# 验证服务状态
sudo systemctl status docker

# 测试 Docker
docker --version
docker ps
```

## 常见原因

1. **systemd 超时时间过短**: 默认超时时间可能不足以启动 Docker
2. **系统资源不足**: 内存或磁盘空间不足
3. **Docker 数据目录损坏**: `/var/lib/docker` 可能存在问题
4. **systemd 守护进程问题**: systemd 本身可能存在问题
5. **进程冲突**: 旧的 Docker 进程可能仍在运行

## 详细诊断

运行诊断脚本获取详细信息：

```bash
sudo .scripts/docker/diagnose_docker_systemd.sh diagnose
```

诊断脚本会检查：
- systemd 状态和日志
- Docker 服务配置
- 系统资源（磁盘、内存）
- Docker 相关文件和目录
- 进程状态

## 其他解决方案

### 如果 systemd 本身有问题

```bash
# 检查 systemd 状态
sudo systemctl is-system-running

# 重启 systemd（谨慎使用）
sudo systemctl daemon-reexec
```

### 如果 Docker 数据目录有问题

```bash
# 备份 Docker 数据（如果需要）
sudo tar -czf /tmp/docker-backup-$(date +%Y%m%d).tar.gz /var/lib/docker

# 停止 Docker 服务
sudo systemctl stop docker

# 清理 Docker 数据（警告：会删除所有容器和镜像）
sudo rm -rf /var/lib/docker/*

# 重新启动 Docker
sudo systemctl start docker
```

### 如果问题持续存在

1. **检查系统日志**:
   ```bash
   sudo journalctl -xe
   sudo journalctl -u docker.service -n 100
   ```

2. **检查磁盘空间**:
   ```bash
   df -h
   ```

3. **检查内存**:
   ```bash
   free -h
   ```

4. **重新安装 Docker**（最后手段）:
   ```bash
   # 卸载 Docker
   sudo apt-get remove docker docker-engine docker.io containerd runc
   
   # 重新安装（参考 Docker 官方文档）
   ```

## 验证修复

修复后，验证 Docker 是否正常工作：

```bash
# 检查服务状态
sudo systemctl status docker

# 测试 Docker 命令
docker --version
docker ps
docker info

# 运行测试容器
docker run hello-world
```

## 预防措施

1. **设置合适的超时时间**: 使用上面的超时配置
2. **监控系统资源**: 确保有足够的磁盘空间和内存
3. **定期清理**: 清理未使用的 Docker 资源
   ```bash
   docker system prune -a
   ```

## 相关文件

- 诊断脚本: `.scripts/docker/diagnose_docker_systemd.sh`
- 安装脚本: `.scripts/docker/install_all.sh`
- Docker 服务配置: `/etc/systemd/system/docker.service.d/timeout.conf`

## 获取帮助

如果问题仍然存在，请：

1. 运行诊断脚本并保存输出
2. 收集系统日志: `sudo journalctl -u docker.service > docker-service.log`
3. 检查系统资源使用情况
4. 联系系统管理员或查看 Docker 官方文档

