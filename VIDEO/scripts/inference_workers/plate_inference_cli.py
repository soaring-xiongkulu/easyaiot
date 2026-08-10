#!/usr/bin/env python3
"""Plate OCR CLI — PaddleOCR/ONNX pipeline; invoked by Java subprocess."""
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
        from app.utils.plate_capture_service import get_plate_pipeline

        get_plate_pipeline()
        return {"available": True, "engine": "paddleocr_onnx"}
    except Exception as exc:
        return {"available": False, "error": str(exc)}


def _load_frame(image_path: str | None, image_base64: str | None):
    import cv2

    if image_path:
        frame = cv2.imread(image_path)
        if frame is None:
            raise ValueError(f"cannot read image: {image_path}")
        return frame
    if image_base64:
        raw = base64.b64decode(image_base64)
        arr = np.frombuffer(raw, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("cannot decode base64 image")
        return frame
    raise ValueError("image_path or image_base64 required")


def cmd_recognize(args: argparse.Namespace) -> dict:
    bootstrap()
    from app.utils.plate_capture_service import detect_and_recognize_plates

    frame = _load_frame(args.image_path, args.image_base64)
    plates = detect_and_recognize_plates(frame)
    return {"ok": True, "plates": plates}


def main() -> int:
    parser = argparse.ArgumentParser(description="plate inference worker")
    parser.add_argument("command", choices=["health", "recognize"])
    parser.add_argument("--image-path")
    parser.add_argument("--image-base64")
    args = parser.parse_args()
    try:
        if args.command == "health":
            _emit(cmd_health())
            return 0
        if args.command == "recognize":
            _emit(cmd_recognize(args))
            return 0
    except Exception as exc:
        _emit({"ok": False, "error": str(exc)})
        return 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
