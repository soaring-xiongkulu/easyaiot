from flask import jsonify, request
from .service import get_model_service_service, deploy_model_service, check_model_service_status_service, list_model_services_service

def get_model_service(model_id):
    try:
        result, status_code = get_model_service_service(model_id)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

def check_model_service_status(model_id):
    try:
        result, status_code = check_model_service_status_service(model_id)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def list_model_services():
    try:
        result, status_code = list_model_services_service()
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500