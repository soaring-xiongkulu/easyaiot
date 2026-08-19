# Sentinel 集群节点哨兵模块设计

> 版本：v0.4  
> 日期：2026-08-19  
> 状态：功能模型已落地（L0 一键脚本管管理面，L2 Sentinel 管调度节点环境）

---

## 1. 背景与问题

EasyAIoT 已具备联邦集群调度能力：控制面 `iot-node` 负责节点纳管与 `allocate/release`，业务编排层（VIDEO / AI）将**集群训练**、**集群算法任务**、**集群推流转发**等工作负载下发至计算节点 Sentinel Agent 执行。

**职责切分（已钉死）**：

| 层 | 谁 | 管什么 |
|----|----|--------|
| **L0 管理面** | 一键部署脚本 | WEB、Gateway、iot-node、Nacos/PG/Redis、VIDEO/AI 控制服务 |
| **L2 调度节点** | Sentinel | RUNTIME、ffmpeg、SRS、bundle、NFS 导出/挂载、EMQX 等 |

单机 = 一台机器同时是控制面 + 勾选了业务功能的节点。

调度决策依赖三类信息：

| 信息来源 | 内容 | 问题 |
|---------|------|------|
| 静态配置 | 创建节点时勾选 **功能**（CSV 写入 `node_role`），由功能推导 `capabilities` JSONB | **声明 ≠ 实测**，节点实际未安装 RUNTIME、SRS、训练环境等仍可能被选中 |
| Agent 心跳 | CPU/内存/磁盘/GPU/NFS 挂载、`activeTasks` | 仅反映**瞬时资源**，不反映软件栈、版本、端口、Bundle 就绪度 |
| 业务侧 failover | 算法/推流心跳超时后迁移分片 | **事后补救**，任务已失败或卡顿后才触发 |

典型失败场景：

1. **算法任务（executor=cpp）**：调度到「具备 `algorithm_realtime` 能力」的节点，但该节点未分发 RUNTIME 二进制或 ONNX 运行时缺失 → 部署失败或进程秒退。
2. **集群训练**：节点勾选 `train` 且 `model_train=true`，但 PyTorch/CUDA 版本不匹配、NFS 未挂载、数据集路径不可写 → 训练 worker 启动失败。
3. **推流转发**：节点勾选 `forward`/`live` 且声明 `srs_live=true`，但 SRS 进程未运行或 1935 端口不可达 → 转发任务 RTMP 推流失败。
4. **LLM 推理**：调度器未校验 `minGpuMemMb`（VO 已定义但未实现），仅靠 AI 模块局部校验。

**结论**：集群能力无法「真正用起来」，是因为缺少一个**主动、持续、可验证**的节点能力感知层。本设计提出 **Sentinel（哨兵）** 模块，将「声明能力」与「实测能力」分离，并为调度器提供**可调度性（Schedulability）** 判定。

> 命名说明：本模块与 Alibaba Sentinel（熔断限流）无关；Sentinel 取「哨兵」语义——持续守望集群节点真实状态。
> 旧 `compute / gpu / media / mqtt / storage / hybrid` 角色已废弃，**不做兼容**。GPU、是否控制面是属性，不是角色。

---

## 2. 目标与非目标

### 2.1 目标

| # | 目标 | 验收标准 |
|---|------|---------|
| G1 | **能力实测** | 每个节点对每个 capability 有 `ready / degraded / unavailable / unknown` 状态及探测依据 |
| G2 | **环境画像** | 记录 OS、Agent/RUNTIME/Bundle 版本、GPU 型号与驱动、Python/CUDA、挂载路径等 |
| G3 | **调度可信** | `NodeSchedulerServiceImpl.allocate()` 仅选择 **Schedulable** 节点；分配前可二次校验 |
| G4 | **主动降级** | 资源过载或探测失败时，临时从可调度集合摘除对应能力，恢复后自动加回 |
| G5 | **可观测** | WEB 集群概览展示「声明 vs 实测」矩阵；变更通过 WebSocket 推送 |
| G6 | **统一注册表** | 能力键、探测项、调度前置条件集中定义，避免 VIDEO/AI 硬编码发散 |

### 2.2 非目标（首期不做）

- 不做跨控制面联邦级的全局 Sentinel 主从选举（沿用现有 `control_plane_peer` 模型，各控制面独立运行）
- 不做基于 ML 的负载预测调度（仍用现有打分逻辑，仅增强过滤条件）
- 不替代 PANEL 容器级诊断（Sentinel 聚焦**计算/媒体工作节点**）
- 不改造 EDGE 边缘采集设备模型（与 `compute_node` 调度域分离）

---

## 3. 核心概念

### 3.0 功能开关（唯一声明源）

注册表：`SENTINEL/registry/functions.yaml`（NODE classpath 同步一份）。WEB 勾选、落库 CSV、Sentinel 期望组件、调度过滤都读这张表。

| id | 含义 | 调度 workload |
|----|------|----------------|
| `algorithm` | 视频分析 | `algorithm_task` |
| `forward` | 推流转发 | `stream_forward` |
| `live` | 直播接入 SRS/ZLM | `srs_live` / `zlm` |
| `train` | 模型训练 | `model_train` |
| `llm` | 大模型 | `llm_service` |
| `label` | 智能标注 | `auto_label` |
| `infer` | 模型推理 | `ai_service` |
| `mqtt` | 物联接入 | `emqx` / `mqtt_gateway` |
| `nfs` | 共享存储（NFS 导出） | 非任务 |
| `transform` | 数据转发 | `transform_runtime` |

NFS 客户端不是功能：勾了 `algorithm/train/label/infer` 才期望 `nfs_mount`。控制面本机默认：`algorithm,forward,live,nfs`。Agent 环境变量：`NODE_FUNCTIONS`。

### 3.1 三层能力模型

```
┌─────────────────────────────────────────────────────────┐
│  Declared Capabilities（声明能力）                        │
│  管理员勾选功能 → 推导写入 compute_node.capabilities           │
│  「这个节点设计上应该能做什么」                            │
└────────────────────────┬────────────────────────────────┘
                         │ Sentinel 探测校验
┌────────────────────────▼────────────────────────────────┐
│  Detected Capabilities（实测能力）                        │
│  Agent 探测 + 控制面聚合 → node_capability_snapshot       │
│  「这个节点此刻实测能做什么」                              │
└────────────────────────┬────────────────────────────────┘
                         │ 资源 + 占用 + 策略
┌────────────────────────▼────────────────────────────────┐
│  Schedulable Capabilities（可调度能力）                   │
│  detected ∩ declared ∩ 资源健康 ∩ 无临时禁入              │
│  「调度器可以安全把任务放上去的能力」                      │
└─────────────────────────────────────────────────────────┘
```

### 3.2 节点状态（Node Operational State）

在现有 `compute_node.status`（online/offline）之上，增加 **operational_state**：

| 状态 | 含义 |
|------|------|
| `online` | 心跳正常（沿用现有） |
| `offline` | 心跳超时（沿用现有） |
| `degraded` | 在线但部分能力不可用或资源告警 |
| `probing` | 正在全量探测（注册后 / 手动 resync） |
| `blocked` | 管理员手动禁止调度 |

### 3.3 能力项状态（Capability Item State）

每个 `(node_id, capability_key)` 记录：

```json
{
  "capability": "algorithm_realtime",
  "state": "ready",
  "reason": "",
  "last_probe_at": "2026-08-18T10:00:00Z",
  "probe_version": "2026.08.1",
  "evidence": {
    "runtime_bin": "/opt/easyaiot/runtime/easyaiot_runtime",
    "runtime_version": "1.2.0",
    "cuda_available": true
  },
  "ttl_seconds": 120
}
```

状态枚举：

| state | 说明 |
|-------|------|
| `ready` | 探测通过，可参与调度 |
| `degraded` | 部分条件不满足（如 GPU 显存 < 阈值），可调度但降权或仅特定任务 |
| `unavailable` | 探测失败，不可调度 |
| `unknown` | 尚未探测或探测过期 |

### 3.4 环境画像（Environment Profile）

与能力分离存储，描述节点**静态/半静态**环境：

```json
{
  "os": {"system": "Linux", "release": "5.15.0", "arch": "x86_64"},
  "agent": {"version": "1.0.0", "port": 9100},
  "gpu": [{"id": 0, "name": "NVIDIA A10", "driver": "535.86", "cuda": "12.1"}],
  "software": {
    "runtime": {"path": "...", "version": "1.2.0", "build": "cuda118"},
    "python": "3.10.12",
    "ffmpeg": "5.1.2",
    "docker": "24.0.7"
  },
  "storage": {
    "cluster_mode": true,
    "nfs_mount_root": "/mnt/easyaiot-media",
    "nfs_mount_ready": true,
    "writable_paths": ["datasets", "models", "train"]
  },
  "network": {
    "srs_rtmp_port_open": true,
    "bandwidth_mbps_est": 850
  },
  "bundles": [
    {"type": "algorithm_realtime", "version": "2026.08.1", "installed_at": "..."}
  ]
}
```

---

## 4. 总体架构

```
                    ┌──────────────────────────────────────┐
                    │           WEB 集群概览 / 节点详情       │
                    │   声明 vs 实测矩阵 · 探测日志 · 手动 resync │
                    └───────────────────┬──────────────────┘
                                        │ REST / WS
┌───────────────────────────────────────▼───────────────────────────────────────┐
│                         iot-node 控制面                                         │
│  ┌─────────────────────┐  ┌──────────────────────┐  ┌─────────────────────┐  │
│  │ SentinelAggregator  │  │ CapabilityRegistry   │  │ NodeScheduler       │  │
│  │ 心跳/探测结果合并     │  │ 能力键 + 探测规则定义  │  │ + SchedulabilityFilter│  │
│  └──────────┬──────────┘  └──────────────────────┘  └─────────────────────┘  │
│             │                                                                   │
│  ┌──────────▼──────────┐  ┌──────────────────────┐  ┌─────────────────────┐  │
│  │ ProbeScheduler      │  │ node_capability_*    │  │ PreDeployValidator  │  │
│  │ 定期触发远程探测      │  │ 表持久化               │  │ deploy 前二次校验    │  │
│  └─────────────────────┘  └──────────────────────┘  └─────────────────────┘  │
└───────────────────────────────────────┬───────────────────────────────────────┘
                                        │ Agent HTTP :9100
                    ┌───────────────────▼───────────────────┐
                    │         SENTINEL（每工作节点全量离线包）   │
                    │  ┌─────────────┐  ┌─────────────────┐ │
                    │  │ run_sentinel│  │ ComponentSentinel│ │
                    │  │ 心跳经网关   │  │ L0/L1/L2 扫描    │ │
                    │  └─────────────┘  └─────────────────┘ │
                    └───────────────────────────────────────┘
                                        │
                    ┌───────────────────▼───────────────────┐
                    │  本地软件栈：RUNTIME / SRS / Python Bundle │
                    │  GPU / NFS / 端口 / 进程                 │
                    └───────────────────────────────────────┘

业务编排层（VIDEO / AI）allocate 时携带 requirements
    → 调度器查 Schedulable Capabilities
    → deploy 前 PreDeployValidator
    → 失败则 release + 排除节点 + 重调度
```

### 4.1 组件职责

| 组件 | 部署位置 | 职责 |
|------|---------|------|
| **sentinel_probe** | NODE Agent 内（Python 模块） | 执行探测脚本，产出 `detectedCapabilities` + `environmentProfile` |
| **SentinelAggregator** | iot-node | 合并心跳探测、持久化、计算 schedulable、推送 WS 事件 |
| **CapabilityRegistry** | iot-node（YAML/DB） | 能力注册表：键名、依赖探测项、调度默认 requirements |
| **ProbeScheduler** | iot-node（定时任务） | 全量/增量探测调度；注册后首次全量；周期轻量 + 周期深度 |
| **SchedulabilityFilter** | NodeSchedulerServiceImpl 扩展 | allocate 过滤链一环 |
| **PreDeployValidator** | NodeCommandServiceImpl 扩展 | HTTP 调用 Agent `/sentinel/validate` 做分配后、部署前校验 |

### 4.2 全量离线自动部署（节点分配即安装）

SENTINEL 具备**完整离线独立部署能力**。每新增一台计算节点（纳管完成、SSH 可用），控制面即携带**全量 Sentinel 环境**到该节点安装，即使当前 Profile 暂时用不到全部组件。

| 步骤 | 行为 |
|------|------|
| 1. 节点分配 | WEB 创建节点（含 SSH）→ `compute_node` 落库 |
| 2. 事务提交后 | `auto-deploy-on-create` 异步 SSH 同步 `SENTINEL/` + `pip-wheels` + `registry/` |
| 3. 目标机安装 | `/opt/easyaiot/sentinel-agent` 执行 `install.sh install`，写 systemd |
| 4. 立即监测 | 进程启动 → 注册 → **首次 L1 全量扫描** → 心跳经 **Gateway `/admin-api/node/agent`** 上报 NODE |
| 5. 持续哨兵 | 每次心跳 L0；默认每 300s L1；缺失期望组件请求 Remediator |

上报路径（强制走网关，不直连 iot-node 端口）：

```
SENTINEL ──POST──▶ http://<gateway>:48080/admin-api/node/agent/heartbeat
                 └── rewrite ──▶ NODE ingestHeartbeat → node_sentinel_snapshot
```

工作负载 Bundle（RUNTIME / 训练环境 / SRS）**不是**节点创建时必装项；Sentinel 先扫描「在不在、能不能调」，缺件再按 registry 自愈分发。

---

## 5. 能力注册表（Capability Registry）

集中定义所有能力键及探测规则，建议首版以 `DEVICE/iot-node/iot-node-biz/src/main/resources/sentinel/capabilities.yaml` 维护，后续可迁 DB。

### 5.1 计算类能力

| capability | 关联 workload_type | 探测项 |
|------------|-------------------|--------|
| `algorithm_realtime` | algorithm_task (realtime) | RUNTIME 二进制存在且 `--version` 成功；CUDA/CPU 后端可用；`algorithm_realtime` Bundle 目录存在 |
| `algorithm_snap` | algorithm_task (snap) | 同上 + Cron 执行环境 |
| `algorithm_patrol` | algorithm_task (patrol) | 同上 + 多路并发资源余量 |
| `stream_forward` | stream_forward | RUNTIME forward 模式或 Python `run_deploy.py`；ffmpeg 可用 |
| `model_train` | model_train | Python 训练 venv；torch+cuda 匹配；NFS 数据集/模型目录可写；GPU 显存 ≥ 配置阈值 |
| `auto_label` | auto_label | SAM/YOLO 依赖；GPU 可选 |
| `llm_inference` | llm_service | GPU 数量；`llm_node_capacity` 显存规则；vLLM/ollama 进程或镜像 |
| `ai_inference` | ai_service | 推理服务 Bundle；Nacos 注册可选 |
| `transform_runtime` | transform_runtime | TRANSFORM 运行时 |

### 5.2 媒体类能力

| capability | 探测项 |
|------------|--------|
| `srs_live` | SRS 进程运行；1935 RTMP 端口监听；HTTP API `/api/v1/summaries` 可达 |
| `srs_ai` | SRS + ai 应用配置存在 |
| `zlm` | ZLM 进程；端口探测 |

### 5.3 基础设施类

| capability | 探测项 |
|------------|--------|
| `nfs_server` | NFS 导出/挂载（storage 角色） |
| `media_storage` | 共享挂载读写探针（写临时文件后删除） |
| `emqx` / `mqtt_gateway` | EMQX 端口 1883/8083 |

### 5.4 调度 Requirements 映射

注册表同时定义 `allocate` 默认 requirements，供 VIDEO/AI 引用：

```yaml
algorithm_realtime:
  capabilities: [algorithm_realtime]
  require_nfs_mount: true
  prefer_gpu: true
  min_free_vram_mb: 2048
  executor_cpp:
    require_runtime: true
    min_runtime_version: "1.0.0"

model_train:
  capabilities: [model_train]
  require_nfs_mount: true
  prefer_gpu: true
  gpu_count: 1
  min_free_vram_mb: 8192

stream_forward:
  capabilities: [stream_forward, srs_live]
  max_cpu_percent: 85
  max_mem_percent: 95
```

---

## 6. 探测机制

### 6.1 探测分级

| 级别 | 触发时机 | 耗时 | 内容 |
|------|---------|------|------|
| **L0 轻量** | 每次心跳（10s） | < 500ms | 资源指标、NFS 挂载、活跃 workload 数、关键进程存活（SRS/RUNTIME 文件存在性） |
| **L1 标准** | 注册成功、Bundle 部署后、每 5min | < 30s | L0 + 版本号采集、端口探测、GPU 详情、Bundle 版本回读 |
| **L2 深度** | 手动 resync、ProbeScheduler 每 30min、deploy 失败重探 | < 120s | L1 + 试跑探针（RUNTIME `--self-test`、训练 import torch、RTMP loopback 推流测试） |

### 6.2 Agent 侧实现

新增 `SENTINEL/sentinel/orchestrator.py`，由 `run_sentinel.py` / `run_agent.py` 在心跳循环中调用：

```python
# 伪代码
def probe(level: str = "L0") -> dict:
    functions = parse(os.environ.get("NODE_FUNCTIONS"))
    expected = expected_components_for(functions)
    results = {cid: run_probe(cid, level) for cid in COMPONENT_PROBES}
    return {
        "probeLevel": level,
        "nodeFunctions": functions,
        "components": results,
        "schedulableCapabilities": derive_capabilities(results),
    }
```

心跳 payload（`sentinel` 字段）：

```json
{
  "nodeId": 1,
  "agentToken": "...",
  "cpuPercent": 12.5,
  "...": "...",
  "sentinel": {
    "probeLevel": "L0",
    "detectedCapabilities": { "algorithm_realtime": {"state": "ready", "...": "..."} },
    "environmentProfile": { "...": "..." }
  }
}
```

Agent HTTP 新增端点（`agent_server.py`）：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/sentinel/probe` | 控制面触发探测，`{"level": "L2"}` |
| POST | `/sentinel/validate` | 部署前校验，`{"workloadType", "requirements", "executor"}` |
| GET | `/sentinel/profile` | 返回最新环境画像 |

### 6.3 控制面聚合逻辑

`SentinelAggregator.onHeartbeat()`：

1. 解析 `sentinel` 字段；若无则标记全部 capability 为 `unknown`
2. 与 `declaredCapabilities` 对比：声明但实测 unavailable → 记告警
3. 应用**临时禁入规则**（资源过载、连续 deploy 失败）
4. 计算 `schedulableCapabilities` 写入 Redis 缓存（供调度热路径）+ 异步落库
5. 若 capability 状态变更 → `NodeClusterMetricsBroadcaster` 推送 `capability_changed` 事件

**Schedulable 计算规则**：

```
schedulable(cap) =
    declared[cap] == true
    AND detected[cap].state ∈ {ready, degraded}
    AND NOT temp_blocked[cap]
    AND node.status == online
    AND node.operational_state ∉ {blocked, probing}
    AND resource_policy(workload_type, metrics) == pass
```

---

## 7. 数据模型

### 7.1 新增表

**node_capability_snapshot**（最新快照，每节点一行）

```sql
CREATE TABLE node_capability_snapshot (
    node_id           BIGINT PRIMARY KEY REFERENCES compute_node(id),
    environment_profile JSONB NOT NULL DEFAULT '{}',
    detected_capabilities JSONB NOT NULL DEFAULT '{}',
    schedulable_capabilities JSONB NOT NULL DEFAULT '{}',
    probe_level       VARCHAR(8) NOT NULL DEFAULT 'L0',
    probe_version     VARCHAR(32),
    last_probe_at     TIMESTAMPTZ NOT NULL,
    last_full_probe_at TIMESTAMPTZ,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**node_capability_probe_log**（可选，首期可采样存储）

```sql
CREATE TABLE node_capability_probe_log (
    id                BIGSERIAL PRIMARY KEY,
    node_id           BIGINT NOT NULL,
    capability        VARCHAR(64),
    probe_level       VARCHAR(8),
    state             VARCHAR(16),
    reason            TEXT,
    evidence          JSONB,
    probed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_probe_log_node_time ON node_capability_probe_log(node_id, probed_at DESC);
```

### 7.2 扩展 compute_node

```sql
ALTER TABLE compute_node
    ADD COLUMN operational_state VARCHAR(16) NOT NULL DEFAULT 'online',
    ADD COLUMN sentinel_agent_version VARCHAR(32),
    ADD COLUMN capability_stale BOOLEAN NOT NULL DEFAULT true;
```

- `capability_stale=true`：Agent 版本不支持 Sentinel 或超过 TTL 未收到探测

### 7.3 Redis 缓存

```
node:schedulable:{nodeId}  → JSON schedulable_capabilities  TTL 60s
node:sentinel:profile:{nodeId} → environmentProfile  TTL 120s
```

调度热路径优先读 Redis，miss 回源 DB。

---

## 8. API 设计

### 8.1 控制面 REST（iot-node）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin-api/node/sentinel/registry` | 能力注册表（给 WEB / 编排层查询） |
| GET | `/admin-api/node/{id}/sentinel` | 节点 Sentinel 详情：声明/实测/可调度三方对比 |
| POST | `/admin-api/node/{id}/sentinel/probe` | 触发远程 L1/L2 探测 |
| POST | `/admin-api/node/sentinel/resync` | 批量 resync（可选 nodeIds） |
| GET | `/admin-api/node/sentinel/schedulable` | 查询当前可调度节点列表（按 capability 过滤） |

### 8.2 调度 API 扩展

现有 `POST /admin-api/node/scheduler/allocate` 的 `Requirements` 扩展：

```json
{
  "workloadType": "algorithm_task",
  "workloadId": "123",
  "requirements": {
    "capabilities": ["algorithm_realtime"],
    "preferGpu": true,
    "requireNfsMount": true,
    "executor": "cpp",
    "minFreeVramMb": 4096,
    "minRuntimeVersion": "1.0.0",
    "requireSchedulable": true
  }
}
```

响应增加：

```json
{
  "nodeId": 5,
  "schedulabilityEvidence": {
    "algorithm_realtime": "ready",
    "runtime_version": "1.2.0",
    "nfs_mount_ready": true
  }
}
```

### 8.3 WebSocket 事件

```json
{
  "type": "capability_changed",
  "nodeId": 5,
  "changes": [
    {"capability": "srs_live", "from": "ready", "to": "unavailable", "reason": "port 1935 closed"}
  ],
  "timestamp": "..."
}
```

---

## 9. 与现有模块集成

### 9.1 NodeSchedulerServiceImpl

`matchRequirements()` 增强：

```java
// 伪代码
private boolean matchRequirements(ComputeNodeDO node, NodeSchedulerAllocateReqVO req) {
    // ... 现有 role/capabilities/nfs/gpu 逻辑 ...

    // Sentinel 增强
    if (req.getRequirements().getRequireSchedulable() != Boolean.FALSE) {
        Map<String, String> schedulable = sentinelService.getSchedulableCapabilities(node.getId());
        for (String cap : resolveRequiredCapabilities(reqVO)) {
            if (!"ready".equals(schedulable.get(cap)) && !"degraded".equals(schedulable.get(cap))) {
                return false;
            }
        }
        if (req.getMinFreeVramMb() != null) {
            if (!sentinelService.hasFreeVram(node.getId(), req.getMinFreeVramMb())) {
                return false;
            }
        }
        if ("cpp".equals(req.getExecutor())) {
            if (!sentinelService.isRuntimeReady(node.getId(), req.getMinRuntimeVersion())) {
                return false;
            }
        }
    }
    return true;
}
```

### 9.2 NodeCommandServiceImpl.deployWorkload()

部署前调用 `PreDeployValidator`：

1. Agent `POST /sentinel/validate`
2. 失败 → `release(workload)` + 抛出可重调度异常 + 临时 `temp_blocked` 该 capability 5min

### 9.3 VIDEO / AI 编排层

| 模块 | 改动 |
|------|------|
| `train_launcher_service.py` | `allocate_node` 增加 `minFreeVramMb`、`requireSchedulable=true` |
| `algorithm_task_launcher_service.py` | executor=cpp 时传 `minRuntimeVersion` |
| `stream_forward_launcher_service.py` | 依赖 Sentinel 的 `srs_live` 端口探测，减少纯静态过滤 |
| `llm_node_capacity.py` | 迁入 Sentinel 校验层或改为读 `schedulable` API |
| `node_client.py`（VIDEO/AI） | 统一封装 requirements 构造 |

### 9.4 健康检查与 Failover 统一

现有 failover 分散在：

- `NodeHealthServiceImpl`（offline）
- `stream_forward_health_service.py`
- `algorithm_task_launcher_service.py`

Sentinel 提供统一信号：

- `operational_state=degraded` + capability unavailable → 触发与现有 failover 相同的分片迁移逻辑
- 编排层订阅 `capability_changed` WS 或轮询 `schedulable` API，**主动迁移**而非等心跳超时

---

## 10. 主动降级与恢复

### 10.1 资源过载降级

| 条件 | 动作 |
|------|------|
| CPU ≥ 90% 持续 3 个心跳 | `algorithm_*`、`model_train` 临时 unavailable |
| 显存使用 ≥ 95% | `llm_inference`、`model_train` unavailable |
| `activeTasks >= maxTaskCount` | 全部计算类 unavailable（现有逻辑保留） |
| NFS 挂载丢失 | 所有 `require_nfs_mount` 能力 unavailable |

恢复：条件消失且 L0 探测通过 → 下一心跳自动恢复，无需人工干预。

### 10.2 连续部署失败

同一节点同一 capability 连续 3 次 deploy 失败 → `temp_blocked` 30min，写入 `node_capability_probe_log`。

---

## 11. WEB 界面

路径：`WEB/src/views/node/` 扩展

### 11.1 节点详情 — Sentinel 面板

- **环境画像卡片**：OS / GPU / Agent / RUNTIME / NFS / 网络
- **能力矩阵表**：

| 能力 | 声明 | 实测 | 可调度 | 最后探测 | 操作 |
|------|------|------|--------|---------|------|
| algorithm_realtime | ✓ | ready | ✓ | 10s 前 | 重新探测 |
| srs_live | ✓ | unavailable | ✗ | 5min 前 | 查看原因 |

- **探测日志**：最近 N 条 state 变更

### 11.2 集群概览

- 泳道卡片增加「能力健康度」徽章：绿/黄/红
- 筛选：仅显示某 capability schedulable 的节点

---

## 12. 实施路线

### Phase 1 — 基础感知（2–3 周）

- [ ] `sentinel_probe.py` L0/L1 探测（RUNTIME 存在、NFS、GPU、SRS 端口）
- [ ] 心跳 payload 扩展 + `SentinelAggregator` 落库
- [ ] `node_capability_snapshot` 表
- [ ] 调度器读取 `schedulable_capabilities`（feature flag：`sentinel.scheduling.enabled=false` 默认）

### Phase 2 — 调度闭环（2 周）

- [ ] CapabilityRegistry YAML
- [ ] `SchedulabilityFilter` + `minFreeVramMb` + `minRuntimeVersion`
- [ ] PreDeployValidator
- [ ] VIDEO/AI `node_client` 适配

### Phase 3 — 可观测与降级（1–2 周）

- [ ] WEB Sentinel 面板
- [ ] WS `capability_changed`
- [ ] 资源过载自动降级
- [ ] failover 与 Sentinel 信号联动

### Phase 4 — 深度探测与治理（持续）

- [ ] L2 试跑探针（RUNTIME self-test、RTMP loopback）
- [ ] Bundle 版本追踪与分发后自动 resync
- [ ] 探测日志与告警规则
- [ ] 带宽估算（替换当前 `bandwidthMbps=0`）

---

## 13. 兼容性与迁移

| 场景 | 策略 |
|------|------|
| 旧版 Agent 无 `sentinel` 字段 | `capability_stale=true`；调度回退到现有静态 `capabilities` 逻辑（可配置） |
| 灰度开启 | `sentinel.scheduling.enabled` 按控制面 / 节点标签渐进 |
| 数据迁移 | 首次部署后对所有 online 节点触发 L1 resync |

---

## 14. 风险与对策

| 风险 | 对策 |
|------|------|
| L2 探测影响生产（试跑占 GPU） | 仅手动 / deploy 失败 / 低峰 Scheduler 触发；加互斥锁 |
| 探测结果与心跳不同步 | schedulable 缓存 TTL ≤ 心跳间隔 × 2 |
| 注册表与代码 capability 字符串不一致 | 启动时校验 Registry ↔ 枚举；CI 单测 |
| 多 Agent 共用 NODE_ID | 沿用现有 hostname/指纹冲突检测 |

---

## 15. 附录：与现有代码映射

| 现有模块 | 路径 | Sentinel 关系 |
|---------|------|--------------|
| Agent 心跳 | `NODE/run_agent.py` | 扩展 payload，调用 `sentinel_probe` |
| Agent HTTP | `NODE/agent_server.py` | 新增 `/sentinel/*` |
| 调度器 | `NodeSchedulerServiceImpl.java` | 集成 SchedulabilityFilter |
| 节点 CRUD | `ComputeNodeServiceImpl.java` | `defaultCapabilities()` 变为声明源 |
| 心跳处理 | `NodeAgentServiceImpl.java` | 调用 SentinelAggregator |
| 离线检测 | `NodeHealthServiceImpl.java` | 联动 operational_state |
| 训练调度 | `AI/.../train_launcher_service.py` | requirements 增强 |
| 算法分片 | `VIDEO/.../algorithm_task_cluster_service.py` | 分片前 schedulable 查询 |
| 推流转发 | `VIDEO/.../stream_forward_launcher_service.py` | srs_live 实测 |
| LLM 显存 | `AI/.../llm_node_capacity.py` | 收敛到 Sentinel |
| 前端指标 | `WEB/.../clusterMetrics.ts` | 扩展 capability 维度 |

---

## 16. 开放问题（待评审）

1. **Sentinel 是否独立进程**：首期嵌入 Agent，后续高负载节点是否拆 sidecar？
2. **degraded 是否参与调度**：建议 degraded 可调度但打分 ×0.5，需产品确认。
3. **跨控制面节点**：联邦场景下 schedulable 是否同步到 Peer 控制面？
4. **探测凭证**：SRS/EMQX API 探测是否需要节点级 secret 配置？

---

*文档结束。评审通过后进入 Phase 1 任务拆分。*
