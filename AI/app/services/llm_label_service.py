"""HARNESS 大模型自然语言冷启动标注。"""
from __future__ import annotations

import base64
import json
import re
from typing import Any

from db_models import LLMModel
from app.services.llm_gateway_client import invoke_vision


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = re.sub(r'^```(?:json)?\s*', '', (text or '').strip(), flags=re.I)
    cleaned = re.sub(r'\s*```$', '', cleaned).strip()
    match = re.search(r'\{[\s\S]*\}', cleaned)
    if not match:
        raise ValueError('大模型未返回可解析的标注 JSON')
    value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise ValueError('大模型标注结果必须为 JSON 对象')
    return value


def _normalize_bbox(raw: Any) -> list[float] | None:
    if not isinstance(raw, list) or len(raw) != 4:
        return None
    try:
        box = [max(0.0, min(1.0, float(value))) for value in raw]
    except (TypeError, ValueError):
        return None
    if box[2] <= box[0] or box[3] <= box[1]:
        return None
    return box


def parse_llm_annotations(text: str, confidence_threshold: float = 0.0) -> list[dict]:
    """把视觉大模型 JSON 转换成平台归一化矩形标注。"""
    payload = _extract_json(text)
    objects = payload.get('objects')
    if not isinstance(objects, list):
        return []
    annotations = []
    for item in objects:
        if not isinstance(item, dict):
            continue
        label = str(item.get('label') or '').strip()
        bbox = _normalize_bbox(item.get('bbox'))
        try:
            confidence = float(item.get('confidence', 1.0))
        except (TypeError, ValueError):
            confidence = 1.0
        if not label or not bbox or confidence < confidence_threshold:
            continue
        x1, y1, x2, y2 = bbox
        annotations.append({
            'type': 'rectangle',
            'label': label,
            'points': [
                {'x': x1, 'y': y1}, {'x': x2, 'y': y1},
                {'x': x2, 'y': y2}, {'x': x1, 'y': y2},
            ],
            'confidence': confidence,
            'source': 'llm-harness',
        })
    return annotations


def build_scene_prompt(scene_description: str, output_labels: list[str] | None = None) -> str:
    labels = '、'.join(output_labels or []) or '从场景描述中归纳简洁、稳定的中文标签名'
    return (
        '你是工业视觉数据标注专家。请严格按照以下真实业务场景识别图片中的目标：\n'
        f'{scene_description.strip()}\n'
        f'允许的输出标签：{labels}。\n'
        '只返回 JSON，不要 Markdown，不要解释。格式：'
        '{"objects":[{"label":"标签名","bbox":[x1,y1,x2,y2],"confidence":0.95}]}。'
        'bbox 必须是 0 到 1 的归一化坐标；没有符合条件的目标时返回 {"objects":[]}。'
        '严格遵守场景描述中的状态、环境和排除条件，不要标注不确定目标。'
    )


def label_image_with_llm(
    image_path: str,
    scene_description: str,
    output_labels: list[str] | None = None,
    confidence_threshold: float = 0.0,
) -> tuple[list[dict], int]:
    """使用当前唯一启用的大模型标注单张图片，返回（标注，模型 ID）。"""
    model = LLMModel.query.filter_by(is_active=True).order_by(LLMModel.id).first()
    if not model:
        raise RuntimeError('未启用任何大模型，请先在大模型管理中启用视觉模型')
    with open(image_path, 'rb') as image_file:
        image_b64 = base64.b64encode(image_file.read()).decode('utf-8')
    result = invoke_vision(
        model,
        image_b64,
        build_scene_prompt(scene_description, output_labels),
        mime_type='image/jpeg',
    )
    return parse_llm_annotations(result.get('response', ''), confidence_threshold), model.id
