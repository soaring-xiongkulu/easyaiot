# 切流阻塞清单（CUTOVER BLOCKERS）

> **话术：** HTTP 契约面已齐；行为/prod 联调进行中。  
> **禁止：** COMPLETE、整域 migrated、用 local soak 冒充 prod 绿。  
> **禁止继续：** FR-B46+ / keys-matrix / field-matrix / POST 样本刷绿等本地取证流水线。  
> 依据：[`PROD_SOAK_CHECKLIST.md`](./PROD_SOAK_CHECKLIST.md)、[`FULL_REPLACEMENT_GAP.md`](./FULL_REPLACEMENT_GAP.md)。  
> 日期：2026-08-11

---

## 1. 本地已证、prod 未证

| Checklist | 项 | 本地证据（≠ prod） |
|-----------|----|-------------------|
| **0.4** | phase0 薄烟雾 | `logs/certify-frb45-phase0.log` 等 |
| **1.1** | Alert Kafka produce | `logs/fr-b26-alert-kafka-latest.json`（iot-sink 消费 EX） |
| **1.2** | 纯 Kafka DVR→MinIO+DB | `logs/fr-b26-pure-kafka-dvr-latest.json` |
| **1.3** | Snap Kafka consumer | FR-B24/B16（缺文件诚实 retry） |
| **1.4** | Matching Kafka produce | `logs/fr-b27-matching-kafka-latest.json` |
| **2.1–2.5** | MinIO put/sync/DVR/cleanup | `logs/fr-b23-*` / `fr-b25-*` / `fr-b32-*` |
| **6.1–6.4** | Face/Plate/Pose/匹配告警 | `logs/fr-b41`～`fr-b45-*`（local Milvus/YOLO） |
| **8.1–8.4** | 契约探针/字段矩阵（local URL） | `logs/fr-b40-contract-latest.json` 等 |

**结论：** 代码路径大多具备；**切流前必须在 prod/预发复跑并附新证据**，不得沿用 local 勾选。

---

## 2. 缺环境才能做（⛔ 依赖，mini 完不成）

| Checklist | 项 | ⛔ 依赖 |
|-----------|----|--------|
| **0.1** | Nacos 注册 + health | prod/预发 Nacos；服务名 `video-server` |
| **0.2** | 网关 `lb://video-server` | 网关实例 + 路由表导出 |
| **0.3** | 共享 DB 只读冒烟 | 与 WEB 同库；告警/设备有真实数据 |
| **3.1–3.3** | WVP / 国标 / 目录 JSON | WVP + SIP；现场目录 |
| **4.1–4.5** | ONVIF / NVR / FlightHub / 对讲 / 抓拍 | 局域网相机、NVR、司空 token、真 RTSP |
| **5.1–5.5** | iot-node / Ceph / 媒体池 / 远程 post_process | 集群节点、Agent、CephFS、媒体 API |
| **7.1–7.4** | 双跑 / 权重切换 / 网关 P0 冒烟 / 回滚 | Nacos 权限 + 运维窗口 |
| **8.1–8.3** | 契约回归 @ **prod URL** | 可达的 prod/预发 base-url |

**最高杠杆（建议下一手，须确认后再做）：** **0.1+0.2+0.3**（Nacos 注册名 → 网关路由 → 共享库只读冒烟）。无环境则保持 ⛔，不退回本地矩阵。

---

## 3. 需产品拍板

| 议题 | 选项 | 影响 |
|------|------|------|
| InsightFace / Milvus / Paddle / YOLO | **真推理** vs **永久旁路 + EX** | 决定 §6 是否必须 prod 绿才能切流 |
| Alert / matching 永久 `direct_*` | 书面确认可不经 Kafka | 影响 §1.1 / §1.4 切流门禁 |
| P2 现场能力（FlightHub / 大华 NVR / audio_talk） | 现场必测 vs 豁免 | 影响 §3–§4 是否阻塞切流 |
| 远程 node / Ceph | 单机部署豁免 vs 集群必测 | 影响 §5 |

未签字前：**不得**把上述项标为「不用做」。

---

## 4. 工作约定（即日起）

1. **进度只看：** 本文件 + `PROD_SOAK_CHECKLIST.md` ⬜→✅（须 **prod/预发证据**）。  
2. **禁止：** 新开 FR-B46+、扩 keys/field/POST 矩阵刷绿、local artifact 当进度。  
3. **phase0：** 仅防回归可选，**不算切流进度**。  
4. **C 类动手：** 须人工确认后再做；做不到就标 ⛔ 并停。
