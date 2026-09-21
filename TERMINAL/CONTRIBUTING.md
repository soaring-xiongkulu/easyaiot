# Contributing to uniTerm

Thank you for your interest in contributing to uniTerm! This guide covers how to report issues, suggest features, and submit code changes.

---

## Reporting Bugs

Found a bug? Please open an issue on [GitHub Issues](https://github.com/ys-ll/uniterm/issues). To help us fix it quickly, include:

- uniTerm version (find it in **Settings → About**)
- Operating system and version
- Steps to reproduce the bug
- Expected vs actual behavior
- Screenshots or logs if available

## Suggesting Features

Feature suggestions are also welcome via [GitHub Issues](https://github.com/ys-ll/uniterm/issues). Please search existing issues first to avoid duplicates. Describe the use case and why it would be valuable.

## Setting Up Development Environment

### Prerequisites

- [Go](https://go.dev/dl/) 1.23+
- [Node.js](https://nodejs.org/) 20+
- [Wails CLI](https://wails.io/docs/gettingstarted/installation) v2
- **macOS**: Xcode Command Line Tools
- **Linux**: `libgtk-3-dev` and `libwebkit2gtk-4.1-dev`
- **Windows**: WebView2 runtime (included in Windows 10+)

### Build & Run

```bash
git clone https://github.com/ys-ll/uniterm.git
cd uniTerm
cd frontend && npm install && cd ..
wails dev                   # Development mode
wails build                 # Production build
```

> **Note:** After modifying frontend code, clear the cache and rebuild manually before running `wails dev`, otherwise changes may not take effect:
> ```bash
> cd frontend && rm -rf dist node_modules/.vite && npm run build && cd .. && wails dev
> ```

## Development Workflow

1. **Fork** the repository
2. Create a new branch from `main`: `git checkout -b feature/your-feature` or `fix/your-bugfix`
3. Make your changes
4. Test locally with `wails dev`
5. Commit your changes (see [Commit Guidelines](#commit-guidelines) below)
6. Push and open a pull request to the `main` branch

## Commit Guidelines

- Write commit messages in **English**
- Keep commits focused and atomic
- Use the present tense ("Add feature", not "Added feature")

## Pull Request Guidelines

- PR descriptions are recommended to be **bilingual**: English first, then Chinese, separated by `---`
- Link related issues if applicable
- Ensure the code compiles and passes local testing

## Project Structure

```
uniTerm/
├── main.go                       # Entry point
├── app.go                        # Wails bindings, LLM API proxy, SFTP API
├── backend/
│   ├── session/                  # SSH/SFTP/database session management
│   ├── database/                 # SQL execution, schema introspection, DSN builders
│   ├── store/                    # Persistent config (connections, AI, settings)
│   └── log/                      # File-based logging
├── frontend/
│   └── src/
│       ├── components/           # Vue components
│       ├── composables/          # Terminal composables
│       ├── stores/               # Pinia stores
│       ├── services/             # AI agent loop, LLM client
│       ├── i18n/                 # Translations
│       └── types/                # TypeScript type definitions
└── wails.json
```

| Layer | Technology |
|-------|-----------|
| Desktop Framework | Wails v2 |
| Backend | Go |
| Frontend | Vue 3 + Pinia + Element Plus |
| Terminal | xterm.js |
| AI Protocol | Anthropic Messages API / OpenAI Chat Completions API |

## Questions?

Feel free to ask in [GitHub Issues](https://github.com/ys-ll/uniterm/issues) or start a discussion in [GitHub Discussions](https://github.com/ys-ll/uniterm/discussions).

Thanks again for contributing! ❤️

---

# 参与贡献 uniTerm

感谢你对 uniTerm 的关注！本文档介绍如何报告问题、建议功能和提交代码。

---

## 报告 Bug

发现 Bug 请在 [GitHub Issues](https://github.com/ys-ll/uniterm/issues) 提交 issue。为帮助我们快速定位问题，请包含以下信息：

- uniTerm 版本（在 **设置 → 关于** 中查看）
- 操作系统及版本
- 复现步骤
- 预期行为与实际行为
- 如有截图或日志请一并附上

## 建议功能

功能建议也请通过 [GitHub Issues](https://github.com/ys-ll/uniterm/issues) 提交。提交前请先搜索是否已有类似建议，避免重复。请描述使用场景以及为什么这个功能有价值。

## 搭建开发环境

### 环境要求

- [Go](https://go.dev/dl/) 1.23+
- [Node.js](https://nodejs.org/) 20+
- [Wails CLI](https://wails.io/docs/gettingstarted/installation) v2
- **macOS**：Xcode Command Line Tools
- **Linux**：`libgtk-3-dev` 和 `libwebkit2gtk-4.1-dev`
- **Windows**：WebView2 运行时（Windows 10+ 已内置）

### 构建与运行

```bash
git clone https://github.com/ys-ll/uniterm.git
cd uniTerm
cd frontend && npm install && cd ..
wails dev                   # 开发模式
wails build                 # 生产构建
```

> **注意：** 修改前端代码后，必须先清理缓存并手动构建再启动 `wails dev`，否则修改可能不生效：
> ```bash
> cd frontend && rm -rf dist node_modules/.vite && npm run build && cd .. && wails dev
> ```

## 开发流程

1. **Fork** 本仓库
2. 从 `main` 分支创建新分支：`git checkout -b feature/your-feature` 或 `fix/your-bugfix`
3. 进行修改
4. 使用 `wails dev` 本地测试
5. 提交代码（见下方[提交规范](#提交规范)）
6. 推送并创建 Pull Request 到 `main` 分支

## 提交规范

- 提交信息使用 **英文**
- 保持每次提交聚焦且原子化
- 使用现在时态（"Add feature" 而非 "Added feature"）

## PR 规范

- PR 描述建议使用 **英文 + 中文双语**：先写英文，后写中文，中间用 `---` 分隔
- 如有相关 issue 请注明链接
- 确保代码可编译通过并经过本地测试

## 项目结构

```
uniTerm/
├── main.go                       # 入口文件
├── app.go                        # Wails 绑定、LLM API 代理、SFTP API
├── backend/
│   ├── session/                  # SSH/SFTP/数据库 会话管理
│   ├── database/                 # SQL 执行、表结构查询、DSN 构建
│   ├── store/                    # 持久化配置（连接、AI、设置）
│   └── log/                      # 文件日志
├── frontend/
│   └── src/
│       ├── components/           # Vue 组件
│       ├── composables/          # 终端组合式函数
│       ├── stores/               # Pinia 状态管理
│       ├── services/             # AI 代理循环、LLM 客户端
│       ├── i18n/                 # 国际化翻译
│       └── types/                # TypeScript 类型定义
└── wails.json
```

| 层级 | 技术 |
|------|------|
| 桌面框架 | Wails v2 |
| 后端 | Go |
| 前端 | Vue 3 + Pinia + Element Plus |
| 终端引擎 | xterm.js |
| AI 协议 | Anthropic Messages API / OpenAI Chat Completions API |

## 有问题？

如有疑问，欢迎在 [GitHub Issues](https://github.com/ys-ll/uniterm/issues) 提问或在 [GitHub Discussions](https://github.com/ys-ll/uniterm/discussions) 发起讨论。

再次感谢你的贡献！❤️
