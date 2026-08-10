"""
VIDEO 模块 ONNX 推理（支持按 GPU 设备 ID 选择 CUDA Execution Provider）

@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import ast
import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

import app.utils.nvidia_lib_path  # noqa: F401  补全 nvidia 库路径后再加载 ort

try:
    import onnxruntime as ort
except ImportError:
    ort = None
    logging.warning("onnxruntime未安装，ONNX推理功能将不可用")

confidence_thres = 0.35
iou_thres = 0.5
classes = {
    0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane', 5: 'bus', 6: 'train', 7: 'truck',
    8: 'boat', 9: 'traffic light', 10: 'fire hydrant', 11: 'stop sign', 12: 'parking meter', 13: 'bench',
    14: 'bird', 15: 'cat', 16: 'dog', 17: 'horse', 18: 'sheep', 19: 'cow', 20: 'elephant', 21: 'bear',
    22: 'zebra', 23: 'giraffe', 24: 'backpack', 25: 'umbrella', 26: 'handbag', 27: 'tie', 28: 'suitcase',
    29: 'frisbee', 30: 'skis', 31: 'snowboard', 32: 'sports ball', 33: 'kite', 34: 'baseball bat',
    35: 'baseball glove', 36: 'skateboard', 37: 'surfboard', 38: 'tennis racket', 39: 'bottle',
    40: 'wine glass', 41: 'cup', 42: 'fork', 43: 'knife', 44: 'spoon', 45: 'bowl', 46: 'banana', 47: 'apple',
    48: 'sandwich', 49: 'orange', 50: 'broccoli', 51: 'carrot', 52: 'hot dog', 53: 'pizza', 54: 'donut',
    55: 'cake', 56: 'chair', 57: 'couch', 58: 'potted plant', 59: 'bed', 60: 'dining table', 61: 'toilet',
    62: 'tv', 63: 'laptop', 64: 'mouse', 65: 'remote', 66: 'keyboard', 67: 'cell phone', 68: 'microwave',
    69: 'oven', 70: 'toaster', 71: 'sink', 72: 'refrigerator', 73: 'book', 74: 'clock', 75: 'vase',
    76: 'scissors', 77: 'teddy bear', 78: 'hair drier', 79: 'toothbrush',
}
color_palette = np.random.uniform(100, 255, size=(len(classes), 3))


def _cuda_provider_candidates(device_id: int) -> List[List]:
    """按优先级返回 CUDA provider 配置；简单配置优先，避免 EXHAUSTIVE 导致静默回退 CPU。"""
    device_id = int(device_id)
    return [
        ['CUDAExecutionProvider', 'CPUExecutionProvider'],
        [
            ('CUDAExecutionProvider', {'device_id': device_id}),
            'CPUExecutionProvider',
        ],
        [
            (
                'CUDAExecutionProvider',
                {
                    'device_id': device_id,
                    'arena_extend_strategy': 'kNextPowerOfTwo',
                    'cudnn_conv_algo_search': 'HEURISTIC',
                    'do_copy_in_default_stream': True,
                },
            ),
            'CPUExecutionProvider',
        ],
    ]


def _create_onnx_session(model_path: str, providers: List) -> Any:
    return ort.InferenceSession(model_path, providers=providers)


def calculate_iou(box, other_boxes):
    x1 = np.maximum(box[0], np.array(other_boxes)[:, 0])
    y1 = np.maximum(box[1], np.array(other_boxes)[:, 1])
    x2 = np.minimum(box[0] + box[2], np.array(other_boxes)[:, 0] + np.array(other_boxes)[:, 2])
    y2 = np.minimum(box[1] + box[3], np.array(other_boxes)[:, 1] + np.array(other_boxes)[:, 3])
    intersection_area = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)
    box_area = box[2] * box[3]
    other_boxes_area = np.array(other_boxes)[:, 2] * np.array(other_boxes)[:, 3]
    return intersection_area / (box_area + other_boxes_area - intersection_area)


def custom_NMSBoxes(boxes, scores, confidence_threshold, iou_threshold):
    if len(boxes) == 0:
        return []
    scores = np.array(scores)
    boxes = np.array(boxes)
    mask = scores > confidence_threshold
    filtered_boxes = boxes[mask]
    filtered_scores = scores[mask]
    if len(filtered_boxes) == 0:
        return []
    sorted_indices = np.argsort(filtered_scores)[::-1]
    indices = []
    while len(sorted_indices) > 0:
        current_index = sorted_indices[0]
        indices.append(current_index)
        if len(sorted_indices) == 1:
            break
        current_box = filtered_boxes[current_index]
        other_boxes = filtered_boxes[sorted_indices[1:]]
        iou = calculate_iou(current_box, other_boxes)
        non_overlapping_indices = np.where(iou <= iou_threshold)[0]
        sorted_indices = sorted_indices[non_overlapping_indices + 1]
    return indices


def preprocess(img, input_width, input_height):
    img_height, img_width = img.shape[:2]
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (input_width, input_height))
    image_data = np.array(img) / 255.0
    image_data = np.transpose(image_data, (2, 0, 1))
    image_data = np.expand_dims(image_data, axis=0).astype(np.float32)
    return image_data, img_height, img_width


def _is_end2end_yolo_output(output) -> bool:
    """YOLO26 等 end2end 模型 ONNX 输出为 (1, N, 6): [x1,y1,x2,y2,conf,class_id]。"""
    arr = np.squeeze(output[0])
    return arr.ndim >= 2 and int(arr.shape[-1]) == 6


def postprocess_end2end(
    input_image,
    output,
    input_width,
    input_height,
    img_width,
    img_height,
    conf_threshold: float = None,
    classes_dict: Dict[int, str] = None,
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """YOLO26 end2end ONNX 后处理（内置 NMS，无需再执行 custom_NMSBoxes）。"""
    conf_thresh = conf_threshold if conf_threshold is not None else confidence_thres
    if classes_dict is None:
        classes_dict = classes

    arr = np.squeeze(output[0])
    if arr.ndim == 3:
        arr = arr[0]

    x_factor = img_width / input_width
    y_factor = img_height / input_height
    detections = []
    for row in arr:
        x1, y1, x2, y2, score, cls_id = row[:6]
        score = float(score)
        if score < conf_thresh:
            continue
        class_id = int(cls_id)
        class_name = classes_dict.get(class_id, f'class_{class_id}')
        detections.append({
            'class': class_id,
            'class_name': class_name,
            'confidence': score,
            'bbox': [
                int(float(x1) * x_factor),
                int(float(y1) * y_factor),
                int(float(x2) * x_factor),
                int(float(y2) * y_factor),
            ],
        })
    return input_image, detections


def postprocess(
    input_image,
    output,
    input_width,
    input_height,
    img_width,
    img_height,
    conf_threshold: float = None,
    iou_threshold: float = None,
    draw: bool = False,
    classes_dict: Dict[int, str] = None,
    color_palette_array: np.ndarray = None,
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    conf_thresh = conf_threshold if conf_threshold is not None else confidence_thres
    iou_thresh = iou_threshold if iou_threshold is not None else iou_thres
    if classes_dict is None:
        classes_dict = classes
    if color_palette_array is None:
        color_palette_array = color_palette

    if _is_end2end_yolo_output(output):
        return postprocess_end2end(
            input_image,
            output,
            input_width,
            input_height,
            img_width,
            img_height,
            conf_threshold=conf_thresh,
            classes_dict=classes_dict,
        )

    outputs = np.transpose(np.squeeze(output[0]))
    rows = outputs.shape[0]
    boxes, scores, class_ids = [], [], []
    x_factor = img_width / input_width
    y_factor = img_height / input_height
    for i in range(rows):
        classes_scores = outputs[i][4:]
        max_score = np.amax(classes_scores)
        if max_score >= conf_thresh:
            class_id = np.argmax(classes_scores)
            x, y, w, h = outputs[i][0], outputs[i][1], outputs[i][2], outputs[i][3]
            left = int((x - w / 2) * x_factor)
            top = int((y - h / 2) * y_factor)
            width = int(w * x_factor)
            height = int(h * y_factor)
            class_ids.append(class_id)
            scores.append(max_score)
            boxes.append([left, top, width, height])

    indices = custom_NMSBoxes(boxes, scores, conf_thresh, iou_thresh)
    detections = []
    for i in indices:
        box = boxes[i]
        score = scores[i]
        class_id = class_ids[i]
        class_name = classes_dict.get(class_id, f'class_{class_id}')
        detections.append({
            'class': int(class_id),
            'class_name': class_name,
            'confidence': float(score),
            'bbox': [box[0], box[1], box[0] + box[2], box[1] + box[3]],
        })
    return input_image, detections


def _parse_names_metadata(raw: str) -> Optional[Dict[int, str]]:
    """解析 Ultralytics ONNX 元数据 names（支持 JSON 与 Python dict 字面量）。"""
    if not raw or not str(raw).strip():
        return None
    text = str(raw).strip()
    for parser in (json.loads, ast.literal_eval):
        try:
            obj = parser(text)
            if isinstance(obj, dict) and obj:
                return {int(k): str(v) for k, v in obj.items()}
            if isinstance(obj, list) and obj:
                return {i: str(v) for i, v in enumerate(obj)}
        except Exception:
            continue
    return None


def _get_classes_from_pt_files(onnx_model_path: str) -> Optional[Dict[int, str]]:
    try:
        model_dir = os.path.dirname(onnx_model_path)
        model_basename = os.path.splitext(os.path.basename(onnx_model_path))[0]
        pt_file = os.path.join(model_dir, f"{model_basename}.pt")
        if os.path.exists(pt_file):
            from ultralytics import YOLO
            yolo_model = YOLO(pt_file)
            if hasattr(yolo_model, 'names') and yolo_model.names:
                return {int(k): str(v) for k, v in yolo_model.names.items()}
        if os.path.isdir(model_dir):
            for file in os.listdir(model_dir):
                if file.endswith('.pt'):
                    try:
                        from ultralytics import YOLO
                        pt_path = os.path.join(model_dir, file)
                        yolo_model = YOLO(pt_path)
                        if hasattr(yolo_model, 'names') and yolo_model.names:
                            return {int(k): str(v) for k, v in yolo_model.names.items()}
                    except Exception:
                        continue
    except Exception as e:
        logging.debug(f"无法从YOLO模型文件获取类别信息: {str(e)}")
    return None


def _infer_yolo_num_classes(session: Any) -> Optional[int]:
    """从标准 YOLO ONNX 输出 shape [1, 4+N, anchors] 推断类别数。"""
    try:
        outputs = session.get_outputs()
        if not outputs:
            return None
        shape = outputs[0].shape
        if len(shape) < 2 or not isinstance(shape[1], int):
            return None
        channels = int(shape[1])
        if len(shape) == 3 and channels > 4 and channels <= 1000:
            return channels - 4
    except Exception:
        pass
    return None


def classes_dict_from_api_names(names: Optional[List[str]]) -> Optional[Dict[int, str]]:
    if not names:
        return None
    result = {i: str(name).strip() for i, name in enumerate(names) if str(name).strip()}
    return result or None


def get_classes_from_onnx_model(onnx_model_path: str) -> Optional[Dict[int, str]]:
    try:
        if ort is not None:
            session = ort.InferenceSession(onnx_model_path, providers=['CPUExecutionProvider'])
            metadata = session.get_modelmeta()
            if hasattr(metadata, 'custom_metadata_map') and metadata.custom_metadata_map:
                if 'names' in metadata.custom_metadata_map:
                    parsed = _parse_names_metadata(metadata.custom_metadata_map['names'])
                    if parsed:
                        logging.info('从ONNX模型元数据中获取到 %d 个类别', len(parsed))
                        return parsed
    except Exception as e:
        logging.debug(f"无法从ONNX模型元数据获取类别信息: {str(e)}")

    parsed = _get_classes_from_pt_files(onnx_model_path)
    if parsed:
        logging.info('从YOLO模型文件获取到 %d 个类别', len(parsed))
    return parsed


def resolve_onnx_classes_dict(
    onnx_model_path: str,
    session: Any,
    api_class_names: Optional[List[str]] = None,
) -> Dict[int, str]:
    """按优先级解析 ONNX 类别：元数据 > AI API > 同目录 .pt > 推断占位 / COCO。"""
    try:
        metadata = session.get_modelmeta()
        if hasattr(metadata, 'custom_metadata_map') and metadata.custom_metadata_map:
            if 'names' in metadata.custom_metadata_map:
                parsed = _parse_names_metadata(metadata.custom_metadata_map['names'])
                if parsed:
                    logging.info('从ONNX模型元数据中获取到 %d 个类别', len(parsed))
                    return parsed
    except Exception as e:
        logging.debug('读取ONNX元数据类别失败: %s', e)

    from_api = classes_dict_from_api_names(api_class_names)
    if from_api:
        logging.info('使用 AI 模块返回的类别信息（%d 个类别）', len(from_api))
        return from_api

    from_pt = _get_classes_from_pt_files(onnx_model_path)
    if from_pt:
        logging.info('从YOLO模型文件获取到 %d 个类别', len(from_pt))
        return from_pt

    num_classes = _infer_yolo_num_classes(session)
    if num_classes == len(classes):
        logging.info('使用默认 COCO 类别（%d 个类别）', len(classes))
        return classes
    if num_classes:
        logging.warning(
            '无法获取 ONNX 类别名，模型含 %d 类，使用 class_N 占位（避免误用 COCO 名称）',
            num_classes,
        )
        return {i: f'class_{i}' for i in range(num_classes)}

    logging.warning('无法获取 ONNX 类别名，回退默认 COCO 类别')
    return classes


class ONNXInference:
    """ONNX Runtime 推理，支持按 device_id 使用 CUDA。"""

    def __init__(
        self,
        onnx_model_path: str,
        conf_threshold: float = 0.35,
        iou_threshold: float = 0.5,
        classes_dict: Optional[Dict[int, str]] = None,
        api_class_names: Optional[List[str]] = None,
        device_id: Optional[int] = None,
    ):
        if ort is None:
            raise ImportError("onnxruntime未安装，请先安装: pip install onnxruntime-gpu 或 onnxruntime")

        self.onnx_model_path = onnx_model_path
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.device_id = device_id
        self.session, self.model_inputs, self.input_width, self.input_height = self._init_model()
        self.providers = self.session.get_providers()

        if classes_dict is None:
            self.classes_dict = resolve_onnx_classes_dict(
                onnx_model_path,
                self.session,
                api_class_names=api_class_names,
            )
        else:
            self.classes_dict = classes_dict

        max_class_id = max(self.classes_dict.keys()) if self.classes_dict else 79
        self.color_palette = np.random.uniform(100, 255, size=(max_class_id + 1, 3))

        if 'CUDAExecutionProvider' in self.providers:
            logging.info('ONNX模型使用 GPU 推理 (device_id=%s)', self.device_id)
        else:
            logging.info('ONNX模型使用 CPU 推理')

    @property
    def names(self) -> Dict[int, str]:
        return self.classes_dict

    def _should_use_gpu(self) -> bool:
        force_cpu = os.environ.get('ORT_EXECUTION_PROVIDERS', '').upper() == 'CPUEXECUTIONPROVIDER'
        if force_cpu:
            return False
        use_gpu = os.environ.get('USE_GPU', 'False').lower() == 'true'
        return use_gpu and self.device_id is not None

    def _init_model(self):
        available_providers = ort.get_available_providers()
        logging.info("ONNX Runtime可用执行提供者: %s", available_providers)

        session = None
        if not self._should_use_gpu() or 'CUDAExecutionProvider' not in available_providers:
            session = _create_onnx_session(self.onnx_model_path, ['CPUExecutionProvider'])
            logging.info("ONNX 使用 CPUExecutionProvider 初始化")
        else:
            last_error: Optional[Exception] = None
            for idx, cuda_providers in enumerate(_cuda_provider_candidates(self.device_id)):
                try:
                    candidate = _create_onnx_session(self.onnx_model_path, cuda_providers)
                    used = candidate.get_providers()
                    if 'CUDAExecutionProvider' in used:
                        session = candidate
                        logging.info(
                            "ONNX 使用 CUDAExecutionProvider 初始化 (device_id=%s, strategy=%s, providers=%s)",
                            self.device_id,
                            idx,
                            used,
                        )
                        break
                    last_error = RuntimeError(f'CUDAExecutionProvider 未生效, providers={used}')
                    logging.debug(
                        "ONNX CUDA 策略 %s 未生效，尝试下一套配置: %s",
                        idx,
                        used,
                    )
                except Exception as e:
                    last_error = e
                    logging.debug("ONNX CUDA 策略 %s 初始化异常: %s", idx, e)

            if session is None:
                logging.warning(
                    "CUDA 初始化失败，回退 CPU: %s",
                    last_error or '所有 CUDA 策略均未生效',
                )
                session = _create_onnx_session(self.onnx_model_path, ['CPUExecutionProvider'])

        model_inputs = session.get_inputs()
        input_shape = model_inputs[0].shape
        input_width = input_shape[2]
        input_height = input_shape[3]
        return session, model_inputs, input_width, input_height

    def detect(
        self,
        image,
        conf_threshold: float = None,
        iou_threshold: float = None,
        draw: bool = False,
    ) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        if isinstance(image, Image.Image):
            result_image = np.array(image)
        elif isinstance(image, str):
            result_image = cv2.imread(image)
            if result_image is None:
                raise ValueError(f"无法读取图像文件: {image}")
        else:
            result_image = image.copy()

        img_data, img_height, img_width = preprocess(result_image, self.input_width, self.input_height)
        outputs = self.session.run(None, {self.model_inputs[0].name: img_data})
        return postprocess(
            result_image,
            outputs,
            self.input_width,
            self.input_height,
            img_width,
            img_height,
            conf_threshold=conf_threshold or self.conf_threshold,
            iou_threshold=iou_threshold or self.iou_threshold,
            draw=draw,
            classes_dict=self.classes_dict,
            color_palette_array=self.color_palette,
        )
