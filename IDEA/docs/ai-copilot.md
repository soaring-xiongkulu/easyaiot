# AI 共创（GitHub Copilot 登录）

**推荐方式**：在 IDEA 里用自己的 **GitHub 账号登录 Copilot**，无需粘贴 API Key。

平台不代持密钥；费用走你自己的 Copilot 订阅（Individual / Business / 学生免费等）。

## 使用步骤

1. 打开工作区 IDE
2. 终端执行（可选，会尝试补装扩展并打印说明）：

```bash
bash scripts/idea/setup-copilot.sh
```

3. 左下角 **Accounts（账号）** → **Sign in to GitHub** / **Sign in to use Copilot**
4. 按提示完成浏览器或设备码登录
5. 侧边栏打开 **Chat**，或使用行内补全（Tab 接受）

也可在扩展面板搜索安装：**GitHub Copilot**、**GitHub Copilot Chat**。

## 前提

- GitHub 账号已开通 [Copilot](https://github.com/settings/copilot)
- 仅有 ChatGPT Plus **不能**代替 Copilot 登录

## 登录异常时

- Command Palette → `Developer: Reload Window`
- Accounts → Sign out → 重新 Sign in
- 若弹出设备码，在浏览器打开提示 URL 并输入码
- code-server 非官方 VS Code，偶发鉴权/兼容问题；仍失败可用下方可选方案

## 可选：自备 API（Continue）

没有 Copilot 订阅时：见 [`ai-byok.md`](./ai-byok.md) 与 `bash scripts/idea/setup-ai.sh`。
