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

The runtime does not depend on WEB, AI, VIDEO, MQTT, Docker, or any other platform module, so the box can run fully offline. Run the commands below from the repository root; a first-time user can follow them in order to bring up one stream.

### 1. Verify the box

```bash
# Read-only: aarch64/RK3588 device tree, NPU/RGA/MPP/DRM nodes, RKNN/RGA/MPP libraries
bash RUNTIME-RK3588/install_linux.sh preflight
```

Continue when it prints `RK3588_PREFLIGHT_OK`; a missing node or library means the host does not meet the conditions above.

### 2. Prepare the model and class names

Only the Rockchip Model Zoo optimized YOLOv8n INT8 RKNN (one input, nine outputs) is accepted. Put the `.rknn` in a stable directory on the box, such as `/opt/models`; the repository already ships the [coco.names](models/coco.names) class file:

```bash
ls -l /opt/models/yolov8n-rk3588-int8.rknn RUNTIME-RK3588/models/coco.names
```

If you do not have the `.rknn` yet, generate it on a conversion host as described under "Models", then copy it to the box.

### 3. Write a minimal manifest

Start offline with one stream; replace the model path and RTSP URL with real values:

```bash
cat > rk3588.tasks.json <<'JSON'
{
  "version": 1,
  "control_plane": { "enabled": false },
  "remote_access": { "enabled": false },
  "models": {
    "person_vehicle": {
      "path": "/opt/models/yolov8n-rk3588-int8.rknn",
      "classes": "RUNTIME-RK3588/models/coco.names"
    }
  },
  "tasks": [
    {
      "id": "north-gate",
      "device_name": "North gate",
      "rtsp_url": "rtsp://user:password@192.168.1.101/stream1",
      "models": ["person_vehicle"],
      "control_port": 8201
    }
  ]
}
JSON
```

A model is registered once. Add a second stream by copying the `tasks` entry and giving it a new `id` and `rtsp_url`; to run several models on one stream, add another key under `models` and put that key in the task's `models` array. `control_port` is the port for that stream's `/health` endpoint; the example pins it to 8201, and when omitted the ports start at 8200 in task order.

### 4. Validate without changing the host

```bash
bash RUNTIME-RK3588/install_linux.sh config-check ./rk3588.tasks.json
```

`任务清单可部署；未改动系统、未启动服务` means the paths, model references, task IDs, and control ports are valid. Re-run this after editing the manifest; no reinstall is needed.

### 5. Install and start

```bash
sudo bash RUNTIME-RK3588/install_linux.sh install ./rk3588.tasks.json
```

The installer runs the hardware/driver preflight, native build, model installation, per-stream INI generation, systemd template-instance registration and startup, and waits for every `/health` endpoint. Without systemd it uses per-task PIDs and logs. It does not start Docker, WEB, AI, VIDEO, or the MQTT agent unless `control_plane` is enabled in the manifest. The unified entry point `bash .scripts/docker/install_linux.sh rk3588 <subcommand>` delegates to the same module script, so either form works.

### 6. Verify and operate

```bash
# All tasks
bash RUNTIME-RK3588/install_linux.sh list
bash RUNTIME-RK3588/install_linux.sh status

# One stream (the task ID is the `id` in the manifest)
bash RUNTIME-RK3588/install_linux.sh verify north-gate
bash RUNTIME-RK3588/install_linux.sh logs north-gate
bash RUNTIME-RK3588/install_linux.sh restart north-gate

# Inspect the hardware pipeline directly
curl -s http://127.0.0.1:8201/health
```

`verify` confirms MPP decode, RGA, and the three-core RKNN path. `/health` should report `infer_ep=rknn-rk3588-3core-ring`, `decode_ep=mpp-rk3588`, and `encode_ep=h264_rkmpp`. Without a task ID, `status`, `logs`, `verify`, and `restart` cover every stream. `logs` follows in real time by default; press `Ctrl+C` to stop, or run `EASYAIOT_RK3588_LOG_FOLLOW=0 bash RUNTIME-RK3588/install_linux.sh logs north-gate` to print the last 200 lines.

After editing the manifest (for example, adding a stream), re-orchestrate the installed box:

```bash
sudo bash RUNTIME-RK3588/install_linux.sh update ./rk3588.tasks.json
```

To compile without installing:

```bash
sudo bash RUNTIME-RK3588/install_linux.sh build
```

Build output lives in `RUNTIME-RK3588/build/` and can be deleted directly. `bash RUNTIME-RK3588/install_linux.sh uninstall` removes binaries and service templates while preserving the manifest, per-stream configuration, models, and logs.

### Optional platform enrollment

Add `control_plane` to the manifest for central management, or enable `remote_access` to reach the box from the platform. Keep both `enabled` values `false` for a fully local box:

```json
{
  "control_plane": {
    "enabled": true,
    "url": "http://platform-ip:48080/admin-api/video/edge",
    "join_token": "EDGE_ENROLL_TOKEN from the central platform",
    "node_name": "Park North-RK3588-01"
  },
  "remote_access": {
    "enabled": false,
    "provider": "frp"
  }
}
```

With `control_plane.enabled=true`, the installer registers an MQTT agent and the box appears automatically in the standalone **Edge Computing** menu. The telemetry path is deliberately direct: `RK3588 → EMQX → iot-sink (authentication, HMAC verification, normalization, direct iot-video20 persistence) → VIDEO / WEB`; it does not pass through Kafka or NODE.

`remote_access.enabled=false` installs no frpc process and opens no public port. When enabled, service access and SSH are separate FRP tunnels. FRP is only an operator access path; heartbeat, hardware metrics, pipelines, and tunnel state continue to use MQTT. Each MQTT message is protected by the node token, HMAC-SHA256, a clock window, topic/node identity checks, and message-id deduplication.

The manifest deliberately matches the platform `RUNTIME` convention:

- `models` registers RKNN files, class names and optional business model IDs once; every task can reuse them;
- every `tasks` item is one RTSP stream, and its `models` array selects one or more models to run on that stream;
- every realtime stream receives its own INI, control port and supervised process, so one failed stream does not take down the others;
- all paths, references, task IDs and ports are validated before any installation starts.

The MQTT agent is installed only when platform enrollment is enabled, and frpc only when FRP is enabled. The installed manifest lives at `/etc/easyaiot/runtime-rk3588/tasks.json`; you can also edit it and run `update`. Legacy single-stream environment variables are still converted into a one-task manifest for backward compatibility. CMake only accepts an aarch64 target and requires `rknnrt`, `librga`, and Rockchip MPP; use `ROCKCHIP_SDK_ROOT` for a non-standard SDK/sysroot.

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
