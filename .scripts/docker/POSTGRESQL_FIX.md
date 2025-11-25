# PostgreSQL 密码重置问题修复指南

## 问题描述

PostgreSQL 容器在电脑重启后重新启动时，数据库密码可能会发生变化，导致应用程序无法连接，出现以下错误：

```
Caused by: org.postgresql.util.PSQLException: FATAL: password authentication failed for user "postgres"
```

## 问题原因

1. **PGDATA 子目录问题**：之前的配置使用了 `PGDATA=/var/lib/postgresql/data/pgdata`，如果这个子目录不存在或为空，PostgreSQL 会重新初始化数据库，此时会使用环境变量 `POSTGRES_PASSWORD` 中的密码，而不是已有的密码配置。

2. **数据目录权限问题**：如果数据目录权限不正确，PostgreSQL 容器可能无法读取已有的数据目录，导致重新初始化。

3. **数据目录为空**：如果数据目录被清空或损坏，PostgreSQL 会重新初始化。

## 解决方案

### 方案 1：使用修复脚本（推荐）

运行修复脚本自动处理所有问题：

```bash
cd .scripts/docker
./fix_postgresql.sh
```

该脚本会：
1. 停止 PostgreSQL 容器
2. 修复数据目录权限
3. 迁移数据（如果需要，从 `pgdata` 子目录迁移到根目录）
4. 重新启动 PostgreSQL 容器
5. 测试数据库连接

### 方案 2：手动修复

#### 步骤 1：停止 PostgreSQL 容器

```bash
cd .scripts/docker
docker stop postgres-server
```

#### 步骤 2：检查数据目录

```bash
# 检查数据目录是否存在
ls -la db_data/data/

# 如果数据在 pgdata 子目录中，需要迁移
# 如果存在 db_data/data/pgdata 目录，需要将其内容移动到 db_data/data/ 根目录
```

#### 步骤 3：修复权限

```bash
# 设置正确的权限（PostgreSQL 容器使用 UID 999）
sudo chown -R 999:999 db_data/data db_data/log
sudo chmod -R 700 db_data/data
sudo chmod -R 755 db_data/log
```

#### 步骤 4：重新启动容器

```bash
# 使用 docker-compose 重新启动
docker-compose up -d PostgresSQL

# 或者使用 docker compose (v2)
docker compose up -d PostgresSQL
```

#### 步骤 5：验证连接

```bash
# 测试数据库连接（使用配置的密码）
docker exec postgres-server psql -U postgres -d postgres -c "SELECT version();"
```

## 配置变更说明

### 已移除的配置

- **移除了 `PGDATA` 环境变量**：之前使用 `PGDATA=/var/lib/postgresql/data/pgdata`，现在使用默认路径 `/var/lib/postgresql/data`

### PostgreSQL 行为说明

PostgreSQL 官方镜像的行为：
- **如果数据目录已存在且不为空**：不会重新初始化，使用已有的密码配置
- **如果数据目录为空**：会使用 `POSTGRES_PASSWORD` 环境变量初始化数据库

### 数据目录结构

修复后的数据目录结构：
```
.scripts/docker/
└── db_data/
    ├── data/          # PostgreSQL 数据目录（直接存储数据，不再使用 pgdata 子目录）
    └── log/           # PostgreSQL 日志目录
```

## 预防措施

1. **定期备份数据**：确保定期备份 PostgreSQL 数据目录
2. **检查权限**：确保数据目录权限正确（UID 999:999）
3. **监控日志**：定期检查容器日志，及时发现问题

## 验证修复

修复后，验证以下内容：

1. **容器状态**：
   ```bash
   docker ps | grep postgres-server
   ```

2. **数据库连接**：
   ```bash
   docker exec postgres-server psql -U postgres -d postgres -c "SELECT version();"
   ```

3. **应用程序连接**：确保应用程序可以正常连接数据库

## 常见问题

### Q: 修复后仍然无法连接？

A: 检查以下几点：
1. 确认容器正在运行：`docker ps | grep postgres-server`
2. 查看容器日志：`docker logs postgres-server`
3. 确认应用程序使用的密码是：`iot45722414822`
4. 检查数据目录权限：`ls -la db_data/data/`

### Q: 数据会丢失吗？

A: 不会。修复脚本会：
- 检查现有数据
- 如果数据在 `pgdata` 子目录中，会迁移到根目录
- 不会删除任何现有数据

### Q: 如果数据目录已损坏怎么办？

A: 如果有备份，可以：
1. 停止容器
2. 删除损坏的数据目录
3. 恢复备份
4. 重新启动容器

如果没有备份，可能需要重新初始化数据库（**会丢失数据**）。

## 联系支持

如果问题仍然存在，请：
1. 收集容器日志：`docker logs postgres-server > postgresql.log`
2. 检查数据目录结构：`ls -laR db_data/`
3. 提供错误信息和应用配置

