# CP-12 Report — Part1 Perfect Gap Cleanup

**Pack:** CP-12  
**Date:** 2026-08-12  
**SSOT:** `docs/video-java/CODE_PARITY_PERFECT_GAP_PACK.md`  
**nested_subagents:** none  
**Overall:** PARTIAL (U4 PARTIAL; U8 SKIPPED)

## Prior

CP-11 marked PASS with compile-heavy evidence; orchestrator review superseded `logs/cp-11-t*.json` as non-behavioral. CP-12 re-ran with stack behavioral evidence.

## Task results

| ID | Status | Evidence | Commit(s) | Notes |
|----|--------|----------|-----------|-------|
| U1 | **PASS** | `logs/cp-12-u1-auto-enroll.json` | `ab741d0` | AutoEnrollTickScheduler 5s tick; DB `is_running` + `last_tick_at` + skip count |
| U2 | **PASS** | `logs/cp-12-u2-flighthub-409.json` | `ab741d0` | Mock upstream 409; flat `data.provider/url_type/suggestion/raw` |
| U3 | **PASS** | `logs/cp-12-u3-gb-alternate.json` | `ab741d0` | **Option A** — `resolveAlternatePullUrl` wired in capture paths |
| U4 | **PARTIAL** | `logs/cp-12-u4-notify-template.json` | `ab741d0` | Template→notify_users code wired; gateway message API 503 blocks full Kafka proof |
| U5 | **PASS** | `logs/cp-12-u5-sink-ack.json` | `197448e` | `future.get` + sink log partition/offset; HTTP 500 on failure path observed |
| U6 | **PASS** | `logs/cp-12-u6-matching-nopath.json` | `ab741d0` | Log `plateNo=(ocr-path)` publish without detection plate_no |
| U7 | **PASS** | `logs/cp-12-u7-remote-hb-robot.json` | `ab741d0` | Remote deploy no pre-seed HB; robot channel via template metadata |
| U8 | **SKIPPED** | — | — | Optional SRS autofix not attempted (no Docker/SRS proof run) |
| U9 | **PASS** | `logs/cp-12-u9-stack-smoke.json` | — | PG/Kafka/video-server/sink UP; behavioral smoke summary |
| U10 | **PASS** | this file + INDEX/BACKLOG/HANDOFF | `0985339` | Honest Part1 verdict below |

## Verification

- Profile: `local`, zero Fallback, no mini/stub as PASS
- `video-server` restarted with `--spring.profiles.active=local` before U9
- Fixed boot NPE: `IpReachabilityMonitorService` ConcurrentHashMap null value (blocked stable stack)

## Honest Part1 verdict

**Part1 可复刻逻辑未达完美收口** — 阻塞项：**U4**（iot-message 经网关 503，无法在栈上完成 template→`notifyUsers` 行为证明）。U1–U3、U5–U7、U9 已有行为级证据。

**禁止 COMPLETE。禁止删 Python。Part2 引擎另令。**

## CP-11 superseded

`logs/cp-11-t*.json` 保留但视为 **superseded**；以 `logs/cp-12-u*.json` 为准。
