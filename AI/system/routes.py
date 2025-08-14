from flask import jsonify
from .service import index_service, health_check_service

def index():
    return index_service()

def health_check():
    result, status_code = health_check_service()
    return jsonify(result), status_code