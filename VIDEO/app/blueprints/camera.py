import datetime
import io
import logging
import threading
import time
from operator import or_

import cv2
import numpy as np
import requests
from flask import Blueprint, request, jsonify, current_app
from minio import Minio
from minio.error import S3Error

from app.services.camera_service import (
    register_camera, get_camera_info, update_camera, delete_camera,
    move_camera_ptz, get_device_list, search_camera,
    get_snapshot_uri, refresh_camera
)
from models import Device

# 创建蓝图
camera_bp = Blueprint('camera', __name__)
logger = logging.getLogger(__name__)

# 全局变量管理截图任务状态
rtsp_tasks = {}
onvif_tasks = {}

# ------------------------- 设备管理接口 -------------------------
@camera_bp.route('/list', methods=['GET'])
def list_devices():
    """查询设备列表（支持分页和搜索）"""
    try:
        # 获取请求参数
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 10))
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()

        # 参数验证
        if page_no < 1 or page_size < 1:
            return jsonify({'code': 400, 'msg': '参数错误：pageNo和pageSize必须为正整数'}), 400

        # 构建基础查询
        query = Device.query

        # 添加搜索条件
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                or_(
                    Device.name.ilike(search_pattern),
                    Device.model.ilike(search_pattern),
                    Device.serial_number.ilike(search_pattern),
                    Device.manufacturer.ilike(search_pattern),
                    Device.ip.ilike(search_pattern)
                )
            )

        # 添加状态过滤
        if status:
            if status.lower() == 'online':
                query = query.filter(Device.status == 'online')
            elif status.lower() == 'offline':
                query = query.filter(Device.status == 'offline')

        # 执行分页查询
        pagination = query.paginate(
            page=page_no,
            per_page=page_size,
            error_out=False
        )

        # 构建响应数据
        device_list = []
        for device in pagination.items:
            device_data = {
                'id': device.id,
                'name': device.name,
                'source': device.source,
                'ip': device.ip,
                'port': device.port,
                'manufacturer': device.manufacturer,
                'model': device.model,
                'firmware_version': device.firmware_version,
                'serial_number': device.serial_number,
                'hardware_id': device.hardware_id,
                'support_move': device.support_move,
                'support_zoom': device.support_zoom,
                'status': device.status,
                'created_at': device.created_at.isoformat() if device.created_at else None,
                'updated_at': device.updated_at.isoformat() if device.updated_at else None
            }

            # 添加NVR信息（如果存在）
            if device.nvr:
                device_data['nvr'] = {
                    'id': device.nvr.id,
                    'name': device.nvr.name,
                    'ip': device.nvr.ip
                }
                device_data['nvr_channel'] = device.nvr_channel

            device_list.append(device_data)

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'items': device_list,
                'total': pagination.total,
                'pageNo': page_no,
                'pageSize': page_size,
                'totalPages': pagination.pages
            }
        })

    except ValueError:
        return jsonify({'code': 400, 'msg': '参数类型错误：pageNo和pageSize需为整数'}), 400
    except Exception as e:
        logger.error(f'设备列表查询失败: {str(e)}')
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500

@camera_bp.route('/device/<string:device_id>', methods=['GET'])
def get_device_info(device_id):
    """获取单个设备详情"""
    try:
        info = get_camera_info(device_id)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': info
        })
    except ValueError:
        return jsonify({'code': 404, 'msg': f'设备 {device_id} 不存在'}), 404
    except Exception as e:
        logger.error(f'获取设备详情失败: {str(e)}')
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500

@camera_bp.route('/register/device', methods=['POST'])
def register_device():
    """注册新设备"""
    try:
        data = request.get_json()
        device_id = register_camera(data)
        return jsonify({
            'code': 0,
            'msg': '设备注册成功',
            'data': {'id': device_id}
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


@camera_bp.route('/device/<string:device_id>', methods=['PUT'])
def update_device(device_id):
    """更新设备信息"""
    try:
        data = request.get_json()
        update_camera(device_id, data)
        return jsonify({
            'code': 0,
            'msg': '设备信息更新成功'
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


@camera_bp.route('/device/<string:device_id>', methods=['DELETE'])
def delete_device(device_id):
    """删除设备"""
    try:
        delete_camera(device_id)
        return jsonify({
            'code': 0,
            'msg': '设备删除成功'
        })
    except ValueError as e:
        return jsonify({'code': 404, 'msg': str(e)}), 404
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


# ------------------------- PTZ控制接口 -------------------------
@camera_bp.route('/device/<string:device_id>/ptz', methods=['POST'])
def control_ptz(device_id):
    """控制摄像头PTZ"""
    try:
        data = request.get_json()
        move_camera_ptz(device_id, data)
        return jsonify({
            'code': 0,
            'msg': 'PTZ指令已发送'
        })
    except ValueError as e:
        return jsonify({'code': 404, 'msg': str(e)}), 404
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


# ------------------------- 设备状态接口 -------------------------
@camera_bp.route('/device/status', methods=['GET'])
def get_device_status():
    """获取所有设备状态统计"""
    try:
        status = get_device_list()
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': status
        })
    except Exception as e:
        logger.error(f'获取设备状态失败: {str(e)}')
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500


# ------------------------- MinIO上传服务 -------------------------
def get_minio_client():
    """创建并返回Minio客户端"""
    minio_endpoint = current_app.config.get('MINIO_ENDPOINT', 'localhost:9000')
    access_key = current_app.config.get('MINIO_ACCESS_KEY', 'minioadmin')
    secret_key = current_app.config.get('MINIO_SECRET_KEY', 'minioadmin')
    secure = current_app.config.get('MINIO_SECURE', 'false').lower() == 'true'
    return Minio(minio_endpoint, access_key, secret_key, secure=secure)


def upload_screenshot_to_minio(camera_id, image_data, image_format="jpg"):
    """上传摄像头截图到MinIO"""
    try:
        minio_client = get_minio_client()
        bucket_name = "camera-screenshots"

        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            logger.info(f"创建截图存储桶: {bucket_name}")

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        object_name = f"{camera_id}/{timestamp}.{image_format}"

        success, encoded_image = cv2.imencode(f'.{image_format}', image_data)
        if not success:
            raise RuntimeError("图像编码失败")

        image_bytes = encoded_image.tobytes()
        minio_client.put_object(
            bucket_name,
            object_name,
            io.BytesIO(image_bytes),
            len(image_bytes),
            content_type=f"image/{image_format}"
        )

        presigned_url = minio_client.presigned_get_object(
            bucket_name,
            object_name,
            expires=datetime.timedelta(days=7)
        )
        logger.info(f"截图上传成功: {bucket_name}/{object_name}")
        return presigned_url
    except S3Error as e:
        logger.error(f"MinIO上传错误: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"截图上传未知错误: {str(e)}")
        return None


# ------------------------- RTSP截图功能 -------------------------
def rtsp_capture_task(device_id, rtsp_url, interval, max_count):
    """RTSP截图线程任务"""
    cap = cv2.VideoCapture(rtsp_url)
    count = 0
    image_format = current_app.config.get('SCREENSHOT_FORMAT', 'jpg')

    while rtsp_tasks.get(device_id, {}).get('running', False) and count < max_count:
        start_time = time.time()
        ret, frame = cap.read()
        if not ret:
            logger.error(f"设备 {device_id} RTSP流读取失败")
            break

        image_url = upload_screenshot_to_minio(device_id, frame, image_format)
        if image_url:
            logger.info(f"设备 {device_id} 截图已上传: {image_url}")
            count += 1
        else:
            logger.error(f"设备 {device_id} 截图上传失败")

        elapsed = time.time() - start_time
        sleep_time = max(0, interval - elapsed)
        time.sleep(sleep_time)

    cap.release()
    rtsp_tasks[device_id]['running'] = False


@camera_bp.route('/device/<int:device_id>/rtsp/start', methods=['POST'])
def start_rtsp_capture(device_id):
    """启动RTSP截图"""
    try:
        device = Device.query.get_or_404(device_id)
        data = request.get_json()
        rtsp_url = data.get('rtsp_url', device.source)
        interval = data.get('interval', 5)
        max_count = data.get('max_count', 100)

        if not rtsp_url:
            return jsonify({'success': False, 'message': 'RTSP地址不能为空'})

        if device_id in rtsp_tasks and rtsp_tasks[device_id]['running']:
            return jsonify({'success': False, 'message': '该设备的截图任务已在运行'})

        rtsp_tasks[device_id] = {'running': True, 'thread': None}
        thread = threading.Thread(
            target=rtsp_capture_task,
            args=(device_id, rtsp_url, interval, max_count)
        )
        thread.daemon = True
        thread.start()
        rtsp_tasks[device_id]['thread'] = thread

        return jsonify({
            'success': True,
            'message': 'RTSP截图任务已启动',
            'task_id': thread.ident
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'RTSP截图启动失败: {str(e)}'})


@camera_bp.route('/device/<int:device_id>/rtsp/stop', methods=['POST'])
def stop_rtsp_capture(device_id):
    """停止RTSP截图任务"""
    try:
        if device_id in rtsp_tasks:
            rtsp_tasks[device_id]['running'] = False
            if rtsp_tasks[device_id]['thread']:
                rtsp_tasks[device_id]['thread'].join(timeout=5.0)
            return jsonify({'success': True, 'message': 'RTSP截图任务已停止'})
        return jsonify({'success': False, 'message': '未找到运行的RTSP截图任务'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'停止RTSP截图失败: {str(e)}'})


@camera_bp.route('/device/<int:device_id>/rtsp/status', methods=['GET'])
def rtsp_status(device_id):
    """获取RTSP截图状态"""
    try:
        status = "stopped"
        if device_id in rtsp_tasks:
            status = "running" if rtsp_tasks[device_id]['running'] else "stopped"
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取RTSP状态失败: {str(e)}'})


# ------------------------- ONVIF功能 -------------------------
def onvif_capture_task(device_id, snapshot_uri, username, password, interval, max_count):
    """ONVIF截图线程任务"""
    count = 0
    auth = (username, password) if username and password else None
    image_format = current_app.config.get('SCREENSHOT_FORMAT', 'jpg')

    while onvif_tasks.get(device_id, {}).get('running', False) and count < max_count:
        start_time = time.time()
        try:
            response = requests.get(snapshot_uri, auth=auth, timeout=10)
            if response.status_code == 200:
                image_bytes = io.BytesIO(response.content)
                image_bytes.seek(0)
                image_np = cv2.imdecode(np.frombuffer(image_bytes.read(), np.uint8), cv2.IMREAD_COLOR)

                image_url = upload_screenshot_to_minio(device_id, image_np, image_format)
                if image_url:
                    logger.info(f"设备 {device_id} ONVIF截图已上传: {image_url}")
                    count += 1
                else:
                    logger.error(f"设备 {device_id} ONVIF截图上传失败")
            else:
                logger.error(f"ONVIF快照请求失败: {response.status_code}")
        except Exception as e:
            logger.error(f"ONVIF截图失败: {str(e)}")

        elapsed = time.time() - start_time
        sleep_time = max(0, interval - elapsed)
        time.sleep(sleep_time)

    onvif_tasks[device_id]['running'] = False


@camera_bp.route('/device/<int:device_id>/onvif/start', methods=['POST'])
def start_onvif_capture(device_id):
    """启动ONVIF截图"""
    try:
        device = Device.query.get_or_404(device_id)
        data = request.get_json()
        interval = data.get('interval', 10)
        max_count = data.get('max_count', 100)

        snapshot_uri = get_snapshot_uri(
            device.ip, device.port, device.username, device.password
        )
        if not snapshot_uri:
            return jsonify({'success': False, 'message': '无法获取ONVIF快照URI'})

        if device_id in onvif_tasks and onvif_tasks[device_id]['running']:
            return jsonify({'success': False, 'message': '该设备的ONVIF截图任务已在运行'})

        onvif_tasks[device_id] = {'running': True, 'thread': None}
        thread = threading.Thread(
            target=onvif_capture_task,
            args=(device_id, snapshot_uri, device.username, device.password, interval, max_count)
        )
        thread.daemon = True
        thread.start()
        onvif_tasks[device_id]['thread'] = thread

        return jsonify({
            'success': True,
            'message': 'ONVIF截图任务已启动',
            'task_id': thread.ident
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'ONVIF截图启动失败: {str(e)}'})


@camera_bp.route('/device/<int:device_id>/onvif/stop', methods=['POST'])
def stop_onvif_capture(device_id):
    """停止ONVIF截图"""
    try:
        if device_id in onvif_tasks:
            onvif_tasks[device_id]['running'] = False
            if onvif_tasks[device_id]['thread']:
                onvif_tasks[device_id]['thread'].join(timeout=5.0)
            return jsonify({'success': True, 'message': 'ONVIF截图任务已停止'})
        return jsonify({'success': False, 'message': '未找到运行的ONVIF截图任务'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'ONVIF截图停止失败: {str(e)}'})


@camera_bp.route('/device/<int:device_id>/onvif/status', methods=['GET'])
def onvif_status(device_id):
    """获取ONVIF截图状态"""
    try:
        status = "stopped"
        if device_id in onvif_tasks:
            status = "running" if onvif_tasks[device_id]['running'] else "stopped"
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取ONVIF截图状态失败: {str(e)}'})


# ------------------------- 设备发现接口 -------------------------
@camera_bp.route('/discovery', methods=['GET'])
def discover_devices():
    """发现网络中的ONVIF设备"""
    try:
        devices = search_camera()
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': devices
        })
    except Exception as e:
        logger.error(f'设备发现失败: {str(e)}')
        return jsonify({'code': 500, 'msg': '设备发现失败'}), 500


# ------------------------- 设备刷新服务 -------------------------
@camera_bp.route('/refresh', methods=['POST'])
def refresh_devices():
    """刷新设备IP信息"""
    try:
        refresh_camera()
        return jsonify({
            'code': 0,
            'msg': '设备刷新任务已启动'
        })
    except Exception as e:
        logger.error(f'设备刷新失败: {str(e)}')
        return jsonify({'code': 500, 'msg': '设备刷新失败'}), 500
