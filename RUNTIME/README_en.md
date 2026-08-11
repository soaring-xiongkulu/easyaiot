# RUNTIME Module

High-performance **C++ frame worker** for EasyAIoT. Handles pull / decode / infer / emit. It does **not** replace VIDEO.

## Role vs VIDEO

- **VIDEO**: orchestration, preview forward, task lifecycle, alert hook, Kafka, DB
- **RUNTIME**: hot path executor for `executor=cpp` realtime tasks

Default remains `executor=python`. See Chinese README for pipeline, build, and VIDEO integration details: [README.md](README.md).
