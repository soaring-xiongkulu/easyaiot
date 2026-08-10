# Report — FIX: Restore Phase 1 camera_list parity

**Status:** PASS

## Root cause
Frozen python golden for `vj_p1_camera_list` listed 2 certify devices (`vj_p1_device`, `vj_p0_device`). Oracle and Java candidate both return 3 (`vj_p2_device` added by P2 seeding) for `search=certify`.

## Fix
Re-recorded python oracle golden:
`python tools/video_java/record_python.py vj_p1_camera_list`

No code/filter changes — stable fixture set is all three `vj_p*_device` rows with `manufacturer=certify`.

## Certify
| Phase | Exit |
|-------|------|
| 0 | 0 |
| 1 | 0 |
| 2 | 0 |

PHASE_1_GATE: PASS. CERTIFY_STATUS Phase 1: PASS.

## Concerns
- P2 seed adds `vj_p2_device`; any future certify run before P2 seed may briefly show 2 vs 3 until oracle is re-recorded or DB is pre-seeded.
- Phase 0/2 gate timestamps drift on full certify sweep; unrelated java golden noise from re-sample should not be committed with this fix.
