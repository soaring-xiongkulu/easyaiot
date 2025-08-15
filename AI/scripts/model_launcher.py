import importlib.util
import json
import logging
import os
import sys
import time
import urllib.parse

import requests
from flask import Flask, request, jsonify

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 检查是否以root权限运行，如果不是则发出警告
if os.geteuid() != 0:
    logger.warning("警告: 当前未以root用户运行，可能会导致模型服务启动失败")

# 获取传递的参数
model_id = sys.argv[1] if len(sys.argv) > 1 else "default_model"
model_path = sys.argv[2] if len(sys.argv) > 2 else "."
port = int(sys.argv[3]) if len(sys.argv) > 3 else 5000

app = Flask(__name__)

# 动态加载模型
model = None
predict_function = None

# 服务信息
service_info = {
    "model_id": model_id,
    "port": port,
    "status": "starting"
}


def find_available_port(start_port):
    """
    查找可用端口，避免端口冲突
    """
    import socket
    port = start_port
    logger.info(f"开始查找可用端口，起始端口: {start_port}")
    while port < 65535:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                result = sock.connect_ex(('localhost', port))
                if result != 0:  # 端口可用
                    logger.info(f"找到可用端口: {port}")
                    return port
                else:
                    logger.debug(f"端口 {port} 已被占用，继续查找...")
        except Exception as e:
            logger.error(f"检查端口 {port} 时发生错误: {e}", exc_info=True)
        port += 1
    raise Exception("无法找到可用端口")


def register_service_to_nacos():
    """
    注册服务到Nacos
    """
    try:
        # Nacos配置
        NACOS_SERVER_ADDR = os.environ.get('NACOS_SERVER_ADDR', 'iot.basiclab.top:8848')
        SERVICE_NAMESPACE = os.environ.get('SERVICE_NAMESPACE', 'public')  # 修改默认命名空间为public

        logger.info(f"Nacos配置: 服务器地址={NACOS_SERVER_ADDR}, 命名空间={SERVICE_NAMESPACE}")

        # 服务URL
        service_url = f"http://localhost:{service_info['port']}"
        logger.info(f"准备注册的服务URL: {service_url}")

        # 准备注册数据
        data = {
            'serviceName': f'model-service-{model_id}',
            'ip': 'localhost',
            'port': service_info['port'],
            'metadata': json.dumps({
                'model_id': model_id,
                'service_url': service_url,
                'timestamp': time.time()
            })
        }

        # 如果命名空间不是public，则添加namespaceId参数
        if SERVICE_NAMESPACE and SERVICE_NAMESPACE != 'public':
            data['namespaceId'] = SERVICE_NAMESPACE
            logger.info(f"使用命名空间ID: {SERVICE_NAMESPACE}")

        # 发送注册请求到Nacos
        url = f'http://{NACOS_SERVER_ADDR}/nacos/v1/ns/instance'
        params = urllib.parse.urlencode(data)
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        logger.info(f"正在注册服务到Nacos: {url}")
        logger.debug(f"注册参数: {params}")

        response = requests.post(url, data=params, headers=headers, timeout=10)

        logger.info(f"Nacos响应状态码: {response.status_code}")
        logger.debug(f"Nacos响应内容: {response.text}")

        if response.status_code == 200:
            logger.info(f"服务成功注册到Nacos，模型ID: {model_id}")
            return True
        else:
            logger.error(f"Nacos注册失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return False

    except Exception as e:
        logger.error(f"Nacos注册异常: {e}", exc_info=True)
        return False


def save_service_to_database():
    """
    保存服务信息到数据库
    """
    try:
        import psycopg2
        
        # 尝试从项目配置中导入数据库配置
        db_config = None
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.py')
        
        if os.path.exists(config_path):
            try:
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from config import DB_CONFIG
                db_config = DB_CONFIG
                logger.info("成功从config.py导入数据库配置")
            except Exception as e:
                logger.warning(f"从config.py导入数据库配置失败: {e}")
        
        # 如果无法从config.py导入，则使用环境变量或默认值
        if not db_config:
            db_config = {
                'host': os.getenv('DB_HOST', 'iot.basiclab.top'),
                'database': os.getenv('DB_NAME', 'iot-ai10'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', 'basiclab@iot45722414822'),
                'port': os.getenv('DB_PORT', '5432')
            }
            logger.info("使用环境变量或默认值作为数据库配置")

        logger.info("开始连接数据库...")

        # 数据库连接配置
        connection = psycopg2.connect(
            host=db_config['host'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password'],
            port=db_config['port']
        )

        logger.info("数据库连接成功")
        cursor = connection.cursor()

        # 服务URL
        service_url = f"http://localhost:{service_info['port']}"
        logger.info(f"服务URL: {service_url}")

        # 插入或更新模型服务信息
        insert_query = """
        INSERT INTO model_services 
        (model_id, model_name, model_version, model_path, service_url, status, port, pid) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (model_id) 
        DO UPDATE SET 
        service_url = EXCLUDED.service_url,
        status = EXCLUDED.status,
        port = EXCLUDED.port,
        pid = EXCLUDED.pid,
        updated_at = CURRENT_TIMESTAMP
        """

        # 获取模型信息
        model_name = f"模型-{model_id}"
        model_version = "1.0.0"

        logger.info(
            f"准备保存模型服务信息: model_id={model_id}, model_name={model_name}, model_version={model_version}")
        logger.debug(
            f"完整参数: {model_id}, {model_name}, {model_version}, {model_path}, {service_url}, running, {service_info['port']}, {os.getpid()}")

        cursor.execute(insert_query, (
            model_id,
            model_name,
            model_version,
            model_path,
            service_url,
            'running',
            service_info['port'],
            os.getpid()
        ))

        connection.commit()
        logger.info("数据库提交成功")
        cursor.close()
        connection.close()

        logger.info(f"服务信息已保存到数据库，模型ID: {model_id}")
        return True

    except Exception as e:
        logger.error(f"保存服务信息到数据库失败: {e}", exc_info=True)
        return False


def load_model():
    global model, predict_function
    try:
        logger.info(f"开始加载模型，路径: {model_path}")

        # 检查模型路径是否存在
        if not os.path.exists(model_path):
            logger.error(f"模型路径不存在: {model_path}")
            raise FileNotFoundError(f"模型路径不存在: {model_path}")

        # 尝试加载常见的模型文件
        model_files = ['model.py', 'predict.py', 'inference.py']
        for model_file in model_files:
            model_file_path = os.path.join(model_path, model_file)
            logger.debug(f"检查模型文件: {model_file_path}")
            if os.path.exists(model_file_path):
                logger.info(f"找到模型文件: {model_file_path}")
                try:
                    spec = importlib.util.spec_from_file_location("model_module", model_file_path)
                    model_module = importlib.util.module_from_spec(spec)
                    logger.info(f"正在加载模型模块: {model_file_path}")
                    spec.loader.exec_module(model_module)
                    if hasattr(model_module, 'predict'):
                        model = model_module
                        predict_function = getattr(model_module, 'predict')
                        logger.info(f"模型成功加载自 {model_file}")
                        return True
                    else:
                        logger.warning(f"模型文件 {model_file} 中未找到predict函数")
                except Exception as e:
                    logger.error(f"加载模型文件 {model_file} 时出错: {e}", exc_info=True)

        # 如果在常见文件中找不到，尝试直接加载.pt文件（YOLO模型）
        import glob
        pt_files = glob.glob(os.path.join(model_path, "*.pt"))
        logger.info(f"查找.pt文件: {pt_files}")
        if pt_files:
            logger.info(f"找到.pt文件: {pt_files}")
            from ultralytics import YOLO
            try:
                logger.info(f"正在加载YOLO模型: {pt_files[0]}")
                model = YOLO(pt_files[0])

                # 创建一个predict函数
                def yolo_predict(data):
                    try:
                        # 根据YOLO模型的要求处理输入数据
                        if isinstance(data, dict) and 'image' in data:
                            logger.debug("使用字典中的image键作为输入")
                            results = model(data['image'])
                        else:
                            logger.debug("直接使用输入数据")
                            results = model(data)
                        # 处理结果，确保返回可JSON序列化的数据
                        if hasattr(results, '__iter__'):
                            logger.debug("处理多个结果")
                            return [r.tojson() if hasattr(r, 'tojson') else str(r) for r in results]
                        else:
                            logger.debug("处理单个结果")
                            return results.tojson() if hasattr(results, 'tojson') else str(results)
                    except Exception as e:
                        logger.error(f"YOLO模型推理时出错: {e}", exc_info=True)
                        raise e

                predict_function = yolo_predict
                logger.info(f"YOLO模型成功加载自 {pt_files[0]}")
                return True
            except Exception as e:
                logger.error(f"加载YOLO模型失败: {e}", exc_info=True)

                # 创建一个模拟的预测函数用于测试
                def mock_predict(data):
                    logger.warning("使用模拟预测函数")
                    return {"mock_result": "This is a mock prediction result",
                            "model_file": pt_files[0] if pt_files else "no model file"}

                predict_function = mock_predict
                logger.info("已创建模拟预测函数")
                return True

        # 尝试加载ONNX模型
        onnx_files = glob.glob(os.path.join(model_path, "*.onnx"))
        logger.info(f"查找.onnx文件: {onnx_files}")
        if onnx_files:
            logger.info(f"找到.onnx文件: {onnx_files}")
            # 加载ONNX模型
            import onnxruntime as ort
            try:
                logger.info(f"正在加载ONNX模型: {onnx_files[0]}")
                model = ort.InferenceSession(onnx_files[0])

                # 创建一个predict函数
                def onnx_predict(data):
                    try:
                        # 处理ONNX模型推理
                        if isinstance(data, dict):
                            # 如果输入是字典格式，提取输入数据
                            inputs = {}
                            for i, input_info in enumerate(model.get_inputs()):
                                input_name = input_info.name
                                if input_name in data:
                                    inputs[input_name] = data[input_name]
                                elif f"input_{i}" in data:
                                    inputs[input_name] = data[f"input_{i}"]
                                else:
                                    # 如果没有匹配的输入名称，使用第一个输入
                                    inputs[input_name] = list(data.values())[0] if data else None
                                    break
                        else:
                            # 如果输入不是字典，假设是单个输入
                            input_name = model.get_inputs()[0].name
                            inputs = {input_name: data}

                        logger.debug(f"ONNX模型输入: {inputs}")
                        # 运行推理
                        results = model.run(None, inputs)
                        logger.debug(f"ONNX模型输出: {results}")

                        # 处理结果，确保返回可JSON序列化的数据
                        if len(results) == 1:
                            result = results[0]
                            # 如果结果是numpy数组，转换为列表
                            if hasattr(result, 'tolist'):
                                return result.tolist()
                            else:
                                return result
                        else:
                            processed_results = []
                            for r in results:
                                if hasattr(r, 'tolist'):
                                    processed_results.append(r.tolist())
                                else:
                                    processed_results.append(r)
                            return processed_results
                    except Exception as e:
                        logger.error(f"ONNX模型推理时出错: {e}", exc_info=True)
                        raise e

                predict_function = onnx_predict
                logger.info(f"ONNX模型成功加载自 {onnx_files[0]}")
                return True
            except Exception as e:
                logger.error(f"加载ONNX模型失败: {e}", exc_info=True)

        # 如果没有找到模型文件，创建一个默认的预测函数
        logger.warning("未找到合适的模型文件，创建默认预测函数")

        def default_predict(data):
            logger.info("使用默认预测函数")
            return {"result": "Default prediction result", "model_path": model_path}

        predict_function = default_predict
        return True
    except Exception as e:
        logger.error(f"模型加载错误: {e}", exc_info=True)

        # 即使模型加载失败，也创建一个默认的预测函数以确保服务可以启动
        def fallback_predict(data):
            logger.warning("模型加载失败，使用备用预测函数")
            return {"error": "模型加载失败", "fallback_result": "This is a fallback result"}

        predict_function = fallback_predict
        return True


# 加载模型
logger.info("开始加载模型...")
model_loaded = load_model()
# 不管模型是否加载成功，都确保服务可以启动
logger.info("模型加载完成，服务将正常启动")


@app.route("/predict", methods=["POST"])
def predict():
    global model, predict_function
    try:
        logger.info("收到预测请求")
        data = request.get_json()
        logger.debug(f"预测请求数据: {data}")
        if model and predict_function:
            # 调用实际的预测函数
            logger.info("调用预测函数")
            result = predict_function(data)
            logger.info(f"预测请求处理完成，模型ID: {model_id}")
            return jsonify({"model_id": model_id, "result": result, "status": "success"})
        else:
            logger.error("模型未找到或预测函数未实现")
            return jsonify({"model_id": model_id, "error": "模型未找到或预测函数未实现", "status": "error"}), 404
    except Exception as e:
        logger.error(f"预测错误: {e}", exc_info=True)
        return jsonify({"model_id": model_id, "error": str(e), "status": "error"}), 500


@app.route("/health", methods=["GET"])
def health():
    logger.debug("收到健康检查请求")
    return jsonify({"status": "healthy", "model_id": model_id})


@app.route("/info", methods=["GET"])
def info():
    logger.debug("收到信息服务请求")
    return jsonify({
        "model_id": model_id,
        "service_status": "running",
        "model_loaded": model is not None,
        "port": service_info['port']
    })


def init_service():
    """
    初始化服务：检查端口、注册Nacos、保存数据库
    """
    global port

    logger.info("开始初始化服务...")

    # 检查并获取可用端口
    try:
        logger.info(f"查找可用端口，起始端口: {port}")
        port = find_available_port(port)
        service_info['port'] = port
        logger.info(f"服务将运行在端口: {port}")
    except Exception as e:
        logger.error(f"无法找到可用端口: {e}", exc_info=True)
        sys.exit(1)

    # 注册服务到Nacos
    logger.info("开始注册服务到Nacos...")
    if register_service_to_nacos():
        logger.info("服务成功注册到Nacos")
    else:
        logger.warning("服务注册到Nacos失败")

    # 保存服务信息到数据库
    logger.info("开始保存服务信息到数据库...")
    if save_service_to_database():
        logger.info("服务信息成功保存到数据库")
    else:
        logger.warning("服务信息保存到数据库失败")


# 修改主函数，确保在Flask直接运行时也能处理端口冲突
if __name__ == "__main__":
    try:
        # 检查是否以root权限运行
        if os.geteuid() != 0:
            logger.warning("警告: 当前未以root用户运行，可能会导致模型服务启动失败")
            logger.info("建议使用以下命令以root权限运行:")
            logger.info(f"  sudo python {sys.argv[0]} {model_id} {model_path} {port}")

        logger.info(f"启动模型服务，模型ID: {model_id}，模型路径: {model_path}，端口: {port}")

        # 初始化服务
        init_service()

        # 更新服务状态
        service_info['status'] = "running"
        logger.info("服务状态更新为: running")

        # 启动Flask应用，使用找到的可用端口
        logger.info(f"模型服务启动中，模型ID: {model_id}，端口: {port}")
        app.run(host="0.0.0.0", port=port, debug=False)
    except Exception as e:
        logger.error(f"启动模型服务时发生错误: {e}", exc_info=True)
        sys.exit(1)