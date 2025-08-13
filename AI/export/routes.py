from flask import Blueprint, request, jsonify, send_file
from .service import YOLOv8ExportService
import os

export_bp = Blueprint('export', __name__)
export_service = YOLOv8ExportService()

@export_bp.route('/', methods=['GET'])
def export_info():
    return jsonify({
        "message": "YOLOv8 Export Service",
        "endpoints": {
            "export_model": "/export/model",
            "download_model": "/export/download/<model_id>"
        }
    })

@export_bp.route('/model', methods=['POST'])
def export_model():
    try:
        data = request.get_json()
        
        # 必需参数
        model_path = data.get('model_path')
        export_format = data.get('export_format', 'onnx')
        
        if not model_path:
            return jsonify({"error": "model_path is required"}), 400
        
        if not os.path.exists(model_path):
            return jsonify({"error": "Model file not found"}), 404
        
        # 导出模型
        export_result = export_service.export_model(model_path, export_format)
        
        return jsonify({
            "message": "Model exported successfully",
            "export_path": export_result["export_path"],
            "model_id": export_result["model_id"]
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@export_bp.route('/download/<model_id>', methods=['GET'])
def download_model(model_id):
    try:
        model_info = export_service.get_exported_model(model_id)
        if not model_info:
            return jsonify({"error": "Model not found"}), 404
            
        return send_file(
            model_info["export_path"],
            as_attachment=True,
            download_name=os.path.basename(model_info["export_path"])
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500