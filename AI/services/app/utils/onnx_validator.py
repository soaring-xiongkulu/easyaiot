"""
ONNX模型验证工具
验证ONNX模型是否为有效的YOLO模型（yolov8或yolov11）

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
# 隐藏GPU设备，避免onnxruntime-gpu在导入时尝试加载CUDA库
if 'CUDA_VISIBLE_DEVICES' not in os.environ:
    os.environ['CUDA_VISIBLE_DEVICES'] = ''

from typing import Optional, Tuple

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

try:
    import onnxruntime as ort
    import onnx
except ImportError:
    ort = None
    onnx = None


def validate_onnx_model(model_path: str) -> Tuple[Optional[str], str]:
    """
    验证ONNX模型是否为有效的YOLO模型（yolov8或yolov11）
    
    Args:
        model_path: ONNX模型文件路径
        
    Returns:
        (版本字符串, 检测方法) - 如果版本为yolov8或yolov11，返回版本字符串；否则返回None
        
    Raises:
        FileNotFoundError: 模型文件不存在
        ImportError: 未安装必要的库
        Exception: 无法判断版本或其他错误
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"模型文件不存在: {model_path}")
    
    if YOLO is None:
        raise ImportError("未安装ultralytics库，请先安装: pip install ultralytics")
    
    # 方法1: 使用ultralytics库加载ONNX模型（推荐方法）
    try:
        # 明确指定task='detect'以避免警告
        model = YOLO(model_path, task='detect')
        
        # 尝试通过模型信息判断版本
        try:
            model_info = str(model.info()).lower()
            if 'yolo11' in model_info or 'yolo 11' in model_info:
                return 'yolov11', "ultralytics库（模型信息）"
            elif 'yolo8' in model_info or 'yolo 8' in model_info or 'yolov8' in model_info:
                return 'yolov8', "ultralytics库（模型信息）"
        except Exception:
            pass
        
        # 尝试通过模型类型判断
        try:
            model_type = str(type(model.model)).lower()
            if 'yolo11' in model_type:
                return 'yolov11', "ultralytics库（类型）"
            elif 'yolo8' in model_type or 'yolov8' in model_type:
                return 'yolov8', "ultralytics库（类型）"
        except Exception:
            pass
        
        # 如果能成功加载，默认认为是YOLOv8（因为YOLOv8更常见）
        # 如果用户需要YOLOv11，可以通过文件名或其他方式明确指定
        return 'yolov8', "ultralytics库（默认推断：模型成功加载）"
        
    except Exception as e:
        error_str = str(e).lower()
        
        # 检查是否是YOLOv5模型
        if 'yolov5' in error_str or 'yolo v5' in error_str or 'yolo5' in error_str:
            raise Exception(
                "检测到YOLOv5模型。该模型与YOLOv8/YOLOv11不兼容。\n"
                "请使用YOLOv8或YOLOv11模型，或使用最新版本的ultralytics包重新训练模型。"
            )
        
        # 如果ultralytics加载失败，尝试使用onnx库直接检查
        if onnx is not None:
            try:
                onnx_model = onnx.load(model_path)
                # 检查模型元数据
                model_metadata = str(onnx_model).lower()
                if 'yolo11' in model_metadata or 'yolo 11' in model_metadata:
                    return 'yolov11', "onnx库（元数据）"
                elif 'yolo8' in model_metadata or 'yolo 8' in model_metadata or 'yolov8' in model_metadata:
                    return 'yolov8', "onnx库（元数据）"
            except Exception:
                pass
        
        # 检查文件名
        model_path_lower = model_path.lower()
        if 'yolo11' in model_path_lower:
            return 'yolov11', "文件名"
        elif 'yolo8' in model_path_lower or 'yolov8' in model_path_lower:
            return 'yolov8', "文件名"
        
        # 如果所有方法都失败，抛出异常
        raise Exception(f"无法通过ultralytics库判断ONNX模型版本: {e}")

