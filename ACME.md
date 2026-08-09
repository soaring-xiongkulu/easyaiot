# ACME 公司工程入口

本仓库为公司产品基座 **acme**，自 [EasyAIoT](https://github.com/soaring-xiongkulu/easyaiot.git) 硬分叉起步。

## 当前阶段

- **打基础**：补齐文档与本地可验证路径；暂无行业分支策略。
- **开发方式**：前后端与平台模块均在本树直接修改。
- **上游**：官方仓库仅作「有选择合并」来源，**不长期跟踪** upstream。
- **Git**：使用默认分支即可；本阶段不引入功能分支/行业分支治理。
- **边端 Agent**：本阶段不做。

## 文档

公司文档索引见 [docs/README.md](docs/README.md)。上游 README 保留作产品说明参考。

## 与 rebekah-learn 的关系

学习/执行面保真在独立仓 F:/biofactory/rebekah-learn；**本仓为平台产品树**。后续 C++ 执行面（rebekah）计划以适配器方式接入，当前仅搭平台壳。

## 产品范围备注

- 不含官方门户 **SITE**（已移除，见 `docs/adr/0002-remove-site.md`）。
