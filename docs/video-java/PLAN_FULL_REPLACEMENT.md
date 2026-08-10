# VIDEO 完整功能替换 — Phase FR 方案

> **For agentic workers:** 本文件是 **Phase FR（Full Replacement）** 的唯一执行方案。  
> **进度表：** [`FULL_REPLACEMENT_GAP.md`](./FULL_REPLACEMENT_GAP.md)（按域勾选）。  
> **历史切片：** Phase -1～3 + EVID 仅作脚手架基线，**不再**当作「项目完成」或「整域 migrated」。

**Goal:** 把 Python VIDEO 的 **HTTP 契约面 + 关键后台守护/调度** 迁到 Java `DEVICE/iot-video`，使 WEB/网关可无功能豁免地使用 Java，并最终退役 Python。

**Architecture:** 以缺口表驱动按域搬迁；读 Python blueprint/service → Java 同前缀 API + 服务 → 短契约测 + 路由清单 diff。旧 oracle/candidate certify **降级为极薄防回归烟雾**。

**Tech Stack:** 不变，见 [`STACK.md`](./STACK.md)。

## Global Constraints

1. **完成定义 = 缺口表域级全 ✅**（路由 + 该域关键后台任务），**不是** `CERTIFY` 全绿、**不是** COMPLETE 话术、**不是** 15～30min observe。
2. **禁止**再标整域 `migrated` / 项目 `COMPLETE`，除非该域在 `FULL_REPLACEMENT_GAP.md` 已全部勾完。
3. **禁止**再堆 CLOSE / EVID / 长观察当作开发进度。
4. **旧 certify：** 仅保留极薄 P0 烟雾（health、真 RUNTIME 启停、alert hook `success`）；每次合入可跑；**不得**用 Phase 1/2/3 全绿当进度 KPI。
5. **扩面验证：** 契约测试（HTTP 状态 / `code` / 关键字段）+ Python↔Java **路由清单 diff**；**不要**为每个新 API 录双边 golden。
6. **长观察：** 移出开发门禁；仅预发/切流 runbook 可选（见 `CUTOVER.md`）。
7. **Oracle：** `VIDEO/_retired_python_video/` 为只读对照；缺对照时允许临时恢复 oracle，**禁止**再把归档当「完成」手段。
8. **EX-*：** 完整替换目标下 = **待实现 backlog**，不是「不用做」（产品书面永久豁免除外，须改缺口表并签字）。
9. **不重写** RUNTIME / ffmpeg / SRS/ZLM / 深度学习引擎。

---

## 0. 角色重定义（门禁 vs 进度）

| 机制 | 旧角色（已废） | 新角色 |
|------|----------------|--------|
| Phase 0/1/2/3 CERTIFY 全绿 | 完成定义 / COMPLETE | **废止为进度**；P1/P2/P3 报告仅历史档案 |
| P0 薄烟雾（health / RUNTIME / hook success） | 与整包 certify 混为一谈 | **防回归**：合入前可选/建议跑，挡骨架回退 |
| 15～30min observe | Phase PASS 证据 | **仅切流/预发运维**；开发期不跑、不算 PASS |
| `BLUEPRINT_GAP`「migrated」 | 暗示域已迁完 | 改为 **slice-only**；真进度只看缺口表 |
| `FULL_REPLACEMENT_GAP.md` | 审计旁注 | **唯一进度表 + 完成定义** |

**KPI（唯一）：** 缩小路由差 **≈265 → ≈29**，以及缺口表 P0/P1（及未豁免 P2）域勾选。

---

## 1. 与历史 Phase 的关系

| 阶段 | 定性 | 以后怎么用 |
|------|------|------------|
| Phase -1～0 | 高价值骨架（模块、ProcessBuilder、hook、心跳） | **保留代码**；烟雾继续防回归 |
| Phase 1～2 | 窄切片刷绿 | **保留已实现端点**；不再扩 golden 剧 |
| Phase 3 + CLOSE | 改名/归档/网关/观察 | **运维档案**；归档 ≠ 功能完成 |
| EVID-S1～S6 | 证据含金量修补 | **已结束**；勿再开 EVID 轮次 |
| **Phase FR（本文件）** | **完整替换主线** | 唯一开发主路径 |

历史文档 [`PLAN.md`](./PLAN.md) 顶部已加「切片基线 / 完整替换见本文」横幅。

---

## 2. 开发主路径（每个工作包）

```text
1. 打开 FULL_REPLACEMENT_GAP.md 对应域「仍缺」表
2. 读 Python：blueprint 路由 + service 实现（_retired 或临时恢复的 oracle）
3. 在 Java 补齐同 URL 前缀的 Controller/Service（字段级对齐 {code,msg,data}）
4. 加/更新该域契约测试（状态码 + 关键字段；直连 :48096）
5. 跑路由清单 diff：该前缀下 Py 路由数 vs Java @*Mapping 数
6. 跑一次薄烟雾：python tools/video_java/certify.py --phase 0（防回归）
7. 在 FULL_REPLACEMENT_GAP.md 勾选已实现行；更新「Py vs Java」计数
8. 小提交：feat(video-java): FR-<域> <能力摘要>
```

**不要：** 新开 PHASE_N_GATE 剧、录双边 golden、16min observe、标 COMPLETE。

---

## 3. 薄烟雾门禁（保留且仅此）

**命令：** `python tools/video_java/certify.py --phase 0`（exit 0）

**允许计入烟雾的 case（保持极薄）：**

| Case | 必须证明 |
|------|----------|
| `vj_p0_health` | candidate health 可达 |
| `vj_p0_task_start_stop` | 真 `RUNTIME.exe` 启停；`executor_bin` 非 stub |
| `vj_p0_alert_hook` | `hook_status=success`（非 skipped） |
| `vj_p0_heartbeat` / `vj_p0_restart` | 可选保留；若 flaky 则修或降级，不扩面 |

**明确移出开发 PASS：** Phase 1/2/3 全绿、长观察、gateway auth 长证据链（切流前再跑 runbook）。

工具演进（可后续小步做，不阻塞 FR-W1）：

- `tools/video_java/route_inventory.py` — 扫 Python 路由 vs Java Mapping，输出缺口计数
- `tools/video_java/contract_smoke.py` — 按域对「已宣称实现」的路径做短 GET/POST 契约抽检

---

## 4. 工作包切分（按缺口表 P0→P1→P2）

完成定义：**该包在 `FULL_REPLACEMENT_GAP.md` 对应行全部 ✅**，并附该域「Py 路由数 / Java 映射数」更新。

### Wave 0 — 治理（先做，1 个短包）

| ID | 交付 | Done when |
|----|------|-----------|
| FR-W0 | 话术与门禁角色切换落地 | 本文 + HANDOFF/PLAN/CERTIFY/BLUEPRINT_GAP 已改；禁止 COMPLETE；缺口表为进度入口 |

### Wave 1 — P0（阻塞切流的管理面与自愈）

| ID | 工作包 | 主要缺口（见 GAP §2） | Done when（可核对） |
|----|--------|----------------------|---------------------|
| FR-W1-ALERT | Alert 管理面 | page/count/statistics/image/record/clear… | GAP §2.2 全部 ✅；`/video/alert` 前缀路由差写入缺口表总览；`route_inventory.py` 可打印该前缀 Py vs Java 数；`--phase 0` 仍绿 |
| FR-W1-ALGO | Algorithm CRUD + patrol heartbeat + logs/streams 骨架 | create/update/delete；heartbeat/patrol；logs | GAP §2.1 相关行 ✅ + 路由差更新 + phase 0 绿 |
| FR-W1-BG | auto_start / 健康恢复对等 | auto_start 算法+推流；与 Python 重启恢复语义对齐 | GAP §3 对应行 ✅ |
| FR-W1-AUTH | Gateway + system-server 鉴权真通 | 去掉或兑现 `EX-GATEWAY-AUTH-LOCAL` | **切流门槛（不可跳过）**；短网关+token 冒烟 |
| FR-W1-KAFKA | Alert Kafka **或** 产品书面永久 direct | 去掉或接受并改缺口表 | **切流门槛（不可跳过）**；实现或产品签字写入 GAP |

**切流硬门槛（钉死）：** 在宣称「可安全切流 / 完整替换可切」之前，`FR-W1-AUTH` 与 `FR-W1-KAFKA`（或产品书面永久 direct）**必须闭环**。`FR-W2-CAM` 等可与 Wave 1 后半**并行开发**，**不能代替** AUTH/KAFKA。立即开工顺序先做 ALERT→ALGO→BG→CAM，**不表示** AUTH/KAFKA 从阻塞清单消失。

**FR-W1-ALERT 工具门槛：** 本包结束前必须交付最小 `tools/video_java/route_inventory.py`（至少能打印指定前缀下 Python 路由数 vs Java `@*Mapping` 数）；契约抽检脚本可后补。

### Wave 2 — P1（设备台 / 媒体主路径）

| ID | 工作包 | 范围摘要 |
|----|--------|----------|
| FR-W2-CAM | Camera 主路径 | 注册/CRUD/目录/ONVIF/PTZ/snapshot/流票据（GAP §2.3）；**不替代** W1-AUTH/KAFKA 切流门槛 |
| FR-W2-MEDIA | Snap/Record/Playback 主路径 | 空间+文件+任务（非仅 list） |
| FR-W2-SF | Stream-forward CRUD + auto_start | list/create/update/delete/restart/… |
| FR-W2-HOOKS | Media hooks SRS/ZLM 全套 | on_dvr/on_publish/… |
| FR-W2-PATROL | Patrol session API | 去掉 EX-PATROL-SESSION-API |
| FR-W2-MATCH | Post-process 真 sink；face/plate 库+识别或旁路 | 去 stub/mock（产品拍板） |

### Wave 3 — P2（长尾）

| ID | 工作包 |
|----|--------|
| FR-W3-CAM-TAIL | NVR/扫描/FlightHub/GB28181 |
| FR-W3-TALK | audio_talk |
| FR-W3-POSE | scenario_pose |
| FR-W3-OPS | janitor / disk guard / 远程 node 等 |

### Wave 4 — 收尾（仅当缺口表 P0/P1 + 未豁免 P2 全 ✅）

| ID | 交付 |
|----|------|
| FR-W4 | 全量路由 diff≈0（或仅剩已签字永久豁免）；全量回滚演练；再允许宣布「完整替换完成」并退役 Python |

---

## 5. 推荐立即开工顺序

1. **FR-W0**（文档已落地）  
2. **FR-W1-ALERT** — Alert 管理面（含 `route_inventory.py` 最小交付）  
3. **FR-W1-ALGO** — Algorithm CRUD + patrol heartbeat  
4. **FR-W1-BG** — auto_start / 重启恢复  
5. **FR-W2-CAM** — Camera 主路径（可并行，**不替代**下列门槛）  

**并行但不可省略（切流前必须闭环）：**

- **FR-W1-AUTH**
- **FR-W1-KAFKA**（或产品书面永久 direct，写入缺口表）

每包结束只更新缺口表 + 短契约 +（ALERT 起）`route_inventory`；**不必**再开 Phase 门禁剧。

---

## 6. 文件与对照路径

| 用途 | 路径 |
|------|------|
| 进度 / 完成定义 | `docs/video-java/FULL_REPLACEMENT_GAP.md` |
| 本方案 | `docs/video-java/PLAN_FULL_REPLACEMENT.md` |
| Python 对照 | `VIDEO/_retired_python_video/app/blueprints/*.py` + `.../services/` |
| 外部 oracle（可选） | `F:/acme/VIDEO` @ `video-java-oracle-baseline` |
| Java | `DEVICE/iot-video/iot-video-biz/.../controller|service` |
| 薄烟雾 | `tools/video_java/certify.py --phase 0` |
| 切片历史（只读） | `docs/video-java/PLAN.md`、`gates/PHASE_*_GATE.md` |

---

## 7. 成功画像（Phase FR）

- [ ] 缺口表 P0 工作包全部 ✅  
- [ ] 缺口表 P1 工作包全部 ✅（或产品签字的永久豁免行）  
- [ ] 路由清单：Java 映射覆盖 Python 前缀（差→0 或仅豁免）  
- [ ] 薄烟雾仍绿（骨架未回退）  
- [ ] 切流 runbook 在预发执行（含可选长观察）——**不算**开发中期 PASS  
- [ ] 仅此时允许对外说「Java 完整替换 Python VIDEO」

**在此之前：** 对外只说 **「完整替换进行中（Phase FR）」** 或 **「切片脚手架已具备」**；禁止 COMPLETE。
