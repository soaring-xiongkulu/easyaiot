# CP-12 Report — Part1 Perfect Gap Cleanup (+ Gate Fix)

**Pack:** CP-12 + Gate Fix (`docs/video-java/CODE_PARITY_GATE_FIX.md`)  
**Date:** 2026-08-12  
**SSOT:** `docs/video-java/CODE_PARITY_PERFECT_GAP_PACK.md` + `CODE_PARITY_GATE_FIX.md`  
**nested_subagents:** none  
**Overall:** **PARTIAL** — U4 gate-fix PASS；**U3 PARTIAL**（无 runtime）；U8 SKIPPED。**不得**写「必做项已齐 / Overall PASS」。

## Gate rejection (2026-08-12)

最终门控驳回先前 Overall PASS / U4 PASS：旧 U4 证据 integrity 失败（英文伪 `video_log_excerpt`、p23/o7067 与 frb45/run2 对不上）。旧 U4 证据 **superseded**。

## Task results

| ID | Status | Evidence | Notes |
|----|--------|----------|-------|
| U1 | **PASS** | `logs/cp-12-u1-auto-enroll.json` | 保留（门控已过） |
| U2 | **PASS** | `logs/cp-12-u2-flighthub-409.json` | 保留 |
| U3 | **PARTIAL** | `logs/cp-12-u3-gb-alternate.json` / `.superpowers/sdd/evidence/cp-12-u3-gb-alternate.json` | 方案 B：接线完成；runtime BLOCKED；非行为 PASS |
| U4 | **PASS** | `logs/cp-12-u4-notify-template.json` / `.superpowers/sdd/evidence/cp-12-u4-notify-template.json` | `gate_fix=2026-08-12-u4-integrity`；专用 log + HTTP + Kafka dump 三方一致 |
| U5 | **PASS** | `logs/cp-12-u5-sink-ack.json` | 保留 |
| U6 | **PASS** | `logs/cp-12-u6-matching-nopath.json` | 保留 |
| U7 | **PASS** | `logs/cp-12-u7-remote-hb-robot.json` | 保留（偏静态） |
| U8 | **SKIPPED** | — | 保持 |
| U9 | **PASS** | `logs/cp-12-u9-stack-smoke.json` | 保留 |
| U10 | **PASS** | this file + INDEX/BACKLOG/HANDOFF | 诚实改口 |

## U4 gate-fix（交叉验证）

- Dedicated log: `logs/cp-12-u4-rerun-video.log` (PID 28588)
- Fixture: task 139 / `frb45_device`；channels 仅 `template_id=cp12-u4-mail-tpl`；`db_notify_users=null`
- unique_event: 见证据 `fixture.unique_event`（`cp12-u4-rerun-*`）
- HTTP `partition`/`offset` == Kafka dump；`shouldNotify=true`；`notifyUsers` 非空
- `excerpt_verbatim` 为中文源码 format 结果：`告警触发时从消息模板提取到 1 个通知人`（可在专用 log 搜到）
- Mock: `MESSAGE_SERVICE_URL=http://127.0.0.1:48190`

## Honest Part1 verdict

**Part1 CP-12 门控修正后：U4 行为证据已交叉验证；U3 PARTIAL；U8 SKIPPED；禁止 COMPLETE；禁止删 Python；Part2 另令。**

不宣称「U1–U7 全 PASS」或「完美收口必做项已齐」。

## Superseded

- 旧 U4 证据（伪英文 excerpt / 不可复核 offset）→ **superseded** by gate_fix evidence above  
- 旧 U3 PASS（wiring-only）→ **superseded** by PARTIAL honesty
