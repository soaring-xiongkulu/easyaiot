# RUNTIME-RK3588 Module

`RUNTIME-RK3588` is the EasyAIoT C++ edge runtime derived from `RUNTIME` for RK3588-based AI appliances. It keeps the existing pull, decode, inference, event-reporting, and annotated-stream pipeline while providing a dedicated baseline for RK3588, RKNN, and NPU acceleration work. See the [Chinese README](README.md) for hardware photos, product positioning, and deployment value.

High-performance **C++ frame worker** for EasyAIoT. Handles pull / decode / infer / emit. It does **not** replace VIDEO.

## Role vs VIDEO

- **VIDEO**: orchestration, preview forward, task lifecycle, alert hook, Kafka, DB
- **RUNTIME**: hot path executor for `executor=cpp` realtime tasks

Default remains `executor=python`. See Chinese README for pipeline, build, and VIDEO integration details: [README.md](README.md).
