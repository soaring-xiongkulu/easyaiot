# EasyAIoT HARNESS（平台 AI Agent 助手）

基于 [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)（`dsh`）的 **Sidecar Agent 模块**：通过聊天框理解 EasyAIoT 项目本体、协助改代码、查询平台健康与常见运维问题。

> **实验模块**：上游 `dsh` 处于 Developer Preview，API 可能变更；生产环境请限制访问范围并配置模型 Key。

## 能力概览

- 浏览器打开 DeepSeek Harness Web UI（默认 `:3080`）
- 工作区默认挂载 **完整 EasyAIoT 仓库**，Agent 可读改源码、执行命令（受 Harness 审批策略约束）
- 内置 **项目本体**（`ontology/AGENTS.md`）：模块关系、端口、常用 API、运维提示
- 可选 **平台 Tool 插件**：探测 Gateway 健康、列出模块说明
- WEB 管控台 **「AI 助手」** 菜单与 **右下角悬浮聊天抽屉**（与 IDEA 互补）

## 与 IDEA 的分工

| | IDEA | HARNESS |
|---|------|---------|
| 界面 | VS Code（code-server） | Agent 聊天 Web UI |
| 用户 | 社区贡献者 / 开发者 | 运维、集成商、管理员 |
| 改代码 | Copilot 补全 + 全功能 IDE | 多步 Agent + 平台 API |
| 改业务 | 弱 | 强（Tool 调 Gateway 等） |

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

- WEB 管控台 **「AI 助手」** 菜单与 **右下角悬浮聊天抽屉**（任意页面可聊，不跳转）；全屏页 `/harness/index` 亦可
- **API Key**：一键部署时可交互输入 DeepSeek Key（可跳过）；也可在 Web UI **Settings → Models** 中随时新增/修改（部署时写入的 Key 不会阻止你在 UI 里改；容器重启也不会覆盖 UI 里已保存的 Key）

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
  cordis.patch.yml          # 挂载 EasyAIoT 插件
  ontology/
    AGENTS.md               # 项目本体（注入工作区）
  plugins/
    easyaiot-platform-tools.ts
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
| `DEEPSEEK_API_KEY` | DeepSeek API Key |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` | OpenAI 兼容端点（如 DashScope） |
| `EASYAIOT_GATEWAY_URL` | 平台 Tool 调用的 Gateway 基址 |

## 后续扩展

- 增加 DEVICE/VIDEO/AI 业务 Tool（创建设备、启停算法任务等）
- 对接 AI 模块 LLM 配置中心
- Milvus RAG 索引全仓 API 文档
