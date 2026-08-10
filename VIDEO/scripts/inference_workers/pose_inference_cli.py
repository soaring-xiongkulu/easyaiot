#!/usr/bin/env python3
"""Pose extraction CLI — YOLO pose; invoked by Java subprocess."""
from __future__ import annotations

import argparse
import base64
import json
import sys

import numpy as np

from _bootstrap import bootstrap


def _emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def cmd_health() -> dict:
    try:
        bootstrap()
        from app.utils.pose_analysis import load_pose_model, DEFAULT_POSE_CONF

        load_pose_model({"model_file_path": "yolo26n-pose.pt", "conf": DEFAULT_POSE_CONF})
        return {"available": True, "engine": "yolo_pose"}
    except Exception as exc:
        return {"available": False, "error": str(exc)}


def _load_bytes(image_path: str | None, image_base64: str | None) -> bytes:
    if image_path:
        with open(image_path, "rb") as f:
            return f.read()
    if image_base64:
        return base64.b64decode(image_base64)
    raise ValueError("image_path or image_base64 required")


def cmd_extract(args: argparse.Namespace) -> dict:
    bootstrap()
    from app.services.scenario_pose_library_service import extract_keypoints_from_image_bytes

    raw = _load_bytes(args.image_path, args.image_base64)
    conf = float(args.conf or 0.25)
    persons = extract_keypoints_from_image_bytes(raw, conf=conf)
    for person in persons:
        kps = person.get("keypoints") or []
        person.setdefault("feature_vector", None)
        person.setdefault("keypointCount", len(kps))
        person.setdefault("poseType", "body17")
    return {"ok": True, "count": len(persons), "persons": persons}


def main() -> int:
    parser = argparse.ArgumentParser(description="pose inference worker")
    parser.add_argument("command", choices=["health", "extract"])
    parser.add_argument("--image-path")
    parser.add_argument("--image-base64")
    parser.add_argument("--conf", type=float, default=0.25)
    args = parser.parse_args()
    try:
        if args.command == "health":
            _emit(cmd_health())
            return 0
        if args.command == "extract":
            _emit(cmd_extract(args))
            return 0
    except Exception as exc:
        _emit({"ok": False, "error": str(exc)})
        return 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
