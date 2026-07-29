"""独立 AI 服务的中文检测标签字体与绘制工具。"""
from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)


def _font_candidates() -> list[Path]:
    candidates: list[Path] = []
    for env_name in ("YOLO_RESULT_FONT_PATH", "ULTRALYTICS_PLOT_FONT"):
        configured = (os.environ.get(env_name) or "").strip()
        if configured:
            candidates.append(Path(configured).expanduser())
    candidates.extend(
        [
            Path("/app/data/fonts/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"),
            Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"),
            Path("/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"),
            Path("/System/Library/Fonts/PingFang.ttc"),
            Path("/System/Library/Fonts/STHeiti Light.ttc"),
        ]
    )
    return candidates


@lru_cache(maxsize=8)
def get_pil_annotation_font(size: int = 14):
    """加载 AI 推理结果标注使用的 CJK 字体。"""
    from PIL import ImageFont

    for candidate in _font_candidates():
        if not candidate.is_file():
            continue
        try:
            return ImageFont.truetype(str(candidate), size)
        except OSError as exc:
            logger.warning("AI 服务中文字体加载失败 %s: %s", candidate, exc)
    _warn_missing_cjk_font_once()
    return None


@lru_cache(maxsize=1)
def _warn_missing_cjk_font_once() -> None:
    logger.warning(
        "未找到 AI 服务中文字体；请设置 YOLO_RESULT_FONT_PATH "
        "指向可读的 .ttf/.ttc 文件"
    )


def draw_utf8_label_on_bgr(
    img,
    text: str,
    org_xy: tuple[int, int],
    font_size: int = 14,
    text_color_rgb: tuple[int, int, int] = (0, 0, 0),
) -> bool:
    """在 BGR 图像上绘制 UTF-8 文本，成功返回 True。"""
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw

    font = get_pil_annotation_font(font_size)
    if font is None:
        return False

    height, width = img.shape[:2]
    bbox = font.getbbox(str(text))
    text_width = max(1, bbox[2] - bbox[0])
    text_height = max(1, bbox[3] - bbox[1])
    left, top = int(org_xy[0]), int(org_xy[1])
    left = max(0, min(left, width - text_width - 1))
    top = max(0, min(top, height - text_height - 1))

    canvas_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(canvas_rgb)
    drawer = ImageDraw.Draw(pil_image)
    drawer.text(
        (left - bbox[0], top - bbox[1]),
        str(text),
        font=font,
        fill=text_color_rgb,
    )
    img[:] = cv2.cvtColor(np.asarray(pil_image), cv2.COLOR_RGB2BGR)
    return True


__all__ = ["draw_utf8_label_on_bgr", "get_pil_annotation_font"]
