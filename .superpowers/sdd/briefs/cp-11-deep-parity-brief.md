# Brief — CP-11: Part1 深对齐清理（Deep Gap Cleanup）

## CRITICAL — NO NESTED SUBAGENTS
Leaf worker only. **Never call the Task tool.**

## SSOT
完整任务包（位置 + 改法 + Done when）：

**[`docs/video-java/CODE_PARITY_DEEP_GAP_PACK.md`](../../../docs/video-java/CODE_PARITY_DEEP_GAP_PACK.md)**

## Goal
清理 CP-1…CP-10 门卡 PASS 后仍存在的 **可代码复刻** 深层 gap（通知载荷、编排 matching、sink 假绿、FlightHub data、AudioTalk 端口/降噪、GB28181 alternate/属性、directory sync、boot reset/NVR、status 心跳、扫尾）。一次性按 T1→T12 做完。

## Out
Part2 引擎/真机；COMPLETE；删 Python；FR-B；mini/stub 当 PASS。

## Deliverables
- `logs/cp-11-*.json`
- `.superpowers/sdd/briefs/cp-11-report.md`
- 更新 INDEX / BACKLOG / HANDOFF；修正 CP-10 M-04 误称

## Prior
Part1 CP-1…CP-10 PASS（见 `CODE_PARITY_INDEX.md`）。本包是深对齐，不是重复刷包门卡。
