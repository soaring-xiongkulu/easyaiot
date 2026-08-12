# VIDEO 仓库切仓与 Python 移除计划（Repo Cutover）

> **日期：** 2026-08-12  
> **状态：** Phase1 已提交；Phase2 draft PR [#143](https://github.com/soaring-xiongkulu/easyaiot/pull/143)（**不删 VIDEO/**）。  
> **分支：** `feat/video-java` @ `9cf6e65e`（以落地时 HEAD 为准）  
> **工作树：** `F:/acme/.worktrees/video-java`  
> **Oracle（对照，勿先删）：** `F:/acme` @ `main` 的 `VIDEO/`；建议保留 tag `video-java-oracle-baseline`  
> **前置：** Part2 Final **W1–W3 PASS**（见 [PART2_FINAL_PLAN.md](./PART2_FINAL_PLAN.md)）  
> **关联：** [HANDOFF.md](./HANDOFF.md) · [CUTOVER.md](./CUTOVER.md) · [CUTOVER_BLOCKERS.md](./CUTOVER_BLOCKERS.md)

---

## 0. 目标一句话

把 **中控 VIDEO 编排面** 永久落在 `DEVICE/iot-video`（Java `video-server`），从本开源仓库 **移除 Python `VIDEO/` 树**；需要对照时从上游 / tag 再取，不在树内双轨维护。

**不在本切仓范围：** EDGE 端侧 Python、AI 训练/标注、RUNTIME C++、ffmpeg/WVP/Kafka/MinIO/Nacos（外挂依赖）。

---

## 1. 现状地图（合并前真相）

| 角色 | 路径 | 说明 |
|------|------|------|
| Candidate（要合入 main） | `DEVICE/iot-video/` | Java 编排；Nacos `video-server`，端口 `48096` |
| Gateway | `DEVICE/iot-gateway/.../application.yaml` | 已是 `lb://video-server`（URI 可不变） |
| Python 服务面（归档副本） | `VIDEO/_retired_python_video/` | Flask `app/`、`services/`、`run.py` 等 |
| 仍挂在 `VIDEO/` 根的资产 | `*.onnx` / 部分 `*.pt`、`scripts/inference_workers/`、`docker-compose.yaml`、`install_*.sh` | **删树前必须先迁走权重与安装入口** |
| 根叙事 | `README.md` / `README_zh.md` | 模块列表仍写独立 **VIDEO** |
| sink 挂载 | `DEVICE/docker-compose.yml` | `../VIDEO/alert_images` |
| 上游对照 | 开源仓库历史 / tag | 删后回滚来源 |

**合并形态建议（已定）：**

1. **Java 模块留在 `DEVICE/iot-video`**（不要再造顶层 `VIDEO-java/`）。  
2. **首个合入 PR 不删 `VIDEO/`**；删除单独 Phase + 单独 PR。  
3. 网关前缀 **`/admin-api/video/**` 保持不变**，降低 WEB/下游破坏面。

---

## 2. 目标架构（切仓完成后）

```text
WEB ──► Gateway /admin-api/video/** ──► Nacos: video-server (Java :48096)
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
              C++ RUNTIME                 ffmpeg / WVP            Kafka / MinIO / PG
           (realtime/snap/patrol)        (本地推流/国标壳)           (外挂)
                    │
                    ▼
         models/（迁出后的中立权重目录）
         + YAML 后处理规则 / 摄像头标定

EDGE（Python）── 仍独立，不进 VIDEO 删除范围
AI（Python workers）── 仍独立
```

开源模块叙事：**「VIDEO」能力 = DEVICE 内 `iot-video` 服务**，不再是顶层 Python 子项目。

---

## 3. 必须迁出 / 必须改掉（删前硬门槛）

### 3.1 权重与模型路径（P0）

| 现状 | 动作 |
|------|------|
| `VIDEO/face_*.onnx`、`plate_*.onnx`、`yolo26n-pose.onnx` 等 | 迁到中立目录，推荐二选一：`DEVICE/iot-video/models/` **或** `RUNTIME/models/`（安装脚本下载亦可） |
| `application-local.yaml` 绝对路径 `F:/acme/.worktrees/video-java/VIDEO/*.onnx` | 改为相对 `ACME_ROOT` / env / `video.inference.*-model-path` |
| `ModelPathResolver` / `VideoModelPaths` 扫 `VIDEO/`、`_retired_python_video` | 只扫新 models 根；去掉 worktree 硬编码 |
| 证据工具 `Part2WaveAEvidenceMain` 等绝对路径 | 改为可配置或相对路径 |

### 3.2 Python 逃逸口（P0）

| 组件 | 动作 |
|------|------|
| `PostProcessLauncherService` → `run_worker.py` | 商业默认已 `java-rules-enabled=true`；**删 VIDEO 前删除或 fortify「仅 Java」**，失败不得静默成功 |
| `PythonInferenceWorker` + `VIDEO/scripts/inference_workers` | 商业 `python-cli-enabled=false`；删除 CLI 目录或迁到 `tools/oracle/`（不进发布） |
| `StreamForwardRemoteDeployService` → 远程 `run_deploy.py` + `remoteVideoRoot=/opt/easyaiot/VIDEO` | 文档标明「多节点清出项」；默认改可配置中立根，**禁止默认假设 VIDEO 树仍在仓库** |
| `_bootstrap.py` 强挂 `_retired` | 随 CLI 一并退役 |

### 3.3 安装 / Compose / 共享盘（P0–P1）

| 项 | 动作 |
|----|------|
| `VIDEO/docker-compose.yaml`（仍假设 `python run.py`） | 废弃或改指向 Java 镜像；根/PANEL/COMPILE 安装改调 `iot-video` |
| `DEVICE/docker-compose.yml` 的 `../VIDEO/alert_images` | 迁中立路径，如 `data/alert_images` 或 `${user.home}/.easyaiot/alert_images` |
| DEVICE compose **缺 iot-video 服务** | 补 Java 服务 + health；否则删 VIDEO 后「无安装入口」 |
| WEB `.env*` 注释 / 直连 `:6000` | 改为 `video-server` / 网关路径说明 |

### 3.4 文档与开源叙事（P1）

| 项 | 动作 |
|----|------|
| 根 README 模块列表 | `VIDEO` → **iot-video（DEVICE / video-server）** |
| Changelog | Breaking：Python VIDEO 退役；迁移步骤；回滚；已知缺口（EDGE/远程 SF/真机） |
| 新建迁移文 | 本文件 + 对外摘要 `MIGRATION_FROM_PYTHON_VIDEO.md`（端口 6000→48096、compose、模型路径、回滚） |
| 权重第三方 NOTICE | InsightFace / YOLO / OCR 等来源与再分发限制写清 |
| LICENSE | 根 MIT 可不变；勿在迁移文档粘真实口令 |

---

## 4. 分阶段执行计划（Phase 0–5）

> **原则：** 合入 Java ≠ 删除 Python。删除是最后一步，且可单独 revert。

### Phase 0 — 冻结与清单（不删、可立刻做）

- [ ] 记录 `feat/video-java` SHA；确认 Oracle tag / `main` `VIDEO/` 可检出  
- [ ] 全仓检索归档：`VIDEO/`、`_retired_python_video`、`inference_workers`、`run_deploy.py`、`/opt/easyaiot/VIDEO`、`:6000`  
- [ ] PR 模板写死：**本 PR 不删 VIDEO**（若开合入 PR）  
- [ ] 产品确认：W1–W3 范围 = 中控替换完成定义；清出项不挡删仓（已在 PART2 锁定）

**回滚：** 无。

---

### Phase 1 — 路径解耦（仍保留 `VIDEO/` 目录）

**目标：** Java 与安装脚本不再 *依赖* 顶层 `VIDEO/` 才能启动商业路径。

- [ ] 模型目录迁出 + 配置去绝对路径  
- [ ] `alert_images` 中立化 + 改 sink compose  
- [ ] 后处理 / CLI：关掉或 fortify py 分支  
- [ ] `remoteVideoRoot` 可配置；文档写清多节点不在本删树范围  
- [ ] 本机 `local` profile：人脸/车牌/姿态/巡检/后处理各一冒烟（沿用已有证据流程）

**回滚：** revert 配置与路径 PR；权重可双份暂留。

**Done when：** 临时把 `VIDEO/` 改名（干跑）后，Java 商业路径仍能解析模型并起服务（或明确失败在「缺模型文件」而非「缺 VIDEO 树结构」）。

---

### Phase 2 — 合入 main（功能合并，**不删树**）

**建议 PR 内容：**

| 包含 | 不包含 |
|------|--------|
| `DEVICE/iot-video/**` + `DEVICE/pom.xml` | 删除 `VIDEO/` |
| gateway 若有差分 | 大范围 README 叙事可放 Phase 3 |
| `docs/video-java/**`、必要 tools | `_retired` 物理删除 |

**检查清单：**

- [ ] `mvn -f DEVICE/pom.xml -pl iot-video/iot-video-biz -am package`  
- [ ] 本机起 Java；Nacos **仅** Java `video-server`（不起 Python `:6000`）  
- [ ] 网关 `/admin-api/video/**` + token 冒烟  
- [ ] 可选：`python tools/video_java/certify.py --phase 0`（防回归，不算进度）  
- [ ] Draft → Ready；合并策略：优先 squash/merge 控制历史噪音  

**回滚（进程级，约 5–15 min）：**

1. 停 Java `video-server`  
2. 从 Oracle / `_retired` / tag 起 Python `:6000` 注册同名  
3. Gateway URI **不变**  

---

### Phase 3 — 安装面与文档切换

- [ ] PANEL / COMPILE / 根安装脚本改 Java `iot-video`，停推 `VIDEO/install_*.sh` 为默认  
- [ ] `VIDEO/docker-compose.yaml` 标 retired 或改为转发说明  
- [ ] README / changelog / `MIGRATION_FROM_PYTHON_VIDEO.md` 发布  
- [ ] WEB 运维注释去掉「主路径直连 :6000」

**回滚：** 恢复 install 入口指向；进程回滚同 Phase 2。

---

### Phase 4 — 资产迁清（`VIDEO/` 变空壳）

- [ ] 权重仅存新位置；校验加载  
- [ ] `scripts/inference_workers`、`ensure_runtime_cpp.sh` 迁 `RUNTIME/scripts` 或 `tools/`  
- [ ] 确认无运行时代码 `Path...("VIDEO", ...)` 商业默认路径  
- [ ] sink / 远程文档不再写死 `../VIDEO/...`

**回滚：** git revert 迁移提交；短期双份权重。

---

### Phase 5 — 删除 `VIDEO/`（单独 PR，最后）

**前置（全部打勾才开删）：**

- [ ] Phase 1–4 Done when 满足  
- [ ] 全仓 `rg`：生产代码无 `VIDEO/`、`_retired_python_video` 硬依赖（文档历史除外可保留）  
- [ ] 迁移文档与 changelog 已合入  
- [ ] **产品 / 维护者明确签字删树**（本文件外的口头确认不够则记入 gates）  
- [ ] 仅用仓库约定的安全删树工具（若有 `tools/runtime_parity/safe_fsops.py`：dry-run → confirm → execute）

**删除范围建议：**

| 删除 | 保留 |
|------|------|
| `VIDEO/` 整树（含 `_retired_python_video`） | `DEVICE/iot-video`、`RUNTIME`、`EDGE`、`AI`、模型新目录 |
| 过时 Python-only install 入口 | Oracle **git tag** / 上游 commit 说明 |

**开源回取策略（你们已定）：**

- 出问题 → 从 **上游开源仓库 / tag `video-java-oracle-baseline` / 删除前 commit** 检出 `VIDEO/`，不在主线双维护。  
- README 迁移文写一行：`git show <tag>:VIDEO/...` 或 clone 历史路径说明。

**回滚：**

1. `git revert` 删除提交 **或** `git checkout <tag> -- VIDEO`  
2. 停 Java → 起 Python `video-server`  
3. 记入 `docs/video-java/gates/ROLLBACK_LOG.md`

---

## 5. PR / 合并节奏（建议）

```text
PR-A  Phase1 路径解耦 + 模型迁出（仍留 VIDEO）
PR-B  Phase2 DEVICE/iot-video 合入 main（不删）
PR-C  Phase3 安装面 + README/changelog/迁移文
PR-D  Phase4 残留引用清零
PR-E  Phase5 删除 VIDEO/（最小 diff，仅删树 + 扫尾引用）
```

当前仓库：**未见** `video-java` 公开 PR；需先 `push -u` 再开 draft。超大 diff 不要把「合入 + 删树」塞进同一 PR。

---

## 6. 风险与明确不做

| 风险 | 缓解 |
|------|------|
| 删权重导致推理断供 | Phase 1/4 先迁后删；Done when 含改名干跑 |
| 误伤 EDGE / AI | 删除范围仅 `VIDEO/`；EDGE/AI **不删** |
| 远程节点仍假定 `/opt/easyaiot/VIDEO` | 清出项；文档 + 可配置；不挡中控删仓但要写进 Breaking |
| compose 空窗 | Phase 3 前必须有 Java 安装入口 |
| 「归档 = 已退役」话术 | `_retired` 只是副本；**以 Phase 5 合入为准** |
| U3 GB / 真机 PARTIAL | 已清出/按需；**不挡**中控 Python 移除（与 PART2 锁定一致） |

---

## 7. 验收口径（切仓专用）

| 阶段 | 什么叫完成 |
|------|------------|
| Phase 1 | Java 商业路径不依赖 `VIDEO/` 目录布局 |
| Phase 2 | main 可编译运行 Java video-server；网关可达 |
| Phase 3 | 新贡献者按 README 装的是 Java，不是 Flask |
| Phase 5 | 树内无 `VIDEO/`；从 tag 可恢复；回滚演练记录存在 |

**不算完成：** 仅 CERTIFY 刷绿、仅 `_retired` 改名、仅文档写 COMPLETE。

---

## 8. 建议下一步（等你点头再动手）

1. **确认本计划**（尤其：模型落点 `DEVICE/iot-video/models` vs `RUNTIME/models`；PR-A～E 节奏）。  
2. 开工 **Phase 1**（路径解耦），仍不删 `VIDEO/`。  
3. 并行准备 **PR-B draft**（合入 iot-video）。  
4. Phase 5 单独要你一句：**「授权删除仓库内 VIDEO/」**。

---

*本文件取代「口头切仓」；执行中若与 HANDOFF 冲突，以「不删直到 Phase 5 签字」为准。*
