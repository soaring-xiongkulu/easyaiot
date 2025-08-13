import os

class Config:
    # MinIO配置
    MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT', 'localhost:9000')
    MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY', 'minioadmin')
    MINIO_SECRET_KEY = os.environ.get('MINIO_SECRET_KEY', 'minioadmin')
    MINIO_SECURE = os.environ.get('MINIO_SECURE', False)
    
    # 应用配置
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    MODEL_FOLDER = os.environ.get('MODEL_FOLDER', 'models')
    DATASET_FOLDER = os.environ.get('DATASET_FOLDER', 'datasets')
    
    # YOLOv8配置
    DEFAULT_EPOCHS = int(os.environ.get('DEFAULT_EPOCHS', 100))
    DEFAULT_IMG_SIZE = int(os.environ.get('DEFAULT_IMG_SIZE', 640))
    
    # 确保目录存在
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(MODEL_FOLDER, exist_ok=True)
    os.makedirs(DATASET_FOLDER, exist_ok=True)