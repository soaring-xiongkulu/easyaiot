# POST 模块详细设计（可落地）

| 项目 | 说明 |
|------|------|
| 文档版本 | **v1.0** |
| 状态 | **可落地设计**（按本文即可开工实现与联调） |
| 实现语言 | **Go** |
| 仓库目录 | `POST/` |
| 关联专项 | [区域检测后处理设计](./区域检测后处理设计.md)（`region_gate` 插件细则） |
| 硬约束 | 只做 `InferEvent→AlertFinal`；集群无状态；**不引入 Redis**；几何唯一实现在 POST |

本文面向实现：契约字段、目录、接口、配置 API、环境变量、迁移步骤、验收用例均给出可执行约定。

---

## 1. 目标与边界

### 1.1 一句话

`POST` 是 AI 事件面的唯一业务中枢：消费推理事件，按任务流水线执行后处理插件，产出最终告警消息。

### 1.2 做 / 不做

| 做 | 不做 |
|----|------|
| 类别过滤、区域门控、布防、决定是否告警 | 模型推理 / 拉流 / 画预览 OSD |
| 插件流水线执行与逐步调试 | Redis / 分布式状态 / 跨帧人流核心 |
| MQTT 进出；无状态多副本 | 替代 iot-sink 的设备协议网关 |
| 读 VIDEO 配置（区域/任务/pipeline） | 管理面 UI（由 WEB 做；本文定义 API） |
| Phase1 兼容现网告警 JSON 供 sink 落库 | Phase1 自建完整通知渠道发送 |

### 1.3 角色分工

| 组件 | 职责 |
|------|------|
| RUNTIME / Python Infer | 全图推理；冷却后发 `InferEvent`；**不算区域** |
| **POST** | 流水线后处理；出 `AlertFinal` |
| VIDEO | 区域/任务/pipeline CRUD；配置查询 API；配置变更通知 |
| WEB | 任务后处理开关与高级 pipeline 编辑；调试回放入口 |
| iot-sink | Phase1：信任 `post_version` 后只落库/MinIO/转发通知；最终取消 AI 判定 |

---

## 2. 端到端时序（落地主路径）

```text
Infer                         POST                         VIDEO              sink
  |                             |                            |                  |
  |-- MQTT InferEvent --------->|                            |                  |
  |                             |-- GET /internal/post/config/--->|             |
  |                             |   (cache miss)             |                  |
  |                             |<-- TaskConfig+Regions -----|                  |
  |                             |  pipeline run              |                  |
  |                             |-- MQTT AlertFinal (兼容包) ------------------>|
  |                             |                            |     若 post_version 存在：
  |                             |                            |     跳过布防，落库+MinIO
```

冷却：Infer 侧已有告警间隔，POST 不再做冷却状态。  
去重：sink/DB 对 `correlation_id` 做唯一或业务去重（Phase1 沿用现网能力；无则允许偶发重复，后续加唯一索引）。

---

## 3. 契约（必须按此实现）

### 3.1 Topic

| Topic | 方向 | QoS | 说明 |
|-------|------|-----|------|
| `mqtt/iot-infer-event` | Infer → POST | 1 | 主输入；共享订阅 `$share/post/mqtt/iot-infer-event` |
| `mqtt/iot-alert-final` | POST → sink/adapter | 1 | 最终告警（Phase1 可同时发兼容旧 topic，见 §3.5） |
| `mqtt/iot-post-config` | VIDEO → POST | 1 | 配置失效；payload 见 §3.6；可选 retained |
| `mqtt/iot-post-trace` | POST → 调试消费者 | 0 | 仅 `POST_DEBUG=1` 时发逐步 trace |

环境变量可覆盖 topic 名（见 §9）。

### 3.2 InferEvent（入参，schema=`infer_event.v1`）

```json
{
  "schema": "infer_event.v1",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_id": 100,
  "task_name": "东门实时检测",
  "task_type": "realtime",
  "device_id": "cam_001",
  "device_name": "东门枪机",
  "timestamp": "2026-08-21T18:00:00+08:00",
  "frame_number": 12345,
  "frame_width": 1920,
  "frame_height": 1080,
  "image_path": "/app/alert_images/cam_001/20260821/xxx.jpg",
  "detections": [
    {
      "bbox": [100.0, 200.0, 180.0, 360.0],
      "class_id": 0,
      "class_name": "person",
      "confidence": 0.92,
      "track_id": 7
    }
  ],
  "model_ids": [1],
  "hints": {
    "alert_class_names": ["person"]
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| schema | string | 是 | 固定 `infer_event.v1` |
| correlation_id | string | 是 | UUID；贯穿日志与落库 |
| task_id | int | 是 | 算法任务 ID |
| task_type | string | 是 | `realtime` / `snap` / `patrol`（snap 兼容 `snapshot`） |
| device_id | string | 是 | 设备 ID；区域按此加载 |
| device_name | string | 否 | 展示用 |
| timestamp | string | 是 | RFC3339；布防按时区解释 |
| frame_width/height | int | 是 | 与 bbox 同一坐标系；用于归一化区域缩放 |
| image_path | string | 建议 | 证据图；可空（则无图告警） |
| detections | array | 是 | 可空数组；空则通常 drop |
| detections[].bbox | [x1,y1,x2,y2] | 是 | **像素坐标** |
| detections[].class_name | string | 是 | 类别过滤用 |
| detections[].confidence | float | 是 | 0~1 |
| detections[].track_id | int | 否 | 默认 0 |
| model_ids | int[] | 否 | 供区域 model_ids 交集 |
| hints.alert_class_names | string[] | 否 | 可被任务配置覆盖；任务配置优先 |

**校验失败**：记日志 `invalid_infer_event`，不 panic；不发告警。

### 3.3 AlertFinal（出参逻辑模型，schema=`alert_final.v1`）

```json
{
  "schema": "alert_final.v1",
  "post_version": "1",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_id": 100,
  "task_name": "东门实时检测",
  "task_type": "realtime",
  "device_id": "cam_001",
  "device_name": "东门枪机",
  "region": "东门禁区",
  "object": "person",
  "event": "入侵",
  "time": "2026-08-21T18:00:00+08:00",
  "image_path": "/app/alert_images/cam_001/20260821/xxx.jpg",
  "detections": [ { "bbox": [100,200,180,360], "class_name": "person", "confidence": 0.92 } ],
  "information": {
    "post_version": "1",
    "gates_applied": ["alert_class", "region_gate", "defense_schedule"],
    "region_filter": "applied",
    "matched_regions": ["东门禁区"],
    "enrichment": {
      "region_gate": { "matched_region_ids": [12] }
    },
    "drop_trace": [],
    "task_type": "realtime"
  }
}
```

| 字段 | 说明 |
|------|------|
| post_version | 固定 `"1"`；sink 凭此跳过 AI 再判定 |
| region | 命中区域名；无区域配置时为 `全画面` |
| object | 默认取 detections[0].class_name 或拼接 |
| event | 来自任务配置 `alert_event`（或默认「检测告警」） |
| information.region_filter | `applied` / `bypass` / `disabled` |

### 3.4 Decision / Drop

插件或流水线可 `drop`，**不发** AlertFinal。

| drop_reason | 含义 |
|-------------|------|
| `empty_detections` | 输入或过滤后无框 |
| `class_filtered` | 类别过滤后为空 |
| `region_miss` | 均不在区域 |
| `defense_off` | 非布防时段 |
| `plugin_drop` | 某插件显式 drop |
| `gate_disabled` | 全局 POST 旁路且策略为不转发（少用） |

指标：`post_drop_total{reason=...}`。

### 3.5 Phase1 兼容现网 sink 的发布形态

为减少第一期改动量：POST 在逻辑上生成 AlertFinal，**发布时映射为现网 `AlertNotificationMessage` 可消费的扁平/嵌套 JSON**，并：

1. 写入 `information.post_version = "1"`  
2. 优先发 `mqtt/iot-alert-final`；同时可用开关 `POST_PUBLISH_LEGACY_ALERT=true` 再发 `mqtt/iot-alert-notification`（或 snapshot 对应 topic）  
3. sink 改造：若 `information.post_version` 或顶层 `post_version` 存在 → **跳过 `checkDefenseSchedule`**，其余落库逻辑不变  

映射字段：

| AlertFinal | 现网 |
|------------|------|
| device_id | deviceId / device_id |
| region | alert.region |
| object/event | alert.object / alert.event |
| image_path | alert.imagePath / image_path |
| information | alert.information |
| time | alert.time / timestamp |
| correlation_id | correlationId |
| task_id | taskId |

### 3.6 配置失效消息 `iot-post-config`

```json
{
  "schema": "post_config_invalidate.v1",
  "scope": "task",
  "task_id": 100,
  "device_id": "",
  "ts": "2026-08-21T18:01:00+08:00"
}
```

| scope | 行为 |
|-------|------|
| `task` | 清 task_id 配置缓存 |
| `device` | 清该 device 区域缓存 |
| `all` | 清全部缓存 |

---

## 4. 流水线与插件（可实现算法）

### 4.1 默认流水线

任务未配置 `pipeline` 时：

```json
[
  {"plugin": "alert_class", "enabled": true, "params": {}},
  {"plugin": "region_gate", "enabled": true, "params": {"hit_mode": "center"}},
  {"plugin": "defense_schedule", "enabled": true, "params": {}},
  {"plugin": "default_alert_decide", "enabled": true, "params": {}}
]
```

### 4.2 Go 接口（必须按此实现）

```go
package pipeline

type Decision string
const (
    DecisionContinue Decision = "continue"
    DecisionDrop     Decision = "drop"
    DecisionAlert    Decision = "alert"
)

type PluginKind string
const (
    KindFilter PluginKind = "filter"
    KindEnrich PluginKind = "enrich"
    KindRender PluginKind = "render"
    KindDecide PluginKind = "decide"
)

type Plugin interface {
    Name() string
    Kinds() []PluginKind
    Process(ctx *Context) (PluginDelta, error)
}

type Context struct {
    Event        contract.InferEvent
    Task         config.TaskConfig
    Regions      []config.Region
    Detections   []contract.Detection
    Enrichment   map[string]any
    Layers       []contract.DrawLayer
    Decision     Decision
    DropReason   string
    PluginParams map[string]any
    Trace        []StepTrace // POST_DEBUG 时填充
}

type PluginDelta struct {
    Detections      *[]contract.Detection
    EnrichmentPatch map[string]any
    LayersAppend    []contract.DrawLayer
    Decision        *Decision
    DropReason      string
    SkipRest        bool
}

type StepTrace struct {
    Plugin         string `json:"plugin"`
    DetectionsIn   int    `json:"detections_in"`
    DetectionsOut  int    `json:"detections_out"`
    Decision       string `json:"decision"`
    DropReason     string `json:"drop_reason,omitempty"`
    EnrichmentPatch map[string]any `json:"enrichment_patch,omitempty"`
    LatencyMs      float64 `json:"latency_ms"`
}
```

### 4.3 流水线执行伪代码（内核）

```text
func Run(event, taskCfg, regions):
  ctx = Context{Event: event, Task: taskCfg, Regions: regions,
                Detections: copy(event.Detections), Decision: continue,
                Enrichment: {}}
  for step in taskCfg.Pipeline where step.Enabled:
      p = Registry[step.Plugin]
      if p == nil: log unknown_plugin; continue
      ctx.PluginParams = step.Params
      in = len(ctx.Detections)
      t0 = now()
      delta, err = p.Process(ctx)
      if err != nil: log plugin_error; Decision=drop; DropReason=plugin_error; break
      apply(delta)  // 合并 detections/enrichment/layers/decision
      trace append
      if ctx.Decision == drop: break
      if delta.SkipRest: break
  if ctx.Decision == drop OR len(detections)==0: return Dropped
  return BuildAlertFinal(ctx)
```

`apply` 规则：

- `Detections != nil` → 替换  
- `EnrichmentPatch` → `Enrichment[pluginName] = patch`（命名空间隔离）  
- `LayersAppend` → append  
- `Decision != nil` → 覆盖  

### 4.4 内置插件规格

#### 4.4.1 `alert_class`（filter）

- 输入：`Task.AlertClassNames`；若空则用 `Event.Hints.AlertClassNames`；仍空 → 不过滤。  
- 行为：保留 `class_name` 在允许集合内的 detections（大小写敏感与 VIDEO `alert_class_filter` 对齐：建议 **大小写不敏感** trim）。  
- 出参：过滤后列表；若空 → `drop` + `class_filtered`。

#### 4.4.2 `region_gate`（filter）——唯一几何实现

- 加载：`Regions` = 该 `device_id` 且 `is_enabled=true`，`region_type in (polygon, rectangle)`，点数 ≥ 3。  
- `model_ids`：区域 `model_ids` 非空时，与 `Event.model_ids`∪`Task.model_ids` 无交集则跳过该区域。  
- 命中：`hit_mode=center`（默认）→ bbox 中心点；`any_corner` → 任一角点。  
- 坐标：points 支持 `[{x,y}]` / `[[x,y]]`；若均在 [0,1] 则 × frame_width/height。  
- 点在多边形内：射线法（含边界算命中）。  
- 无启用区域：`region_filter=bypass`，region=`全画面`，detections 不变。  
- 有区域但无一命中：drop `region_miss`。  
- 多区域命中：取 `sort_order` 最小者写入 region；全部名称进 `matched_regions`。  
- **line 类型**：本期跳过（不参与），日志 `skip_line_region`。

#### 4.4.3 `defense_schedule`（filter）

- 读 `Task.DefenseMode`：`full` → 直接通过。  
- `custom`：解析 `DefenseSchedule` 为 7×24 布尔（与现网一致）；时区 **Asia/Shanghai**；用 `Event.timestamp` 换算 weekday+hour。  
- 不在布防：drop `defense_off`。  
- schedule 空且非 full：与现网对齐——视为通过或拒绝？**落地约定：与 `AlertServiceImpl` 当前行为一致**（实现前对照该函数；建议写单测锁定）。  

#### 4.4.4 `default_alert_decide`（decide）

- 若 Decision 已 drop → 保持。  
- 若 detections 为空 → drop `empty_detections`。  
- 否则 Decision=`alert`；组装 object/event/region。

#### 4.4.5 `region_overlay`（render，Phase 可选）

- 仅追加 DrawLayer；Phase1 可不实现合成，只留接口。

#### 4.4.6 `user_script`（enrich，Phase2）

- HTTP POST 到 `USER_SCRIPT_URL`，body=Context JSON 子集，timeout 可配（默认 2s）。  
- 响应必须可解析为 PluginDelta；失败 → 可配置 `fail_open`（跳过）或 `fail_closed`（drop）。默认 **fail_open** 打错误日志。

### 4.5 插件注册表

```go
var Registry = map[string]Plugin{
  "alert_class":          AlertClass{},
  "region_gate":          RegionGate{},
  "defense_schedule":     DefenseSchedule{},
  "default_alert_decide": DefaultDecide{},
  // "region_overlay":    RegionOverlay{},
  // "user_script":       UserScript{},
}
```

未知 plugin id：跳过并 metric `unknown_plugin`，不中断整链（避免配错导致全挂）；也可配置严格模式。

---

## 5. 配置面（VIDEO API，必须提供）

### 5.1 POST 拉取配置

`GET /video/internal/post/config?task_id={id}&device_id={id}`

（网关前缀按现网：`/admin-api/video/...` 或内网直连 VIDEO；用 env `VIDEO_BASE_URL`）

响应：

```json
{
  "task": {
    "id": 100,
    "task_name": "东门实时检测",
    "task_type": "realtime",
    "alert_event": "入侵",
    "alert_class_names": ["person"],
    "defense_mode": "custom",
    "defense_schedule": [[true,true,...], ...],
    "model_ids": [1],
    "pipeline": [ {"plugin":"alert_class","enabled":true,"params":{}}, ... ],
    "post_process_enabled": false,
    "post_process_script": "post_process.py",
    "alert_notification_config": {}
  },
  "regions": [
    {
      "id": 12,
      "device_id": "cam_001",
      "region_name": "东门禁区",
      "region_type": "polygon",
      "points": [{"x":0.1,"y":0.2},{"x":0.5,"y":0.2},{"x":0.5,"y":0.8},{"x":0.1,"y":0.8}],
      "is_enabled": true,
      "sort_order": 0,
      "model_ids": []
    }
  ]
}
```

鉴权：内网 token 或 mTLS；env `VIDEO_INTERNAL_TOKEN`。

### 5.2 缓存

- key：`task:{id}`、`regions:{device_id}`  
- TTL 默认 30s（`CONFIG_CACHE_TTL_SEC`）  
- 收到 `iot-post-config` 立即失效对应 key  
- 进程内存即可；重启丢缓存安全  

### 5.3 DB 增量（VIDEO）

`algorithm_task` 增加列（若不存在）：

```sql
ALTER TABLE algorithm_task
  ADD COLUMN IF NOT EXISTS post_pipeline TEXT NULL;
-- JSON：pipeline 数组；NULL 表示使用默认流水线
```

区域表继续用 `device_detection_region`，不改表结构；points 读写兼容两种格式。

配置变更时（区域 CRUD、任务更新 pipeline/布防/标签）VIDEO 发布 `mqtt/iot-post-config`。

### 5.4 管理平台（WEB）最小能力

Phase1：

- 任务页展示「后处理由 POST 执行」说明  
- 区域/标签/布防沿用现 UI（即默认流水线三件套）  

Phase2：

- 「后处理流水线」高级面板：开关、排序、params  
- 「回放调试」：粘贴/上传 InferEvent → 调 POST `POST /debug/pipeline` → 展示 StepTrace  

---

## 6. 仓库与代码结构（Go）

```text
POST/
  go.mod
  README.md
  schemas/
    infer_event.v1.json
    alert_final.v1.json
    post_config_invalidate.v1.json
  cmd/post/main.go
  cmd/post-replay/main.go          # CLI：post-replay event.json
  internal/
    contract/                      # structs + validate
    pipeline/                      # Run + apply + registry
    plugin/
      alert_class.go
      region_gate.go               # 含 normalize points + ray casting
      defense_schedule.go
      decide.go
      region_gate_test.go          # 黄金用例
      defense_schedule_test.go
    config/
      client.go                   # HTTP 拉 VIDEO
      cache.go
    mqtt/
      subscriber.go
      publisher.go
    maplegacy/
      alert_notification.go       # AlertFinal → 现网告警 JSON
    debug/
      http.go                     # /debug/pipeline /debug/plugin
    metrics/
      metrics.go
    health/
      health.go                   # /healthz /readyz
  deploy/
    Dockerfile
    docker-compose.post.yml
```

Go module path 建议：`easyaiot/post`（以仓库实际 module 规范为准）。

MQTT 库建议：`github.com/eclipse/paho.mqtt.golang`。

---

## 7. HTTP 调试 API（可落地）

监听 `POST_HTTP_ADDR` 默认 `:8089`。

### 7.1 `POST /debug/pipeline`

Request：

```json
{
  "event": { /* InferEvent */ },
  "pipeline_override": null,
  "until_plugin": ""
}
```

Response：

```json
{
  "result": "alert",
  "drop_reason": "",
  "trace": [ /* StepTrace */ ],
  "alert_final": { /* or null */ }
}
```

### 7.2 `POST /debug/plugin`

```json
{ "plugin": "region_gate", "event": {...}, "params": {"hit_mode":"center"} }
```

返回单步 Delta + 处理后 detections。

### 7.3 安全

生产默认 `POST_DEBUG_HTTP=false`；仅内网或 debug 打开。

CLI：`post-replay ./event.json` 等价调用本地 pipeline（可进程内不经 HTTP）。

---

## 8. 指标与日志

### 8.1 Metrics（Prometheus 文本或 /metrics）

| 指标 | 类型 | 标签 |
|------|------|------|
| post_infer_total | counter | |
| post_alert_total | counter | |
| post_drop_total | counter | reason |
| post_plugin_latency_ms | histogram | plugin |
| post_config_fetch_error_total | counter | |
| post_mqtt_publish_error_total | counter | |

### 8.2 日志字段（强制）

每条处理：`correlation_id`, `task_id`, `device_id`, `instance_id`, `result=alert|drop`, `drop_reason`, `detections_in`, `detections_out`。

Debug 逐步：再加 `plugin`, `latency_ms`。

---

## 9. 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `MQTT_BROKER` | `tcp://emqx:1883` | |
| `MQTT_USERNAME` / `MQTT_PASSWORD` | 空 | |
| `MQTT_CLIENT_ID_PREFIX` | `post` | 实际 id=`prefix-hostname-pid` |
| `MQTT_SHARE_GROUP` | `post` | `$share/{group}/...` |
| `TOPIC_INFER_EVENT` | `mqtt/iot-infer-event` | |
| `TOPIC_ALERT_FINAL` | `mqtt/iot-alert-final` | |
| `TOPIC_LEGACY_ALERT` | `mqtt/iot-alert-notification` | |
| `TOPIC_CONFIG` | `mqtt/iot-post-config` | |
| `POST_PUBLISH_LEGACY_ALERT` | `true` | Phase1 兼容 |
| `VIDEO_BASE_URL` | `http://video:5000` | |
| `VIDEO_INTERNAL_TOKEN` | 空 | |
| `CONFIG_CACHE_TTL_SEC` | `30` | |
| `POST_HTTP_ADDR` | `:8089` | |
| `POST_DEBUG` | `false` | trace |
| `POST_DEBUG_HTTP` | `false` | 打开 /debug/* |
| `TZ` | `Asia/Shanghai` | 布防 |
| `POST_ENABLED` | `true` | false 时只消费不应答（或按策略透传，默认丢弃并打点） |

---

## 10. 部署

### 10.1 Dockerfile 要点

- 多阶段：`golang:1.22` build → `gcr.io/distroless/static` 或 alpine  
- 二进制 `/usr/local/bin/post`  
- 只读挂载告警图目录（若 overlay 需要；Phase1 可只传 path 不读图）  

### 10.2 compose 片段

```yaml
post:
  image: easyaiot/post:1.0.0
  replicas: 2   # swarm/k8s；compose 可用 scale
  environment:
    MQTT_BROKER: tcp://emqx:1883
    VIDEO_BASE_URL: http://video:5000
    POST_PUBLISH_LEGACY_ALERT: "true"
  volumes:
    - alert_images:/app/alert_images:ro
  depends_on:
    - emqx
```

k8s：Deployment + 就绪探针 `GET /readyz`（MQTT 已连接）。

### 10.3 各 Profile

| Profile | replicas | 说明 |
|---------|----------|------|
| standard/full | ≥2 | 共享订阅 |
| mini/edge | 1 | 同二进制 |
| cluster | ≥2 | 与调度无关，只扩 POST |

---

## 11. 迁移步骤（按 PR 拆分）

### PR-A：契约与 VIDEO 配置 API

1. 增加 `schemas/*.json`  
2. VIDEO：`GET /internal/post/config`  
3. `algorithm_task.post_pipeline` 列  
4. 区域/任务更新时发 `iot-post-config`  

### PR-B：POST 骨架 + 三插件 + replay

1. `POST/` Go module  
2. region_gate / alert_class / defense + 单测黄金集  
3. MQTT 消费/发布 + legacy 映射  
4. `/debug/pipeline`、`post-replay`  

### PR-C：Infer 切流（开关）

1. Python：`POST_ENABLED` 时发 InferEvent，不直接最终告警  
2. RUNTIME：删告警 ROI；发 InferEvent（MQTT）  
3. 文档：回滚开关  

### PR-D：sink 信任 post_version

1. `AlertServiceImpl`：有 `post_version` 跳过布防  
2. 确认通知 enrichment 过渡策略（Phase1 仍可 sink 补通知配置）  

### PR-E：WEB 说明与（可选）流水线编辑 / 回放 UI  

### PR-F：收紧

1. 关 `POST_PUBLISH_LEGACY_ALERT` 仅 `alert-final`  
2. sink 取消算法判定与后处理编排  
3. 删除 RUNTIME 区域告警代码  

---

## 12. Infer 侧改造要点（可对照改代码）

### 12.1 Python

在现 `try_send_alert_*` 前：

```text
if os.getenv("POST_ENABLED") == "true":
    publish_infer_event(...)  # 新函数，topic mqtt/iot-infer-event
    return
# else 旧路径
```

`publish_infer_event` 字段必须满足 §3.2；bbox 像素；带 frame 宽高。

### 12.2 RUNTIME

1. 告警路径去掉 `_isInAlarmRegion` / `pointInRegions` 对 alarmDetections 的过滤（OSD 可暂留或改为只画全量框）。  
2. `_sendAlarmCallback` 改为组 InferEvent JSON，publish `mqtt/iot-infer-event`（或 HTTP 旁路仅调试）。  
3. ini 的 `[regions]` **不再作为告警依据**（可删或仅文档标明废弃）。  

---

## 13. 测试用例（验收必须过）

### 13.1 region_gate 单测

| ID | 输入 | 期望 |
|----|------|------|
| R1 | 无区域 | bypass，全画面，框不变 |
| R2 | 方形区域，中心在内 | keep，region=名 |
| R3 | 中心在外 | drop region_miss |
| R4 | points 为 `{x,y}` | 与 `[[x,y]]` 同结果 |
| R5 | 归一化点 + frame 1920x1080 | 缩放正确 |
| R6 | 两区域都命中 | 取 sort_order 较小 |
| R7 | 区域 model_ids 无交集 | 该区域不参与 |
| R8 | 双设备区域数据误传入 | 只使用 Context.Regions（调用方按 device 过滤） |

### 13.2 流水线

| ID | 场景 | 期望 |
|----|------|------|
| P1 | 默认链，区内 person | alert |
| P2 | 区外 | drop |
| P3 | 区内但类别不匹配 | drop class_filtered |
| P4 | 区内类别对但非布防 | drop defense_off |
| P5 | replay 逐步 trace 长度=启用插件数 | 一致 |

### 13.3 集成

| ID | 场景 | 期望 |
|----|------|------|
| I1 | POST×2 副本，杀 1 个 | 仍有告警 |
| I2 | 改区域后发 config invalidate | 新事件用新区域 |
| I3 | sink 收带 post_version 的告警 | 落库且不再布防二次拒绝 |

---

## 14. 管理平台如何管不同插件（落地产品语义）

| 用户可见开关 | 映射到 pipeline |
|--------------|-----------------|
| 告警标签（已有配置即启用过滤） | `alert_class` enabled |
| 设备有启用区域 | `region_gate` enabled（无区域时插件仍跑但 bypass） |
| 布防非 full | `defense_schedule` enabled |
| 用户脚本开关 | `user_script` |
| 高级：拖拽排序 | 写 `post_pipeline` JSON |

普通用户不接触 JSON；高级面板编辑 `post_pipeline`。

调试：任务工具页调用 POST `/debug/pipeline`，展示每步 in/out/drop_reason。

---

## 15. 风险与回滚

| 风险 | 回滚 |
|------|------|
| POST 异常无告警 | `POST_ENABLED=false` Infer 走旧路径 |
| 区域误杀告警 | 任务关 region_gate 或清区域；replay 定位 |
| sink 双过滤 | 确认 post_version 短路已上 |
| 配置 API 挂 | 缓存 TTL 内仍可用；过期后 drop 并打 `config_fetch_error`（也可 fail_open 仅类别，**默认 fail_closed 不发告警防误报**） |

---

## 16. Phase1 完成定义（DoD）

1. `POST/` 可编译镜像，replicas≥2 共享订阅消费。  
2. 默认流水线四插件行为符合 §4.4 + §13 单测。  
3. Python 或 RUNTIME 至少一条链路 `POST_ENABLED=true` 发 InferEvent，区内告警区外不告警。  
4. 落库告警含正确 `region`，`information.post_version=1`。  
5. `post-replay` / `/debug/pipeline` 可逐步看到插件结果。  
6. 无 Redis 依赖；文档与 compose 可按 §10 部署。  

---

## 17. 实现顺序清单（开发任务拆解）

1. [ ] 写 `schemas/*.json` 与 Go `contract` + Validate  
2. [ ] 实现 `region_gate` + 单测 R1–R8  
3. [ ] 实现 `alert_class`、`defense_schedule`、`decide`  
4. [ ] 实现 `pipeline.Run` + StepTrace  
5. [ ] VIDEO `GET /internal/post/config` + cache client  
6. [ ] MQTT sub/pub + legacy mapper  
7. [ ] health/metrics/debug HTTP + post-replay  
8. [ ] Dockerfile + compose  
9. [ ] Infer 开关切流  
10. [ ] sink 信任 post_version  
11. [ ] 联调验收 §13 / §16  

按此清单即可分工开工，无需再补「方向性」设计。
