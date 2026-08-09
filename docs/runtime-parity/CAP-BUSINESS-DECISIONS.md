# 算法 Runtime 能力 — 业务取舍表（FINAL）

> **冻结日期：** 2026-08-09  
> **产品拍板：** 等价测试场、C++ Runtime（含 Windows）、目标追踪及下表其余项均为 **要**；仅算法任务 SAM 为 **不要**。  
> **`AI/` 标注 SAM：** 保留（不在本表删除范围）。

| ID | 能力（白话） | 今天在哪 | 决定 |
|----|--------------|----------|------|
| CAP-YOLO-ONNX | 目标检测（ONNX） | py+cpp | **要** |
| CAP-PT-ULTRALYTICS | 热路径直接跑 .pt | 仅 py | **不要（工程）**：以导出 ONNX 满足业务，C++ 不内嵌 ultralytics |
| CAP-MULTI-MODEL | 一任务多模型串联 | 仅 py | **要**（多 ONNX） |
| CAP-REGION | 检测区域/电子围栏 | py+cpp | **要** |
| CAP-ALERT-HOOK | 检出后告警上报 | py+cpp | **要** |
| CAP-ALERT-CLASS | 只对某些类别告警 | 仅 py | **要** |
| CAP-ALERT-SUPPRESS | 告警冷却/抑制 | py+cpp | **要** |
| CAP-HEARTBEAT | 任务心跳 | py+cpp | **要** |
| CAP-RTMP | AI 画面推流叠框 | py+部分 cpp | **要** |
| CAP-OVERLAY-DUAL | overlay/告警双队列级预览表现 | 仅 py | **要**（表现对齐；实现可优化但 certify 须达标） |
| CAP-TRACKING | 目标追踪 track_id/停留 | 仅 py | **要** |
| CAP-MOTION-GATE | 运动门控再检 | 仅 py | **要** |
| CAP-FACE-FILTER | 人脸类过滤 | 仅 py | **要** |
| CAP-PLATE-FILTER | 车牌类过滤 | 仅 py | **要** |
| CAP-FACE-MATCH | 人脸库 1:N 匹配 | 触发在 py | **要**（触发上收 VIDEO） |
| CAP-PLATE-MATCH | 车牌库匹配 | 触发在 py | **要**（触发上收 VIDEO） |
| CAP-POST-PROCESS | 自定义后处理入队 | 触发在 py | **要** |
| CAP-POSE | 姿态分析/意图 | 触发在 py | **要** |
| CAP-DEFENSE | 布防时段全防/半防 | 配置在任务 | **要** |
| CAP-CRON-SNAP | 抓拍 Cron 精确调度 | py 强 / cpp 弱 | **要** |
| CAP-SNAP-SPACE | 抓拍写入抓拍空间 | 仅 py | **要** |
| CAP-PATROL-POOL | 巡检连接池并行 | py+cpp | **要** |
| CAP-PATROL-ROTATE | 巡检轮转 | py+cpp | **要** |
| CAP-PATROL-HYBRID | 巡检 hybrid+焦点机 | 仅 py | **要** |
| CAP-GB28181-SRC | 国标源解析供算法拉流 | 仅 py | **要** |
| CAP-NVENC-AUTO | NVENC/画质自动降档 | 仅 py | **要** |
| CAP-WINDOWS | Windows 编译运行 RUNTIME | 无 | **要** |
| CAP-PARITY-TESTBED | 等价测试场 / certify | 无 | **要** |
| ~~CAP-SAM-TASK~~ | ~~算法任务 SAM 补充~~ | ~~仅 py~~ | **不要（已砍）** |
| AI 标注 SAM | 数据集标注分割 | `AI/` | **保留（不在 Runtime 收归删除）** |
