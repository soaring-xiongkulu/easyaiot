# 调研摘要（计划输入）

> 只读勘察汇总，供审查 STACK/PLAN。日期：2026-08-10。Oracle tip：`4f93baf`。

## Java 生态

- `DEVICE/`：Maven，Java 21，Boot **2.7.18**，Cloud **2021.0.5**，SCA **2021.0.4.0**，`groupId=com.basiclab.iot`。
- **无** `iot-video` 模块；网关已有 `video-admin-api` → `lb://video-server` + `StripPrefix=1`。
- iot-sink：经网关调 `/admin-api/video/face|plate/matching/process`、`/alert/hook`；Kafka 主题 `iot-face-matching*`、`iot-plate-matching*`、`iot-post-process*`、`iot-snapshot-alert`。
- iot-node：SSH 部署 ffmpeg/RUNTIME 静态包与 workload 类型，不本地常驻推理进程。
- DB：`iot-video20`（VIDEO / sink video DS / message 只读）。

## Python VIDEO

- 入口 `VIDEO/run.py`；14 Blueprint；`/actuator/health|info`。
- 关键：`algorithm_task_daemon/launcher`、`runtime_config_service`、`alert_hook_service`、camera `FFmpegDaemon`。
- 执行器：**仅 cpp**；ProcessBuilder 等价物为 `Popen([RUNTIME_BIN, ini])`。
- 规模：`app/` 约 4–5 万 LOC。

## 吸收面（帧后）

见 `docs/runtime-parity/reports/04-video-absorb-surface.md`：Hook/心跳已在 VIDEO；人脸/车牌/后处理 **触发** 在删 Python runtime 后仍有缺口，应在 Java VIDEO 帧后编排补齐（P2），不是塞进 RUNTIME。

## 推荐放置

新建 `DEVICE/iot-video`（api+biz），双跑名 `video-server-java`，切流改回 `video-server`。不扩展 iot-device/sink/gb28181 承载 VIDEO 全域。
