# Report — P1-S5: Health recovery + dual-run gateway docs

## STATUS
**DONE** — algorithm-task health recovery scheduler (skippable); `DUAL_RUN.md` + optional gateway snippet documented. Phase 0/1 certify exit **0**.

## Commits
- (this commit) `feat(video-java): P1-S5 health recovery scheduler and dual-run docs`

## Certify exits
| phase | exit | notes |
|-------|------|-------|
| 0 | **0** | `--no-record --no-java` |
| 1 | **0** | `--no-record` (all 4 P1 cases PASS) |

## What changed
- **Java**: `AlgorithmTaskHealthRecoveryService` + `AlgorithmTaskHealthRecoveryScheduler` (`@Scheduled` 60s default, startup recovery); `VideoSchedulingConfig`; `VideoProperties` (`skip-background-tasks`, `health-monitor.*`); `AlgorithmTaskRepository.findEnabledLocal()`.
- **Config**: `application-local.yaml` sets `video.skip-background-tasks: true` (certify-safe, mirrors `VIDEO_SKIP_BACKGROUND_TASKS`).
- **Docs**: `docs/video-java/DUAL_RUN.md`, `docs/video-java/gateway-optional-route.yaml` (commented `/admin-api/video-java/**` → `lb://video-server-java`); `PHASE_1_GATE.md` / `CERTIFY_STATUS.md` notes.
- **Gateway**: production `video-admin-api` → `lb://video-server` **unchanged**.

## Concerns
- `mvn package` repackage failed when `iot-video-biz.jar` locked (running candidate); `mvn compile` OK.
- Health recovery only covers `schedule_policy=local` enabled tasks; remote node deploy still out of scope.
- Enable recovery in dual-run prod by `video.skip-background-tasks=false` on a non-local profile — local certify profile keeps skip on.
