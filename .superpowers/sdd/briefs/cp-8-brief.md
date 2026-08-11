# Brief — CP-8: GB28181 code path (no live SIP required)

## CRITICAL — NO NESTED SUBAGENTS
Leaf only when executed (另令).

## Goal
`gb28181://` resolve + sync API code parity with synthetic/fixture inputs. Live SIP/NVR = Part2.

## Oracle / Java
- `gb28181_source.py`, `gb28181_sync_service.py`
- `Gb28181SourceSupport`, `Gb28181SyncService`

## Done when
- `logs/cp-8-gb28181-code.json` + report; honest failures

## Prereq
CP-1
