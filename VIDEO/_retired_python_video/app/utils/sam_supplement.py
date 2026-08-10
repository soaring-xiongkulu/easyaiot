"""
算法任务 YOLO + SAM 补充识别（Pipeline 精修 / 开放词汇 / 告警确认）
"""
import base64
import json
import logging
import os
import threading
import time
from typing import Any, Optional

import cv2
import numpy as np
import requests

logger = logging.getLogger(__name__)

_frame_counter = 0
_frame_counter_lock = threading.Lock()


def _next_frame() -> int:
    global _frame_counter
    with _frame_counter_lock:
        _frame_counter += 1
        return _frame_counter


def load_sam_config_from_env() -> dict:
    """从环境变量解析 SAM 补充配置（由 algorithm_task_launcher 注入）。"""
    enabled = os.getenv('SAM_SUPPLEMENT_ENABLED', 'false').lower() in ('1', 'true', 'yes')
    if not enabled:
        return {'enabled': False}

    text_raw = os.getenv('SAM_TEXT_PROMPTS', '')
    text_prompts = [t.strip() for t in text_raw.split(',') if t.strip()] if text_raw else []

    config_raw = os.getenv('SAM_SUPPLEMENT_CONFIG', '')
    if config_raw:
        try:
            cfg = json.loads(config_raw)
            if isinstance(cfg, dict):
                return {
                    'enabled': True,
                    'pipeline_mode': cfg.get('pipeline_mode', 'none'),
                    'text_prompts': cfg.get('text_prompts') or text_prompts,
                    'conf': float(cfg.get('conf', 0.45)),
                    'trigger': cfg.get('trigger', 'on_interval'),
                    'interval_frames': int(cfg.get('interval_frames', 25)),
                    'merge_iou': float(cfg.get('merge_iou', 0.5)),
                    'return_masks': bool(cfg.get('return_masks', True)),
                }
        except Exception as e:
            logger.warning('解析 SAM_SUPPLEMENT_CONFIG 失败: %s', e)

    return {
        'enabled': True,
        'pipeline_mode': os.getenv('SAM_PIPELINE_MODE', 'none'),
        'text_prompts': text_prompts,
        'conf': float(os.getenv('SAM_CONF', '0.45')),
        'trigger': os.getenv('SAM_TRIGGER', 'on_interval'),
        'interval_frames': int(os.getenv('SAM_INTERVAL_FRAMES', '25')),
        'merge_iou': float(os.getenv('SAM_MERGE_IOU', '0.5')),
        'return_masks': os.getenv('SAM_RETURN_MASKS', 'true').lower() in ('1', 'true', 'yes'),
    }


def _bbox_iou(a: list, b: list) -> float:
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    if inter <= 0:
        return 0.0
    area_a = max(0, a[2] - a[0]) * max(0, a[3] - a[1])
    area_b = max(0, b[2] - b[0]) * max(0, b[3] - b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def merge_yolo_sam_detections(yolo_dets: list, sam_dets: list, iou_thresh: float = 0.5) -> list:
    """合并 YOLO 与 SAM 检测结果，SAM 独有框标记 source=sam。"""
    merged = [dict(d, source='yolo') for d in yolo_dets]
    for sam in sam_dets:
        sb = sam.get('bbox') or []
        if len(sb) < 4:
            continue
        overlapped = False
        for yd in merged:
            yb = yd.get('bbox') or []
            if len(yb) >= 4 and _bbox_iou(sb, yb) >= iou_thresh:
                overlapped = True
                if sam.get('mask'):
                    yd['mask'] = sam['mask']
                    yd['source'] = 'yolo+sam'
                break
        if not overlapped:
            merged.append(dict(sam, source='sam'))
    return merged


class SamClient:
    """HTTP 调用 AI model-server /model/sam/predict。"""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 30):
        self.base_url = (base_url or os.getenv('AI_SERVICE_URL', 'http://localhost:5000')).rstrip('/')
        self.timeout = timeout

    def _encode_frame(self, frame: np.ndarray) -> str:
        ok, buf = cv2.imencode('.jpg', frame)
        if not ok:
            raise ValueError('帧编码失败')
        return 'data:image/jpeg;base64,' + base64.b64encode(buf.tobytes()).decode('utf-8')

    def predict(self, frame: np.ndarray, *, text: list = None, bboxes: list = None,
                return_masks: bool = True, conf: float = 0.45) -> dict:
        payload = {
            'image_base64': self._encode_frame(frame),
            'return_masks': return_masks,
            'conf': conf,
        }
        if text:
            payload['text'] = text
        if bboxes:
            payload['bboxes'] = bboxes
        resp = requests.post(
            f'{self.base_url}/model/sam/predict',
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        body = resp.json()
        if body.get('code') != 0:
            raise RuntimeError(body.get('msg', 'SAM 推理失败'))
        return body.get('data') or {}

    def predict_text(self, frame: np.ndarray, text_prompts: list, **kwargs) -> list:
        data = self.predict(frame, text=text_prompts, **kwargs)
        return _sam_data_to_detections(data)

    def predict_bboxes(self, frame: np.ndarray, bboxes: list, **kwargs) -> list:
        data = self.predict(frame, bboxes=bboxes, **kwargs)
        return _sam_data_to_detections(data)


def _sam_data_to_detections(data: dict) -> list:
    dets = []
    for pred in data.get('predictions') or []:
        dets.append({
            'class_name': pred.get('class_name', 'object'),
            'confidence': pred.get('confidence', 0),
            'bbox': pred.get('bbox', []),
            'source': 'sam',
        })
    masks = data.get('masks') or []
    for i, det in enumerate(dets):
        if i < len(masks) and masks[i].get('xy'):
            det['mask'] = masks[i]['xy']
    return dets


def _should_trigger_sam(config: dict, yolo_detections: list, frame_number: int) -> bool:
    trigger = config.get('trigger', 'on_interval')
    if trigger == 'always':
        return True
    if trigger == 'on_yolo_empty':
        return not yolo_detections
    if trigger == 'on_alert':
        return bool(yolo_detections)
    if trigger == 'on_interval':
        interval = max(1, int(config.get('interval_frames', 25)))
        return frame_number % interval == 0
    return False


def sam_supplement_frame(
    frame: np.ndarray,
    yolo_detections: list,
    config: dict,
    sam_client: SamClient,
    *,
    frame_number: int = 0,
) -> list:
    """对单帧 YOLO 结果做 SAM 补充，返回合并后的检测列表。"""
    mode = config.get('pipeline_mode', 'none')
    if not config.get('enabled') or mode == 'none':
        return yolo_detections

    if not _should_trigger_sam(config, yolo_detections, frame_number):
        return yolo_detections

    try:
        conf = float(config.get('conf', 0.45))
        return_masks = bool(config.get('return_masks', True))

        if mode == 'refine_mask' and yolo_detections:
            bboxes = [d['bbox'] for d in yolo_detections if d.get('bbox')]
            if not bboxes:
                return yolo_detections
            sam_result = sam_client.predict_bboxes(frame, bboxes, return_masks=return_masks, conf=conf)
            merged = [dict(d, source='yolo') for d in yolo_detections]
            for i, det in enumerate(merged):
                if i < len(sam_result) and sam_result[i].get('mask'):
                    det['mask'] = sam_result[i]['mask']
                    det['source'] = 'yolo+sam'
            return merged

        if mode == 'open_vocab':
            text_prompts = config.get('text_prompts') or []
            if not text_prompts:
                return yolo_detections
            sam_dets = sam_client.predict_text(frame, text_prompts, return_masks=return_masks, conf=conf)
            return merge_yolo_sam_detections(
                yolo_detections, sam_dets, config.get('merge_iou', 0.5)
            )

        if mode == 'alert_verify' and yolo_detections:
            text_prompts = config.get('text_prompts') or []
            if not text_prompts:
                return yolo_detections
            sam_dets = sam_client.predict_text(frame, text_prompts, return_masks=False, conf=conf)
            if not sam_dets:
                return []
            return merge_yolo_sam_detections(yolo_detections, sam_dets, config.get('merge_iou', 0.5))

    except Exception as e:
        logger.warning('SAM 补充识别失败: %s', e)
    return yolo_detections
