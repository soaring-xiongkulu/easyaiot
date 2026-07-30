"""
检测结果的 UTF-8 标签绘制工具。

此文件由 EDGE/scripts/sync_runtime_from_video.sh 从 VIDEO 公共实现同步，
EDGE 运行时保留独立副本，避免依赖 VIDEO 源码目录。
"""
from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

_DEFAULT_FONT_SIZE = 28


def _font_candidates() -> list[Path]:
    candidates: list[Path] = []
    for env_name in ("VIDEO_OVERLAY_FONT_PATH", "YOLO_RESULT_FONT_PATH"):
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
def get_overlay_font(font_size: int = _DEFAULT_FONT_SIZE) -> Optional[ImageFont.FreeTypeFont]:
    for candidate in _font_candidates():
        if not candidate.is_file():
            continue
        try:
            return ImageFont.truetype(str(candidate), font_size)
        except OSError as exc:
            logger.warning("算法中文字体加载失败 %s: %s", candidate, exc)
    return None


@lru_cache(maxsize=1)
def _warn_missing_cjk_font_once() -> None:
    logger.warning(
        "未找到算法中文字体，非 ASCII 类别名将回退 OpenCV；"
        "请设置 VIDEO_OVERLAY_FONT_PATH 指向可读的 .ttf/.ttc 文件"
    )


def _normalize_color(color_bgr: Tuple[int, int, int]) -> Tuple[int, int, int]:
    return tuple(int(channel) for channel in color_bgr)


def _draw_ascii_label(
    frame: np.ndarray,
    text: str,
    box_left: int,
    box_top: int,
    color_bgr: Tuple[int, int, int],
    font_scale: float,
    font_thickness: int,
    background_bgr: Optional[Tuple[int, int, int]],
) -> None:
    (text_width, text_height), baseline = cv2.getTextSize(
        text,
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        font_thickness,
    )
    text_x = max(0, min(int(box_left), max(0, frame.shape[1] - text_width)))
    text_y = max(text_height + 5, int(box_top) - 5)
    text_y = min(frame.shape[0] - max(1, baseline), text_y)
    if background_bgr is not None:
        cv2.rectangle(
            frame,
            (text_x - 2, max(0, text_y - text_height - 2)),
            (min(frame.shape[1] - 1, text_x + text_width + 2), min(frame.shape[0] - 1, text_y + baseline + 2)),
            _normalize_color(background_bgr),
            cv2.FILLED,
        )
    cv2.putText(
        frame,
        text,
        (text_x, text_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        _normalize_color(color_bgr),
        font_thickness,
        lineType=cv2.LINE_AA,
    )


def draw_detection_label(
    frame: np.ndarray,
    text: str,
    box_left: int,
    box_top: int,
    color_bgr: Tuple[int, int, int],
    *,
    font_scale: float = 0.8,
    font_thickness: int = 2,
    cjk_font_size: int = _DEFAULT_FONT_SIZE,
    background_bgr: Optional[Tuple[int, int, int]] = None,
) -> bool:
    normalized_text = str(text or "")
    if normalized_text.isascii():
        _draw_ascii_label(
            frame,
            normalized_text,
            int(box_left),
            int(box_top),
            color_bgr,
            font_scale,
            font_thickness,
            background_bgr,
        )
        return False

    font = get_overlay_font(cjk_font_size)
    if font is None:
        _warn_missing_cjk_font_once()
        _draw_ascii_label(
            frame,
            normalized_text,
            int(box_left),
            int(box_top),
            color_bgr,
            font_scale,
            font_thickness,
            background_bgr,
        )
        return False

    frame_height, frame_width = frame.shape[:2]
    bbox = font.getbbox(normalized_text)
    text_width = max(1, bbox[2] - bbox[0])
    text_height = max(1, bbox[3] - bbox[1])
    padding = 2

    text_left = max(0, min(int(box_left), frame_width - text_width - padding))
    text_top = max(0, int(box_top) - text_height - 5)
    roi_left = max(0, text_left - padding)
    roi_top = max(0, text_top - padding)
    roi_right = min(frame_width, text_left + text_width + padding)
    roi_bottom = min(frame_height, text_top + text_height + padding)
    if roi_right <= roi_left or roi_bottom <= roi_top:
        return False

    roi_bgr = frame[roi_top:roi_bottom, roi_left:roi_right]
    if background_bgr is not None:
        roi_bgr[:] = _normalize_color(background_bgr)
    roi_rgb = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(roi_rgb)
    drawer = ImageDraw.Draw(pil_image)
    draw_x = text_left - roi_left - bbox[0]
    draw_y = text_top - roi_top - bbox[1]
    color_rgb = (
        int(color_bgr[2]),
        int(color_bgr[1]),
        int(color_bgr[0]),
    )
    drawer.text((draw_x, draw_y), normalized_text, font=font, fill=color_rgb)
    frame[roi_top:roi_bottom, roi_left:roi_right] = cv2.cvtColor(
        np.asarray(pil_image),
        cv2.COLOR_RGB2BGR,
    )
    return True
