#!/usr/bin/env python3
"""Face inference CLI — InsightFace ONNX + Milvus; invoked by Java subprocess."""
from __future__ import annotations

import argparse
import base64
import json
import sys
import tempfile
from pathlib import Path

from _bootstrap import bootstrap


def _emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def cmd_health() -> dict:
    try:
        bootstrap()
        from app.services.face_recognition_service import get_face_recognition_service

        svc = get_face_recognition_service()
        svc._ensure_rec_model()
        return {
            "available": True,
            "engine": "insightface_onnx",
            "milvus_uri": svc.milvus_uri,
            "collection": svc.collection_name,
        }
    except Exception as exc:
        return {"available": False, "error": str(exc)}


def _load_image(image_path: str | None, image_base64: str | None):
    import cv2
    import numpy as np

    if image_path:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"cannot read image: {image_path}")
        return img
    if image_base64:
        raw = base64.b64decode(image_base64)
        arr = np.frombuffer(raw, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("cannot decode base64 image")
        return img
    raise ValueError("image_path or image_base64 required")


def cmd_match(args: argparse.Namespace) -> dict:
    bootstrap()
    from app.services.face_recognition_service import get_face_recognition_service

    image = _load_image(args.image_path, args.image_base64)
    threshold = float(args.threshold or 0.55)
    svc = get_face_recognition_service()
    result = svc.match_image_file_in_library(int(args.library_id), image, threshold)
    return {"ok": True, "result": result}


def cmd_recognize(args: argparse.Namespace) -> dict:
    bootstrap()
    from app.services.face_recognition_service import get_face_recognition_service

    image = _load_image(args.image_path, args.image_base64)
    top_k = int(args.top_k or 3)
    library_id = int(args.library_id) if args.library_id else None
    threshold = float(args.threshold) if args.threshold else None
    svc = get_face_recognition_service()
    result = svc.recognize(image, top_k=top_k, library_id=library_id, threshold=threshold)
    return {"ok": True, "result": result}


def main() -> int:
    parser = argparse.ArgumentParser(description="face inference worker")
    parser.add_argument("command", choices=["health", "match", "recognize"])
    parser.add_argument("--image-path")
    parser.add_argument("--image-base64")
    parser.add_argument("--library-id", type=int)
    parser.add_argument("--threshold", type=float)
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()
    try:
        if args.command == "health":
            _emit(cmd_health())
            return 0
        if args.command == "match":
            if args.library_id is None:
                _emit({"ok": False, "error": "library_id required"})
                return 1
            _emit(cmd_match(args))
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
