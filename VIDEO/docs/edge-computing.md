# 边缘计算统管协议

边缘计算属于 VIDEO 业务域，WEB 以独立一级菜单呈现；NODE 不参与盒子遥测，Kafka 也不在这条链路中。

```text
RK3588 / BM1688 / 其他盒子
          │ MQTT QoS 1
          ▼
        EMQX
          │ 共享订阅
          ▼
       iot-sink ── 鉴权 / HMAC / 时间窗 / 去重 / 归一化 / 直接落库
          │
          ▼
      iot-video20
          │
          ▼
       VIDEO API ──► WEB「边缘计算」
```

## 通用硬件身份

协议不把 RK3588 写死为唯一芯片。盒子通过以下字段声明能力：

- `hardwareProvider`：`rockchip`、`sophon` 等；
- `socModel`：`RK3588`、`BM1688` 等；
- `acceleratorType`：`npu`、`tpu`、`gpu`；
- `acceleratorCount`：逻辑加速单元数量；
- `runtimeTarget`：`rknn-rk3588`、`sophon-bm1688` 等；
- `acceleratorInfo`、`pipelines`：芯片适配器归一化后的运行快照。

新增芯片只需要实现盒子 Agent 适配器并继续输出该契约，平台表结构和页面无需复制。

## 纳管与 MQTT

一次性纳管接口为 `POST /video/edge/enroll`。若中心设置 `EDGE_ENROLL_TOKEN`，盒子必须同时提供相同的 `joinToken`。响应返回节点独立的 MQTT 用户名、Client ID、token 和 Topic：

```text
mqtt/iot-edge-node/{nodeId}/heartbeat
mqtt/iot-edge-node/{nodeId}/status
mqtt/iot-edge-node/{nodeId}/command
mqtt/iot-edge-node/{nodeId}/command-ack
```

持续遥测只使用 MQTT。消息信封版本为 `easyaiot.edge.telemetry/v1`，`payload` 是原始 JSON 字符串；签名原文为以下字段以换行拼接：

```text
specVersion
messageType
nodeId
messageId
sentAt
payload
```

签名算法为节点 token 的 HMAC-SHA256 十六进制值。iot-sink 还会检查 MQTT 登录身份、Topic 与 nodeId 一致性、120 秒时间窗，以及 `(nodeId, messageId)` 唯一性。

## FRP 边界

FRP 是可选的人工访问通道，不承载心跳与指标：

- `service` 隧道暴露 Agent 只读状态入口；
- `ssh` 隧道独立暴露盒子 SSH；
- FRP 关闭或短时断线不影响 MQTT 统管；
- FRP token、节点 token 和 SSH 凭据不通过管理 API 返回给 WEB。
