# NODE — 集群管理面（控制面汇总）

> **维度**：管理节点 / 中心控制面  
> **模式**：观察者汇聚 — 经网关接收各节点 SENTINEL 上报，汇总组件与可调度能力

## 职责

| 能力 | 实现 |
|------|------|
| 节点纳管 | SSH、功能勾选、权重、Sentinel Agent 令牌 |
| **全量离线下发** | 节点分配完成后自动 SSH 同步 SENTINEL 整包并安装 |
| **Sentinel 汇总** | ingest 心跳快照 → `node_sentinel_snapshot` |
| **可调度推导** | 调度器读 `schedulableCapabilities` |
| 任务调度 | allocate / release → 指令下发 SENTINEL 执行 |
| 制品仓库 | Remediator 按缺组件分发 RUNTIME / Bundle / 媒体栈 |

## 与 SENTINEL 的关系

```
WEB / 业务编排
        │
        ▼
 Gateway :48080  /admin-api/node/**
        │
        ▼
┌─────────────────────────────────────┐
│  NODE（本目录，Java iot-node 服务）   │
│  纳管 · 离线分发 · 汇总 · 调度        │
└──────────────┬──────────────────────┘
               │ 心跳 sentinel 字段（经网关）
    ┌──────────┼──────────┐
    ▼          ▼          ▼
 SENTINEL   SENTINEL   SENTINEL  （../SENTINEL/，各计算节点全量离线安装）
```

节点创建（含 SSH）后：`easyaiot.sentinel.auto-deploy-on-create=true`（默认）会异步把全量 Sentinel 环境装到目标机并拉起监测。

## 构建

```bash
cd DEVICE
mvn -pl ../NODE/iot-node-biz -am package
```

Docker 服务名仍为 `iot-node-biz`（兼容现有部署）。

## 相关文档

- [Sentinel 设计](../.doc/设计文档/Sentinel集群节点哨兵模块设计.md)
- [SENTINEL 边缘 Agent](../SENTINEL/README.md)
- 节点功能注册表：`SENTINEL/registry/functions.yaml`
