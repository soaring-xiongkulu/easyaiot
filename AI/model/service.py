import os
import subprocess
import requests
import time
import zipfile
from utils.database import get_db_connection
from utils.minio_client import get_minio_client
# 添加nacos相关导入
import json

# 模型服务配置
MODEL_STORAGE_PATH = os.environ.get('MODEL_STORAGE_PATH', '/tmp/models')
NACOS_SERVER_ADDR = os.environ.get('NACOS_SERVER_ADDR', 'iot.basiclab.top:8848')
SERVICE_NAMESPACE = os.environ.get('SERVICE_NAMESPACE', 'local')

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
    cur.execute("SELECT id, status FROM model_services WHERE model_id = %s;", (model_id,))
    existing_model = cur.fetchone()
    
    # 如果服务已存在且正在运行，则返回现有服务信息
    if existing_model:
        service_id, status = existing_model
        if status == 'running':
            cur.close()
            conn.close()
            # 重新注册到Nacos
            register_service_nacos(model_id, model_name, model_version)
            return {"message": "模型服务已在运行", "model_id": model_id}, 200
        elif status == 'stopped':
            # 重启服务
            cur.execute("SELECT port, model_path FROM model_services WHERE model_id = %s;", (model_id,))
            result = cur.fetchone()
            port, model_path = result
                
            # 启动模型服务
            service_process = start_model_service_process(model_id, model_path, port)
                
            # 更新数据库中的状态
            cur.execute("UPDATE model_services SET status = %s, pid = %s, updated_at = CURRENT_TIMESTAMP WHERE model_id = %s;",
                           ('running', service_process.pid, model_id))
            conn.commit()
            cur.close()
            conn.close()
                
            service_url = f"http://localhost:{port}"
            # 注册到Nacos
            register_service_nacos(model_id, model_name, model_version)
                
            return {
                "id": service_id,
                "model_id": model_id,
                "service_url": service_url,
                "message": "模型服务重启成功"
            }, 200
        
        # 确保模型存储目录存在
        os.makedirs(MODEL_STORAGE_PATH, exist_ok=True)
        
        # 构建本地模型路径
        local_model_filename = f"{model_id}_{model_version}.zip"
        local_model_path = os.path.join(MODEL_STORAGE_PATH, local_model_filename)
        
        # 从Minio下载模型
        minio_client = get_minio_client()
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
        service_process = start_model_service_process(model_id, extract_path, port)
        
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
        
        # 注册到Nacos
        register_service_nacos(model_id, model_name, model_version)
        
        return {
            "id": service_id,
            "model_id": model_id,
            "service_url": service_url,
            "message": "模型部署成功"
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

# 新增：注册服务到Nacos
def register_service_nacos(model_id, model_name, model_version):
    try:
        import urllib.request
        import urllib.parse
        
        # 获取服务URL
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT service_url, port FROM model_services WHERE model_id = %s;", (model_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if not result:
            return False
            
        service_url = result[0]
        port = result[1]
        
        # 解析服务URL获取IP
        import re
        ip_match = re.search(r'http://([^:]+):(\d+)', service_url)
        if not ip_match:
            return False
            
        ip = ip_match.group(1)
        port = ip_match.group(2)
        
        # 准备注册数据
        data = {
            'serviceName': f'model-service-{model_id}',
            'ip': ip,
            'port': port,
            'metadata': json.dumps({
                'model_id': model_id,
                'model_name': model_name,
                'model_version': model_version
            })
        }
        
        # 发送注册请求到Nacos
        url = f'http://{NACOS_SERVER_ADDR}/nacos/v1/ns/instance'
        params = urllib.parse.urlencode(data)
        req = urllib.request.Request(url, data=params.encode('utf-8'), method='POST')
        with urllib.request.urlopen(req) as response:
            return response.status == 200
            
    except Exception as e:
        print(f"Nacos registration failed: {e}")
        return False

# 新增：启动模型服务进程
def start_model_service_process(model_id, model_path, port):
    service_process = subprocess.Popen([
        'python', '-c', f'''
            from flask import Flask, request, jsonify
            import sys
            import os
            sys.path.append('{model_path}')
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
            
            @app.route("/info", methods=["GET"])
            def info():
                return jsonify({{
                    "model_id": "{model_id}",
                    "service_status": "running"
                }})
            
            if __name__ == "__main__":
                app.run(host="0.0.0.0", port={port})
        '''])
    return service_process

# 新增：停止模型服务
def stop_model_service_service(model_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT pid, port FROM model_services WHERE model_id = %s;", (model_id,))
    result = cur.fetchone()
    
    if not result:
        cur.close()
        conn.close()
        return {"error": "Model service not found"}, 404
    
    pid, port = result
    
    try:
        # 终止进程
        import os
        import signal
        os.kill(pid, signal.SIGTERM)
    except Exception as e:
        print(f"Failed to stop process: {e}")
    
    # 更新数据库状态
    cur.execute("UPDATE model_services SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE model_id = %s;",
               ('stopped', model_id))
    conn.commit()
    cur.close()
    conn.close()
    
    # 从Nacos注销服务
    try:
        import urllib.request
        import urllib.parse
        
        data = {
            'serviceName': f'model-service-{model_id}',
            'ip': 'localhost',  # 简化处理，实际应获取具体IP
            'port': port
        }
        
        url = f'http://{NACOS_SERVER_ADDR}/nacos/v1/ns/instance?' + urllib.parse.urlencode(data)
        req = urllib.request.Request(url, method='DELETE')
        with urllib.request.urlopen(req) as response:
            pass  # 忽略返回结果
    except Exception as e:
        print(f"Nacos deregistration failed: {e}")
    
    return {"message": "Model service stopped successfully"}, 200

# 新增：获取模型服务详细信息
def get_model_service_detail_service(model_id):
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
        
        # 检查服务健康状态
        try:
            response = requests.get(f"{result[5]}/health", timeout=5)
            model_service['health_status'] = 'healthy' if response.status_code == 200 else 'unhealthy'
        except:
            model_service['health_status'] = 'unreachable'
            
        return model_service, 200
    else:
        return {"message": "Model service not found"}, 404
