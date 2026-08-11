# 本机完整栈验收阻塞清单

> **话术：** 阶段 0：规矩与商业默认已切换；完整替换进行中；Python 仍为对照，禁止删除。  
> **唯一环境：** 本机（Kafka / MinIO / Nacos / 网关 = 现成依赖，只挂不重写）。  
> **禁止：** COMPLETE、删 main `VIDEO/`、FR-B46+ / 矩阵刷绿、「等 prod / 缺线上」叙事。  
> 日期：2026-08-11（阶段 0 纠偏）

Oracle = `F:/acme` @ main `VIDEO/` · Candidate = worktree `DEVICE/iot-video` · 日常 profile = **`local`**（见 [PHASE0_DEFAULTS.md](./PHASE0_DEFAULTS.md)）

---

## 1. 代码路径已备、须本机完整栈复验

| Checklist | 项 | 历史 local 证据（仅参考，须本机完整栈复跑） |
|-----------|----|---------------------------------------------|
| 0.4 | phase0（可选防回归） | `mini` profile + certify |
| 1.1–1.4 | Alert / DVR / Snap / Matching Kafka | `logs/fr-b26`～`fr-b27` / `fr-b45` |
| 2.1–2.5 | MinIO | `logs/fr-b23`～`fr-b25` / `fr-b32` |
| 6.1–6.4 | Face/Plate/Pose/匹配告警 | `logs/fr-b41`～`fr-b45` |

**结论：** 不得用旧 local artifact 冒充本机完整栈等价。

---

## 2. 本机须挂起的外部依赖（⛔ 未挂则无法验收）

| # | 项 | 依赖 |
|---|-----|------|
| 0.1 | Nacos 注册 + health | 本机 Nacos；名 `video-server` |
| 0.2 | 网关 `lb://video-server` | 本机网关 |
| 0.3 | 共享 DB 只读冒烟 | 与 WEB 同库 |
| 3.x | WVP / 国标 | 本机可达 WVP 则测；否则记缺口 |
| 4.x | ONVIF / NVR / 真机 | 有设备则测 |
| 5.x | iot-node / Ceph / 媒体池 | 有集群则测 |
| 7.x | 双跑 / 切换 / 回滚 | 本机 Nacos 权重 |

**最高杠杆（阶段 1）：** 0.1 → 0.2 → 0.3。阶段 0 **不起**全套联调。

---

## 3. 需产品拍板

真推理 vs 旁路（InsightFace/Milvus/Paddle/YOLO）；Kafka 永久 direct 是否允许；P2 现场项豁免。未签字不得标「不用做」。

---

## 4. 约定

1. 进度 = 本机完整栈功能等价（对标 Python）。  
2. 禁止 FR-B46+ / 矩阵刷绿。  
3. 日常 `local`；捷径仅 `mini`。  
4. 阶段 1 须另令。
