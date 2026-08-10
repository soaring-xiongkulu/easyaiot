#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fetch industry-standard YOLO/OpenVINO sample videos for runtime-parity.

Canonical upstream (same family as rebekah-learn / rebekah-core-rebuild loops):
  https://github.com/intel-iot-devkit/sample-videos

Default: download into testdata/runtime-parity/media/
Optional: --from-local-loops copies from an existing rebekah loops dir via
  printing a safe_fsops dry-run command (does not execute copy itself).
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

# Raw GitHub URLs (master). These are the Intel IoT DevKit sample clips used
# widely with OpenVINO / YOLO demos — not synthetic color bars.
SAMPLES = (
    {
        "name": "people-detection.mp4",
        "url": "https://github.com/intel-iot-devkit/sample-videos/raw/master/people-detection.mp4",
        "parity_alias": "media_person_roi_30s.mp4",
    },
    {
        "name": "one-by-one-person-detection.mp4",
        "url": "https://github.com/intel-iot-devkit/sample-videos/raw/master/one-by-one-person-detection.mp4",
        "parity_alias": None,
    },
    {
        "name": "person-bicycle-car-detection.mp4",
        "url": "https://github.com/intel-iot-devkit/sample-videos/raw/master/person-bicycle-car-detection.mp4",
        "parity_alias": None,
    },
    {
        "name": "face-demographics-walking-and-pause.mp4",
        "url": "https://github.com/intel-iot-devkit/sample-videos/raw/master/face-demographics-walking-and-pause.mp4",
        "parity_alias": None,
    },
)

# Ultralytics still used only as optional tiny auxiliary (not a replacement for the four).
AUX_STILLS = ()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > 100_000:
        print(f"SKIP exists ({dest.stat().st_size} bytes): {dest}")
        return
    print(f"GET {url}")
    print(f" -> {dest}")
    tmp = dest.with_suffix(dest.suffix + ".part")
    urllib.request.urlretrieve(url, tmp)  # nosec B310 - fixed allowlist URLs above
    tmp.replace(dest)
    print(f"OK {dest.stat().st_size} bytes sha256={_sha256(dest)[:16]}...")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Default: <repo>/testdata/runtime-parity/media",
    )
    p.add_argument(
        "--from-local-loops",
        type=Path,
        default=None,
        help="If set, print safe_fsops copy dry-run commands from this loops dir "
        "(e.g. F:/biofactory/rebekah-core-rebuild/testdata/loops). Does not copy.",
    )
    p.add_argument(
        "--also-alias",
        action="store_true",
        help="Also write parity_alias filenames (hardlink or copy) for manifest ids.",
    )
    args = p.parse_args()
    root = _repo_root()
    out = args.out_dir or (root / "testdata" / "runtime-parity" / "media")
    out = out.resolve()

    if args.from_local_loops:
        loops = args.from_local_loops.resolve()
        print("LOCAL LOOPS MODE — will NOT copy; use safe_fsops after orchestrator review:")
        for s in SAMPLES:
            src = loops / s["name"]
            dst = out / s["name"]
            if not src.is_file():
                print(f"MISSING {src}")
                continue
            print(
                f'python tools/runtime_parity/safe_fsops.py copy --src "{src}" --dst "{dst}" '
                f'--allow-root "{root}" --allow-root "{loops.parent.parent}"'
            )
        return 0

    print(f"Downloading Intel IoT sample-videos into {out}")
    print("Upstream: https://github.com/intel-iot-devkit/sample-videos")
    for s in SAMPLES:
        dest = out / s["name"]
        download(s["url"], dest)
        if args.also_alias and s.get("parity_alias"):
            alias = out / s["parity_alias"]
            if not alias.exists():
                try:
                    alias.hardlink_to(dest)
                except OSError:
                    alias.write_bytes(dest.read_bytes())
                print(f"ALIAS {alias.name} -> {dest.name}")

    readme = out / "README.md"
    readme.write_text(
        """# runtime-parity media

## Provenance (required)

Primary clips are **Intel IoT DevKit sample-videos**, the same family used by
rebekah-learn / rebekah-core-rebuild loop publishers and OpenVINO YOLO demos:

- Upstream: https://github.com/intel-iot-devkit/sample-videos
- Files: `people-detection.mp4`, `one-by-one-person-detection.mp4`,
  `person-bicycle-car-detection.mp4`, `face-demographics-walking-and-pause.mp4`

Fetch:

```bat
python tools\\runtime_parity\\fetch_parity_media.py --also-alias
```

Or copy from a local rebekah loops tree (orchestrator must approve safe_fsops):

```bat
python tools\\runtime_parity\\fetch_parity_media.py --from-local-loops F:\\biofactory\\rebekah-core-rebuild\\testdata\\loops
```

## Forbidden

Do **not** use ffmpeg color-bar / synthetic clips as P0 detection media.
""",
        encoding="utf-8",
    )
    print(f"Wrote {readme}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
