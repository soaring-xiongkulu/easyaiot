"""姿态意图告警图骨架叠层。"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def maybe_draw_skeleton_on_alert_image(task_config: Any, ctx: Dict[str, Any]) -> Optional[str]:
    """
    在告警图上叠加 COCO-17 骨架并保存副本，路径写入 ctx['skeleton_image_path']。
    """
    from app.services.pose_intent_matching_service import load_pose_intent_config

    cfg = load_pose_intent_config(task_config)
    if not cfg.get('draw_skeleton_on_alert'):
        return None

    image_path = (ctx.get('alert_image_path') or '').strip()
    pose_persons = ctx.get('pose_persons') or []
    if not image_path or not os.path.isfile(image_path) or not pose_persons:
        return None

    try:
        import cv2
        from app.utils.pose_analysis import draw_pose_skeleton

        frame = cv2.imread(image_path)
        if frame is None:
            return None

        highlight = None
        matches = ctx.get('pose_intent_matches') or []
        if matches:
            highlight = matches[0].get('person_index')

        for idx, person in enumerate(pose_persons):
            kps = person.get('keypoints') or []
            if not kps:
                continue
            frame = draw_pose_skeleton(frame, [{'keypoints': kps}])

        base, ext = os.path.splitext(image_path)
        out_path = f'{base}_pose_skeleton{ext or ".jpg"}'
        cv2.imwrite(out_path, frame)
        ctx['skeleton_image_path'] = out_path
        logger.debug('姿态骨架叠图已保存: %s', out_path)
        return out_path
    except Exception as exc:
        logger.warning('姿态骨架叠图失败: %s', exc)
        return None
