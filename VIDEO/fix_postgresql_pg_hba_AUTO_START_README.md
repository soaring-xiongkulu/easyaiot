# PostgreSQL pg_hba.conf 自动修复服务安装说明

## 📋 概述

此服务会在系统启动后自动运行，等待 PostgreSQL Docker 容器启动后，自动执行 `pg_hba.conf` 修复脚本，解决 "no pg_hba.conf entry for host" 连接错误。

## 🚀 快速安装

### 方法一：使用安装脚本（推荐）

```bash
# 进入 VIDEO 目录
cd /opt/projects/easyaiot/VIDEO

# 使用 sudo 运行安装脚本
sudo bash install_fix_postgresql_service.sh
```

安装脚本会自动：
1. ✅ 检查必要文件是否存在
2. ✅ 更新服务文件中的用户配置
3. ✅ 复制服务文件到 systemd 目录
4. ✅ 重新加载 systemd 配置
5. ✅ 启用服务（开机自启动）

### 方法二：手动安装

```bash
# 1. 进入 VIDEO 目录
cd /opt/projects/easyaiot/VIDEO

# 2. 复制服务文件到 systemd 目录
sudo cp fix_postgresql_pg_hba.service /etc/systemd/system/

# 3. 编辑服务文件，修改用户和组（如果需要）
sudo nano /etc/systemd/system/fix_postgresql_pg_hba.service
# 将 User=basiclab 和 Group=basiclab 改为您的用户名

# 4. 重新加载 systemd 配置
sudo systemctl daemon-reload

# 5. 启用服务（开机自启动）
sudo systemctl enable fix_postgresql_pg_hba.service

# 6. 验证服务状态
sudo systemctl status fix_postgresql_pg_hba.service
```

## 📝 服务管理

### 查看服务状态

```bash
sudo systemctl status fix_postgresql_pg_hba.service
```

### 手动启动服务

```bash
sudo systemctl start fix_postgresql_pg_hba.service
```

### 停止服务

```bash
sudo systemctl stop fix_postgresql_pg_hba.service
```

### 禁用服务（取消开机自启动）

```bash
sudo systemctl disable fix_postgresql_pg_hba.service
```

### 查看服务日志

```bash
# 查看所有日志
sudo journalctl -u fix_postgresql_pg_hba.service

# 实时查看日志
sudo journalctl -u fix_postgresql_pg_hba.service -f

# 查看最近的日志（最后50行）
sudo journalctl -u fix_postgresql_pg_hba.service -n 50

# 查看今天的日志
sudo journalctl -u fix_postgresql_pg_hba.service --since today
```

### 查看脚本日志

服务脚本还会在 VIDEO 目录的 `logs/` 目录下生成日志文件：

```bash
# 查看日志目录
ls -lh /opt/projects/easyaiot/VIDEO/logs/fix_postgresql_pg_hba_auto_*.log

# 查看最新日志
tail -f /opt/projects/easyaiot/VIDEO/logs/fix_postgresql_pg_hba_auto_$(date +%Y%m%d).log
```

## ⚙️ 服务配置说明

### 服务文件位置

- **源文件**: `/opt/projects/easyaiot/VIDEO/fix_postgresql_pg_hba.service`
- **系统文件**: `/etc/systemd/system/fix_postgresql_pg_hba.service`

### 服务配置参数

```ini
[Unit]
Description=Auto-fix PostgreSQL pg_hba.conf on startup
After=docker.service          # 在 Docker 服务启动后运行
Requires=docker.service        # 需要 Docker 服务

[Service]
Type=oneshot                  # 一次性服务（执行完即退出）
User=basiclab                 # 运行用户（根据实际情况修改）
Group=basiclab                # 运行组（根据实际情况修改）
WorkingDirectory=/opt/projects/easyaiot/VIDEO
ExecStart=/opt/projects/easyaiot/VIDEO/fix_postgresql_pg_hba_auto.sh
TimeoutStartSec=600           # 超时时间（10分钟）

[Install]
WantedBy=multi-user.target    # 在系统多用户模式下启动
```

### 修改服务配置

如果需要修改服务配置：

```bash
# 1. 编辑服务文件
sudo nano /etc/systemd/system/fix_postgresql_pg_hba.service

# 2. 修改配置后，重新加载
sudo systemctl daemon-reload

# 3. 重启服务（如果需要）
sudo systemctl restart fix_postgresql_pg_hba.service
```

## 🔧 工作原理

### 执行流程

1. **系统启动** → systemd 启动 Docker 服务
2. **Docker 启动后** → systemd 启动修复服务
3. **等待 Docker** → 脚本等待 Docker 服务可用
4. **等待容器** → 脚本等待 PostgreSQL 容器启动（最多5分钟）
5. **等待服务** → 脚本等待 PostgreSQL 服务就绪（最多2分钟）
6. **执行修复** → 运行 `fix_postgresql_pg_hba.sh` 修复脚本
7. **记录日志** → 将执行结果记录到日志文件

### 等待机制

- **Docker 服务**: 最多等待 2 分钟（每 2 秒检查一次）
- **PostgreSQL 容器**: 最多等待 5 分钟（每 5 秒检查一次）
- **PostgreSQL 服务**: 最多等待 2 分钟（每 2 秒检查一次）

如果超时，脚本会记录错误日志并退出。

## 🛠️ 故障排查

### 问题 1: 服务未启动

**检查服务状态**:
```bash
sudo systemctl status fix_postgresql_pg_hba.service
```

**可能原因**:
- Docker 服务未启动
- 服务文件配置错误
- 权限问题

**解决方法**:
```bash
# 检查 Docker 服务
sudo systemctl status docker

# 检查服务文件
sudo cat /etc/systemd/system/fix_postgresql_pg_hba.service

# 查看服务日志
sudo journalctl -u fix_postgresql_pg_hba.service -n 50
```

### 问题 2: 服务执行失败

**查看日志**:
```bash
# 查看 systemd 日志
sudo journalctl -u fix_postgresql_pg_hba.service -n 100

# 查看脚本日志
tail -100 /opt/projects/easyaiot/VIDEO/logs/fix_postgresql_pg_hba_auto_*.log
```

**可能原因**:
- PostgreSQL 容器启动太慢（超过等待时间）
- 修复脚本执行失败
- 权限问题

**解决方法**:
```bash
# 手动执行修复脚本测试
cd /opt/projects/easyaiot/VIDEO
bash fix_postgresql_pg_hba.sh

# 如果手动执行成功，检查服务配置中的路径是否正确
```

### 问题 3: 服务超时

**错误信息**:
```
TimeoutStartSec=600 expired
```

**解决方法**:
```bash
# 增加超时时间
sudo nano /etc/systemd/system/fix_postgresql_pg_hba.service
# 修改 TimeoutStartSec=1200  # 增加到 20 分钟

# 重新加载配置
sudo systemctl daemon-reload
```

### 问题 4: 权限问题

**错误信息**:
```
Permission denied
```

**解决方法**:
```bash
# 检查脚本权限
ls -l /opt/projects/easyaiot/VIDEO/fix_postgresql_pg_hba_auto.sh
ls -l /opt/projects/easyaiot/VIDEO/fix_postgresql_pg_hba.sh

# 确保脚本有执行权限
chmod +x /opt/projects/easyaiot/VIDEO/fix_postgresql_pg_hba_auto.sh
chmod +x /opt/projects/easyaiot/VIDEO/fix_postgresql_pg_hba.sh

# 检查服务文件中的用户配置
sudo cat /etc/systemd/system/fix_postgresql_pg_hba.service | grep -E "User|Group"
```

## 📊 验证服务是否正常工作

### 方法 1: 查看服务状态

```bash
sudo systemctl status fix_postgresql_pg_hba.service
```

应该看到：
- `Active: inactive (dead)` - 服务已执行完成（正常，因为是 oneshot 类型）
- 或者 `Active: active (exited)` - 服务已成功执行

### 方法 2: 查看日志

```bash
# 查看 systemd 日志
sudo journalctl -u fix_postgresql_pg_hba.service --since "1 hour ago"

# 查看脚本日志
tail -50 /opt/projects/easyaiot/VIDEO/logs/fix_postgresql_pg_hba_auto_*.log
```

应该看到：
- `[SUCCESS] PostgreSQL pg_hba.conf 修复完成`

### 方法 3: 检查 PostgreSQL 配置

```bash
# 检查 pg_hba.conf 是否已配置
docker exec postgres-server tail -5 /var/lib/postgresql/data/pgdata/pg_hba.conf
```

应该看到：
```
host    all             all             0.0.0.0/0               md5
host    all             all             ::/0                    md5
```

### 方法 4: 测试数据库连接

```bash
cd /opt/projects/easyaiot/VIDEO
bash fix_postgresql_pg_hba.sh --check-only
```

应该看到：
- `[SUCCESS] pg_hba.conf 已包含允许所有主机连接的配置`

## 🔄 卸载服务

如果需要卸载服务：

```bash
# 1. 停止服务
sudo systemctl stop fix_postgresql_pg_hba.service

# 2. 禁用服务
sudo systemctl disable fix_postgresql_pg_hba.service

# 3. 删除服务文件
sudo rm /etc/systemd/system/fix_postgresql_pg_hba.service

# 4. 重新加载 systemd
sudo systemctl daemon-reload

# 5. 验证服务已删除
sudo systemctl status fix_postgresql_pg_hba.service
# 应该显示 "Unit fix_postgresql_pg_hba.service could not be found."
```

## 📚 相关文件

- **自动修复脚本**: `fix_postgresql_pg_hba_auto.sh`
- **修复脚本**: `fix_postgresql_pg_hba.sh`
- **服务文件**: `fix_postgresql_pg_hba.service`
- **安装脚本**: `install_fix_postgresql_service.sh`
- **使用文档**: `fix_postgresql_pg_hba_README.md`

## 💡 注意事项

1. **用户权限**: 确保服务文件中指定的用户有权限执行 Docker 命令
   - 用户应该在 `docker` 组中：`sudo usermod -aG docker $USER`

2. **Docker 启动顺序**: 服务会在 Docker 启动后运行，但不会等待 PostgreSQL 容器自动启动
   - 如果 PostgreSQL 容器需要手动启动，服务会等待容器启动（最多5分钟）

3. **日志文件**: 日志文件会按日期创建，不会无限增长
   - 日志位置: `/opt/projects/easyaiot/VIDEO/logs/fix_postgresql_pg_hba_auto_YYYYMMDD.log`

4. **服务类型**: 这是 `oneshot` 类型服务，执行完即退出
   - 不会持续运行，只在系统启动时执行一次

5. **超时设置**: 如果 PostgreSQL 容器启动很慢，可能需要增加超时时间
   - 修改服务文件中的 `TimeoutStartSec` 参数

## 📞 支持

如果遇到问题，请：

1. 查看服务日志：`sudo journalctl -u fix_postgresql_pg_hba.service -n 100`
2. 查看脚本日志：`tail -100 /opt/projects/easyaiot/VIDEO/logs/fix_postgresql_pg_hba_auto_*.log`
3. 手动执行修复脚本测试：`bash fix_postgresql_pg_hba.sh`
4. 查看本文档的故障排查部分

---

**最后更新**：2024-12-06  
**服务版本**：1.0.0

