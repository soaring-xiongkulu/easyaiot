# RUNTIME-NVIDIA：把视频 AI 热路径留在 NVIDIA GPU

RUNTIME-NVIDIA 是 EasyAIoT 面向 NVIDIA 边缘盒子的独立硬件运行时。它不是通用 RUNTIME 打开一个 CUDA 开关，也不把解码后的图像下载到 CPU 再上传。VIDEO 负责统一管理摄像头、模型、任务和告警，本模块把每一帧沿着 **NVDEC → CUDA → TensorRT** 的设备内存路径执行；硬件链路缺一项即退出，不启用 ONNX Runtime、CPU 推理或软件解码。

“零内存”在这里有明确工程含义：热路径零主机帧拷贝、启动期预分配、固定容量环形队列、无逐帧设备内存申请和无无界缓存；它不代表程序不占 RAM 或显存。

## 硬件价值如何真正变成吞吐

```text
RTSP H.264/H.265/AV1
          │
          ▼
NVDEC 硬解 ── CUDA/NV12 surface（不下载主存）
          │
          ▼
固定 Decode Ring ──► 轮询分发 ─┬─ CUDA Stream 0 / TensorRT Context 0
                               ├─ CUDA Stream 1 / TensorRT Context 1
                               └─ 可按实测扩展更多流
                                         │
CUDA NV12→RGB + Letterbox + Normalize ──┘
                                         │
                         enqueueV3 + CUDA Graph
                                         ▼
固定 Result Ring ──► MQTT → iot-sink / edge HTTP hook
```

- **NVDEC 与 CUDA 解耦**：视频解码使用独立硬件引擎，NV12 surface 以引用穿过解码环形队列；推理完成后立即释放 surface，不让告警网络请求占住解码池。
- **融合预处理**：一个 CUDA kernel 完成 NV12→RGB、等比例缩放、填充、归一化和 NCHW 写入，输出直接是 TensorRT 输入地址。
- **权重只加载一次**：每个模型只有一个 `ICudaEngine`；并发通道各自拥有 `IExecutionContext`、非默认 CUDA stream 和预分配 I/O，避免用多线程重复加载整份权重。
- **CUDA Graph**：静态 engine 在启动时预热并捕获 `enqueueV3` 与输出拷贝，减少小模型多 kernel 的 CPU 发射开销。模型包含数据依赖控制流、无法捕获时会明确失败，用户可显式设置 `cuda_graph=false`，但不会切到 CPU。
- **锁住内存上限**：Decode、每条 Infer lane、Result 都是固定容量 ring；慢消费者只淘汰最旧帧，实时任务不会因为积压不断增大内存。
- **多路与多模型**：多路 RTSP 使用多份配置/多 systemd 实例；每份配置可通过 `model_path_1`、`model_path_2` 继续挂载多个 TensorRT engine。GPU 选择、推理流数和队列深度均按盒子调优。

实际帧率取决于 GPU 型号、功耗模式、engine 精度与 shape、码流分辨率、并发路数和温度。项目不写脱离硬件实测的固定 FPS；`/metrics` 返回真实推理耗时、帧数、丢帧与预分配字节数。

## 严格契约

1. Linux 主机必须提供可用 NVIDIA Driver、CUDA Runtime、TensorRT 10+ 和 FFmpeg CUDA/NVDEC。
2. 只接受在目标盒子上构建并验收的静态 `.engine` / `.plan`；输入必须为 `[1,3,H,W]` FP16/FP32，输出支持 `[1,84,N]`、`[1,N,84]` 或融合后 `[1,N,6]`。
3. 运行时不读取 `.onnx`、`.pt`、`.rknn` 或 `.bmodel`。ONNX 只允许作为离线构建 engine 的输入。
4. 当前版本只开放 realtime 任务；当前热路径不生成叠框视频和证据图。`enable_rtmp=true` 会失败，不会偷偷调用软件编码。
5. dGPU 使用 CUDA hwframe；Jetson 必须使用能向 FFmpeg 暴露 CUDA/NVDEC surface 的 JetPack/容器镜像。只有 NVMM/NvBufSurface、没有 CUDA hwframe 的系统会在预检阶段失败，避免“看似硬解、实际回主存”。

## 在 NVIDIA 盒子上轻松部署

先把 ONNX 在实际盒子上固化成 TensorRT engine。engine 与 GPU 架构和 TensorRT 版本相关，不应从另一台机器盲目复制：

```bash
cd RUNTIME-NVIDIA
./scripts/build_engine.sh /path/to/yolov8n.onnx ./models/yolov8n-nvidia-fp16.engine fp16
./install_linux.sh preflight
./install_linux.sh build
```

目标 GPU 对 INT8 友好时，可使用带显式 Q/DQ 节点的量化 ONNX，或额外传入离线生成的校准缓存：

```bash
./scripts/build_engine.sh /path/to/yolov8n-qdq.onnx ./models/yolov8n-nvidia-int8.engine int8
./scripts/build_engine.sh /path/to/yolov8n.onnx ./models/yolov8n-nvidia-int8.engine int8 /path/to/calibration.cache
```

量化和校准仍在部署阶段完成；在线任务只反序列化静态 engine，不现场转换模型。

复制配置，只需填写摄像头和 engine：

```bash
cp config/config.example.ini ./gate-a.ini
./install_linux.sh install ./gate-a.ini gate-a
```

再加摄像头无需改脚本：

```bash
./install_linux.sh add gate-b ./gate-b.ini
./install_linux.sh status gate-a
./install_linux.sh status gate-b
```

每个任务使用自己的 `control_port`：

```bash
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8001/metrics
curl -X POST http://127.0.0.1:8001/stop
```

健康数据会明确给出 GPU 名称、Compute Capability、NVDEC/CUDA/TensorRT 端点、CUDA Graph 状态、推理通道数和各环形队列丢帧数。
