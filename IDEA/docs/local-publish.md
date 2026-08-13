# 本机发布（替换现网模块容器）

按钮和操作台在 **IDEA 门户** `http://<host>:9300`，不在 WEB 模块里。重建 WEB 不会关掉 IDEA。

## 做什么

用当前工作区源码执行该模块的 `install_linux.sh build`，再在本机栈目录执行 `restart`，覆盖正在跑的同名镜像/容器。刷新现网地址即可看到结果。

## 发哪个模块

门户根据工作区 git 变更路径建议（`WEB/` → WEB）。默认勾选建议项，可改。不自动发全仓。

## 不碰 IDEA

容器名含 `easyaiot-idea` 的不会被选中或重启。

## 关闭

`IDEA_ALLOW_LOCAL_PUBLISH=0`

## API

| 方法 | 路径 |
|---|---|
| GET | `/api/publish/suggest` |
| POST | `/api/publish`  body: `{"modules":["WEB"],"action":"publish"}` |
| GET | `/api/publish/jobs/:id` |
| GET/PUT | `/api/git/remotes` |

`action` 也可为 `restart`（只重启不构建）。
