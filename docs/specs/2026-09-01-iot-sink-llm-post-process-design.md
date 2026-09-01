# iot-sink 大模型（LLM）后处理改造详细设计

## 1. 背景与目标

平台大模型能力（`AI` 模块：`llm_config` 模型配置、`llm_gateway_client` 统一调用网关、`rag_expert` 智能体/知识集、RAG 检索）已完善，但算法事件链路（RUNTIME → iot-sink → 告警落库/通知）尚未接入大模型。本设计在 **iot-sink 增加大模型后处理**：

- 算法任务命中告警事件后，按**事件规则**匹配已绑定的**智能体**，对事件时刻的**图片**或事件间隔的**视频**进行大模型研判。
- 大模型研判**不阻塞、不影响**现有告警主链路性能，通过**独立队列**异步消费。
- 支持按规则配置**是否二次判断**（二次判断 = 大模型结论决定/门控告警通知），判断方式可选**图片或视频**，视频**时长（事件前后窗口）可配置**。

## 2. 现状与改造定位

### 2.1 现有链路（已核实）

```
RUNTIME(C++) AlgoMqttBus ──EMQX mqtt/iot-alert-notification──┐
VIDEO alert_hook_service ──────────Kafka iot-alert-notification──┤
                                                               ▼
                                    iot-sink IotAlgoBusMqttHandler.handleAlert
                                    AlertNotificationConsumer.consumeAlertNotification
                                                               │
                                               AlertServiceImpl.processAlert/processSnapshotAlert
                                                               │
                                          ┌────────────────────┴────────────────────┐
                                          ▼                                       ▼
                                落库 VIDEO.alert（image→MinIO）         通知：iot-alert-notification-send
                                发布 iot-alert-created（flow）         （iot-message 消费）
```

- 告警统一处理入口：`AlertServiceImpl`（`iot-sink-biz/.../service/impl/AlertServiceImpl.java`），MQTT 与 Kafka 两路均汇聚于此，是插入 LLM 后处理的最佳扩展点。
- 事件规则**内嵌在算法任务**上（`VIDEO/models.py AlgorithmTask`：`alert_event_enabled`、`alert_class_names`、`alert_event_suppress_time`、`defense_schedule` 等），**无独立 event_rule 表**。
- 已有 POST 后处理范式（`PostProcessRequestConsumer` → `PostProcessServiceImpl.dispatchAndPublishResult` → worker `/execute` → `PostProcessResultConsumer` → `persistResultAndDispatchAlerts`），按 `correlation_id` 去重落 `algorithm_post_process_result`。LLM 后处理沿用该范式：**独立 topic、独立消费者、correlation_id 贯穿**。
- 智能体：`AI/db_models.py RagExpert`（表 `rag_expert`，含 `system_prompt` + 知识集组合），即本设计绑定的"智能体"。
- LLM 调用网关：`AI/app/services/llm_gateway_client.py`，`invoke_vision`（base64 图片）、`invoke_video`（video_url 或 base64，内部流式聚合），可直接复用；`AI/app/blueprints/llm.py` 已有 vision/video 理解 HTTP 接口（前缀 `/model/llm`）。

### 2.2 改造定位

| 层 | 模块 | 职责 | 改动量 |
| --- | --- | --- | --- |
| 配置 | VIDEO（库 + API + WEB） | 任务级总开关、事件规则绑定智能体 | 中 |
| 匹配/投递 | iot-sink（Java） | 事件规则匹配命中后投递独立队列，主链路零等待 | 小 |
| 执行 | iot-sink 新消费者（Java） | 消费独立 topic，同步调 AI 内部研判接口（独立并发，不占告警线程） | 中 |
| 研判 | AI（Python） | 新增内部研判接口：组装智能体提示词 + RAG 上下文 + 图片/视频窗口切片 + 调用 LLM + JSON 结构化输出 | 中 |
| 回写 | iot-sink（Java） | 结论回写 `alert.information`/新表，按门控策略补发或抑制通知 | 小 |

## 3. 总体架构与消息流

```
                ┌──────────── 告警主链路（性能关键路径，零新增阻塞）────────────┐
告警事件(MQTT/Kafka) → IotAlgoBusMqttHandler/AlertNotificationConsumer → AlertServiceImpl
        │ 落库 alert（llm_judge_status 按需写 pending）  │ 通知（非门控模式照常发送）
        ▼                                              │
   LlmRuleMatcher.match(msg) ──命中且规则 enabled──► 投递 Kafka iot-alert-llm-judge
        │ 未命中：不投递，链路与现状完全一致              │（QoS 保证，producer 失败仅记日志，不影响主链路）
        ▼                                              ▼
┌──────────────────────── 独立 LLM 研判队列（与告警消费隔离）────────────────────────┐
│ AlertLlmJudgeConsumer（新消费者，concurrency=2~4，独立 group）                       │
│   └─ LlmJudgeService.execute(msg)                                                  │
│        └─ HTTP POST AI 模块 /model/llm/internal/judge（同步调用，超时可控）         │
│             ├─ 按 agent_id 组装 system_prompt（rag_expert）+ 可选 RAG 检索上下文    │
│             ├─ media_type=image → invoke_vision（MinIO image_url）                 │
│             ├─ media_type=video → ffmpeg 按事件前后窗口切片 → invoke_video          │
│             └─ 返回 {confirm, confidence, reason, structured}（JSON 约束输出）      │
│   └─ 回写：落 algorithm_llm_judge_result（审计）                                    │
│        └─ 更新 alert.information.llm + llm_judge_status                            │
│             ├─ 模式A（后置增强，无门控）：仅回写，通知已发                            │
│             └─ 模式B（二次判断，门控）：confirm→补发 iot-alert-notification-send；    │
│                 reject→回写抑制原因，不发通知                                        │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 关键设计原则

1. **主链路零等待**：规则匹配命中后仅做一次 Kafka 投递（毫秒级），立即返回；LLM 调用（秒级~分钟级）全部发生在独立消费者线程。LLM 服务故障、topic 故障**不得**影响告警落库与通知。
2. **独立队列**：新增 topic `iot-alert-llm-judge`（请求）与 `iot-alert-llm-result`（结果，可选，用于审计/回放），独立 group、独立并发、独立 DLT。
3. **幂等**：以 `correlation_id` 为唯一键，结果落库与回写均先查重（沿用 `PostProcessServiceImpl.existsByCorrelationId` 模式）。
4. **降级**：LLM 调用失败按规则 `fail_policy` 处理（默认 `skip`：不改动原告警/通知结果），门控模式下 `skip` 等价于放行原始结果，避免大模型故障导致漏报。

## 4. 配置模型

回答架构问题：**算法任务需要增加"开启大模型后处理"总开关**，与现有 `post_process_enabled`（脚本/POST 规则后处理）并列、互不替代。其下按"事件规则"粒度绑定智能体。

### 4.1 `algorithm_task` 新增列（VIDEO 库，沿用 `ensure_*_columns` 兼容迁移模式，参考 `ensure_algorithm_task_post_process_columns` `VIDEO/models.py:2938`）

```sql
ALTER TABLE algorithm_task ADD COLUMN llm_post_process_enabled BOOLEAN DEFAULT FALSE NOT NULL; -- 任务级总开关
```

总开关关闭时，即使存在规则也不投递；总开关打开但无规则，等同关闭。

### 4.2 新表 `algorithm_task_llm_rule`（事件规则 × 智能体绑定）

```sql
CREATE TABLE IF NOT EXISTS algorithm_task_llm_rule (
    id               SERIAL PRIMARY KEY,
    task_id          INTEGER      NOT NULL REFERENCES algorithm_task(id) ON DELETE CASCADE,
    rule_name        VARCHAR(100) NOT NULL,                       -- 规则名称（前端展示）
    -- 事件匹配维度：与告警 alert.object / information.detections[].class_name 匹配
    match_objects    JSONB,        -- 匹配的检测对象/事件类别，NULL=全部（如 ["person","vehicle"]）
    match_events     JSONB,        -- 匹配的事件类型，NULL=全部（如 ["detection","intrusion"]）
    -- 智能体绑定
    agent_id         INTEGER      NOT NULL,                       -- rag_expert.id（智能体）
    model_id         INTEGER      NULL,                           -- llm_config.id，NULL=用智能体/系统默认模型
    -- 判断方式
    judge_mode       VARCHAR(10)  NOT NULL DEFAULT 'image',       -- image: 事件时刻图片; video: 事件间隔视频
    -- 视频窗口（仅 judge_mode=video 生效）：事件时间前/后各取 N 秒
    video_pre_seconds   INTEGER DEFAULT 5,                        -- 事件前窗口（秒）
    video_post_seconds  INTEGER DEFAULT 10,                       -- 事件后窗口（秒）
    video_max_seconds   INTEGER DEFAULT 30,                       -- 切片最大时长（秒），防超长请求
    -- 二次判断（门控）
    secondary_judge  BOOLEAN      NOT NULL DEFAULT FALSE,         -- true=大模型确认后才发通知; false=后置增强仅回写
    fail_policy      VARCHAR(10)  NOT NULL DEFAULT 'skip',        -- LLM失败时: skip(不改动原结果)/confirm(放行)/reject(抑制)
    -- 提示词与输出
    prompt_override  TEXT         NULL,                           -- 覆盖智能体默认研判提示词（含占位符）
    require_json     BOOLEAN      NOT NULL DEFAULT TRUE,          -- 强制 JSON 结构化输出 {confirm,confidence,reason}
    -- 节流与启停
    min_interval_sec INTEGER      DEFAULT 0,                      -- 同任务/设备 LLM 研判最小间隔（秒），0=不限
    priority         SMALLINT     DEFAULT 5,                      -- 规则优先级（多规则命中取最高）
    enabled          BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMP    DEFAULT NOW(),
    updated_at       TIMESTAMP    DEFAULT NOW(),
    UNIQUE (task_id, rule_name)
);
```

> 说明：平台当前事件规则内嵌于 `algorithm_task`（无独立事件规则表），故"事件规则绑定智能体"落为**任务下多条匹配规则**。若后续平台抽象出独立事件规则实体，本表可平滑迁移为 `event_rule_id` 外键。

### 4.3 新表 `algorithm_llm_judge_result`（研判审计/回放）

```sql
CREATE TABLE IF NOT EXISTS algorithm_llm_judge_result (
    id               SERIAL PRIMARY KEY,
    correlation_id   VARCHAR(64)  NOT NULL,                       -- 与 alert.correlation_id 对齐，唯一去重
    alert_id         INTEGER      NOT NULL,                       -- 关联告警
    task_id          INTEGER,
    device_id        VARCHAR(100),
    rule_id          INTEGER,
    agent_id         INTEGER,
    model_id         INTEGER,
    judge_mode       VARCHAR(10),
    media_url        VARCHAR(500),                                -- 图片 URL 或视频切片 URL
    prompt           TEXT,                                        -- 实际发送提示词（含 RAG 上下文）
    raw_response     TEXT,                                        -- 模型原始返回
    confirm          BOOLEAN,                                     -- 研判结论：事件成立?
    confidence       FLOAT,
    reason           TEXT,                                        -- 模型理由
    structured       JSONB,                                       -- 解析后的结构化输出
    duration_ms      INTEGER,                                     -- 单次研判耗时
    status           VARCHAR(20) NOT NULL DEFAULT 'pending',      -- pending/success/error/dlt
    error_msg        TEXT,
    created_at       TIMESTAMP DEFAULT NOW(),
    updated_at       TIMESTAMP DEFAULT NOW(),
    UNIQUE (correlation_id)
);
```

### 4.4 `alert` 新增列（门控模式状态机，兼容模式参考已有 `ensure` 迁移）

```sql
ALTER TABLE alert ADD COLUMN llm_judge_status VARCHAR(20) NULL;  -- pending/confirmed/rejected/error/skipped
ALTER TABLE alert ADD COLUMN llm_judge_detail TEXT NULL;         -- JSON：研判结论快照（冗余，避免每次读表）
```

`information` 字段同时合并写 `llm` 节点（双写：列用于筛选/统计，JSON 用于前端展示与 API 兼容）。

### 4.5 配置示例（WEB 前端"大模型后处理"Tab 编辑结果）

```json
{
  "llm_post_process_enabled": true,
  "llm_rules": [
    {
      "rule_name": "周界入侵二次确认",
      "match_objects": ["person", "vehicle"],
      "match_events": null,
      "agent_id": 3,
      "model_id": 1,
      "judge_mode": "video",
      "video_pre_seconds": 5,
      "video_post_seconds": 10,
      "video_max_seconds": 30,
      "secondary_judge": true,
      "fail_policy": "skip",
      "prompt_override": "判断画面中是否存在人员翻越围墙的行为，输出JSON..."
    },
    {
      "rule_name": "消防通道占用增强标注",
      "match_objects": ["car"],
      "match_events": null,
      "agent_id": 5,
      "judge_mode": "image",
      "secondary_judge": false,
      "fail_policy": "skip"
    }
  ]
}
```

## 5. 事件规则匹配与投递（iot-sink）

### 5.1 匹配时机与位置

`AlertServiceImpl.processAlert / processSnapshotAlert` 是 MQTT/Kafka 两路告警的统一入口（`IotAlgoBusMqttHandler.handleAlert` 与 `AlertNotificationConsumer`/`SnapshotAlertConsumer` 均调用之）。在 `AlertService` 内新增扩展点：

```java
// AlertServiceImpl 落库成功后（拿到 alertId）：
llmJudgeEnricher.tryEnqueue(msg, alertId);   // 命中规则 → 投递，未命中 → 直接返回
```

- **模式 A（无门控）**：匹配与投递放在落库之后，主链路后续通知照常，LLM 结论异步回写。
- **模式 B（门控）**：匹配结果需提前于通知决策。在 `IotAlgoBusMqttHandler.handleAlert` / 消费者中，通知发送前调用 `llmJudgeEnricher.isGated(msg)`（内部查规则，命中 `secondary_judge=true` 返回 true），门控时跳过 `maybeForwardNotification`，落库时置 `llm_judge_status='pending'`。查询有缓存（规则表变更走 VIDEO 推送失效），单次查询控制在毫秒级。

### 5.2 匹配规则

1. 按 `device_id + task_type + is_enabled` 关联 `algorithm_task`，取 `llm_post_process_enabled=true` 的任务规则集（复用/扩展 `enrichNotificationFromVideoDb` 的查询模式，`IotAlgoBusMqttHandler.java:292`）。
2. 规则内 `match_objects`/`match_events` 与告警 `alert.object`、`information.detections[].class_name`、`alert.event` 匹配（复用 `AlertClassFilter` 的解析方式）。
3. 多条命中取 `priority` 最高的一条；同规则受 `min_interval_sec` 节流（Redis SETNX 或 DB 时间戳比较，推荐 Redis，key：`llm:judge:{taskId}:{deviceId}:{ruleId}`）。
4. 布防时段（`defense_schedule`）不在此处重复判断——事件能产生告警即已过布防，LLM 规则跟随任务布防语义。

### 5.3 投递消息结构（Kafka `iot-alert-llm-judge`）

```json
{
  "correlation_id": "uuid",
  "alert_id": 123,
  "task_id": 7,
  "device_id": "34020000001320000001",
  "rule_id": 11,
  "agent_id": 3,
  "model_id": 1,
  "judge_mode": "video",
  "media": {
    "image_url": "http://minio:9000/api/v1/buckets/.../download?...",  // image 模式
    "record_path": "http://minio:9000/api/v1/buckets/.../download?...", // video 模式（MinIO 下载路径）
    "event_time": "2026-09-01T10:15:30Z",
    "pre_seconds": 5,
    "post_seconds": 10,
    "max_seconds": 30
  },
  "prompt_override": null,
  "require_json": true,
  "fail_policy": "skip",
  "gated": true,
  "notify_payload": { "channels": [...], "notify_users": [...], "task_name": "..." },
  "timestamp": 1725171330000
}
```

> `notify_payload` 携带 `enrichNotificationFromVideoDb` 已补齐的通知配置，门控模式下 confirm 后补发通知无需再查库。投递时 `msg.getShouldNotify()!=true` 或通道为空则 `gated` 字段置 false（无通知可门控，仅回写）。

## 6. 判断方式：图片 / 视频（时长窗口）

### 6.1 图片（`judge_mode=image`）

- 媒体源：`alert.image_url`（iot-sink 落库时已上传 MinIO）优先；无 URL 时降级 `alert.image_path`。
- AI 侧 `invoke_vision` 需要 base64：AI 内部接口从 MinIO 下载（`minio_proxy.py` 已有下载模式）或直传 URL 由模型服务拉取；实现上优先**直传 URL**（省一次传输），`invoke_vision` 因协议需要 base64 时由 AI 侧下载转码（图片通常 <1MB，可接受）。

### 6.2 视频（`judge_mode=video`）

- 媒体源：`alert.record_path`（MinIO 录像下载路径）优先；缺失时由 AI 内部接口回退调用 VIDEO 的 `record_video_service.find_segment_for_alert`（`VIDEO/app/services/record_video_service.py`）按告警时间定位片段。
- **时长窗口（"视频流时长长短"配置）**：AI 内部接口按 `event_time ± pre/post_seconds` 用 ffmpeg 从源录像切片生成临时 mp4（存 MinIO `llm-judge/` 前缀或本地 tmp，7 天清理），切片时长受 `video_max_seconds` 上限保护；再调 `invoke_video(video_url=切片URL, ...)`。
- 切片失败（源不存在/损坏）按 `fail_policy` 降级；`pre_seconds=0` 且 `post_seconds=0` 时回退 `image` 模式（用事件图研判），避免视频模式空跑。

### 6.3 智能体（agent）组装

AI 内部接口按 `agent_id` 取 `rag_expert`：`system_prompt` 作为系统提示词；其 `knowledge_sets` 关联的知识集做 RAG 检索（复用 `AI/app/services/rag_service.py` 的检索），将 Top-K 片段拼入上下文；`model_id` 取 `llm_config`（NULL 用全局激活模型，`llm.py:get_active_model`）。研判提示词模板（默认，可被 `prompt_override` 覆盖）：

```
你是{expert_name}，负责对算法告警事件进行二次研判。
检测信息：{object}/{event}，检测框信息：{detections_json}
请基于提供的{图片|视频}判断该事件是否真实成立。
仅输出 JSON：{"confirm": true|false, "confidence": 0~1, "reason": "简要理由", "attributes": {...}}
```

`require_json=true` 时对模型输出做 JSON 解析（含 ```json 围栏剥离），解析失败重试一次 `invoke_chat` 纠错，仍失败按 `fail_policy` 处理并在 `structured` 里保留原文。

## 7. 二次判断语义与通知门控

| 模式 | `secondary_judge` | 落库 | 通知 | LLM 结论 |
| --- | --- | --- | --- | --- |
| A 后置增强（默认） | false | 立即，`llm_judge_status` 不写 pending | 立即发送（现状不变） | 异步回写 `information.llm` + 更新状态列，不改通知结果 |
| B 二次判断（门控） | true | 立即，`llm_judge_status='pending'` | **延迟**：等待 LLM 结论 | `confirm` → 更新状态 + 用 `notify_payload` 补发 `iot-alert-notification-send`；`reject` → 更新状态 + 回写抑制原因，不发通知；`error/skip` → 按 `fail_policy`：`skip` 补发通知（视同通过）或 `reject` 不发 |

状态机：`pending → confirmed / rejected / error / skipped`。门控模式下通知延迟的上限由 LLM 超时链保证（AI 内部接口超时 = `model.timeout * 2`，视频 `* 3`，再加消费者处理余量），建议 AI 内部接口总超时不超过 120s；超出则按 `fail_policy` 兜底并记 `error`。

## 8. 性能与可靠性保障

| 关注点 | 措施 |
| --- | --- |
| 主链路零影响 | 匹配+投递在告警线程内仅做一次内存判断与 Kafka send（异步 fire-and-forget，失败仅日志）；LLM 调用、媒体切片、RAG 检索全部在独立消费者线程 |
| 独立队列 | 新 topic `iot-alert-llm-judge`、独立 group、`concurrency=2~4`（KafkaConfig 中独立 containerFactory 或独立 properties，不复用告警消费者并发 16） |
| 背压 | LLM 是慢下游：消费者并发数、`max-poll-records`（建议 50）、`max.poll.interval.ms`（建议 ≥300000，与 LLM 超时匹配）独立配置；`video_max_seconds` 限制媒体体积 |
| 失败重试 | 消费异常指数退避重投（`RetryTemplate` 3 次，退避 1s/5s/15s），超限进 DLT `iot-alert-llm-judge-dlt` 人工复盘 |
| 幂等去重 | `correlation_id` 唯一键：投递前查重（`algorithm_llm_judge_result`），回写前查重，重复消息直接 ack |
| 限流 | 规则级 `min_interval_sec`（Redis）；可选模型级 QPS 限流（`llm_config` 无此字段则暂按规则节流） |
| 降级 | `fail_policy` 三态；AI 内部接口不可达 → 重试耗尽 → 按 `fail_policy` + `llm_judge_status='error'`，门控模式不因 LLM 故障造成漏报（`skip` 默认放行通知） |
| 配置热更新 | 规则表变更由 VIDEO 推送（新增 `llm_rule_revision` 或复用 `template_revision` 语义），iot-sink 本地缓存规则（Caffeine，TTL 60s 兜底），避免每事件查库 |
| 消息体积 | 媒体引用走 URL 而非二进制，队列消息 <10KB |

## 9. 各模块改造清单

### 9.1 VIDEO（Python，配置与媒体）

- `models.py`：`AlgorithmTask` 加 `llm_post_process_enabled` 列；新增 `AlgorithmTaskLlmRule`、`AlgorithmLlmJudgeResult` 模型；`ensure_algorithm_task_llm_columns` / `ensure_algorithm_llm_tables` 迁移函数（参照 `ensure_algorithm_task_post_process_columns` `models.py:2938`）。
- `app/services/`：新增 `algorithm_task_llm_rule_service.py`（CRUD + 规则缓存失效推送）；`algorithm_task_service.py` 的 `to_dict`/`update` 透传 `llm_post_process_enabled` 与 `llm_rules`。
- `app/blueprints/algorithm_task.py`：任务详情接口返回规则列表；新增 `llm_rule_bp`（前缀 `/algorithm_task/{task_id}/llm_rules`，POST/PUT/DELETE）。
- 视频窗口切片归属 AI 侧，VIDEO 仅需提供 `record_path`（已具备）；如 `record_path` 缺失需按事件时间定位录像时，复用 `record_video_service.find_segment_for_alert`。

### 9.2 iot-sink（Java，匹配/投递/执行/回写）

| 新增/修改 | 文件（`iot-sink-biz/.../`） | 内容 |
| --- | --- | --- |
| 修改 | `protocol/emqx/router/IotAlgoBusMqttHandler.java` | `handleAlert` 通知发送前判断门控（`isGated`）并跳过转发；落库后调用 `tryEnqueue` |
| 修改 | `consumer/AlertNotificationConsumer.java`、`SnapshotAlertConsumer.java` | 同上两处扩展点（Kafka 链路） |
| 修改 | `service/impl/AlertServiceImpl.java` | `processAlert/processSnapshotAlert` 落库成功后调 `llmJudgeEnricher.tryEnqueue(msg, alertId)`；门控落库时写 `llm_judge_status='pending'` |
| 新增 | `service/LlmJudgeEnricher.java` + `service/impl/LlmJudgeEnricherImpl.java` | 规则缓存（Caffeine）、规则匹配、节流（Redis）、Kafka 投递（`iotKafkaTemplate`） |
| 新增 | `domain/model/LlmJudgeRequestMessage.java` | 队列消息模型（见 5.3） |
| 新增 | `consumer/AlertLlmJudgeConsumer.java` | `@KafkaListener(topic=iot-alert-llm-judge, group=iot-sink-llm-judge, containerFactory=iotLlmJudgeKafkaListenerContainerFactory)`，`ack=manual_immediate`，重试/退避/DLT |
| 新增 | `service/LlmJudgeService.java` + `service/impl/LlmJudgeServiceImpl.java` | 调 AI 内部接口（Hutool `HttpUtil`，超时可配）；结果回写：落 `algorithm_llm_judge_result`（correlation_id 查重）、更新 `alert.llm_judge_status/llm_judge_detail`、合并 `information.llm`；门控 confirm → 用 `notify_payload` 发 `iot-alert-notification-send` |
| 修改 | `messagebus/config/KafkaConfig.java` + `application.yaml` | 新增 `iotLlmJudgeKafkaListenerContainerFactory`（concurrency 2~4、max-poll-records 50、max.poll.interval 300s、DLT）；`llm-judge` 配置段（topic/group/ai-base-url/超时/开关） |

### 9.3 AI（Python，研判内部接口）

- 新增 `app/blueprints/llm_internal.py`（前缀 `/model/llm/internal`，注册进 `AI/run.py:366` 附近）：
  - `POST /model/llm/internal/judge`：入参 = 5.3 消息的 `media` + `agent_id`/`model_id`/`prompt_override`/`require_json`；流程：取智能体 → 组装 system_prompt → RAG 检索拼上下文（可选）→ image：下载/转 base64 → `invoke_vision`；video：ffmpeg 切片（`video_max_seconds` 上限）→ `invoke_video` → JSON 解析与纠错 → 返回 `{confirm, confidence, reason, structured, usage, duration_ms}`。
  - 内部鉴权：内网网段 + 可选共享 token 头（`X-Internal-Token`），不开放公网。
- 切片工具：`app/services/llm_video_clip_service.py`（ffmpeg 命令封装 + 临时文件/对象存储清理）。
- 复用：`llm_gateway_client.invoke_vision/invoke_video`、`rag_service` 检索、`llm.py:get_active_model`。

### 9.4 WEB 前端

- 算法任务"编辑/详情"新增 **大模型后处理** 区块/Tab：总开关、规则列表（匹配对象、智能体下拉（`/model/rag` 专家列表）、判断方式（图片/视频）、视频前/后窗口秒数、最大时长、二次判断开关、失败策略、提示词覆盖）。
- 告警详情页 `information.llm` 渲染研判结论（确认/置信度/理由），`llm_judge_status` 展示状态徽标。

## 10. 配置项（iot-sink application.yaml 新增段）

```yaml
spring:
  kafka:
    llm-judge:
      request-topic: iot-alert-llm-judge
      dlt-topic: iot-alert-llm-judge-dlt
      group-id: iot-sink-llm-judge
      concurrency: 3
      max-poll-records: 50
      max-poll-interval-ms: 300000
      retry-max-attempts: 3
      retry-backoff-ms: [1000, 5000, 15000]
llm-judge:
  enabled: true                 # 全局总开关（灰度/紧急止血）
  ai-internal-base-url: http://ai-service:8081
  ai-internal-token: ${AI_INTERNAL_TOKEN:}
  judge-timeout-ms: 120000      # AI 内部接口超时
  rule-cache-ttl-sec: 60
  redis-dedup-ttl-sec: 86400
```

> 注：实现采用"消费者直接回写"（研判完成由 iot-sink 写 VIDEO 库并门控补发通知），
> 不发布结果 topic，故不再需要 `result-topic` 配置。

## 11. 监控与可观测性

- 指标（Micrometer/Prometheus）：`llm_judge_enqueued_total`、`llm_judge_success_total`、`llm_judge_error_total`、`llm_judge_duration_ms`（histogram）、`llm_judge_queue_depth`（Kafka lag）、门控模式 `llm_judge_gated_notify_delay_ms`。
- 日志：`correlation_id` 贯穿投递→研判→回写（MDC），与告警链路日志可串联排查。
- 告警规则：LLM 研判 error 率 > 5% / 队列 lag > 1000 / 门控超时未回写（pending 超过 5 分钟）触发平台告警。
- 数据面：`algorithm_llm_judge_result` 支持按任务/设备/智能体查询研判记录，便于复盘误报/漏报与提示词调优。

## 12. 实施步骤与里程碑

| 阶段 | 内容 | 验收 |
| --- | --- | --- |
| M1 配置面 | VIDEO 建表/模型/API + WEB 配置 Tab | 能保存任务级开关与规则 |
| M2 研判面 | AI 内部 `/model/llm/internal/judge`（图片+视频+RAG+JSON 输出） | curl 单测图片/视频研判通过 |
| M3 队列面 | iot-sink 新消费者 + LlmJudgeService + 回写（模式 A 先行） | 模拟告警 → 结论回写 `information.llm`，主链路延迟无变化 |
| M4 门控面 | 规则匹配投递 + 门控通知 + fail_policy + DLT/监控 | 模式 B 端到端：confirm 补发 / reject 抑制 |
| M5 加固 | 压测（LLM 命中/未命中对比主链路 P95 延迟）、幂等/重试/降级演练、监控告警上线 | 压测报告 + 演练记录 |

## 13. 风险与兼容性

- **兼容性**：所有新表/新列均走 `ensure` 迁移与 `CREATE TABLE IF NOT EXISTS`，老版本 VIDEO/iot-sink 升级无破坏；`llm_post_process_enabled` 默认 false，行为与现状完全一致。
- **LLM 延迟不可控**：靠独立队列 + 门控超时兜底 + `fail_policy` 三态消化，杜绝拖垮主链路。
- **媒体获取失败**（录像缺失/MinIO 不可用）：视频模式回退图片模式或按 `fail_policy` 处理，不产生脏研判。
- **成本**：LLM 调用按事件计费，`min_interval_sec` 节流 + `alert_event_suppress_time` 既有抑制 + 规则 `match_objects` 收窄，控制调用量。
- **误判风险**：`secondary_judge=true` 的 reject 会抑制通知，提供 `fail_policy` 与审计表，投产前建议先在模式 A 下观察研判准确率再开启门控。
