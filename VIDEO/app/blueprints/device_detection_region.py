"""
设备区域检测管理路由
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import cv2
import subprocess
import numpy as np
import json
from flask import Blueprint, request, jsonify

from models import Device, Image, db, AlgorithmTask
from app.services.device_detection_region_service import (
    get_device_regions, create_device_region, update_device_region,
    delete_device_region, update_device_cover_image
)
from app.blueprints.camera import upload_screenshot_to_minio

device_detection_region_bp = Blueprint('device_detection_region', __name__)
logger = logging.getLogger(__name__)


@device_detection_region_bp.route('/device/<string:device_id>/regions', methods=['GET'])
def list_device_regions(device_id):
    """获取设备的检测区域列表"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'code': 400, 'msg': f'设备不存在: ID={device_id}'}), 400
        
        regions = get_device_regions(device_id)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': [region.to_dict() for region in regions]
        })
    except Exception as e:
        logger.error(f'获取设备检测区域列表失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@device_detection_region_bp.route('/device/<string:device_id>/regions', methods=['POST'])
def create_region(device_id):
    """创建设备检测区域"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        # 检查设备是否关联了算法任务，以及算法任务是否有模型列表
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'code': 400, 'msg': f'设备不存在: ID={device_id}'}), 400
        
        # 查找设备关联的算法任务（实时算法任务）
        algorithm_tasks = AlgorithmTask.query.filter(
            AlgorithmTask.devices.contains(device),
            AlgorithmTask.task_type == 'realtime'
        ).all()
        
        if algorithm_tasks:
            # 检查是否有算法任务配置了模型列表
            has_valid_model = False
            for task in algorithm_tasks:
                if task.model_ids:
                    try:
                        model_ids_list = json.loads(task.model_ids) if isinstance(task.model_ids, str) else task.model_ids
                        if model_ids_list and len(model_ids_list) > 0:
                            has_valid_model = True
                            break
                    except:
                        pass
            
            if not has_valid_model:
                return jsonify({'code': 400, 'msg': '该设备关联的算法任务未配置算法模型列表，无法配置区域检测'}), 400
        
        region_name = data.get('region_name')
        if not region_name:
            return jsonify({'code': 400, 'msg': '区域名称不能为空'}), 400
        
        region_type = data.get('region_type', 'polygon')
        if region_type not in ['polygon', 'line']:
            return jsonify({'code': 400, 'msg': '区域类型必须是 polygon 或 line'}), 400
        
        points = data.get('points')
        if not points or not isinstance(points, list):
            return jsonify({'code': 400, 'msg': '区域坐标点不能为空'}), 400
        
        # 处理 model_ids
        model_ids = data.get('model_ids')
        if model_ids and not isinstance(model_ids, list):
            try:
                model_ids = json.loads(model_ids) if isinstance(model_ids, str) else model_ids
            except:
                model_ids = None
        
        region = create_device_region(
            device_id=device_id,
            region_name=region_name,
            region_type=region_type,
            points=points,
            image_id=data.get('image_id'),
            color=data.get('color', '#FF5252'),
            opacity=data.get('opacity', 0.3),
            is_enabled=data.get('is_enabled', True),
            sort_order=data.get('sort_order', 0),
            model_ids=model_ids
        )
        
        return jsonify({
            'code': 0,
            'msg': '创建成功',
            'data': region.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'创建设备检测区域失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@device_detection_region_bp.route('/region/<int:region_id>', methods=['PUT'])
def update_region(region_id):
    """更新设备检测区域"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        # 获取区域信息，检查设备是否关联了算法任务
        from models import DeviceDetectionRegion
        region = DeviceDetectionRegion.query.get(region_id)
        if not region:
            return jsonify({'code': 400, 'msg': f'检测区域不存在: ID={region_id}'}), 400
        
        device = Device.query.get(region.device_id)
        if device:
            # 查找设备关联的算法任务（实时算法任务）
            algorithm_tasks = AlgorithmTask.query.filter(
                AlgorithmTask.devices.contains(device),
                AlgorithmTask.task_type == 'realtime'
            ).all()
            
            if algorithm_tasks:
                # 检查是否有算法任务配置了模型列表
                has_valid_model = False
                for task in algorithm_tasks:
                    if task.model_ids:
                        try:
                            model_ids_list = json.loads(task.model_ids) if isinstance(task.model_ids, str) else task.model_ids
                            if model_ids_list and len(model_ids_list) > 0:
                                has_valid_model = True
                                break
                        except:
                            pass
                
                if not has_valid_model:
                    # 如果算法任务没有模型列表，自动禁用区域检测配置
                    data['is_enabled'] = False
                    logger.info(f"算法任务未配置模型列表，自动禁用区域检测配置: region_id={region_id}")
        
        region_type = data.get('region_type')
        if region_type and region_type not in ['polygon', 'line']:
            return jsonify({'code': 400, 'msg': '区域类型必须是 polygon 或 line'}), 400
        
        region = update_device_region(region_id, **data)
        
        return jsonify({
            'code': 0,
            'msg': '更新成功',
            'data': region.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'更新设备检测区域失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@device_detection_region_bp.route('/region/<int:region_id>', methods=['DELETE'])
def delete_region(region_id):
    """删除设备检测区域"""
    try:
        delete_device_region(region_id)
        return jsonify({
            'code': 0,
            'msg': '删除成功'
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'删除设备检测区域失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@device_detection_region_bp.route('/device/<string:device_id>/cover-image', methods=['POST'])
def update_cover_image(device_id):
    """抓拍并更新设备封面图"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'code': 400, 'msg': f'设备不存在: ID={device_id}'}), 400
        
        if not device.source:
            return jsonify({'code': 400, 'msg': '设备源地址为空'}), 400
        
        # 抓拍逻辑（复用camera.py中的逻辑）
        source = device.source.strip()
        source_lower = source.lower()
        
        # 判断是否是RTMP流
        if source_lower.startswith('rtmp://'):
            # 使用FFmpeg从RTMP流中抽帧
            try:
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-i', source,
                    '-vframes', '1',
                    '-f', 'image2',
                    '-vcodec', 'mjpeg',
                    '-q:v', '2',
                    'pipe:1'
                ]
                
                process = subprocess.Popen(
                    ffmpeg_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                stdout, stderr = process.communicate(timeout=10)
                
                if process.returncode != 0:
                    error_msg = stderr.decode('utf-8', errors='ignore') if stderr else '未知错误'
                    return jsonify({'code': 500, 'msg': f'RTMP流抽帧失败: {error_msg}'}), 500
                
                if not stdout:
                    return jsonify({'code': 500, 'msg': 'RTMP流抽帧失败: 未获取到图像数据'}), 500
                
                image_array = np.frombuffer(stdout, np.uint8)
                frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                
                if frame is None:
                    return jsonify({'code': 500, 'msg': 'RTMP流抽帧失败: 图像解码失败'}), 500
            except subprocess.TimeoutExpired:
                return jsonify({'code': 500, 'msg': 'RTMP流抽帧超时'}), 500
            except Exception as e:
                logger.error(f"RTMP流抽帧异常: {str(e)}", exc_info=True)
                return jsonify({'code': 500, 'msg': f'RTMP流抽帧异常: {str(e)}'}), 500
        else:
            # 使用OpenCV从RTSP流抓取一帧
            cap = cv2.VideoCapture(source)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return jsonify({'code': 500, 'msg': '无法从RTSP流读取帧'}), 500
        
        # 上传到MinIO并存入数据库
        image_url = upload_screenshot_to_minio(device_id, frame, 'jpg')
        
        if not image_url:
            return jsonify({'code': 500, 'msg': '图片上传失败'}), 500
        
        # 更新设备封面图
        device = update_device_cover_image(device_id, image_url)
        
        # 获取图片信息
        image_record = Image.query.filter_by(device_id=device_id).order_by(Image.created_at.desc()).first()
        
        return jsonify({
            'code': 0,
            'msg': '更新封面图成功',
            'data': {
                'cover_image_path': device.cover_image_path,
                'image_url': image_url,
                'image_id': image_record.id if image_record else None,
                'width': image_record.width if image_record else None,
                'height': image_record.height if image_record else None
            }
        })
    except Exception as e:
        logger.error(f'更新设备封面图失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@device_detection_region_bp.route('/device/<string:device_id>/snapshot', methods=['POST'])
def capture_device_snapshot(device_id):
    """抓拍设备截图（用于区域检测绘制）"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'code': 400, 'msg': f'设备不存在: ID={device_id}'}), 400
        
        if not device.source:
            return jsonify({'code': 400, 'msg': '设备源地址为空'}), 400
        
        source = device.source.strip()
        source_lower = source.lower()
        
        # 判断是否是RTMP流
        if source_lower.startswith('rtmp://'):
            # 使用FFmpeg从RTMP流中抽帧
            try:
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-i', source,
                    '-vframes', '1',
                    '-f', 'image2',
                    '-vcodec', 'mjpeg',
                    '-q:v', '2',
                    'pipe:1'
                ]
                
                process = subprocess.Popen(
                    ffmpeg_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                stdout, stderr = process.communicate(timeout=10)
                
                if process.returncode != 0:
                    error_msg = stderr.decode('utf-8', errors='ignore') if stderr else '未知错误'
                    return jsonify({'code': 500, 'msg': f'RTMP流抽帧失败: {error_msg}'}), 500
                
                if not stdout:
                    return jsonify({'code': 500, 'msg': 'RTMP流抽帧失败: 未获取到图像数据'}), 500
                
                image_array = np.frombuffer(stdout, np.uint8)
                frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                
                if frame is None:
                    return jsonify({'code': 500, 'msg': 'RTMP流抽帧失败: 图像解码失败'}), 500
            except subprocess.TimeoutExpired:
                return jsonify({'code': 500, 'msg': 'RTMP流抽帧超时'}), 500
            except Exception as e:
                logger.error(f"RTMP流抽帧异常: {str(e)}", exc_info=True)
                return jsonify({'code': 500, 'msg': f'RTMP流抽帧异常: {str(e)}'}), 500
        else:
            # 使用OpenCV从RTSP流抓取一帧
            cap = cv2.VideoCapture(source)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return jsonify({'code': 500, 'msg': '无法从RTSP流读取帧'}), 500
        
        # 上传到MinIO并存入数据库
        image_url = upload_screenshot_to_minio(device_id, frame, 'jpg')
        
        if not image_url:
            return jsonify({'code': 500, 'msg': '图片上传失败'}), 500
        
        # 自动更新设备封面图
        try:
            device = update_device_cover_image(device_id, image_url)
            logger.info(f"抓拍成功后自动更新设备封面图: device_id={device_id}, image_path={image_url}")
        except Exception as e:
            logger.warning(f"抓拍成功后自动更新设备封面图失败: {str(e)}，但不影响抓拍结果")
        
        # 获取图片信息
        image_record = Image.query.filter_by(device_id=device_id).order_by(Image.created_at.desc()).first()
        
        return jsonify({
            'code': 0,
            'msg': '抓拍成功',
            'data': {
                'image_id': image_record.id if image_record else None,
                'image_url': image_url,
                'width': image_record.width if image_record else None,
                'height': image_record.height if image_record else None
            }
        })
    except Exception as e:
        logger.error(f'抓拍设备截图失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500

