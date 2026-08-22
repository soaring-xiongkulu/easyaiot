# POST — 定制后处理服务

Go 服务，用于对推理事件做定制后处理。仅在 **standard / full** 部署；**mini / edge 不部署**。

## 快速开始（本地）

```bash
export PATH="$HOME/.local/go/bin:$PATH"
cd POST
cp -n env.example .env
go test ./...
go run ./cmd/post
# 或
bash install_linux.sh dev
```

本地调试时工作目录设为 `POST/`，复制 `env.example` → `.env`。

## Docker 管理

```bash
# 安装并启动（需 EASYAIOT_DEPLOY_PROFILE=standard|full）
bash POST/install_linux.sh install

# 常用运维
bash POST/install_linux.sh start|stop|restart|status|logs|update|clean|build

# 统一入口
./.scripts/docker/install_linux.sh install POST
./.scripts/docker/install_linux.sh build-runtime POST   # 仅构建/推送 POST 运行时镜像
./.scripts/docker/install_linux.sh build-runtime        # 全量含 POST
```

| 文件 | 说明 |
|------|------|
| `Dockerfile` | 镜像构建 |
| `docker-compose.yaml` | 主编排 |
| `docker-compose.desktop.yaml` | Desktop 覆盖 |
| `env.example` | 环境变量模板（复制为 `.env.docker` / `.env`） |
| `install_linux.sh` | 安装/启停/构建管理脚本 |

配置项见 `env.example`。

## 镜像

```bash
docker build -t post-service:latest .
# 或
bash install_linux.sh build
docker compose up -d
```
