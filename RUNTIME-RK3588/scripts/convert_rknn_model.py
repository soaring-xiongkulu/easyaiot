#!/usr/bin/env python3
"""Convert Rockchip's optimized nine-output YOLOv8 ONNX to RK3588 RKNN.

Run this on the RKNN-Toolkit2 conversion host, not inside the runtime process.
The default is INT8 because it is the high-throughput RK3588 deployment path.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Rockchip YOLOv8 9-output ONNX -> RK3588 INT8 RKNN")
    parser.add_argument("input", type=Path, help="Rockchip optimized 9-output YOLOv8 ONNX")
    parser.add_argument("output", type=Path, help="output .rknn")
    parser.add_argument("--dataset", type=Path, help="INT8 calibration list, one image path per line")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.input.suffix.lower() != ".onnx" or not args.input.is_file():
        parser.error("input must be an existing .onnx file")
    if args.output.suffix.lower() != ".rknn":
        parser.error("output must end in .rknn")
    if args.dataset is None or not args.dataset.is_file():
        parser.error("INT8 conversion requires --dataset")

    try:
        import onnx
    except ImportError as exc:
        raise SystemExit("the onnx package is required to validate the 9-output contract") from exc
    graph = onnx.load(str(args.input), load_external_data=False).graph
    if len(graph.input) != 1 or len(graph.output) != 9:
        parser.error(
            f"expected Rockchip optimized YOLOv8 with 1 input/9 outputs; "
            f"got {len(graph.input)} input(s)/{len(graph.output)} output(s)"
        )

    try:
        from rknn.api import RKNN
    except ImportError as exc:
        raise SystemExit("RKNN-Toolkit2 is required on the conversion host") from exc

    args.output.parent.mkdir(parents=True, exist_ok=True)
    rknn = RKNN(verbose=args.verbose)
    try:
        ret = rknn.config(
            mean_values=[[0, 0, 0]],
            std_values=[[255, 255, 255]],
            target_platform="rk3588",
            optimization_level=3,
        )
        if ret != 0:
            raise RuntimeError(f"rknn.config failed: {ret}")
        ret = rknn.load_onnx(model=str(args.input))
        if ret != 0:
            raise RuntimeError(f"rknn.load_onnx failed: {ret}")
        ret = rknn.build(
            do_quantization=True,
            dataset=str(args.dataset),
        )
        if ret != 0:
            raise RuntimeError(f"rknn.build failed: {ret}")
        ret = rknn.export_rknn(str(args.output))
        if ret != 0:
            raise RuntimeError(f"rknn.export_rknn failed: {ret}")
    finally:
        rknn.release()
    print(f"RKNN_OK: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
