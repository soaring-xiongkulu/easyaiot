#!/usr/bin/env python3
"""从 panel-logo.png 生成圆形白底图标（外圈透明），与 Ubuntu/Windows/macOS 共用。"""
from __future__ import annotations

import argparse
import sys

from PIL import Image, ImageDraw


def make_circle_icon(src: str, dst: str, size: int = 512) -> None:
    img = Image.open(src).convert("RGBA")
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    # 与 Ubuntu pack_deb.sh / Windows build.sh 保持一致
    margin = int(size * 0.015)
    draw.ellipse((margin, margin, size - margin, size - margin), fill=(255, 255, 255, 255))
    inner = int((size - margin * 2) * 0.98)
    img.thumbnail((inner, inner), Image.Resampling.LANCZOS)
    x = (size - img.width) // 2
    y = (size - img.height) // 2
    canvas.alpha_composite(img, (x, y))
    if dst.lower().endswith(".ico"):
        canvas.save(
            dst,
            format="ICO",
            sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )
    else:
        canvas.save(dst, format="PNG", optimize=True)


def main() -> int:
    p = argparse.ArgumentParser(description="Make circular white-bg panel icon")
    p.add_argument("src", help="source logo PNG (COMPILE/assets/panel-logo.png)")
    p.add_argument("dst", help="output .png or .ico")
    p.add_argument("--size", type=int, default=512)
    args = p.parse_args()
    make_circle_icon(args.src, args.dst, args.size)
    print(f"wrote {args.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
