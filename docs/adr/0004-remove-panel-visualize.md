# ADR-0004 — 从 acme 产品树移除 PANEL 与 VISUALIZE

- 日期: 2026-08-09
- 状态: Accepted

## 决策

acme 硬分叉产品 **不再包含 / 维护**：

1. **PANEL/** — 1Panel 式运维控制台（:9200）
2. **VISUALIZE/** — GoView 大屏编辑器（:8002）及 WEB 侧「可视化」管理页

## 理由

- 严肃工业视频 AI：装机可用命令行脚本；大屏/指挥成屏非当前产品核心。
- PANEL 仅为安装脚本与 Docker 的 GUI 壳；去掉不影响 WEB/DEVICE/VIDEO/AI 主链路。
- VISUALIZE 为展示加项（仅 full）；与 FUXA 工艺组态（:1881）无关，FUXA 保留。

## 后果

- 删除 `PANEL/`、`VISUALIZE/`、`WEB/src/views/visualize/` 及 panel/visualize 辅助文件。
- 安装/运行时/COMPILE 清单去掉 PANEL、VISUALIZE。
- WEB 菜单强制隐藏「可视化*」；集群页去掉「打开 PANEL」按钮。
- **`DEVICE/iot-visualize` Java 微服务暂留**（属 DEVICE 子模块，本轮不拆 DEVICE 工程）；无前端入口后等同闲置，后续可再裁。
- FUXA / 工业主路径不受影响。
