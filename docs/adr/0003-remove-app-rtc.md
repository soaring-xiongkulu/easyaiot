# ADR-0003 — 从 acme 产品树移除 APP 与 RTC

- 日期: 2026-08-09
- 状态: Accepted

## 决策

acme 硬分叉产品 **不再包含 / 维护**：

1. **APP/** — UniApp 移动端（WEB 视频 AI 运维缩量版）
2. **RTC/** — go2rtc 消费级摄像头 P2P 桥接（Tapo/Tuya/Ring/米家等）

## 理由

- 目标场景为严肃工业视频 AI（GB28181 / ONVIF / NVR / 标准 RTSP），不以消费级门铃品牌与移动缩量为产品面。
- APP 与 RTC 正交，一并移除可避免重复清理。

## 后果

- 删除 `APP/`、`RTC/` 源码树。
- 清理安装/运行时清单、COMPILE 打包列表中的 APP/RTC。
- WEB 去掉「RTC 平台」接入 UI 与 nginx `/dev-api/go2rtc/` 反代；VIDEO 去掉 `rtc-live` API。
- **保留** WEB 工业 WebRTC 播放器（`rtcPlayer.vue` / ZLMRTCClient），与 RTC 模块无关。
- 工业主路径 WEB / DEVICE / VIDEO / AI / RUNTIME 不受影响。
