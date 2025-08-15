import os
import subprocess
import requests
import time
import zipfile
from utils.database import get_db_connection
from utils.minio_client import get_minio_client
# 添加nacos相关导入
import json
# 添加推理所需导入
import sys
import importlib.util
# 添加文件操作相关导入
import shutil
import uuid
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 模型服务配置
MODEL_STORAGE_PATH = os.environ.get('MODEL_STORAGE_PATH', '/tmp/models')
NACOS_SERVER_ADDR = os.environ.get('NACOS_SERVER_ADDR', 'iot.basiclab.top:8848')
SERVICE_NAMESPACE = os.environ.get('SERVICE_NAMESPACE', 'public')  # 修改默认命名空间为public

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

def deploy_model_service(model_id, model_name, model_version, minio_model_path=None, local_model_path=None):
    # 检查是否以root权限运行
    if os.geteuid() != 0:
        logger.warning("警告: 当前未以root用户运行，可能会导致模型服务启动失败")
    
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
            if result:
                port, model_path = result
                
                # 启动模型服务
                try:
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
                except Exception as e:
                    cur.close()
                    conn.close()
                    return {"error": f"模型服务启动失败: {str(e)}"}, 500
    
    # 如果没有提供模型路径，尝试从existing_models表中查找
    if not minio_model_path and not local_model_path:
        cur.execute("SELECT model_path FROM existing_models WHERE model_id = %s;", (model_id,))
        result = cur.fetchone()
        if result:
            minio_model_path = result[0]
        else:
            cur.close()
            conn.close()
            return {"error": "必须提供模型文件路径"}, 400
    
    # 确保模型存储目录存在
    os.makedirs(MODEL_STORAGE_PATH, exist_ok=True)
    
    # 处理模型文件 - 支持从MinIO下载或使用本地上传的模型
    extract_path = os.path.join(MODEL_STORAGE_PATH, model_id)
    os.makedirs(extract_path, exist_ok=True)
    
    if minio_model_path:
        # 从Minio下载模型
        local_model_filename = f"{model_id}_{model_version}.zip"
        local_model_path = os.path.join(MODEL_STORAGE_PATH, local_model_filename)
        
        minio_client = get_minio_client()
        minio_client.fget_object(
            "ai-service-bucket",
            minio_model_path,
            local_model_path
        )
        
        # 解压模型文件（假设是zip格式）
        with zipfile.ZipFile(local_model_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
    elif local_model_path:
        # 使用本地上传的模型文件
        if os.path.isfile(local_model_path):
            # 如果是zip文件，解压到目标目录
            if local_model_path.endswith('.zip'):
                with zipfile.ZipFile(local_model_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
            else:
                # 如果是单个文件，直接复制到目标目录
                filename = os.path.basename(local_model_path)
                shutil.copy2(local_model_path, os.path.join(extract_path, filename))
        else:
            cur.close()
            conn.close()
            return {"error": "本地模型文件不存在"}, 400
    else:
        # 既没有指定MinIO路径也没有指定本地路径
        cur.close()
        conn.close()
        return {"error": "必须提供模型文件路径"}, 400
    
    # 为模型服务分配端口
    port = 9000 + int(time.time()) % 1000  # 简单的端口分配策略
    
    # 启动模型服务（这里只是一个示例，实际应根据模型类型启动相应的服务）
    # 例如：使用Flask或其他框架启动模型推理服务
    try:
        service_process = start_model_service_process(model_id, extract_path, port)
    except Exception as e:
        return {"error": f"模型服务进程启动失败: {str(e)}"}, 500
    
    # 等待服务启动
    service_url = f"http://localhost:{port}"
    max_wait_time = 30  # 最大等待时间30秒
    start_time = time.time()
    service_ready = False
    
    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(f"{service_url}/health", timeout=1)
            if response.status_code == 200:
                service_ready = True
                break
        except requests.exceptions.RequestException:
            time.sleep(1)
    
    if not service_ready:
        # 终止已启动的进程
        try:
            import signal
            service_process.terminate()
            service_process.wait(timeout=5)
        except:
            try:
                service_process.kill()
            except:
                pass
        return {"error": "模型服务在超时时间内未能成功启动"}, 500
    
    # 保存模型服务信息到数据库
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
        
        # Nacos配置
        NACOS_SERVER_ADDR = os.environ.get('NACOS_SERVER_ADDR', 'iot.basiclab.top:8848')
        SERVICE_NAMESPACE = os.environ.get('SERVICE_NAMESPACE', 'public')  # 默认使用public命名空间
        
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
        
        # 如果命名空间不是public，则添加namespaceId参数
        if SERVICE_NAMESPACE and SERVICE_NAMESPACE != 'public':
            data['namespaceId'] = SERVICE_NAMESPACE
        
        # 发送注册请求到Nacos
        url = f'http://{NACOS_SERVER_ADDR}/nacos/v1/ns/instance'
        params = urllib.parse.urlencode(data)
        req = urllib.request.Request(url, data=params.encode('utf-8'), method='POST')
        with urllib.request.urlopen(req) as response:
            return response.status == 200
            
    except Exception as e:
        print(f"Nacos registration failed: {e}")
        return False

# 修改：启动模型服务进程
def start_model_service_process(model_id, model_path, port):
    # 使用独立的启动脚本启动模型服务进程
    script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'model_launcher.py')
    
    # 确保脚本存在
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Model launcher script not found at {script_path}")
    
    # 检查是否以root权限运行，如果不是则给出警告
    if os.geteuid() != 0:
        logger.warning("警告: 当前未以root用户运行，可能会导致模型服务启动失败")
        logger.info(f"建议使用以下命令以root权限运行: sudo python {script_path} {model_id} {model_path} {port}")
    
    # 确保脚本有执行权限
    if not os.access(script_path, os.X_OK):
        try:
            os.chmod(script_path, 0o755)  # 添加执行权限
            logger.info(f"已为脚本添加执行权限: {script_path}")
        except Exception as e:
            logger.warning(f"无法为脚本添加执行权限: {e}")
    
    # 启动模型服务进程，传递参数
    try:
        logger.info(f"使用Python解释器启动模型服务: {sys.executable}")
        service_process = subprocess.Popen([
            sys.executable, script_path, model_id, model_path, str(port)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待一小段时间检查进程是否正常启动
        time.sleep(3)
        
        # 检查进程是否仍在运行
        if service_process.poll() is not None:
            # 进程已退出，获取错误信息
            stdout, stderr = service_process.communicate(timeout=5)
            error_msg = f"模型服务进程启动失败. stdout: {stdout.decode()}, stderr: {stderr.decode()}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        logger.info(f"模型服务进程已启动，PID: {service_process.pid}")
        return service_process
    except subprocess.TimeoutExpired:
        # 进程仍在运行，这是期望的行为
        logger.info(f"模型服务进程正在运行，PID: {service_process.pid}")
        return service_process
    except Exception as e:
        logger.error(f"启动模型服务进程时出错: {e}")
        raise Exception(f"启动模型服务进程失败: {str(e)}")

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

# 新增：模型推理服务
def predict_service(model_id, input_data):
    # 获取模型服务信息
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT model_path, status, service_url FROM model_services WHERE model_id = %s;", (model_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    if not result:
        return {"error": "Model service not found"}, 404
    
    model_path, status, service_url = result
    
    if status != 'running':
        return {"error": "Model service is not running"}, 400
    
    try:
        # 尝试调用远程服务的predict接口
        response = requests.post(f"{service_url}/predict", json=input_data, timeout=30)
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to call model service: {str(e)}"}, 500
    except Exception as e:
        return {"error": f"Prediction failed: {str(e)}"}, 500