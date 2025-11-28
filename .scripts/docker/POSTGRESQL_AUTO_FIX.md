# PostgreSQL 自动权限修复说明

## 概述

从 2025-11-28 开始，PostgreSQL 容器配置已更新，**自动在启动时修复数据目录权限问题**，无需手动干预。

## 问题原因

PostgreSQL 容器使用 **UID 999** 运行，但数据目录可能被其他用户拥有（如 root），导致错误：
```
FATAL: could not open file "global/pg_filenode.map": Permission denied
```

## 自动修复机制

### 1. Entrypoint 脚本

创建了 `postgresql-entrypoint.sh` 脚本，在 PostgreSQL 启动前：
1. 检查数据目录权限
2. 如果权限不正确，自动修复为 999:999
3. 然后切换到 postgres 用户启动 PostgreSQL

### 2. Docker Compose 配置

在 `docker-compose.yml` 中：
- PostgreSQL 容器以 **root 用户启动**（`user: "0:0"`）
- 使用自定义 entrypoint 脚本
- Entrypoint 修复权限后，使用 `gosu` 切换到 postgres 用户执行原始 entrypoint

### 3. Init 容器（备用）

保留了 `PostgresSQL-init` 容器作为备用方案，可以手动运行：
```bash
docker-compose run --rm PostgresSQL-init
```

## 工作流程

```
1. Docker Compose 启动 PostgreSQL 容器（root 用户）
   ↓
2. 执行 postgresql-entrypoint.sh
   ↓
3. 检查数据目录权限
   ↓
4. 如果权限不正确 → 修复为 999:999
   ↓
5. 使用 gosu 切换到 postgres 用户
   ↓
6. 执行原始 PostgreSQL entrypoint
   ↓
7. PostgreSQL 正常启动
```

## 优势

1. **自动化**：无需手动修复权限
2. **每次启动都检查**：确保权限始终正确
3. **透明**：对用户无感知，正常工作
4. **安全**：修复权限后立即切换到非 root 用户运行

## 验证

启动 PostgreSQL 容器后，查看日志应该看到：
```
[PostgreSQL Entrypoint] 检查并修复数据目录权限...
[PostgreSQL Entrypoint] ✓ 数据目录权限正确 (UID: 999)
```
或
```
[PostgreSQL Entrypoint] 检测到权限问题：数据目录所有者是 UID 1000，应该是 999
[PostgreSQL Entrypoint] 正在修复权限...
[PostgreSQL Entrypoint] ✓ 权限已修复
```

## 回退方案

如果自动修复不工作，可以：

1. **手动运行 init 容器**：
   ```bash
   docker-compose run --rm PostgresSQL-init
   docker-compose restart PostgresSQL
   ```

2. **使用修复脚本**：
   ```bash
   ./fix_postgresql_permissions.sh
   ```

3. **手动修复**：
   ```bash
   sudo chown -R 999:999 db_data/data db_data/log
   sudo chmod -R 700 db_data/data
   sudo chmod -R 755 db_data/log
   ```

## 技术细节

### Entrypoint 脚本位置
- 文件：`.scripts/docker/postgresql-entrypoint.sh`
- 容器内路径：`/postgresql-entrypoint.sh`
- 权限：可执行（755）

### 用户切换
- 启动用户：root (UID 0)
- 运行用户：postgres (UID 999)
- 切换工具：gosu（PostgreSQL 官方镜像自带）

### 权限要求
- 数据目录：`/var/lib/postgresql/data` → 999:999, 700
- 日志目录：`/var/log/postgresql` → 999:999, 755

## 相关文件

- `postgresql-entrypoint.sh` - 自动权限修复脚本
- `docker-compose.yml` - Docker Compose 配置
- `fix_postgresql_permissions.sh` - 手动修复脚本（备用）
- `POSTGRESQL_PERMISSION_FIX.md` - 详细的问题说明和手动修复指南

