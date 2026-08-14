# EasyAIoT EDGE — C# 边缘采集模块

独立边缘采集运行时：多协议 C# 采集器插件、本地调度、配置驱动解析、MQTT 对接 EasyAIoT 云平台。

EDGE **没有单独的设备页面**。它在现场以 **GATEWAY（网关设备）** 身份接入，采集结果经 MQTT 进入 DEVICE/`iot-sink`，在 WEB「设备管理」里展现为该网关及其 SUBSET 子设备（在线状态、运行状态/影子、历史曲线、属性下发）。

## 与平台「设备管理网关」的关系

设备管理里的「网关」是云上的 **产品/设备类型（GATEWAY + SUBSET 拓扑）**：负责建档、影子、绑定、下发与告警。谁来当这台网关，可以是会 MQTT 的第三方网关，也可以是本模块。

**EDGE 就是现场去当这台网关的运行时**：挂在 RS-485 / PLC 旁本地采集，再按平台网关 Topic 上云。两者不是两套系统——EDGE 对上的就是设备管理现有网关角色。

另有一条容易混淆的路径：**iot-sink 可在云端直接轮询 Modbus/OPC UA**（设备详情会出现「点位管理 / 点位影子」）。协议看起来像，采集发生的位置不同：

| | 设备管理「网关」 | 云端工业轮询（iot-sink） | EDGE |
|---|---|---|---|
| 是什么 | 逻辑角色与拓扑 | 云进程主动采现场设备 | 现场独立部署的采集进程 |
| 跑在哪 | DEVICE / WEB | 机房 / 与平台同网 | 工控机、边缘盒子、串口旁 |
| 数据落哪 | 设备管理 | 同一套设备管理 | **同一套设备管理**（以 GATEWAY 出现） |
| 适用 | 纳管、展现、下发 | 平台能直接够到 PLC/电表（同网、VPN） | OT 隔离、仅有串口、云够不到现场——现场只出 MQTT |

`DEVICE/iot-gateway` 是 HTTP API 网关，与物联网网关不是一回事。

## 能否作为真正的现场网关？

**核心数据面已经可以对上平台现有网关**：网关自身属性上下行、子设备属性代报（透传）、云端配置下发、属性写值下行。现场仪表不必直连平台，由 EDGE 汇聚后上云，子设备首次上报可由平台自动建档并挂到该网关下。

完整网关协议面（拓扑主动申报、子设备事件/服务透传、OTA 等）尚未齐，见下表。工业采集场景以属性读写为主，当前即可作为现场网关使用；若要对齐平台网关 Topic 全量能力，仍需后续补齐。

| 能力 | 平台网关语义 | EDGE 现状 |
|------|----------------|-----------|
| 网关属性上行 | `property/upstream/report` | 已实现 |
| 子设备属性代报 | `sub/property/upstream/report` | 已实现（payload 带子设备产品/设备标识，平台自动创建并绑定） |
| 网关属性下行 + 回执 | `property/downstream/desired/set` → `…/desired/set/ack` | 已实现 |
| 子设备属性下行透传 | `sub/property/downstream/desired/set` | 已订阅并执行写值；回执暂走网关 ack Topic，尚未按子设备精确路由到对应采集任务 |
| 云端配置下发 | `config/downstream/push` | 已实现 |
| 拓扑添加 / 删除 / 状态 | `topo/upstream/add|delete|status` | 未实现（可用首次属性代报触发平台自动建档） |
| 子设备事件代报 | `sub/event/upstream/report` | 未实现 |
| 子设备服务透传 | `sub/service/downstream/invoke` 及响应 | 未实现 |
| NTP / OTA / 标签 / 日志 / 广播 | 对应 Topic | 未实现 |

## 模块结构

```
EDGE/
├── EasyAIoT.Edge.sln
├── pack_linux.sh                 # 打包脚本（x86_64 / arm64）
├── src/
│   ├── EasyAIoT.Edge.Abstractions/
│   ├── EasyAIoT.Edge.Hardware/
│   ├── EasyAIoT.Edge.Mqtt/
│   ├── EasyAIoT.Edge.Core/
│   ├── EasyAIoT.Edge.Collectors.Modbus/   # modbus-rtu、modbus-tcp
│   ├── EasyAIoT.Edge.Collectors.OpcUa/
│   └── EasyAIoT.Edge.Host/
└── configs/
    ├── devices.example.json
    └── cloud-config-push.example.json
```

## 采集器

| collectorId | 协议 |
|-------------|------|
| `modbus-rtu` | Modbus RTU（RS485/串口） |
| `modbus-tcp` | Modbus TCP |
| `opc-ua` | OPC UA |

## 快速开始

```bash
cd EDGE
dotnet build EasyAIoT.Edge.sln -c Release
dotnet run --project src/EasyAIoT.Edge.Host -c Release
```

## 配置

- `appsettings.json`：`Edge.Gateway`、`Edge.Mqtt`
- `data/device-jobs.json`：本地采集任务
- 云端 MQTT `thing.config.push` 可覆盖任务列表（见 `configs/cloud-config-push.example.json`）

## MQTT Topic

Topic 中 `{product}` / `{gateway}` 为 **网关产品标识** 与 **网关设备标识**，须与设备管理中已创建的 GATEWAY 设备一致。

| 方向 | Topic | 状态 |
|------|-------|------|
| 网关上报属性 | `/iot/{product}/{gateway}/property/upstream/report` | 已实现 |
| 网关代报子设备属性 | `/iot/{product}/{gateway}/sub/property/upstream/report` | 已实现 |
| 云端下发配置 | `/iot/{product}/{gateway}/config/downstream/push` | 已实现 |
| 云端设置网关属性 | `/iot/{product}/{gateway}/property/downstream/desired/set` | 已实现 |
| 云端经网关设置子设备属性 | `/iot/{product}/{gateway}/sub/property/downstream/desired/set` | 已订阅 |
| 属性设置回执 | `/iot/{product}/{gateway}/property/upstream/desired/set/ack` | 已实现 |

## 云—边联调 Demo

```bash
bash EDGE/demo/run_e2e.sh
```

详见 [demo/README.md](demo/README.md)。对接 EasyAIoT 云平台（iot-sink 上行入库、属性下发）见 [docs/PLATFORM_INTEGRATION.md](docs/PLATFORM_INTEGRATION.md)。

## 打包发布

```bash
# 本机架构
bash EDGE/pack_linux.sh

# 指定 ARM64（交叉发布需安装对应 runtime）
EDGE_ARCH=arm64 bash EDGE/pack_linux.sh
```

产出：`EDGE/.bundle-edge/{arch}/easyaiot-edge-{arch}.tar.gz`

## 扩展采集器

1. 实现 `ICollector`
2. 在 Host `Program.cs` 注册 `ICollector`
3. 任务配置中指定 `collectorId`
