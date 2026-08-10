# Progress — Phase FR（行为对等续作）

HTTP 路由面 FR-W0～W4 已齐（≈259/259）。**COMPLETE 仍禁止。**

## Behavior wave（GAP §3–§4）

| 包 | Status | 目标 |
|----|--------|------|
| **FR-B1** | DONE | Post-process 真 sink（`use-stub-enqueue=false` → HTTP iot-sink） |
| **FR-B2** | DONE | MinIO 空间同步/清理 + media DVR 上传 |
| FR-B3 | pending | snap_task `init_all_tasks` 调度 |
| FR-B4 | pending | 远程 node（EX-REMOTE-NODE）或 iot-node 客户端 |
| FR-B5 | pending | Face/Plate 真 Kafka + 推理/明确旁路 |
| FR-B6 | pending | Camera ONVIF/PTZ/snapshot/NVR 行为去桩 |
| FR-B7 | pending | 流票据鉴权 + 全量回滚演练 |
| FR-B8 | pending | stream_forward 集群健康迁移 |

协作：composer-2.5 · Python-first · 禁止嵌套 · 不中断汇报直至行为缺口可勾选或产品签字豁免。
