# 本机完整栈验收阻塞清单

> **话术：** 阶段 0：规矩与商业默认已切换；完整替换进行中；Python 仍为对照，禁止删除。  
> **唯一环境：** 本机（Kafka / MinIO / Nacos / 网关 = 现成依赖，只挂不重写）。  
> **禁止：** COMPLETE、删 main `VIDEO/`、FR-B46+ / 矩阵刷绿、「等 prod / 缺线上」叙事。  
> 日期：2026-08-11（阶段 1 接线完成）

Oracle = `F:/acme` @ main `VIDEO/` · Candidate = worktree `DEVICE/iot-video` · 日常 profile = **`local`**（见 [PHASE0_DEFAULTS.md](./PHASE0_DEFAULTS.md)）

阶段 1 接线报告：[PHASE1_STACK.md](./PHASE1_STACK.md)

---

## 1. 阶段 1 结果（2026-08-11）

| Checklist | 项 | 结果 | 证据 |
|-----------|----|------|------|
| 0.1 | Nacos 注册 + health | **PASS** | `logs/phase1-0.1-evidence.json` |
| 0.2 | 网关 `lb://video-server` | **PASS** | `logs/phase1-0.2-evidence.json` |
| 0.3 | 共享 DB 只读冒烟 | **PASS**（功能）/ **⛔**（5432 字面端口） | `logs/phase1-0.3-evidence.json` |

**已修复配置：** `bootstrap-local.yaml` Nacos discovery 启用；`application-local.yaml` datasource 对齐 `5432` + MinIO env 占位。

---

## 2. 剩余阻塞（阶段 2 前须处理）

| # | 项 | 阻塞说明 |
|---|-----|----------|
| D1 | Desktop PG 端口冲突 | 本机 `postgresql-x64-17` 占用 `:5432`（密码与 `iot-video20` 不一致）；docker `postgres-server` 映射 **`:15432`**。已提交配置为 `5432`；须管理员停止 native PG 或重映射 docker 至 `5432`。 |
| D2 | Nacos 冷启动 | 全新 Nacos 卷须 `POST /nacos/v1/auth/users/admin` 初始化（见 `install_middleware_desktop.sh`）。 |
| 3.x | WVP / 国标 | 本机可达 WVP 则测；否则记缺口 |
| 4.x | ONVIF / NVR / 真机 | 有设备则测 |
| 5.x | iot-node / Ceph / 媒体池 | 有集群则测 |
| 7.x | 双跑 / 切换 / 回滚 | 本机 Nacos 权重 |

**代码路径已备、须本机完整栈复验（阶段 2+）：**

| Checklist | 项 | 历史 local 证据（仅参考） |
|-----------|----|---------------------------|
| 0.4 | phase0（可选防回归） | `mini` profile + certify |
| 1.1–1.4 | Alert / DVR / Snap / Matching Kafka | `logs/fr-b26`～`fr-b27` / `fr-b45` |
| 2.1–2.5 | MinIO | `logs/fr-b23`～`fr-b25` / `fr-b32` |
| 6.1–6.4 | Face/Plate/Pose/匹配告警 | `logs/fr-b41`～`fr-b45` |

---

## 3. 需产品拍板

真推理 vs 旁路（InsightFace/Milvus/Paddle/YOLO）；Kafka 永久 direct 是否允许；P2 现场项豁免。未签字不得标「不用做」。

---

## 4. 约定

1. 进度 = 本机完整栈功能等价（对标 Python）。  
2. 禁止 FR-B46+ / 矩阵刷绿。  
3. 日常 `local`；捷径仅 `mini`。  
4. 阶段 2 须另令。
