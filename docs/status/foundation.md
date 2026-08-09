# 搭建状态（foundation）

- 更新: 2026-08-09 13:25 +08:00
- HEAD: e40fb0b0d39cf3e1da5071cf29758ac4f8081213（移除 SITE 前基线；随后本地有未推送 commit）
- 分支: main
- 浅克隆: 是
- 远程: 仅 `upstream`（EasyAIoT）；公司 `origin` 未配

## 根因与修复（本轮介入）

| 问题 | 根因 | 修复 |
|------|------|------|
| Postgres 起不来 | 本机 `postgres.exe` 占用 **5432**；且 **compose override 无法去掉** 主文件里的 `5432`（ports 是合并追加） | 改 `docker-compose.yml`：主机映射 **15432→5432** |
| Redis `exec format error` | 镜像架构不匹配 | 主文件加 `platform: linux/amd64`，主机端口 **16379→6379**，并重新 pull |
| PANEL Hub 超时 | 当时拉不到 python/node | 预拉 `python:3.11-slim-bookworm` / `node:20-bookworm-slim` 后 `install.sh build` |

## Smoke（当前）

| 组件 | 结果 |
|------|------|
| Docker Server | 29.6.1 OK |
| MinIO | `http://127.0.0.1:9000/minio/health/live` → **200** |
| Postgres | 容器 healthy；宿主机 **15432**；`pg_isready` OK |
| Redis | 容器 healthy；宿主机 **16379**；`PONG`；arch=amd64 |
| PANEL | `http://127.0.0.1:9200/health` → **ok**（`easyaiot/panel:latest`） |

容器当前保持运行，便于继续开发。停止命令见 `docs/ops/getting-started.md`。

## 产品范围

- **SITE 官方门户已从产品树移除**（ADR-0002）；安装脚本 `site` 为失败桩；README 模块列表已同步。

## 尚未覆盖（后续）

- 全量 mini 中间件（Nacos/Kafka/SRS 等）未在本轮强拉
- DEVICE/VIDEO 业务服务未起
- 公司 Git `origin` 未配
