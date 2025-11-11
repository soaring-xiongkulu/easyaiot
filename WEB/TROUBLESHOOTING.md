# WEB服务故障排查指南

## 问题：nginx报499错误，VIDEO服务接口访问不通

### 问题描述
在云端服务器部署后，通过nginx访问VIDEO容器接口时，nginx返回499错误，但DEVICE容器的接口正常。

### 原因分析

1. **网络连接问题**：VIDEO服务使用`network_mode: host`，nginx容器需要通过宿主机IP访问
2. **host-gateway不工作**：某些云端服务器环境不支持`host-gateway`特性
3. **超时配置不足**：视频服务可能需要更长的响应时间

### 解决方案

#### 方案1：检查host-gateway是否工作

在web-service容器内测试连接：

```bash
# 进入web-service容器
docker exec -it web-service sh

# 测试video-host解析
ping video-host

# 测试端口连通性
wget -O- http://video-host:6000/actuator/health
```

如果ping不通或连接失败，说明`host-gateway`不工作，需要使用方案2。

#### 方案2：手动配置宿主机IP（推荐）

1. **获取宿主机IP地址**：

```bash
# 方法1：获取Docker默认网关IP
ip addr show docker0 | grep "inet " | awk '{print $2}' | cut -d/ -f1

# 方法2：获取宿主机主IP
hostname -I | awk '{print $1}'

# 方法3：获取默认网关IP
ip route | grep default | awk '{print $3}'
```

2. **修改docker-compose.yaml**：

编辑 `WEB/docker-compose.yaml`，找到 `extra_hosts` 部分，将 `host-gateway` 替换为实际IP：

```yaml
extra_hosts:
  - "gateway:172.17.0.1"        # 替换为实际宿主机IP
  - "video-host:172.17.0.1"     # 替换为实际宿主机IP
  - "ai-host:172.17.0.1"        # 替换为实际宿主机IP
```

3. **重启web-service容器**：

```bash
cd WEB
docker-compose down
docker-compose up -d
```

#### 方案3：检查VIDEO服务是否正常运行

```bash
# 检查VIDEO服务容器状态
docker ps | grep video-service

# 检查VIDEO服务日志
docker logs video-service --tail 100

# 在宿主机上直接测试VIDEO服务
curl http://localhost:6000/actuator/health
```

#### 方案4：检查防火墙和端口

确保宿主机6000端口没有被防火墙阻止：

```bash
# 检查端口监听
netstat -tlnp | grep 6000
# 或
ss -tlnp | grep 6000

# 检查防火墙规则（如果使用iptables）
iptables -L -n | grep 6000

# 检查防火墙规则（如果使用firewalld）
firewall-cmd --list-ports
```

### 验证修复

修复后，通过以下方式验证：

1. **测试健康检查接口**：
```bash
curl http://your-server-ip:8888/dev-api/video/camera/health
```

2. **查看nginx日志**：
```bash
docker logs web-service --tail 50
# 或
tail -f WEB/logs/access.log
tail -f WEB/logs/error.log
```

3. **在浏览器中测试**：
访问 `http://your-server-ip:8888/dev-api/video/camera/xxx`，应该能正常返回数据。

### 常见错误码说明

- **499**：客户端关闭连接（通常是nginx无法连接到后端或超时）
- **502**：网关错误（后端服务不可用）
- **503**：服务不可用（后端服务未启动）
- **504**：网关超时（后端服务响应超时）

### 其他注意事项

1. **确保VIDEO服务使用host网络模式**：检查 `VIDEO/docker-compose.yaml` 中 `network_mode: host` 配置
2. **确保VIDEO服务监听在0.0.0.0:6000**：检查环境变量 `FLASK_RUN_HOST=0.0.0.0` 和 `FLASK_RUN_PORT=6000`
3. **检查nginx超时配置**：已在配置中添加了更长的超时时间（20分钟）

### 联系支持

如果以上方案都无法解决问题，请提供以下信息：

1. nginx错误日志：`WEB/logs/error.log`
2. VIDEO服务日志：`docker logs video-service`
3. 网络配置信息：`ip addr` 和 `docker network inspect easyaiot-network`
4. 宿主机IP地址和Docker版本信息

