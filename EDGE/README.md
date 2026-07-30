# EasyAIoT EDGE 模块

第八核心模块：**无限联邦边缘集群模式**——无界面、纯命令行边缘算法运行时。内存占用约 **512MB**，**Ceph 边缘 0 硬盘占用**，一行命令把普通开发板直接智能化，算力可铺开部署并汇聚上云；通过 MQTT/EMQX 无限扩容，算法任务从 VIDEO 控制面抽离，边缘侧 **不落本地业务盘、不直传 MinIO**。

## 你只需配置 NODE；有多个 SRS 时再指定媒体节点

```bash
# edge.env
EDGE_NODE_URL=http://<iot-node控制面主机>:48080
# 可选：多媒体节点时手动指定 AI 推流目标（控制台下拉会生成命令）
# python -m edge config set-srs --host <SRS主机> --rtmp-port 1935 --http-port 8080 --api-port 1985
```

其余由控制面自动下发：

- EMQX / MQTT broker 列表（有序，支持故障从头探测）
- MQTT 租户 / 用户名 / 密码 / clientId
- Ceph 热缓冲路径（`ALERT_IMAGES_DIR` 等）
- 算法 Topic 约定、节点 ID / Agent Token

`set-srs` 写入的是**中心侧已部署**的 SRS 地址，边缘不在本地再装一套流媒体。

## 快速开始

```bash
cd EDGE
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1. 写入 NODE 地址（必配）
python -m edge config set-node http://10.0.0.10:48080

# 1b. 多 SRS 时指定本台推流目标（控制台下拉生成）
# python -m edge config set-srs --host 10.0.0.20 --rtmp-port 1935 --http-port 8080 --api-port 1985

# 2. 向控制面登记本机并拉取运行时配置（自动）
python -m edge enroll

# 3. 前台常驻（订阅 MQTT 任务指令，无 UI）
python -m edge run

# 4. 另一终端：命令下发启停（不经 WEB「算法任务」Tab）
python -m edge task start --task-id 900001 --type realtime
python -m edge task stop --task-id 900001
# 单机冒烟（不经 MQTT）可加 --local

# 常用命令
python -m edge status
python -m edge pull-config
python -m edge stop   # 优雅退出本机 edge run
```

生产环境建议在控制面配置 `easyaiot.edge.join-token`，边缘侧同步：

```bash
python -m edge config set-join-token <与控制面一致的令牌>
```

私网实验室可开启控制面 `easyaiot.edge.allow-open-enroll=true`，此时仅需 `EDGE_NODE_URL`。

## 设计原则

| 项 | 说明 |
|----|------|
| 无界面 | 全部 CLI / systemd，不提供 WEB |
| 全 MQTT | 启停/心跳/告警/后处理走算法总线 |
| 命令下发 | `edge task start/stop` 发 `mqtt/iot-algo-task-cmd`；与算法任务 Tab 隔离 |
| 不存储 | 业务图写 Ceph 共享路径；归档由中心 sink 完成 |
| 无限集群 | 多 EDGE 节点共享同一 EMQX 集群 |
| 单配置入口 | 必配 NODE；多 SRS 时另 `set-srs` |
| 与 VIDEO 解耦 | 执行包在 `EDGE/runtime`；VIDEO `algorithm_task`/`alert` **无** `edge_node_*` 字段 |

## 目录

```
EDGE/
  edge/           # CLI 与运行时（enroll / mqtt / workload / task）
  runtime/        # 边缘算法执行包（自有；VIDEO 仅可选种子）
  scripts/        # sync_runtime_from_video.sh（种子 + overlays）
  edge.env.example
  requirements.txt
```

算法包说明：[`runtime/README.md`](runtime/README.md)
