import threading
import time
import cv2
import numpy as np
import requests
import io
import datetime
from flask import Blueprint, request, jsonify, current_app
from onvif import ONVIFCamera

from app.services.camera_service import get_snapshot_uri
from models import Device, db
from minio import Minio
from minio.error import S3Error

# 创建蓝图
camera_bp = Blueprint('camera', __name__)

# 全局变量管理截图任务状态
rtsp_tasks = {}
onvif_tasks = {}


# ------------------------- MinIO上传服务 -------------------------
def get_minio_client():
    """创建并返回Minio客户端"""
    minio_endpoint = current_app.config.get('MINIO_ENDPOINT', 'localhost:9000')
    access_key = current_app.config.get('MINIO_ACCESS_KEY', 'minioadmin')
    secret_key = current_app.config.get('MINIO_SECRET_KEY', 'minioadmin')
    secure = current_app.config.get('MINIO_SECURE', 'false').lower() == 'true'

    return Minio(
        minio_endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure
    )


def upload_screenshot_to_minio(camera_id, image_data, image_format="jpg"):
    """上传摄像头截图到MinIO"""
    try:
        minio_client = get_minio_client()
        bucket_name = "camera-screenshots"  # 专用存储桶

        # 自动创建存储桶
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            current_app.logger.info(f"创建截图存储桶: {bucket_name}")

        # 生成对象名 (按摄像头ID和时间戳组织)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        object_name = f"{camera_id}/{timestamp}.{image_format}"

        # 将图像数据转为字节流上传
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

        # 生成访问URL
        presigned_url = minio_client.presigned_get_object(
            bucket_name,
            object_name,
            expires=datetime.timedelta(days=7)  # 7天有效期
        )

        current_app.logger.info(f"截图上传成功: {bucket_name}/{object_name}")
        return presigned_url
    except S3Error as e:
        current_app.logger.error(f"MinIO截图上传错误: {str(e)}")
        return None
    except Exception as e:
        current_app.logger.error(f"截图上传未知错误: {str(e)}")
        return None


# ------------------------- RTSP截图功能 -------------------------
def rtsp_capture_task(device_id, rtsp_url, interval, max_count):
    """RTSP截图线程任务 - 直接上传到MinIO"""
    cap = cv2.VideoCapture(rtsp_url)
    count = 0
    image_format = current_app.config.get('SCREENSHOT_FORMAT', 'jpg')

    while rtsp_tasks.get(device_id, {}).get('running', False) and count < max_count:
        start_time = time.time()

        # 读取视频帧
        ret, frame = cap.read()
        if not ret:
            current_app.logger.error(f"设备 {device_id} RTSP流读取失败")
            break

        # 上传截图到MinIO
        image_url = upload_screenshot_to_minio(device_id, frame, image_format)
        if image_url:
            current_app.logger.info(f"设备 {device_id} 截图已上传: {image_url}")
            count += 1
        else:
            current_app.logger.error(f"设备 {device_id} 截图上传失败")

        # 等待下一个截图周期
        elapsed = time.time() - start_time
        sleep_time = max(0, interval - elapsed)
        time.sleep(sleep_time)

    cap.release()
    rtsp_tasks[device_id]['running'] = False


@camera_bp.route('/device/<int:device_id>/rtsp/start', methods=['POST'])
def start_rtsp_capture(device_id):
    """启动RTSP截图 - 直接上传到MinIO"""
    try:
        device = Device.query.get_or_404(device_id)
        data = request.get_json()

        rtsp_url = data.get('rtsp_url', device.source)
        interval = data.get('interval', 5)
        max_count = data.get('max_count', 100)

        if not rtsp_url:
            return jsonify({'success': False, 'message': 'RTSP地址不能为空'})

        # 检查任务是否已在运行
        if device_id in rtsp_tasks and rtsp_tasks[device_id]['running']:
            return jsonify({'success': False, 'message': '该设备的截图任务已在运行'})

        # 初始化任务状态
        rtsp_tasks[device_id] = {
            'running': True,
            'thread': None
        }

        # 启动RTSP截图线程
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


# ------------------------- ONVIF功能 -------------------------
def onvif_capture_task(device_id, snapshot_uri, username, password, interval, max_count):
    """ONVIF截图线程任务 - 直接上传到MinIO"""
    count = 0
    auth = (username, password) if username and password else None
    image_format = current_app.config.get('SCREENSHOT_FORMAT', 'jpg')

    while onvif_tasks.get(device_id, {}).get('running', False) and count < max_count:
        start_time = time.time()

        try:
            # 获取快照
            response = requests.get(snapshot_uri, auth=auth, timeout=10)
            if response.status_code == 200:
                # 将图像数据转换为OpenCV格式
                image_bytes = io.BytesIO(response.content)
                image_bytes.seek(0)
                image_np = cv2.imdecode(np.frombuffer(image_bytes.read(), np.uint8), cv2.IMREAD_COLOR)

                # 上传截图到MinIO
                image_url = upload_screenshot_to_minio(device_id, image_np, image_format)
                if image_url:
                    current_app.logger.info(f"设备 {device_id} ONVIF截图已上传: {image_url}")
                    count += 1
                else:
                    current_app.logger.error(f"设备 {device_id} ONVIF截图上传失败")
            else:
                current_app.logger.error(f"ONVIF快照请求失败: {response.status_code}")
        except Exception as e:
            current_app.logger.error(f"ONVIF截图失败: {str(e)}")

        # 等待下一个截图周期
        elapsed = time.time() - start_time
        sleep_time = max(0, interval - elapsed)
        time.sleep(sleep_time)

    onvif_tasks[device_id]['running'] = False


@camera_bp.route('/device/<int:device_id>/onvif/start', methods=['POST'])
def start_onvif_capture(device_id):
    """启动ONVIF截图 - 直接上传到MinIO"""
    try:
        device = Device.query.get_or_404(device_id)
        data = request.get_json()

        interval = data.get('interval', 10)
        max_count = data.get('max_count', 100)

        # 获取快照URI
        snapshot_uri = get_snapshot_uri(
            device.ip, device.port,
            device.username, device.password
        )

        if not snapshot_uri:
            return jsonify({'success': False, 'message': '无法获取ONVIF快照URI'})

        # 检查任务是否已在运行
        if device_id in onvif_tasks and onvif_tasks[device_id]['running']:
            return jsonify({'success': False, 'message': '该设备的ONVIF截图任务已在运行'})

        # 初始化任务状态
        onvif_tasks[device_id] = {
            'running': True,
            'thread': None
        }

        # 启动ONVIF截图线程
        thread = threading.Thread(
            target=onvif_capture_task,
            args=(device_id, snapshot_uri, device.username,
                  device.password, interval, max_count)
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

@camera_bp.route('/device/onvif/<device_ip>/<int:device_port>/profiles', methods=['POST'])
def get_onvif_profiles(device_ip, device_port):
    """获取ONVIF设备的配置文件列表"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'})

        # 创建ONVIF相机对象
        cam = ONVIFCamera(device_ip, device_port, username, password)

        # 创建媒体服务
        media_service = cam.create_media_service()

        # 获取配置文件
        profiles = media_service.GetProfiles()

        # 格式化响应
        profile_list = []
        for profile in profiles:
            profile_list.append({
                'token': profile.token,
                'name': profile.Name,
                'video_source': profile.VideoSourceConfiguration.SourceToken
            })

        return jsonify({
            'success': True,
            'profiles': profile_list
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取配置文件失败: {str(e)}'})