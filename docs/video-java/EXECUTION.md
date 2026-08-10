# VIDEO Java — EXECUTION 纪律

对齐 `docs/runtime-parity/EXECUTION.md` 精神，**门禁与工具独立**。

## 1. 角色

| 角色 | 职责 |
|------|------|
| 编排 | 审查计划、收门禁、决定切流 |
| 实现 Agent | 只修红清单；先测后改 |
| Oracle | Python VIDEO 行为冻结（tag 后） |

## 2. 允许 / 禁止

**允许：** 在 `feat/video-java` 增加 `DEVICE/iot-video`、`docs/video-java`、`tools/video_java`、网关双跑路由、部署脚本；录 golden；safe_fsops 纪律下的测试媒体拷贝。

**禁止：**

- 未过本目录 Phase 门禁就改网关默认 `lb://video-server` 到 Java
- 修改 RUNTIME 帧内算法「顺便」完成 VIDEO 能力
- 重写 ffmpeg/SRS/ZLM/AI
- `git push --force` 到 main
- 把 video-java certify 结果写进 `docs/runtime-parity/gates` 冒充旧程序延续
- 用 runtime-parity「约 3 小时」或空人月当本任务排期

## 3. 文件系统破坏性操作

删除/移动大树必须走 `tools/runtime_parity/safe_fsops.py`（或继任工具）：**dry-run → 编排确认 token → --execute**。Python VIDEO 退役波次同此。

## 4. 提交

- 波次小提交；门禁证据与代码分开或可追溯  
- 不提交密钥、`.env.acme` 实密、logs、大 mp4（媒体走脚本/provenance）

## 5. 环境变量

Candidate 使用独立 `application-local.yaml` / `.env` 覆盖；双跑时注意 `VIDEO_SKIP_BACKGROUND_TASKS`、禁用双边 `auto_start` 抢任务。
