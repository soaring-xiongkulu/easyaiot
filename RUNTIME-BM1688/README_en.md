# RUNTIME-BM1688

RUNTIME-BM1688 is EasyAIoT's hardware-only video inference runtime for BM1688/CV186X SoCs. VIDEO keeps the common task contract while this module executes it through Sophon VPU decode, BMCV/VPSS preprocessing, and two explicitly assigned BMRuntime TPU cores.

There is no ONNX, CPU, or software-codec fallback. Startup fails if the box, SDK, hardware codec, or `.bmodel` contract is missing.

The hot path is designed around bounded memory: decoded device frames are handed to BMCV without copying frame data to the CPU; input images, output tensors, and BMRuntime neuron memory are preallocated; decode, per-core inference, and result stages use fixed-capacity rings that drop the oldest frame under backpressure.

Build on a BM1688 box:

```bash
./scripts/bm1688_preflight.sh
./install_linux.sh build
```

Standalone deployment supports multiple independent RTSP tasks and multiple BModels per task:

```bash
sudo ./install_linux.sh install ./gate-a.ini gate-a
sudo ./install_linux.sh add gate-b ./gate-b.ini
```

Use `GET /health` and `GET /metrics` on each task's control port for measured throughput, inference latency, errors, and ring-drop counters. Performance depends on the actual BModel, batch, streams, firmware, and SDK; no unverified fixed FPS claim is made.
