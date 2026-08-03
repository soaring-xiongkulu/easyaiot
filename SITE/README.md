# EasyAIoT SITE — 官方网站（纯前端）

云边端一体化智能算法应用平台的官方站点：产品介绍、特性、安装包下载、文档入口与关于页。

## 开发

```bash
cd SITE
pnpm install
pnpm dev
```

默认地址：`http://localhost:8090`

## 构建

```bash
pnpm build
pnpm preview
```

## Docker

```bash
# 统一入口（推荐）
./.scripts/docker/install_linux.sh site install
./.scripts/docker/install_linux.sh site start
./.scripts/docker/install_linux.sh site stop
./.scripts/docker/install_linux.sh site status

# 或直接进入模块目录
cd SITE && ./install_linux.sh install
```

交互菜单：运行 `./.scripts/docker/install_linux.sh` → 选择 **3) 官网**。

宿主机端口默认 **8090**（`SITE_PORT` 可覆盖）。

### Nginx 配置（统一在 WEB/conf）

| 文件 | 用途 |
|------|------|
| `WEB/conf/nginx.site.conf` | SITE 独立容器（site-service）完整配置 |
| `WEB/conf/nginx.conf` / `nginx.mini.conf` | Docker WEB 内附加 `listen 8090`，root=`html/SITE` |
| `WEB/conf/nginx.prod-server.conf` | 生产多端口：`8090 → html/SITE` |

独立容器默认挂载 `../WEB/conf/nginx.site.conf`，不再维护 `SITE/conf/nginx.conf`。

生产部署：将 `SITE/dist` 拷到 nginx 的 `html/SITE/` 后 reload。

## 页面

| 路径 | 说明 |
|------|------|
| `/` | 首页 Hero + 三档硬件 |
| `/features` | 产品特性 |
| `/download` | 安装包与部署档位 |
| `/docs` | 文档外链入口 |
| `/about` | 关于与开源仓库 |
