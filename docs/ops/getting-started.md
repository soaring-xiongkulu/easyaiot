# 本机上手（acme）

工程路径: `F:/acme`

## Windows 推荐

- Docker Desktop + Git Bash
- 关键数据端口（acme Desktop 改写后）：
  - Postgres → **127.0.0.1:15432**（容器内仍 5432）
  - Redis → **127.0.0.1:16379**（容器内仍 6379；密码见 compose）
  - MinIO → **9000 / 9001**
  - PANEL → **9200**

说明：Compose 的 `override` **不能删除** 主文件已声明的 `ports`（只会追加），因此端口改动写在 `docker-compose.yml` 本身。

## 最小中间件 smoke

```bash
cd /f/acme/.scripts/docker
docker compose pull PostgresSQL-init PostgresSQL Redis MinIO
docker compose up -d PostgresSQL-init
docker compose up -d PostgresSQL Redis MinIO
# 探测
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9000/minio/health/live
docker exec redis-server redis-cli -a 'basiclab@iot975248395' ping
docker exec postgres-server pg_isready -U postgres
```

可选全量（更慢，含 Nacos 等）：

```bash
cd /f/acme/.scripts/docker
EASYAIOT_DEPLOY_PROFILE=mini bash install_middleware_desktop.sh install
```

## PANEL

```bash
# 若 Hub 慢，先预拉
docker pull python:3.11-slim-bookworm
docker pull node:20-bookworm-slim

cd /f/acme/PANEL
bash install.sh build   # 首次
bash install.sh start   # http://127.0.0.1:9200/
bash install.sh status
```

健康检查: `http://127.0.0.1:9200/health`

## 停止

```bash
cd /f/acme/PANEL && bash install.sh stop
cd /f/acme/.scripts/docker && docker compose stop MinIO Redis PostgresSQL && docker compose rm -f MinIO Redis PostgresSQL PostgresSQL-init
```

## Smoke 记录（2026-08-09）

见 `docs/status/foundation.md`：Postgres/Redis/MinIO/PANEL 均已健康。
