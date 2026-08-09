# ADR-0002 — 从 acme 产品树移除 SITE 官网

- 日期: 2026-08-09
- 状态: Accepted

## 决策

acme 硬分叉产品 **不再包含 / 维护** EasyAIoT 官方门户模块 `SITE/`（纯前端营销站）。

## 理由

- 官网非业务管控能力；公司不负责维护该对外营销面。
- 保留会干扰本地代码分析、误入打包与认知负担。
- 上游若仍有 SITE，仅作偶发合并时跳过；不长期跟踪。

## 后果

- 删除 `SITE/` 源码树与 `WEB/conf/nginx.site.conf`。
- WEB nginx / docker-compose 去掉 8090 官网监听与映射。
- 安装脚本 `site` 子命令改为明确失败桩。
- 业务 WEB/PANEL/DEVICE 不受影响。
