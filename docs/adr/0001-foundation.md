# ADR-0001：以 EasyAIoT 硬分叉为 acme 基座

- **状态**：已接受（2026-08-09）

## 决策

1. 从 EasyAIoT 克隆为 F:/acme，作为产品 acme 的主工程树。
2. 前后端在本树直接修改。
3. 官方远程命名为 upstream，不自动 merge；按需选择性合并。
4. 暂不建立 git 分支治理；边端 Agent 后置。
5. C++ 执行面（rebekah）后续适配器接入；本阶段只搭平台壳。
