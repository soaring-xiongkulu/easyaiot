# AI 共创（可选：自备 API Key）

**推荐优先使用 GitHub Copilot 登录**，见 [`ai-copilot.md`](./ai-copilot.md)。

没有 Copilot 订阅时，可用自己的 OpenAI / 兼容 API Key，通过 **Continue** 辅助改代码。  
平台不代持、不上传密钥。

## 配置

```bash
bash scripts/idea/setup-ai.sh
```

支持：

- OpenAI 官方 Key
- OpenAI 兼容网关（自定义 Base URL + Key）

非交互示例：

```bash
OPENAI_API_KEY=sk-xxx OPENAI_MODEL=gpt-4o bash scripts/idea/setup-ai.sh
OPENAI_API_KEY=sk-xxx OPENAI_API_BASE=https://your-gateway/v1 OPENAI_MODEL=gpt-4o \
  bash scripts/idea/setup-ai.sh
```

## 使用

1. 侧边栏打开 **Continue**
2. 选择已配置模型，对当前文件/选区提问或要求修改
3. 终端需要 Key 时：`source ~/project-data/.ai-env`

## 清除

```bash
bash scripts/idea/clear-ai.sh
```

## 说明

- ChatGPT Plus 网页订阅 ≠ API Key
- 不要把 Key 写进仓库或提交到 Git
