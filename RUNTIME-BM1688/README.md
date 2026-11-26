# RUNTIME-BM1688：把视频 AI 真正压进算丰盒子

RUNTIME-BM1688 是 EasyAIoT 面向 BM1688 / CV186X SoC 的硬件专用算法运行时。它不是通用 RUNTIME 的 ARM 编译版，也不会在缺少芯片能力时偷偷改走 ONNX 或 CPU。VIDEO 继续负责统一的摄像头、模型、任务和告警编排；本模块只负责把任务稳定地压到 BM1688 的 VPU、VPSS/BMCV 与双核 TPU 上执行。

它解决的不是“程序能不能跑”，而是盒子长期值守时更重要的四件事：视频解码不挤占 CPU、图像预处理不在主存中来回复制、两个 TPU 核持续有活可做、上游或下游抖动时内存仍然有上限。

## 这台盒子的价值如何被用出来

```text
Sophon VPU 硬解 RTSP
        │ 设备帧（不下载到 CPU）
        ▼
固定容量 Decode Ring ──丢最旧帧，保实时性──► 双核任务分发
                                               ├─ Core 0 Infer Ring
BM1688 BModel ◄─ BMRuntime 预分配 ◄─ BMCV/VPSS ┤
                                               └─ Core 1 Infer Ring
        │
        ▼
固定容量 Result Ring ──► MQTT → iot-sink / edge HTTP hook / 硬件编码推流
```

- **硬件解码**：启动时必须找到 `h264_bm` 和 `hevc_bm`；找不到就失败，不启用软解。
- **零拷贝优先**：Sophon OpenCV 解码帧通过 `cv::bmcv::toBMI` 转成 `bm_image`，不发生帧数据复制；VPP 在设备侧完成等比例缩放、填充和色彩转换。
- **预分配而非逐帧申请**：输入图像池、输出张量和 BMRuntime 神经网络计算内存在启动阶段一次准备，热路径不反复申请设备内存。
- **双核并发**：每个 TPU 核拥有独立推理通道，调用 `bmrt_launch_tensor_multi_cores` 指定 core 0 / core 1，并用 `bm_thread_sync_from_core` 精确同步。
- **有界内存**：解码、两个推理通道和结果发布都是固定容量环形队列；拥塞时丢最旧帧，进程内存不会随摄像头卡顿无限增长。“零内存”在这里指零拷贝优先和零无界增长，并非不占 RAM。
- **多模型**：一份任务配置可写 `model_path`、`model_path_1`……；同一批设备帧依次经过多个 BModel，检测结果统一汇聚。
- **统一业务出口**：集群形态走 MQTT 标准消息，由 iot-sink 归一化并落库；edge 单体走 VIDEO HTTP hook 直接落库；心跳始终回到 VIDEO。

## 严格运行契约

1. 仅支持 BM1688 / CV186X aarch64 SoC。
2. 仅接受 BM1688/CV186X 编译的 `.bmodel`，不接受 `.onnx`、`.pt` 或 `.rknn`。
3. BModel 必须包含一个静态 YOLO 检测网络，输入为 NCHW/NHWC 四维张量，且提供双核运行信息；`core_ids` 固定为 `0,1`，不允许悄悄退化成单核。
4. 当前硬件流水线支持 FP32、INT8、UINT8 输入/输出张量；输出支持 YOLOv8 `[N,84,8400]` 或融合后的 `[N,K,6]`。
5. 当前平台契约先开放实时 C++ 任务；抓拍/巡检不会伪装成实时循环执行。实际吞吐由模型、batch、码流分辨率、SDK/固件版本和并发路数共同决定；仓库不写脱离实测环境的固定 FPS 承诺。`/metrics` 会返回真实帧数、队列丢帧和推理耗时。

## 与 VIDEO 一起运行

在 BM1688 盒子的一键部署中选择 `bm1688` 后，VIDEO 会自动识别宿主机，并在新建低时延算法任务时固定选择 **BM1688 · VPU + VPSS/BMCV + 双核 TPU**。模型选择只显示内置 yolov8n 或已登记的 `.bmodel`；任务只能本机调度。

手工构建：

```bash
cd RUNTIME-BM1688
./scripts/bm1688_preflight.sh
./install_linux.sh build
```

VIDEO 创建任务后会自动生成配置并直接拉起 `build/RUNTIME <task.ini>`，无需维护单独的 RTSP 环境变量。

## 不依赖其他模块的独立部署

先复制示例并填入摄像头、BModel 和告警出口：

```bash
cp config/config.example.ini ./gate-a.ini
sudo ./install_linux.sh install ./gate-a.ini gate-a
```

再加摄像头不需要改脚本；每路任务一份配置即可。每份配置本身又可以挂多个 BModel：

```bash
sudo ./install_linux.sh add gate-b ./gate-b.ini
sudo ./install_linux.sh status gate-a
sudo ./install_linux.sh status gate-b
```

独立部署只依赖盒子出厂的 BM1688 SOPHONSDK、Sophon OpenCV/FFmpeg 和系统服务，不依赖 WEB、VIDEO、AI 或通用 RUNTIME。

## 健康与性能观测

每个进程使用配置中的 `control_port`：

```bash
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8001/metrics
curl -X POST http://127.0.0.1:8001/stop
```

指标会明确显示 `sophon-vpu`、`bmcv-vpp`、`bmrt-2core` 三个硬件端点，以及各环形队列的丢帧数。只要任何硬件前提不成立，进程都会以非零状态退出，让 systemd 和平台看到真实故障。
