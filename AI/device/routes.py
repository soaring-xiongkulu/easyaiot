from flask import jsonify, request
from .service import get_devices_service, create_device_service

def get_devices():
    try:
        devices_list = get_devices_service()
        return jsonify(devices_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def create_device():
    try:
        data = request.get_json()
        device_id = data['device_id']
        name = data['name']
        description = data.get('description', '')
        
        result = create_device_service(device_id, name, description)
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500