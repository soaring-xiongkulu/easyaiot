# 云—Edge MQTT 联调

无需现场设备，使用 `demo-simulator` 采集器验证完整链路。

## 一键联调

```bash
cd /projects/new/easyaiot
bash EDGE/demo/run_e2e.sh
```

脚本会：

1. 启动 Mosquitto（端口 **18883**，避免与平台 EMQX 1883 冲突）
2. 启动 Edge Host
3. 运行 `cloud_simulator.py`：下发配置 → 等待属性上报 → 下发属性设置 → 等待回执

## 对接已有 EasyAIoT 平台 EMQX

平台侧配置、上行/下行数据流、验收清单见 **[docs/PLATFORM_INTEGRATION.md](../docs/PLATFORM_INTEGRATION.md)**。

```bash
# 一键冒烟（连接平台 EMQX 1883，需预先创建 GATEWAY/SUBSET 产品）
export EDGE_PRODUCT=edge-gateway-product
export EDGE_GATEWAY=gateway-demo-001
export EDGE_SUBSET_PRODUCT=edge-subset-product
bash EDGE/demo/run_platform_smoke.sh
```

或使用 `run_e2e.sh --skip-mqtt`（不校验 SUBSET 产品字段）：

```bash
export EDGE_MQTT_HOST=127.0.0.1
export EDGE_MQTT_PORT=1883
export EDGE_PRODUCT=你的网关产品标识
export EDGE_GATEWAY=你的网关设备标识
bash EDGE/demo/run_e2e.sh --skip-mqtt
```

## 手动分步

```bash
# 1. 启动 demo MQTT（可选）
docker compose -f EDGE/demo/docker-compose.yml up -d

# 2. 订阅上行
EDGE_MQTT_PORT=18883 bash EDGE/demo/mqtt_subscribe_uplink.sh

# 3. 启动 Edge
export DOTNET_ENVIRONMENT=E2E
dotnet run --project EDGE/src/EasyAIoT.Edge.Host -c Release

# 4. 下发配置（另一终端）
EDGE_MQTT_PORT=18883 bash EDGE/demo/mqtt_publish_config.sh
```

## 文件说明

| 文件 | 作用 |
|------|------|
| `run_platform_smoke.sh` | 对接平台 EMQX 的冒烟脚本 |
| `cloud_simulator.py` | 模拟云平台 MQTT 下行与上行验收 |
| `payloads/config_push.json` | `thing.config.push` 示例 |
| `payloads/property_set.json` | `thing.property.set` 示例 |
| `appsettings.e2e.json` | Edge 联调 MQTT/网关标识 |

## 验收标准

- 收到 ≥2 条属性上报（`/sub/property/upstream/report` 或 `/property/upstream/report`）
- 收到属性设置回执，且 `code` 为 `0`
