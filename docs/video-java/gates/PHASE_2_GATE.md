# PHASE 2 Gate — face/plate / snap-record-playback / patrol / regions / media_hook

**Status:** FAIL (scaffold — Java Phase 2 not implemented)
**Updated:** 2026-08-10 04:16 UTC

Gate PASS when every P2 case `ok` — each layer `pass` or signed `exempt`.
Layers: `api`, `side_effect` (effects.json) for matching publish/process and post-process enqueue.

## Commands

```text
python tools/video_java/seed_p2_fixture.py
python tools/video_java/certify.py --phase 2
```

## Case table

| case_id | layers | notes |
|---------|--------|-------|
| vj_p2_face_publish_process | api, side_effect | POST /video/face/matching/publish + process |
| vj_p2_plate_publish_process | api, side_effect | POST /video/plate/matching/publish + process |
| vj_p2_post_process_enqueue | side_effect | alert hook → post_process enqueue follow-on |
| vj_p2_snap_list_or_create | api | GET snap space list + POST create |
| vj_p2_record_query | api | GET /video/record/space/list |
| vj_p2_playback_url | api | SUBSTITUTE: GET /video/playback/list (no stable play-url) |
| vj_p2_patrol_task_list | api | GET algorithm task list task_type=patrol |
| vj_p2_media_hook | api | POST /video/media/hook/snap/completed |
| vj_p2_detection_region_get | api | GET device-detection regions |

## Case results

| case_id | ok | layers |
|---------|----|--------|
| vj_p2_face_publish_process | False | api:fail, side_effect:fail |
| vj_p2_plate_publish_process | False | api:fail, side_effect:fail |
| vj_p2_post_process_enqueue | False | side_effect:fail |
| vj_p2_snap_list_or_create | False | api:fail |
| vj_p2_record_query | False | api:fail |
| vj_p2_playback_url | False | api:fail |
| vj_p2_patrol_task_list | False | api:fail |
| vj_p2_media_hook | False | api:fail |
| vj_p2_detection_region_get | False | api:fail |

## Documented exemptions (this run)

- (none)
