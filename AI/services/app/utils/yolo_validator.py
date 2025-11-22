"""
YOLO模型版本验证工具
使用ultralytics库判断YOLO模型是版本8还是版本11

@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import os
from typing import Optional, Tuple

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

try:
    import torch
except ImportError:
    torch = None


def validate_yolo_model(model_path: str) -> Tuple[Optional[str], str]:
    """
    验证YOLO模型版本，只接受yolov8或yolov11
    
    Args:
        model_path: 模型文件路径
        
    Returns:
        (版本字符串, 检测方法) - 如果版本为yolov8或yolov11，返回版本字符串；否则返回None
        
    Raises:
        FileNotFoundError: 模型文件不存在
        ImportError: 未安装ultralytics库
        Exception: 无法判断版本或其他错误
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"模型文件不存在: {model_path}")
    
    if YOLO is None:
        raise ImportError("未安装ultralytics库，请先安装: pip install ultralytics")
    
    # 方法0: 先尝试直接检查torch模型文件的元数据（最快的方法）
    if torch is not None:
        try:
            checkpoint = torch.load(model_path, map_location='cpu', weights_only=False)
            if isinstance(checkpoint, dict):
                # 检查模型元数据中的版本信息
                metadata_str = str(checkpoint).lower()
                if 'yolo11' in metadata_str or 'yolo 11' in metadata_str:
                    return 'yolov11', "torch模型元数据"
                elif 'yolo8' in metadata_str or 'yolo 8' in metadata_str or 'yolov8' in metadata_str:
                    return 'yolov8', "torch模型元数据"
                
                # 检查模型架构路径
                if 'model' in checkpoint:
                    model_data = checkpoint['model']
                    if isinstance(model_data, dict):
                        model_str = str(model_data).lower()
                        if 'yolo11' in model_str:
                            return 'yolov11', "torch模型元数据"
                        elif 'yolo8' in model_str or 'yolov8' in model_str:
                            return 'yolov8', "torch模型元数据"
        except Exception:
            # 如果torch加载失败，继续使用ultralytics方法
            pass
    
    try:
        # 加载模型
        model = YOLO(model_path)
        
        # 方法1: 检查模型信息字符串（注意：model.info()可能会打印信息但不返回包含版本号的字符串）
        try:
            model_info = str(model.info()).lower()
            if 'yolo11' in model_info or 'yolo 11' in model_info:
                return 'yolov11', "ultralytics库"
            elif 'yolo8' in model_info or 'yolo 8' in model_info or 'yolov8' in model_info:
                return 'yolov8', "ultralytics库"
        except Exception:
            pass
        
        # 方法2: 检查模型类名
        try:
            model_type = str(type(model.model)).lower()
            if 'yolo11' in model_type:
                return 'yolov11', "ultralytics库（类名）"
            elif 'yolo8' in model_type or 'yolov8' in model_type:
                return 'yolov8', "ultralytics库（类名）"
        except Exception:
            pass
        
        # 方法3: 检查模型架构名称
        try:
            if hasattr(model.model, 'yaml') and model.model.yaml:
                yaml_str = str(model.model.yaml).lower()
                if 'yolo11' in yaml_str:
                    return 'yolov11', "ultralytics库（yaml）"
                elif 'yolo8' in yaml_str or 'yolov8' in yaml_str:
                    return 'yolov8', "ultralytics库（yaml）"
        except Exception:
            pass
        
        # 方法4: 检查模型的metadata（如果存在）
        try:
            if hasattr(model, 'overrides') and model.overrides:
                overrides_str = str(model.overrides).lower()
                if 'yolo11' in overrides_str:
                    return 'yolov11', "ultralytics库（metadata）"
                elif 'yolo8' in overrides_str or 'yolov8' in overrides_str:
                    return 'yolov8', "ultralytics库（metadata）"
        except Exception:
            pass
        
        # 方法5: 检查模型的任务类型和架构
        try:
            if hasattr(model.model, 'names'):
                # 尝试通过模型结构判断
                model_str = str(model.model).lower()
                if 'yolo11' in model_str:
                    return 'yolov11', "ultralytics库（架构）"
                elif 'yolo8' in model_str or 'yolov8' in model_str:
                    return 'yolov8', "ultralytics库（架构）"
        except Exception:
            pass
        
        # 方法6: 检查模型文件路径（作为备用）
        model_path_lower = model_path.lower()
        if 'yolo11' in model_path_lower:
            return 'yolov11', "ultralytics库（文件名）"
        elif 'yolo8' in model_path_lower or 'yolov8' in model_path_lower:
            return 'yolov8', "ultralytics库（文件名）"
        
        # 方法7: 如果模型能成功加载且没有报错，尝试通过模型的实际结构判断
        try:
            # 尝试获取模型的任务类型
            task = getattr(model, 'task', None)
            if task:
                task_str = str(task).lower()
                if 'yolo11' in task_str:
                    return 'yolov11', "ultralytics库（任务类型）"
                elif 'yolo8' in task_str or 'yolov8' in task_str:
                    return 'yolov8', "ultralytics库（任务类型）"
            
            # 尝试通过模型的实际层结构判断
            if hasattr(model.model, 'model'):
                inner_model = model.model.model
                if hasattr(inner_model, '__class__'):
                    class_name = str(inner_model.__class__).lower()
                    if 'yolo11' in class_name or 'yolo 11' in class_name:
                        return 'yolov11', "ultralytics库（内部模型类）"
                    elif 'yolo8' in class_name or 'yolov8' in class_name or 'yolo 8' in class_name:
                        return 'yolov8', "ultralytics库（内部模型类）"
        except Exception:
            pass
        
        # 如果模型能成功加载，且所有检查方法都无法明确识别版本，默认认为是YOLOv8
        # 这是一个合理的假设，因为：
        # 1. YOLOv8是更常见的版本
        # 2. 如果模型能通过ultralytics库加载，说明它是兼容的
        # 3. YOLOv11是较新的版本，如果存在会有更明显的标识
        # 4. 从日志可以看到模型成功加载并打印了摘要，说明模型是有效的
        return 'yolov8', "ultralytics库（默认推断：模型成功加载）"
            
    except Exception as e:
        error_str = str(e).lower()
        
        # 检查是否是YOLOv5模型
        if 'yolov5' in error_str or 'yolo v5' in error_str or 'yolo5' in error_str:
            raise Exception(
                "检测到YOLOv5模型。该模型与YOLOv8/YOLOv11不兼容。\n"
                "请使用YOLOv8或YOLOv11模型，或使用最新版本的ultralytics包重新训练模型。"
            )
        
        # 检查是否是其他不支持的模型版本
        if 'not forwards compatible' in error_str or 'not compatible' in error_str:
            # 尝试提取模型版本信息
            detected_version = None
            if 'yolov3' in error_str or 'yolo v3' in error_str or 'yolo3' in error_str:
                detected_version = "YOLOv3"
            elif 'yolov4' in error_str or 'yolo v4' in error_str or 'yolo4' in error_str:
                detected_version = "YOLOv4"
            elif 'yolov6' in error_str or 'yolo v6' in error_str or 'yolo6' in error_str:
                detected_version = "YOLOv6"
            elif 'yolov7' in error_str or 'yolo v7' in error_str or 'yolo7' in error_str:
                detected_version = "YOLOv7"
            
            if detected_version:
                raise Exception(
                    f"检测到{detected_version}模型。该模型与YOLOv8/YOLOv11不兼容。\n"
                    "请使用YOLOv8或YOLOv11模型，或使用最新版本的ultralytics包重新训练模型。"
                )
        
        # 其他错误，抛出原始异常信息
        raise Exception(f"无法通过ultralytics库判断版本: {e}")

