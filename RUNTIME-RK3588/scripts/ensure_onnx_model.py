#!/usr/bin/env python3
"""Export Ultralytics YOLO .pt → .onnx for RUNTIME (v8 / v11 / v26).

Idempotent: skips when output exists and is newer than input (unless --force).

Usage:
  python3 ensure_onnx_model.py --input yolov8n.pt --output /path/to/yolov8n.onnx
  python3 ensure_onnx_model.py --input /models/3/model.pt
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _write_names(onnx_path: Path, names) -> None:
    names_path = onnx_path.with_suffix(".names")
    lines: list[str] = []
    if isinstance(names, dict):
        for i in range(len(names)):
            lines.append(str(names.get(i, names.get(str(i), f"class_{i}"))))
    elif isinstance(names, (list, tuple)):
        lines = [str(x) for x in names]
    else:
        return
    names_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote_names={names_path} count={len(lines)}")


def export_pt(input_path: Path, output_path: Path, imgsz: int, force: bool) -> int:
    if not force and output_path.is_file():
        if (not input_path.is_file()) or output_path.stat().st_mtime >= input_path.stat().st_mtime:
            print(f"skip_existing={output_path}")
            return 0

    try:
        from ultralytics import YOLO
    except Exception as exc:  # pragma: no cover
        print(f"ERROR: ultralytics required to export .pt → onnx: {exc}", file=sys.stderr)
        return 2

    # Allow bare names like yolo11n.pt (ultralytics downloads)
    model_ref = str(input_path) if input_path.is_file() else input_path.name
    print(f"loading={model_ref}")
    model = YOLO(model_ref)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Export into target directory; ultralytics names file after model stem
    print(f"exporting imgsz={imgsz} → {output_path}")
    exported = model.export(format="onnx", imgsz=imgsz, simplify=True, opset=12)
    exported_path = Path(str(exported))
    if exported_path.resolve() != output_path.resolve():
        output_path.write_bytes(exported_path.read_bytes())
        # keep ultralytics artifact too; prefer canonical output_path
        print(f"copied_from={exported_path}")

    names = getattr(getattr(model, "model", None), "names", None) or getattr(model, "names", None)
    if names:
        _write_names(output_path, names)
        # also dump json sidecar for debugging
        meta = output_path.with_suffix(".names.json")
        meta.write_text(json.dumps(names, ensure_ascii=False, indent=2), encoding="utf-8")

    if not output_path.is_file():
        print(f"ERROR: export produced no file at {output_path}", file=sys.stderr)
        return 3
    print(f"ok={output_path} size={output_path.stat().st_size}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", "-i", required=True, help=".pt path or ultralytics model name")
    ap.add_argument("--output", "-o", default="", help="output .onnx path (default: sibling)")
    ap.add_argument("--imgsz", type=int, default=640, help="export imgsz (yolo26 may use 640/1280)")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    input_path = Path(args.input)
    if args.output:
        output_path = Path(args.output)
    else:
        if input_path.suffix.lower() == ".pt":
            output_path = input_path.with_suffix(".onnx")
        else:
            output_path = Path(str(input_path) + ".onnx")

    # YOLO26: slightly larger default if name hints
    imgsz = args.imgsz
    name = input_path.name.lower()
    if "yolo26" in name and args.imgsz == 640:
        imgsz = 640  # keep 640 for portable RUNTIME; VIDEO may raise at runtime

    return export_pt(input_path, output_path, imgsz=imgsz, force=args.force)


if __name__ == "__main__":
    sys.exit(main())
