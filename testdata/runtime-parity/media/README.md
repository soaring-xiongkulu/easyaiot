# runtime-parity media

## Provenance (required)

Primary clips are **Intel IoT DevKit sample-videos** — the same family used by
rebekah-learn / rebekah-core-rebuild loop publishers and OpenVINO YOLO demos:

| File | Upstream |
|------|----------|
| `people-detection.mp4` | https://github.com/intel-iot-devkit/sample-videos |
| `one-by-one-person-detection.mp4` | same |
| `person-bicycle-car-detection.mp4` | same |
| `face-demographics-walking-and-pause.mp4` | same |

Fetch (network):

```bat
python tools\runtime_parity\fetch_parity_media.py
```

Or copy from a local rebekah loops tree that already holds these files
(orchestrator must approve `safe_fsops` dry-run → execute):

```bat
python tools\runtime_parity\fetch_parity_media.py --from-local-loops F:\biofactory\rebekah-core-rebuild\testdata\loops
```

MP4 binaries are **gitignored**; CI/dev machines must fetch or copy them.

## Forbidden

Do **not** use ffmpeg color-bar / synthetic clips as P0 detection media.
