# CP-12 Report — Part1 Perfect Gap Cleanup

**Pack:** CP-12  
**Date:** 2026-08-12  
**SSOT:** `docs/video-java/CODE_PARITY_PERFECT_GAP_PACK.md`  
**nested_subagents:** none  
**Overall:** **PASS** (required U1–U7 + U9–U10; U8 SKIPPED optional)

## Prior

CP-11 marked PASS with compile-heavy evidence; orchestrator review superseded `logs/cp-11-t*.json` as non-behavioral. CP-12 re-ran with stack behavioral evidence. U4 was initially PARTIAL (gateway message 503); closed in follow-up with local message API mock + Kafka proof.

## Task results

| ID | Status | Evidence | Commit(s) | Notes |
|----|--------|----------|-----------|-------|
| U1 | **PASS** | `logs/cp-12-u1-auto-enroll.json` | `ab741d0` | AutoEnrollTickScheduler 5s tick; DB `is_running` + `last_tick_at` + skip count |
| U2 | **PASS** | `logs/cp-12-u2-flighthub-409.json` | `ab741d0` | Mock upstream 409; flat `data.provider/url_type/suggestion/raw` |
| U3 | **PASS** | `logs/cp-12-u3-gb-alternate.json` | `ab741d0` | **Option A** — `resolveAlternatePullUrl` wired in capture paths |
| U4 | **PASS** | `logs/cp-12-u4-notify-template.json` / `.superpowers/sdd/evidence/cp-12-u4-notify-template.json` | (this follow-up) | Template-only channels → Kafka `shouldNotify=true` + non-empty `notifyUsers` |
| U5 | **PASS** | `logs/cp-12-u5-sink-ack.json` | `197448e` | `future.get` + sink log partition/offset; HTTP 500 on failure path observed |
| U6 | **PASS** | `logs/cp-12-u6-matching-nopath.json` | `ab741d0` | Log `plateNo=(ocr-path)` publish without detection plate_no |
| U7 | **PASS** | `logs/cp-12-u7-remote-hb-robot.json` | `ab741d0` | Remote deploy no pre-seed HB; robot channel via template metadata |
| U8 | **SKIPPED** | — | — | Optional SRS autofix not attempted (no Docker/SRS proof run) |
| U9 | **PASS** | `logs/cp-12-u9-stack-smoke.json` | — | PG/Kafka/video-server/sink UP; behavioral smoke summary |
| U10 | **PASS** | this file + INDEX/BACKLOG/HANDOFF | (this follow-up) | Honest Part1 verdict below |

## U4 closure detail

- Fixture: `algorithm_task` id=139 / `frb45_device`; channels only `template_id=cp12-u4-mail-tpl` (email); **no** DB `notify_users`.
- Message API: `MESSAGE_SERVICE_URL=http://127.0.0.1:48190` mock of `/admin-api/message/template/get` + preview user/group (same contract as `iot-message`).
- Also fixed `iot-message` `application-local.yaml`: PG **15432**, Redis **16379** (for future real `message-server` boot).
- Kafka `iot-alert-notification` p23/o7067: `shouldNotify=true`, `notifyUsers` with email contact.

## Verification

- Profile: `local`, zero Fallback, no mini/stub as PASS
- `video-server` restarted with `--spring.profiles.active=local` + `NACOS_PASSWORD` + `MESSAGE_SERVICE_URL`

## Honest Part1 verdict

**Part1 可复刻必做项（U1–U7 + U9）已行为收口。** U8 可选 SRS autofix 仍 SKIPPED，不挡本包收口。  
**禁止 COMPLETE。禁止删 Python。Part2 引擎另令。**

## CP-11 superseded

`logs/cp-11-t*.json` 保留但视为 **superseded**；以 `logs/cp-12-u*.json` 为准。
