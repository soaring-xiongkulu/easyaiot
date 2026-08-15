# EasyAIoT HARNESS（平台 AI Agent 助手）

基于 [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)（`dsh`）的 **Sidecar Agent 模块**：通过聊天框理解 EasyAIoT 项目本体、协助改代码、查询平台健康与常见运维问题。

> **实验模块**：上游 `dsh` 处于 Developer Preview，API 可能变更；生产环境请限制访问范围并配置模型 Key。

## 能力概览

- 浏览器打开 DeepSeek Harness Web UI（默认 `:3080`）
- 工作区默认挂载 **完整 EasyAIoT 仓库**，启动时**自动注册工作区**（免手动「选择工作区」）
- **文件树侧边栏**（`dsh-better-sidebar`）：浏览/预览/编辑源码、终端、Git，与当前任务会话关联
- 内置 **项目本体**（`ontology/AGENTS.md`）：模块关系、端口、常用 API、运维提示
- **平台 Tool 插件**：探测 Gateway 健康、列出模块说明
- WEB 管控台 **「AI 助手」** 菜单与 **右下角悬浮聊天抽屉**（与 IDEA 互补）

## 与 IDEA 的分工

| | IDEA | HARNESS |
|---|------|---------|
| 界面 | VS Code（code-server）+ 右侧可嵌 HARNESS | Agent 聊天 + 文件侧边栏 |
| 用户 | 社区贡献者 / 开发者 | 运维、集成商、管理员 |
| 改代码 | Copilot 补全 + 全功能 IDE | 多步 Agent + 侧栏编辑 + 平台 API |
| 改业务 | 弱 | 强（Tool 调 Gateway 等） |
| 联动 | 工具栏「AI 助手」打开右侧 HARNESS；`?file=&harness=1` | Tool `easyaiot_open_in_idea` 生成门户链接 |

## 快速开始

```bash
cd HARNESS
cp harness.env.example harness.env
# 配置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY + OPENAI_BASE_URL（DashScope 等兼容端点）

bash install.sh install    # 构建镜像并启动
bash install.sh status
# 浏览器打开 http://<host>:3080
# Settings → Models 中也可在 UI 内填写 API Key
```

打开后应能直接看到：

1. 左侧只有 **EasyAIoT** 工作区（启动会清掉旧的 `/harness` 会话）→ 点 **新建会话**
2. 右侧资源管理器应列出 `WEB`、`DEVICE`、`AI`、`HARNESS` 等全仓目录；点文件可预览/编辑；行尾可 `@文件` 引用进聊天
3. 默认 **Cursor Light** 浅色主题（冷灰侧栏 + 米白主区）。完整 IDE 布局请用 IDEA / Cursor（`:9300`）
4. 输入框可用 `@文件路径` 引用工作区文件进当前任务

> HARNESS 是 Agent 聊天壳 + 文件侧栏，视觉可贴近 Cursor，但不会变成完整 VS Code/Cursor 三栏 IDE。
> 容器重建会保留 named volume 里的会话；每次启动会删除 `sessions/--harness--`，只保留 EasyAIoT。清空全部：`docker compose down -v`。

## 建议搭配的能力

| 能力 | 说明 |
|------|------|
| 文件树侧边栏 | 浏览/预览/编辑、终端、Git |
| `@文件` 提及 | 聊天框输入 `@` 搜索并引用路径 |
| 平台 Tool | `easyaiot_gateway_health` / `easyaiot_list_modules` / `easyaiot_service_health` / `easyaiot_dev_portals` / `easyaiot_open_in_idea` |
| IDEA | 完整 VS Code：打开 `:9300`；工具栏点「AI 助手」可分屏 HARNESS |

## 部署形态

- **mini / standard / full**：默认启用（`EASYAIOT_ENABLE_HARNESS=0` 可关闭）

## 目录结构

```
HARNESS/
  Dockerfile
  docker-compose.yml
  docker-entrypoint.sh
  install.sh / install_linux.sh
  harness.env.example
  cordis.patch.yml          # EasyAIoT 插件补丁
  scripts/
    ensure-ux-plugins.sh    # 安装/补齐侧边栏插件
  ontology/
    AGENTS.md               # 项目本体（注入工作区）
  plugins/
    easyaiot-platform-tools.ts
    easyaiot-workspace-seed.ts
```

## 安全注意

- Agent 具备读文件与执行 Shell 能力，**勿对公网裸奔**；建议仅内网或管理员角色可用
- 生产环境在 Harness UI 中启用写操作/命令 **审批策略**
- 不要把 API Key 提交进 Git；使用 `harness.env`（已在 `.gitignore`）

## 环境变量

| 变量 | 说明 |
|------|------|
| `HARNESS_LISTEN_PORT` | 监听端口，默认 `3080` |
| `HARNESS_WORKSPACE_HOST` | 宿主机 EasyAIoT 根目录（Agent 工作区） |
| `HARNESS_WORKSPACE` | 容器内工作区路径，默认 `/workspace/easyaiot` |
| `HARNESS_WORKSPACE_TITLE` | Web UI 工作区显示名，默认 `EasyAIoT` |
| `HARNESS_ENABLE_SIDEBAR` | `1` 启用文件树侧边栏（默认），`0` 关闭 |
| `HARNESS_SIDEBAR_PACKAGE` | 侧边栏 npm 规格，默认 `dsh-better-sidebar@0.12.1` |
| `DEEPSEEK_API_KEY` | DeepSeek API Key |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` | OpenAI 兼容端点（如 DashScope） |
| `EASYAIOT_GATEWAY_URL` | 平台 Tool 调用的 Gateway 基址 |
| `EASYAIOT_IDEA_URL` | `easyaiot_open_in_idea` 生成的 IDEA 门户基址 |
| `HARNESS_TRUSTED_HOSTS` | iframe 嵌入时追加 trusted-host（含 `:9300` 门户） |

## 后续扩展

- 增加 DEVICE/VIDEO/AI 业务 Tool（创建设备、启停算法任务等）
- 对接 AI 模块 LLM 配置中心
- Milvus RAG 索引全仓 API 文档
