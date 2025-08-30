import datetime
import io
import logging
import threading
import time
import uuid
import subprocess
import psutil
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
    get_snapshot_uri, refresh_camera, _to_dict
)
from models import Device, db, Image

# 创建蓝图
camera_bp = Blueprint('camera', __name__)
logger = logging.getLogger(__name__)

# 全局变量管理截图任务状态
rtsp_tasks = {}
onvif_tasks = {}
# 全局变量管理FFmpeg转码进程
ffmpeg_processes = {}

# 应用启动时自动启动需要推流的设备
def auto_start_streaming():
    """应用启动时自动启动需要推流的设备"""
    try:
        devices = Device.query.filter_by(enable_forward=True).all()
        for device in devices:
            try:
                # 检查设备是否已经有运行的进程
                if device.id in ffmpeg_processes and ffmpeg_processes[device.id]['process'] is not None:
                    process = ffmpeg_processes[device.id]['process']
                    if process.poll() is None:  # 进程仍在运行
                        logger.info(f"设备 {device.id} 的流媒体转发已在运行中")
                        continue

                # 启动FFmpeg进程
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-rtsp_transport', 'tcp',  # 强制TCP传输避免UDP丢包问题
                    '-i', device.source,  # RTSP输入源地址
                    '-an',  # 禁用音频流（若无需音频）
                    '-c:v', 'libx264',  # H.264视频编码
                    '-preset', 'ultrafast',  # 最快编码速度（降低延迟）
                    '-tune', 'zerolatency',  # 零延迟模式（实时推流关键）
                    '-b:v', '512k',  # 目标码率512kbps
                    '-maxrate', '512k',  # 峰值码率限制（防网络波动）
                    '-bufsize', '1024k',  # 码率缓冲区（建议为码率2倍）
                    '-g', '50',  # 关键帧间隔（2秒@25fps）
                    '-f', 'flv',  # 输出FLV格式
                    device.rtmp_stream  # RTMP推流地址
                ]

                logger.info(f"自动启动FFmpeg转码: {' '.join(ffmpeg_cmd)}")

                process = subprocess.Popen(
                    ffmpeg_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE
                )

                # 存储进程信息
                ffmpeg_processes[device.id] = {
                    'process': process,
                    'rtmp_url': device.rtmp_stream,
                    'start_time': datetime.datetime.now()
                }

                # 启动线程监控进程输出
                threading.Thread(
                    target=monitor_ffmpeg_output,
                    args=(device.id, process),
                    daemon=True
                ).start()

                logger.info(f"设备 {device.id} 的流媒体转发已自动启动")

            except Exception as e:
                logger.error(f"自动启动设备 {device.id} 的流媒体转发失败: {str(e)}", exc_info=True)

    except Exception as e:
        logger.error(f"自动启动流媒体转发失败: {str(e)}", exc_info=True)


# 在应用启动时调用此函数
# 注意：这个调用应该放在应用启动的地方，例如在create_app函数中

# ------------------------- FFmpeg转发接口 -------------------------
@camera_bp.route('/device/<string:device_id>/stream/start', methods=['POST'])
def start_ffmpeg_stream(device_id):
    """启动FFmpeg转发RTSP流到RTMP服务器"""
    try:
        device = Device.query.get_or_404(device_id)

        # 检查是否已有转码进程在运行
        if device_id in ffmpeg_processes and ffmpeg_processes[device_id]['process'] is not None:
            process = ffmpeg_processes[device_id]['process']
            if process.poll() is None:  # 进程仍在运行
                return jsonify({
                    'code': 400,
                    'msg': '该设备的流媒体转发已在运行中'
                }), 400

        # 构建FFmpeg命令
        ffmpeg_cmd = [
            'ffmpeg',
            '-rtsp_transport', 'tcp',  # 强制TCP传输避免UDP丢包问题
            '-i', device.source,  # RTSP输入源地址
            '-an',  # 禁用音频流（若无需音频）
            '-c:v', 'libx264',  # H.264视频编码
            '-preset', 'ultrafast',  # 最快编码速度（降低延迟）
            '-tune', 'zerolatency',  # 零延迟模式（实时推流关键）
            '-b:v', '512k',  # 目标码率512kbps
            '-maxrate', '512k',  # 峰值码率限制（防网络波动）
            '-bufsize', '1024k',  # 码率缓冲区（建议为码率2倍）
            '-g', '50',  # 关键帧间隔（2秒@25fps）
            '-f', 'flv',  # 输出FLV格式
            device.rtmp_stream  # RTMP推流地址
        ]

        logger.info(f"启动FFmpeg转码: {' '.join(ffmpeg_cmd)}")
        # 启动FFmpeg进程
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )

        # 存储进程信息
        ffmpeg_processes[device_id] = {
            'process': process,
            'rtmp_url': device.rtmp_stream,
            'start_time': datetime.datetime.now()
        }

        # 更新数据库中的enable_forward状态
        device.enable_forward = True
        db.session.commit()

        # 启动线程监控进程输出
        threading.Thread(
            target=monitor_ffmpeg_output,
            args=(device_id, process),
            daemon=True
        ).start()

        return jsonify({
            'code': 0,
            'msg': '流媒体转发已启动',
            'data': {
                'rtmp_url': device.rtmp_stream,
                'process_id': process.pid
            }
        })

    except Exception as e:
        logger.error(f"启动FFmpeg转码失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 500,
            'msg': f'启动流媒体转发失败: {str(e)}'
        }), 500


def monitor_ffmpeg_output(device_id, process):
    """监控FFmpeg进程输出"""
    try:
        # 读取stderr输出
        for line in iter(process.stderr.readline, b''):
            if line:
                logger.debug(f"FFmpeg[{device_id}]: {line.decode().strip()}")

        # 等待进程结束
        process.wait()
        return_code = process.returncode

        if return_code == 0:
            logger.info(f"FFmpeg进程正常结束，设备ID: {device_id}")
        else:
            logger.error(f"FFmpeg进程异常结束，返回码: {return_code}，设备ID: {device_id}")

        # 清理进程记录并更新数据库状态
        if device_id in ffmpeg_processes:
            ffmpeg_processes[device_id]['process'] = None

        # 更新数据库中的enable_forward状态
        try:
            device = Device.query.get(device_id)
            if device:
                device.enable_forward = False
                db.session.commit()
                logger.info(f"已更新设备 {device_id} 的enable_forward状态为False")
        except Exception as e:
            logger.error(f"更新设备 {device_id} 的enable_forward状态失败: {str(e)}")

    except Exception as e:
        logger.error(f"监控FFmpeg输出失败: {str(e)}", exc_info=True)


@camera_bp.route('/device/<string:device_id>/stream/stop', methods=['POST'])
def stop_ffmpeg_stream(device_id):
    """停止FFmpeg转发进程"""
    try:
        if device_id not in ffmpeg_processes or ffmpeg_processes[device_id]['process'] is None:
            return jsonify({
                'code': 404,
                'msg': '未找到运行的流媒体转发进程'
            }), 404

        process = ffmpeg_processes[device_id]['process']

        # 终止进程及其所有子进程
        if process.poll() is None:  # 进程仍在运行
            parent = psutil.Process(process.pid)
            children = parent.children(recursive=True)

            # 先终止所有子进程
            for child in children:
                child.terminate()

            # 等待子进程终止
            gone, still_alive = psutil.wait_procs(children, timeout=5)

            # 如果有子进程仍然存活，强制杀死
            for child in still_alive:
                child.kill()

            # 终止父进程
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

        # 清理进程记录
        ffmpeg_processes[device_id]['process'] = None

        # 更新数据库中的enable_forward状态
        device = Device.query.get(device_id)
        if device:
            device.enable_forward = False
            db.session.commit()
            logger.info(f"已更新设备 {device_id} 的enable_forward状态为False")

        return jsonify({
            'code': 0,
            'msg': '流媒体转发已停止'
        })

    except Exception as e:
        logger.error(f"停止FFmpeg转码失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 500,
            'msg': f'停止流媒体转发失败: {str(e)}'
        }), 500


@camera_bp.route('/device/<string:device_id>/stream/status', methods=['GET'])
def get_ffmpeg_stream_status(device_id):
    """获取FFmpeg转发状态"""
    try:
        # 首先检查数据库中的enable_forward状态
        device = Device.query.get(device_id)
        if not device:
            return jsonify({
                'code': 404,
                'msg': '设备不存在'
            }), 404

        db_status = device.enable_forward

        # 检查进程状态
        process_status = "stopped"
        if device_id in ffmpeg_processes and ffmpeg_processes[device_id]['process'] is not None:
            process = ffmpeg_processes[device_id]['process']
            process_status = "running" if process.poll() is None else "stopped"

            # 如果数据库状态和进程状态不一致，更新数据库状态
            if db_status != (process_status == "running"):
                device.enable_forward = (process_status == "running")
                db.session.commit()
                logger.info(f"已同步设备 {device_id} 的enable_forward状态为{process_status == 'running'}")

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'status': process_status,
                'rtmp_url': device.rtmp_stream if process_status == "running" else None,
                'enable_forward': device.enable_forward,
                'pid': ffmpeg_processes[device_id]['process'].pid if device_id in ffmpeg_processes and
                                                                     ffmpeg_processes[device_id][
                                                                         'process'] is not None else None,
                'start_time': ffmpeg_processes[device_id]['start_time'].isoformat() if device_id in ffmpeg_processes and
                                                                                       ffmpeg_processes[device_id][
                                                                                           'process'] is not None else None
            }
        })

    except Exception as e:
        logger.error(f"获取FFmpeg转码状态失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 500,
            'msg': f'获取流媒体转发状态失败: {str(e)}'
        }), 500


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
        logger.error(f'更新设备信息失败: {str(e)}')
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except RuntimeError as e:
        logger.error(f'更新设备信息失败: {str(e)}')
        return jsonify({'code': 500, 'msg': str(e)}), 500


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
        logger.error(f'控制摄像头PTZ失败: {str(e)}')
        return jsonify({'code': 404, 'msg': str(e)}), 404
    except RuntimeError as e:
        logger.error(f'控制摄像头PTZ失败: {str(e)}')
        return jsonify({'code': 500, 'msg': str(e)}), 500


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