from minio import Minio
from config import Config
from urllib.parse import urlparse

def create_minio_client():
    return Minio(
        Config.MINIO_ENDPOINT,
        access_key=Config.MINIO_ACCESS_KEY,
        secret_key=Config.MINIO_SECRET_KEY,
        secure=Config.MINIO_SECURE
    )

def download_from_minio(minio_url, local_path):
    """
    从MinIO下载文件
    minio_url 格式: http://minio-server:9000/bucket-name/object-name
    """
    # 解析URL
    parsed_url = urlparse(minio_url)
    
    # 从路径中提取bucket和object名称
    path_parts = parsed_url.path.lstrip('/').split('/', 1)
    if len(path_parts) != 2:
        raise ValueError("Invalid MinIO URL format")
    
    bucket_name = path_parts[0]
    object_name = path_parts[1]
    
    # 创建MinIO客户端
    client = create_minio_client()
    
    # 下载文件
    client.fget_object(bucket_name, object_name, local_path)
    
    return local_path