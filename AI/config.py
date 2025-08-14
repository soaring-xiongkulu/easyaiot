import os

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'iot.basiclab.top'),
    'database': os.getenv('DB_NAME', 'iot-ai10'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'basiclab@iot45722414822'),
    'port': os.getenv('DB_PORT', '5432')
}


class Config:
    # MinIO配置
    MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT', 'iot.basiclab.top:9000')
    MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY', 'minio_root')
    MINIO_SECRET_KEY = os.environ.get('MINIO_SECRET_KEY', 'minio_123456')
    MINIO_SECURE = os.environ.get('MINIO_SECURE', False)
    
    # 应用配置
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'data/uploads')
    MODEL_FOLDER = os.environ.get('MODEL_FOLDER', 'data/models')
    DATASET_FOLDER = os.environ.get('DATASET_FOLDER', 'data/datasets')
    
    # YOLOv8配置
    DEFAULT_EPOCHS = int(os.environ.get('DEFAULT_EPOCHS', 100))
    DEFAULT_IMG_SIZE = int(os.environ.get('DEFAULT_IMG_SIZE', 640))
    
    # 确保目录存在
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(MODEL_FOLDER, exist_ok=True)
    os.makedirs(DATASET_FOLDER, exist_ok=True)