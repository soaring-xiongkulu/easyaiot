"""
最小化的模型部署服务模板
用于部署模型并提供推理接口

@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import os
import sys
import time
import threading
import logging
import socket
import atexit
import signal
import multiprocessing
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# 添加当前目录到路径，以便导入模型相关代码
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============================================
# 环境变量和系统配置初始化
# ============================================

# 加载环境变量配置文件
env_file = '.env'
if os.path.exists(env_file):
    load_dotenv(env_file, override=True)
    print(f"✅ 已加载配置文件: {env_file} (覆盖模式)", file=sys.stderr)
else:
    print(f"⚠️  配置文件 {env_file} 不存在，使用系统环境变量", file=sys.stderr)

# 设置multiprocessing启动方法为'spawn'以支持CUDA
try:
    try:
        current_method = multiprocessing.get_start_method()
    except RuntimeError:
        current_method = None
    
    if current_method != 'spawn':
        multiprocessing.set_start_method('spawn', force=True)
        print(f"✅ 已设置multiprocessing启动方法为'spawn'（原方法: {current_method or '未设置'}）", file=sys.stderr)
    else:
        print(f"✅ multiprocessing启动方法已为'spawn'", file=sys.stderr)
except RuntimeError as e:
    try:
        current_method = multiprocessing.get_start_method()
        print(f"⚠️  无法设置multiprocessing启动方法: {str(e)}，当前方法: {current_method}", file=sys.stderr)
    except RuntimeError:
        print(f"⚠️  无法设置multiprocessing启动方法: {str(e)}", file=sys.stderr)

# 强制 ONNX Runtime 使用 CPU（在导入任何使用 ONNX Runtime 的模块之前设置）
os.environ['ORT_EXECUTION_PROVIDERS'] = 'CPUExecutionProvider'
print("✅ 已设置 ONNX Runtime 使用 CPU 执行提供者", file=sys.stderr)

# 如果未设置 CUDA_VISIBLE_DEVICES，临时隐藏 GPU
if 'CUDA_VISIBLE_DEVICES' not in os.environ:
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    print("⚠️  临时隐藏 GPU 设备以避免 onnxruntime-gpu 导入时的 CUDA 库加载错误", file=sys.stderr)

# 导入推理相关模块
ONNXInference = None
try:
    from app.utils.onnx_inference import ONNXInference
except ImportError as e:
    print(f"[SERVICES] 警告: 无法导入ONNX推理模块: {e}", file=sys.stderr)

app = Flask(__name__)
CORS(app)

# 配置日志
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('flask').setLevel(logging.WARNING)

logging.basicConfig(
    level=logging.INFO,
    format='[SERVICES] %(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True,
    stream=sys.stderr
)
logger = logging.getLogger(__name__)
logger.info("=" * 60)
logger.info("🚀 模型部署服务 (Services Module) 启动")
logger.info("=" * 60)

# 全局变量
model = None
model_loaded = False
server_ip = None
port = None
nacos_client = None
nacos_service_name = None


def get_local_ip():
    """获取本地IP地址"""
    # 方案1: 环境变量优先
    if ip := os.getenv('POD_IP'):
        return ip
    
    # 方案2: 多网卡探测
    try:
        import netifaces
        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface).get(netifaces.AF_INET, [])
            for addr in addrs:
                ip = addr['addr']
                if ip != '127.0.0.1' and not ip.startswith('169.254.'):
                    return ip
    except:
        pass
    
    # 方案3: 原始方式
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'


def is_port_available(port, host='0.0.0.0'):
    """检查端口是否可用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            return True
    except OSError:
        return False


def find_available_port(start_port, host='0.0.0.0', max_attempts=100):
    """从指定端口开始，自动递增寻找可用端口"""
    port = start_port
    attempts = 0
    
    while attempts < max_attempts:
        if is_port_available(port, host):
            return port
        port += 1
        attempts += 1
    
    logger.error(f"在 {max_attempts} 次尝试后仍未找到可用端口（从 {start_port} 开始）")
    return None


def load_model(model_path):
    """加载模型"""
    global model, model_loaded
    
    try:
        logger.info(f"开始加载模型: {model_path}")
        
        # 根据文件扩展名判断模型类型
        if model_path.endswith('.onnx'):
            # ONNX模型加载
            try:
                if ONNXInference is None:
                    error_msg = "onnxruntime未安装，无法加载ONNX模型。请运行: pip install onnxruntime"
                    logger.error(error_msg)
                    print(error_msg, file=sys.stderr)
                    return False
                model = ONNXInference(model_path)
                logger.info("✅ ONNX模型加载成功")
                model_loaded = True
                return True
            except Exception as e:
                error_msg = f"ONNX模型加载失败: {str(e)}"
                logger.error(error_msg)
                print(error_msg, file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
                return False
        else:
            # PyTorch模型加载（.pt文件）
            try:
                from ultralytics import YOLO
                model = YOLO(model_path)
                logger.info("✅ YOLO模型加载成功")
                model_loaded = True
                return True
            except ImportError as e:
                error_msg = f"ultralytics未安装，无法加载YOLO模型: {str(e)}。请运行: pip install ultralytics"
                logger.error(error_msg)
                print(error_msg, file=sys.stderr)
                return False
            except Exception as e:
                error_msg = f"YOLO模型加载失败: {str(e)}"
                logger.error(error_msg)
                print(error_msg, file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
                return False
        
    except Exception as e:
        error_msg = f"加载模型失败: {str(e)}"
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        model_loaded = False
        return False


def setup_nacos():
    """设置Nacos注册（可选）"""
    global nacos_client, nacos_service_name, server_ip, port
    
    try:
        from nacos import NacosClient
        
        # 获取Nacos配置
        nacos_server = os.getenv('NACOS_SERVER', 'localhost:8848')
        namespace = os.getenv('NACOS_NAMESPACE', '')
        username = os.getenv('NACOS_USERNAME', 'nacos')
        password = os.getenv('NACOS_PASSWORD', 'basiclab@iot78475418754')
        
        # 创建Nacos客户端
        nacos_client = NacosClient(
            server_addresses=nacos_server,
            namespace=namespace,
            username=username,
            password=password
        )
        
        # 构建Nacos服务名
        service_name = os.getenv('SERVICE_NAME', 'deploy_service')
        nacos_service_name = service_name
        
        # 注册服务实例
        nacos_client.add_naming_instance(
            service_name=nacos_service_name,
            ip=server_ip,
            port=port,
            cluster_name="DEFAULT",
            healthy=True,
            ephemeral=True
        )
        
        logger.info(f"✅ 服务注册到Nacos成功: {nacos_service_name}@{server_ip}:{port}")
        return True
        
    except ImportError:
        logger.warning("nacos-sdk-python未安装，跳过Nacos注册")
        return False
    except Exception as e:
        logger.error(f"Nacos注册失败: {str(e)}")
        return False


def send_nacos_heartbeat():
    """发送Nacos心跳"""
    global nacos_client, nacos_service_name, server_ip, port
    
    while True:
        try:
            if nacos_client and nacos_service_name:
                nacos_client.send_heartbeat(
                    service_name=nacos_service_name,
                    ip=server_ip,
                    port=port
                )
        except Exception as e:
            logger.error(f"Nacos心跳发送异常: {str(e)}")
        
        time.sleep(5)  # 每5秒发送一次Nacos心跳


def deregister_nacos():
    """注销Nacos服务"""
    global nacos_client, nacos_service_name, server_ip, port
    
    try:
        if nacos_client and nacos_service_name:
            nacos_client.remove_naming_instance(
                service_name=nacos_service_name,
                ip=server_ip,
                port=port
            )
            logger.info(f"🔴 Nacos服务注销成功: {nacos_service_name}@{server_ip}:{port}")
    except Exception as e:
        logger.error(f"Nacos注销异常: {str(e)}")


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model_loaded,
        'service_name': os.getenv('SERVICE_NAME', 'deploy_service')
    })


@app.route('/inference', methods=['POST'])
def inference():
    """推理接口"""
    global model, model_loaded
    
    if not model_loaded or model is None:
        return jsonify({
            'code': 500,
            'msg': '模型未加载'
        }), 500
    
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({
                'code': 400,
                'msg': '未找到文件'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'code': 400,
                'msg': '未选择文件'
            }), 400
        
        # 获取推理参数
        conf_thres = float(request.form.get('conf_thres', 0.25))
        iou_thres = float(request.form.get('iou_thres', 0.45))
        
        # 保存临时文件
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
        file.save(temp_file.name)
        temp_file.close()
        
        try:
            # 执行推理
            # 检查是否为ONNX模型
            is_onnx = False
            if ONNXInference is not None:
                is_onnx = isinstance(model, ONNXInference)
            
            if is_onnx:
                # ONNX模型推理
                output_image, detections = model.detect(
                    temp_file.name,
                    conf_threshold=conf_thres,
                    iou_threshold=iou_thres,
                    draw=True
                )
                
                # 保存结果图片
                import cv2
                result_path = temp_file.name.replace(os.path.splitext(temp_file.name)[1], '_result.jpg')
                cv2.imwrite(result_path, output_image)
                
                return jsonify({
                    'code': 0,
                    'msg': '推理成功',
                    'data': {
                        'predictions': detections,
                        'result_image_path': result_path
                    }
                })
            elif hasattr(model, 'predict'):  # YOLO模型
                results = model.predict(
                    temp_file.name,
                    conf=conf_thres,
                    iou=iou_thres,
                    verbose=False
                )
                
                # 处理结果
                predictions = []
                for result in results:
                    boxes = result.boxes
                    for box in boxes:
                        predictions.append({
                            'class': int(box.cls.item()),
                            'class_name': result.names[int(box.cls.item())],
                            'confidence': float(box.conf.item()),
                            'bbox': box.xyxy.tolist()[0]
                        })
                
                # 保存结果图片
                result_path = temp_file.name.replace(os.path.splitext(temp_file.name)[1], '_result.jpg')
                results[0].save(filename=result_path)
                
                return jsonify({
                    'code': 0,
                    'msg': '推理成功',
                    'data': {
                        'predictions': predictions,
                        'result_image_path': result_path
                    }
                })
            else:
                return jsonify({
                    'code': 500,
                    'msg': '不支持的模型类型'
                }), 500
                
        finally:
            # 清理临时文件
            try:
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
            except:
                pass
                
    except Exception as e:
        logger.error(f"推理失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'推理失败: {str(e)}'
        }), 500


@app.route('/stop', methods=['POST'])
def stop_service():
    """停止服务接口"""
    try:
        logger.info("收到停止服务请求")
        deregister_nacos()
        
        # 延迟关闭，给响应时间
        def delayed_shutdown():
            time.sleep(1)
            os._exit(0)
        
        threading.Thread(target=delayed_shutdown, daemon=True).start()
        
        return jsonify({
            'code': 0,
            'msg': '服务正在停止'
        })
    except Exception as e:
        logger.error(f"停止服务失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'停止服务失败: {str(e)}'
        }), 500


@app.route('/restart', methods=['POST'])
def restart_service():
    """重启服务接口"""
    global model, model_loaded
    
    try:
        logger.info("收到重启服务请求")
        
        # 重新加载模型
        model_path = os.getenv('MODEL_PATH')
        if model_path:
            model_loaded = False
            model = None
            if load_model(model_path):
                return jsonify({
                    'code': 0,
                    'msg': '服务重启成功'
                })
            else:
                return jsonify({
                    'code': 500,
                    'msg': '模型重新加载失败'
                }), 500
        else:
            return jsonify({
                'code': 400,
                'msg': 'MODEL_PATH环境变量未设置'
            }), 400
            
    except Exception as e:
        logger.error(f"重启服务失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'重启服务失败: {str(e)}'
        }), 500


def main():
    """主函数"""
    global server_ip, port, nacos_client
    
    # 输出启动信息到stderr
    print("=" * 60, file=sys.stderr)
    print("🚀 模型部署服务启动中...", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # 从环境变量获取配置
    service_name = os.getenv('SERVICE_NAME', 'deploy_service')
    
    # 安全地获取端口号
    try:
        port = int(os.getenv('PORT', 8000))
    except ValueError:
        error_msg = f"❌ 无效的端口号: {os.getenv('PORT')}"
        print(error_msg, file=sys.stderr)
        sys.exit(1)
    
    model_path = os.getenv('MODEL_PATH')
    
    # 输出环境变量信息用于诊断
    print(f"[SERVICES] 服务名称: {service_name}", file=sys.stderr)
    print(f"[SERVICES] 模型路径: {model_path}", file=sys.stderr)
    print(f"[SERVICES] 端口: {port}", file=sys.stderr)
    
    server_ip = get_local_ip()
    print(f"[SERVICES] 服务器IP: {server_ip}", file=sys.stderr)
    
    if not model_path:
        error_msg = "❌ MODEL_PATH环境变量未设置，无法启动服务"
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        sys.exit(1)
    
    # 验证模型文件是否存在
    if not os.path.exists(model_path):
        error_msg = f"❌ 模型文件不存在: {model_path}"
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        sys.exit(1)
    
    # 验证模型文件是否可读
    if not os.access(model_path, os.R_OK):
        error_msg = f"❌ 模型文件不可读: {model_path}"
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        sys.exit(1)
    
    # 加载模型
    logger.info(f"准备加载模型: {model_path}")
    if not load_model(model_path):
        error_msg = f"❌ 模型加载失败: {model_path}，请检查模型文件是否完整或格式是否正确"
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    
    # 注册到Nacos（可选）
    setup_nacos()
    
    # 启动Nacos心跳线程（如果Nacos可用）
    if nacos_client:
        nacos_heartbeat_thread = threading.Thread(target=send_nacos_heartbeat, daemon=True)
        nacos_heartbeat_thread.start()
        logger.info("Nacos心跳线程已启动")
    
    # 注册退出处理
    atexit.register(deregister_nacos)
    
    # 注册信号处理
    def signal_handler(signum, frame):
        logger.info(f"收到信号 {signum}，正在关闭服务...")
        deregister_nacos()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # 检查端口是否可用，如果不可用则自动查找可用端口
    host = '0.0.0.0'
    original_port = port
    logger.info(f"🔍 检查端口 {port} 是否可用...")
    
    if not is_port_available(port, host):
        logger.warning(f"⚠️  端口 {port} 已被占用，正在查找可用端口...")
        new_port = find_available_port(port, host)
        if new_port is None:
            error_msg = f"❌ 无法找到可用端口（从 {port} 开始，已尝试100个端口）"
            logger.error(error_msg)
            print(error_msg, file=sys.stderr)
            sys.exit(1)
        port = new_port
        logger.info(f"✅ 已切换到可用端口: {port}")
    else:
        logger.info(f"✅ 端口 {port} 可用")
    
    # 如果端口发生了变化，更新环境变量
    if port != original_port:
        os.environ['PORT'] = str(port)
        logger.info(f"已更新环境变量 PORT={port}")
    
    # 禁用 Flask 的默认日志输出
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    # 启动Flask服务
    logger.info(f"部署服务启动: {service_name} on {server_ip}:{port}")
    logger.info("=" * 60)
    logger.info(f"🌐 服务地址: http://{server_ip}:{port}")
    logger.info(f"📊 健康检查: http://{server_ip}:{port}/health")
    logger.info(f"🔮 推理接口: http://{server_ip}:{port}/inference")
    logger.info("=" * 60)
    logger.info("🚀 正在启动Flask应用...")
    # 同时输出到stderr
    print("=" * 60, file=sys.stderr)
    print(f"🌐 服务地址: http://{server_ip}:{port}", file=sys.stderr)
    print(f"📊 健康检查: http://{server_ip}:{port}/health", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("🚀 正在启动Flask应用...", file=sys.stderr)
    
    try:
        app.run(host=host, port=port, threaded=True, debug=False, use_reloader=False)
    except OSError as e:
        if "Address already in use" in str(e) or "端口" in str(e):
            error_msg = f"❌ 端口 {port} 启动失败: {str(e)}\n💡 请检查是否有其他进程在使用该端口"
            logger.error(error_msg)
            print(error_msg, file=sys.stderr)
        else:
            error_msg = f"❌ 服务启动失败: {str(e)}"
            logger.error(error_msg)
            print(error_msg, file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        deregister_nacos()
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务...")
        deregister_nacos()
        sys.exit(0)
    except Exception as e:
        error_msg = f"❌ 服务启动异常: {str(e)}"
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        deregister_nacos()
        sys.exit(1)


if __name__ == '__main__':
    main()

