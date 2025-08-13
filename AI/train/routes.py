from flask import Blueprint, request, jsonify
from .service import YOLOv8TrainingService
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