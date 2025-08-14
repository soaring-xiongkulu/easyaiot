from flask import jsonify
from . import get_db_connection, minio_client

def index_service():
    return jsonify({"message": "AI Service is running", "service": "ai-service"})

def health_check_service():
    try:
        # 检查数据库连接
        conn = get_db_connection()
        conn.close()
        
        # 检查Minio连接
        minio_client.bucket_exists('healthcheck')
        
        return {"status": "UP"}, 200
    except Exception as e:
        return {"status": "DOWN", "error": str(e)}, 500