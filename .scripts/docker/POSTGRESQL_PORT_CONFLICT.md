# PostgreSQL 端口冲突问题修复指南

## 问题描述

从宿主机连接 PostgreSQL Docker 容器时，出现以下错误：

```
psql: error: connection to server at "127.0.0.1", port 5432 failed: FATAL: password authentication failed for user "postgres"
```

虽然容器内连接正常，但宿主机连接失败。

## 问题原因

**根本原因**：宿主机上运行着 PostgreSQL 服务（通常是系统安装的 PostgreSQL），占用了 5432 端口，导致 Docker 容器无法正确绑定端口映射。

### 为什么会出现这个问题？

1. **端口被占用**：宿主机 PostgreSQL 服务监听在 0.0.0.0:5432 或 127.0.0.1:5432
2. **Docker 端口映射失败**：Docker 尝试绑定 5432 端口时失败，容器虽然启动，但端口映射未生效
3. **连接到了错误的服务**：从宿主机连接 127.0.0.1:5432 时，实际连接的是宿主机的 PostgreSQL，而不是 Docker 容器中的 PostgreSQL

### 如何确认问题？

运行以下命令检查：

```bash
# 检查端口占用
ss -tlnp | grep 5432
# 或
netstat -tlnp | grep 5432

# 检查是否有宿主机 PostgreSQL 进程
ps aux | grep postgres | grep -v docker

# 检查 Docker 容器端口映射
docker inspect postgres-server --format '{{json .HostConfig.PortBindings}}'
```

如果端口被非 Docker 进程占用，且 Docker 容器端口映射为空 `{}`，则确认是端口冲突问题。

## 解决方案

### 方案 1：停止宿主机 PostgreSQL 服务（推荐）

如果不需要使用宿主机的 PostgreSQL 服务，可以停止它：

```bash
# 停止服务
sudo systemctl stop postgresql

# 禁止开机自启（可选）
sudo systemctl disable postgresql

# 重新启动 Docker 容器
cd .scripts/docker
docker-compose stop PostgresSQL
docker-compose up -d PostgresSQL
```

### 方案 2：修改 Docker 容器端口映射

如果需要在宿主机上同时运行 PostgreSQL 服务，可以修改 Docker 容器的端口映射：

1. 编辑 `docker-compose.yml`：

```yaml
PostgresSQL:
  ports:
    - "5433:5432"  # 改为使用 5433 作为宿主机端口
```

2. 更新所有连接配置中的端口号（从 5432 改为 5433）

3. 重新启动容器：

```bash
docker-compose stop PostgresSQL
docker-compose up -d PostgresSQL
```

### 方案 3：修改宿主机 PostgreSQL 端口

如果需要在宿主机上运行 PostgreSQL，但想让它使用其他端口：

1. 编辑 PostgreSQL 配置文件：

```bash
sudo nano /etc/postgresql/*/main/postgresql.conf
# 修改 port = 5433
```

2. 重启宿主机 PostgreSQL 服务：

```bash
sudo systemctl restart postgresql
```

3. 重新启动 Docker 容器：

```bash
cd .scripts/docker
docker-compose stop PostgresSQL
docker-compose up -d PostgresSQL
```

## 使用自动修复脚本

我们提供了自动检测和修复脚本：

```bash
cd .scripts/docker
./fix_postgresql_port_conflict.sh
```

该脚本会：
1. 自动检测端口冲突
2. 提供解决方案选项
3. 可选择自动停止宿主机 PostgreSQL 服务
4. 自动重启 Docker 容器

## 验证修复

修复后，运行测试脚本验证：

```bash
cd .scripts/docker
./test_postgresql_connection.sh
```

如果修复成功，应该能看到：
- ✅ Docker 容器端口映射配置正常
- ✅ psql 连接测试成功

## 相关脚本

- `test_postgresql_connection.sh` - 连接测试脚本（已更新，可检测端口冲突）
- `fix_postgresql_port_conflict.sh` - 端口冲突修复脚本（新增）
- `fix_postgresql_password.sh` - 密码修复脚本

## 注意事项

1. **数据安全**：停止宿主机 PostgreSQL 服务前，确保没有重要数据依赖该服务
2. **服务依赖**：检查是否有其他服务依赖宿主机的 PostgreSQL
3. **端口选择**：如果修改端口，确保新端口未被其他服务占用

## 常见问题

### Q: 为什么容器内连接正常，但宿主机连接失败？

A: 因为 Docker 容器的端口映射未生效，从宿主机连接时实际连接的是宿主机的 PostgreSQL 服务，而不是容器内的服务。

### Q: 如何确认连接的是哪个 PostgreSQL？

A: 运行以下命令查看 PostgreSQL 版本：

```bash
# 宿主机连接（如果端口映射正常，应该显示容器内的版本）
psql -h 127.0.0.1 -p 5432 -U postgres -c "SELECT version();"

# 容器内连接（直接显示容器内的版本）
docker exec postgres-server psql -U postgres -c "SELECT version();"
```

如果两个版本不同，说明连接的是不同的 PostgreSQL 实例。

### Q: 修改端口后如何更新应用配置？

A: 需要更新所有使用 PostgreSQL 的应用配置，将端口从 5432 改为新的端口（如 5433）。

