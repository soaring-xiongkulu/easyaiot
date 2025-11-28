# PostgreSQL 权限问题修复指南

## 问题描述

启动 DEVICE 服务时，偶尔会遇到以下错误：

```
org.postgresql.util.PSQLException: FATAL: could not open file "global/pg_filenode.map": Permission denied
```

这是一个 PostgreSQL 数据目录权限问题，通常发生在：
- 系统重启后
- Docker 容器重启后
- 数据目录权限被意外修改后

## 问题原因

PostgreSQL 容器使用 **UID 999** 运行，但数据目录可能被其他用户拥有（如 root 或其他用户），导致 PostgreSQL 进程无法访问数据文件。

### 为什么是"偶尔"出现？

1. **系统重启后**：如果数据目录在重启时被挂载或权限被重置
2. **Docker 更新后**：Docker 版本更新可能影响卷挂载权限
3. **手动操作后**：如果手动修改了数据目录权限
4. **容器重建后**：容器被删除重建时，权限可能不正确

## 快速修复方案

### 方案 1：使用快速修复脚本（推荐）

```bash
cd .scripts/docker
./fix_postgresql_permissions.sh
```

该脚本会：
1. 停止 PostgreSQL 容器
2. 修复数据目录权限（设置为 999:999）
3. 重新启动 PostgreSQL 容器
4. 测试数据库连接

### 方案 2：使用 Docker Compose 初始化容器

```bash
cd .scripts/docker
docker-compose run --rm PostgresSQL-init
docker-compose up -d PostgresSQL
```

### 方案 3：手动修复

#### 步骤 1：停止 PostgreSQL 容器

```bash
cd .scripts/docker
docker stop postgres-server
```

#### 步骤 2：修复权限

```bash
# 设置正确的权限（PostgreSQL 容器使用 UID 999）
sudo chown -R 999:999 db_data/data db_data/log
sudo chmod -R 700 db_data/data
sudo chmod -R 755 db_data/log
```

#### 步骤 3：重新启动容器

```bash
docker-compose up -d PostgresSQL
```

#### 步骤 4：验证修复

```bash
# 检查容器状态
docker ps | grep postgres-server

# 测试数据库连接
docker exec postgres-server psql -U postgres -d postgres -c "SELECT version();"
```

## 验证权限

修复后，可以验证权限是否正确：

```bash
cd .scripts/docker
ls -la db_data/data
```

应该看到类似输出：
```
drwx------ 999 999 ... data/
```

关键点：
- **所有者应该是 999:999**（或显示为 postgres:postgres，但 UID/GID 是 999）
- **权限应该是 700**（drwx------）

## 预防措施

### 1. 在安装脚本中确保权限正确

确保安装脚本在创建数据目录时设置正确权限：

```bash
mkdir -p db_data/data db_data/log
sudo chown -R 999:999 db_data/data db_data/log
sudo chmod -R 700 db_data/data
sudo chmod -R 755 db_data/log
```

### 2. 使用 Docker Compose 初始化容器

在 `docker-compose.yml` 中已经配置了 `PostgresSQL-init` 容器，可以在需要时运行：

```bash
docker-compose run --rm PostgresSQL-init
```

### 3. 定期检查权限

可以创建一个检查脚本：

```bash
#!/bin/bash
cd .scripts/docker
OWNER=$(stat -c "%u:%g" db_data/data 2>/dev/null)
if [ "$OWNER" != "999:999" ]; then
    echo "警告：数据目录权限不正确！当前: $OWNER，应该是: 999:999"
    echo "运行修复脚本: ./fix_postgresql_permissions.sh"
fi
```

## 常见问题

### Q: 修复后仍然报错？

A: 检查以下几点：
1. **确认权限已正确设置**：
   ```bash
   ls -la db_data/data
   # 应该显示 999:999 和 700 权限
   ```

2. **检查容器内的权限**：
   ```bash
   docker exec postgres-server ls -la /var/lib/postgresql/data
   ```

3. **查看容器日志**：
   ```bash
   docker logs postgres-server
   ```

4. **确认数据目录挂载正确**：
   ```bash
   docker inspect postgres-server | grep -A 10 Mounts
   ```

### Q: 为什么需要 sudo？

A: 因为需要修改文件所有者，这通常需要 root 权限。如果不想使用 sudo，可以：
1. 以 root 用户运行脚本
2. 配置 sudoers 允许无密码执行 chown/chmod（不推荐）

### Q: 数据会丢失吗？

A: **不会**。修复脚本只修改权限，不会删除或修改数据文件。

### Q: 如何避免这个问题？

A: 
1. 确保安装脚本正确设置权限
2. 避免手动修改数据目录权限
3. 使用提供的修复脚本而不是手动操作
4. 定期检查权限是否正确

## 技术细节

### PostgreSQL 容器用户

PostgreSQL 官方镜像使用：
- **UID**: 999
- **GID**: 999
- **用户名**: postgres

### 数据目录要求

- **所有者**: 999:999
- **权限**: 700 (drwx------)
- **位置**: `/var/lib/postgresql/data`（容器内）

### 为什么是 999？

PostgreSQL 官方镜像选择 999 作为 UID/GID，这是一个常见的系统用户 ID 范围（100-999），避免与普通用户冲突。

## 相关文件

- `fix_postgresql_permissions.sh` - 快速权限修复脚本
- `fix_postgresql.sh` - 完整的 PostgreSQL 修复脚本（包括密码重置）
- `POSTGRESQL_FIX.md` - PostgreSQL 密码问题修复指南
- `docker-compose.yml` - Docker Compose 配置文件

## 联系支持

如果问题仍然存在，请：
1. 收集容器日志：`docker logs postgres-server > postgresql.log`
2. 检查数据目录权限：`ls -laR db_data/`
3. 提供错误信息和修复脚本输出

