# Brief — Phase 2 Pack A2: Algo task start/stop + real RUNTIME

## HARD RULE — NO NESTED SUBAGENTS
Do ALL work yourself. **Forbidden:** Task tool, spawning any subagent, FR-Bxx, COMPLETE, deleting Python, stub executor, mini profile to fake green.

## Mandatory prior reading (links — read before coding)
1. Index: `F:/acme/.worktrees/video-java/.superpowers/sdd/PHASE2_AGENT_INDEX.md`
2. A1 report: `F:/acme/.worktrees/video-java/.superpowers/sdd/briefs/phase2-a1-report.md`
3. A1 evidence: `F:/acme/.worktrees/video-java/logs/phase2-a1-alert-kafka.json`
4. Phase1 stack: `F:/acme/.worktrees/video-java/docs/video-java/PHASE1_STACK.md`
5. HANDOFF: `F:/acme/.worktrees/video-java/docs/video-java/HANDOFF.md`

## Goal
On local full stack, start an algo task via Java → **real RUNTIME process alive** → services/status reasonable → stop clean. Align with Oracle Python task start/stop semantics.

## Paths
- Worktree: `F:/acme/.worktrees/video-java` @ `feat/video-java`
- Oracle: `F:/acme/VIDEO/` — algo/task start/stop, executor_bin (NOT stub)
- Candidate: `DEVICE/iot-video` algo/task controllers + runtime process management
- Stack: PG `127.0.0.1:15432`, Kafka `:9092`, Nacos `:8848`, MinIO `:9000`, gateway `:48080`, video-server `:48096` profile **local**
- JAVA_HOME=`F:\acme\.tools\jdk-21.0.2` ; Maven=`F:\acme\.tools\apache-maven-3.9.16\bin\mvn.cmd`
- Prefer gateway `http://127.0.0.1:48080/admin-api/video/**`

## Python-first
Read Oracle task start/stop + how RUNTIME binary is launched. Cite paths in evidence + report.
Find a same-DB task that can start (prefer existing; minimal fixture OK if needed).

## Acceptance
1. `executor_bin` must NOT be stub; if binary missing → honest ⛔, do not fake running
2. start → process PID alive on Windows
3. services/status (or Java equivalent) shows running/reasonable
4. stop → process gone / state stopped
5. Evidence: `logs/phase2-a2-runtime-lifecycle.json`
6. Update `docs/video-java/PHASE2_MAINPATH.md` A2 + `HANDOFF.md`
7. **REQUIRED handover report:** `.superpowers/sdd/briefs/phase2-a2-report.md` (status, evidence, commit, oracle cites, fixture leftovers, next-pack notes)
8. Update `.superpowers/sdd/PHASE2_AGENT_INDEX.md` A2 row
9. Commit: `feat(video-java): phase2 A2 runtime lifecycle parity` (include report + evidence + docs; no secrets/conda/models/unrelated dirty files)

## Done when
PASS with real process lifecycle OR honest ⛔ if RUNTIME binary/config missing (do not stub). Report file exists.

## Return to orchestrator
STATUS, commit hash, evidence path, report path, ready for A3?
