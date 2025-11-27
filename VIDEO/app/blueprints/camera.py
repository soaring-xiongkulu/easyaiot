"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import datetime
import io
import logging
import subprocess
import threading
import time
import uuid
from operator import or_
from typing import Optional

import cv2
import numpy as np
import requests
from flask import Blueprint, current_app, request, jsonify
from minio import Minio
from minio.error import S3Error

from app.services.camera_service import *
from app.services.camera_service import (
    register_camera, register_camera_by_onvif, get_camera_info, update_camera, delete_camera,
    search_camera,
    get_snapshot_uri, refresh_camera, _to_dict
)
import app.services.camera_service as camera_service
from models import Device, db, Image, DeviceDirectory, DetectionRegion

camera_bp = Blueprint('camera', __name__)
logger = logging.getLogger(__name__)

# 全局变量管理截图任务状态
rtsp_tasks = {}
onvif_tasks = {}

# 全局进程管理
ffmpeg_processes = {}
ffmpeg_lock = threading.Lock()


class FFmpegDaemon:
    """FFmpeg进程守护线程（支持自动重启）"""

    def __init__(self, device_id):
        self.device_id = device_id
        self.process = None
        self._running = True
        self._restart_flag = False
        self.start_daemon()

    def start_daemon(self):
        device = Device.query.get(self.device_id)

        def daemon_task():
            while self._running:
                # 关键修复：移除路径引号
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-rtsp_transport', 'tcp',
                    '-i', device.source,  # 直接使用路径
                    '-an',  # 禁用音频
                    '-c:v', 'libx264',
                    '-b:v', '512k',
                    '-f', 'flv',
                    f'{device.rtmp_stream}'
                ]

                # 启动进程并捕获错误流
                self.process = subprocess.Popen(
                    ffmpeg_cmd,
                    stderr=subprocess.PIPE,  # 关键：捕获错误日志
                    stdin=subprocess.PIPE,
                    text=False
                )
                logger.debug(f"启动FFmpeg: {' '.join(ffmpeg_cmd)}")

                # 实时监控输出（仅记录错误和警告）
                while self._running:
                    line = self.process.stderr.readline()
                    if not line:
                        break
                    line_str = line.decode().strip()
                    # 只记录错误和警告信息
                    if 'error' in line_str.lower() or 'warning' in line_str.lower() or 'failed' in line_str.lower():
                        logger.warning(f"[FFmpeg:{self.device_id}] {line_str}")

                # 进程结束后处理
                return_code = self.process.wait()
                if return_code != 0:
                    logger.error(f"FFmpeg异常退出，返回码: {return_code}，设备: {self.device_id}")

                # 按需重启
                if not self._running:
                    return
                if self._restart_flag:
                    self._restart_flag = False
                    logger.info(f"设备 {self.device_id} 配置更新，立即重启")
                else:
                    logger.warning(f"设备 {self.device_id} 进程异常，10秒后重启...")
                    time.sleep(10)  # 等待后重启

        threading.Thread(target=daemon_task, daemon=True).start()

    def restart(self):
        self._restart_flag = True
        if self.process:
            self.process.terminate()

    def stop(self):
        self._running = False
        if self.process:
            self.process.terminate()


# ------------------------- 自动启动函数 -------------------------
def auto_start_streaming():
    """应用启动时自动启动需要推流的设备[1](@ref)"""
    try:
        devices = Device.query.filter_by(enable_forward=True).all()
        for device in devices:
            # 如果摄像头地址是 rtmp，则不启动推送
            if device.source and device.source.strip().lower().startswith('rtmp://'):
                logger.info(f"设备 {device.id} 的源地址是 RTMP，跳过推送启动")
                continue
            
            # 如果设备离线，则不启动推送
            if not camera_service._monitor.is_online(device.id):
                logger.info(f"设备 {device.id} 处于离线状态，跳过推送启动")
                continue
            
            with ffmpeg_lock:
                # 跳过已运行的进程
                if device.id in ffmpeg_processes:
                    daemon = ffmpeg_processes[device.id]
                    if daemon._running:
                        logger.debug(f"设备 {device.id} 的流媒体转发已在运行中")
                        continue

                # 创建并启动守护线程
                ffmpeg_processes[device.id] = FFmpegDaemon(device.id)
                logger.debug(f"设备 {device.id} 的流媒体转发已自动启动")

    except Exception as e:
        logger.error(f"自动启动流媒体转发失败: {str(e)}", exc_info=True)


# ------------------------- 接口实现 -------------------------
@camera_bp.route('/device/<string:device_id>/stream/start', methods=['POST'])
def start_ffmpeg_stream(device_id):
    try:
        device = Device.query.get_or_404(device_id)
        
        # 如果摄像头地址是 rtmp，则不启动推送
        if device.source and device.source.strip().lower().startswith('rtmp://'):
            return jsonify({
                'code': 400,
                'msg': '摄像头源地址是 RTMP，不支持推送功能'
            }), 400
        
        # 如果设备离线，则不启动推送
        if not camera_service._monitor.is_online(device_id):
            return jsonify({
                'code': 400,
                'msg': '设备处于离线状态，无法启动推送'
            }), 400
        
        with ffmpeg_lock:
            if device_id in ffmpeg_processes:
                daemon = ffmpeg_processes[device_id]
                if daemon._running:
                    return jsonify({'code': 400, 'msg': '转码任务已在运行'}), 400
                daemon.stop()

            # 启动新进程并更新数据库
            ffmpeg_processes[device_id] = FFmpegDaemon(device_id)
            device.enable_forward = True
            db.session.commit()

        return jsonify({
            'code': 0,
            'msg': '流媒体转发已启动',
            'data': {'rtmp_url': device.rtmp_stream}
        })
    except Exception as e:
        logger.error(f"启动失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'启动失败: {str(e)}'}), 500


@camera_bp.route('/device/<string:device_id>/stream/stop', methods=['POST'])
def stop_ffmpeg_stream(device_id):
    try:
        with ffmpeg_lock:
            if device_id in ffmpeg_processes:
                ffmpeg_processes[device_id].stop()
                del ffmpeg_processes[device_id]

            device = Device.query.get(device_id)
            if device:
                device.enable_forward = False
                db.session.commit()

        return jsonify({'code': 0, 'msg': '转码已停止'})
    except Exception as e:
        logger.error(f"停止失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'停止失败: {str(e)}'}), 500


@camera_bp.route('/device/<string:device_id>/stream/status', methods=['GET'])
def get_stream_status(device_id):
    """获取FFmpeg转发状态"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'code': 404, 'msg': f'设备 {device_id} 不存在'}), 404

        status = 'stopped'
        pid = None
        start_time = None
        rtmp_url = device.rtmp_stream if device.rtmp_stream else None

        with ffmpeg_lock:
            if device_id in ffmpeg_processes:
                daemon = ffmpeg_processes[device_id]
                if daemon._running and daemon.process:
                    # 检查进程是否还在运行
                    if daemon.process.poll() is None:  # None表示进程仍在运行
                        status = 'running'
                        pid = daemon.process.pid
                    else:
                        # 进程已退出，但daemon可能还在运行（等待重启）
                        status = 'stopped'
                else:
                    status = 'stopped'
            else:
                # 没有在ffmpeg_processes中，但检查数据库中的enable_forward状态
                if device.enable_forward:
                    # 数据库标记为启用，但进程不存在，可能是异常退出
                    status = 'stopped'
                else:
                    status = 'stopped'

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'status': status,
                'rtmp_url': rtmp_url,
                'enable_forward': device.enable_forward,
                'pid': pid,
                'start_time': start_time
            }
        })
    except Exception as e:
        logger.error(f"获取流状态失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'获取流状态失败: {str(e)}'}), 500


# ------------------------- 设备管理接口 -------------------------
@camera_bp.route('/list', methods=['GET'])
def list_devices():
    """查询设备列表（支持分页和搜索）"""
    try:
        # 获取请求参数
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 10))
        search = request.args.get('search', '').strip()

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

        # 按修改时间降序排序（新添加的设备排在前面）
        query = query.order_by(Device.updated_at.desc())

        # 执行分页查询
        pagination = query.paginate(
            page=page_no,
            per_page=page_size,
            error_out=False
        )

        device_list = [_to_dict(device) for device in pagination.items]

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': device_list,
            'total': pagination.total
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
    except ValueError as e:
        logger.error(f'获取设备详情失败: {str(e)}')
        return jsonify({'code': 404, 'msg': f'设备 {device_id} 不存在'}), 404
    except Exception as e:
        logger.error(f'获取设备详情失败: {str(e)}')
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500


@camera_bp.route('/register/device', methods=['POST'])
def register_device():
    """注册新设备"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        # 对于自定义设备，如果manufacturer或model为空，使用默认值
        camera_type = data.get('cameraType', '')
        if camera_type == 'custom':
            manufacturer = data.get('manufacturer', '').strip() if data.get('manufacturer') else ''
            model = data.get('model', '').strip() if data.get('model') else ''
            if not manufacturer:
                manufacturer = 'EasyAIoT'
                data['manufacturer'] = manufacturer
            if not model:
                model = 'Camera-EasyAIoT'
                data['model'] = model
        
        device_id = register_camera(data)
        return jsonify({
            'code': 0,
            'msg': '设备注册成功',
            'data': {'id': device_id}
        })
    except ValueError as e:
        logger.error(f'注册新设备失败: {str(e)}')
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except RuntimeError as e:
        logger.error(f'注册新设备失败: {str(e)}')
        return jsonify({'code': 500, 'msg': str(e)}), 500


@camera_bp.route('/register/device/onvif', methods=['POST'])
def register_device_by_onvif():
    """通过ONVIF搜索并自动注册摄像头"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        ip = data.get('ip', '').strip()
        port = data.get('port', 80)
        password = data.get('password', '').strip()
        
        if not ip:
            return jsonify({'code': 400, 'msg': '摄像头IP地址不能为空'}), 400
        if not password:
            return jsonify({'code': 400, 'msg': '摄像头密码不能为空'}), 400
        
        try:
            port = int(port)
        except (ValueError, TypeError):
            return jsonify({'code': 400, 'msg': '摄像头端口必须是数字'}), 400
        
        device_id = register_camera_by_onvif(ip, port, password)
        return jsonify({
            'code': 0,
            'msg': '设备注册成功',
            'data': {'id': device_id}
        })
    except ValueError as e:
        logger.error(f'ONVIF注册设备失败: {str(e)}')
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except RuntimeError as e:
        logger.error(f'ONVIF注册设备失败: {str(e)}')
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'ONVIF注册设备失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'设备注册失败: {str(e)}'}), 500


@camera_bp.route('/device/<string:device_id>', methods=['PUT'])
def update_device(device_id):
    """更新设备信息"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        # 如果更新manufacturer或model字段为空，使用默认值
        if 'manufacturer' in data:
            manufacturer = data.get('manufacturer', '').strip() if data.get('manufacturer') else ''
            if not manufacturer:
                data['manufacturer'] = 'EasyAIoT'
        if 'model' in data:
            model = data.get('model', '').strip() if data.get('model') else ''
            if not model:
                data['model'] = 'Camera-EasyAIoT'
        
        update_camera(device_id, data)
        return jsonify({
            'code': 0,
            'msg': '设备信息更新成功'
        })
    except ValueError as e:
        logger.error(f'更新设备信息失败: {str(e)}')
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except RuntimeError as e:
        logger.error(f'更新设备信息失败: {str(e)}')
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'更新设备信息失败（未知错误）: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'更新设备信息失败: {str(e)}'}), 500


@camera_bp.route('/device/<string:device_id>', methods=['DELETE'])
def delete_device(device_id):
    """删除设备"""
    try:
        # 先停止可能的流媒体转发
        if device_id in ffmpeg_processes and ffmpeg_processes[device_id]['process'] is not None:
            process = ffmpeg_processes[device_id]['process']
            if process.poll() is None:  # 进程仍在运行
                stop_ffmpeg_stream(device_id)

        delete_camera(device_id)
        return jsonify({
            'code': 0,
            'msg': '设备删除成功'
        })
    except ValueError as e:
        logger.error(f'删除设备失败: {str(e)}')
        return jsonify({'code': 404, 'msg': str(e)}), 404
    except RuntimeError as e:
        logger.error(f'删除设备失败: {str(e)}')
        return jsonify({'code': 500, 'msg': str(e)}), 500


# ------------------------- PTZ控制接口 -------------------------
@camera_bp.route('/device/<device_id>/ptz', methods=['POST'])
def control_ptz(device_id: str):
    """
    处理PTZ控制请求
    Args:
        device_id: 设备标识符
    Request Body:
        {x: number, y: number, z: number} - PTZ移动向量
    """
    try:
        # 解析请求数据
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # 提取移动向量
        x = data.get('x', 0.0)
        y = data.get('y', 0.0)
        z = data.get('z', 0.0)

        # 验证参数类型
        if not all(isinstance(v, (int, float)) for v in [x, y, z]):
            return jsonify({'error': 'Invalid parameter types'}), 400

        # 根据device_id获取相机实例
        camera = get_camera_by_id(device_id)  # 您需要实现这个函数

        if not camera:
            return jsonify({'error': 'Camera not found'}), 404

        # 执行PTZ移动
        camera.move((x, y, z))

        return jsonify({'success': True, 'message': 'PTZ command executed'})

    except Exception as e:
        logger.error(f"PTZ control error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


def get_camera_by_id(device_id: str) -> Optional[OnvifCamera]:
    """
    根据设备ID获取OnvifCamera实例
    """
    try:
        # 从数据库获取设备信息
        device = Device.query.get(device_id)
        if not device:
            logger.error(f"设备 {device_id} 不存在")
            return None

        # 检查设备是否有必要的连接信息
        if not all([device.ip, device.port, device.username, device.password]):
            logger.error(f"设备 {device_id} 缺少连接信息")
            return None

        # 创建OnvifCamera实例
        return OnvifCamera(
            ip=device.ip,
            port=device.port,
            username=device.username,
            password=device.password
        )
    except Exception as e:
        logger.error(f"创建相机实例失败: {str(e)}")
        return None


# ------------------------- MinIO上传服务 -------------------------
def get_minio_client():
    """创建并返回Minio客户端"""
    minio_endpoint = current_app.config.get('MINIO_ENDPOINT', 'localhost:9000')
    access_key = current_app.config.get('MINIO_ACCESS_KEY', 'minioadmin')
    secret_key = current_app.config.get('MINIO_SECRET_KEY', 'minioadmin')
    secure = current_app.config.get('MINIO_SECURE', 'false').lower() == 'true'
    return Minio(minio_endpoint, access_key, secret_key, secure=secure)


def upload_screenshot_to_minio(camera_id, image_data, image_format="jpg"):
    """上传摄像头截图到MinIO并存入数据库"""
    try:
        minio_client = get_minio_client()
        bucket_name = "camera-screenshots"

        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            logger.info(f"创建截图存储桶: {bucket_name}")

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # 生成唯一文件名
        unique_filename = f"{uuid.uuid4().hex}.{image_format}"
        object_name = f"{camera_id}/{unique_filename}"

        success, encoded_image = cv2.imencode(f'.{image_format}', image_data)
        if not success:
            raise RuntimeError("图像编码失败")

        # 获取图像尺寸
        height, width = image_data.shape[:2]

        image_bytes = encoded_image.tobytes()
        minio_client.put_object(
            bucket_name,
            object_name,
            io.BytesIO(image_bytes),
            len(image_bytes),
            content_type=f"image/{image_format}"
        )

        # 使用统一的URL格式
        download_url = f"/api/v1/buckets/{bucket_name}/objects/download?prefix={object_name}"

        # 将图片信息存入数据库
        try:
            image_record = Image(
                filename=unique_filename,
                original_filename=f"{camera_id}_{timestamp}.{image_format}",
                path=download_url,
                width=width,
                height=height,
                device_id=camera_id
            )
            db.session.add(image_record)
            db.session.commit()
            logger.info(f"图片信息已存入数据库，ID: {image_record.id}")
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"数据库存储失败: {str(db_error)}")
        logger.info(f"截图上传成功: {bucket_name}/{object_name}")
        return download_url
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
            return jsonify({'code': 400, 'msg': 'RTSP地址不能为空'}), 400

        if device_id in rtsp_tasks and rtsp_tasks[device_id]['running']:
            return jsonify({'code': 400, 'msg': '该设备的截图任务已在运行'}), 400

        rtsp_tasks[device_id] = {'running': True, 'thread': None}
        thread = threading.Thread(
            target=rtsp_capture_task,
            args=(device_id, rtsp_url, interval, max_count)
        )
        thread.daemon = True
        thread.start()
        rtsp_tasks[device_id]['thread'] = thread

        return jsonify({
            'code': 0,
            'msg': 'RTSP截图任务已启动',
            'data': {
                'task_id': thread.ident
            }
        })
    except Exception as e:
        logger.error(f"启动RTSP截图失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'启动RTSP截图失败: {str(e)}'}), 500


@camera_bp.route('/device/<int:device_id>/rtsp/stop', methods=['POST'])
def stop_rtsp_capture(device_id):
    """停止RTSP截图任务"""
    try:
        if device_id in rtsp_tasks:
            rtsp_tasks[device_id]['running'] = False
            if rtsp_tasks[device_id]['thread']:
                rtsp_tasks[device_id]['thread'].join(timeout=5.0)
            return jsonify({'code': 0, 'msg': 'RTSP截图任务已停止'})
        return jsonify({'code': 404, 'msg': '未找到运行的RTSP截图任务'}), 404
    except Exception as e:
        logger.error(f"停止RTSP截图失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'停止RTSP截图失败: {str(e)}'}), 500


@camera_bp.route('/device/<int:device_id>/rtsp/status', methods=['GET'])
def rtsp_status(device_id):
    """获取RTSP截图状态"""
    try:
        status = "stopped"
        if device_id in rtsp_tasks:
            status = "running" if rtsp_tasks[device_id]['running'] else "stopped"
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {'status': status}
        })
    except Exception as e:
        logger.error(f"获取RTSP状态失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'获取RTSP状态失败: {str(e)}'}), 500


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
            return jsonify({'code': 400, 'msg': '无法获取ONVIF快照URI'}), 400

        if device_id in onvif_tasks and onvif_tasks[device_id]['running']:
            return jsonify({'code': 400, 'msg': '该设备的ONVIF截图任务已在运行'}), 400

        onvif_tasks[device_id] = {'running': True, 'thread': None}
        thread = threading.Thread(
            target=onvif_capture_task,
            args=(device_id, snapshot_uri, device.username, device.password, interval, max_count)
        )
        thread.daemon = True
        thread.start()
        onvif_tasks[device_id]['thread'] = thread

        return jsonify({
            'code': 0,
            'msg': 'ONVIF截图任务已启动',
            'data': {
                'task_id': thread.ident
            }
        })
    except Exception as e:
        logger.error(f"启动ONVIF截图失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'启动ONVIF截图失败: {str(e)}'}), 500


@camera_bp.route('/device/<int:device_id>/onvif/stop', methods=['POST'])
def stop_onvif_capture(device_id):
    """停止ONVIF截图"""
    try:
        if device_id in onvif_tasks:
            onvif_tasks[device_id]['running'] = False
            if onvif_tasks[device_id]['thread']:
                onvif_tasks[device_id]['thread'].join(timeout=5.0)
            return jsonify({'code': 0, 'msg': 'ONVIF截图任务已停止'})
        return jsonify({'code': 404, 'msg': '未找到运行的ONVIF截图任务'}), 404
    except Exception as e:
        logger.error(f"停止ONVIF截图失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'停止ONVIF截图失败: {str(e)}'}), 500


@camera_bp.route('/device/<int:device_id>/onvif/status', methods=['GET'])
def onvif_status(device_id):
    """获取ONVIF截图状态"""
    try:
        status = "stopped"
        if device_id in onvif_tasks:
            status = "running" if onvif_tasks[device_id]['running'] else "stopped"
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {'status': status}
        })
    except Exception as e:
        logger.error(f"获取ONVIF截图状态失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'获取ONVIF截图状态失败: {str(e)}'}), 500


# ------------------------- RTSP单帧抓拍接口 -------------------------
@camera_bp.route('/device/<string:device_id>/snapshot', methods=['POST'])
def capture_snapshot(device_id):
    """从RTSP流抓取一帧图片并存入数据库"""
    try:
        device = Device.query.get_or_404(device_id)
        
        if not device.source:
            return jsonify({'code': 400, 'msg': '设备源地址为空'}), 400
        
        # 检查是否是RTMP流（不支持）
        if device.source.strip().lower().startswith('rtmp://'):
            return jsonify({'code': 400, 'msg': 'RTMP流不支持抓拍，请使用RTSP流'}), 400
        
        # 使用OpenCV从RTSP流抓取一帧
        import cv2
        cap = cv2.VideoCapture(device.source)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 减少缓冲区，获取最新帧
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return jsonify({'code': 500, 'msg': '无法从RTSP流读取帧'}), 500
        
        # 上传到MinIO并存入数据库
        image_url = upload_screenshot_to_minio(device_id, frame, 'jpg')
        
        if not image_url:
            return jsonify({'code': 500, 'msg': '图片上传失败'}), 500
        
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
        logger.error(f"抓拍失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'抓拍失败: {str(e)}'}), 500


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


@camera_bp.route('/callback/on_publish', methods=['POST'])
def on_publish_callback():
    try:
        return jsonify({
            'code': 0,
            'msg': None
        })
    except:
        pass


@camera_bp.route('/callback/on_dvr', methods=['POST'])
def on_dvr_callback():
    try:
        return jsonify({
            'code': 0,
            'msg': None
        })
    except:
        pass


# ------------------------- 设备目录管理接口 -------------------------
@camera_bp.route('/directory/list', methods=['GET'])
def list_directories():
    """查询目录列表（树形结构）"""
    try:
        def build_tree(parent_id=None):
            """递归构建目录树"""
            directories = DeviceDirectory.query.filter_by(parent_id=parent_id).order_by(DeviceDirectory.sort_order, DeviceDirectory.id).all()
            result = []
            for directory in directories:
                directory_dict = {
                    'id': directory.id,
                    'name': directory.name,
                    'parent_id': directory.parent_id,
                    'description': directory.description,
                    'sort_order': directory.sort_order,
                    'device_count': Device.query.filter_by(directory_id=directory.id).count(),
                    'created_at': directory.created_at.isoformat() if directory.created_at else None,
                    'updated_at': directory.updated_at.isoformat() if directory.updated_at else None,
                    'children': build_tree(directory.id)
                }
                result.append(directory_dict)
            return result
        
        tree = build_tree()
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': tree
        })
    except Exception as e:
        logger.error(f'查询目录列表失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'查询目录列表失败: {str(e)}'}), 500


@camera_bp.route('/directory', methods=['POST'])
def create_directory():
    """创建目录"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        name = data.get('name', '').strip()
        if not name:
            return jsonify({'code': 400, 'msg': '目录名称不能为空'}), 400
        
        parent_id = data.get('parent_id')
        if parent_id:
            # 验证父目录是否存在
            parent = DeviceDirectory.query.get(parent_id)
            if not parent:
                return jsonify({'code': 400, 'msg': '父目录不存在'}), 400
        
        description = data.get('description', '').strip()
        sort_order = data.get('sort_order', 0)
        
        directory = DeviceDirectory(
            name=name,
            parent_id=parent_id,
            description=description,
            sort_order=sort_order
        )
        db.session.add(directory)
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'msg': '目录创建成功',
            'data': {
                'id': directory.id,
                'name': directory.name,
                'parent_id': directory.parent_id,
                'description': directory.description,
                'sort_order': directory.sort_order
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'创建目录失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'创建目录失败: {str(e)}'}), 500


@camera_bp.route('/directory/<int:directory_id>', methods=['PUT'])
def update_directory(directory_id):
    """更新目录"""
    try:
        directory = DeviceDirectory.query.get_or_404(directory_id)
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        if 'name' in data:
            name = data.get('name', '').strip()
            if not name:
                return jsonify({'code': 400, 'msg': '目录名称不能为空'}), 400
            directory.name = name
        
        if 'parent_id' in data:
            parent_id = data.get('parent_id')
            if parent_id:
                # 验证父目录是否存在
                if parent_id == directory_id:
                    return jsonify({'code': 400, 'msg': '不能将目录设置为自己的子目录'}), 400
                parent = DeviceDirectory.query.get(parent_id)
                if not parent:
                    return jsonify({'code': 400, 'msg': '父目录不存在'}), 400
                # 检查是否会形成循环引用
                def check_circular(parent_id, current_id):
                    if parent_id == current_id:
                        return True
                    parent_dir = DeviceDirectory.query.get(parent_id)
                    if parent_dir and parent_dir.parent_id:
                        return check_circular(parent_dir.parent_id, current_id)
                    return False
                if check_circular(parent_id, directory_id):
                    return jsonify({'code': 400, 'msg': '不能将目录移动到其子目录下'}), 400
            directory.parent_id = parent_id
        
        if 'description' in data:
            directory.description = data.get('description', '').strip()
        
        if 'sort_order' in data:
            directory.sort_order = data.get('sort_order', 0)
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'msg': '目录更新成功',
            'data': {
                'id': directory.id,
                'name': directory.name,
                'parent_id': directory.parent_id,
                'description': directory.description,
                'sort_order': directory.sort_order
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新目录失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'更新目录失败: {str(e)}'}), 500


@camera_bp.route('/directory/<int:directory_id>', methods=['DELETE'])
def delete_directory(directory_id):
    """删除目录"""
    try:
        directory = DeviceDirectory.query.get_or_404(directory_id)
        
        # 检查是否有子目录
        children_count = DeviceDirectory.query.filter_by(parent_id=directory_id).count()
        if children_count > 0:
            return jsonify({
                'code': 400, 
                'msg': f'不能删除当前目录，存在 {children_count} 个下级目录。请先删除所有下级目录后，才可以删除当前目录'
            }), 400
        
        # 检查是否有设备
        device_count = Device.query.filter_by(directory_id=directory_id).count()
        if device_count > 0:
            return jsonify({'code': 400, 'msg': f'该目录下存在 {device_count} 个设备，请先移除设备后再删除目录'}), 400
        
        db.session.delete(directory)
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'msg': '目录删除成功'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'删除目录失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'删除目录失败: {str(e)}'}), 500


@camera_bp.route('/directory/<int:directory_id>/devices', methods=['GET'])
def list_directory_devices(directory_id):
    """查询目录下的设备列表"""
    try:
        directory = DeviceDirectory.query.get_or_404(directory_id)
        
        # 获取请求参数
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 10))
        search = request.args.get('search', '').strip()
        
        # 参数验证
        if page_no < 1 or page_size < 1:
            return jsonify({'code': 400, 'msg': '参数错误：pageNo和pageSize必须为正整数'}), 400
        
        # 构建基础查询
        query = Device.query.filter_by(directory_id=directory_id)
        
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
        
        # 按修改时间降序排序
        query = query.order_by(Device.updated_at.desc())
        
        # 执行分页查询
        pagination = query.paginate(
            page=page_no,
            per_page=page_size,
            error_out=False
        )
        
        device_list = [_to_dict(device) for device in pagination.items]
        
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': device_list,
            'total': pagination.total
        })
    except ValueError:
        return jsonify({'code': 400, 'msg': '参数类型错误：pageNo和pageSize需为整数'}), 400
    except Exception as e:
        logger.error(f'查询目录设备列表失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500


@camera_bp.route('/device/<string:device_id>/directory', methods=['PUT'])
def move_device_to_directory(device_id):
    """移动设备到目录"""
    try:
        device = Device.query.get_or_404(device_id)
        data = request.get_json()
        
        directory_id = data.get('directory_id')
        if directory_id is not None:
            # 验证目录是否存在
            if directory_id != 0:  # 0表示移动到根目录（无目录）
                directory = DeviceDirectory.query.get(directory_id)
                if not directory:
                    return jsonify({'code': 400, 'msg': '目录不存在'}), 400
                device.directory_id = directory_id
            else:
                device.directory_id = None
        else:
            return jsonify({'code': 400, 'msg': 'directory_id参数不能为空'}), 400
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'msg': '设备移动成功',
            'data': {
                'device_id': device.id,
                'directory_id': device.directory_id
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'移动设备到目录失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'移动设备到目录失败: {str(e)}'}), 500


@camera_bp.route('/directory/<int:directory_id>', methods=['GET'])
def get_directory_info(directory_id):
    """获取目录详情"""
    try:
        directory = DeviceDirectory.query.get_or_404(directory_id)
        
        # 获取目录下的设备数量
        device_count = Device.query.filter_by(directory_id=directory_id).count()
        
        # 获取子目录数量
        children_count = DeviceDirectory.query.filter_by(parent_id=directory_id).count()
        
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'id': directory.id,
                'name': directory.name,
                'parent_id': directory.parent_id,
                'description': directory.description,
                'sort_order': directory.sort_order,
                'device_count': device_count,
                'children_count': children_count,
                'created_at': directory.created_at.isoformat() if directory.created_at else None,
                'updated_at': directory.updated_at.isoformat() if directory.updated_at else None
            }
        })
    except Exception as e:
        logger.error(f'获取目录详情失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500
