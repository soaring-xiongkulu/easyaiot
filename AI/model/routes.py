from flask import Blueprint, jsonify, request
from model.service import get_model_service_service, deploy_model_service, check_model_service_status_service, list_model_services_service
from model.service import stop_model_service_service, get_model_service_detail_service
# 添加predict相关导入
from model.service import predict_service
# 添加文件操作相关导入
import os
import tempfile

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
        # 检查是否有文件上传
        local_model_file = request.files.get('model_file')
        local_model_path = None
        
        # 保存上传的文件到临时位置
        if local_model_file:
            # 创建临时文件
            temp_dir = tempfile.mkdtemp()
            local_model_path = os.path.join(temp_dir, local_model_file.filename)
            local_model_file.save(local_model_path)
        
        # 获取表单数据或JSON数据
        if request.is_json:
            data = request.get_json()
        else:
            # 从表单数据中获取
            data = {
                'model_id': request.form.get('model_id'),
                'model_name': request.form.get('model_name'),
                'model_version': request.form.get('model_version'),
                'minio_model_path': request.form.get('minio_model_path')
            }
        
        model_id = data['model_id']
        model_name = data['model_name']
        model_version = data['model_version']
        minio_model_path = data.get('minio_model_path')
        
        # 调用部署服务，支持从MinIO下载或使用上传的本地文件
        result, status_code = deploy_model_service(
            model_id, model_name, model_version, 
            minio_model_path=minio_model_path,
            local_model_path=local_model_path
        )
        
        # 清理临时文件
        if local_model_path and os.path.exists(local_model_path):
            temp_dir = os.path.dirname(local_model_path)
            import shutil
            shutil.rmtree(temp_dir)
        
        return jsonify(result), status_code
    except Exception as e:
        # 清理临时文件（如果存在）
        if 'local_model_path' in locals() and local_model_path and os.path.exists(local_model_path):
            temp_dir = os.path.dirname(local_model_path)
            import shutil
            shutil.rmtree(temp_dir)
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

# 新增：模型推理接口
@model_bp.route('/<model_id>/predict', methods=['POST'])
def predict(model_id):
    try:
        data = request.get_json()
        result, status_code = predict_service(model_id, data)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500
