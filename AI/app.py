from flask import Flask
import os

# 导入各个模块的路由
from device.routes import get_devices, create_device
from train.routes import log_training_step, get_training_logs, get_current_training_step
from system.routes import index, health_check
from model.routes import get_model_service, deploy_model, check_model_service_status, list_model_services

app = Flask(__name__)

@app.route('/')
def index_route():
    return index()

@app.route('/api/devices', methods=['GET'])
def devices_get():
    return get_devices()

@app.route('/api/devices', methods=['POST'])
def devices_post():
    return create_device()

# 健康检查端点，供Nacos进行健康检查
@app.route('/health', methods=['GET'])
def health():
    return health_check()

# 记录训练步骤日志
@app.route('/api/training/log', methods=['POST'])
def training_log():
    return log_training_step()

# 查询训练日志
@app.route('/api/training/<training_id>/logs', methods=['GET'])
def training_logs(training_id):
    return get_training_logs(training_id)

# 获取训练当前步骤
@app.route('/api/training/<training_id>/current', methods=['GET'])
def current_training_step(training_id):
    return get_current_training_step(training_id)

# 模型服务接口
@app.route('/api/models/deploy', methods=['POST'])
def deploy_model_route():
    return deploy_model()

@app.route('/api/models/<model_id>', methods=['GET'])
def get_model_service_route(model_id):
    return get_model_service(model_id)

@app.route('/api/models/<model_id>/status', methods=['GET'])
def check_model_service_status_route(model_id):
    return check_model_service_status(model_id)

@app.route('/api/models', methods=['GET'])
def list_model_services_route():
    return list_model_services()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)