# EasyAIoT IDEA（社区贡献在线 IDE）

面向**社区贡献者 / 内部开发**的在线开发环境：以 **code-server** 为编辑器底座，通过「**配置 + 镜像 + 门户**」提供默认**全仓**工作区，少改上游源码。

## 能力概览

- 浏览器打开 VS Code 风格 IDE，默认 clone **完整 EasyAIoT 仓库**
- 一人一工作区（Docker），预装 Node / Python / JDK / Go / CMake 等常用工具链
- **独立门户** `http://<host>:9300`：进入 IDE、按改动发布到本机、贡献到 Gitee/GitHub/GitLab
- 工作区（code-server）默认端口池 **13338–13437**，支持多人同时在线
- AI 共创：预装 **GitHub Copilot**（账号登录）；可选 Continue 自备 API Key
- 六语言工具链对齐本机：**JDK 21**、Node 22、Python、Go、CMake/C++、.NET 8（EDGE）
- **闲置自动停机**（默认 8h，可配）；心跳与打开 IDE 会刷新活跃时间
- **Gitee / GitHub OAuth** 登录（可选强制），一人一区绑定账号

> 成功标准：能改代码、能跑模块级验证、能提 PR。  
> 全仓可见 ≠ 每人环境都能完整编译 RUNTIME / VIDEO 等重型原生模块（请走 CI）。

## 快速开始

```bash
cd IDEA
cp idea.env.example idea.env
# 按需修改 IDEA_GIT_URL / IDEA_PUBLIC_HOST / IDEA_TOKEN / IDEA_IDLE_TIMEOUT_HOURS
# OAuth：见 docs/oauth.md（IDEA_OAUTH_REDIRECT_BASE / IDEA_WEB_CALLBACK / CLIENT_ID...）

bash install.sh build          # 构建 workspace + portal 镜像（首次较久）
bash install.sh prepare-ref    # 可选：准备 git bare 仓加速全仓 clone
# idea.env 中设置: IDEA_GIT_REFERENCE=/opt/git-reference/easyaiot.git

bash install.sh start
bash install.sh status
bash install.sh create-demo    # 创建演示工作区并打印 url/password
# bash install.sh reap-idle    # 立即回收闲置工作区
# bash install.sh dev          # 本机 Python 跑门户（调试用）
```

门户默认：`http://<host>:9300`（操作台在门户页，不依赖 WEB）  
工作区端口池：`13338–13437`（门户可列出全部工作区并选择打开）  
API：[`docs/portal-api.md`](docs/portal-api.md) · 本机发布：[`docs/local-publish.md`](docs/local-publish.md) · 多语言：[`docs/dev-languages.md`](docs/dev-languages.md) · OAuth：[`docs/oauth.md`](docs/oauth.md) · 贡献流：[`docs/contrib-workflow.md`](docs/contrib-workflow.md) · Git 凭据：[`docs/git-auth.md`](docs/git-auth.md) · AI：[`docs/ai-copilot.md`](docs/ai-copilot.md) · 可选 BYOK：[`docs/ai-byok.md`](docs/ai-byok.md)

## 目录结构

```
IDEA/
  Dockerfile              # 门户镜像
  image/Dockerfile        # 贡献者 code-server 镜像
  image/entrypoint.sh     # 启动时保证全仓就绪
  workspace-template/     # 写入工作区的 .vscode 与欢迎说明
  workspace_ops.py        # Docker 工作区编排
  idea_server.py          # Flask API
  docker-compose.yml
  install.sh
```

## 操作台

独立门户：`http://<host>:9300`（不依赖 WEB）

WEB 管控台 `/idea` 仅跳转到上述门户。

## 贡献者使用提示

工作区内打开 `IDEA-README-FIRST.md`：绑定自己的 fork → 开分支 → push → 向官方提 PR。

## 安全注意

- 门户挂载 `docker.sock`，请限制网络访问并配置 `IDEA_TOKEN`
- 工作区含终端，具备容器内执行能力；务必一人一区、配额与闲置回收
- 不要把平台统一 AI Key 写进镜像；优先 Copilot 个人登录，或用户自备 Key

## 后续规划（P1+）

- 闲置自动关机、磁盘配额清理
- 与 Gitee/GitHub OAuth 打通
- 需要更大规模时接入 Coder / K8s 编排，编辑器镜像可继续复用
