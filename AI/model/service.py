import os
import subprocess
import requests
import time
import zipfile
from ..system import get_db_connection, minio_client

# 模型服务配置
MODEL_STORAGE_PATH = os.environ.get('MODEL_STORAGE_PATH', '/tmp/models')

def get_model_service_service(model_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''SELECT id, model_id, model_name, model_version, model_path, 
                  service_url, status, port, pid, created_at, updated_at 
                  FROM model_services WHERE model_id = %s;''', (model_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    if result:
        model_service = {
            'id': result[0],
            'model_id': result[1],
            'model_name': result[2],
            'model_version': result[3],
            'model_path': result[4],
            'service_url': result[5],
            'status': result[6],
            'port': result[7],
            'pid': result[8],
            'created_at': result[9].isoformat() if result[9] else None,
            'updated_at': result[10].isoformat() if result[10] else None
        }
        return model_service, 200
    else:
        return {"message": "Model service not found"}, 404

def deploy_model_service(model_id, model_name, model_version, minio_model_path):
    # 检查模型服务是否已存在
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM model_services WHERE model_id = %s;", (model_id,))
    existing_model = cur.fetchone()
    
    if existing_model:
        cur.close()
        conn.close()
        return {"error": "Model service already exists"}, 400
    
    # 确保模型存储目录存在
    os.makedirs(MODEL_STORAGE_PATH, exist_ok=True)
    
    # 构建本地模型路径
    local_model_filename = f"{model_id}_{model_version}.zip"
    local_model_path = os.path.join(MODEL_STORAGE_PATH, local_model_filename)
    
    # 从Minio下载模型
    minio_client.fget_object(
        "ai-service-bucket",
        minio_model_path,
        local_model_path
    )
    
    # 解压模型文件（假设是zip格式）
    extract_path = os.path.join(MODEL_STORAGE_PATH, model_id)
    os.makedirs(extract_path, exist_ok=True)
    
    with zipfile.ZipFile(local_model_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
    
    # 为模型服务分配端口
    port = 9000 + int(time.time()) % 1000  # 简单的端口分配策略
    
    # 启动模型服务（这里只是一个示例，实际应根据模型类型启动相应的服务）
    # 例如：使用Flask或其他框架启动模型推理服务
    service_process = subprocess.Popen([
        'python', '-c', f'''
from flask import Flask, request, jsonify
import sys
app = Flask(__name__)

@app.route("/predict", methods=["POST"])
def predict():
    # 这里应该加载模型并执行推理
    data = request.get_json()
    # 模拟推理结果
    return jsonify({{"model_id": "{model_id}", "result": "prediction_result", "status": "success"}})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({{"status": "healthy"}})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port={port})
'''])
    
    # 保存模型服务信息到数据库
    service_url = f"http://localhost:{port}"
    cur.execute('''INSERT INTO model_services 
                  (model_id, model_name, model_version, model_path, service_url, status, port, pid) 
                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;''',
               (model_id, model_name, model_version, extract_path, service_url, 'running', port, service_process.pid))
    service_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    return {
        "id": service_id,
        "model_id": model_id,
        "service_url": service_url,
        "message": "Model deployed successfully"
    }, 201

def check_model_service_status_service(model_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT service_url, status FROM model_services WHERE model_id = %s;", (model_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    if not result:
        return {"error": "Model service not found"}, 404
    
    service_url, current_status = result
    
    # 检查服务是否可用
    try:
        response = requests.get(f"{service_url}/health", timeout=5)
        if response.status_code == 200:
            status = "running"
        else:
            status = "error"
    except:
        status = "stopped"
    
    # 更新数据库中的状态（如果发生变化）
    if status != current_status:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE model_services SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE model_id = %s;",
                   (status, model_id))
        conn.commit()
        cur.close()
        conn.close()
    
    return {"model_id": model_id, "status": status}, 200

def list_model_services_service():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''SELECT model_id, model_name, model_version, service_url, status, port, created_at 
                  FROM model_services ORDER BY created_at DESC;''')
    results = cur.fetchall()
    cur.close()
    conn.close()
    
    services = []
    for result in results:
        services.append({
            'model_id': result[0],
            'model_name': result[1],
            'model_version': result[2],
            'service_url': result[3],
            'status': result[4],
            'port': result[5],
            'created_at': result[6].isoformat() if result[6] else None
        })
    
    return services, 200