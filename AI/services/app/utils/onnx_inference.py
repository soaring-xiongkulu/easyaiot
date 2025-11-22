"""
ONNX推理模块
基于yolov8_detect_onnx.py的ONNX推理逻辑

@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import os
# 在导入onnxruntime之前设置环境变量，强制使用CPU执行提供者
# 这样可以避免CUDA库加载错误（如cublasLtCreate符号未找到）
# 注意：这些环境变量需要在导入onnxruntime之前设置
if 'ORT_EXECUTION_PROVIDERS' not in os.environ:
    os.environ['ORT_EXECUTION_PROVIDERS'] = 'CPUExecutionProvider'

# 临时隐藏GPU设备，避免onnxruntime-gpu在导入时尝试加载CUDA库
# 保存原始的CUDA_VISIBLE_DEVICES值，以便在导入后恢复（如果需要）
_original_cuda_visible_devices = os.environ.get('CUDA_VISIBLE_DEVICES')
if _original_cuda_visible_devices is None:
    # 如果未设置，临时设置为空，避免CUDA库加载错误
    os.environ['CUDA_VISIBLE_DEVICES'] = ''

import cv2
import numpy as np
import logging
from typing import Tuple, List, Dict, Any, Optional
from PIL import Image

try:
    import onnxruntime as ort
except ImportError:
    ort = None
    logging.warning("onnxruntime未安装，ONNX推理功能将不可用")

# 置信度阈值
confidence_thres = 0.35
# IOU阈值
iou_thres = 0.5
# 类别
classes = {0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane', 5: 'bus', 6: 'train', 7: 'truck',
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
           76: 'scissors', 77: 'teddy bear', 78: 'hair drier', 79: 'toothbrush'}
# 随机颜色
color_palette = np.random.uniform(100, 255, size=(len(classes), 3))


def calculate_iou(box, other_boxes):
    """
    计算给定边界框与一组其他边界框之间的交并比（IoU）。

    参数：
    - box: 单个边界框，格式为 [x1, y1, width, height]。
    - other_boxes: 其他边界框的数组，每个边界框的格式也为 [x1, y1, width, height]。

    返回值：
    - iou: 一个数组，包含给定边界框与每个其他边界框的IoU值。
    """
    # 计算交集的左上角坐标
    x1 = np.maximum(box[0], np.array(other_boxes)[:, 0])
    y1 = np.maximum(box[1], np.array(other_boxes)[:, 1])
    # 计算交集的右下角坐标
    x2 = np.minimum(box[0] + box[2], np.array(other_boxes)[:, 0] + np.array(other_boxes)[:, 2])
    y2 = np.minimum(box[1] + box[3], np.array(other_boxes)[:, 1] + np.array(other_boxes)[:, 3])
    # 计算交集区域的面积
    intersection_area = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)
    # 计算给定边界框的面积
    box_area = box[2] * box[3]
    # 计算其他边界框的面积
    other_boxes_area = np.array(other_boxes)[:, 2] * np.array(other_boxes)[:, 3]
    # 计算IoU值
    iou = intersection_area / (box_area + other_boxes_area - intersection_area)
    return iou


def custom_NMSBoxes(boxes, scores, confidence_threshold, iou_threshold):
    """自定义NMS实现"""
    # 如果没有边界框，则直接返回空列表
    if len(boxes) == 0:
        return []
    # 将得分和边界框转换为NumPy数组
    scores = np.array(scores)
    boxes = np.array(boxes)
    # 根据置信度阈值过滤边界框
    mask = scores > confidence_threshold
    filtered_boxes = boxes[mask]
    filtered_scores = scores[mask]
    # 如果过滤后没有边界框，则返回空列表
    if len(filtered_boxes) == 0:
        return []
    # 根据置信度得分对边界框进行排序
    sorted_indices = np.argsort(filtered_scores)[::-1]
    # 初始化一个空列表来存储选择的边界框索引
    indices = []
    # 当还有未处理的边界框时，循环继续
    while len(sorted_indices) > 0:
        # 选择得分最高的边界框索引
        current_index = sorted_indices[0]
        indices.append(current_index)
        # 如果只剩一个边界框，则结束循环
        if len(sorted_indices) == 1:
            break
        # 获取当前边界框和其他边界框
        current_box = filtered_boxes[current_index]
        other_boxes = filtered_boxes[sorted_indices[1:]]
        # 计算当前边界框与其他边界框的IoU
        iou = calculate_iou(current_box, other_boxes)
        # 找到IoU低于阈值的边界框，即与当前边界框不重叠的边界框
        non_overlapping_indices = np.where(iou <= iou_threshold)[0]
        # 更新sorted_indices以仅包含不重叠的边界框
        sorted_indices = sorted_indices[non_overlapping_indices + 1]
    # 返回选择的边界框索引
    return indices


def draw_detections(img, box, score, class_id, classes_dict: Dict[int, str], color_palette_array: np.ndarray):
    """
    在输入图像上绘制检测到的对象的边界框和标签。

    参数:
            img: 要在其上绘制检测结果的输入图像。
            box: 检测到的边界框。
            score: 对应的检测得分。
            class_id: 检测到的对象的类别ID。
            classes_dict: 类别ID到类别名称的字典。
            color_palette_array: 类别颜色调色板数组。

    返回:
            无
    """
    # 提取边界框的坐标
    x1, y1, w, h = box
    # 根据类别ID检索颜色（如果class_id超出范围，使用模运算）
    color_idx = class_id % len(color_palette_array)
    color = color_palette_array[color_idx]
    # 在图像上绘制边界框
    cv2.rectangle(img, (int(x1), int(y1)), (int(x1 + w), int(y1 + h)), color, 2)
    # 创建标签文本，包括类名和得分
    class_name = classes_dict.get(class_id, f'class_{class_id}')
    label = f'{class_name}: {score:.2f}'
    # 计算标签文本的尺寸
    (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    # 计算标签文本的位置
    label_x = x1
    label_y = y1 - 10 if y1 - 10 > label_height else y1 + 10
    # 绘制填充的矩形作为标签文本的背景
    cv2.rectangle(img, (label_x, label_y - label_height), (label_x + label_width, label_y + label_height), color, cv2.FILLED)
    # 在图像上绘制标签文本
    cv2.putText(img, label, (label_x, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)


def preprocess(img, input_width, input_height):
    """
    在执行推理之前预处理输入图像。

    返回:
        image_data: 为推理准备好的预处理后的图像数据。
        img_height: 原始图像高度
        img_width: 原始图像宽度
    """
    # 获取输入图像的高度和宽度
    img_height, img_width = img.shape[:2]
    # 将图像颜色空间从BGR转换为RGB
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # 将图像大小调整为匹配输入形状
    img = cv2.resize(img, (input_width, input_height))
    # 通过除以255.0来归一化图像数据
    image_data = np.array(img) / 255.0
    # 转置图像，使通道维度为第一维
    image_data = np.transpose(image_data, (2, 0, 1))  # 通道首
    # 扩展图像数据的维度以匹配预期的输入形状
    image_data = np.expand_dims(image_data, axis=0).astype(np.float32)
    # 返回预处理后的图像数据
    return image_data, img_height, img_width


def postprocess(input_image, output, input_width, input_height, img_width, img_height, 
                conf_threshold: float = None, iou_threshold: float = None, 
                draw: bool = True, classes_dict: Dict[int, str] = None,
                color_palette_array: np.ndarray = None) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    对模型输出进行后处理，提取边界框、得分和类别ID。

    参数:
        input_image (numpy.ndarray): 输入图像。
        output (numpy.ndarray): 模型的输出。
        input_width (int): 模型输入宽度。
        input_height (int): 模型输入高度。
        img_width (int): 原始图像宽度。
        img_height (int): 原始图像高度。
        conf_threshold (float): 置信度阈值，如果为None则使用默认值。
        iou_threshold (float): IOU阈值，如果为None则使用默认值。
        draw (bool): 是否在图像上绘制检测结果。
        classes_dict (Dict[int, str]): 类别ID到类别名称的字典，如果为None则使用默认COCO类别。
        color_palette_array (numpy.ndarray): 类别颜色调色板数组，如果为None则使用默认调色板。

    返回:
        numpy.ndarray: 绘制了检测结果的输入图像（如果draw=True）。
        List[Dict[str, Any]]: 检测结果列表，每个元素包含class_id, class_name, confidence, bbox
    """
    # 使用默认阈值或传入的阈值
    conf_thresh = conf_threshold if conf_threshold is not None else confidence_thres
    iou_thresh = iou_threshold if iou_threshold is not None else iou_thres
    
    # 使用传入的类别字典或默认类别
    if classes_dict is None:
        classes_dict = classes
    if color_palette_array is None:
        color_palette_array = color_palette

    # 转置和压缩输出以匹配预期的形状
    outputs = np.transpose(np.squeeze(output[0]))
    # 获取输出数组的行数
    rows = outputs.shape[0]
    # 用于存储检测的边界框、得分和类别ID的列表
    boxes = []
    scores = []
    class_ids = []
    # 计算边界框坐标的缩放因子
    x_factor = img_width / input_width
    y_factor = img_height / input_height
    # 遍历输出数组的每一行
    for i in range(rows):
        # 从当前行提取类别得分
        classes_scores = outputs[i][4:]
        # 找到类别得分中的最大得分
        max_score = np.amax(classes_scores)
        # 如果最大得分高于置信度阈值
        if max_score >= conf_thresh:
            # 获取得分最高的类别ID
            class_id = np.argmax(classes_scores)
            # 从当前行提取边界框坐标
            x, y, w, h = outputs[i][0], outputs[i][1], outputs[i][2], outputs[i][3]
            # 计算边界框的缩放坐标
            left = int((x - w / 2) * x_factor)
            top = int((y - h / 2) * y_factor)
            width = int(w * x_factor)
            height = int(h * y_factor)
            # 将类别ID、得分和框坐标添加到各自的列表中
            class_ids.append(class_id)
            scores.append(max_score)
            boxes.append([left, top, width, height])
    
    # 应用非最大抑制过滤重叠的边界框
    indices = custom_NMSBoxes(boxes, scores, conf_thresh, iou_thresh)
    
    # 构建检测结果列表
    detections = []
    # 遍历非最大抑制后的选定索引
    for i in indices:
        # 根据索引获取框、得分和类别ID
        box = boxes[i]
        score = scores[i]
        class_id = class_ids[i]
        
        # 获取类别名称
        class_name = classes_dict.get(class_id, f'class_{class_id}')
        
        # 添加到检测结果列表
        detections.append({
            'class': int(class_id),
            'class_name': class_name,
            'confidence': float(score),
            'bbox': [box[0], box[1], box[0] + box[2], box[1] + box[3]],  # [x1, y1, x2, y2]格式
        })
        
        # 如果draw=True，在输入图像上绘制检测结果
        if draw:
            draw_detections(input_image, box, score, class_id, classes_dict, color_palette_array)
    
    # 返回修改后的输入图像和检测结果
    return input_image, detections


def get_classes_from_onnx_model(onnx_model_path: str) -> Optional[Dict[int, str]]:
    """
    尝试从ONNX模型或对应的YOLO模型中获取类别信息
    
    Args:
        onnx_model_path: ONNX模型文件路径
        
    Returns:
        类别字典，如果无法获取则返回None
    """
    # 方法1: 尝试从ONNX模型的元数据中获取类别信息
    try:
        if ort is not None:
            session = ort.InferenceSession(onnx_model_path, providers=['CPUExecutionProvider'])
            metadata = session.get_modelmeta()
            # 检查元数据中是否有类别信息
            if hasattr(metadata, 'custom_metadata_map') and metadata.custom_metadata_map:
                # 尝试从元数据中获取类别
                if 'names' in metadata.custom_metadata_map:
                    import json
                    names_json = metadata.custom_metadata_map['names']
                    names_dict = json.loads(names_json)
                    # 将字符串键转换为整数键
                    classes_dict = {int(k): v for k, v in names_dict.items()}
                    logging.info(f"从ONNX模型元数据中获取到 {len(classes_dict)} 个类别")
                    return classes_dict
    except Exception as e:
        logging.debug(f"无法从ONNX模型元数据获取类别信息: {str(e)}")
    
    # 方法2: 尝试从对应的YOLO模型文件中获取类别信息
    try:
        # 查找同目录下的.pt文件（可能是对应的PyTorch模型）
        import os
        model_dir = os.path.dirname(onnx_model_path)
        model_basename = os.path.splitext(os.path.basename(onnx_model_path))[0]
        
        # 尝试查找同名的.pt文件
        pt_file = os.path.join(model_dir, f"{model_basename}.pt")
        if os.path.exists(pt_file):
            try:
                from ultralytics import YOLO
                yolo_model = YOLO(pt_file)
                if hasattr(yolo_model, 'names') and yolo_model.names:
                    # 将YOLO的names字典转换为我们的格式
                    classes_dict = {int(k): str(v) for k, v in yolo_model.names.items()}
                    logging.info(f"从对应的YOLO模型文件中获取到 {len(classes_dict)} 个类别")
                    return classes_dict
            except Exception as e:
                logging.debug(f"无法从YOLO模型文件获取类别信息: {str(e)}")
        
        # 尝试查找同目录下的其他.pt文件
        for file in os.listdir(model_dir):
            if file.endswith('.pt'):
                try:
                    from ultralytics import YOLO
                    pt_path = os.path.join(model_dir, file)
                    yolo_model = YOLO(pt_path)
                    if hasattr(yolo_model, 'names') and yolo_model.names:
                        classes_dict = {int(k): str(v) for k, v in yolo_model.names.items()}
                        logging.info(f"从同目录下的YOLO模型文件 {file} 中获取到 {len(classes_dict)} 个类别")
                        return classes_dict
                except Exception:
                    continue
    except Exception as e:
        logging.debug(f"无法从YOLO模型文件获取类别信息: {str(e)}")
    
    return None


class ONNXInference:
    """ONNX推理类"""
    
    def __init__(self, onnx_model_path: str, conf_threshold: float = 0.35, iou_threshold: float = 0.5,
                 classes_dict: Optional[Dict[int, str]] = None):
        """
        初始化ONNX推理模型
        
        Args:
            onnx_model_path: ONNX模型文件路径
            conf_threshold: 置信度阈值
            iou_threshold: IOU阈值
            classes_dict: 类别ID到类别名称的字典，如果为None则尝试从模型获取，否则使用默认COCO类别
        """
        if ort is None:
            raise ImportError("onnxruntime未安装，请先安装: pip install onnxruntime")
        
        self.onnx_model_path = onnx_model_path
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        
        # 初始化模型
        self.session, self.model_inputs, self.input_width, self.input_height = self._init_model()
        
        # 获取类别信息
        if classes_dict is None:
            # 尝试从模型获取类别信息
            self.classes_dict = get_classes_from_onnx_model(onnx_model_path)
            if self.classes_dict is None:
                # 如果无法获取，使用默认COCO类别
                self.classes_dict = classes
                logging.info(f"使用默认COCO类别（{len(self.classes_dict)}个类别）")
            else:
                logging.info(f"使用从模型获取的类别信息（{len(self.classes_dict)}个类别）")
        else:
            self.classes_dict = classes_dict
            logging.info(f"使用传入的类别信息（{len(self.classes_dict)}个类别）")
        
        # 根据类别数量生成颜色调色板
        max_class_id = max(self.classes_dict.keys()) if self.classes_dict else 79
        num_classes = max_class_id + 1
        self.color_palette = np.random.uniform(100, 255, size=(num_classes, 3))
        
        # 判断是否使用GPU推理
        if 'CUDAExecutionProvider' in self.session.get_providers():
            logging.info('ONNX模型正在使用GPU进行推理...')
        else:
            logging.info('ONNX模型使用CPU进行推理...')
    
    def _init_model(self):
        """初始化检测模型"""
        # 检查环境变量，如果强制使用CPU，则跳过CUDA尝试
        force_cpu = os.environ.get('ORT_EXECUTION_PROVIDERS', '').upper() == 'CPUEXECUTIONPROVIDER'
        
        session = None
        used_providers = []
        
        # 检查可用的执行提供者
        available_providers = ort.get_available_providers()
        logging.info(f"ONNX Runtime可用执行提供者: {available_providers}")
        
        # 如果环境变量强制使用CPU，或者CUDA不可用，直接使用CPU
        if force_cpu or 'CUDAExecutionProvider' not in available_providers:
            if force_cpu:
                logging.info("检测到环境变量强制使用CPU执行提供者，跳过CUDA尝试")
            else:
                logging.info("CUDA执行提供者不可用，使用CPU执行提供者")
            try:
                session = ort.InferenceSession(self.onnx_model_path, providers=['CPUExecutionProvider'])
                used_providers = session.get_providers()
                logging.info("已使用CPU执行提供者初始化模型")
            except Exception as cpu_error:
                logging.error(f"CPU执行提供者初始化失败: {str(cpu_error)}")
                raise
        else:
            # 尝试使用CUDA，如果失败则使用CPU
            try:
                logging.info("尝试使用CUDA执行提供者初始化模型...")
                cuda_providers = [
                    ('CUDAExecutionProvider', {
                        'device_id': 0,
                        'arena_extend_strategy': 'kNextPowerOfTwo',
                        'gpu_mem_limit': 2 * 1024 * 1024 * 1024,  # 2GB
                        'cudnn_conv_algo_search': 'EXHAUSTIVE',
                        'do_copy_in_default_stream': True,
                    }),
                    'CPUExecutionProvider',
                ]
                session = ort.InferenceSession(self.onnx_model_path, providers=cuda_providers)
                used_providers = session.get_providers()
                if 'CUDAExecutionProvider' in used_providers:
                    logging.info("成功使用CUDA执行提供者初始化模型")
                else:
                    logging.warning("CUDA执行提供者初始化失败，已回退到CPU")
            except Exception as e:
                logging.warning(f"CUDA执行提供者初始化失败: {str(e)}，回退到CPU")
                try:
                    session = ort.InferenceSession(self.onnx_model_path, providers=['CPUExecutionProvider'])
                    used_providers = session.get_providers()
                    logging.info("已使用CPU执行提供者初始化模型")
                except Exception as cpu_error:
                    logging.error(f"CPU执行提供者初始化也失败: {str(cpu_error)}")
                    raise
        
        # 获取模型的输入信息
        model_inputs = session.get_inputs()
        # 获取输入的形状，用于后续使用
        input_shape = model_inputs[0].shape
        # 从输入形状中提取输入宽度
        input_width = input_shape[2]
        # 从输入形状中提取输入高度
        input_height = input_shape[3]
        # 返回会话、模型输入信息、输入宽度和输入高度
        return session, model_inputs, input_width, input_height
    
    def detect(self, image, conf_threshold: float = None, iou_threshold: float = None, 
               draw: bool = True) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        执行目标检测
        
        Args:
            image: 输入图像（可以是文件路径、PIL Image或numpy数组）
            conf_threshold: 置信度阈值，如果为None则使用初始化时的值
            iou_threshold: IOU阈值，如果为None则使用初始化时的值
            draw: 是否在图像上绘制检测结果
        
        Returns:
            output_image: 处理后的图像（如果draw=True则包含检测框）
            detections: 检测结果列表
        """
        # 如果输入的图像是PIL图像对象，将其转换为NumPy数组
        if isinstance(image, Image.Image):
            result_image = np.array(image)
        elif isinstance(image, str):
            # 如果是文件路径，读取图像
            result_image = cv2.imread(image)
            if result_image is None:
                raise ValueError(f"无法读取图像文件: {image}")
        else:
            # 否则，直接使用输入的图像（假定已经是NumPy数组）
            result_image = image.copy()
        
        # 预处理图像数据，调整图像大小并可能进行归一化等操作
        img_data, img_height, img_width = preprocess(result_image, self.input_width, self.input_height)
        # 使用预处理后的图像数据进行推理
        outputs = self.session.run(None, {self.model_inputs[0].name: img_data})
        # 对推理结果进行后处理，例如解码检测框，过滤低置信度的检测等
        # 传递当前模型的类别信息和颜色调色板
        output_image, detections = postprocess(
            result_image, outputs, self.input_width, self.input_height, 
            img_width, img_height, 
            conf_threshold=conf_threshold or self.conf_threshold,
            iou_threshold=iou_threshold or self.iou_threshold,
            draw=draw,
            classes_dict=self.classes_dict,
            color_palette_array=self.color_palette
        )
        # 返回处理后的图像和检测结果
        return output_image, detections

