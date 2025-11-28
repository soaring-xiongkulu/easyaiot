# 使用说明

## 1 建立基础环境目录
> mkdir -p db_data/{data,log} taos_data/{data,log} mq_data/{data,log} redis_data/{data,log} nacos_data/{data,log}

## 2 上传docker-compose.yml 文件

## 3 常见问题修复

### PostgreSQL 权限问题

**✅ 已自动修复**：从 2025-11-28 开始，PostgreSQL 容器会在启动时自动修复权限问题，无需手动干预。

如果仍然遇到 `could not open file "global/pg_filenode.map": Permission denied` 错误：

**快速修复**：
```bash
cd .scripts/docker
./fix_postgresql_permissions.sh
```

详细说明请参考：
- [POSTGRESQL_AUTO_FIX.md](./POSTGRESQL_AUTO_FIX.md) - 自动修复机制说明
- [POSTGRESQL_PERMISSION_FIX.md](./POSTGRESQL_PERMISSION_FIX.md) - 手动修复指南

### PostgreSQL 密码问题

如果遇到密码认证失败问题：

**快速修复**：
```bash
cd .scripts/docker
./fix_postgresql.sh
```

详细说明请参考：[POSTGRESQL_FIX.md](./POSTGRESQL_FIX.md)

