# PostgreSQL 数据库备份脚本使用说明

## 概述

`backup_databases.sh` 是一个用于备份 PostgreSQL 数据库的脚本。该脚本解决了 PostgreSQL 版本不匹配的问题，通过使用 Docker 容器内的 `pg_dump` 工具来确保版本一致性。

## 解决的问题

当本地系统的 `pg_dump` 版本与 PostgreSQL 服务器版本不匹配时，会出现以下错误：
```
pg_dump: error: aborting because of server version mismatch
pg_dump: detail: server version: 18.1; pg_dump version: 16.11
```

本脚本通过在 Docker 容器内执行 `pg_dump` 来解决这个问题，因为容器内的 `pg_dump` 版本与服务器版本一致（都是 18）。

## 功能特性

- ✅ 自动检测 PostgreSQL 容器运行状态
- ✅ 检查数据库是否存在，跳过不存在的数据库
- ✅ 使用 Docker 容器内的 `pg_dump`（版本匹配）
- ✅ 按时间戳创建备份目录
- ✅ 备份多个数据库（iot-ai20、iot-device20、iot-video20、iot-message20、ruoyi-vue-pro20）
- ✅ 彩色日志输出，清晰显示备份状态
- ✅ 备份统计信息

## 使用方法

### 基本使用

```bash
cd /opt/projects/easyaiot/.scripts/postgresql
./backup_databases.sh
```

### 前置条件

1. **PostgreSQL 容器必须运行**
   ```bash
   # 检查容器状态
   docker ps | grep postgres-server
   
   # 如果未运行，启动容器
   docker start postgres-server
   ```

2. **确保有足够的磁盘空间**
   - 备份文件可能较大，请确保备份目录有足够空间

## 备份目录结构

备份文件保存在 `.scripts/postgresql/` 目录下，按时间戳命名：

```
.scripts/postgresql/
├── 20241201_143022/          # 时间戳目录
│   ├── iot-ai20.sql
│   ├── iot-device20.sql
│   ├── iot-video20.sql
│   ├── iot-message20.sql
│   └── ruoyi-vue-pro20.sql
├── 20241201_150315/          # 另一个时间戳目录
│   └── ...
└── backup_databases.sh
```

## 配置说明

脚本中的配置项（可根据需要修改）：

```bash
# PostgreSQL 容器名称
POSTGRES_CONTAINER="postgres-server"

# PostgreSQL 连接信息
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="iot45722414822"
POSTGRES_HOST="localhost"
POSTGRES_PORT="5432"

# 需要备份的数据库列表
DATABASES=(
    "iot-ai20"
    "iot-device20"
    "iot-video20"
    "iot-message20"
    "ruoyi-vue-pro20"
)
```

## 备份选项说明

脚本使用的 `pg_dump` 选项：

- `--clean`: 在创建数据库对象之前先删除它们
- `--if-exists`: 使用 IF EXISTS 子句（与 --clean 配合使用）
- `--create`: 包含创建数据库的命令
- `--format=plain`: 使用纯文本格式（SQL 文件）
- `--no-owner`: 不输出设置所有权的命令
- `--no-privileges`: 不输出设置权限的命令

## 输出示例

```
[INFO] ==========================================
[INFO] PostgreSQL 数据库备份脚本
[INFO] ==========================================
[INFO] PostgreSQL 容器 postgres-server 运行正常
[INFO] 备份目录: /opt/projects/easyaiot/.scripts/postgresql/20241201_143022
[INFO] 开始备份数据库: iot-ai20
[INFO] ✓ 数据库 iot-ai20 备份成功: .../iot-ai20.sql (大小: 2.5M)

[INFO] 开始备份数据库: iot-device20
[INFO] ✓ 数据库 iot-device20 备份成功: .../iot-device20.sql (大小: 15M)

[INFO] ==========================================
[INFO] 备份完成统计:
[INFO]   成功: 5 个数据库
[INFO] 备份目录: /opt/projects/easyaiot/.scripts/postgresql/20241201_143022
[INFO] ==========================================
```

## 定时备份

可以使用 `cron` 设置定时备份，例如每天凌晨 2 点备份：

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每天凌晨 2 点执行备份）
0 2 * * * /opt/projects/easyaiot/.scripts/postgresql/backup_databases.sh >> /opt/projects/easyaiot/.scripts/postgresql/backup.log 2>&1
```

## 恢复数据库

使用 `psql` 恢复备份：

```bash
# 方法1：使用本地 psql（需要版本匹配）
PGPASSWORD=iot45722414822 psql -h localhost -U postgres -d iot-ai20 < backup_dir/iot-ai20.sql

# 方法2：使用 Docker 容器内的 psql（推荐，版本匹配）
docker exec -i -e PGPASSWORD=iot45722414822 postgres-server \
    psql -U postgres -h localhost -p 5432 -d iot-ai20 < backup_dir/iot-ai20.sql
```

## 注意事项

1. **版本匹配问题**：本脚本通过使用容器内的 `pg_dump` 解决了版本不匹配问题
2. **备份文件大小**：大型数据库的备份文件可能很大，请确保有足够磁盘空间
3. **备份时间**：备份时间取决于数据库大小，大型数据库可能需要较长时间
4. **权限问题**：确保脚本有执行权限：`chmod +x backup_databases.sh`
5. **容器状态**：备份前确保 PostgreSQL 容器正在运行

## 故障排除

### 问题1：容器未运行
```
[ERROR] PostgreSQL 容器 postgres-server 未运行！
```
**解决方案**：启动容器
```bash
docker start postgres-server
```

### 问题2：数据库不存在
```
[WARN] 数据库 xxx 不存在，跳过备份
```
**解决方案**：检查数据库名称是否正确，或创建该数据库

### 问题3：备份文件为空
```
[ERROR] 数据库 xxx 备份文件为空或创建失败
```
**解决方案**：
- 检查数据库是否有数据
- 检查容器日志：`docker logs postgres-server`
- 检查磁盘空间是否充足

## 相关文件

- `backup_databases.sh`: 备份脚本
- `00-init-databases.sh`: 数据库初始化脚本
- `docker-compose.yml`: Docker 配置文件（位于 `.scripts/docker/`）

## 更新日志

- **2024-12-01**: 初始版本，支持使用 Docker 容器内的 pg_dump 解决版本不匹配问题

