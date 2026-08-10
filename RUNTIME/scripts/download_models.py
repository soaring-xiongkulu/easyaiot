#!/usr/bin/env python3
"""Download Ultralytics YOLO weights and export ONNX for RUNTIME.

Canonical names (align VIDEO model_ids -1/-2/-3):
  yolo11n / yolov8n / yolo26n

Usage:
  RUNTIME_PYTHON=python python3 RUNTIME/scripts/download_models.py
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = Path(os.getenv("RUNTIME_MODEL_DIR", str(ROOT / "models")))
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# name → description
MODELS = {
    "yolo11n": "默认 builtin (-1)，classic detect",
    "yolov8n": "builtin (-2)，classic detect",
    "yolo26n": "builtin (-3)，end2end [N,6]",
}


def download_and_export(model_name: str, description: str) -> bool:
    print(f"\n{'=' * 60}")
    print(f"处理: {model_name} ({description})")
    print(f"{'=' * 60}")
    try:
        print(f"加载 {model_name}.pt ...")
        model = YOLO(f"{model_name}.pt")
        print("导出 ONNX ...")
        onnx_path = Path(
            str(
                model.export(
                    format="onnx",
                    imgsz=640,
                    simplify=True,
                    opset=12,
                )
            )
        )
        target = MODEL_DIR / f"{model_name}.onnx"
        if onnx_path.resolve() != target.resolve():
            shutil.copy2(onnx_path, target)
        # Keep .pt next to onnx when ultralytics downloaded it locally
        for cand in (Path(f"{model_name}.pt"), Path.cwd() / f"{model_name}.pt"):
            if cand.is_file():
                shutil.copy2(cand, MODEL_DIR / f"{model_name}.pt")
                break
        print(f"OK {target} ({target.stat().st_size} bytes)")
        # Historical alias for YOLO11
        if model_name == "yolo11n":
            legacy = MODEL_DIR / "yolov11n.onnx"
            if not legacy.exists():
                shutil.copy2(target, legacy)
                print(f"alias {legacy}")
        return True
    except Exception as exc:
        print(f"FAIL {model_name}: {exc}")
        return False


def ensure_coco_names() -> None:
    coco = MODEL_DIR / "coco.names"
    if coco.is_file():
        print(f"已有 {coco}")
        return
    # Prefer ensure_onnx sidecar or minimal stub — full list lives in repo coco.names
    repo_coco = ROOT / "models" / "coco.names"
    if repo_coco.is_file() and repo_coco.resolve() != coco.resolve():
        shutil.copy2(repo_coco, coco)
        print(f"复制 {coco}")
        return
    print(f"请手动放置 coco.names → {coco}")


def main() -> None:
    print("YOLO 模型下载/导出 →", MODEL_DIR)
    ensure_coco_names()
    ok = 0
    for name, desc in MODELS.items():
        if download_and_export(name, desc):
            ok += 1
    print(f"\n完成 {ok}/{len(MODELS)}")
    print(
        f"""
[ai]
model_path={MODEL_DIR}/yolo11n.onnx
classes_path={MODEL_DIR}/coco.names
threads=2
"""
    )


if __name__ == "__main__":
    main()
