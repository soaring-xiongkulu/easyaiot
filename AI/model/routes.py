from flask import Blueprint, jsonify, request
from model.service import get_model_service_service, deploy_model_service, check_model_service_status_service, list_model_services_service
from model.service import stop_model_service_service, get_model_service_detail_service

# 创建model蓝图
model_bp = Blueprint('model', __name__)

@model_bp.route('/<model_id>', methods=['GET'])
def get_model_service(model_id):
    try:
        result, status_code = get_model_service_service(model_id)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@model_bp.route('/deploy', methods=['POST'])
def deploy_model():
    try:
        data = request.get_json()
        model_id = data['model_id']
        model_name = data['model_name']
        model_version = data['model_version']
        minio_model_path = data['minio_model_path']
        
        result, status_code = deploy_model_service(model_id, model_name, model_version, minio_model_path)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@model_bp.route('/status/<model_id>', methods=['GET'])
def check_model_service_status(model_id):
    try:
        result, status_code = check_model_service_status_service(model_id)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@model_bp.route('/list', methods=['GET'])
def list_model_services():
    try:
        result, status_code = list_model_services_service()
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 新增：停止模型服务
@model_bp.route('/stop/<model_id>', methods=['POST'])
def stop_model_service(model_id):
    try:
        result, status_code = stop_model_service_service(model_id)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 新增：获取模型服务详细信息
@model_bp.route('/detail/<model_id>', methods=['GET'])
def get_model_service_detail(model_id):
    try:
        result, status_code = get_model_service_detail_service(model_id)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500