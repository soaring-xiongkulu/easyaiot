# RUNTIME-NVIDIA: keep the video-AI hot path on NVIDIA silicon

RUNTIME-NVIDIA is EasyAIoT's strict NVIDIA edge runtime. Frames stay on the NVDEC → CUDA preprocessing → TensorRT path. Missing NVIDIA capability is a startup failure; there is no ONNX Runtime, CPU inference, or software-codec fallback.

The runtime shares one deserialized TensorRT engine across independent execution contexts, preallocates every TensorRT I/O buffer, uses a non-default CUDA stream per lane, optionally captures `enqueueV3` as a CUDA Graph, and connects stages with fixed-capacity drop-oldest rings. “Zero memory” means zero host-frame copies on the hot path and zero unbounded growth—not literally zero RAM or VRAM.

Only static TensorRT 10+ `.engine`/`.plan` files with `[1,3,H,W]` FP16/FP32 input are accepted. Engines are GPU-architecture and TensorRT-version specific, so build and validate them on the target box:

```bash
cd RUNTIME-NVIDIA
./scripts/build_engine.sh /path/to/yolo11n.onnx ./models/yolo11n-nvidia-fp16.engine fp16
./install_linux.sh preflight
./install_linux.sh build
cp config/config.example.ini ./gate-a.ini
./install_linux.sh install ./gate-a.ini gate-a
```

Use one config/systemd instance per RTSP stream. A config may reference multiple engines with `model_path_1`, `model_path_2`, and so on. `/health` and `/metrics` expose the real GPU, compute capability, pipeline endpoints, inference latency, bounded-queue drops, and preallocated bytes; no fixed FPS is claimed without measurement on the deployed hardware.
