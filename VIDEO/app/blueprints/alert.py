"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
from flask import Blueprint, request, jsonify, send_file
from pathlib import Path
import logging
from app.services.alert_service import (
    get_alert_list,
    get_alert_count,
    create_alert
)

# 创建Alert蓝图
alert_bp = Blueprint('alert', __name__)
logger = logging.getLogger(__name__)


def api_response(code=200, message="success", data=None):
    """统一API响应格式"""
    response = {
        "code": code,
        "message": message,
        "data": data
    }
    return jsonify(response), code


@alert_bp.route('/page')
def get_alert_list_route():
    """获取报警列表"""
    try:
        args_dict = dict(request.args)
        result = get_alert_list(args_dict)
        return api_response(data=result)
    except Exception as e:
        logger.error(f'获取报警列表失败: {str(e)}')
        return api_response(500, f'获取失败: {str(e)}')


@alert_bp.route('/count')
def get_alert_count_route():
    """获取报警统计"""
    try:
        args_dict = dict(request.args)
        result = get_alert_count(args_dict)
        return api_response(data=result)
    except Exception as e:
        logger.error(f'获取报警统计失败: {str(e)}')
        return api_response(500, f'获取失败: {str(e)}')


@alert_bp.route('/image')
def get_alert_image():
    """获取报警图片"""
    try:
        path = request.args.get('path')
        if not path:
            return api_response(400, '路径参数不能为空')
        
        file_path = Path(path)
        if not file_path.exists():
            return api_response(404, f'文件不存在: {path}')
        
        return send_file(str(file_path))
    except Exception as e:
        logger.error(f'获取报警图片失败: {str(e)}')
        return api_response(500, f'获取失败: {str(e)}')


@alert_bp.route('/record')
def get_alert_record():
    """获取报警录像"""
    try:
        path = request.args.get('path')
        if not path:
            return api_response(400, '路径参数不能为空')
        
        file_path = Path(path)
        if not file_path.exists():
            return api_response(404, f'文件不存在: {path}')
        
        return send_file(str(file_path))
    except Exception as e:
        logger.error(f'获取报警录像失败: {str(e)}')
        return api_response(500, f'获取失败: {str(e)}')


@alert_bp.route('/hook', methods=['POST'])
def create_alert_hook():
    """Hook回调接口：通过HTTP添加告警记录
    
    请求体格式（JSON）:
    {
        "object": "person",           // 必填：对象类型
        "event": "intrusion",         // 必填：事件类型
        "device_id": "camera_001",    // 必填：设备ID
        "device_name": "摄像头1",      // 必填：设备名称
        "region": "区域A",            // 可选：区域
        "information": {...},         // 可选：详细信息（可以是对象或字符串）
        "time": "2024-01-01 12:00:00", // 可选：报警时间（默认当前时间）
        "image_path": "/path/to/image.jpg", // 可选：图片路径
        "record_path": "/path/to/video.mp4" // 可选：录像路径
    }
    """
    try:
        # 获取JSON请求体
        if not request.is_json:
            return api_response(400, '请求体必须是JSON格式')
        
        alert_data = request.get_json()
        if not alert_data:
            return api_response(400, '请求体不能为空')
        
        # 调用服务创建告警记录
        result = create_alert(alert_data)
        return api_response(200, '告警记录创建成功', result)
    except ValueError as e:
        logger.error(f'创建告警记录参数错误: {str(e)}')
        return api_response(400, f'参数错误: {str(e)}')
    except Exception as e:
        logger.error(f'创建告警记录失败: {str(e)}')
        return api_response(500, f'创建失败: {str(e)}')

