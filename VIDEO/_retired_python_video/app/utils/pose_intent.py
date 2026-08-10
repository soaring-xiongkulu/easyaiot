"""
场景姿态意图分析：COCO-17 关键点特征提取与相似度匹配。
"""
from __future__ import annotations

import json
import logging
import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

KEYPOINT_COUNT = 17
# COCO-17: 0 nose, 5 L_shoulder, 6 R_shoulder, 7 L_elbow, 8 R_elbow,
# 9 L_wrist, 10 R_wrist, 11 L_hip, 12 R_hip, 13 L_knee, 14 R_knee, 15 L_ankle, 16 R_ankle
NOSE, L_SHOULDER, R_SHOULDER = 0, 5, 6
L_ELBOW, R_ELBOW = 7, 8
L_WRIST, R_WRIST = 9, 10
L_HIP, R_HIP = 11, 12
L_KNEE, R_KNEE = 13, 14
L_ANKLE, R_ANKLE = 15, 16

SCENE_TEMPLATES: Dict[str, Dict[str, Any]] = {
    'fall': {
        'name': '跌倒检测',
        'scene_category': 'fall',
        'intent_event': 'pose_fall_detected',
        'intent_object': '跌倒行为',
        'match_mode': 'combined',
        'similarity_threshold': 0.72,
        'extra_rules': {
            'torso_ground_angle_max': 40,
            'head_below_hip': True,
            'min_visible_keypoints': 8,
        },
    },
    'climb': {
        'name': '攀爬检测',
        'scene_category': 'climb',
        'intent_event': 'pose_climb_detected',
        'intent_object': '攀爬行为',
        'match_mode': 'combined',
        'similarity_threshold': 0.70,
        'extra_rules': {
            'wrists_above_shoulder': True,
            'torso_tilt_min': 35,
            'min_visible_keypoints': 8,
        },
    },
    'squat': {
        'name': '蹲伏检测',
        'scene_category': 'squat',
        'intent_event': 'pose_squat_detected',
        'intent_object': '蹲伏行为',
        'match_mode': 'angle',
        'similarity_threshold': 0.68,
        'extra_rules': {
            'knee_angle_max': 100,
            'min_visible_keypoints': 8,
        },
    },
    'hands_up': {
        'name': '举手求助',
        'scene_category': 'hands_up',
        'intent_event': 'pose_hands_up_detected',
        'intent_object': '举手求助',
        'match_mode': 'angle',
        'similarity_threshold': 0.65,
        'extra_rules': {
            'wrists_above_shoulder': True,
            'min_visible_keypoints': 6,
        },
    },
}


def _kp_xy(keypoints: List[List[float]], idx: int) -> Optional[Tuple[float, float, float]]:
    if idx >= len(keypoints):
        return None
    x, y, c = keypoints[idx]
    if c < 0.05:
        return None
    return float(x), float(y), float(c)


def visible_keypoint_count(keypoints: List[List[float]], min_conf: float = 0.25) -> int:
    return sum(1 for kp in keypoints if len(kp) >= 3 and float(kp[2]) >= min_conf)


def _angle_at(a: Tuple[float, float], b: Tuple[float, float], c: Tuple[float, float]) -> float:
    """点 b 处夹角（度）"""
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    dot = ba[0] * bc[0] + ba[1] * bc[1]
    norm_ba = math.hypot(ba[0], ba[1])
    norm_bc = math.hypot(bc[0], bc[1])
    if norm_ba < 1e-6 or norm_bc < 1e-6:
        return 0.0
    cos_val = max(-1.0, min(1.0, dot / (norm_ba * norm_bc)))
    return math.degrees(math.acos(cos_val))


def _torso_center(keypoints: List[List[float]]) -> Optional[Tuple[float, float]]:
    ls = _kp_xy(keypoints, L_SHOULDER)
    rs = _kp_xy(keypoints, R_SHOULDER)
    lh = _kp_xy(keypoints, L_HIP)
    rh = _kp_xy(keypoints, R_HIP)
    pts = [p[:2] for p in (ls, rs, lh, rh) if p]
    if len(pts) < 2:
        return None
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def _shoulder_width(keypoints: List[List[float]]) -> float:
    ls = _kp_xy(keypoints, L_SHOULDER)
    rs = _kp_xy(keypoints, R_SHOULDER)
    if ls and rs:
        return max(math.hypot(ls[0] - rs[0], ls[1] - rs[1]), 1.0)
    lh = _kp_xy(keypoints, L_HIP)
    rh = _kp_xy(keypoints, R_HIP)
    if lh and rh:
        return max(math.hypot(lh[0] - rh[0], lh[1] - rh[1]), 1.0)
    return 100.0


def extract_angle_features(
    keypoints: List[List[float]],
    min_conf: float = 0.25,
) -> Optional[List[float]]:
    """提取尺度/位置归一化的关节角度特征向量。"""
    if visible_keypoint_count(keypoints, min_conf) < 4:
        return None

    scale = _shoulder_width(keypoints)
    center = _torso_center(keypoints) or (0.0, 0.0)

    def pt(idx: int) -> Optional[Tuple[float, float]]:
        p = _kp_xy(keypoints, idx)
        if not p or p[2] < min_conf:
            return None
        return ((p[0] - center[0]) / scale, (p[1] - center[1]) / scale)

    features: List[float] = []

    def add_angle(i: int, j: int, k: int) -> None:
        a, b, c = pt(i), pt(j), pt(k)
        if a and b and c:
            features.append(_angle_at(a, b, c) / 180.0)
        else:
            features.append(-1.0)

    add_angle(L_SHOULDER, L_ELBOW, L_WRIST)
    add_angle(R_SHOULDER, R_ELBOW, R_WRIST)
    add_angle(L_HIP, L_KNEE, L_ANKLE)
    add_angle(R_HIP, R_KNEE, R_ANKLE)
    add_angle(L_SHOULDER, L_HIP, L_KNEE)
    add_angle(R_SHOULDER, R_HIP, R_KNEE)
    add_angle(L_SHOULDER, NOSE, R_SHOULDER)

    ls, rs, lh, rh = pt(L_SHOULDER), pt(R_SHOULDER), pt(L_HIP), pt(R_HIP)
    if ls and rs and lh and rh:
        mid_shoulder = ((ls[0] + rs[0]) / 2, (ls[1] + rs[1]) / 2)
        mid_hip = ((lh[0] + rh[0]) / 2, (lh[1] + rh[1]) / 2)
        dx = mid_shoulder[0] - mid_hip[0]
        dy = mid_shoulder[1] - mid_hip[1]
        torso_angle = math.degrees(math.atan2(abs(dx), abs(dy) + 1e-6))
        features.append(torso_angle / 90.0)
    else:
        features.append(-1.0)

    lw, rw = pt(L_WRIST), pt(R_WRIST)
    if lw and ls:
        features.append((ls[1] - lw[1]) / 2.0)
    else:
        features.append(-1.0)
    if rw and rs:
        features.append((rs[1] - rw[1]) / 2.0)
    else:
        features.append(-1.0)

    nose = pt(NOSE)
    if nose and lh and rh:
        mid_hip_y = (lh[1] + rh[1]) / 2
        features.append(1.0 if nose[1] > mid_hip_y else 0.0)
    else:
        features.append(-1.0)

    return features


def features_to_json(features: Optional[List[float]]) -> Optional[str]:
    if features is None:
        return None
    return json.dumps([round(x, 6) for x in features], ensure_ascii=False)


def features_from_json(raw) -> Optional[np.ndarray]:
    if raw is None:
        return None
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
        if isinstance(parsed, list) and parsed:
            return np.array(parsed, dtype=np.float64)
    except Exception:
        pass
    return None


def compute_pose_similarity(
    query_feat: Optional[List[float]],
    ref_feat: Optional[np.ndarray],
    mode: str = 'angle',
) -> float:
    if query_feat is None or ref_feat is None:
        return 0.0
    q = np.array(query_feat, dtype=np.float64)
    r = ref_feat
    if q.shape != r.shape:
        min_len = min(len(q), len(r))
        q = q[:min_len]
        r = r[:min_len]

    valid = (q >= 0) & (r >= 0)
    if not np.any(valid):
        return 0.0
    qv, rv = q[valid], r[valid]

    if mode == 'ratio':
        diff = np.abs(qv - rv)
        return float(max(0.0, 1.0 - np.mean(diff)))

    dot = float(np.dot(qv, rv))
    norm_q = float(np.linalg.norm(qv))
    norm_r = float(np.linalg.norm(rv))
    if norm_q < 1e-9 or norm_r < 1e-9:
        return 0.0
    cosine = dot / (norm_q * norm_r)
    angle_sim = max(0.0, min(1.0, (cosine + 1.0) / 2.0))

    if mode == 'combined':
        diff = np.abs(qv - rv)
        ratio_sim = max(0.0, 1.0 - np.mean(diff))
        return 0.7 * angle_sim + 0.3 * ratio_sim
    return angle_sim


def evaluate_extra_rules(keypoints: List[List[float]], rules: Optional[Dict[str, Any]]) -> bool:
    if not rules:
        return True

    min_kp = int(rules.get('min_visible_keypoints') or 0)
    if min_kp and visible_keypoint_count(keypoints) < min_kp:
        return False

    ls = _kp_xy(keypoints, L_SHOULDER)
    rs = _kp_xy(keypoints, R_SHOULDER)
    lh = _kp_xy(keypoints, L_HIP)
    rh = _kp_xy(keypoints, R_HIP)
    lw = _kp_xy(keypoints, L_WRIST)
    rw = _kp_xy(keypoints, R_WRIST)
    nose = _kp_xy(keypoints, NOSE)

    if rules.get('wrists_above_shoulder'):
        if not (ls and rs and lw and rw):
            return False
        if not (lw[1] < ls[1] and rw[1] < rs[1]):
            return False

    if rules.get('head_below_hip') and nose and lh and rh:
        mid_hip_y = (lh[1] + rh[1]) / 2
        if nose[1] <= mid_hip_y:
            return False

    max_torso = rules.get('torso_ground_angle_max')
    if max_torso is not None and ls and rs and lh and rh:
        mid_shoulder = ((ls[0] + rs[0]) / 2, (ls[1] + rs[1]) / 2)
        mid_hip = ((lh[0] + rh[0]) / 2, (lh[1] + rh[1]) / 2)
        dx = mid_shoulder[0] - mid_hip[0]
        dy = mid_shoulder[1] - mid_hip[1]
        angle = math.degrees(math.atan2(abs(dx), abs(dy) + 1e-6))
        if angle > float(max_torso):
            return False

    min_tilt = rules.get('torso_tilt_min')
    if min_tilt is not None and ls and rs and lh and rh:
        mid_shoulder = ((ls[0] + rs[0]) / 2, (ls[1] + rs[1]) / 2)
        mid_hip = ((lh[0] + rh[0]) / 2, (lh[1] + rh[1]) / 2)
        dx = mid_shoulder[0] - mid_hip[0]
        dy = mid_shoulder[1] - mid_hip[1]
        angle = math.degrees(math.atan2(abs(dx), abs(dy) + 1e-6))
        if angle < float(min_tilt):
            return False

    knee_max = rules.get('knee_angle_max')
    if knee_max is not None:
        lk = _angle_at(
            (lh[0], lh[1]) if lh else (0, 0),
            ( _kp_xy(keypoints, L_KNEE)[0], _kp_xy(keypoints, L_KNEE)[1]) if _kp_xy(keypoints, L_KNEE) else (0, 0),
            ( _kp_xy(keypoints, L_ANKLE)[0], _kp_xy(keypoints, L_ANKLE)[1]) if _kp_xy(keypoints, L_ANKLE) else (0, 0),
        ) if lh and _kp_xy(keypoints, L_KNEE) and _kp_xy(keypoints, L_ANKLE) else 180.0
        rk = _angle_at(
            (rh[0], rh[1]) if rh else (0, 0),
            ( _kp_xy(keypoints, R_KNEE)[0], _kp_xy(keypoints, R_KNEE)[1]) if _kp_xy(keypoints, R_KNEE) else (0, 0),
            ( _kp_xy(keypoints, R_ANKLE)[0], _kp_xy(keypoints, R_ANKLE)[1]) if _kp_xy(keypoints, R_ANKLE) else (0, 0),
        ) if rh and _kp_xy(keypoints, R_KNEE) and _kp_xy(keypoints, R_ANKLE) else 180.0
        if min(lk, rk) > float(knee_max):
            return False

    return True


def match_person_to_entry(
    keypoints: List[List[float]],
    entry_features: Optional[np.ndarray],
    *,
    match_mode: str = 'angle',
    extra_rules: Optional[Dict[str, Any]] = None,
    source_type: str = 'image',
) -> Tuple[float, bool]:
    """返回 (similarity, rules_passed)"""
    if source_type == 'rule' and extra_rules:
        passed = evaluate_extra_rules(keypoints, extra_rules)
        return (1.0 if passed else 0.0, passed)

    query_feat = extract_angle_features(keypoints)
    if query_feat is None:
        return 0.0, False

    sim = compute_pose_similarity(query_feat, entry_features, mode=match_mode)
    rules_ok = evaluate_extra_rules(keypoints, extra_rules)
    if extra_rules and not rules_ok:
        sim *= 0.5
    return sim, rules_ok


def _frame_vector_distance(a: List[float], b: List[float]) -> float:
    """两帧特征向量距离（0=相同，2=最大差异）。"""
    if not a or not b:
        return 2.0
    n = min(len(a), len(b))
    va = np.array(a[:n], dtype=np.float64)
    vb = np.array(b[:n], dtype=np.float64)
    valid = (va >= 0) & (vb >= 0)
    if not np.any(valid):
        return 2.0
    return float(np.mean(np.abs(va[valid] - vb[valid])))


def dtw_similarity(seq_a: List[List[float]], seq_b: List[List[float]]) -> float:
    """动态时间规整（DTW）相似度，返回 0~1。"""
    if not seq_a or not seq_b:
        return 0.0
    n, m = len(seq_a), len(seq_b)
    inf = float('inf')
    dtw = np.full((n + 1, m + 1), inf)
    dtw[0, 0] = 0.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = _frame_vector_distance(seq_a[i - 1], seq_b[j - 1])
            dtw[i, j] = cost + min(dtw[i - 1, j], dtw[i, j - 1], dtw[i - 1, j - 1])
    dist = float(dtw[n, m]) / max(n, m)
    return max(0.0, min(1.0, 1.0 - dist))


def match_sequence_to_entry(
    feature_sequence: List[List[float]],
    entry_rules: Optional[Dict[str, Any]],
    *,
    threshold: float = 0.65,
) -> Tuple[float, bool]:
    """将多帧特征序列与条目 reference 序列做 DTW 匹配。"""
    if not feature_sequence or not entry_rules:
        return 0.0, False
    ref = entry_rules.get('sequence_features') or entry_rules.get('reference_sequence')
    if not ref or not isinstance(ref, list):
        return 0.0, False
    sim = dtw_similarity(feature_sequence, ref)
    return sim, sim >= threshold
