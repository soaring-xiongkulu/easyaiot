# EasyAIoT EDGE — C# 边缘采集模块

独立边缘采集运行时：多协议 C# 采集器插件、本地调度、配置驱动解析、MQTT 对接 EasyAIoT 云平台。

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

| 方向 | Topic |
|------|-------|
| 网关上报属性 | `/iot/{product}/{gateway}/property/upstream/report` |
| 网关代报子设备 | `/iot/{product}/{gateway}/sub/property/upstream/report` |
| 云端下发配置 | `/iot/{product}/{gateway}/config/downstream/push` |
| 云端设置属性 | `/iot/{product}/{gateway}/property/downstream/desired/set` |

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
