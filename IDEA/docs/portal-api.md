# EasyAIoT IDEA Portal API

Base URL: `http://<host>:9300`  
可选鉴权：环境变量 `IDEA_TOKEN` 非空时，请求需带 `X-IDEA-Token: <token>`。

## Endpoints

| Method | Path | 说明 |
|--------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/api/auth/providers` | OAuth 提供方 |
| GET | `/api/auth/me` | 当前登录用户 |
| POST | `/api/auth/logout` | 退出 |
| GET | `/api/stats` | 容量与镜像信息 |
| GET | `/api/workspaces?user=` | 列出工作区 |
| GET | `/api/workspaces?scope=all` | 列出全部工作区（他人密码脱敏） |
| POST | `/api/workspaces` | 创建或复用工作区 |
| GET | `/api/workspaces/:id` | 详情（含 url / password） |
| POST | `/api/workspaces/:id/start` | 启动 |
| POST | `/api/workspaces/:id/stop` | 停止 |
| POST | `/api/workspaces/:id/heartbeat` | 刷新活跃时间（防闲置停机） |
| POST | `/api/reap-idle` | 立即执行闲置回收 |
| DELETE | `/api/workspaces/:id` | 删除容器 |
| GET | `/api/publish/meta` | 本机发布开关、现网 URL |
| GET | `/api/publish/modules` | 可发布模块白名单 |
| GET | `/api/publish/suggest` | 按工作区 git 改动建议模块 |
| POST | `/api/publish` | `{"modules":["WEB"],"action":"publish\|restart"}` |
| GET | `/api/publish/jobs/:id` | 发布任务日志 |
| GET/PUT | `/api/git/remotes` | 读/写 origin（Gitee/GitHub/GitLab） |

闲置策略：`IDEA_IDLE_TIMEOUT_HOURS`（默认 8，`<=0` 关闭）。活跃时间由创建/启动/心跳/详情写入 `activity.json`。

OAuth 配置见 [`oauth.md`](oauth.md)。请求可带 `X-IDEA-Session`（用户登录）或 `X-IDEA-Token`（服务令牌）。

### POST `/api/workspaces`

```json
{ "user": "alice" }
```

响应：

```json
{
  "ok": true,
  "data": {
    "id": "alice-1710000000",
    "name": "easyaiot-idea-alice",
    "user": "alice",
    "status": "running",
    "port": 13338,
    "password": "...",
    "url": "http://host:13338",
    "owned": true,
    "created_at": "2026-08-13T02:00:00Z",
    "container_id": "abc123",
    "image": "easyaiot/idea-workspace:latest"
  }
}
```

浏览器打开 `url`，使用 `password` 登录 code-server。默认文件夹为全仓 `/home/coder/easyaiot`。

## 操作台

打开门户根路径 `/` 即为工作区 / 发布到本机 / 贡献。与 WEB 管控台解耦。

门户查询参数（由前端消费后清除）：

| 参数 | 说明 |
|------|------|
| `file` / `path` | 仓库相对路径，启动编辑器后尽量打开该文件 |
| `harness` / `panel` | `1` / `harness` / `open` 时打开右侧 HARNESS AI 面板 |

示例：`http://<host>:9300/?file=NODE/agent_server.py&harness=1`

## WEB 对接

WEB 仅可选跳转：`VITE_IDEA_URL`（空则当前主机 `:9300`）。不在 WEB 内放发布按钮。
