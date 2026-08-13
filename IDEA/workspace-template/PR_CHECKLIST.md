# EasyAIoT Pull Request 检查清单（IDEA 工作区副本）

提交 PR 前请自检（不必全部勾满，按你改动的模块勾选）。

## 通用

- [ ] 已从 `upstream` 同步最新代码
- [ ] 分支名清晰（如 `feat/web-xxx` / `fix/device-yyy`）
- [ ] Commit message 说明动机与范围
- [ ] 未提交密钥、`.env`、大数据、`*_data`、`.build-cache`
- [ ] 未引入无关格式化大爆改

## 按模块（改到哪个勾哪个）

### WEB
- [ ] `pnpm install` 可通过
- [ ] 相关页面本地可打开 / 无明显控制台报错
- [ ] 若改路由/菜单，确认权限与 i18n 无破坏

### APP
- [ ] 依赖安装成功
- [ ] 主要流程可编译或通过既有检查脚本

### DEVICE / NODE
- [ ] 接口契约未随意破坏；若破坏已在 PR 说明迁移方式
- [ ] 相关单测或手工验证步骤已写在 PR

### AI / VIDEO / RUNTIME
- [ ] 说明是否需要 GPU / 特殊模型权重
- [ ] 重型编译建议走 CI；本地仅做必要验证
- [ ] 配置项/环境变量变更已文档化

### EDGE
- [ ] 说明目标运行时（Linux x86/ARM）
- [ ] 配置样例或回滚方式已给出

### TRANSFORM / VISUALIZE / PANEL / SITE / IDEA
- [ ] 配置与部署说明已更新（README 或模块文档）
- [ ] 与 WEB 入口/代理（如有）保持一致

## PR 正文建议包含

1. **背景 / 动机**
2. **改动说明**（模块列表）
3. **验证方式**（命令或截图）
4. **风险与回滚**

官方 PR 模板：`.github/PULL_REQUEST_TEMPLATE.md`（Gitee：`.gitee/PULL_REQUEST_TEMPLATE.zh-CN.md`）
