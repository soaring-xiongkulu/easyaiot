# Brief — CP-7: AudioTalk main-path code parity

## CRITICAL — NO NESTED SUBAGENTS
Leaf only when executed (另令).

## Goal
capabilities/start/stop/health key path vs Python. Real SIP phone = Part2.

## Oracle / Java
- `VIDEO/app/blueprints/audio_talk.py`
- `AudioTalkController`, `AudioTalkService`

## Done when
- Honest failure without device; with fixture, start/stop explainable
- `logs/cp-7-audiotalk.json` + report

## Prereq
CP-1
