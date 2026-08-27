# 边缘录像分层存储与按需播放实施设计

## 1. 文档状态

- 状态：已批准，进入实施拆分。
- 日期：2026-08-26。
- 关联设计：
  - `2026-08-25-edge-camera-ingress-design.md`
  - `2026-08-25-algorithm-task-ingress-node-design.md`
- 适用形态：一个主节点、一个或多个边缘节点，摄像头可能只与所属边缘节点网络互通。

## 2. 已批准的架构决策

采用“边缘节点可选择中心共享存储或边缘本地存储，中心统一管理事件证据和录像目录”的双模式模型：

1. 每个边缘节点手动配置一种录像存储模式：`central_shared` 使用主节点现有 SRS/NFS/MinIO 链路，`edge_local` 使用边缘本地存储。
2. 小集群、边缘到主节点网络稳定且中心容量充足时，可选择 `central_shared`，不部署边缘完整录像存储，简化架构和运维。
3. 摄像头较多、跨节点带宽受限或要求断网继续录像时，选择 `edge_local`；事件元数据、事件图片和事件前后片段仍同步主节点，普通连续录像只同步索引。
4. 主节点负责设备、节点、录像目录、权限、播放路由和审计；是否保存普通连续录像由节点存储模式决定。
5. `edge_local` 模式下，客户端能够安全访问边缘媒体地址时，主节点签发短期播放地址并让客户端直接读取边缘录像；不能直达时由主节点媒体网关按需、流式代理。
6. 视频代理必须支持 `HEAD`、单段 `Range` 和 `206 Partial Content`，禁止应用服务将完整录像读入内存后返回。
7. 节点存储模式不自动故障切换。`central_shared` 网络中断时可能产生录像缺口；`edge_local` 可继续本地录像。
8. 模式切换只影响切换完成后产生的新录像，不自动搬迁历史录像；历史录像继续按原资产位置播放至过期。
9. 第一阶段保留现有边缘到主节点 SRS 的实时推流，避免同时改造录像和实时链路；后续可按节点和设备启用实时流按需中继。
10. 保留 MinIO 作为中心持久对象存储；NFS 继续服务 `central_shared` 和旧链路，但退出 `edge_local` 新事件媒体与连续录像的关键路径。
11. 本次不引入 Ceph，不替换 SRS，不建设每个边缘节点的多节点对象存储集群。

## 3. 背景与问题

当前边缘摄像头由接入节点拉取 RTSP，并通过 `publish_scope=control_plane` 将实时流推到主节点 SRS。SRS 持续生成 DVR 分片，录像通过共享媒体目录交给 iot-sink 上传 MinIO，最终更新 `Playback`、`RecordFile` 和 `Alert.record_path`。

该方式在少量摄像头下可工作，但边缘设备数量增加后存在以下问题：

- 边缘录像持续占用边缘到主节点带宽，主节点带宽随摄像头数量线性增长。
- 主节点 SRS、NFS、iot-sink、MinIO 共同处于录像关键路径，任一环节异常都会影响录像入库。
- 主节点承担所有录像容量、对象存储副本和回放读取，扩容边缘节点无法分散存储压力。
- 事件录像实际是持续 DVR 分片与事件时间的事后关联，不是精确的事件前后片段。
- 数据库保存固定 URL 或本地绝对路径，媒体位置、状态和可用性表达不完整。
- 当前对象代理整对象读取，不适合大录像并发、拖动和断点续播。

容量估算公式：

```text
单路每天容量 GB ≈ 码率 Mbps × 10.8
边缘容量 GB ≈ 摄像头数 × 码率 Mbps × 10.8 × 保留天数 × 1.2
```

例如 100 路、每路 4Mbps，每天约产生 4.32TB 原始录像数据；若全部持续上传中心，中心入口至少长期承受约 400Mbps 视频带宽，尚未包含副本、回放和管理流量。

## 4. 范围

### 4.1 本次范围

- 边缘节点手动选择中心共享存储或边缘本地存储。
- 边缘本地连续录像和容量水位管理。
- 按设备配置录像行为和保存周期，物理存储位置继承所属节点。
- 录像分片的中心目录索引和节点归属。
- 事件图片、事件片段的可靠中心同步。
- 主节点统一播放入口、边缘直连和主节点代理两种播放路径。
- 媒体资产状态、重试、幂等、审计和监控。
- 旧 `Alert`、`Playback`、`RecordFile` 数据和接口的渐进兼容。

### 4.2 非目标

- 不在首期改变现有摄像头添加、ONVIF 扫描和接入节点绑定流程。
- 不在首期取消边缘流向主节点 SRS 的持续实时推流。
- 不在首期建设多活 SRS Origin 集群。
- 不在首期迁移历史 MinIO 对象到边缘节点。
- 不在首期引入 CephFS、Ceph RGW 或其他新存储产品。
- 不把边缘连续录像视为中心灾备副本；是否双存由设备策略显式决定。

## 5. 方案比较与选择理由

### 5.1 方案 A：全部集中存储

边缘持续推流，主节点统一 DVR、NFS 中转和 MinIO 保存。该方案在本设计中作为 `central_shared` 模式正式保留。

优点是实现和运维集中，适合节点少、网络稳定的小集群；缺点是中心带宽、容量和故障域随设备数线性增长，断网时无法保证边缘持续录像。

### 5.2 方案 B：分层存储和按需播放

边缘保存连续录像，中心保存事件证据和目录；播放时直连边缘或由中心按需代理。该方案对应 `edge_local` 模式。

该方案复用现有 SRS、MinIO、节点绑定和本地存储能力，能直接降低中心持续录像带宽与容量，适合摄像头较多或网络不稳定的边缘节点。

### 5.3 方案 C：完全边缘自治

事件、录像、索引全部留在边缘，中心只做页面聚合。

该方案中心压力最低，但边缘损坏会丢失事件证据，离线时事件不可查看，无法满足统一审计和事件留存要求，因此不采用。

## 6. 目标架构

```text
摄像头 / NVR
    │ RTSP
    ▼
边缘媒体入口（现有 SRS / FFmpeg）
    ├──► 边缘算法任务
    │
    ├──节点模式 central_shared
    │       └──► 主节点 SRS DVR ──► 主节点 NFS / MinIO
    │
    └──节点模式 edge_local
            ├──► 边缘本地 DVR + 可靠队列 ──► 主节点录像索引
            └──► 事件图片/前后片段 ────────► 主节点 MinIO

客户端
    │
    ▼
主节点统一媒体接口
    ├──中心事件媒体──► MinIO Range / 短期签名地址
    ├──边缘可直达───► 短期边缘播放地址
    └──边缘不可直达─► 主节点媒体网关流式代理
```

### 6.1 控制面

主节点 VIDEO 服务负责：

- 保存设备录像策略和媒体资产索引。
- 保存并下发边缘节点录像存储模式。
- 校验设备与 `ingress_node_id` 的归属关系。
- 接收边缘录像分片批量上报。
- 为事件媒体签发上传凭证。
- 生成统一播放地址并决定直连、代理或中心对象存储路径。
- 展示边缘节点在线状态、存储容量、上传积压和录像可用性。

### 6.2 边缘媒体面

边缘 VIDEO/SRS 负责：

- 摄像头只在接入节点被拉取和录像。
- SRS DVR 写入节点本地媒体目录。
- DVR 回调注册分片，不再要求主节点通过 NFS 读取边缘绝对路径。
- 持久化待上报、待上传、重试和删除保护状态。
- 根据事件时间生成事件前后片段。
- 提供受保护的录像 `HEAD`/`Range GET` 接口。

以上边缘本地职责只在节点选择 `edge_local` 时启用。`central_shared` 节点继续使用主节点现有 DVR、NFS和 MinIO链路，边缘侧不部署完整录像目录、录像索引队列和历史录像内容接口，仅保留事件临时队列。

### 6.3 中心数据面

主节点 MinIO 负责长期保存：

- 事件原图和业务附图。
- 事件前后片段。
- 中心存储策略设备的连续录像。
- 从边缘按需提升为中心留存的录像。

`edge_local` 模式下，NFS 不参与新边缘录像和事件媒体的正常数据流。`central_shared` 模式继续使用现有主节点存储配置，主节点最终存储可以是 NFS挂载目录、主节点本地目录和 MinIO持久对象层的既有组合。

## 7. 录像与实时流策略

### 7.1 节点录像存储模式

物理存储位置在边缘节点级配置，同一边缘节点下的摄像头使用相同存储架构：

| 模式 | 连续录像位置 | 事件媒体 | 适用场景 |
|---|---|---|---|
| `central_shared` | 主节点 SRS/NFS/MinIO | 主节点保存 | 小集群、网络稳定、希望简化边缘部署 |
| `edge_local` | 边缘本地磁盘 | 同步主节点 | 摄像头较多、带宽有限、需要断网录像 |

`central_shared` 表示逻辑上统一使用主节点存储：边缘将流发布到主节点，由主节点 SRS落盘并进入既有存储链路。边缘节点不直接远程挂载和高频写主节点 NFS，避免把 NFS网络写入故障引入边缘进程。

选择建议：

- 预计边缘持续推流总码率小于边缘到主节点可用带宽的 60%，且主节点录像容量满足保存周期时，选择 `central_shared`。
- 超过带宽或容量安全线，或者要求主节点网络中断期间继续录像时，选择 `edge_local`。
- 主节点固定为 `central_shared`，不可修改。
- 已有边缘节点升级后默认 `central_shared`，保持当前行为。
- 新增边缘节点必须在页面明确选择，页面默认推荐 `central_shared`，并同时展示估算总码率、中心容量风险和两种模式差异。
- 不支持运行时自动从一种模式切换到另一种模式，避免同一时间段录像位置不确定。

### 7.2 设备录像策略

设备级策略不再决定物理存储位置，只决定是否录像和如何保留：

| 模式 | 行为 |
|---|---|
| `continuous` | 按所属节点存储模式保存完整连续录像 |
| `event_only` | 只保留环形缓存并生成事件前后片段 |
| `off` | 不保存视频，事件图片仍按中心事件策略保存 |

历史设备默认 `continuous`。保存周期、事件前后秒数和事件媒体同步规则仍按设备配置。

`event_only` 的环形缓存位置同样继承节点模式：`central_shared` 在主节点保存短期环形分片，`edge_local` 在边缘保存；事件片段生成成功并进入中心留存后，环形分片按水位和时间清理。

### 7.3 实时流传输策略

首期保留现有 `publish_scope=control_plane`。待录像分层稳定后，增加独立的 `live_transport_mode`：

| 模式 | 行为 |
|---|---|
| `always_push` | 始终推到主节点 SRS，兼容当前行为 |
| `on_demand` | 边缘保持本地源，主节点在观看或中心算法需要时建立中继 |
| `local_only` | 仅边缘消费，不提供中心实时预览 |

录像策略与实时传输策略必须解耦。例如设备可以本地连续录像，同时实时流仍始终推向中心。

约束：`central_shared + continuous` 必须使用 `always_push`，否则主节点无法持续录像；`edge_local` 可以使用 `always_push` 或后续的 `on_demand`。

节点启用 `edge_local` 后，中心的持续录像写入、NFS 中转和 MinIO容量压力会立即下降；但只要仍使用 `always_push`，主节点仍需承担该节点全部实时流的 RTMP 入站带宽。要消除这部分随摄像头数量线性增长的带宽，必须完成阶段 5，将非重点设备改为 `on_demand`。因此阶段 5 是目标架构的一部分，只是与存储改造分开发布。

### 7.4 节点存储模式切换

切换必须由节点管理页面显式触发，并采用“先验证新链路、再停止旧链路”的方式：

#### `central_shared → edge_local`

1. 预检边缘本地录像根、容量、SRS DVR、ffprobe 和内部媒体接口。
2. 将节点状态置为 `applying`，存储代次 `generation + 1`。
3. 启动边缘本地 DVR，至少验证一个新分片成功登记。
4. 将主节点实时推流切换到“只提供实时播放、不做中心 DVR”的 SRS vhost。
5. 状态置为 `active`；旧中心录像保留在原位置，不迁移。

#### `edge_local → central_shared`

1. 预检主节点 SRS、中心存储和边缘到主节点网络。
2. 将节点状态置为 `applying`，存储代次 `generation + 1`。
3. 将推流切换到启用 DVR 的主节点 SRS vhost，验证中心产生新分片。
4. 停止边缘持续 DVR；未完成的事件片段和上传任务继续处理。
5. 状态置为 `active`；旧边缘录像继续由边缘提供至过期。

切换失败时恢复旧模式并将错误写入节点状态。切换窗口允许短时间双写以避免录像缺口；统一索引以 `storage_generation` 和实际时间范围去重展示。

## 8. 数据模型

### 8.1 节点存储配置

物理存储模式由 iot-node 管理的计算节点持久化，VIDEO 通过节点 API 查询，不跨服务直接读表：

| 字段 | 类型 | 说明 |
|---|---|---|
| `recording_storage_mode` | varchar(20) | `central_shared/edge_local` |
| `recording_storage_state` | varchar(20) | `active/applying/error` |
| `recording_storage_generation` | bigint | 每次成功或开始切换时递增，用于区分切换前后资产 |
| `media_public_url` | varchar(500) nullable | 客户端可安全直连的边缘媒体地址 |
| `recording_storage_updated_at` | timestamptz | 最近模式切换时间 |
| `recording_storage_error` | varchar(500) nullable | 最近一次应用失败摘要 |

兼容规则：

- 主节点固定返回 `central_shared`。
- 历史边缘节点幂等补为 `central_shared`，不改变当前录像链路。
- 模式配置必须由节点管理接口修改，不能只修改某个容器环境变量造成控制面与实际状态不一致。
- VIDEO 只有在节点状态为 `active` 后才按新模式创建新录像资产。

### 8.2 `device_recording_policy`

新增设备录像策略表：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | bigint | 主键 |
| `device_id` | varchar(100) | 设备 ID，唯一索引 |
| `recording_mode` | varchar(20) | `continuous/event_only/off` |
| `retention_hours` | int | 连续录像保存小时数，默认 168；中心模式同步到既有录像空间策略 |
| `event_pre_seconds` | int | 事件前录像，默认 10，范围 0～300 |
| `event_post_seconds` | int | 事件后录像，默认 20，范围 0～300 |
| `event_image_sync` | boolean | 是否同步事件图片，默认 true |
| `event_clip_sync` | boolean | 是否同步事件片段，默认 true |
| `live_transport_mode` | varchar(20) | 首期写入 `always_push` |
| `playback_route_mode` | varchar(20) | `auto/direct/proxy`，默认 `auto` |
| `created_at` | timestamptz | UTC 创建时间 |
| `updated_at` | timestamptz | UTC 更新时间 |

跨服务不建立数据库外键，服务端保存前校验 `device_id` 存在。

### 8.3 `media_asset`

新增统一媒体资产表。外部接口只暴露资产 ID，不暴露节点绝对路径。

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | varchar(36) | 产生资产的服务生成 UUID，跨重试保持不变 |
| `asset_type` | varchar(32) | `alert_image/event_clip/recording_segment/snapshot/thumbnail` |
| `device_id` | varchar(100) | 设备 ID |
| `alert_id` | bigint nullable | 关联事件 |
| `task_id` | bigint nullable | 关联算法任务 |
| `source_node_id` | bigint nullable | 摄像头接入或算法执行 compute node ID，主节点设备为空 |
| `storage_node_id` | bigint nullable | 实际提供文件的边缘节点 ID；中心存储为空 |
| `storage_generation` | bigint | 产生资产时的节点存储代次 |
| `storage_scope` | varchar(16) | `edge/central` |
| `storage_backend` | varchar(16) | `local/minio` |
| `bucket_name` | varchar(255) nullable | MinIO bucket |
| `object_key` | varchar(500) | 对象键或相对媒体根路径 |
| `status` | varchar(16) | `pending/uploading/ready/failed/deleted` |
| `start_time` | timestamptz nullable | UTC 媒体开始时间 |
| `end_time` | timestamptz nullable | UTC 媒体结束时间 |
| `duration_ms` | bigint nullable | 真实时长，禁止依赖固定分片时长 |
| `file_size` | bigint nullable | 字节数 |
| `content_type` | varchar(100) | MIME 类型 |
| `etag` | varchar(128) nullable | 对象存储 ETag |
| `checksum` | varchar(128) nullable | SHA-256 等校验值 |
| `retry_count` | int | 上报或上传重试次数 |
| `last_error` | text nullable | 最近错误摘要，不记录凭证 |
| `expires_at` | timestamptz nullable | 资产逻辑过期时间 |
| `created_at` | timestamptz | UTC 创建时间 |
| `updated_at` | timestamptz | UTC 更新时间 |

索引和约束：

- `(device_id, start_time, end_time)`：时间轴查询。
- `(alert_id, asset_type)`：事件媒体查询。
- `(source_node_id, status)`：节点积压和故障查询。
- `(storage_node_id, start_time)`：边缘文件路由和时间轴查询。
- `(expires_at, status)`：清理任务。
- `id` 作为所有上报和重试的幂等键。
- 中心 MinIO 对象增加 `(bucket_name, object_key)` 唯一约束。

资产状态转换规则：

```text
pending ──► uploading ──► ready ──► deleted
   │             │
   └─────────────┴──────► failed ──► uploading
```

- `ready` 只有在本地文件可读，或者中心对象已经完成大小与 checksum 校验后才能进入。
- `deleted` 是终态；同一物理媒体重新产生时必须使用新的资产 ID。
- 普通边缘录像在本地登记完成后可以直接为 `ready`；其上报状态单独保存在边缘可靠队列，不能复用资产状态表达网络同步进度。

边缘本地 `object_key` 必须是相对于边缘媒体根目录的规范化路径，例如：

```text
playbacks/live/{device_id}/2026/08/26/{start_ms}.flv
```

禁止把 `/data/...`、`/mnt/...` 等绝对路径同步给浏览器。

### 8.4 现有表兼容

- `Alert` 新增可空的 `image_asset_id`、`record_asset_id`。
- `Alert.image_url`、`record_path` 保留，在迁移期由资产 `ready` 事件兼容回填。
- `RecordFile` 新增可空的 `asset_id`，新录像列表优先从 `media_asset` 构造。
- `Playback` 保留为旧接口兼容索引，不再作为新边缘录像的唯一事实来源。
- 不删除、重写或搬迁现有 MinIO 对象。

### 8.5 边缘可靠队列

`edge_local` 节点增加独立的本地 SQLite 队列 `media-spool.db`，放在本地媒体根的状态目录，不放在 NFS：

```text
{EDGE_RECORDING_ROOT}/.state/media-spool.db
```

队列至少保存：

- `asset_id`
- `device_id`
- 相对路径
- 开始/结束时间
- 上报状态
- 上传状态
- 重试次数和下次重试时间
- 删除保护计数

SQLite 使用 WAL 模式，单节点单写者；主节点不可用时边缘继续登记，恢复后按创建时间批量补报。`central_shared` 节点不需要普通录像索引队列，只保留事件文件短时重试目录。

## 9. 核心流程

### 9.1 中心共享存储连续录像

```text
边缘摄像头 RTSP
    │
    ▼
边缘转发任务 ──RTMP──► 主节点 SRS DVR
                              │
                              ▼
                    现有 NFS / 本地目录 / iot-sink / MinIO
                              │
                              ▼
                    主节点登记 central media_asset
```

该模式复用当前实现，不在边缘保存完整录像。主节点网络、SRS 或共享存储不可用时允许出现录像缺口，页面和节点状态必须明确显示该风险，不进行隐式本地录像降级。

### 9.2 边缘本地连续录像

```text
SRS 完成 DVR 分片
    │
    ▼
边缘 on_dvr Hook
    ├──校验文件位于 EDGE_RECORDING_ROOT
    ├──解析 device_id / task_id
    ├──ffprobe 获取真实 start/end/duration
    ├──生成 asset_id 和 checksum
    ├──写入边缘可靠队列
    └──异步批量上报主节点
            │
            ▼
主节点按 asset_id 幂等 upsert media_asset
```

Hook 在本地登记成功即可向 SRS 返回成功；主节点暂时不可达不能阻塞下一路录像。

### 9.3 事件图片同步

```text
算法产生事件和本地图片
    │
    ├──主节点立即落事件，image status=pending
    │
    └──边缘请求短期上传凭证
            │
            ├──成功：直接 PUT 主节点 MinIO
            │          └──complete 回调，status=ready
            │
            └──失败：进入本地队列，指数退避补传
```

边缘不保存长期 MinIO 管理员凭证。主节点根据节点令牌、设备归属和资产类型签发 5 分钟以内、限定 bucket/object key 的上传凭证。

事件列表不能再以 `image_url` 非空作为事件存在条件：

- `ready`：正常显示图片。
- `pending/uploading`：显示“媒体同步中”。
- `failed`：显示失败原因摘要和重试状态。

### 9.4 事件片段生成

```text
事件时间 T
    │
    ▼
等待 T + event_post_seconds
    │
    ▼
锁定覆盖 [T-pre, T+post] 的录像节点分片
    │
    ▼
FFmpeg 无损拼接/转封装
    │
    ├──成功：生成 event_clip 资产并上传中心
    └──失败：保留源分片，记录错误并重试
```

规则：

- 事件片段默认 `pre=10s`、`post=20s`。
- 同一设备时间窗口高度重叠的多个事件允许共用一个物理片段，但每条事件保持独立资产关联。
- `edge_local` 在边缘生成片段；`central_shared` 在主节点使用中心分片生成片段。
- 片段上传完成前，涉及的源分片标记为 protected，磁盘清理任务不得删除。
- 优先使用 `-c copy` 转封装；源编码或时间戳不兼容时允许回退到转码，并上报转码耗时。
- 片段真实开始、结束和时长必须来自媒体探测结果。

### 9.5 录像索引查询

主节点录像页面按设备和时间范围查询 `media_asset`：

1. 返回所有 `ready` 的中心和在线边缘资产。
2. 边缘离线时仍显示索引，但标记 `node_offline` 和不可播放。
3. 边缘尚未完成补报时，页面不保证展示断网期间的最新录像；节点恢复后自动补齐。
4. 时间轴以 UTC 毫秒为事实值，前端按用户时区展示。

### 9.6 录像播放路由

客户端始终请求统一地址：

```http
GET /video/media/assets/{asset_id}/content
HEAD /video/media/assets/{asset_id}/content
```

主节点根据资产位置选择：

#### 中心 MinIO 资产

- 优先返回短期签名 GET 地址，或由 Nginx/对象网关透传 Range。
- 需要强制同源时，由媒体网关流式代理。

#### 边缘直连

满足以下条件时使用：

- 节点在线并上报 HTTPS `media_public_url`。
- 设备策略为 `auto` 或 `direct`。
- 部署网络明确允许客户访问该地址。

主节点签发包含 `asset_id`、用户、过期时间和允许方法的短期令牌，返回 `302` 到边缘播放地址。边缘再次校验资产归属、路径和令牌。

#### 主节点代理

以下情况使用代理：

- 节点没有客户端可达地址。
- 设备策略为 `proxy`。
- 客户端从公网访问，而边缘节点位于专网/NAT 后。

主节点应用只做鉴权和路由决策，实际字节由 Nginx 或独立媒体网关转发。代理必须：

- 透传 `Range`、`If-Range`、`If-Modified-Since`。
- 返回 `Accept-Ranges`、`Content-Range`、`Content-Length`、`Content-Type`。
- 支持客户端中断，不继续下载剩余对象。
- 对每个用户、节点和全局设置并发与带宽限制。
- 上游地址只能来自已注册节点，防止 SSRF。

响应语义：

| 条件 | HTTP 状态 |
|---|---|
| 资产不存在 | 404 |
| 无权访问 | 403 |
| 资产处理中 | 409 |
| 资产已过期或删除 | 410 |
| 边缘节点离线 | 503 |
| Range 合法 | 206 |
| Range 越界 | 416 |

### 9.7 热门录像按需提升

首期不默认缓存边缘录像。后续可以提供“保存到中心”操作：

1. 主节点创建 `central` 副本资产，状态为 `pending`。
2. 边缘直接上传中心 MinIO，或媒体网关边播边缓存。
3. 校验大小和 checksum 后切换为 `ready`。
4. 后续播放优先使用中心副本。

该操作必须显式触发或基于明确的热度策略，不能把全部边缘录像重新自动复制到中心。

## 10. API 设计

### 10.1 管理端 API

```http
GET  /admin-api/iot/node/{node_id}/recording-storage
PUT  /admin-api/iot/node/{node_id}/recording-storage
POST /admin-api/iot/node/{node_id}/recording-storage/preflight
GET  /video/recording/policies/{device_id}
PUT  /video/recording/policies/{device_id}
GET  /video/recording/assets?device_id=&begin=&end=&asset_type=
GET  /video/recording/nodes/{node_id}/storage
POST /video/recording/assets/{asset_id}/promote
```

策略更新校验：

- 节点模式切换要求节点在线，并通过目标模式预检。
- `central_shared` 预检主节点 SRS、中心存储和节点到主节点可用带宽。
- `edge_local` 预检边缘本地录像根、可用容量、SRS DVR 和内部媒体接口。
- 设备策略要求设备存在有效 `ingress_node_id`，并继承该节点物理存储模式。
- `central_shared + continuous` 要求中心媒体服务和对象存储可用，并强制实时流 `always_push`。
- 保存时间和事件前后秒数必须在配置范围内。
- 修改策略不删除已有录像；只影响更新成功后产生的新分片。

### 10.2 边缘到主节点内部 API

```http
POST /video/internal/media/assets/report-batch
POST /video/internal/media/assets/upload-ticket
POST /video/internal/media/assets/{asset_id}/complete
POST /video/internal/media/assets/{asset_id}/failed
POST /video/internal/media/nodes/storage-report
```

要求：

- 使用节点身份令牌和请求时间戳签名。
- 主节点验证 `source_node_id` 与令牌一致。
- 批量上报单次最多 500 条，完整请求体限制 2MB。
- `report-batch`、`complete` 和 `failed` 均按 `asset_id` 幂等。
- 节点只能操作归属于自己的边缘资产。

### 10.3 边缘媒体内部 API

```http
GET  /video/internal/edge-media/assets/{asset_id}/content
HEAD /video/internal/edge-media/assets/{asset_id}/content
GET  /video/internal/edge-media/health
```

边缘接口只接受主节点签名令牌或集群内部双向认证，不接受服务器绝对路径参数。

### 10.4 前端响应结构

录像列表项统一增加：

```json
{
  "asset_id": "uuid",
  "device_id": "camera-001",
  "source_node_id": 181,
  "storage_scope": "edge",
  "status": "ready",
  "availability": "online",
  "start_time": "2026-08-26T02:00:00.000Z",
  "end_time": "2026-08-26T02:01:00.000Z",
  "duration_ms": 60000,
  "play_url": "/video/media/assets/uuid/content"
}
```

前端不得根据 `source_node_id` 自行拼接边缘 IP。

## 11. 存储目录与对象命名

### 11.1 边缘本地目录

以下目录只在 `edge_local` 模式启用；`central_shared` 不要求边缘配置完整录像盘：

```text
{EDGE_RECORDING_ROOT}/
  playbacks/{app}/{device_id}/{yyyy}/{MM}/{dd}/{start_ms}.{ext}
  event-clips/{device_id}/{yyyy}/{MM}/{dd}/{alert_id}-{start_ms}.mp4
  event-images/{device_id}/{yyyy}/{MM}/{dd}/{alert_id}.jpg
  .state/media-spool.db
  .tmp/
```

要求：

- `EDGE_RECORDING_ROOT` 必须是本地独立磁盘或本地卷，启动时拒绝解析为主节点 NFS 挂载。
- 临时文件先写 `.tmp`，完成后原子重命名。
- 文件名和对象键只使用服务端生成的安全字符。

### 11.2 中心 MinIO

首期复用现有 bucket，新增规范前缀：

```text
alert-images/{device_id}/{yyyy}/{MM}/{dd}/{alert_id}.jpg
record-space/events/{device_id}/{yyyy}/{MM}/{dd}/{alert_id}-{start_ms}.mp4
record-space/continuous/{device_id}/{yyyy}/{MM}/{dd}/{start_ms}.{ext}
```

对象键入库，下载 URL 在请求时动态生成，不保存永久签名 URL。

## 12. 容量管理和清理

每个 `edge_local` 边缘节点独立执行磁盘守护；`central_shared` 使用主节点既有磁盘守护和录像空间保存策略：

| 水位 | 默认值 | 行为 |
|---|---:|---|
| 目标水位 | 75% | 正常清理到该水位 |
| 高水位 | 85% | 按过期时间和最旧时间加速清理 |
| 临界水位 | 95% | 删除最旧非保护分片并标记存储降级 |

清理顺序：

1. 已过保存期且未受保护的普通分片。
2. 已同步中心且未被事件片段任务引用的本地事件临时文件。
3. 未过期的最旧普通分片，仅在临界水位触发。

不得自动删除：

- 正在上传或生成事件片段引用的分片。
- 中心要求保留且尚未完成同步的事件图片、事件片段。
- 运维手动锁定的证据资产。

节点每 60 秒上报：

- 总容量、已用容量、可用容量。
- 估算剩余录像小时数。
- 最早/最新录像时间。
- 待上报、待上传和失败资产数。
- 最近一次清理结果。

## 13. 一致性、并发与幂等

- 每个 `device_id + stream_profile` 同一节点只允许一个录像写入者。
- `asset_id` 在媒体产生服务首次登记时生成，所有重试复用同一 ID。
- 主节点使用 upsert，重复报告不能生成重复录像。
- 事件片段任务以 `alert_id + policy_version` 幂等。
- 上传完成必须校验对象存在、文件大小和 checksum，再将资产置为 `ready`。
- 数据库状态和对象存储之间使用补偿式一致性，不假设跨数据库和 MinIO 的分布式事务。
- 主节点定时对账 `uploading/failed` 资产；边缘定时对账本地队列与实际文件。
- 所有开始、结束、事件时间使用 UTC；节点必须启用 NTP，时钟偏差超过 5 秒时产生告警。

## 14. 故障处理

### 14.1 主节点或中心网络不可用

- `edge_local`：边缘持续录像，元数据和事件媒体进入本地可靠队列，恢复后按“事件媒体优先、普通索引其次”补报。
- `central_shared`：实时推流和中心录像可能中断并产生录像缺口；节点只缓存尚未发送的事件图片，不承诺完整录像续录。
- 两种模式均不做自动物理存储模式切换，页面必须展示网络异常时间范围和可能的录像缺口。
- `edge_local` 事件关联分片保持删除保护；本地空间不足时优先保留事件媒体。

### 14.2 MinIO 不可用

- 主节点事件正常落库，媒体状态为 `pending` 或 `failed`。
- `edge_local` 保留边缘文件；`central_shared` 保留中心暂存文件，并分别指数退避重试。
- 页面显示事件但提示媒体暂不可用。
- 不因图片上传失败从事件列表过滤事件。

### 14.3 边缘节点离线

- 中心事件图片和事件片段继续可播放。
- `edge_local` 连续录像索引继续显示，播放按钮禁用并提示节点离线。
- `central_shared` 已经落到中心的历史录像继续可播放，但离线期间不会产生新录像。
- 不自动切换到其他节点读取本地录像。
- 节点恢复后重新同步存储状态和缺失索引。

### 14.4 边缘文件缺失

- 本节只适用于 `edge_local` 资产。
- 播放返回 410，资产状态改为 `deleted` 或 `failed`。
- 主节点记录“索引存在但文件缺失”告警。
- 若存在中心副本，自动改用中心副本。

### 14.5 播放代理中断

- 客户端以 Range 从已播放位置重试。
- 主节点不缓存未完成响应到应用内存。
- 媒体网关记录上游节点、资产 ID、传输字节和中断原因。

## 15. 安全设计

- 外部接口只接受 `asset_id`，不接受任意 `path`。
- 边缘解析本地对象键后必须确认真实路径仍位于 `EDGE_RECORDING_ROOT`。
- 禁止通过软链接逃逸媒体根目录。
- 上传凭证限制节点、bucket、object key、方法和有效期。
- 播放令牌限制资产、用户、方法和有效期，不包含 MinIO 管理员凭证。
- 主节点代理只连接节点注册表中的媒体端点，拒绝用户提供上游地址。
- 事件图片和录像响应默认 `Content-Disposition: inline`，并设置正确 `Content-Type`。
- 所有播放和提升到中心的操作记录用户、设备、资产、节点、结果和传输量。

## 16. 部署配置

### 16.1 边缘节点

新增配置：

```dotenv
EDGE_RECORDING_STORAGE_MODE=central_shared
EDGE_RECORDING_ENABLED=false
EDGE_RECORDING_ROOT=/mnt/easyaiot-edge-media
EDGE_RECORDING_SEGMENT_SECONDS=10
EDGE_RECORDING_TARGET_PERCENT=75
EDGE_RECORDING_HIGH_PERCENT=85
EDGE_RECORDING_CRITICAL_PERCENT=95
EDGE_MEDIA_REPORT_INTERVAL_SECONDS=10
EDGE_MEDIA_STORAGE_REPORT_INTERVAL_SECONDS=60
EDGE_MEDIA_RETRY_MAX_SECONDS=300
MEDIA_CONTROL_PLANE_URL=https://control-plane.example.internal
```

`EDGE_RECORDING_STORAGE_MODE` 是节点控制面下发后的运行时有效值，不允许运维长期只修改本地 `.env`。当模式为 `central_shared` 时，`EDGE_RECORDING_ENABLED=false`，完整录像根、普通录像 SQLite队列和边缘录像内容接口不启动；仍保留小容量事件临时目录用于失败重试。

节点 ID 和节点令牌复用现有安全配置，不写入设计文档、测试代码或仓库环境文件。

### 16.2 主节点

新增配置：

```dotenv
MEDIA_ASSET_V2_ENABLED=false
MEDIA_PLAYBACK_ROUTER_V2_ENABLED=false
MEDIA_UPLOAD_TICKET_TTL_SECONDS=300
MEDIA_PLAY_TICKET_TTL_SECONDS=120
MEDIA_EDGE_PROXY_ENABLED=true
MEDIA_EDGE_PROXY_MAX_CONCURRENT=100
MEDIA_EDGE_PROXY_CONNECT_TIMEOUT_SECONDS=5
MEDIA_EDGE_PROXY_READ_TIMEOUT_SECONDS=60
```

默认关闭功能开关，按节点和设备灰度启用。

### 16.3 SRS

- `central_shared` 流发布到主节点“启用 DVR”的 vhost，继续使用当前中心录像链路。
- `edge_local` 的边缘 SRS `dvr_path` 指向 `EDGE_RECORDING_ROOT` 本地挂载，`on_dvr` 回调指向边缘本地 VIDEO。
- `edge_local` 即使继续向主节点推实时流，也必须进入主节点“禁用 DVR”的实时 vhost，防止中心和边缘重复保存连续录像。
- 首期分片建议 10 秒，最终时间以 ffprobe 为准。
- 主节点设备固定使用中心 DVR vhost。

## 17. 代码改造边界

### 17.1 VIDEO 后端

预计新增：

- `MediaAsset`、`DeviceRecordingPolicy` 模型和幂等迁移。
- `media_asset_service.py`：资产状态、查询、上报、对账。
- `edge_recording_service.py`：边缘 Hook、可靠队列、容量上报。
- `event_clip_service.py`：事件前后片段选择、锁定、生成和上传。
- `media_route_service.py`：中心、边缘直连和代理路由决策。
- `media_asset` blueprint：管理、内部和播放接口。

预计修改：

- `models.py`：新增模型和兼容字段。
- `dvr_upload_service.py`：保留中心旧链路，新增资产回填。
- `alert_service.py`：不再过滤无图片事件，返回媒体状态。
- `alert.py`：旧路径接口增加媒体根白名单并逐步废弃。
- `record_video_service.py`：优先查询 `media_asset` 时间轴。
- `playback_disk_guard_service.py`：支持边缘保护分片和策略保存期。
- `service_urls.py`：不再把固定 URL 作为媒体事实值。

### 17.2 DEVICE / iot-node

- 计算节点增加 `recording_storage_mode/state/generation` 和错误摘要字段。
- 节点管理接口提供模式查询、预检和应用操作。
- 节点注册信息增加媒体端点、直连能力和存储能力标签。
- 节点状态接口增加录像容量和积压摘要。
- 模式切换编排负责配置目标 SRS vhost、启动或停止边缘 DVR，并等待新分片验证。
- 主节点代理通过节点注册表解析内部媒体地址。
- 不在节点标签中保存 MinIO 管理员凭证。

### 17.3 WEB

- 边缘节点新增/编辑页增加“使用主节点共享存储/使用边缘本地存储”选择器、容量估算、风险提示和切换进度。
- 摄像头编辑页只配置连续/事件/关闭录像、保存时间、事件前后秒数和播放路由模式，不重复配置物理存储位置。
- 录像时间轴显示“边缘/中心”“节点在线/离线”“媒体同步中/失败”。
- 播放器始终使用统一 `play_url`，不拼接 MinIO或边缘地址。
- 事件列表显示图片和录像媒体状态，不再隐藏媒体未完成的事件。
- 节点页面显示录像磁盘容量、预计剩余时长和上传积压。

### 17.4 Nginx / 媒体网关

- 新增受保护的 `/media-assets/` 内部代理位置。
- 透传并校验 Range 相关头。
- 动态上游只能来自后端生成的内部路由结果。
- 记录资产级访问日志，但不记录签名令牌。
- 现有 Python MinIO整对象代理保留兼容，播放器新链路不再使用它。

### 17.5 部署脚本

- `central_shared` profile 复用当前推主 SRS 和中心存储链路，不创建边缘完整录像根。
- `edge_local` profile 创建独立本地录像根，不复用主节点 NFS 媒体根。
- `edge_local` 校验录像根是可写本地文件系统，并输出容量预估，SRS和 VIDEO映射同一个本地录像卷。
- 部署脚本根据模式选择主节点 DVR vhost 或实时无 DVR vhost。
- 升级脚本将历史边缘节点补为 `central_shared`，不改变历史设备实际行为。

## 18. 分阶段实施

### 阶段 0：现有链路正确性修复

- 事件列表取消 `image_url` 非空过滤。
- SRS 分片使用真实时长，消除 30/60 秒硬编码不一致。
- 本地图片和录像接口增加允许根目录校验。
- 对象播放支持 Range 或签名 URL。

阶段完成后，即使尚未启用边缘本地录像，现有事件链路也具备明确状态和安全回放能力。

### 阶段 1：媒体资产与策略控制面

- 创建节点存储模式字段、`device_recording_policy`、`media_asset` 和兼容字段。
- 实现节点模式选择、预检、状态和存储代次管理。
- 实现资产状态、节点容量上报和统一录像查询接口。
- 为历史 `RecordFile`、`Playback` 提供只读适配，不批量搬迁对象。
- 页面增加策略配置和资产状态展示。

### 阶段 2：边缘本地连续录像

- 保持 `central_shared` 节点继续使用现有中心链路。
- 部署边缘本地录像目录、SRS DVR 和可靠队列。
- `on_dvr` 本地登记并批量向主节点上报。
- 启用边缘水位清理和保护机制。
- 先选择一个测试边缘节点切换为 `edge_local`，验证模式切换和历史录像兼容。

### 阶段 3：事件媒体直传中心

- 图片使用短期上传凭证直传 MinIO。
- 实现事件前后片段生成和补传。
- 事件表关联 `image_asset_id`、`record_asset_id`。
- `edge_local` 新事件移除对共享 NFS 的依赖；`central_shared` 可继续复用当前中心暂存链路。

### 阶段 4：统一播放路由

- 实现中心 MinIO、边缘直连、中心代理三种路由。
- Nginx/媒体网关支持 Range 和连接中断。
- 前端全部使用统一资产播放地址。
- 按节点验证内网、NAT 和 HTTPS 场景。

### 阶段 5：实时流按需中继（独立发布单元）

- 在录像架构稳定后增加 `live_transport_mode=on_demand`。
- 边缘流本地发布，主节点按观看和中心算法需求建立中继。
- 保留 `always_push` 作为重点设备和兼容选项。

每个阶段均可独立发布和回滚；不得将阶段 5 作为前四阶段上线的前置条件。

## 19. 测试设计

### 19.1 单元测试

- 节点存储模式默认值、合法切换和状态恢复。
- `central_shared + continuous` 与 `on_demand` 的冲突校验。
- 存储代次递增和切换窗口重复分片去重。
- 录像策略默认值和参数边界。
- 资产状态转换和非法转换。
- `asset_id` 重复上报幂等。
- 本地对象键路径归一化和目录逃逸拦截。
- Range 解析：完整请求、开放区间、后缀区间、越界。
- 事件窗口分片选择、跨分片和重叠事件。
- UTC 时间转换、夏令时无关性和时钟偏差检测。
- 水位清理不得删除 protected 资产。

### 19.2 集成测试

- `central_shared` 节点继续通过主节点 SRS/NFS/MinIO 生成和播放录像，边缘不创建完整录像目录。
- `edge_local` 节点的主节点实时流不产生中心 DVR 对象，避免双写。
- 边缘 SRS 生成真实分片，主节点只收到索引，不读取边缘本地路径。
- 双向切换 `central_shared ↔ edge_local`，验证新录像位置改变、历史录像仍可播放且切换失败可以回退。
- `edge_local` 模式下主节点断开 30 分钟后恢复，边缘录像不中断且索引补齐、无重复。
- MinIO断开后事件仍可查询，恢复后图片和片段自动变为 `ready`。
- 边缘节点离线时中心事件片段可播放，边缘连续录像显示不可用。
- `Range: bytes=0-1023` 返回 206、正确 `Content-Range` 和 1024 字节。
- 播放中断后从新 Range 继续，不重新传完整文件。
- 旧 `Alert.record_path`、`Playback`、`RecordFile` 仍可播放。

### 19.3 页面端到端测试

1. 页面添加摄像头并选择边缘接入节点。
2. 在节点页面选择 `central_shared`，创建同节点算法任务并启动真实推流。
3. 验证录像落在主节点既有存储，边缘不创建完整录像目录，页面可正常播放。
4. 执行切换预检并将该边缘节点切换为 `edge_local`。
5. 验证边缘目录持续产生新录像，主节点不再为该节点产生普通连续录像对象，切换前中心录像仍可播放。
6. 触发算法事件，验证事件立即可见并经历 `pending → ready`。
7. 验证中心存在事件图片和前后片段。
8. 从录像时间轴播放边缘录像并拖动进度条。
9. 分别验证直连和主节点代理模式。
10. 断开边缘到主节点网络，验证 `edge_local` 继续录像和队列积压。
11. 恢复网络，验证事件优先补传、索引补齐且没有重复。
12. 切换回 `central_shared`，验证中心重新产生新录像，旧边缘录像仍能按原位置访问。
13. 将边缘节点置为离线，验证中心事件可用、边缘完整录像提示明确。

测试环境的服务器地址、账号、密码、签名令牌和日志原文不得提交仓库；测试报告只保留脱敏后的节点角色、版本、用例和结果。

### 19.4 容量与性能验证

- `central_shared` 模式下，页面展示的估算总码率、主节点入站带宽和中心容量增长与实际误差不超过 20%。
- `edge_local + on_demand` 在无用户播放时，主节点不应出现与边缘摄像头总码率等量的实时流入站或录像写入流量。
- `edge_local + always_push` 允许主节点存在实时流入站，但不得产生该节点普通连续录像对象。
- 单路 4Mbps 边缘录像经主节点代理时，主节点入站和出站分别接近单路码率，而不是全部摄像头总码率。
- 多并发播放过程中 VIDEO 应用内存不随完整录像大小线性增长。
- 事件媒体在网络正常时，应在 `event_post_seconds + 60秒` 内变为 `ready`。
- 达到高水位后应自动回落到目标水位，且受保护事件分片不丢失。

实际最大摄像头数和并发播放数按服务器网卡、磁盘和 CPU 压测结果写入部署容量基线，不在代码中硬编码。

## 20. 验收标准

1. 边缘节点可以在页面手动选择 `central_shared` 或 `edge_local`，并展示适用条件和风险。
2. 历史边缘节点升级后保持 `central_shared`，不改变现有录像链路。
3. `central_shared` 模式复用主节点现有存储，边缘无需部署完整录像盘和普通录像索引队列。
4. `edge_local` 模式的普通连续录像只写所属边缘本地存储，主节点实时 SRS不为其重复 DVR。
5. 双向切换只影响新录像，历史中心和边缘录像均按原资产位置继续播放。
6. 模式切换预检失败或应用失败时恢复旧模式，不出现无提示的半切换状态。
7. 主节点能统一查询中心和边缘录像的设备、节点、开始时间、结束时间、大小和可用状态。
8. 事件产生后，事件记录不依赖图片上传成功即可在页面显示；事件图片和片段可靠同步中心。
9. 主节点或中心网络短时中断时，`edge_local` 继续录像并在恢复后无重复补齐；`central_shared` 明确展示录像缺口风险。
10. 用户通过统一地址播放录像，能正常暂停、拖动和 Range 续传。
11. 客户端可访问边缘时可使用短期直连地址；不可访问时可通过主节点媒体网关流式代理。
12. 边缘离线时中心事件媒体仍可访问，边缘完整录像显示明确不可用状态。
13. 边缘磁盘水位清理正常，未同步事件和受保护片段不会被删除。
14. 旧事件、旧录像空间和旧播放接口保持可用。
15. API、数据库和日志不向客户端暴露边缘服务器绝对路径或长期存储凭证。

## 21. 发布、灰度与回滚

发布顺序：

1. 先发布主节点兼容数据库和只读接口。
2. 为历史节点补 `central_shared`，确认现有链路无变化。
3. 发布节点模式预检、切换编排和边缘本地录像能力。
4. 选择一个测试边缘节点切换为 `edge_local`。
5. 验证 24 小时录像连续性、事件补传、磁盘清理、回放和切回 `central_shared`。
6. 其余节点根据带宽和容量评估决定是否切换，不要求所有节点统一使用同一模式。

回滚原则：

- 关闭 `MEDIA_ASSET_V2_ENABLED` 和 `MEDIA_PLAYBACK_ROUTER_V2_ENABLED`，页面恢复旧接口。
- 将节点模式切回 `central_shared`，重新使用现有中心 DVR 链路。
- 新表和新字段保留，不在回滚中删除数据。
- 边缘已有录像保留至保存期结束，避免回滚造成额外数据丢失。

## 22. 实施任务拆分

建议按以下最小可交付单元创建开发任务：

1. 现有事件可见性、录像时长、路径白名单和 Range 修复。
2. 节点 `central_shared/edge_local` 数据模型、预检接口和管理页面。
3. `device_recording_policy`、`media_asset` 数据模型和迁移。
4. 主节点资产上报、查询、上传凭证和状态 API。
5. SRS中心 DVR/实时无 DVR vhost 路由和模式切换编排。
6. 边缘本地 DVR Hook、SQLite可靠队列和批量补报。
7. 边缘磁盘水位、保护引用、容量上报和节点页面。
8. 事件图片直传和事件媒体状态改造。
9. 事件前后片段生成、上传和事件关联。
10. 统一播放路由及中心 MinIO Range 链路。
11. 边缘直连签名播放和主节点流式代理。
12. 摄像头录像策略、录像时间轴和事件状态前端改造。
13. 双模式切换、断网、恢复、磁盘满、MinIO故障和并发播放回归。

前六个任务完成后即可开始边缘本地录像灰度；任务 9～12 完成后达到本设计的完整业务验收条件。
