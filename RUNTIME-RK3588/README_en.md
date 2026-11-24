# RUNTIME-RK3588

`RUNTIME-RK3588` is an RK3588-only EasyAIoT execution runtime. It requires Rockchip MPP video decode, RGA image processing, RKNN Runtime 2 and the RK3588 three-core NPU. Missing hardware, drivers, SDK libraries, or `h264_rkmpp` is a fatal error—there is no ONNX Runtime, CPU inference, software decode, or `libx264` fallback.

![RK3588 edge box front and wireless expansion](../.images/rk3588/rk3588-front-wireless.jpg)

Wireless and cellular expansion supports remote and weak-network sites while local inference reduces uplink bandwidth and alert latency.

![RK3588 edge AI box](../.images/rk3588/rk3588-box.jpg)

The finned metal enclosure is suited to sustained video and NPU workloads. Bounded frame pools and per-model queues prevent memory growth under overload.

![RK3588 edge box I/O panel](../.images/rk3588/rk3588-io-panel.jpg)

Dual Ethernet, HDMI, USB, Type-C and SIM connectivity support separated camera/platform networks and integrated field deployments.

## Data path

The module architecture is shown below:

![RK3588 system architecture diagram](../.images/rk3588/rk3588-architecture.jpg)

The packet-level path in detail:

```text
FFmpeg demux -> MPP NV12 DMA-BUF -> RGA -> preallocated RKNN input FD -> NPU cores 0/1/2
                                  \-> RGA BGR overlay -> RGA NV12 -> h264_rkmpp -> RTMP
```

- MPP output uses a count-limited DMA buffer group.
- Imported RGA handles and RKNN input/output tensor memory are reused.
- RKNN workers are pinned to the three NPU cores and share model weights.
- Every NPU core has a dedicated bounded task ring and completion ring; a separate collector publishes results without a shared task-queue lock.
- Nine native INT8 outputs are preallocated and YOLOv8 DFL postprocessing reads `NC1HWC2` directly without per-frame FP32 conversion.
- Inference-only mode does not allocate a BGR frame pool; bounded BGR storage is enabled only for alert evidence or RTMP output.
- Snap and patrol modes use the same MPP/RGA capture path.
- Fixed-capacity queues drop the oldest stale frame instead of growing indefinitely.

“Zero memory” means zero-copy-first, no unbounded growth, and no per-frame large allocations—not literally zero bytes of process memory. The implementation follows the official Rockchip MPP, RKNN Runtime 2, and RGA interface contracts and strictly validates hardware nodes, drivers, tensor layouts, and codec capabilities.

## Standalone one-command deployment

Run one command from the repository root on the RK3588 box. The deployment does not require the EasyAIoT platform and does not start WEB, AI, VIDEO, MQTT, Docker, or any other module:

```bash
sudo env \
  EASYAIOT_RK3588_RTSP_URL='rtsp://user:pass@camera/stream' \
  EASYAIOT_RK3588_MODEL_PATH='/home/rock/yolov8n-rk3588-int8.rknn' \
  bash .scripts/docker/install_linux.sh rk3588 install
```

The script performs the hardware and driver preflight, native build, model installation, standalone configuration, boot-service registration, startup, and `/health` hardware-path acceptance. Without systemd it uses a managed background process with a PID and log file. For a guided flow, run `sudo bash .scripts/docker/install_linux.sh`, choose “RK3588”, then “one-click install”, and answer the RTSP/model prompts.

```bash
bash .scripts/docker/install_linux.sh rk3588 status
bash .scripts/docker/install_linux.sh rk3588 logs
bash .scripts/docker/install_linux.sh rk3588 verify
bash .scripts/docker/install_linux.sh rk3588 restart
```

Updates preserve the existing standalone configuration. Uninstall removes the service and binaries but keeps the model, configuration, and logs. `EASYAIOT_RK3588_MODEL_URL` can download a model, with optional `EASYAIOT_RK3588_MODEL_SHA256` verification. CMake only accepts an aarch64 target and requires `rknnrt`, `librga`, and Rockchip MPP; use `ROCKCHIP_SDK_ROOT` for a non-standard SDK/sysroot.

## Models

Only the Rockchip Model Zoo optimized YOLOv8n INT8 `.rknn` contract is accepted: one input and nine outputs (DFL boxes, class scores, and score sum for three scales).

```bash
./RUNTIME-RK3588/scripts/prepare_yolov8n_rk3588.sh \
  calibration.txt /opt/models/yolov8n-rk3588-int8.rknn
```

The script downloads Rockchip's optimized nine-output ONNX, validates the graph contract, and converts it for RK3588 INT8 with optimization level 3.

## Runtime configuration

```ini
[ai]
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

The build also produces `RUNTIME-RK3588-BENCH`. Run the same RGA/RKNN/ring pipeline on the target box:

```bash
/opt/easyaiot/RUNTIME-RK3588/bin/RUNTIME-RK3588-BENCH \
  /opt/easyaiot/RUNTIME-RK3588/models/yolov8n-rk3588-int8.rknn \
  test.jpg 30 150 \
  /opt/easyaiot/RUNTIME-RK3588/models/coco.names
```

`BENCH_PASS` with zero drops validates the 150 FPS aggregate three-core target. This is a hardware acceptance target, not a claim that a 25 FPS input stream becomes 150 FPS or a guarantee across arbitrary models, clocks, thermals, drivers, and system images. `/health` exposes `npu_throughput_fps`, completed tasks, sampled NPU time, and ring drops.
