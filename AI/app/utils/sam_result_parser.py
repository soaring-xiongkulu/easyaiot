"""
SAM 推理结果 → 标注工具 JSON 格式转换
"""
import logging

logger = logging.getLogger(__name__)


def to_annotations(
    result: dict,
    image_width: int,
    image_height: int,
    *,
    annotation_type: str = 'rectangle',
) -> list:
    """将 SamService.predict 返回结构转为标注工具 annotations 列表。"""
    if not result or not image_width or not image_height:
        return []

    annotations = []
    predictions = result.get('predictions') or []
    masks = result.get('masks') or []

    if annotation_type == 'polygon' and masks:
        for mask in masks:
            try:
                class_name = mask.get('class_name') or 'object'
                confidence = float(mask.get('confidence', 0))
                xyn = mask.get('xyn') or []
                if not xyn:
                    xy = mask.get('xy') or []
                    if xy and xy[0]:
                        xyn = [
                            [
                                {'x': x / image_width, 'y': y / image_height}
                                for x, y in xy[0]
                            ]
                        ]
                contour = xyn[0] if xyn else []
                if len(contour) < 3:
                    continue
                points = [
                    {'x': float(p['x'] if isinstance(p, dict) else p[0]),
                     'y': float(p['y'] if isinstance(p, dict) else p[1])}
                    for p in contour
                ]
                annotations.append({
                    'label': class_name,
                    'confidence': confidence,
                    'points': points,
                    'type': 'polygon',
                    'auto': True,
                    'color': '#722ed1',
                    'source': 'sam3',
                })
            except Exception as e:
                logger.warning('解析 SAM mask 失败: %s', e)
        return annotations

    for pred in predictions:
        try:
            class_name = pred.get('class_name') or str(pred.get('class', 'object'))
            confidence = float(pred.get('confidence', 0))
            bbox = pred.get('bbox') or []
            if len(bbox) < 4:
                continue
            x1, y1, x2, y2 = bbox[:4]
            x1 = max(0, min(float(x1), image_width))
            y1 = max(0, min(float(y1), image_height))
            x2 = max(0, min(float(x2), image_width))
            y2 = max(0, min(float(y2), image_height))
            norm_x1, norm_y1 = x1 / image_width, y1 / image_height
            norm_x2, norm_y2 = x2 / image_width, y2 / image_height
            annotations.append({
                'label': class_name,
                'confidence': confidence,
                'points': [
                    {'x': norm_x1, 'y': norm_y1},
                    {'x': norm_x2, 'y': norm_y1},
                    {'x': norm_x2, 'y': norm_y2},
                    {'x': norm_x1, 'y': norm_y2},
                ],
                'type': 'rectangle',
                'auto': True,
                'color': '#722ed1',
                'source': 'sam3',
            })
        except Exception as e:
            logger.warning('解析 SAM prediction 失败: %s', e)
    return annotations
