"""车牌识别两步流水线：定位(四角) -> 透视校正 -> 号码识别。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

import app.utils.nvidia_lib_path  # noqa: F401

import onnxruntime as ort

from app.utils.plate_recognition.double_plate_split_merge import get_split_merge

PLATE_COLORS = ["黑色", "蓝色", "绿色", "白色", "黄色"]
PLATE_CHARS = (
    "#京沪津渝冀晋蒙辽吉黑苏浙皖闽赣鲁豫鄂湘粤桂琼川贵云藏陕甘青宁新学警港澳挂使领民航危"
    "0123456789ABCDEFGHJKLMNPQRSTUVWXYZ险品"
)
PLATE_TYPE_NAMES = {0: "单层", 1: "双层"}
LANDMARK_COLORS = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
REC_MEAN, REC_STD = 0.588, 0.193


@dataclass
class PlateResult:
    plate_no: str
    plate_color: str
    detect_conf: float
    plate_type: int
    tilt_angle: float
    is_tilted: bool
    rect: list[int]
    landmarks: list[list[float]] = field(default_factory=list)


def order_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def calc_tilt_angle(landmarks: np.ndarray) -> float:
    ordered = order_points(landmarks.astype(np.float32))
    tl, tr = ordered[0], ordered[1]
    return float(np.degrees(np.arctan2(tr[1] - tl[1], tr[0] - tl[0])))


def four_point_transform(image: np.ndarray, pts: np.ndarray) -> np.ndarray:
    rect = order_points(pts.astype(np.float32))
    tl, tr, br, bl = rect
    width_a = np.linalg.norm(br - bl)
    width_b = np.linalg.norm(tr - tl)
    max_width = max(int(width_a), int(width_b))
    height_a = np.linalg.norm(tr - br)
    height_b = np.linalg.norm(tl - bl)
    max_height = max(int(height_a), int(height_b))
    dst = np.array(
        [[0, 0], [max_width - 1, 0], [max_width - 1, max_height - 1], [0, max_height - 1]],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, matrix, (max_width, max_height))


def letterbox(
    image: np.ndarray,
    new_shape: tuple[int, int] = (640, 640),
    color: tuple[int, int, int] = (114, 114, 114),
) -> tuple[np.ndarray, float, float, float]:
    h, w = image.shape[:2]
    ratio = min(new_shape[0] / h, new_shape[1] / w)
    new_unpad = (int(round(w * ratio)), int(round(h * ratio)))
    dw = (new_shape[1] - new_unpad[0]) / 2
    dh = (new_shape[0] - new_unpad[1]) / 2
    resized = cv2.resize(image, new_unpad, interpolation=cv2.INTER_LINEAR)
    top = int(round(dh - 0.1))
    bottom = int(round(dh + 0.1))
    left = int(round(dw - 0.1))
    right = int(round(dw + 0.1))
    padded = cv2.copyMakeBorder(
        resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color
    )
    return padded, ratio, left, top


def restore_point(x: float, y: float, ratio: float, left: float, top: float) -> tuple[float, float]:
    return (x - left) / ratio, (y - top) / ratio


def decode_plate(indexes: np.ndarray) -> str:
    chars: list[str] = []
    prev = 0
    for value in indexes:
        if value != 0 and value != prev:
            chars.append(PLATE_CHARS[int(value)])
        prev = value
    return "".join(chars)


def preprocess_rec(image: np.ndarray) -> np.ndarray:
    img = cv2.resize(image, (168, 48))
    img = img.astype(np.float32)
    img = (img / 255.0 - REC_MEAN) / REC_STD
    img = img.transpose(2, 0, 1)
    return np.expand_dims(img, axis=0)


class PlatePipeline:
    """两步识别：1) 车牌定位+四角  2) 透视校正+号码识别。"""

    def __init__(
        self,
        detect_model: str | Path,
        rec_model: str | Path,
        providers: list[str] | None = None,
        tilt_threshold: float = 3.0,
    ):
        if providers is None:
            available = ort.get_available_providers()
            providers = [p for p in ("CUDAExecutionProvider", "CPUExecutionProvider") if p in available]

        self.detect_sess = ort.InferenceSession(str(detect_model), providers=providers)
        self.rec_sess = ort.InferenceSession(str(rec_model), providers=providers)
        self.detect_input = self.detect_sess.get_inputs()[0].name
        self.rec_input = self.rec_sess.get_inputs()[0].name
        self.tilt_threshold = tilt_threshold

    def _detect(self, image: np.ndarray, conf: float) -> list[dict]:
        blob, ratio, left, top = letterbox(image)
        inp = blob[:, :, ::-1].transpose(2, 0, 1).astype(np.float32) / 255.0
        inp = np.expand_dims(inp, axis=0)
        rows = self.detect_sess.run(None, {self.detect_input: inp})[0][0]
        detections: list[dict] = []
        for row in rows:
            if float(row[4]) < conf:
                continue
            kpts = row[6:14].reshape(4, 2).astype(np.float32)
            for i in range(4):
                kpts[i, 0], kpts[i, 1] = restore_point(kpts[i, 0], kpts[i, 1], ratio, left, top)
            box = row[:4].astype(np.float32).copy()
            box[[0, 2]] = [(box[0] - left) / ratio, (box[2] - left) / ratio]
            box[[1, 3]] = [(box[1] - top) / ratio, (box[3] - top) / ratio]
            h, w = image.shape[:2]
            box = box.clip(min=0)
            box[[0, 2]] = box[[0, 2]].clip(0, w)
            box[[1, 3]] = box[[1, 3]].clip(0, h)
            detections.append(
                {
                    "conf": float(row[4]),
                    "plate_type": int(row[5]),
                    "box": box.astype(int).tolist(),
                    "landmarks": kpts.tolist(),
                }
            )
        detections.sort(key=lambda x: x["conf"], reverse=True)
        return detections

    def _recognize(self, roi: np.ndarray) -> tuple[str, str]:
        inp = preprocess_rec(roi)
        plate_logits, color_logits = self.rec_sess.run(None, {self.rec_input: inp})
        plate_idx = np.argmax(plate_logits, axis=-1)[0]
        color_idx = int(np.argmax(color_logits))
        return decode_plate(plate_idx), PLATE_COLORS[color_idx]

    def predict(self, image: np.ndarray, conf: float = 0.25) -> list[PlateResult]:
        results: list[PlateResult] = []
        for det in self._detect(image, conf):
            landmarks = np.array(det["landmarks"], dtype=np.float32)
            angle = calc_tilt_angle(landmarks)
            roi = four_point_transform(image, landmarks)
            if det["plate_type"] == 1:
                roi = get_split_merge(roi)
            plate_no, plate_color = self._recognize(roi)
            results.append(
                PlateResult(
                    plate_no=plate_no,
                    plate_color=plate_color,
                    detect_conf=det["conf"],
                    plate_type=det["plate_type"],
                    tilt_angle=angle,
                    is_tilted=abs(angle) >= self.tilt_threshold,
                    rect=det["box"],
                    landmarks=det["landmarks"],
                )
            )
        return results
