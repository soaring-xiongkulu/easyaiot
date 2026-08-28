"""Persist auto-label output while enforcing dataset retention policy."""
import json

import requests


def write_auto_label_result(
    java_url: str,
    dataset_id: int,
    image_id: int,
    annotations: list,
    *,
    keep_annotated_images_only: bool = True,
    timeout: int = 15,
) -> tuple[str, str]:
    """Write annotations or remove an empty image. Returns (JSON, action)."""
    annotations_json = json.dumps(annotations, ensure_ascii=False)
    base_url = java_url.rstrip('/')

    if keep_annotated_images_only and not annotations:
        response = requests.delete(
            f'{base_url}/admin-api/dataset/image/delete/{image_id}',
            timeout=timeout,
        )
        action = 'deleted'
    else:
        response = requests.put(
            f'{base_url}/admin-api/dataset/image/update',
            json={
                'id': image_id,
                'datasetId': dataset_id,
                'annotations': annotations_json,
                'completed': 1 if annotations else 0,
            },
            timeout=timeout,
        )
        action = 'updated'

    if response.status_code != 200:
        raise RuntimeError(f'写入数据集图片失败: HTTP {response.status_code}')
    try:
        body = response.json()
    except (TypeError, ValueError):
        body = {}
    if isinstance(body, dict) and body.get('code') not in (None, 0):
        raise RuntimeError(f'写入数据集图片失败: {body.get("msg") or body.get("code")}')
    return annotations_json, action
