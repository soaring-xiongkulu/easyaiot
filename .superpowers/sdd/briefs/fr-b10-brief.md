# Brief — FR-B10: Patrol 守护/SSE + audio_talk 真路径 + 匹配告警 MinIO（Python-first）

## HARD RULE — NO NESTED SUBAGENTS
Do ALL work yourself.

## Remaining from FR-B9 / GAP
1. Patrol daemon + SSE not mini-hollow — align Python PatrolSessionDaemon / progress hub
2. audio_talk ONVIF back-channel: ensure real RTSP DESCRIBE/SETUP/PLAY path works when device available (fix G.711 if stubbed)
3. Match alert MinIO image upload chain like Python
4. Pose library match-test similarity scoring if still thin

## Python-first
Read patrol_session_service, patrol daemon, progress hub, onvif_audio_backchannel, audio_talk_service_onvif, library_matching alert image upload.

## Goal
Close GAP remaining behavior rows for patrol/audio_talk/match-image/pose match-test. phase0 0. Commit + `fr-b10-report.md`. Update progress + GAP.

## Toolchain
JAVA_HOME=`F:\acme\.tools\jdk-21.0.2`; Maven=`F:\acme\.tools\apache-maven-3.9.16\bin`
