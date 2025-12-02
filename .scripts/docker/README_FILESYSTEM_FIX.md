# 文件系统只读问题修复指南

## 问题描述

当运行 `docker-compose up -d` 时，如果遇到以下错误：

```
Error response from daemon: error while creating mount source path '/opt/easyaiot/.scripts/docker/db_data/data': mkdir /opt/easyaiot: read-only file system
```

这表示 `/opt/easyaiot` 所在的文件系统是只读的，Docker 无法创建挂载目录。

## 快速修复方法

### 方法 1: 使用自动修复脚本（推荐）

```bash
cd /opt/easyaiot/.scripts/docker
sudo ./fix_readonly_filesystem.sh
```

脚本会自动：
1. 检查文件系统状态
2. 检查磁盘空间
3. 尝试重新挂载文件系统为可写模式
4. 创建所有必要的目录

### 方法 2: 手动修复

#### 步骤 1: 检查文件系统挂载状态

```bash
# 检查挂载点
df -h /opt/easyaiot

# 检查挂载选项
mount | grep $(df /opt/easyaiot | tail -1 | awk '{print $1}')
```

#### 步骤 2: 检查磁盘空间

```bash
df -h /opt/easyaiot
```

如果磁盘空间已满（使用率 100%），文件系统会自动变为只读。需要清理磁盘空间。

#### 步骤 3: 重新挂载为可写

```bash
# 获取文件系统设备
DEVICE=$(df /opt/easyaiot | tail -1 | awk '{print $1}')
MOUNT_POINT=$(df /opt/easyaiot | tail -1 | awk '{print $6}')

# 重新挂载为可写
sudo mount -o remount,rw $MOUNT_POINT
```

#### 步骤 4: 创建必要的目录

```bash
cd /opt/easyaiot/.scripts/docker

# 创建所有数据目录
sudo mkdir -p \
  standalone-logs \
  db_data/data db_data/log \
  taos_data/data taos_data/log \
  redis_data/data redis_data/logs \
  mq_data/data \
  minio_data/data minio_data/config \
  srs_data/conf srs_data/data \
  nodered_data/data

# 设置权限
sudo chmod -R 777 db_data taos_data redis_data mq_data minio_data srs_data nodered_data standalone-logs
```

#### 步骤 5: 验证修复

```bash
# 测试文件系统是否可写
touch /opt/easyaiot/.scripts/docker/.test_write && rm /opt/easyaiot/.scripts/docker/.test_write && echo "文件系统可写" || echo "文件系统仍然只读"
```

### 方法 3: 检查文件系统错误

如果重新挂载失败，可能是文件系统存在错误：

```bash
# 检查文件系统（只读模式，不会修改）
DEVICE=$(df /opt/easyaiot | tail -1 | awk '{print $1}')
sudo fsck -n $DEVICE
```

如果发现错误，需要修复（**注意：修复可能需要卸载文件系统**）：

```bash
# 卸载文件系统（如果可能）
sudo umount $MOUNT_POINT

# 修复文件系统
sudo fsck -y $DEVICE

# 重新挂载
sudo mount $DEVICE $MOUNT_POINT
```

## 常见原因

1. **磁盘空间已满**: 当磁盘使用率达到 100% 时，Linux 会自动将文件系统挂载为只读
2. **文件系统错误**: 文件系统损坏会导致只读挂载
3. **挂载配置错误**: `/etc/fstab` 中配置了只读挂载
4. **硬件问题**: 存储设备故障

## 预防措施

1. **监控磁盘空间**: 定期检查磁盘使用率，保持在 90% 以下
2. **定期检查文件系统**: 使用 `fsck` 定期检查文件系统健康
3. **使用数据卷**: 考虑将 Docker 数据目录挂载到独立的可写分区

## 如果修复失败

如果上述方法都无法修复，可以考虑：

1. **将数据目录移动到其他位置**:
   - 修改 `docker-compose.yml` 中的挂载路径
   - 将数据目录指向 `/data` 或 `/var/lib/docker/volumes` 等可写位置

2. **使用 Docker 命名卷**:
   - 修改 `docker-compose.yml`，使用命名卷而不是绑定挂载
   - Docker 会自动管理命名卷的存储位置

3. **联系系统管理员**:
   - 检查服务器硬件状态
   - 检查存储设备健康状态
   - 检查系统日志: `dmesg | grep -i error`

## 相关文件

- `fix_readonly_filesystem.sh`: 自动修复脚本
- `diagnose_filesystem.sh`: 文件系统诊断脚本
- `docker-compose.yml`: Docker Compose 配置文件

