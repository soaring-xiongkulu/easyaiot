#!/usr/bin/env python3
"""
YOLO模型版本检测脚本
使用ultralytics库判断YOLO模型是版本8还是版本11

@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import os
import sys
from typing import Optional, Tuple

try:
    from ultralytics import YOLO
except ImportError:
    print("错误: 未安装ultralytics库，请先安装: pip install ultralytics", file=sys.stderr)
    sys.exit(1)


def detect_yolo_version(model_path: str) -> Tuple[Optional[str], str]:
    """
    使用ultralytics库判断YOLO模型版本
    
    Args:
        model_path: 模型文件路径
        
    Returns:
        (版本字符串, 检测方法)
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"模型文件不存在: {model_path}")
    
    try:
        # 加载模型
        model = YOLO(model_path)
        
        # 方法1: 检查模型信息字符串
        model_info = str(model.info()).lower()
        if 'yolo11' in model_info or 'yolo 11' in model_info:
            return 'yolov11', "ultralytics库"
        elif 'yolo8' in model_info or 'yolo 8' in model_info or 'yolov8' in model_info:
            return 'yolov8', "ultralytics库"
        
        # 方法2: 检查模型类名
        model_type = str(type(model.model)).lower()
        if 'yolo11' in model_type:
            return 'yolov11', "ultralytics库"
        elif 'yolo8' in model_type or 'yolov8' in model_type:
            return 'yolov8', "ultralytics库"
        
        # 方法3: 检查模型架构名称
        if hasattr(model.model, 'yaml') and model.model.yaml:
            yaml_str = str(model.model.yaml).lower()
            if 'yolo11' in yaml_str:
                return 'yolov11', "ultralytics库"
            elif 'yolo8' in yaml_str or 'yolov8' in yaml_str:
                return 'yolov8', "ultralytics库"
        
        # 方法4: 检查模型文件路径（作为备用）
        model_path_lower = model_path.lower()
        if 'yolo11' in model_path_lower:
            return 'yolov11', "ultralytics库（文件名）"
        elif 'yolo8' in model_path_lower or 'yolov8' in model_path_lower:
            return 'yolov8', "ultralytics库（文件名）"
            
    except Exception as e:
        raise Exception(f"无法通过ultralytics库判断版本: {e}")
    
    return None, "未知"


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python check_yolo_version.py <模型文件路径>")
        print("示例: python check_yolo_version.py yolov8n.pt")
        print("示例: python check_yolo_version.py yolo11n.pt")
        sys.exit(1)
    
    model_path = sys.argv[1]
    
    try:
        version, method = detect_yolo_version(model_path)
        
        if version:
            print(f"模型版本: {version.upper()}")
            print(f"检测方法: {method}")
            
            # 返回退出码：0表示成功检测到版本
            if version == 'yolov8':
                sys.exit(0)
            elif version == 'yolov11':
                sys.exit(0)
            else:
                sys.exit(2)
        else:
            print("无法确定模型版本")
            print("提示: 请确保模型文件是有效的YOLO模型（.pt格式）")
            print("提示: 如果模型文件有效，可能是ultralytics库版本不兼容")
            sys.exit(1)
            
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

