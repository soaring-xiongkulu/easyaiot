# FR-B43 health probes

- generated_at: 20260810T224110Z
- base_url: http://127.0.0.1:48096
- server_up: True

## Python-first cites

- face ping: `VIDEO/_retired_python_video/app/services/face_vector_store.py ping L164-179`
- face health: `VIDEO/_retired_python_video/app/blueprints/face.py health L83-90`
- plate status: `VIDEO/_retired_python_video/app/utils/plate_model_download.py get_plate_model_status L47-62`
- plate health: `VIDEO/_retired_python_video/app/blueprints/plate.py health L55-59`

## Results

| id | http | code | ok | collection_exists / exists | model_loaded |
|----|------|------|-----|------------------------------|--------------|
| face_health_truthful | 200 | 0 | True | True/— | True |
| plate_health_truthful | 200 | 0 | True | —/True | — |

