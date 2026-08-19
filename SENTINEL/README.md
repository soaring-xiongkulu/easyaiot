# SENTINEL — 集群节点观察者 Agent

> **维度**：跟着每台调度节点走  
> **模式**：按勾选功能探测 + 本机在线补齐节点环境（经网关进入 NODE 管理面）

后续智能体请以代码入口与 `SENTINEL/registry/` 为准。内部交接文档已移除，如需对齐开发请联系负责人。

## 产品模型

1. **功能驱动**：`NODE_FUNCTIONS`（如 `algorithm,forward,live`）决定期望组件，不再使用 compute/gpu/hybrid 角色。
2. **节点纳管后安装 Sentinel**：NODE 提交后 SSH 同步 Agent 并启动，按功能扫描。
3. **哨兵主动扫描**：首次 L1，之后心跳 L0 + 周期 L1。
4. **经网关上报表**：`CONTROL_PLANE_URL=http://<gateway>:48080/admin-api/node/agent`。

```
新增节点 ──全量离线包──▶ 目标机 /opt/easyaiot/sentinel-agent
        │
        ▼ systemd 启动
  SENTINEL 扫描组件 ──POST /heartbeat──▶ Gateway ──▶ NODE
        ▲                                      │
        └── 缺组件可请求 /sentinel/remediate ◀──┘
```

## 职责

| 能力 | 说明 |
|------|------|
| **离线安装** | `pip-wheels` + `install.sh`，断网节点可装 |
| **组件探测** | `sentinel/` 扫描 runtime / CUDA / SRS / ffmpeg / bundle / NFS 挂载等 |
| **可调度上报** | 心跳 `schedulableCapabilities` 经网关进入 NODE |
| **任务执行** | 接收 NODE deploy 指令启动工作负载 |
| **自愈请求** | 缺失期望组件时请求 NODE Remediator 分发 |

## 启动

```bash
cd SENTINEL
cp agent.env.example agent.env   # NODE_ID / AGENT_TOKEN / CONTROL_PLANE_URL（网关）
./install.sh install
# 或开发态：
python3 run_sentinel.py
```

远程默认目录：`/opt/easyaiot/sentinel-agent`

## 目录

```
SENTINEL/
├── run_sentinel.py      # 主进程：探测 + 心跳上报
├── agent_server.py      # HTTP :9100
├── sentinel/            # 组件探测 + 推导
├── registry/            # components.yaml / capabilities.yaml
├── pip-wheels/          # 离线依赖（export_pip_wheels.sh 生成）
└── install.sh
```
