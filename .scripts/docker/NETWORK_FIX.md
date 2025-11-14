# Docker网络修复指南

## 问题描述

当宿主机IP地址发生变化后，Redis容器（或其他容器）可能无法加入 `easyaiot-network` 网络。

### 原因分析

1. **Docker网络配置缓存**：Docker网络在创建时会记录一些网络配置信息，当宿主机IP变化时，这些配置可能不再有效
2. **网络状态不一致**：IP变化可能导致网络内部状态与宿主机网络环境不匹配
3. **容器网络连接失败**：由于网络配置问题，容器尝试加入网络时会失败

## 解决方案

### 方案1：自动修复（推荐）

安装脚本已自动集成了网络检测和修复功能。当运行安装脚本时，如果检测到网络问题，会自动尝试修复：

```bash
cd /projects/easyaiot
./.scripts/install_all.sh restart
```

### 方案2：使用修复脚本

如果自动修复失败，可以使用专门的修复脚本：

```bash
cd /projects/easyaiot/.scripts/docker
./fix_network.sh
```

修复脚本会：
1. 检查网络状态
2. 列出使用该网络的所有容器
3. 提供选项：自动停止容器并重新创建网络，或手动处理
4. 重新创建网络并验证

### 方案3：手动修复

如果上述方法都不行，可以手动执行以下步骤：

```bash
# 1. 停止所有相关容器
cd /projects/easyaiot/.scripts/docker
docker-compose down

# 2. 删除旧网络
docker network rm easyaiot-network

# 3. 重新创建网络
docker network create easyaiot-network

# 4. 重新启动容器
docker-compose up -d
```

## 预防措施

1. **固定IP地址**：如果可能，建议为服务器配置固定IP地址
2. **使用DHCP保留**：在DHCP服务器上为设备配置IP地址保留
3. **定期检查**：定期运行 `docker network inspect easyaiot-network` 检查网络状态

## 验证网络状态

检查网络是否正常：

```bash
# 查看网络信息
docker network inspect easyaiot-network

# 测试网络连通性
docker run --rm --network easyaiot-network alpine:latest ping -c 1 8.8.8.8

# 查看连接到网络的容器
docker network inspect easyaiot-network --format '{{range .Containers}}{{.Name}} {{end}}'
```

## 常见错误

### 错误1：network not found
```
Error: network easyaiot-network not found
```
**解决方法**：运行修复脚本或手动创建网络

### 错误2：network is in use
```
Error: network easyaiot-network is in use
```
**解决方法**：先停止所有使用该网络的容器，然后删除网络

### 错误3：container cannot connect to network
```
Error: container cannot connect to network easyaiot-network
```
**解决方法**：删除并重新创建网络，然后重启容器

## 技术支持

如果以上方法都无法解决问题，请检查：
1. Docker服务是否正常运行：`systemctl status docker`
2. 系统日志：`journalctl -u docker -n 50`
3. Docker网络列表：`docker network ls`
4. 容器状态：`docker ps -a`

