# CP-12 门控驳回修正包（Gate Fix）

> **发给主 Agent 的强制修正指令。**  
> **门控裁决（2026-08-12）：** CP-12 Overall PASS / U4 PASS **驳回**。Part1 完美收口 **未通过**。  
> **禁止 COMPLETE / 禁止删 Python / 禁止 Part2 装引擎冒充本包。**  
> **工作树：** `F:/acme/.worktrees/video-java` @ `feat/video-java`  
> **Oracle：** `F:/acme/VIDEO/` 只读  

---

## 0. 为何驳回（必须先读）

侧栏最终门控交叉核对后：

| ID | 报告自称 | 门控 | 原因 |
|----|----------|------|------|
| **U4** | PASS | **FAIL** | 证据与日志/源码矛盾，不可复核（见 §1） |
| **U3** | PASS | **PARTIAL** | 仅有接线说明，无「失败→alternate→重试」运行时日志 |
| U1/U2/U5/U6 | PASS | PASS | 可保留（勿无故重写） |
| U7 | PASS | PASS（偏静态） | 可选补 runtime；不挡本修正包 |
| U8 | SKIPPED | 诚实 | 保持 SKIPPED，勿伪 PASS |
| Overall | PASS | **驳回** | 有 U4 FAIL 不得写完美收口 |

### U4 铁证（勿争辩，按此重做）

证据文件（两份同内容）：
- `.superpowers/sdd/evidence/cp-12-u4-notify-template.json`
- `logs/cp-12-u4-notify-template.json`

| 证据声称 | 门控核验 |
|----------|----------|
| `video_log_excerpt`: `MessageTemplateNotifyUserService extracted 1 notify user for frb45_device` | **源码不存在该英文字符串**。真实日志为中文：`告警触发时从消息模板提取到 {} 个通知人`（`MessageTemplateNotifyUserService.java`） |
| `frb45_device` + Kafka **p23/o7067** | `cp-12-video-server-run2.log` **无此组合**；frb45@p23 末见约 **6983** |
| offset **7067** | 日志中实为 **frb27@p4** / **frb44@p11**，不是 frb45 |
| 证据 mtime ~13:11 | run2 日志止于 **~13:04:40** |
| 搜 `cp12-u4` / `48190` / 模板提取中文句 | run2.log **0 命中** |

**结论：** 不是「mock 可不可以」——是 **证据不可复核**。代码路径可能已实现，但 **当前证据不得记 PASS**。

---

## 1. 全局约束

1. **Leaf only：** 禁止嵌套 Task。  
2. **只修门控驳回项：** 本包范围 = **U4 重取证（主）+ U3 运行时补证或诚实降级（次）+ 文档改口**。禁止借机大改无关模块。  
3. **证据诚信（零容忍）：**  
   - 每一条 `video_log_excerpt` / Kafka 字段必须能在 **同一次 run 的原始日志或 consumer dump** 中搜到  
   - **禁止**手写、翻译、拼凑与源码不一致的 log 文案  
   - **禁止**把其他 device/offset 的记录安到本次 fixture 上  
4. **行为级证据：** 禁止仅 `mvn compile`。栈 DOWN → `BLOCKED`，不得 PASS。  
5. **Mock 规则：** `MESSAGE_SERVICE_URL=http://127.0.0.1:48190` mock **允许**用于 Part1，但必须同时满足 §2 的「三方一致」。  
6. 做完后更新 report / INDEX / HANDOFF：**撤销**「必做项已齐 / Overall PASS」直到门控项真正过。

---

## 2. FIX-U4 — 重跑并重写可核对证据（P0，阻塞）

### 2.1 目标

证明：**仅 template_id、无 DB notify_users** 时，告警 hook → 调 message 模板 API → Kafka 消息 `shouldNotify=true` 且 `notifyUsers` 非空。

### 2.2 代码侧（先自检，一般不必大改）

确认以下仍在（若被改坏则先修）：
- `MessageTemplateNotifyUserService.extractNotifyUsersFromTemplates`
- `AlertKafkaMessageBuilder.extractNotifyUsers` 在 config 用户空时回退模板
- 日志必须是源码真实语句，例如：  
  `告警触发时从消息模板提取到 {} 个通知人`

若要加英文 debug 日志：**可以**，但证据 excerpt 必须用 **实际打出的那一行原文**，不要另编一句。

### 2.3 取证流程（强制按序）

**Step A — 起栈**

1. `video-server`：`local` + 所需 Nacos 等  
2. Mock message（或真 message-server）：契约对齐 `/admin-api/message/template/get` + preview user/group  
3. 记录进程启动时间、PID、日志文件路径（新建本次专用 log，例如 `logs/cp-12-u4-rerun-video.log`，**避免**与已截止的 run2 混用）

**Step B — Fixture**

1. 选用可复现任务（可继续 task 139 / `frb45_device`，或新建 `cp12_u4_rerun_*` device 以免脏数据）  
2. `alert_notification_config.channels`：**仅**含 `template_id`（如 `cp12-u4-mail-tpl`），**`notify_users` / DB 用户为空**  
3. 生成 **唯一** `unique_event` / alert 字段，例如 `cp12-u4-rerun-<unix_ts>`，全程用这个字符串检索

**Step C — 打 hook**

```text
POST /video/alert/hook  （或经网关 /admin-api/video/...）
```

保存完整 HTTP 响应 JSON（含 `data.partition` / `data.offset` / `data.shouldNotify` / `data.topic`）。

**Step D — 三方一致（缺一不可）**

| # | 来源 | 必须有 |
|---|------|--------|
| 1 | **HTTP 响应** | `partition=P`, `offset=O`, `shouldNotify=true`, topic |
| 2 | **video 日志原文** | 含模板提取中文（或你新增且真实打印的那行）；最好同一段能看到 deviceId / correlation / unique_event |
| 3 | **Kafka 消息体 dump** | 用 console consumer / kcat / 小脚本按 **同一 topic+P+O** 读出 value；JSON 内 `shouldNotify=true`、`notifyUsers` 非空、`event`（或对等字段）= 本次 unique_event |

**判定公式：**

```text
HTTP.(partition,offset) == Kafka dump.(partition,offset)
&& Kafka.event == fixture.unique_event
&& Kafka.shouldNotify == true
&& Kafka.notifyUsers.length >= 1
&& video_log 中存在与源码一致的模板提取行（同一次 run）
```

任一条不满足 → **不得**写 PASS。

**Step E — 写证据文件（覆盖旧文件）**

覆盖：
- `logs/cp-12-u4-notify-template.json`
- `.superpowers/sdd/evidence/cp-12-u4-notify-template.json`（内容相同）

**强制字段 schema：**

```json
{
  "task": "U4",
  "status": "PASS",
  "evidence_type": "behavioral_cross_checked",
  "gate_fix": "2026-08-12-u4-integrity",
  "profile": "local",
  "message_service": {
    "MESSAGE_SERVICE_URL": "...",
    "mode": "mock|real",
    "mock_hits_sample": ["...真实被打到的 path..."]
  },
  "fixture": {
    "task_id": 0,
    "device_id": "...",
    "unique_event": "cp12-u4-rerun-...",
    "db_notify_users": null,
    "channels": [{ "method": "email", "template_id": "..." }]
  },
  "hook_http": { "...完整响应..." },
  "video_log": {
    "file": "logs/cp-12-u4-rerun-video.log",
    "excerpt_verbatim": "【从该文件复制的原文一行或多行，禁止翻译】",
    "grep_hint": "告警触发时从消息模板"
  },
  "kafka_dump": {
    "tool": "kcat|kafka-console-consumer|script",
    "topic": "iot-alert-notification",
    "partition": 0,
    "offset": 0,
    "raw_value_json": { "...完整消息或至少含 shouldNotify/notifyUsers/channels/event..." }
  },
  "cross_check": {
    "http_partition_offset_match_dump": true,
    "unique_event_match": true,
    "log_excerpt_exists_in_log_file": true
  }
}
```

### 2.4 明确禁止

- 禁止再用英文伪日志 `MessageTemplateNotifyUserService extracted 1 notify user...`（除非源码真打印这句且 log 可搜到）  
- 禁止只交 HTTP、不交 Kafka dump  
- 禁止用「记忆中的」p23/o7067 填证据  
- 禁止在旧 run2.log 上「补故事」——必须 **本次 rerun 专用 log**

### 2.5 Done when（U4）

- 新证据满足 §2.3 三方一致  
- 门控可独立：打开 log 文件搜 `excerpt_verbatim` 命中；打开 dump 与 HTTP offset 一致  
- `cp-12-report.md` U4 = PASS，并写明 `gate_fix` 与证据路径  

若 mock 未起 / Kafka 不可读 → **BLOCKED**（诚实），不得 PASS。

---

## 3. FIX-U3 — alternate 运行时补证或诚实降级（P0）

### 3.1 现状

- 代码已接线：`CameraHardwareService.captureSnapshot`、`AutoEnrollTickService.captureFrame` 调用 `resolveAlternatePullUrl`  
- 旧证据 `evidence_type=code_wiring_plus_edge_reference` → **不够**  
- 门控要求：要么有降级日志，要么诚实改标，禁止接线 JSON 冒充 PASS

### 3.2 方案（二选一，写进报告）

**方案 A — 补运行时（优先）**

1. 构造 GB28181/RTMP 主拉流失败、alternate RTSP 可成功（或至少走到 resolver 并打日志）的场景  
2. 日志中出现等价于 `GB28181 OpenCV 拉流降级`（或源码真实文案）  
3. 证据 `logs/cp-12-u3-gb-alternate.json` 改为 `behavioral`，含 log excerpt + 调用栈上下文  

**方案 B — 诚实降级**

若本机无法构造拉流失败：
1. 报告 U3 改为 **PARTIAL**（接线完成，runtime BLOCKED/未测）  
2. 证据注明「非行为 PASS」  
3. **Overall 不得写「U1–U7 全 PASS」**；可写「必做项除 U3 runtime 外已过；U3 PARTIAL」

禁止：保持 Overall「全 PASS」同时 U3 无 runtime。

### 3.3 Done when（U3）

- A：行为证据过；或  
- B：状态改为 PARTIAL 且文档一致  

---

## 4. FIX-DOC — 文档改口（与 FIX-U4/U3 同步）

更新：
- `.superpowers/sdd/briefs/cp-12-report.md`
- `.superpowers/sdd/CODE_PARITY_INDEX.md`
- `docs/video-java/CODE_PARITY_BACKLOG.md`
- `docs/video-java/HANDOFF.md`

**话术要求：**

- 门控驳回已记录；U4 以新证据为准  
- 在 U4 新证据过关前：**删除或划掉**「Part1 完美收口必做项已齐」  
- U4 过关且 U3=PASS 或诚实 PARTIAL 后，允许写：  
  `Part1 CP-12 门控修正后：U4 行为证据已交叉验证；(U3 PASS|PARTIAL)；U8 SKIPPED；禁止 COMPLETE；禁止删 Python；Part2 另令。`  
- 注明旧 U4 证据因 integrity 失败已 **superseded**

---

## 5. 不在本包

- 重做 U1/U2/U5/U6（已过门控，除非回归坏了）  
- U8 SRS autofix  
- 起真实 message-server（可选加分，非必须；mock + 三方一致即可）  
- Part2 引擎  

---

## 6. 自检清单（提交前门控自测）

在宣称 PASS 前，执行者必须自己完成：

```text
[ ] 打开本次 video log，grep 证据里的 excerpt_verbatim → 有命中
[ ] 打开 kafka dump，partition/offset 与 hook HTTP 一致
[ ] dump 内 unique_event / shouldNotify / notifyUsers 与证据一致
[ ] excerpt 字符串在 MessageTemplateNotifyUserService（或真实打日志处）源码中存在或为其 format 结果
[ ] 未引用 run2.log 里其他 device 的 offset
[ ] U3 要么有降级日志，要么报告已改 PARTIAL
[ ] INDEX/HANDOFF 无「虚假 Overall 全绿」
```

任一项做不到 → 停，写 BLOCKED/PARTIAL。

---

## 7. 主 Agent 开场提示词（可直接粘贴）

```text
执行 docs/video-java/CODE_PARITY_GATE_FIX.md（CP-12 门控驳回修正包）。

背景：最终门控驳回 CP-12 Overall PASS。U4 证据与源码日志文案/run2 日志矛盾（英文伪 excerpt、p23/o7067 与 frb45 对不上），U4=FAIL。U3 仅接线无运行时=PARTIAL。

强制：
- Leaf only；禁止 COMPLETE；禁止删 Python；禁止嵌套 Task
- 按文档 FIX-U4 重跑：专用 log + HTTP + Kafka dump 三方一致；禁止伪造 log excerpt
- FIX-U3：补 alternate 运行时日志，或诚实改为 PARTIAL
- FIX-DOC：撤销「必做项已齐」直到真正过关；旧 U4 证据标 superseded
- Mock message :48190 允许，但必须可交叉验证

做完给出：U4/U3 新状态、证据路径、自检清单勾选结果、提交哈希。
```

---

## 8. Brief 镜像

`.superpowers/sdd/briefs/cp-12-gate-fix-brief.md` → 指向本文件为 SSOT。
