from ultralytics import YOLO
import os
import uuid
import json
import threading
from utils.minio_client import download_from_minio
from config import Config

class YOLOv8TrainingService:
    def __init__(self):
        self.tasks = {}
        
    def start_training(self, dataset_url, model_config):
        task_id = str(uuid.uuid4())
        
        # 在后台线程中启动训练
        thread = threading.Thread(
            target=self._train_model, 
            args=(task_id, dataset_url, model_config)
        )
        thread.start()
        
        self.tasks[task_id] = {
            "status": "started",
            "progress": 0,
            "model_path": None,
            "error": None
        }
        
        return task_id
    
    def _train_model(self, task_id, dataset_url, model_config):
        try:
            self.tasks[task_id]["status"] = "downloading_dataset"
            
            # 从MinIO下载数据集
            dataset_path = os.path.join(Config.DATASET_FOLDER, f"{task_id}_dataset.zip")
            download_from_minio(dataset_url, dataset_path)
            
            # 解压数据集
            import zipfile
            extract_path = os.path.join(Config.DATASET_FOLDER, task_id)
            with zipfile.ZipFile(dataset_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            # 删除压缩包
            os.remove(dataset_path)
            
            self.tasks[task_id]["status"] = "training"
            
            # 初始化模型
            model_type = model_config.get('model_type', 'yolov8s.pt')
            model = YOLO(model_type)
            
            # 训练参数
            epochs = model_config.get('epochs', Config.DEFAULT_EPOCHS)
            imgsz = model_config.get('imgsz', Config.DEFAULT_IMG_SIZE)
            batch_size = model_config.get('batch_size', 16)
            project = os.path.join(Config.MODEL_FOLDER, task_id)
            
            # 数据集配置文件路径
            data_yaml_path = os.path.join(extract_path, 'data.yaml')
            
            # 开始训练
            results = model.train(
                data=data_yaml_path,
                epochs=epochs,
                imgsz=imgsz,
                batch=batch_size,
                project=project,
                name='train',
                exist_ok=True
            )
            
            # 保存训练好的模型路径
            model_path = os.path.join(project, 'train', 'weights', 'best.pt')
            
            self.tasks[task_id].update({
                "status": "completed",
                "progress": 100,
                "model_path": model_path,
                "results": str(results) if results else None
            })
            
        except Exception as e:
            self.tasks[task_id].update({
                "status": "failed",
                "error": str(e)
            })
    
    def get_training_status(self, task_id):
        return self.tasks.get(task_id)