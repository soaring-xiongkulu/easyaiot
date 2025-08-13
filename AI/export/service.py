from ultralytics import YOLO
import os
import uuid
from config import Config

class YOLOv8ExportService:
    def __init__(self):
        self.exported_models = {}
    
    def export_model(self, model_path, export_format):
        model_id = str(uuid.uuid4())
        
        # 加载模型
        model = YOLO(model_path)
        
        # 确定导出路径
        export_dir = os.path.join(Config.MODEL_FOLDER, 'exported')
        os.makedirs(export_dir, exist_ok=True)
        
        # 根据格式确定文件扩展名
        format_extensions = {
            'onnx': '.onnx',
            'torchscript': '.torchscript',
            'openvino': '_openvino_model',
            'engine': '.engine',
            'coreml': '.mlmodel',
            'saved_model': '_saved_model',
            'pb': '.pb',
            'tflite': '.tflite',
            'edgetpu': '_edgetpu.tflite',
            'tfjs': '_web_model',
            'paddle': '_paddle_model'
        }
        
        extension = format_extensions.get(export_format, '.onnx')
        export_path = os.path.join(export_dir, f"{model_id}{extension}")
        
        # 执行导出
        model.export(format=export_format, project=export_dir, name=model_id)
        
        # 记录导出的模型信息
        self.exported_models[model_id] = {
            "export_path": export_path,
            "format": export_format,
            "original_model_path": model_path
        }
        
        return {
            "model_id": model_id,
            "export_path": export_path
        }
    
    def get_exported_model(self, model_id):
        return self.exported_models.get(model_id)