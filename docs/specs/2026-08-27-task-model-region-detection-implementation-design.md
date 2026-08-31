# 算法任务级多模型区域检测开发实施设计

## 1. 文档状态

- 状态：已批准方案的实施设计。
- 日期：2026-08-27。
- 适用模块：`VIDEO`、`POST`、`RUNTIME`、`WEB`。
- 目标版本：在保持现有单视频流共享解码、多算法任务订阅和任务内多模型推理架构不变的前提下，实现任务级、模型级区域隔离和运行时热更新。

## 2. 已确认的核心决策

1. 区域归属于一个算法任务和一个设备，不再存在运行态的“设备全局区域”。
2. 单视频流继续由 `CameraSourceManager` 单次拉流、单次解码，通过共享帧环向多个算法任务提供同一帧。
3. 每个算法任务继续独立加载自己的模型列表；任务内多个模型对完整画面推理，不按区域裁剪输入图像。
4. 区域过滤统一由 `POST` 执行，推理服务只负责输出带有任务、设备和来源模型身份的检测结果。
5. 每个区域可配置：
   - `model_ids = NULL`：适用于该任务的全部模型；
   - `model_ids = [1, 2]`：只适用于指定模型。
6. 某个模型在当前任务、设备下没有适用区域时，该模型按全画面检测；存在适用区域时，检测目标命中任一区域才保留。
7. 多模型事件必须在每个 `detection` 上携带业务模型 ID，不能用事件级模型 ID 并集代替检测级归属。
8. 区域修改后只刷新所属任务的 POST 模板，不重启算法任务，不刷新同设备的其他任务。
9. 首期普通区域门禁支持 `polygon` 和 `rectangle`。`line` 继续由越线插件使用，不参与普通区域门禁。

## 3. 背景与当前实现

当前系统已经具备以下基础：

- `VIDEO/app/services/camera_source_manager.py` 按设备维护共享拉流和共享帧环。
- `VIDEO/app/utils/camera_source_client.py` 使用 `task_id` 订阅共享视频源，失败时可按配置降级到任务独立拉流。
- `VIDEO/services/realtime_algorithm_service/run_deploy.py` 在同一帧上依次执行任务内多个模型，并在 Python 检测结果上写入 `model_id`。
- `VIDEO/models.py` 的 `DeviceDetectionRegion` 已包含 `task_id`、`device_id` 和 `model_ids`。
- `POST/internal/plugin/region_gate.go` 已具备多边形几何判断和检测结果过滤能力。
- `POST` 已有任务模板缓存、HTTP 模板推送、MQTT 多副本同步和数据库启动预热能力。

现有实现仍存在影响目标功能的关键问题：

1. `VIDEO/app/services/post_template_client.py` 和 `POST/internal/template/store.go` 加载区域时只按设备过滤，可能把同设备其他任务的区域装入当前任务模板。
2. `POST/internal/contract/types.go` 的 `Detection` 没有接收 `model_id`，Python 已发送的检测级模型身份会在 Go 反序列化时丢失。
3. `POST/internal/plugin/regions.go` 使用事件模型与任务模型的并集筛选区域，无法判断单个检测结果来自哪个模型。
4. `RUNTIME/src/Detech.cpp` 生成 InferEvent 时没有为每个检测结果输出正确的业务模型 ID，且轨迹 ID 固定为 `0`。
5. 区域路由尝试调用 `refresh_running_tasks_for_task`，但当前模板客户端没有该函数，只能降级为按设备刷新多个任务。
6. 前端保存区域时默认写入空 `model_ids`，尚未提供“全部模型/指定模型”的明确交互。
7. `ALGO_BUS_TRANSPORT=http` 会关闭当前 MQTT InferEvent 通道，而启用 POST 时本地区域判断又会被跳过，存在区域过滤被整体绕过的风险。

## 4. 范围

### 4.1 本次范围

- 任务、设备、模型三个维度的区域配置和隔离。
- 同一摄像头被多个任务使用时，各任务独立绘制、保存和应用区域。
- 同一任务内多个模型使用全部模型区域或模型专属区域。
- 区域批量原子保存、并发编辑保护和 POST 模板热更新。
- Python 与 C++ InferEvent 检测级模型身份对齐。
- POST 数据库预热、HTTP 推送和多副本同步的一致性修复。
- 区域配置、事件契约、过滤结果和失败原因的测试与可观测性。
- 历史无 `task_id` 区域数据的安全迁移。

### 4.2 非目标

- 不改变现有 `CameraSourceManager` 共享拉流和共享帧协议。
- 不把多个算法任务合并成一个推理进程。
- 不共享不同任务的模型实例或推理结果。
- 不按区域裁剪图片后再推理，不引入分块推理或多 ROI 推理。
- 不在本期重新设计模型调度、GPU 分配和任务部署架构。
- 不在本期承诺补齐 C++ 轨迹算法；依赖轨迹的越线、进入离开和停留插件必须在执行器具备有效 `track_id` 时才能启用。

## 5. 术语和配置语义

| 名称 | 语义 |
|---|---|
| 任务区域 | 由 `task_id + device_id` 唯一确定归属范围的区域记录 |
| 全模型区域 | `model_ids IS NULL`，适用于任务当前和后续加入的全部模型 |
| 指定模型区域 | `model_ids` 为非空数组，只适用于数组中的业务模型 ID |
| 适用区域 | 对某个检测结果，任务、设备匹配且模型范围匹配的启用区域 |
| 业务模型 ID | `algorithm_task.model_ids` 中使用的模型 ID，不是推理线程池内部下标 |
| 模板版本 | `algorithm_task.template_revision`，用于拒绝乱序模板更新 |

空数组不作为持久化语义：请求中的 `model_ids: []` 在服务端规范化为数据库 `NULL`。API 响应额外返回 `model_scope`，避免前端依赖空数组猜测语义。

## 6. 目标架构与数据流

```text
摄像头 device-1
    │
    ▼
CameraSourceManager
单次拉流 / 单次解码 / SharedFrameRing
    │
    ├── Task A（task_id=A）
    │     ├── Model 1 ─┐
    │     └── Model 2 ─┴─► InferEvent(A, device-1, detections[].model_id)
    │                              │
    │                              ▼
    │                    POST Template A revision=N
    │                    只含 Task A + device-1 区域
    │                              │
    │                              ▼
    │                    按 detection.model_id 过滤
    │
    └── Task B（task_id=B）
          ├── Model 2 ─┐
          └── Model 3 ─┴─► InferEvent(B, device-1, detections[].model_id)
                                       │
                                       ▼
                             POST Template B revision=M
                             只含 Task B + device-1 区域
```

### 6.1 配置流

```text
WEB 区域编辑器
  → VIDEO 批量保存 API
  → 数据库事务：保存区域 + template_revision 加一
  → 事务提交
  → 仅向 POST 推送当前 task_id 的新模板
  → POST 按 revision 原子替换缓存
  → POST 多副本 MQTT 同步
```

### 6.2 事件流

```text
共享帧
  → 任务内各模型完整画面推理
  → 每个 detection 标注业务 model_id
  → 发布 InferEvent
  → POST 按 task_id 获取模板
  → 按 device_id 取设备区域
  → 对每个 detection 独立选择适用区域并判断命中
  → 输出过滤后的告警
```

区域配置不进入视频源管理层。视频源层只负责帧共享，因而增加任务区域不会产生额外拉流、解码或推理次数。

## 7. 数据模型设计

### 7.1 `device_detection_region`

保留现有表和 `model_ids TEXT`，避免为内存过滤引入无必要的 JSONB 迁移。服务端必须将 TEXT 规范化为合法 JSON 数组或 `NULL`。

目标约束：

| 字段 | 目标约束 | 说明 |
|---|---|---|
| `id` | 主键 | 区域 ID |
| `task_id` | `NOT NULL`、外键、级联删除 | 区域任务归属 |
| `device_id` | `NOT NULL`、外键、级联删除 | 区域设备归属 |
| `region_name` | `NOT NULL` | 同任务设备内允许重名，但前端应提示 |
| `region_type` | `polygon/rectangle/line` | 普通门禁忽略 `line` |
| `points` | `NOT NULL` | 归一化点数组 JSON |
| `model_ids` | nullable TEXT | `NULL` 为全部模型，非空 JSON 数组为指定模型 |
| `is_enabled` | `NOT NULL` | 是否进入模板 |
| `sort_order` | `NOT NULL` | 命中多个区域时决定主区域 |

新增启用区域查询索引：

```sql
CREATE INDEX IF NOT EXISTS idx_device_detection_region_task_device_enabled
ON device_detection_region (task_id, device_id, sort_order)
WHERE is_enabled = true;
```

### 7.2 `algorithm_task.template_revision`

新增：

```sql
ALTER TABLE algorithm_task
ADD COLUMN IF NOT EXISTS template_revision BIGINT NOT NULL DEFAULT 1;
```

以下变更必须在业务数据事务内将版本加一：

- 区域创建、更新、删除或批量替换；
- 任务模型列表变化；
- 任务设备列表变化；
- POST pipeline、脚本、启用状态变化；
- 任务启动或停止导致模板新增、删除。

版本使用数据库条件更新实现乐观锁，不使用进程内时间戳：

```sql
UPDATE algorithm_task
SET template_revision = template_revision + 1
WHERE id = :task_id
  AND template_revision = :expected_revision
RETURNING template_revision;
```

未返回记录表示其他客户端已经修改任务配置，API 返回 HTTP `409`。

### 7.3 历史数据迁移

迁移分两阶段执行，禁止直接把历史空 `task_id` 区域自动应用到所有任务。

阶段一：兼容清洗。

1. 将 `model_ids` 为 `''`、空白、`'[]'` 或非法 JSON 的记录规范化为 `NULL`；非法非空值同时记录迁移报告。
2. 对 `task_id IS NULL` 的区域，根据 `algorithm_task_device` 查询设备关联任务：
   - 恰好关联一个任务：自动补齐 `task_id`；
   - 没有关联任务：禁用并列入“无归属区域”报告；
   - 关联多个任务：禁用并列入“归属冲突区域”报告，由管理员选择复制到哪些任务。
3. 迁移报告至少包含区域 ID、设备 ID、候选任务 ID 和处理结果。

阶段二：收紧约束。

1. 管理员处理全部无归属和归属冲突记录。
2. 确认 `task_id IS NULL` 记录数量为零。
3. 将 `task_id` 修改为 `NOT NULL`。

迁移期间 POST 和新 API 只加载 `task_id` 精确匹配的区域；空 `task_id` 历史记录即使启用也不进入运行模板。

## 8. VIDEO 区域服务与 API

### 8.1 服务端验证

每次保存必须验证：

1. 任务存在，设备存在，设备属于该任务。
2. 任务配置了至少一个模型。
3. 指定模型集合非空、去重，且是 `algorithm_task.model_ids` 的子集；负数默认模型 ID 是合法业务模型 ID，`0` 不合法。
4. 坐标是有限数值并位于 `[0, 1]`。
5. `polygon` 至少 3 个点，`rectangle` 恰好 4 个点，`line` 恰好 2 个点。
6. 多边形和矩形面积大于零，不允许自相交。
7. `opacity` 位于 `[0, 1]`，`sort_order` 为非负整数。
8. 更新和删除的区域必须同时属于路径中的任务和设备。

任务移除模型时，不得把引用该模型的区域自动转换成全模型区域。任务保存接口应返回受影响区域列表，并采用以下规则：

- 默认拒绝模型移除，提示先修改区域；
- 管理员显式选择“同时禁用受影响区域”后，才允许在同一事务中禁用这些区域并保存任务。

### 8.2 原子批量接口

前端主流程使用批量接口，替代逐条创建、更新、删除：

```http
GET /video/device-detection/task/{task_id}/device/{device_id}/regions
```

响应：

```json
{
  "code": 0,
  "msg": "success",
  "task_id": 101,
  "device_id": "camera-1",
  "revision": 12,
  "data": [
    {
      "id": 301,
      "region_name": "人员通道",
      "region_type": "polygon",
      "points": [
        {"x": 0.1, "y": 0.2},
        {"x": 0.5, "y": 0.2},
        {"x": 0.5, "y": 0.8}
      ],
      "model_scope": "selected",
      "model_ids": [11],
      "is_enabled": true,
      "sort_order": 0
    }
  ]
}
```

`data` 继续保持数组，确保旧前端可以在 VIDEO 先发布时正常读取；`revision`、任务和设备字段以顶层增量字段返回。

```http
PUT /video/device-detection/task/{task_id}/device/{device_id}/regions
```

请求：

```json
{
  "expected_revision": 12,
  "regions": [
    {
      "id": 301,
      "region_name": "人员通道",
      "region_type": "polygon",
      "points": [
        {"x": 0.1, "y": 0.2},
        {"x": 0.5, "y": 0.2},
        {"x": 0.5, "y": 0.8}
      ],
      "model_scope": "selected",
      "model_ids": [11],
      "is_enabled": true,
      "sort_order": 0
    },
    {
      "region_name": "全模型区域",
      "region_type": "rectangle",
      "points": [
        {"x": 0.55, "y": 0.2},
        {"x": 0.9, "y": 0.2},
        {"x": 0.9, "y": 0.8},
        {"x": 0.55, "y": 0.8}
      ],
      "model_scope": "all",
      "model_ids": [],
      "is_enabled": true,
      "sort_order": 1
    }
  ]
}
```

批量保存语义：

- 有 `id` 的记录更新；无 `id` 的记录创建；数据库中存在但请求未包含的记录删除。
- 所有记录、删除操作和 `template_revision` 加一处于同一事务。
- 任一记录验证失败时全部回滚。
- 事务提交后只调用一次 `refresh_running_tasks_for_task(task_id)`。
- POST 立即推送成功时返回 `runtime_sync_status=applied`；失败时数据仍保存，返回 `runtime_sync_status=pending`，由定时对账恢复。
- `expected_revision` 冲突返回 HTTP `409`，前端要求用户重新加载后再保存。

### 8.3 兼容接口

现有单条接口保留一个发布周期，但必须增加任务归属校验并标记废弃：

- `POST /task/{task_id}/device/{device_id}/regions`
- `PUT /region/{region_id}`
- `DELETE /region/{region_id}`

旧更新和删除接口内部仍要锁定区域所属任务、增加模板版本并只刷新该任务。新 WEB 不再调用旧接口。旧的设备级接口必须要求 `task_id`，不能恢复设备全局查询语义。

### 8.4 事务边界

`device_detection_region_service.py` 中的底层 create/update/delete 不再自行 `commit`。事务由批量服务或路由上层统一管理，避免保存一半后刷新模板。POST 推送只能发生在数据库提交成功之后。

## 9. InferEvent 契约

### 9.1 Detection 字段

在兼容 `infer_event.v1` 的前提下为 Detection 增加：

```json
{
  "model_id": 11,
  "bbox": [100, 120, 260, 480],
  "class_id": 0,
  "class_name": "person",
  "confidence": 0.92,
  "track_id": 123
}
```

约束：

- `model_id` 是业务模型 ID，必需；迁移期允许兼容补齐。
- `bbox` 继续使用原图像素坐标 `[x1, y1, x2, y2]`。
- 区域点继续使用 `[0,1]` 归一化坐标。
- `frame_width` 和 `frame_height` 在存在适用区域时必须大于零。

Go 结构建议使用指针区分“缺失”和数值：

```go
ModelID *int64 `json:"model_id,omitempty"`
```

不要用事件级 `model_ids` 推断每个检测结果的来源。事件级字段只用于审计、兼容和快速校验。

### 9.2 兼容补齐规则

POST 处理顺序：

1. 检测结果存在 `model_id`：验证其属于任务模型集合。
2. 检测结果缺少 `model_id`，事件级 `model_ids` 只有一个：使用该 ID 补齐。
3. 检测结果缺少 `model_id`，任务模型也只有一个：使用任务模型 ID 补齐。
4. 多模型事件仍无法确定检测来源，且模板存在模型专属区域：整条事件丢弃，原因 `missing_detection_model_id`。
5. 多模型事件只有全模型区域：允许继续使用全模型区域，但记录兼容计数。
6. 检测模型不属于任务：整条事件丢弃，原因 `foreign_detection_model_id`。

完成所有生产者升级和观察期后，将检测级 `model_id` 调整为强校验字段。

### 9.3 生产者改造

Python：

- `VIDEO/services/realtime_algorithm_service/run_deploy.py` 已在每个检测结果写入模型 ID，保留并增加测试。
- `VIDEO/app/utils/algo_mqtt_bus.py` 对 `model_id is None` 的检测不应发送 JSON `null`，而应在发布前按上述兼容规则补齐或拒绝。
- snapshot、patrol 任务使用同一事件构造函数，统一获得相同行为。

C++：

- `RUNTIME/src/Detech.cpp` 在 `detections[]` 写入 `det.model_id` 对应的业务模型 ID。
- 线程池内部模型下标不能直接作为业务模型 ID。任务配置装载时必须建立 `runtime_model_slot → business_model_id` 映射。
- 事件级 `model_ids` 必须包含负数默认模型 ID，不能使用 `>= 0` 过滤。
- C++ 当前输出 `track_id=0` 的问题不阻塞普通区域门禁，但启用轨迹类空间插件前必须解决。

## 10. POST 任务模板和缓存

### 10.1 模板结构

在 `post_task_template.v1` 增加向后兼容的顶层 `revision`：

```json
{
  "schema": "post_task_template.v1",
  "revision": 13,
  "task": {
    "id": 101,
    "model_ids": [11, 12]
  },
  "regions": []
}
```

每个模板必须满足：

- `task.id` 与 URL 路径 `task_id` 相同，否则返回 `400`。
- 每个区域的 `task_id` 不需要重复传输，但区域 `device_id` 必须属于任务设备列表。
- VIDEO 构建模板时查询条件必须包含 `task_id`。
- POST 数据库预热查询必须使用 `task_id + device_id`，不能只使用设备集合。

`POST/internal/template/store.go` 的目标签名：

```text
loadRegions(ctx, taskID, deviceIDs)
```

目标 SQL：

```sql
SELECT ...
FROM device_detection_region
WHERE task_id = $1
  AND device_id IN (...)
  AND is_enabled = true
ORDER BY device_id, sort_order, id;
```

### 10.2 版本和乱序保护

POST Cache 为每个任务保存最近接收版本，包括删除墓碑：

- `upsert.revision < current_revision`：忽略并记录 `stale_upsert`。
- `upsert.revision == current_revision`：允许幂等覆盖和 TTL 刷新。
- `upsert.revision > current_revision`：原子替换模板和设备索引。
- `delete.revision < current_revision`：忽略。
- `delete.revision >= current_revision`：删除模板但保留版本墓碑，避免迟到的旧 upsert 复活任务。

HTTP 模板更新、MQTT 多副本同步和数据库预热共用同一版本比较逻辑。同步消息必须携带 `revision`。

兼容期版本缺失按 `0` 处理；一旦任务缓存见过大于 `0` 的版本，拒绝后续版本 `0` 的更新。

### 10.3 热更新与定时对账

新增 `refresh_running_tasks_for_task(task_id)`：

- 任务不处于 `running/restarting` 时不推送，启动流程会推送最新模板。
- 运行中只构建并推送该任务模板。
- HTTP 请求设置管理令牌、连接超时和有限重试。

为处理提交成功但即时推送失败的情况，POST 在配置数据库连接时每 30 秒执行一次运行任务模板对账：

1. 加载运行任务的 `template_revision`。
2. 只重建版本高于本地缓存的任务。
3. 应用统一的版本比较逻辑。
4. 单任务加载失败不影响其他任务，记录任务 ID 和原因。

即时推送目标生效时间不超过 3 秒；推送失败时，定时对账目标生效时间不超过 35 秒。

## 11. POST 区域过滤算法

### 11.1 每检测结果独立选择区域

当前基于事件模型并集的 `activePolygonRegions(ctx)` 必须拆为按检测模型选择：

```text
applicableRegions(taskRegions, detection.model_id):
    enabled
    AND region_type IN (polygon, rectangle)
    AND points valid
    AND (region.model_ids is empty/all OR contains detection.model_id)
```

`region_gate` 对每个检测结果执行：

```text
for detection in event.detections:
    regions = applicableRegions(detection.model_id)

    if regions is empty:
        keep detection              # 该模型全画面检测
        mark detection as bypass
        continue

    hits = regions containing selected sample point(s)
    if hits is empty:
        drop detection
    else:
        keep detection
        attach all matched region ids/names
```

不能先求整个事件的适用区域并对所有检测统一判断。

### 11.2 命中模式

后端和前端统一使用以下枚举：

| 值 | 语义 |
|---|---|
| `center` | 检测框中心点，默认 |
| `bottom_center` | 检测框底边中心，适合人员落脚点 |
| `any_corner` | 检测框任一角点命中 |

历史前端值 `bottom`、`any` 等在读取时映射到新枚举，保存时只写标准值。

### 11.3 输出语义

过滤后的 Detection 增加可选输出字段：

```json
{
  "matched_region_ids": [301, 302],
  "matched_region_names": ["人员通道", "入口"]
}
```

事件级 enrichment 保留所有检测结果的去重并集：

- `region_filter`: `bypass/applied/partial`；
- `matched_region_ids`；
- `matched_regions`；
- `region_revision`。

主区域从全部命中区域中按 `sort_order`、再按 `id` 选择，保证结果稳定。

如果所有检测结果都被区域过滤掉，事件结果为 drop，原因 `region_miss`。如果至少保留一个检测结果，则后续插件只处理保留结果。

### 11.4 其他空间插件

`region_enter_exit`、`line_cross`、`dwell_timer` 和 `headcount_gate` 也必须使用检测级模型范围，避免模型专属区域在这些插件中串用。

轨迹类插件的状态键应至少包含：

```text
task_id + device_id + model_id + track_id + region_id
```

当 `track_id` 缺失或为 `0` 时，轨迹类插件明确跳过并增加 `missing_track_id` 指标；普通 `region_gate` 不受影响。

## 12. WEB 交互设计

### 12.1 入口和上下文

- 区域编辑从算法任务上下文进入，`task_id` 必填。
- 页面顶部固定显示任务名称和当前设备名称。
- 设备切换列表只展示该任务已关联设备。
- 不提供不带任务的设备全局区域编辑入口。

### 12.2 区域编辑器

每个区域提供：

- 区域名称；
- 区域类型；
- 启用状态；
- 颜色和透明度；
- “适用模型”单选：`全部任务模型`、`指定模型`；
- 选择“指定模型”后，显示任务模型多选框，至少选择一个。

全部模型保存为 `model_scope=all, model_ids=[]`，服务端持久化为 `NULL`。指定模型保存为 `model_scope=selected, model_ids=[...]`。

保存按钮一次提交整个区域集合。收到 `409` 时提示“区域配置已被其他用户修改”，保留本地草稿并提供重新加载；不能静默覆盖。

### 12.3 运行态反馈

- 保存成功且 POST 已同步：显示“已生效”。
- 数据已保存但 POST 即时同步失败：显示“已保存，运行配置同步中”，不提示任务重启。
- 页面轮询当前 revision 或由现有状态通道刷新；对账完成后更新为“已生效”。
- 任务未运行时显示“配置已保存，将在任务启动时生效”。

## 13. POST 入口和失败策略

### 13.1 传输配置解耦

InferEvent 进入 POST 的配置不能继续隐式依赖最终告警的 `ALGO_BUS_TRANSPORT`。新增：

```text
POST_INGRESS_TRANSPORT=mqtt|off
POST_FAIL_STRATEGY=closed|open
```

首期 POST 入口只正式支持 MQTT。`POST_INGRESS_TRANSPORT=mqtt` 时要求配置可用 MQTT Broker 和 InferEvent topic。

`should_publish_infer_event` / `shouldPublishInferEvent` 由以下条件共同决定：

- POST 已启用；
- POST 健康检查就绪；
- `POST_INGRESS_TRANSPORT=mqtt`；
- MQTT 发布端可用。

本地区域过滤只能在上述 POST 通道真正可用时跳过，不能仅根据 `POST_ENABLED=true` 跳过。

### 13.2 失败行为

默认 `POST_FAIL_STRATEGY=closed`：

- InferEvent 发布失败时不直接产生未经 POST 过滤的告警；
- 释放告警抑制槽，允许后续帧恢复后重新告警；
- 记录任务、设备、模型和失败原因。

兼容场景可显式配置 `open`，但告警必须标记：

```json
{
  "post_bypass": true,
  "post_bypass_reason": "post_unready_or_publish_failed"
}
```

生产环境存在启用区域或自定义 POST pipeline 的任务时不建议使用 `open`。

## 14. 可观测性

### 14.1 结构化日志

POST 每个事件至少记录：

- `correlation_id`；
- `task_id`；
- `device_id`；
- `template_revision`；
- 输入和输出检测数量；
- 检测涉及的 `model_id`；
- 适用区域数量和命中区域 ID；
- `result` 和 `drop_reason`。

日志不输出完整图片、视频地址、鉴权令牌或过大的点集。

### 14.2 指标

新增或扩展：

```text
post_region_detection_total{result,model_scope,instance}
post_region_detection_drop_total{reason,instance}
post_region_model_id_compat_total{mode,instance}
post_task_template_stale_total{op,instance}
post_task_template_revision{task_id,instance}
video_post_template_sync_total{result}
video_post_ingress_publish_total{result,task_type}
camera_source_subscriber_count{device_id}
```

如 Prometheus 标签基数受限，`task_id/device_id` 只进入日志，不作为长期指标标签。

## 15. 安全、性能和并发约束

### 15.1 安全

- 区域 API 必须沿用任务管理权限，并校验调用者有权访问任务和设备。
- 仅凭 `region_id` 不得跨任务更新或删除区域。
- POST 模板管理接口在生产环境必须配置 `POST_ADMIN_TOKEN`。
- 模板 URL 中的 `task_id` 必须与请求体 `task.id` 一致。

### 15.2 性能

- 视频源、解码和模型推理次数不因区域数增加。
- 普通过滤复杂度为 `O(D × R × P)`：检测数、适用区域数和区域点数的乘积。
- 进入插件前按设备、启用状态和模型建立内存索引，避免每个检测扫描任务全部区域。
- 模板更新时预生成以下索引：
  - 设备全模型区域；
  - 设备按模型 ID 的专属区域；
  - 设备线区域。
- 首期将单任务单设备启用区域上限设为 100、单区域点数上限设为 64；超出时 API 给出明确提示并拒绝保存。限制值通过服务端配置统一调整。

### 15.3 并发

- WEB 使用 `expected_revision` 防止多人编辑覆盖。
- POST 模板替换持有短写锁，事件读取使用不可变快照。
- MQTT 同步、HTTP 推送和数据库对账可能并发到达，统一由 revision 决定是否应用。

## 16. 代码改动清单

### 16.1 VIDEO

| 文件 | 改动 |
|---|---|
| `VIDEO/models.py` | `AlgorithmTask` 增加 `template_revision`；收紧区域字段语义和 API 输出 |
| `VIDEO/run.py` | 增加幂等数据库迁移和历史数据检查，最终收紧 `task_id` |
| `VIDEO/app/services/device_detection_region_service.py` | 增加统一验证、批量事务保存、模型子集检查和 revision 乐观锁 |
| `VIDEO/app/blueprints/device_detection_region.py` | 增加批量 GET/PUT 返回结构，旧接口兼容和任务归属校验 |
| `VIDEO/app/services/post_template_client.py` | 区域按 task/device 查询；加入 revision；实现任务级刷新 |
| `VIDEO/app/utils/algo_mqtt_bus.py` | 检测级模型 ID 校验；POST 入口配置与失败策略解耦 |
| `VIDEO/services/realtime_algorithm_service/run_deploy.py` | 保证所有检测和事件分组保留模型 ID |
| `VIDEO/services/snapshot_algorithm_service/run_deploy.py` | 对齐相同 InferEvent 契约 |
| `VIDEO/services/patrol_algorithm_service/run_deploy.py` | 对齐相同 InferEvent 契约 |

### 16.2 POST

| 文件 | 改动 |
|---|---|
| `POST/internal/contract/types.go` | Detection 增加模型和命中区域字段；增加身份校验 |
| `POST/internal/config/template_types.go` | TaskTemplate 增加 revision；区域索引支持按模型选择 |
| `POST/internal/template/store.go` | 预热按 task/device 精确加载区域和 revision |
| `POST/internal/template/cache.go` | 版本比较、删除墓碑、不可变设备/模型区域索引 |
| `POST/internal/template/http.go` | 校验路径任务 ID、处理 revision、返回是否应用 |
| `POST/internal/template/sync_mqtt.go` | 同步 revision，拒绝乱序消息 |
| `POST/internal/plugin/regions.go` | 改为检测级模型区域选择 |
| `POST/internal/plugin/region_gate.go` | 每个检测独立 bypass/apply，输出检测级命中区域 |
| `POST/internal/plugin/region_enter_exit.go` | 使用模型级区域和复合轨迹状态键 |
| `POST/internal/plugin/line_cross.go` | 使用模型级线区域和复合轨迹状态键 |
| `POST/internal/plugin/dwell_timer.go` | 使用模型级区域和复合轨迹状态键 |
| `POST/internal/plugin/headcount_gate.go` | 按检测模型统计适用区域内数量 |
| `POST/internal/metrics/metrics.go` | 增加区域、模型兼容和模板乱序指标 |
| `POST/schemas/infer_event.v1.json` | 补充 Detection 字段结构和约束 |
| `POST/schemas/post_task_template.v1.json` | 补充 revision、task 和 region 结构约束 |

### 16.3 RUNTIME

| 文件 | 改动 |
|---|---|
| `RUNTIME/src/Detech.cpp` | InferEvent 检测级业务模型 ID；修正负数模型 ID；发布失败策略 |
| `RUNTIME/src/YoloThreadPool.*` | 明确内部 slot 与业务模型 ID 映射，不用固定 `0` 代替模型身份 |
| `RUNTIME/src/AlgoMqttBus.*` | POST 入口配置与告警传输解耦；仅在真实可用时跳过本地判断 |
| `RUNTIME/src/ConfigParser.cpp` | 解析新增 POST 入口和失败策略配置 |

### 16.4 WEB

| 文件 | 改动 |
|---|---|
| `WEB/src/api/device/device_detection_region.ts` | 使用批量 GET/PUT、revision 和 model_scope 类型 |
| `WEB/src/views/camera/components/DeviceRegionDrawer/index.vue` | 增加模型范围选择、批量保存、冲突和同步状态处理 |
| 算法任务编辑入口相关组件 | 强制传递 task_id、任务模型列表和任务设备列表 |

## 17. 测试设计

### 17.1 VIDEO 单元测试

1. 任务设备归属正确和错误场景。
2. `model_scope=all` 保存为 `NULL`。
3. 指定模型去重、非法模型、`0`、任务外模型校验。
4. polygon、rectangle、line 点数和坐标校验。
5. 批量创建、更新、删除成功时只增加一次 revision。
6. 批量中任一记录失败时全部回滚。
7. `expected_revision` 冲突返回 409。
8. 模型移除时引用区域被拒绝或显式禁用。
9. 模板只包含当前任务区域。
10. 任务未运行时保存不推送，运行时只刷新当前任务。

### 17.2 POST Go 单元测试

必须扩展 `region_gate_test.go` 和模板缓存测试，至少覆盖：

1. 无区域时全画面通过。
2. 全模型区域对不同模型均生效。
3. 模型 1 区域不影响模型 2 检测。
4. 同一事件包含模型 1 和模型 2，分别命中各自区域。
5. 模型 1 有区域、模型 2 无区域时，模型 2 全画面通过。
6. 一个检测命中多个区域，检测级和事件级命中信息正确。
7. 任务 A 模板不包含任务 B 的同设备区域。
8. 多模型事件缺失检测级模型 ID 时按兼容规则处理。
9. 外部模型 ID 被拒绝。
10. 帧尺寸缺失且需要区域缩放时 fail-closed。
11. polygon/rectangle 进入门禁，line 不进入普通门禁。
12. 低 revision upsert/delete 被忽略，删除墓碑阻止旧模板复活。
13. HTTP 路径 task ID 与请求体不一致返回 400。

### 17.3 契约测试

建立固定 JSON fixture，由 Python、Go、C++ 共用：

- 单模型事件；
- 多模型事件；
- 负数默认模型 ID；
- 缺失检测模型 ID；
- 像素 bbox 和归一化区域；
- 多区域命中输出。

Python 生成 fixture 后由 Go 反序列化测试读取；C++ 增加事件 JSON 生成测试，确保字段名称和类型一致。

### 17.4 集成和端到端测试

| 场景 | 期望 |
|---|---|
| 同摄像头 Task A 左区、Task B 右区 | 左侧目标只触发 A，右侧目标只触发 B |
| Task A 的 Model 1 左区、Model 2 右区 | 两模型按各自区域过滤，无交叉命中 |
| Model 2 未配置任何适用区域 | Model 2 保持全画面检测 |
| 运行中修改 Task A 区域 | 不重启任务，Task A 在目标时间内生效，Task B 不变化 |
| 同摄像头两个任务同时运行 | 共享源会话数为 1，订阅数为 2 |
| POST 重启 | 数据库预热后恢复精确任务区域 |
| POST 多副本收到乱序模板 | 最终所有副本保留最高 revision |
| POST 不可用、closed 策略 | 不产生绕过区域的告警 |
| POST 不可用、open 策略 | 允许直发且带明确 bypass 标记 |

## 18. 验收标准

1. 同一视频流同时运行多个算法任务时仍只有一个共享拉流和解码会话，正常降级场景除外。
2. 每个任务可以为自己的每个设备绘制多个矩形或多边形区域。
3. 每个区域可以选择全部任务模型或一个以上指定模型。
4. POST 模板中不存在同设备其他任务的区域。
5. 多模型事件中，每个检测结果只应用属于其来源模型的区域。
6. 某模型没有适用区域时按全画面检测，不被其他模型区域误过滤。
7. 区域修改成功后不重启任务；即时推送正常时 3 秒内生效，推送失败时 35 秒内由对账恢复。
8. 并发编辑不会静默覆盖，旧 revision 保存请求返回 409。
9. POST 不可用时遵循明确的 fail-open/fail-closed 策略，不出现隐式绕过。
10. 历史空 `task_id` 区域不会被静默应用到多个任务。
11. Python、C++ 和 POST 对 `model_id`、bbox 和区域坐标契约一致。
12. POST 单元测试、VIDEO 相关测试、WEB 类型检查和 RUNTIME 构建全部通过。

## 19. 实施拆分和依赖顺序

### 实施单元 1：数据库和区域 API

- 添加 `template_revision` 和索引。
- 实现历史数据扫描、规范化和迁移报告。
- 实现统一验证、批量事务 API、乐观锁和任务级刷新入口。
- 保留旧接口兼容。

完成条件：API 单元测试通过，批量保存不会部分提交，不会刷新其他任务。

### 实施单元 2：事件契约和生产者

- POST Detection 增加可区分缺失的模型 ID。
- Python 三类任务统一事件构造和校验。
- C++ 输出业务模型 ID，修正固定 slot 和负数模型问题。
- 增加跨语言 fixture。

完成条件：单模型、多模型和负数默认模型的 fixture 在 Python、Go、C++ 中一致。

### 实施单元 3：POST 模板隔离和区域过滤

- 修复 VIDEO 推送和 POST 预热的 task/device 精确查询。
- 按检测模型选择区域。
- 更新普通门禁及其他空间插件。
- 增加模板 revision、墓碑和乱序保护。

完成条件：Go 测试矩阵通过，同设备不同任务、同任务不同模型均无串区。

### 实施单元 4：WEB 区域编辑

- 增加模型范围选择。
- 切换到批量保存和 revision 冲突处理。
- 增加运行态同步反馈。

完成条件：可以在两个任务中分别编辑同一设备区域，刷新后配置保持隔离。

### 实施单元 5：传输、故障和对账

- 解耦 POST 入口和告警传输配置。
- 实现 closed/open 失败策略。
- 增加定时模板对账、指标和日志。

完成条件：POST 故障和恢复测试通过，不会产生未标记的旁路告警。

### 实施单元 6：迁移和灰度发布

- 运行历史数据扫描并处理冲突记录。
- 开启观察模式，对比“将被过滤”的结果但暂不抑制告警。
- 观察无跨任务、跨模型误判后开启强制过滤。
- 清理完成后将 `task_id` 收紧为 `NOT NULL`。

完成条件：灰度期无错误串区，运行任务模板版本一致，迁移报告无未处理记录。

## 20. 发布顺序和回滚

### 20.1 发布顺序

1. 数据库兼容迁移：新增列和索引，不立即设置 `task_id NOT NULL`。
2. 发布兼容新旧事件和 revision=0 的 POST。
3. 发布 VIDEO API、模板精确查询和 Python 生产者。
4. 发布 RUNTIME 生产者和配置。
5. 发布 WEB 批量区域编辑器。
6. 处理历史区域并开启观察模式。
7. 开启强制区域过滤和默认 fail-closed。
8. 完成历史清洗后收紧数据库约束。

### 20.2 回滚原则

- 数据库新增列和索引保留，不做破坏性回滚。
- WEB 可回滚到旧单条 API，兼容接口保留一个发布周期。
- POST 可通过任务 pipeline 暂时关闭 `region_gate`，但必须显式操作并记录审计。
- 如新生产者异常，POST 兼容补齐规则允许单模型事件继续运行；多模型专属区域不允许错误降级。
- 不允许通过恢复设备全局区域查询来回滚。

## 21. 风险和控制措施

| 风险 | 控制措施 |
|---|---|
| 历史区域无任务归属 | 禁用冲突记录、生成报告、人工选择，不自动复制到全部任务 |
| 多模型检测缺少来源模型 | 跨语言契约测试；多模型专属区域场景 fail-closed |
| 区域保存成功但模板推送失败 | 返回 pending；POST 30 秒对账；revision 幂等恢复 |
| 多副本消息乱序 | 单调 revision 和删除墓碑 |
| 前端逐条保存导致部分提交 | 改为批量事务 PUT |
| 模型被任务移除后区域语义变化 | 默认拒绝；显式选择后禁用受影响区域 |
| POST 故障绕过区域 | 入口配置解耦；默认 fail-closed；open 必须带 bypass 标记 |
| 区域过多导致过滤变慢 | 模型索引、可配置数量和点数上限、插件延迟指标 |
| C++ 内部 slot 冒充业务模型 ID | 显式映射和负数默认模型契约测试 |

## 22. 完成定义

本功能只有在以下条件全部满足时才算完成：

- 数据迁移、API、前端、Python、C++、POST 均按本设计落地。
- 所有单元、契约、集成和端到端测试通过。
- 同视频流多任务时共享源指标证明没有新增重复解码。
- 同设备不同任务、同任务不同模型的隔离测试通过。
- 区域热更新、乱序模板、POST 故障和恢复测试通过。
- 生产配置不再存在 `POST_ENABLED=true` 但 InferEvent 入口被隐式关闭的组合。
- 历史迁移报告中不存在未处理的启用区域。
- 运维文档说明新增配置、失败策略、指标和回滚方法。
