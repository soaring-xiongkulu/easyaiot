# PostgreSQL pg_hba.conf 修复脚本使用说明

## 📋 问题描述

当应用程序连接 PostgreSQL 时出现以下错误：

```
psycopg2.OperationalError: connection to server at "localhost" (127.0.0.1), port 5432 failed: 
FATAL: no pg_hba.conf entry for host "172.18.0.1", user "postgres", database "iot-video20", no encryption
```

这个错误通常发生在以下情况：

- **Docker 网络问题**：应用程序从 Docker 网桥 IP（如 172.18.0.1）连接 PostgreSQL，但 `pg_hba.conf` 只允许本地连接
- **配置缺失**：PostgreSQL 的 `pg_hba.conf` 文件缺少允许远程主机连接的配置
- **配置未生效**：修改了 `pg_hba.conf` 但未重新加载配置

## 🚀 快速修复步骤

### 方法一：一键修复（推荐！）

```bash
# 进入VIDEO目录
cd /opt/projects/easyaiot/VIDEO

# 运行修复脚本（自动检查、修复、验证）
bash fix_postgresql_pg_hba.sh
```

这个脚本会自动：
1. ✅ 检查 Docker 和 PostgreSQL 容器状态
2. ✅ 查找正确的 `pg_hba.conf` 文件路径
3. ✅ 检查当前配置
4. ✅ 添加允许所有主机连接的配置（如果缺失）
5. ✅ 重新加载 PostgreSQL 配置
6. ✅ 验证数据库连接

### 方法二：仅检查配置（不修改）

```bash
# 进入VIDEO目录
cd /opt/projects/easyaiot/VIDEO

# 仅检查配置，不进行修改
bash fix_postgresql_pg_hba.sh --check-only
```

### 方法三：强制重新添加配置

```bash
# 进入VIDEO目录
cd /opt/projects/easyaiot/VIDEO

# 强制重新添加配置（即使已存在）
bash fix_postgresql_pg_hba.sh --force
```

## 📝 详细使用说明

### 脚本参数

```bash
bash fix_postgresql_pg_hba.sh [选项]

选项：
  --check-only    仅检查配置，不进行修改
  --force         强制重新添加配置（即使已存在）
  -h, --help      显示帮助信息（在脚本中查看）
```

### 使用示例

#### 示例 1：检查配置状态

```bash
bash fix_postgresql_pg_hba.sh --check-only
```

输出示例：
```
========================================
  PostgreSQL pg_hba.conf 修复工具
========================================

[INFO] PostgreSQL 容器: postgres-server
[INFO] PostgreSQL 用户: postgres
[INFO] PostgreSQL 数据库: iot-video20

[INFO] 检查 Docker 服务状态...
[SUCCESS] Docker 服务正在运行
[INFO] 检查 PostgreSQL 容器状态...
[SUCCESS] PostgreSQL 容器正在运行
[INFO] 等待 PostgreSQL 服务就绪...
[SUCCESS] PostgreSQL 服务已就绪
[INFO] 查找 PostgreSQL pg_hba.conf 文件路径...
[SUCCESS] 找到 pg_hba.conf 文件: /var/lib/postgresql/data/pgdata/pg_hba.conf
[INFO] 检查 pg_hba.conf 配置...
[SUCCESS] pg_hba.conf 已包含允许所有主机连接的配置
[SUCCESS] 配置检查通过，无需修复
```

#### 示例 2：修复配置

```bash
bash fix_postgresql_pg_hba.sh
```

输出示例：
```
========================================
  PostgreSQL pg_hba.conf 修复工具
========================================

[INFO] PostgreSQL 容器: postgres-server
[INFO] PostgreSQL 用户: postgres
[INFO] PostgreSQL 数据库: iot-video20

[INFO] 检查 Docker 服务状态...
[SUCCESS] Docker 服务正在运行
[INFO] 检查 PostgreSQL 容器状态...
[SUCCESS] PostgreSQL 容器正在运行
[INFO] 等待 PostgreSQL 服务就绪...
[SUCCESS] PostgreSQL 服务已就绪
[INFO] 查找 PostgreSQL pg_hba.conf 文件路径...
[SUCCESS] 找到 pg_hba.conf 文件: /var/lib/postgresql/data/pgdata/pg_hba.conf
[INFO] 检查 pg_hba.conf 配置...
[WARNING] pg_hba.conf 缺少允许所有主机连接的配置
[INFO] 添加允许所有主机连接的配置到 pg_hba.conf...
[SUCCESS] 已备份 pg_hba.conf 到: /var/lib/postgresql/data/pgdata/pg_hba.conf.backup.20241206_101530
[SUCCESS] 已添加配置到 pg_hba.conf
[INFO] 重新加载 PostgreSQL 配置...
[SUCCESS] PostgreSQL 配置已重新加载
[INFO] 测试数据库连接...
[SUCCESS] 数据库连接测试成功

========================================
  修复完成
========================================
[SUCCESS] PostgreSQL pg_hba.conf 配置已修复
```

## ⚙️ 配置说明

脚本会自动从以下位置读取配置（按优先级）：

1. **命令行参数**（最高优先级）
2. **环境变量**
   - `POSTGRES_CONTAINER` - PostgreSQL 容器名称（默认: postgres-server）
   - `POSTGRES_USER` - PostgreSQL 用户名（默认: postgres）
   - `POSTGRES_PASSWORD` - PostgreSQL 密码
   - `POSTGRES_DB` - PostgreSQL 数据库名
3. **.env文件**（在VIDEO目录下）
   - 从 `DATABASE_URL` 环境变量中解析配置
   - 格式：`postgresql://用户名:密码@主机:端口/数据库名`

### 配置示例

`.env` 文件中的 `DATABASE_URL` 示例：

```bash
# Docker 环境（使用容器服务名称）
DATABASE_URL=postgresql://postgres:iot45722414822@PostgresSQL:5432/iot-video20

# 宿主机环境（使用 localhost）
DATABASE_URL=postgresql://postgres:iot45722414822@localhost:5432/iot-video20
```

## 🔧 工作原理

### 1. 查找 pg_hba.conf 文件

脚本会按以下顺序查找配置文件：

1. 通过 PostgreSQL 查询 `SHOW hba_file;` 获取实际路径
2. 尝试常见路径：
   - `/var/lib/postgresql/data/pgdata/pg_hba.conf`（推荐，使用 PGDATA 子目录时）
   - `/var/lib/postgresql/data/pg_hba.conf`
   - `/var/lib/postgresql/pg_hba.conf`

### 2. 检查配置

脚本会检查 `pg_hba.conf` 中是否包含以下配置：

```conf
host    all             all             0.0.0.0/0               md5
host    all             all             ::/0                    md5
```

- `0.0.0.0/0` - 允许所有 IPv4 地址连接
- `::/0` - 允许所有 IPv6 地址连接
- `md5` - 使用 MD5 密码认证

### 3. 添加配置

如果配置缺失，脚本会：

1. **备份原文件**：创建带时间戳的备份文件
2. **添加配置**：在文件末尾追加允许所有主机连接的规则
3. **重新加载配置**：执行 `SELECT pg_reload_conf();` 使配置生效

### 4. 验证连接

脚本会尝试使用 `psql` 客户端连接数据库，验证配置是否生效。

## 🛠️ 故障排查

### 问题 1：容器不存在或未运行

**错误信息**：
```
[ERROR] PostgreSQL 容器 'postgres-server' 不存在
```

**解决方法**：
```bash
# 检查容器状态
docker ps -a | grep postgres

# 如果容器存在但未运行，启动它
docker start postgres-server

# 如果容器不存在，需要先启动中间件
cd .scripts/docker
docker-compose up -d PostgresSQL
```

### 问题 2：PostgreSQL 服务未就绪

**错误信息**：
```
[ERROR] PostgreSQL 服务未就绪
```

**解决方法**：
```bash
# 查看容器日志
docker logs postgres-server

# 等待容器完全启动（通常需要 10-30 秒）
sleep 30

# 检查服务状态
docker exec postgres-server pg_isready -U postgres
```

### 问题 3：无法找到 pg_hba.conf 文件

**错误信息**：
```
[ERROR] 无法找到 pg_hba.conf 文件
```

**解决方法**：
```bash
# 手动查找文件
docker exec postgres-server find /var/lib/postgresql -name "pg_hba.conf"

# 检查 PostgreSQL 配置
docker exec postgres-server psql -U postgres -c "SHOW hba_file;"
```

### 问题 4：配置已添加但连接仍失败

**可能原因**：
1. 配置未重新加载
2. 防火墙阻止连接
3. PostgreSQL 监听地址配置问题

**解决方法**：
```bash
# 1. 手动重新加载配置
docker exec postgres-server psql -U postgres -c "SELECT pg_reload_conf();"

# 2. 重启 PostgreSQL 容器（如果重新加载失败）
docker restart postgres-server

# 3. 检查 PostgreSQL 监听地址
docker exec postgres-server psql -U postgres -c "SHOW listen_addresses;"

# 4. 检查端口映射
docker ps | grep postgres
# 应该看到: 0.0.0.0:5432->5432/tcp

# 5. 测试连接
PGPASSWORD=iot45722414822 psql -h localhost -U postgres -d iot-video20 -c "SELECT 1;"
```

### 问题 5：权限问题

**错误信息**：
```
Permission denied
```

**解决方法**：
```bash
# 检查文件权限
docker exec postgres-server ls -la /var/lib/postgresql/data/pgdata/pg_hba.conf

# 如果权限不正确，修复权限
docker exec postgres-server chown postgres:postgres /var/lib/postgresql/data/pgdata/pg_hba.conf
docker exec postgres-server chmod 600 /var/lib/postgresql/data/pgdata/pg_hba.conf
```

## 📊 配置说明

### pg_hba.conf 配置规则

脚本添加的配置规则说明：

```conf
# 允许从宿主机和所有网络连接（由修复脚本自动添加）
host    all             all             0.0.0.0/0               md5
host    all             all             ::/0                    md5
```

- **host**：TCP/IP 连接（加密或非加密）
- **all**：所有数据库
- **all**：所有用户
- **0.0.0.0/0**：所有 IPv4 地址
- **::/0**：所有 IPv6 地址
- **md5**：MD5 密码认证

### 安全注意事项

⚠️ **警告**：允许所有主机连接（0.0.0.0/0）会降低安全性。在生产环境中，建议：

1. **限制 IP 范围**：只允许特定网段连接
   ```conf
   host    all    all    172.18.0.0/16    md5
   ```

2. **使用 SSL**：配置 SSL 连接
   ```conf
   hostssl    all    all    0.0.0.0/0    md5
   ```

3. **防火墙规则**：在系统层面限制访问

## 🔄 持久化说明

### 配置持久化

- ✅ 配置文件存储在 Docker 数据卷中，容器重启后配置会保留
- ✅ 备份文件会保存在同一目录，文件名格式：`pg_hba.conf.backup.YYYYMMDD_HHMMSS`

### 容器重建

如果 PostgreSQL 容器被删除并重新创建：

1. **数据卷保留**：如果使用命名卷或绑定挂载，配置会保留
2. **数据卷删除**：如果数据卷被删除，需要重新运行修复脚本

## 📚 相关文档

- [PostgreSQL 官方文档 - Client Authentication](https://www.postgresql.org/docs/current/auth-pg-hba-conf.html)
- [Docker PostgreSQL 镜像文档](https://hub.docker.com/_/postgres)
- [VIDEO 服务 README](../README.md)

## 💡 常见问题

### Q1: 为什么需要允许所有主机连接？

A: 在 Docker 环境中，应用程序可能从不同的网络接口（如 Docker 网桥 IP 172.18.0.1）连接 PostgreSQL，而不是 localhost。允许所有主机连接可以确保从任何网络接口都能连接。

### Q2: 配置修改后需要重启容器吗？

A: 不需要。脚本会自动执行 `pg_reload_conf()` 重新加载配置。只有在重新加载失败时才需要重启容器。

### Q3: 如何撤销修改？

A: 脚本会自动创建备份文件。您可以：
```bash
# 1. 找到备份文件
docker exec postgres-server ls -la /var/lib/postgresql/data/pgdata/pg_hba.conf.backup.*

# 2. 恢复备份
docker exec postgres-server cp /var/lib/postgresql/data/pgdata/pg_hba.conf.backup.20241206_101530 \
    /var/lib/postgresql/data/pgdata/pg_hba.conf

# 3. 重新加载配置
docker exec postgres-server psql -U postgres -c "SELECT pg_reload_conf();"
```

### Q4: 脚本可以用于生产环境吗？

A: 可以，但建议：
1. 先使用 `--check-only` 检查配置
2. 在生产环境应用前，先在测试环境验证
3. 考虑使用更严格的 IP 限制而不是 0.0.0.0/0

## 📞 支持

如果遇到问题，请：

1. 查看脚本输出日志
2. 检查 PostgreSQL 容器日志：`docker logs postgres-server`
3. 查看本文档的故障排查部分
4. 联系技术支持

---

**最后更新**：2024-12-06  
**脚本版本**：1.0.0

