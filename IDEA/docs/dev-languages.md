# IDEA 多语言开发支持

EasyAIoT 六种语言分工；IDEA 工作区目标是 **能改、能模块级验证、能发本机可发布模块**，不是每人环境编过全部原生重模块。

## 本机参考环境（开发主机实测）

| 项 | 本机 | IDEA 工作区镜像目标 |
|---|---|---|
| JDK | **21.0.11**（`JAVA_HOME=/opt/jdk-21_...`） | **OpenJDK 21**（DEVICE `java.version=21`） |
| Maven | 3.9.15 | 镜像内 maven |
| Node / pnpm | **v22.22.0** / pnpm 11 | **Node 22** + pnpm 9（与 WEB Dockerfile 同大版本） |
| Python | 3.14 | 发行版 python3（AI 模块级验证） |
| Go | 未装 | 镜像内 golang-go |
| .NET | 未装 | **.NET SDK 8**（EDGE） |
| g++ | 15.2 | build-essential + cmake + clangd |
| cmake | 未装 | 镜像内 cmake |
| Docker | Client 29.4；**daemon 当前不可用** | CLI 预装；发布依赖宿主机 daemon |

> 旧镜像曾用 JDK 17，与 DEVICE 父 POM（Java 21）不一致，已改正。

## 六语言能力

| 语言 | 主模块 | 工作区能力 | 本机发布 |
|---|---|---|---|
| TypeScript / Vue | WEB、APP、SITE、PANEL、VISUALIZE | Node 22 + pnpm + Volar/ESLint | 是 |
| Java | DEVICE、TRANSFORM 等 | **JDK 21** + Maven + Java 扩展包 | 是 |
| Python | AI、VIDEO/RTC 管理侧等 | Python3 + pip/venv + Pylance | 是 |
| Go | NODE 等 | Go + Go 扩展 | 视脚本 |
| C++ | RUNTIME | CMake + g++ + clangd/C++ 扩展；**全量编过走 CI** | 否（第一期改代码+PR） |
| C# | EDGE | .NET SDK 8 + C# 扩展；`dotnet build` 轻量验证 | 默认 PR；有统一脚本再开放发布 |

## 规划要点（已更新）

1. 工作区 JDK **必须 21**，与本机和 DEVICE 对齐；不要再用 17。
2. Node **22**，与本机 / WEB 构建对齐。
3. 补 .NET（EDGE）与 C/C++ 语言服务（RUNTIME 阅读/轻改）。
4. 成功标准：六语言都能打开、有语法辅助、能跑该语言常见模块命令；RUNTIME 全量原生编译不强制在贡献者容器内。
5. 本机 Docker daemon 需可用，否则「发布到本机」无法验证。
6. WEB 仅悬浮球跳转；操作台在 IDEA 门户 `:9300`。
