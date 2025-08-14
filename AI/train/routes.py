from flask import Blueprint, request, jsonify
from train.service import YOLOv8TrainingService
from train.service import (log_training_step_service, get_training_logs_service, 
                     get_current_training_step_service, get_training_config_service,
                     update_training_status_service, list_trainings_service)

import os

train_bp = Blueprint('train', __name__)
training_service = YOLOv8TrainingService()

@train_bp.route('/', methods=['GET'])
def train_info():
    return jsonify({
        "message": "YOLOv8 Training Service",
        "endpoints": {
            "start_training": "/train/start",
            "training_status": "/train/status/<task_id>"
        }
    })

@train_bp.route('/start', methods=['POST'])
def start_training():
    try:
        data = request.get_json()
        
        # 必需参数
        dataset_url = data.get('dataset_url')
        model_config = data.get('model_config', {})
        
        if not dataset_url:
            return jsonify({"error": "dataset_url is required"}), 400
        
        # 启动训练任务
        task_id = training_service.start_training(dataset_url, model_config)
        
        return jsonify({
            "message": "Training started successfully",
            "task_id": task_id
        }), 202
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@train_bp.route('/status/<task_id>', methods=['GET'])
def training_status(task_id):
    try:
        status = training_service.get_training_status(task_id)
        if status:
            return jsonify(status)
        else:
            return jsonify({"error": "Task not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@train_bp.route('/log', methods=['POST'])
def log_training_step():
    try:
        data = request.get_json()
        training_id = data['training_id']
        step = data['step']
        operation = data['operation']
        details = data.get('details', {})
        status = data.get('status', 'running')
        
        result = log_training_step_service(training_id, step, operation, details, status)
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@train_bp.route('/logs/<training_id>', methods=['GET'])
def get_training_logs(training_id):
    try:
        # 获取分页参数
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        offset = (page - 1) * per_page
        
        result = get_training_logs_service(training_id, page, per_page, offset)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@train_bp.route('/current_step/<training_id>', methods=['GET'])
def get_current_training_step(training_id):
    try:
        result = get_current_training_step_service(training_id)
        if result:
            return jsonify(result), 200
        else:
            return jsonify({"message": "No training logs found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 新增：获取训练配置
@train_bp.route('/config/<training_id>', methods=['GET'])
def get_training_config(training_id):
    try:
        result = get_training_config_service(training_id)
        if result:
            return jsonify(result), 200
        else:
            return jsonify({"message": "No training config found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 新增：更新训练状态
@train_bp.route('/status/<training_id>', methods=['PUT'])
def update_training_status(training_id):
    try:
        data = request.get_json()
        status = data.get('status')
        
        if not status:
            return jsonify({"error": "status is required"}), 400
            
        result = update_training_status_service(training_id, status)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 新增：列出所有训练任务
@train_bp.route('/list', methods=['GET'])
def list_trainings():
    try:
        # 获取分页参数
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        offset = (page - 1) * per_page
        
        result = list_trainings_service(page, per_page, offset)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
