# RUNTIME-RK3588

`RUNTIME-RK3588` 是 EasyAIoT 为 **Rockchip RK3588 边缘 AI 盒子量身定制**的执行模块，不是通用 `RUNTIME` 的兼容构建。它强制使用 RK3588 的 MPP 视频引擎、RGA 图像加速器和三核 NPU；设备、驱动或 SDK 任一不满足时直接拒绝构建或启动，不会切换 ONNX Runtime、CPU 推理、软件解码或 `libx264`。

## 硬件与项目价值

![RK3588 盒子前面板与无线扩展](../.images/rk3588/rk3588-front-wireless.jpg)

前面板提供 Wi-Fi 与多路 4G/5G 天线位，适合弱网、移动点位和蜂窝备链场景。视频在盒子本地完成解码与推理，只回传检测结果、告警和按需画面，可降低上行带宽与告警时延。

![RK3588 边缘 AI 盒子](../.images/rk3588/rk3588-box.jpg)

大面积金属鳍片机身有利于持续视频解码和 NPU 推理时散热。运行时通过固定缓冲池、固定任务队列和三核分配控制峰值资源，避免长时间运行后队列与内存持续增长。

![RK3588 盒子接口与双网口](../.images/rk3588/rk3588-io-panel.jpg)

双 RJ45、HDMI IN/OUT、USB、Type-C 和 SIM 等接口让盒子可同时连接摄像头侧网络、平台侧网络及本地显示/存储设备，适合园区、门店、工业和交通现场的一体化部署。

RK3588 官方规格包括 4×Cortex-A76 + 4×Cortex-A55、Mali-G610、2D 图像加速器、最高 8K 编解码能力，以及支持 INT4/INT8/INT16/FP16/BF16/TF32 的 6 TOPS 三核 NPU。本模块围绕这些片上单元建立专用数据通路，不把 RK3588 当作普通 ARM CPU 使用。

## 硬件流水线

模块的系统架构如下：

![RK3588 系统架构图](../.images/rk3588/rk3588-architecture.jpg)

压缩包从输入到输出的具体数据通路如下：

```text
RTSP/文件
   │ FFmpeg 仅解复用压缩包
   ▼
MPP 硬解 ──► 固定数量 NV12 DMA-BUF ──────────────┐
   │                                             │
   ├──► RGA 缩放/颜色转换 ─► RKNN 预分配输入 FD ─► 三核 NPU
   │                                             │
   └──► RGA 转 BGR（画框/告警图）──► RGA NV12 ─► h264_rkmpp ─► RTMP
```

关键实现：

- MPP 通过外部缓冲组输出 NV12 DMA-BUF，缓冲数量由 `mpp_buffer_count` 限制。
- RGA 导入的 DMA-BUF 与 RKNN 输入 FD 按生命周期缓存复用，不逐帧 `import/release`。
- RKNN 输入、9 个 INT8 输出张量启动时一次分配并通过 `rknn_set_io_mem` 绑定；输入由 RGA 直接写入，YOLOv8 DFL 后处理直接读取原生 `NC1HWC2`，不逐帧转成 FP32。
- 三个工作实例固定绑定 `RKNN_NPU_CORE_0/1/2`，相同模型启用权重内存共享。
- 每个 NPU 核拥有独立任务环和完成环，调度器优先投递到最短 lane；完成结果由单独汇聚线程发布，避免三核争抢共享任务锁。
- MPP 帧环、每核任务环、每核完成环和告警结果环均为固定容量；满载时淘汰最旧帧并计数，不阻塞拉流、不无限堆积。
- 纯推理模式不创建 BGR 帧池，也不执行显示链路颜色转换；只有启用告警取证或 RTMP 输出时才分配固定 BGR 池。
- `snap` 与 `patrol` 同样使用 MPP/RGA，不调用 OpenCV `VideoCapture` 软件解码。
- RTMP 仅使用 `h264_rkmpp`；编码器缺失时失败，不回退 `libx264`。

“零内存”在这里指**零拷贝优先、零无界增长、零逐帧大块分配**，并不表示进程占用 0 字节内存。压缩包进入 MPP 时仍有一次有界拷贝，画框和告警图片也需要固定 BGR 缓冲。

实现遵循 Rockchip MPP、RKNN Runtime 2 与 RGA 的官方接口约定，并严格校验硬件节点、驱动、张量布局和编解码能力。

## 强制运行条件

- RK3588/RK3588S，Linux aarch64；
- 可用节点：`/dev/rknpu*`、`/dev/rga*`、MPP/VPU 节点、`/dev/dri/renderD128`；
- RKNN Runtime 2、librga、Rockchip MPP；
- FFmpeg/libavformat，以及带 `h264_rkmpp` 编码器的 Rockchip FFmpeg；
- OpenCV 只用于检测框、区域和告警图片，不承担解码、缩放预处理或推理。

## 独立一键部署

推理运行时本身不依赖 WEB、AI、VIDEO、MQTT 或 Docker；离线现场可以完全独立运行。需要中心统管时，只额外启用同一清单里的轻量 MQTT Agent，盒子端仍不安装平台服务。先从示例得到一份任务清单，只需维护这一个文件：

```bash
cp RUNTIME-RK3588/config/standalone.tasks.example.json ./rk3588.tasks.json
# 编辑 models 与 tasks 后，可先做零改动校验，再一键安装
bash .scripts/docker/install_linux.sh rk3588 config-check ./rk3588.tasks.json
sudo bash .scripts/docker/install_linux.sh rk3588 install ./rk3588.tasks.json
```

也可以把 `RUNTIME-RK3588` 当作 `build-runtime` 的模块单独编译或清理。它是板端原生运行时，不走 Docker 镜像与镜像仓库：

```bash
# 仅编译 RUNTIME-RK3588（调用 RUNTIME-RK3588/install_linux.sh build）
sudo bash .scripts/docker/install_linux.sh build-runtime RUNTIME-RK3588

# 仅清理本机编译产物 build/（--dry-run 可预览；--dist/--cache 可一并清理导出与离线缓存）
sudo bash .scripts/docker/install_linux.sh clean-build-runtime RUNTIME-RK3588 --dry-run
```

任务清单同时决定是否接入平台、是否打开内网穿透：

```json
{
  "control_plane": {
    "enabled": true,
    "url": "http://平台IP:48080/admin-api/video/edge",
    "join_token": "中心平台配置的 EDGE_ENROLL_TOKEN",
    "node_name": "园区北区-RK3588-01"
  },
  "remote_access": {
    "enabled": false,
    "provider": "frp"
  }
}
```

- `control_plane.enabled=true`：安装器自动注册 MQTT Agent，首次通过 VIDEO 完成纳管，此后心跳、CPU/内存/温度、NPU、推理管线和 FRP 状态只走 MQTT；WEB 的独立“边缘计算”菜单会自动出现盒子，不需要手工建节点。
- 遥测链路固定为 `RK3588 → EMQX → iot-sink（鉴权、HMAC 验签、协议归一化、直接写 iot-video20）→ VIDEO / WEB`，不绕 Kafka，也不进入 NODE 模块。
- `remote_access.enabled=false`：不下载、不安装、不启动 frpc；盒子只主动连接 MQTT，不暴露任何公网端口。
- `remote_access.enabled=true`：一键安装并校验 arm64 frpc；`service.enabled` 与 `ssh.enabled` 分别控制状态服务和 SSH 隧道。FRP 只解决“从平台访问/登录盒子”，不承载心跳和指标，因此隧道短暂中断不会破坏 MQTT 统管。
- MQTT 除 Broker 登录鉴权外，每条消息还使用节点独立 token 做 HMAC-SHA256，并校验时间窗、Topic/nodeId 与 messageId 去重；FRP token、SSH 凭据不会进入 WEB 返回值。

清单与平台 `RUNTIME` 的运行约定一致：

- `models` 集中登记 RKNN 模型、类别文件与可选业务模型 ID；模型安装一次，可被任意任务复用；
- `tasks` 每一项代表一路 RTSP，`models` 数组决定该路同时运行哪些模型；增加视频流只需增加任务；
- 每路实时视频生成独立 INI、控制端口和受监管进程，某一路故障不会把其他路一起带走；
- 全部路径、模型引用、任务 ID 和控制端口先校验后安装，避免部署到一半才发现配置错误。

脚本随后完成硬件与驱动预检、本机编译、共享模型安装、逐路配置生成、systemd 模板实例注册与启动，并逐路等待 `/health` 验收 MPP、RGA、RKNN 硬件链路。启用平台纳管时还会安装 MQTT Agent；启用 FRP 时才会下载、校验并注册 frpc。没有 systemd 时，每路推理任务自动使用独立 PID 与日志。交互菜单只需选择任务清单，不会再要求把一条 RTSP 和一个模型塞进环境变量。

```bash
bash .scripts/docker/install_linux.sh rk3588 list
bash .scripts/docker/install_linux.sh rk3588 status
bash .scripts/docker/install_linux.sh rk3588 logs north-gate
bash .scripts/docker/install_linux.sh rk3588 verify north-gate
bash .scripts/docker/install_linux.sh rk3588 restart north-gate
```

不写任务 ID 时命令作用于全部视频流；写任务 ID 时只处理一路。修改已安装的 `/etc/easyaiot/runtime-rk3588/tasks.json` 后执行 `rk3588 update` 即可重编排。卸载只移除服务模板与程序，默认保留任务清单、逐路配置、模型和日志，避免误删现场数据。旧版单流环境变量仍会自动转换为一条任务，仅用于向后兼容。

交叉编译时必须提供 aarch64 RK3588 工具链，并通过 `ROCKCHIP_SDK_ROOT` 指向包含 RKNN/RGA/MPP 头文件和库的 SDK sysroot。CMake 在非 aarch64 或依赖缺失时会直接报错。

## RKNN 模型

运行时只接受 **Rockchip Model Zoo 优化版 YOLOv8n INT8 RKNN**。它必须是 1 输入、9 输出：三个尺度各包含 DFL 框、分类分数和分数和张量。普通 Ultralytics 单输出 ONNX/RKNN、FP 模型以及其他输出契约会在启动时被拒绝，避免“能运行但结果错”或悄悄走低性能路径。

在安装 RKNN-Toolkit2 的转换机上下载官方优化 ONNX 并转换：

```bash
./RUNTIME-RK3588/scripts/prepare_yolov8n_rk3588.sh \
  calibration.txt /opt/models/yolov8n-rk3588-int8.rknn
```

`calibration.txt` 每行一个有代表性的现场图片路径。脚本采用 Rockchip Model Zoo 的 YOLOv8 九输出优化模型约定，目标固定为 `rk3588`、INT8、优化等级 3，并在转换前验证 1 输入/9 输出契约。

## 配置

```ini
[ai]
enable=true
model_path=/opt/easyaiot/RUNTIME-RK3588/models/yolov8n-rk3588-int8.rknn
classes_path=/opt/easyaiot/RUNTIME-RK3588/models/coco.names
frame_skip=1

[rk3588]
npu_workers=3
task_queue_depth=2
frame_pool_size=6
mpp_buffer_count=8
use_sram=true
enable_perf_query=false
```

资源参数都带硬上限：NPU worker 为 1–3，`task_queue_depth` 是**每个 NPU lane** 的环深度（1–16），帧池 3–32，MPP 缓冲 4–32。实时场景建议从 `3/2/6/8` 开始；`enable_perf_query=false` 可避免逐帧性能查询影响极限吞吐，吞吐计数本身仍会持续统计。

`GET /health` 会返回 `infer_ep=rknn-rk3588-3core-ring`、`decode_ep=mpp-rk3588`、`encode_ep=h264_rkmpp`，以及 `npu_throughput_fps`、`npu_completed`、NPU 采样耗时与环队列丢帧计数。任何字段出现通用 CPU 后端都应视为部署错误；本模块本身没有这些回退代码。

## 150 FPS 真机基准

构建会同时生成 `RUNTIME-RK3588-BENCH`。它用同一套 RGA 预处理、三核线程池、原生 INT8 后处理和多环队列持续压测，默认门槛是 150 FPS：

```bash
/opt/easyaiot/RUNTIME-RK3588/bin/RUNTIME-RK3588-BENCH \
  /opt/easyaiot/RUNTIME-RK3588/models/yolov8n-rk3588-int8.rknn \
  test.jpg 30 150 \
  /opt/easyaiot/RUNTIME-RK3588/models/coco.names
```

只有输出 `BENCH_PASS` 且 `dropped=0` 才通过。这里的 150 FPS 是三核 NPU 的**聚合推理吞吐验收目标**，不是把 25 FPS 摄像头虚构成 150 FPS，也不是对任意模型、频率、温度和系统镜像的无条件承诺。真机结果低于目标时应先检查 NPU/DDR 频率策略、RKNN 驱动与 Toolkit2 版本配套、散热降频和后台负载。

## 真机验收

仓库开发机不是 RK3588 时只能做语法和逻辑检查，最终交付必须在目标盒子完成：

1. `rk3588_preflight.sh` 全部通过；
2. 连续运行至少 2 小时，进程 RSS 与 DMA 占用进入稳定区间，不随帧数线性增长；
3. `/health` 三个 EP 均为 RK3588 硬件后端；
4. 使用上述基准记录 `npu_throughput_fps`，并记录每路输入分辨率/FPS、`npu_duration_us`、端到端 P50/P95、队列丢帧和温度；
5. 同时开启目标路数、告警截图和 RTMP 后复测，确认没有热降频与驱动错误。

性能没有脱离模型、分辨率、码流和散热条件的单一“最大值”；以目标盒子的持续 P95 和稳定性为验收标准。
