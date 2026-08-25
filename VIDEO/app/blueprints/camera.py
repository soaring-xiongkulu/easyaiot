"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import base64
import datetime
import hashlib
import io
import logging
import os
import re
import subprocess
import threading
import time
import uuid
from datetime import timezone, timedelta
from operator import or_
from typing import Optional

import cv2
import numpy as np
import requests
from flask import Blueprint, current_app, request, jsonify
from minio import Minio
from minio.error import S3Error
from urllib.parse import quote, urlparse, parse_qs, urlencode, urlunparse

from app.services.camera_service import *
from app.services.camera_service import (
    register_camera, register_camera_by_onvif, get_camera_info, update_camera, delete_camera,
    batch_delete_cameras,
    search_camera,
    get_snapshot_uri, refresh_camera, _to_dict
)
import app.services.camera_service as camera_service
from app.utils.ffmpeg_compat import (
    ffmpeg_rtsp_open_timeout_flag as _ffmpeg_rtsp_open_timeout_flag,
    ffmpeg_rtsp_timeout_args as _ffmpeg_rtsp_timeout_args,
    ffmpeg_supports_rw_timeout as _ffmpeg_supports_rw_timeout,
)
from app.utils.ffmpeg_process_registry import stop_registered_process
from app.utils.flighthub_source import (
    build_register_info as build_flighthub_register_info,
    flighthub_env,
    get_flighthub_public_config,
    model_for_device_type,
    resolve_camera_index,
    resolve_device_type_from_record,
    start_flighthub_live,
)
from app.utils.rtc_source import (
    build_rtc_stream_url,
    get_rtc_public_config,
    list_rtc_platforms,
    register_rtc_live,
    cleanup_rtc_stream_for_device,
    is_rtc_device,
)
from app.utils.gb28181_source import resolve_gb28181_source
from app.utils.node_client import resolve_java_backend_url
from models import Device, db, Image, DeviceDirectory, DetectionRegion, StreamForwardTask, AlgorithmTask
from sqlalchemy import and_

camera_bp = Blueprint('camera', __name__)
logger = logging.getLogger(__name__)

# 受保护的流路径前缀（SRS http-flv: /ai /live；ZLMediaKit ws-flv: /rtp）
_STREAM_PATH_RE = re.compile(r'^/(ai|live|rtp)/')
_AUTH_CHECK_PATH = '/admin-api/system/auth/get-permission-info'


def _resolve_auth_check_url() -> str:
    """登录校验地址：优先 AUTH_CHECK_URL，否则跟随 JAVA_BACKEND_URL / GATEWAY_URL（mini 为 48099）。"""
    explicit = (os.environ.get('AUTH_CHECK_URL') or '').strip()
    if explicit:
        return explicit
    base = resolve_java_backend_url().rstrip('/')
    return f'{base}{_AUTH_CHECK_PATH}'


def _check_login(req) -> bool:
    """用请求里的 JWT 校验登录态：HTTP 200 且业务 code==0 才算有效。

    nginx 把 /dev-api/video/ 直连 VIDEO 绕过了网关，故签发接口必须自校验登录。
    edge 规格下优先本地校验 VIDEO 签发的 token，避免再绕一圈 HTTP。
    """
    auth = (req.headers.get('Authorization') or req.headers.get('X-Authorization') or '').strip()
    if not auth:
        return False
    try:
        from app.auth.auth_api import is_video_auth_enabled
        from app.auth.token_service import verify_access_token
        if is_video_auth_enabled() and verify_access_token(auth):
            return True
    except Exception as e:
        logger.debug(f'本地 VIDEO token 校验跳过: {e}')
    try:
        r = requests.get(
            _resolve_auth_check_url(),
            headers={
                'Authorization': auth,
                'tenant-id': req.headers.get('tenant-id', '') or req.headers.get('Tenant-Id', ''),
            },
            timeout=5,
        )
        if r.status_code != 200:
            return False
        body = r.json()
        return isinstance(body, dict) and body.get('code') == 0
    except Exception as e:
        logger.warning(f'流票据登录校验失败: {e}')
        return False


@camera_bp.route('/stream/ticket/sign', methods=['POST'])
def sign_stream_ticket():
    """为流地址签发短期 secure_link 票据（需登录）。

    请求: { "path": "/rtp/xxx.live.flv", "ttl": 90 }
    返回: { "code": 0, "data": { "e": <过期unix秒>, "st": <url-safe base64 md5> } }
    未登录/过期: HTTP 401（前端 axios 据此跳登录）。

    签名公式必须与 nginx `secure_link_md5 "$arg_e$uri <secret>"` 逐字符一致：
    md5( f"{e}{path} {secret}" ) -> url-safe base64 -> 去掉 '=' 填充。
    """
    if not _check_login(request):
        return jsonify({'code': 401, 'msg': 'unauthorized'}), 401
    data = request.get_json(silent=True) or {}
    path = (data.get('path') or '').strip()
    if not _STREAM_PATH_RE.match(path):
        return jsonify({'code': 400, 'msg': 'invalid stream path'}), 400
    secret = os.environ.get('STREAM_TICKET_SECRET', '')
    if not secret:
        logger.error('STREAM_TICKET_SECRET 未配置，无法签发流票据')
        return jsonify({'code': 500, 'msg': 'stream ticket secret not configured'}), 500
    try:
        ttl = int(data.get('ttl') or 90)
    except (TypeError, ValueError):
        ttl = 90
    ttl = max(15, min(ttl, 600))
    e = int(time.time()) + ttl
    raw = hashlib.md5(f"{e}{path} {secret}".encode('utf-8')).digest()
    st = base64.urlsafe_b64encode(raw).decode('ascii').rstrip('=')
    return jsonify({'code': 0, 'msg': 'success', 'data': {'e': e, 'st': st}})


def _strip_rtsp_transport_query(source_url: str) -> tuple[str, Optional[str]]:
    """
    从 RTSP URL 查询参数中读取传输方式并剔除该参数，避免将自定义参数传给 NVR/摄像头。
    支持: easyaiot_rtsp_transport / rtsp_transport / iot_rtsp_transport = tcp|udp
    """
    try:
        p = urlparse(source_url)
        if p.scheme.lower() != 'rtsp' or not p.query:
            return source_url, None
        q = parse_qs(p.query, keep_blank_values=True)
        transport = None
        for key in ("easyaiot_rtsp_transport", "rtsp_transport", "iot_rtsp_transport"):
            if key in q and q[key]:
                transport = (q[key][0] or "").strip().lower()
                del q[key]
                break
        if transport is None:
            return source_url, None
        new_query = urlencode(q, doseq=True)
        return urlunparse(p._replace(query=new_query)), transport
    except Exception:
        return source_url, None


# 全局变量管理截图任务状态
rtsp_tasks = {}
onvif_tasks = {}

# 全局进程管理
ffmpeg_processes = {}
ffmpeg_lock = threading.Lock()

# HEVC 起播/丢包时解码器常见告警，推流通常仍可继续，不必刷屏
_FFMPEG_DECODER_NOISE_PATTERNS = (
    "error constructing the frame rps",
    "could not find ref with poc",
    "skipping invalid undecodable nalu",
    "missing reference picture",
    "illegal short term buffer state",
    "no frame!",
    "duplicate poc",
    "discarding one",
)


def _ffmpeg_stderr_should_log(line: str) -> bool:
    """过滤 FFmpeg stderr 中已知的无害解码告警。"""
    lower = line.lower()
    if not any(k in lower for k in ("error", "warning", "failed")):
        return False
    if any(p in lower for p in _FFMPEG_DECODER_NOISE_PATTERNS):
        return False
    return True


class FFmpegDaemon:
    """FFmpeg进程守护线程（支持自动重启）"""

    def __init__(self, device_id):
        self.device_id = device_id
        self.process = None
        self._running = True
        self._restart_flag = False
        self._app = current_app._get_current_object()
        self.start_daemon()

    def _forward_enabled_in_db(self) -> bool:
        with self._app.app_context():
            device = Device.query.get(self.device_id)
            return bool(device and device.enable_forward)

    def start_daemon(self):
        def daemon_task():
            while self._running:
                if not self._forward_enabled_in_db():
                    logger.info(f"设备 {self.device_id} 已关闭观看转发(enable_forward=False)，守护线程退出")
                    return

                with self._app.app_context():
                    device = Device.query.get(self.device_id)
                if not device:
                    logger.warning(f"设备 {self.device_id} 不存在，守护线程退出")
                    return
                # 说明：
                # - 撕裂/下半发白/解码报错，常见诱因是上游转推重连后缺少关键帧或关键帧间隔过大；
                #   增加关键帧频率并关闭B帧，可显著降低“重连后花屏/撕裂持续时间”。
                # - RTSP 端异常（如 5XX）需要超时参数避免阻塞卡死，便于守护线程重启。
                def _env_int(name: str, default: int) -> int:
                    try:
                        return int((os.getenv(name) or "").strip() or default)
                    except Exception:
                        return default

                def _env_str(name: str, default: str) -> str:
                    v = (os.getenv(name) or "").strip()
                    return v if v else default

                def _parse_bitrate_to_k(value: str) -> Optional[int]:
                    """
                    解析形如 '3500k' / '3500000' 的码率为 k 单位整数。
                    返回 None 表示无法解析。
                    """
                    try:
                        v = (value or "").strip().lower()
                        if not v:
                            return None
                        if v.endswith("k"):
                            return int(float(v[:-1]))
                        if v.endswith("m"):
                            return int(float(v[:-1]) * 1000)
                        # 纯数字：按 bps 估算为 k
                        if v.isdigit():
                            return max(1, int(int(v) / 1000))
                        return None
                    except Exception:
                        return None

                # 观看链路参数：优先 VIEW_*，回退到历史通用变量
                source_fps = _env_int("VIEW_SOURCE_FPS", _env_int("SOURCE_FPS", 25))
                # GOP 默认：2秒一个关键帧（与服务内其他实现保持一致），避免重连后长时间等IDR
                gop_size = _env_int("VIEW_FFMPEG_GOP_SIZE", _env_int("FFMPEG_GOP_SIZE", max(1, source_fps * 2)))
                preset = _env_str("VIEW_FFMPEG_PRESET", _env_str("FFMPEG_PRESET", "veryfast"))
                # 默认码率提升到 3500k（与 .env high 档一致），避免客户反馈“更糊”
                bitrate = _env_str("VIEW_FFMPEG_VIDEO_BITRATE", _env_str("FFMPEG_VIDEO_BITRATE", "3500k"))
                # 可选：恒定质量模式（更直观地控制“清晰度”）。例如 FFMPEG_CRF=23/21/19（越小越清晰）
                crf = (os.getenv("VIEW_FFMPEG_CRF") or os.getenv("FFMPEG_CRF") or "").strip()

                # 码控缓冲：默认 2x bitrate，避免 bufsize 过小导致画质波动/发糊
                bufsize_env = (os.getenv("VIEW_FFMPEG_VIDEO_BUFSIZE") or os.getenv("FFMPEG_VIDEO_BUFSIZE") or "").strip()
                if bufsize_env:
                    bufsize = bufsize_env
                else:
                    k = _parse_bitrate_to_k(bitrate)
                    bufsize = f"{max(1, (k or 3500) * 2)}k"

                rtsp_open_timeout_us = _env_int("FFMPEG_RTSP_OPEN_TIMEOUT_US", 10_000_000)  # 10s
                rtsp_io_timeout_us = _env_int("FFMPEG_RTSP_IO_TIMEOUT_US", 5_000_000)  # 5s

                input_url, url_rtsp_transport = _strip_rtsp_transport_query(device.source or "")
                # 海康等「传输协议 UDP」子码流：需与设备一致；默认可用环境变量或 URL 查询参数覆盖
                rtsp_transport = (url_rtsp_transport or _env_str(
                    "FFMPEG_RTSP_TRANSPORT",
                    _env_str("VIEW_FFMPEG_RTSP_TRANSPORT", "udp"),
                )).lower()
                if rtsp_transport not in ("tcp", "udp"):
                    rtsp_transport = "udp"

                is_rtsp_input = (input_url or "").strip().lower().startswith("rtsp://")

                ffmpeg_cmd = [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "warning",
                ]

                # 输入：RTSP 传输方式（默认 UDP，与海康子码流常见配置一致；需 TCP 时设 FFMPEG_RTSP_TRANSPORT=tcp）
                if is_rtsp_input:
                    ffmpeg_cmd.extend([
                        "-rtsp_transport",
                        rtsp_transport,
                    ])
                    if rtsp_transport == "tcp":
                        ffmpeg_cmd.extend(["-rtsp_flags", "prefer_tcp"])
                    ffmpeg_cmd.extend(_ffmpeg_rtsp_timeout_args(rtsp_open_timeout_us, rtsp_io_timeout_us))
                elif _ffmpeg_supports_rw_timeout():
                    ffmpeg_cmd.extend(["-rw_timeout", str(rtsp_io_timeout_us)])
                elif _ffmpeg_rtsp_open_timeout_flag() == "-timeout":
                    ffmpeg_cmd.extend(["-timeout", str(rtsp_io_timeout_us)])

                ffmpeg_cmd.extend([
                    "-fflags",
                    # 丢弃损坏包并生成时间戳：可减少“半边白/马赛克”持续时间（以连续性换取画面完整性）
                    "nobuffer+discardcorrupt+genpts",
                    # 忽略部分比特流错误，避免轻微抖动导致直接退出
                    "-err_detect",
                    "ignore_err",
                    "-flags",
                    "low_delay",
                    "-i",
                    input_url,

                    # 输出：仅视频
                    "-an",

                    # 编码：低延迟 + 高频关键帧 + 无B帧，减少重连后花屏/撕裂
                    "-c:v",
                    "libx264",
                    "-preset",
                    preset,
                    "-tune",
                    "zerolatency",
                ])

                # 优先使用 CRF（恒定质量）；否则使用 ABR/CBR（码率）
                if crf:
                    ffmpeg_cmd.extend(["-crf", crf])
                else:
                    ffmpeg_cmd.extend([
                        "-b:v",
                        bitrate,
                        "-maxrate",
                        bitrate,
                        "-bufsize",
                        bufsize,
                    ])

                ffmpeg_cmd.extend([
                    "-pix_fmt",
                    "yuv420p",
                    "-profile:v",
                    "main",
                    "-g",
                    str(max(1, gop_size)),
                    "-keyint_min",
                    str(max(1, source_fps)),
                    "-sc_threshold",
                    "0",
                    "-bf",
                    "0",

                    # RTMP/FLV
                    "-f",
                    "flv",
                    "-flvflags",
                    "no_duration_filesize",
                    device.rtmp_stream,
                ])

                # 启动进程并捕获错误流
                self.process = subprocess.Popen(
                    ffmpeg_cmd,
                    stderr=subprocess.PIPE,  # 关键：捕获错误日志
                    stdin=subprocess.PIPE,
                    text=False
                )
                logger.info(f"启动FFmpeg: {' '.join(ffmpeg_cmd)}")

                # 实时监控输出（仅记录错误和警告）
                while self._running:
                    line = self.process.stderr.readline()
                    if not line:
                        break
                    line_str = line.decode().strip()
                    if _ffmpeg_stderr_should_log(line_str):
                        logger.warning(f"[FFmpeg:{self.device_id}] {line_str}")

                # 进程结束后处理
                return_code = self.process.wait()
                if return_code != 0:
                    logger.error(f"FFmpeg异常退出，返回码: {return_code}，设备: {self.device_id}")

                # 按需重启（算法任务停止不会改 enable_forward，需显式关转发或 DB 置 False）
                if not self._running:
                    return
                if not self._forward_enabled_in_db():
                    logger.info(f"设备 {self.device_id} 已关闭观看转发，不再重启 FFmpeg")
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
            if not camera_service.is_device_available_for_stream(device):
                logger.info(f"设备 {device.id} 处于离线状态，跳过推送启动")
                continue
            
            with ffmpeg_lock:
                # 跳过已运行的进程
                if device.id in ffmpeg_processes:
                    daemon = ffmpeg_processes[device.id]
                    if daemon._running:
                        logger.info(f"设备 {device.id} 的流媒体转发已在运行中")
                        continue

                # 创建并启动守护线程
                ffmpeg_processes[device.id] = FFmpegDaemon(device.id)
                logger.info(f"设备 {device.id} 的流媒体转发已自动启动")

    except Exception as e:
        logger.error(f"自动启动流媒体转发失败: {str(e)}", exc_info=True)


# ------------------------- 接口实现 -------------------------
@camera_bp.route('/device/<string:device_id>/stream/start', methods=['POST'])
def start_ffmpeg_stream(device_id):
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'code': 400, 'msg': f'设备不存在: ID={device_id}'}), 400
        
        # 如果摄像头地址是 rtmp，则不启动推送
        if device.source and device.source.strip().lower().startswith('rtmp://'):
            return jsonify({
                'code': 400,
                'msg': '摄像头源地址是 RTMP，不支持推送功能'
            }), 400
        
        # 如果设备离线，则不启动推送（不 sole 依赖 ICMP ping）
        if not camera_service.is_device_available_for_stream(device):
            return jsonify({
                'code': 400,
                'msg': '设备处于离线状态，无法启动推送'
            }), 400
        
        with ffmpeg_lock:
            if device_id in ffmpeg_processes:
                daemon = ffmpeg_processes[device_id]
                if daemon._running:
                    return jsonify({
                        'code': 0,
                        'msg': '流媒体转发已在运行',
                        'data': {'rtmp_url': device.rtmp_stream, 'status': 'running'}
                    })
                daemon.stop()

            # 必须先落库 enable_forward=True，守护线程启动时会立刻查库
            device.enable_forward = True
            db.session.commit()
            ffmpeg_processes[device_id] = FFmpegDaemon(device_id)

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
        stop_registered_process(ffmpeg_processes, ffmpeg_lock, device_id)
        with ffmpeg_lock:
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
            return jsonify({'code': 400, 'msg': f'设备 {device_id} 不存在'}), 400

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

        # 确保当前页的设备都有对应的抓拍空间和录像空间
        for device in pagination.items:
            try:
                camera_service.ensure_device_spaces(device.id)
            except Exception as e:
                logger.warning(f'检查设备 {device.id} 空间时出错: {str(e)}')

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


@camera_bp.route('/locations', methods=['GET'])
def list_device_locations():
    """查询摄像头位置信息（供地图/轨迹等场景，不影响现有列表接口）。"""
    try:
        directory_id = request.args.get('directory_id')
        has_location = request.args.get('has_location', 'true').strip().lower()
        dir_id = int(directory_id) if directory_id not in (None, '') else None
        items = list_devices_for_map(
            directory_id=dir_id,
            has_location_only=has_location not in ('false', '0', 'no'),
        )
        return jsonify({'code': 0, 'msg': 'success', 'data': items, 'total': len(items)})
    except ValueError:
        return jsonify({'code': 400, 'msg': '参数 directory_id 需为整数'}), 400
    except Exception as e:
        logger.error(f'摄像头位置列表查询失败: {str(e)}')
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500


@camera_bp.route('/device/<string:device_id>/location', methods=['GET'])
def get_device_location_route(device_id):
    """获取单个摄像头坐标（地图选点弹窗，国标虚拟通道按需入库）。"""
    try:
        ensure_name = (request.args.get('name') or request.args.get('ensure_name') or '').strip() or None
        info = get_device_location_info(device_id, ensure_name=ensure_name)
        return jsonify({'code': 0, 'msg': 'success', 'data': info})
    except ValueError as e:
        logger.error(f'获取设备坐标失败: {str(e)}')
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'获取设备坐标失败: {str(e)}')
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500


@camera_bp.route('/device/<string:device_id>/location', methods=['PUT'])
def update_device_location_route(device_id):
    """更新单个摄像头位置（地图选点等）。"""
    try:
        data = request.get_json() or {}
        ensure_name = (data.pop('name', None) or data.pop('ensure_name', None) or '').strip() or None
        loc = update_device_location(device_id, data, ensure_name=ensure_name)
        return jsonify({'code': 0, 'msg': '位置更新成功', 'data': loc})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'更新摄像头位置失败: {str(e)}')
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500


@camera_bp.route('/locations/batch', methods=['POST'])
def batch_update_locations():
    """批量更新摄像头位置（CSV 导入等）。"""
    try:
        data = request.get_json() or {}
        items = data.get('items') or data.get('locations') or []
        if not isinstance(items, list):
            return jsonify({'code': 400, 'msg': 'items 需为数组'}), 400
        if len(items) > 500:
            return jsonify({'code': 400, 'msg': '单次最多导入 500 条'}), 400
        result = batch_update_device_locations(items)
        return jsonify({'code': 0, 'msg': 'success', 'data': result})
    except Exception as e:
        logger.error(f'批量更新摄像头位置失败: {str(e)}')
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500


@camera_bp.route('/tracks/sessions', methods=['GET'])
def list_device_track_sessions():
    """查询摄像头轨迹段列表。"""
    try:
        device_id = request.args.get('device_id')
        begin = request.args.get('begin_datetime') or request.args.get('begin')
        end = request.args.get('end_datetime') or request.args.get('end')
        limit = request.args.get('limit', 50)
        items = list_track_sessions(
            device_id=device_id,
            begin=begin,
            end=end,
            limit=int(limit) if str(limit).isdigit() else 50,
        )
        return jsonify({'code': 0, 'msg': 'success', 'data': items, 'total': len(items)})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'轨迹段列表查询失败: {str(e)}')
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500


@camera_bp.route('/tracks/points', methods=['GET'])
def list_device_track_points():
    """查询轨迹点（按 session_id 或 device_id + 时间）。"""
    try:
        session_id = request.args.get('session_id')
        device_id = request.args.get('device_id')
        begin = request.args.get('begin_datetime') or request.args.get('begin')
        end = request.args.get('end_datetime') or request.args.get('end')
        limit = request.args.get('limit', 5000)
        items = list_track_points(
            session_id=session_id,
            device_id=device_id,
            begin=begin,
            end=end,
            limit=int(limit) if str(limit).isdigit() else 5000,
        )
        return jsonify({'code': 0, 'msg': 'success', 'data': items, 'total': len(items)})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'轨迹点查询失败: {str(e)}')
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500


@camera_bp.route('/device/<string:device_id>', methods=['GET'])
def get_device_info(device_id):
    """获取单个设备详情"""
    try:
        ensure_name = (request.args.get('name') or request.args.get('ensure_name') or '').strip() or None
        info = get_camera_info(device_id, ensure_name=ensure_name)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': info
        })
    except ValueError as e:
        logger.error(f'获取设备详情失败: {str(e)}')
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'获取设备详情失败: {str(e)}')
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500


@camera_bp.route('/device/<string:device_id>/inference-input', methods=['GET'])
def get_device_inference_input(device_id):
    """解析设备推理输入流（RTSP/RTMP/SRS/国标点播）。"""
    try:
        data = resolve_device_inference_input(device_id)
        return jsonify({'code': 0, 'msg': 'success', 'data': data})
    except ValueError as e:
        logger.error(f'解析设备推理输入流失败: {str(e)}')
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'解析设备推理输入流失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500


@camera_bp.route('/device/<string:device_id>/ensure-spaces', methods=['POST'])
def ensure_device_spaces_route(device_id):
    """确保设备已关联抓拍空间与录像空间（缺失则自动创建）"""
    try:
        from models import Device
        from app.services.snap_space_service import get_snap_space_by_device_id
        from app.services.record_space_service import get_record_space_by_device_id

        device = Device.query.get(device_id)
        if not device:
            return jsonify({'code': 404, 'msg': f'设备不存在: {device_id}'}), 404

        ensure_device_spaces(device_id)
        snap_space = get_snap_space_by_device_id(device_id)
        record_space = get_record_space_by_device_id(device_id)
        return jsonify({
            'code': 0,
            'msg': '存储空间已就绪',
            'data': {
                'snap_space': snap_space.to_dict() if snap_space else None,
                'record_space': record_space.to_dict() if record_space else None,
            },
        })
    except Exception as e:
        logger.error(f'初始化设备存储空间失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


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


@camera_bp.route('/flighthub/config', methods=['GET'])
def get_flighthub_config():
    """返回司空 FlightHub 配置（机场/无人机共用同一套 OpenAPI）。"""
    return jsonify({'code': 0, 'msg': 'success', 'data': get_flighthub_public_config()})


@camera_bp.route('/rtc/config', methods=['GET'])
def get_rtc_config():
    """返回 RTC / go2rtc 公共配置。"""
    return jsonify({'code': 0, 'msg': 'success', 'data': get_rtc_public_config()})


@camera_bp.route('/rtc/platforms', methods=['GET'])
def get_rtc_platforms():
    """返回 RTC 支持的摄像头平台列表。"""
    try:
        platforms = list_rtc_platforms()
        return jsonify({'code': 0, 'msg': 'success', 'data': {'platforms': platforms}})
    except Exception as e:
        logger.error(f'RTC platforms fetch failed: {e}', exc_info=True)
        return jsonify({'code': 502, 'msg': f'RTC 服务不可用: {e}'}), 502


@camera_bp.route('/rtc/build-url', methods=['POST'])
def build_rtc_url():
    """预览 RTC 平台源流 URL（不注册）。"""
    data = request.get_json(silent=True) or {}
    platform = (data.get('platform') or '').strip()
    params = data.get('params') or {}
    if not platform:
        return jsonify({'code': 400, 'msg': 'platform is required'}), 400
    try:
        source = build_rtc_stream_url(platform, params)
        return jsonify({'code': 0, 'msg': 'success', 'data': {'platform': platform, 'source': source}})
    except Exception as e:
        logger.error(f'RTC build-url failed: {e}', exc_info=True)
        return jsonify({'code': 400, 'msg': str(e)}), 400


@camera_bp.route('/register/device/rtc-live', methods=['POST'])
def register_rtc_live_device():
    """登记 RTC 平台摄像头（Tapo/Tuya/Ring 等），自动注册 go2rtc 流并写入 VIDEO。"""
    data = request.get_json(silent=True) or {}
    try:
        result = register_rtc_live(data)
        if not result.get('ok'):
            return jsonify({
                'code': int(result.get('code') or 500),
                'msg': result.get('msg') or 'RTC live register failed',
            }), int(result.get('code') or 500)

        register_info = result['register_info']
        if data.get('enable_forward') is not None:
            register_info['enable_forward'] = bool(data.get('enable_forward'))
        device_id = register_camera(register_info)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'id': device_id,
                'platform': result.get('platform'),
                'stream_name': result.get('stream_name'),
                'source': register_info.get('source'),
                'rtsp_url': result.get('rtsp_url'),
                'play_urls': result.get('play_urls'),
            },
        })
    except Exception as e:
        logger.error(f'RTC live device register failed: {e}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': str(e)}), 500


@camera_bp.route('/register/device/dji-live', methods=['POST'])
def register_dji_live_device():
    """登记大疆直播设备（机场 dock / 无人机 drone，协议相同，仅元数据区分）。"""
    data = request.get_json(silent=True) or {}
    source = (data.get('source') or '').strip()
    if not source:
        return jsonify({'code': 400, 'msg': 'source is required'}), 400
    try:
        register_info = build_flighthub_register_info(data, source)
        device_id = register_camera(register_info)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'id': device_id,
                'device_type': register_info.get('device_type'),
                'model': register_info.get('model'),
            },
        })
    except Exception as e:
        logger.error(f'DJI live device register failed: {e}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': str(e)}), 500


@camera_bp.route('/flighthub/live-stream/start', methods=['POST'])
def start_flighthub_live_stream():
    """调用司空开启直播；直拉地址自动登记为本地自定义设备。"""
    data = request.get_json(silent=True) or {}
    try:
        result = start_flighthub_live(data)
        if not result.get('ok'):
            code = int(result.get('code') or 500)
            payload = {
                'provider': result.get('provider'),
                'url_type': result.get('url_type'),
                'suggestion': result.get('suggestion'),
                'raw': result.get('raw'),
            }
            # 保留 provider 细节给前端做 SDK / volc 分支登记
            if result.get('provider') is not None:
                payload['provider'] = result.get('provider')
            return jsonify({
                'code': code,
                'msg': result.get('msg') or 'FlightHub live start failed',
                'data': payload if any(payload.values()) else result.get('raw'),
            }), 200

        register_info = build_flighthub_register_info(data, result['url'])
        # 直拉供应商默认允许走现有 SRS 转发
        if data.get('enable_forward') is None:
            register_info['enable_forward'] = True
        device_id = register_camera(register_info)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'id': device_id,
                'source': result['url'],
                'provider': result.get('provider'),
                'device_type': register_info.get('device_type'),
                'model': register_info.get('model'),
                'raw': result.get('raw'),
            },
        })
    except Exception as e:
        logger.error(f'FlightHub live start failed: {e}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': str(e)}), 200


@camera_bp.route('/flighthub/live-stream/refresh-device/<string:device_id>', methods=['POST'])
def refresh_flighthub_live_by_device(device_id: str):
    """按已登记大疆设备刷新司空直播地址（鉴权过期时用）。"""
    device = Device.query.get(device_id)
    if not device:
        return jsonify({'code': 404, 'msg': 'device not found'}), 404
    data = request.get_json(silent=True) or {}
    device_type = resolve_device_type_from_record(
        data.get('device_type'),
        model=device.model or '',
        name=device.name or '',
        connection_status=device.connection_status or '',
    )
    camera_index = resolve_camera_index(
        data,
        source=device.source or '',
        connection_status=device.connection_status or '',
    )
    data.setdefault('name', device.name)
    data.setdefault('serial_number', device.serial_number)
    data.setdefault(
        'project_uuid',
        (device.hardware_id or '').replace('flighthub:', '').split('|')[0] or device.username or '',
    )
    data.setdefault(
        'user_token',
        getattr(device, 'skylink_token', None)
        or data.get('user_token')
        or data.get('skylink_token')
        or flighthub_env('FLIGHTHUB_USER_TOKEN')
        or device.password
        or '',
    )
    data.setdefault('api_host', device.firmware_version or flighthub_env('FLIGHTHUB_OPENAPI_HOST'))
    data.setdefault('sn', device.serial_number or '')
    data.setdefault('camera_index', camera_index)
    data.setdefault('device_type', device_type)
    data.setdefault('model', device.model or model_for_device_type(device_type))
    data.setdefault('enable_forward', bool(device.enable_forward))
    data.setdefault('address', device.address)
    data.setdefault('longitude', device.longitude)
    data.setdefault('latitude', device.latitude)
    data.setdefault('altitude', device.altitude)
    with current_app.test_request_context(json=data):
        return start_flighthub_live_stream()


@camera_bp.route('/register/device/onvif', methods=['POST'])
def register_device_by_onvif():
    """通过 ONVIF 连接并注册单机设备（调用 ``register_camera_by_onvif``）。"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        ip = data.get('ip', '').strip()
        port = data.get('port', 80)
        username = data.get('username')
        if username is not None:
            username = str(username).strip()
        password = data.get('password', '').strip()
        
        if not ip:
            return jsonify({'code': 400, 'msg': '摄像头IP地址不能为空'}), 400
        if not password:
            return jsonify({'code': 400, 'msg': '摄像头密码不能为空'}), 400
        
        try:
            port = int(port)
        except (ValueError, TypeError):
            return jsonify({'code': 400, 'msg': '摄像头端口必须是数字'}), 400
        
        ingress_node_id = data.get('ingress_node_id')
        if ingress_node_id not in (None, '', 0, '0'):
            try:
                ingress_node_id = int(ingress_node_id)
            except (TypeError, ValueError):
                return jsonify({'code': 400, 'msg': '接入节点 ID 无效'}), 400
        else:
            ingress_node_id = None
        device_id = register_camera_by_onvif(
            ip, port, password, username=username or None,
            ingress_node_id=ingress_node_id,
        )
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

        # 规范化布尔字段：空字符串 / None 统一转为 False，字符串 'true'/'false' 转为布尔值
        bool_fields = ['support_move', 'support_zoom', 'enable_forward']
        for field in bool_fields:
            if field in data:
                val = data[field]
                if val is None or val == '':
                    data[field] = False
                elif isinstance(val, str):
                    data[field] = val.lower() in ('true', '1', 'yes', 'on')
        
        # 如果更新manufacturer或model字段为空，使用默认值
        if 'manufacturer' in data:
            manufacturer = data.get('manufacturer', '').strip() if data.get('manufacturer') else ''
            if not manufacturer:
                data['manufacturer'] = 'EasyAIoT'
        if 'model' in data:
            model = data.get('model', '').strip() if data.get('model') else ''
            if not model:
                data['model'] = 'Camera-EasyAIoT'
        
        if 'ingress_node_id' in data:
            raw_node_id = data.get('ingress_node_id')
            if raw_node_id in (None, '', 0, '0'):
                data['ingress_node_id'] = None
            else:
                try:
                    data['ingress_node_id'] = int(raw_node_id)
                except (TypeError, ValueError):
                    return jsonify({'code': 400, 'msg': '接入节点 ID 无效'}), 400
                device = Device.query.get(device_id)
                if device and device.source:
                    from app.utils.node_client import camera_access
                    camera_access(data['ingress_node_id'], 'probe-stream', {
                        'source': data.get('source') or device.source,
                        'timeout': 10,
                    })

        update_camera(device_id, data)

        if 'ingress_node_id' in data:
            device = Device.query.get(device_id)
            if device and device.nvr_id:
                from models import Nvr
                nvr = Nvr.query.get(device.nvr_id)
                if nvr:
                    nvr.ingress_node_id = data['ingress_node_id']
                    for channel in Device.query.filter_by(nvr_id=nvr.id).all():
                        channel.ingress_node_id = data['ingress_node_id']
                    db.session.commit()
                    from app.services.stream_forward_service import ensure_nvr_stream_forward_task
                    ensure_nvr_stream_forward_task(nvr.id)
            else:
                from app.services.stream_forward_service import ensure_device_stream_forward_task
                ensure_device_stream_forward_task(device_id)

        # 关闭观看转发时同步停止守护进程（与算法任务无关）
        ef = data.get('enable_forward')
        if ef is False or (isinstance(ef, str) and ef.lower() in ('false', '0', 'no', 'off')):
            stop_registered_process(ffmpeg_processes, ffmpeg_lock, device_id)

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
        # 停止转发属于删除前的尽力清理；子进程已退出等清理异常不能阻断设备删库。
        try:
            stop_registered_process(ffmpeg_processes, ffmpeg_lock, device_id)
        except Exception as e:
            logger.warning(f'删除设备前停止流媒体转发失败 {device_id}: {e}', exc_info=True)

        delete_camera(device_id)
        return jsonify({
            'code': 0,
            'msg': '设备删除成功'
        })
    except ValueError as e:
        logger.error(f'删除设备失败: {str(e)}')
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except RuntimeError as e:
        logger.error(f'删除设备失败: {str(e)}')
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'删除设备失败（未知错误）: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'删除设备失败: {str(e)}'}), 500


@camera_bp.route('/devices/batch-delete', methods=['POST'])
def batch_delete_devices():
    """批量删除摄像头设备。"""
    try:
        data = request.get_json(silent=True) or {}
        device_ids = data.get('device_ids') or data.get('deviceIds') or []
        if not isinstance(device_ids, list) or not device_ids:
            return jsonify({'code': 400, 'msg': 'device_ids 不能为空'}), 400

        for raw_id in device_ids:
            device_id = str(raw_id or '').strip()
            if not device_id:
                continue
            if device_id in ffmpeg_processes:
                try:
                    stop_ffmpeg_stream(device_id)
                except Exception as e:
                    logger.warning(f'批量删除前停止推流失败 {device_id}: {e}')

        result = batch_delete_cameras(device_ids)
        return jsonify({
            'code': 0,
            'msg': '批量删除完成',
            'data': result,
        })
    except Exception as e:
        logger.error(f'批量删除设备失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'批量删除失败: {str(e)}'}), 500


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
            return jsonify({'error': 'Camera not found'}), 400

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
    secure_value = current_app.config.get('MINIO_SECURE', False)
    # 处理 secure 可能是布尔值或字符串的情况
    if isinstance(secure_value, bool):
        secure = secure_value
    else:
        secure = str(secure_value).lower() == 'true'
    return Minio(minio_endpoint, access_key=access_key, secret_key=secret_key, secure=secure)


def _public_read_policy(bucket_name):
    """生成匿名只读(download)策略：允许前端经 MinIO 下载接口加载该桶图片。

    截图桶仅供前端展示，只读即可（不开放匿名写），与 alert-images 等显示用桶一致。
    """
    import json
    return json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Principal": {"AWS": ["*"]},
             "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
             "Resource": [f"arn:aws:s3:::{bucket_name}"]},
            {"Effect": "Allow", "Principal": {"AWS": ["*"]},
             "Action": ["s3:GetObject"],
             "Resource": [f"arn:aws:s3:::{bucket_name}/*"]},
        ],
    })


def _persist_screenshot_record(
    camera_id,
    download_url,
    unique_filename,
    timestamp,
    image_format,
    width,
    height,
):
    """将截图元数据写入数据库。"""
    try:
        image_record = Image(
            filename=unique_filename,
            original_filename=f"{camera_id}_{timestamp}.{image_format}",
            path=download_url,
            width=width,
            height=height,
            device_id=camera_id,
        )
        db.session.add(image_record)
        db.session.commit()
        logger.info(f"图片信息已存入数据库，ID: {image_record.id}")
    except Exception as db_error:
        db.session.rollback()
        logger.error(f"数据库存储失败: {str(db_error)}")


def _upload_screenshot_to_local(camera_id, image_data, image_format="jpg"):
    """mini 形态：截图落本地磁盘，经 /video/alert/image 对外提供访问。"""
    from datetime import datetime as _dt

    from app.services.playback_disk_guard_service import get_camera_screenshot_dir
    from app.utils.service_urls import build_alert_image_api_url

    timestamp = _dt.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{uuid.uuid4().hex}.{image_format}"

    success, encoded_image = cv2.imencode(f'.{image_format}', image_data)
    if not success:
        raise RuntimeError("图像编码失败")

    height, width = image_data.shape[:2]
    screenshot_root = get_camera_screenshot_dir()
    device_dir = os.path.join(screenshot_root, str(camera_id))
    os.makedirs(device_dir, exist_ok=True)
    local_path = os.path.join(device_dir, unique_filename)
    with open(local_path, 'wb') as handle:
        handle.write(encoded_image.tobytes())

    download_url = build_alert_image_api_url(local_path)
    _persist_screenshot_record(
        camera_id, download_url, unique_filename, timestamp, image_format, width, height
    )
    logger.info(f"截图本地保存成功: {local_path}")
    return download_url


def upload_screenshot_to_minio(camera_id, image_data, image_format="jpg"):
    """上传摄像头截图（MinIO 或 mini 本地）并存入数据库。"""
    from app.utils.service_urls import minio_storage_enabled

    if not minio_storage_enabled():
        try:
            return _upload_screenshot_to_local(camera_id, image_data, image_format)
        except Exception as e:
            logger.error(f"截图本地保存失败: {str(e)}")
            return None

    try:
        minio_client = get_minio_client()
        bucket_name = "camera-screenshots"

        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            # 新建桶设为匿名只读，否则前端无法经 MinIO 下载接口加载截图（画布会空白）
            try:
                minio_client.set_bucket_policy(bucket_name, _public_read_policy(bucket_name))
            except Exception as e:
                logger.warning(f"设置截图桶 {bucket_name} 匿名只读策略失败(不影响上传，但前端可能加载不出图片): {e}")
            logger.info(f"创建截图存储桶: {bucket_name}")

        # 本模块顶部的 `from app.services.camera_service import *` 会用 datetime 类覆盖
        # 模块名 datetime，导致 datetime.datetime 不可用，这里用局部别名规避
        from datetime import datetime as _dt
        timestamp = _dt.now().strftime("%Y%m%d_%H%M%S")
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
        _persist_screenshot_record(
            camera_id, download_url, unique_filename, timestamp, image_format, width, height
        )
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
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'code': 400, 'msg': f'设备不存在: ID={device_id}'}), 400
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
        return jsonify({'code': 400, 'msg': '未找到运行的RTSP截图任务'}), 400
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
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'code': 400, 'msg': f'设备不存在: ID={device_id}'}), 400
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
        return jsonify({'code': 400, 'msg': '未找到运行的ONVIF截图任务'}), 400
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


# ------------------------- ONVIF 预置点接口 -------------------------
@camera_bp.route('/device/<string:device_id>/onvif/presets', methods=['GET'])
def list_onvif_presets_api(device_id: str):
    """查询 ONVIF 设备预置点列表"""
    try:
        presets = camera_service.list_onvif_presets(device_id)
        return jsonify({'code': 0, 'msg': 'success', 'data': presets})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error('查询 ONVIF 预置点失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'查询预置点失败: {str(e)}'}), 500


@camera_bp.route('/device/<string:device_id>/onvif/presets', methods=['POST'])
def set_onvif_preset_api(device_id: str):
    """保存当前位置为 ONVIF 预置点

    Body: { "name": "预置点 1", "preset_token": "可选，覆盖已有预置点" }
    """
    try:
        data = request.get_json() or {}
        name = str(data.get('name') or '').strip()
        if not name:
            return jsonify({'code': 400, 'msg': '预置点名称不能为空'}), 400
        preset_token = data.get('preset_token')
        if preset_token is not None:
            preset_token = str(preset_token).strip() or None
        token = camera_service.set_onvif_preset(device_id, name, preset_token)
        return jsonify({
            'code': 0,
            'msg': '预置点已保存',
            'data': {'token': token, 'name': name},
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error('保存 ONVIF 预置点失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'保存预置点失败: {str(e)}'}), 500


@camera_bp.route('/device/<string:device_id>/onvif/presets/call', methods=['POST'])
def call_onvif_preset_api(device_id: str):
    """调用 ONVIF 预置点

    Body: { "preset_token": "1" }
    """
    try:
        data = request.get_json() or {}
        preset_token = str(data.get('preset_token') or data.get('token') or '').strip()
        if not preset_token:
            return jsonify({'code': 400, 'msg': '缺少 preset_token'}), 400
        camera_service.call_onvif_preset(device_id, preset_token)
        return jsonify({'code': 0, 'msg': '预置点已调用'})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error('调用 ONVIF 预置点失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'调用预置点失败: {str(e)}'}), 500


@camera_bp.route('/device/<string:device_id>/onvif/presets/<string:preset_token>', methods=['DELETE'])
def delete_onvif_preset_api(device_id: str, preset_token: str):
    """删除 ONVIF 预置点"""
    try:
        camera_service.delete_onvif_preset(device_id, preset_token)
        return jsonify({'code': 0, 'msg': '预置点已删除'})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error('删除 ONVIF 预置点失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'删除预置点失败: {str(e)}'}), 500


def grab_frame_for_snapshot(device):
    """解析设备源地址并抓取一帧。

    与 realtime/snapshot 算法服务保持一致：先用 resolve_gb28181_source 把
    gb28181:// 虚拟源按需点播解析为可播放的 RTSP/RTMP（普通 rtsp/rtmp 源原样返回），
    这样即使算法任务未启动，也能为抓拍/区域绘制取到一帧。

    返回 (frame, error_msg)，成功时 error_msg 为 None。
    """
    try:
        source = resolve_gb28181_source((device.source or '').strip(), logger=logger)
    except Exception as e:
        logger.error(f"解析设备源地址失败: device_id={device.id}, error={str(e)}", exc_info=True)
        return None, f'解析设备源地址失败: {str(e)}'

    if not source:
        return None, '无法获取可播放的视频流地址（国标点播失败或设备离线）'

    source = source.strip()
    source_lower = source.lower()

    # 判断是否是RTMP流
    if source_lower.startswith('rtmp://'):
        # 使用FFmpeg从RTMP流中抽帧
        try:
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', source,  # RTMP流地址
                '-vframes', '1',  # 只抽取1帧
                '-f', 'image2',  # 输出格式为图片
                '-vcodec', 'mjpeg',  # 使用MJPEG编码
                '-q:v', '2',  # 高质量
                'pipe:1'  # 输出到标准输出
            ]

            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            stdout, stderr = process.communicate(timeout=10)  # 10秒超时

            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else '未知错误'
                return None, f'RTMP流抽帧失败: {error_msg}'

            if not stdout:
                return None, 'RTMP流抽帧失败: 未获取到图像数据'

            image_array = np.frombuffer(stdout, np.uint8)
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            if frame is None:
                return None, 'RTMP流抽帧失败: 图像解码失败'
            return frame, None
        except subprocess.TimeoutExpired:
            return None, 'RTMP流抽帧超时'
        except Exception as e:
            logger.error(f"RTMP流抽帧异常: {str(e)}", exc_info=True)
            return None, f'RTMP流抽帧异常: {str(e)}'
    else:
        # 使用OpenCV从RTSP流抓取一帧
        cap = cv2.VideoCapture(source)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 减少缓冲区，获取最新帧

        ret, frame = cap.read()
        cap.release()

        if not ret:
            return None, '无法从视频流读取帧'
        return frame, None


# ------------------------- RTSP/RTMP单帧抓拍接口 -------------------------
@camera_bp.route('/device/<string:device_id>/snapshot', methods=['POST'])
def capture_snapshot(device_id):
    """从RTSP/RTMP流抓取一帧图片并存入数据库"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'code': 400, 'msg': f'设备不存在: ID={device_id}'}), 400

        if not device.source:
            return jsonify({'code': 400, 'msg': '设备源地址为空'}), 400

        # 抓拍一帧（自动解析 gb28181:// 源，普通 rtsp/rtmp 原样使用）
        frame, capture_err = grab_frame_for_snapshot(device)
        if capture_err:
            # 返回 HTTP 200 + code:500：前端 isTransformResponse=false，会读取 msg 显示具体原因，
            # 避免全局拦截器把 HTTP 500 统一提示为"服务器错误,请联系管理员!"
            return jsonify({'code': 500, 'msg': capture_err})

        # 上传到MinIO并存入数据库
        image_url = upload_screenshot_to_minio(device_id, frame, 'jpg')

        if not image_url:
            return jsonify({'code': 500, 'msg': '图片上传失败'})

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


# ------------------------- NVR 管理 -------------------------
@camera_bp.route('/nvr/list', methods=['GET'])
def list_nvr_devices():
    """NVR 列表（含各 NVR 下已注册摄像头数量）。"""
    try:
        from app.services.nvr_service import list_nvrs
        include = request.args.get('include_cameras', '').lower() in ('1', 'true', 'yes')
        return jsonify({'code': 0, 'msg': 'success', 'data': list_nvrs(include_cameras=include)})
    except Exception as e:
        logger.error(f'获取 NVR 列表失败: {e}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'获取 NVR 列表失败: {e}'}), 500


@camera_bp.route('/nvr/<int:nvr_id>', methods=['GET'])
def get_nvr_device(nvr_id: int):
    try:
        from app.services.nvr_service import get_nvr
        include = request.args.get('include_cameras', 'true').lower() in ('1', 'true', 'yes')
        return jsonify({'code': 0, 'msg': 'success', 'data': get_nvr(nvr_id, include_cameras=include)})
    except ValueError as e:
        return jsonify({'code': 404, 'msg': str(e)}), 404
    except Exception as e:
        logger.error(f'获取 NVR 详情失败: {e}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'获取 NVR 详情失败: {e}'}), 500


@camera_bp.route('/nvr/upsert', methods=['POST'])
def upsert_nvr_device():
    """创建或更新 NVR 记录（按 IP+端口唯一）。"""
    try:
        from app.services.nvr_service import upsert_nvr
        data = request.get_json() or {}
        if not (data.get('ip') or '').strip():
            return jsonify({'code': 400, 'msg': 'NVR IP 不能为空'}), 400
        row = upsert_nvr(data)
        return jsonify({'code': 0, 'msg': 'success', 'data': row})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'保存 NVR 失败: {e}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'保存 NVR 失败: {e}'}), 500


@camera_bp.route('/nvr/register-channels', methods=['POST'])
def register_nvr_channels_device():
    """登记 NVR 并批量挂载枚举到的通道；未传 channels 时服务端自动枚举。"""
    try:
        from app.services.hik_scan_service import enumerate_nvr_channels
        from app.services.nvr_service import bulk_register_nvr_channels

        data = request.get_json() or {}
        ip = (data.get('ip') or '').strip()
        if not ip:
            return jsonify({'code': 400, 'msg': 'NVR IP 不能为空'}), 400
        raw_ingress_node_id = data.get('ingress_node_id')
        if raw_ingress_node_id in (None, '', 0, '0'):
            data['ingress_node_id'] = None
        else:
            try:
                data['ingress_node_id'] = int(raw_ingress_node_id)
            except (TypeError, ValueError):
                return jsonify({'code': 400, 'msg': '接入节点 ID 无效'}), 400
        try:
            port = int(data.get('port') or 80)
        except (TypeError, ValueError):
            return jsonify({'code': 400, 'msg': '端口必须是数字'}), 400

        username = (data.get('username') or '').strip() or None
        password = data.get('password')
        credentials = data.get('credentials')
        if credentials is not None and not isinstance(credentials, list):
            return jsonify({'code': 400, 'msg': 'credentials 须为数组'}), 400

        vendor = (data.get('vendor') or '').strip() or None
        rtsp_template = (data.get('rtsp_template') or '').strip() or None
        rtsp_port = data.get('rtsp_port')
        if rtsp_port is not None:
            try:
                rtsp_port = int(rtsp_port)
            except (TypeError, ValueError):
                rtsp_port = None
        channel_count = data.get('channel_count')
        if channel_count is not None:
            try:
                channel_count = int(channel_count)
            except (TypeError, ValueError):
                channel_count = None

        channels = data.get('channels')
        enum_error: str | None = None

        is_custom = vendor == 'custom' or (rtsp_template is not None)

        if channels is None:
            if is_custom:
                if not channel_count or channel_count <= 0:
                    return jsonify({'code': 400, 'msg': '自定义品牌请填写通道数量'}), 400
                channels = [
                    {'channel_id': i, 'name': f'通道{i}'}
                    for i in range(1, channel_count + 1)
                ]
            else:
                from app.services.nvr_service import merge_nvr_enum_credentials

                username, password, credentials = merge_nvr_enum_credentials(
                    ip,
                    port,
                    username=username,
                    password=password,
                    credentials=credentials,
                )
                if not credentials and not username:
                    return jsonify({'code': 400, 'msg': '请至少填写一组用户名和密码'}), 400
                has_password = bool(password) or any(
                    isinstance(c, dict) and c.get('password')
                    for c in (credentials or [])
                )
                if not has_password:
                    return jsonify({
                        'code': 400,
                        'msg': '请填写 NVR Web 登录密码（枚举通道需 ISAPI 认证）',
                    }), 400
                if password and not data.get('password'):
                    data['password'] = password
                if username and not data.get('username'):
                    data['username'] = username
                timeout = max(float(data.get('timeout') or 5.0), 10.0)
                ingress_node_id = data.get('ingress_node_id')
                if ingress_node_id not in (None, '', 0, '0'):
                    from app.utils.node_client import camera_access
                    inv = camera_access(int(ingress_node_id), 'nvr-channels', {
                        **data,
                        'ip': ip,
                        'port': port,
                        'username': username,
                        'password': password,
                        'credentials': credentials,
                        'timeout': timeout,
                        'vendor': vendor,
                        'probe_cameras': False,
                        'channel_filter': 'registerable',
                    })
                else:
                    inv = enumerate_nvr_channels(
                        ip,
                        port,
                        username=username,
                        password=password,
                        credentials=credentials,
                        timeout=timeout,
                        vendor=vendor,
                        probe_cameras=False,
                        channel_filter='registerable',
                    )
                channels = inv.get('channels') or []
                enum_error = inv.get('error')
                if inv.get('auth_username') and not username:
                    username = inv.get('auth_username')
                if not data.get('name') and inv.get('nvr_device_name'):
                    data['name'] = inv.get('nvr_device_name')
                if not data.get('model') and inv.get('nvr_model'):
                    data['model'] = inv.get('nvr_model')
                if not data.get('vendor') and inv.get('nvr_vendor'):
                    data['vendor'] = inv.get('nvr_vendor')
                if not data.get('serial_number') and inv.get('nvr_serial'):
                    data['serial_number'] = inv.get('nvr_serial')
        elif not isinstance(channels, list):
            return jsonify({'code': 400, 'msg': 'channels 须为数组'}), 400

        row = bulk_register_nvr_channels(
            data,
            channels,
            username=username or '',
            password=password or '',
            vendor=(data.get('vendor') or '').strip() or None,
            rtsp_template=rtsp_template,
            rtsp_port=rtsp_port,
        )
        stats = row.pop('register_stats', {})
        msg = f"已挂载 {stats.get('registered', 0)} 路通道"
        if stats.get('skipped'):
            msg += f"，跳过 {stats['skipped']} 路（无 RTSP）"
        if stats.get('errors'):
            msg += f"，{len(stats['errors'])} 路失败"
        if stats.get('registered', 0) == 0 and not channels:
            if enum_error:
                msg += f"（枚举失败：{enum_error}）"
            else:
                msg += "（未枚举到可登记通道，请确认 NVR 已添加摄像头且凭证正确）"
            detail = enum_error or '未枚举到可登记通道，请确认 NVR 已添加摄像头且凭证正确'
            if ';' in detail:
                detail = detail.split(';', 1)[0].strip()
            if ': ' in detail:
                detail = detail.split(': ', 1)[1].strip()
            return jsonify({'code': 400, 'msg': detail, 'data': row, 'stats': stats}), 400
        return jsonify({'code': 0, 'msg': msg, 'data': row, 'stats': stats})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'NVR 通道批量注册失败: {e}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'NVR 通道批量注册失败: {e}'}), 500


@camera_bp.route('/nvr/<int:nvr_id>', methods=['DELETE'])
def delete_nvr_device(nvr_id: int):
    """删除 NVR 记录。"""
    try:
        from app.services.nvr_service import delete_nvr
        delete_nvr(nvr_id)
        return jsonify({'code': 0, 'msg': 'success'})
    except ValueError as e:
        return jsonify({'code': 404, 'msg': str(e)}), 404
    except Exception as e:
        logger.error(f'删除 NVR 失败: {e}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'删除 NVR 失败: {e}'}), 500


@camera_bp.route('/nvr/batch-delete', methods=['POST'])
def batch_delete_nvr_devices():
    """批量删除 NVR 记录。"""
    try:
        from app.services.nvr_service import batch_delete_nvrs

        data = request.get_json(silent=True) or {}
        nvr_ids = data.get('nvr_ids') or data.get('nvrIds') or []
        if not isinstance(nvr_ids, list) or not nvr_ids:
            return jsonify({'code': 400, 'msg': 'nvr_ids 不能为空'}), 400

        result = batch_delete_nvrs(nvr_ids)
        return jsonify({
            'code': 0,
            'msg': '批量删除完成',
            'data': result,
        })
    except Exception as e:
        logger.error(f'批量删除 NVR 失败: {e}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'批量删除 NVR 失败: {e}'}), 500


# ------------------------- 网段扫描（hiktools） -------------------------
@camera_bp.route('/scan/segment', methods=['POST'])
def scan_segment_devices():
    """按网段扫描摄像头/NVR（HTTP 指纹 + 凭证探测，支持 CIDR / IP 范围）。"""
    try:
        from app.services.hik_scan_service import scan_segment

        data = request.get_json() or {}
        ingress_node_id = data.get('ingress_node_id')
        targets = (data.get('targets') or '').strip()
        if not targets:
            return jsonify({'code': 400, 'msg': '请填写扫描目标（网段 / IP / 范围）'}), 400

        username = (data.get('username') or '').strip() or None
        password = data.get('password')
        credentials = data.get('credentials')
        if credentials is not None and not isinstance(credentials, list):
            return jsonify({'code': 400, 'msg': 'credentials 须为数组'}), 400
        ports = (data.get('ports') or '80,443,8000,8443').strip()
        concurrency = int(data.get('concurrency') or 200)
        timeout = float(data.get('timeout') or 3.0)
        if timeout < 0.5 or timeout > 30:
            return jsonify({'code': 400, 'msg': '单点超时需在 0.5–30 秒之间'}), 400
        only_hits = bool(data.get('only_hits', True))
        nvr_only = bool(data.get('nvr_only', False))
        exclude_nvr = bool(data.get('exclude_nvr', False))

        if concurrency < 1 or concurrency > 2000:
            return jsonify({'code': 400, 'msg': '并发数需在 1–2000 之间'}), 400

        from app.vendor.hiktools.core.targets import MAX_SCAN_TASKS, estimate_scan_tasks

        try:
            task_count = estimate_scan_tasks(targets, ports)
        except ValueError as e:
            return jsonify({'code': 400, 'msg': str(e)}), 400
        if task_count > MAX_SCAN_TASKS:
            return jsonify({
                'code': 400,
                'msg': (
                    f'扫描目标过多（约 {task_count} 个探测点），请缩小网段或范围'
                    f'（单次上限 {MAX_SCAN_TASKS}）'
                ),
            }), 400

        if ingress_node_id not in (None, '', 0, '0'):
            from app.utils.node_client import camera_access
            devices = camera_access(int(ingress_node_id), 'scan-segment', data)
        else:
            devices = scan_segment(
                targets,
                ports_spec=ports,
                username=username,
                password=password,
                credentials=credentials,
                concurrency=concurrency,
                timeout=timeout,
                only_hits=only_hits,
                nvr_only=nvr_only,
                exclude_nvr=exclude_nvr,
            )
        return jsonify({'code': 0, 'msg': 'success', 'data': devices})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'网段扫描失败: {e}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'网段扫描失败: {e}'}), 500


@camera_bp.route('/scan/nvr/channels', methods=['POST'])
def scan_nvr_channels():
    """枚举 NVR 下属摄像头通道（海康/大华 ISAPI 或 CGI）。"""
    try:
        from app.services.hik_scan_service import enumerate_nvr_channels

        data = request.get_json() or {}
        ingress_node_id = data.get('ingress_node_id')
        ip = (data.get('ip') or '').strip()
        if not ip:
            return jsonify({'code': 400, 'msg': 'NVR IP 不能为空'}), 400
        try:
            port = int(data.get('port') or 80)
        except (TypeError, ValueError):
            return jsonify({'code': 400, 'msg': '端口必须是数字'}), 400

        username = (data.get('username') or '').strip() or None
        password = data.get('password')
        credentials = data.get('credentials')
        if credentials is not None and not isinstance(credentials, list):
            return jsonify({'code': 400, 'msg': 'credentials 须为数组'}), 400
        if not credentials and not username:
            return jsonify({'code': 400, 'msg': '请至少填写一组用户名和密码'}), 400

        timeout = float(data.get('timeout') or 5.0)
        vendor = (data.get('vendor') or '').strip() or None
        probe_cameras = bool(data.get('probe_cameras', False))
        only_mounted = bool(data.get('only_mounted', True))

        if ingress_node_id not in (None, '', 0, '0'):
            from app.utils.node_client import camera_access
            inv = camera_access(int(ingress_node_id), 'nvr-channels', data)
        else:
            inv = enumerate_nvr_channels(
                ip,
                port,
                username=username,
                password=password,
                credentials=credentials,
                timeout=timeout,
                vendor=vendor,
                probe_cameras=probe_cameras,
                only_mounted=only_mounted,
            )
        return jsonify({'code': 0, 'msg': 'success', 'data': inv})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'NVR 通道枚举失败: {e}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'NVR 通道枚举失败: {e}'}), 500


# ------------------------- 单机实时 ONVIF 发现 -------------------------
@camera_bp.route('/discovery', methods=['GET'])
def discover_devices():
    """发现网络中的 ONVIF 设备（WS-Discovery + camera_service._discovery_cameras）。供摄像头管理页局域网扫描使用。"""
    try:
        ingress_node_id = request.args.get('ingress_node_id', '').strip()
        if ingress_node_id:
            from app.utils.node_client import camera_access
            devices = camera_access(int(ingress_node_id), 'discover', {})
        else:
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
    """SRS发布回调接口
    当客户端尝试发布RTMP流时，SRS会调用此接口
    如果检测到流已存在，会尝试停止旧的发布者，然后允许新的发布
    
    注意：此回调必须快速响应（建议<1秒），否则SRS可能会超时并拒绝推流
    """
    import threading
    
    # 立即返回允许推流，避免阻塞
    # 流冲突检查在后台线程中异步执行
    try:
        data = request.get_json()
        if not data:
            logger.debug("on_publish回调：请求数据为空，允许发布")
            return jsonify({'code': 0, 'msg': None})
        
        # 从回调数据中提取流信息
        stream_url = data.get('stream_url', '')  # 格式: /live/1764341204704370859
        client_id = data.get('client_id', '')
        app = data.get('app', '')
        stream = data.get('stream', '')
        
        logger.debug(f"on_publish回调：收到推流请求 stream_url={stream_url}, client_id={client_id}, app={app}, stream={stream}")
        
        if not stream_url:
            logger.debug(f"on_publish回调：流URL为空，允许发布 client_id={client_id}")
            return jsonify({'code': 0, 'msg': None})
        
        # 在后台线程中异步检查并处理流冲突，避免阻塞回调响应
        def check_and_stop_existing_stream_async():
            try:
                # 从stream_url提取流路径: /live/1764341204704370859 -> live/1764341204704370859
                stream_path = stream_url.lstrip('/')
                
                # 获取SRS服务器地址（从环境变量或使用默认值）
                srs_host = os.getenv('SRS_HOST', 'localhost')
                srs_api_url = f"http://{srs_host}:1985/api/v1/streams/"
                
                # 获取所有流（使用较短的超时时间）
                try:
                    response = requests.get(srs_api_url, timeout=1)
                    if response.status_code == 200:
                        streams = response.json()
                        
                        # 查找匹配的流
                        stream_list = []
                        if isinstance(streams, dict) and 'streams' in streams:
                            stream_list = streams['streams']
                        elif isinstance(streams, list):
                            stream_list = streams
                        
                        for existing_stream in stream_list:
                            stream_app = existing_stream.get('app', '')
                            stream_stream = existing_stream.get('stream', '')
                            full_stream_path = f"{stream_app}/{stream_stream}" if stream_stream else stream_app
                            
                            # 检查是否匹配当前流
                            if stream_path == full_stream_path or stream_path.endswith(full_stream_path) or full_stream_path.endswith(stream_path):
                                publish_info = existing_stream.get('publish', {})
                                publish_cid = publish_info.get('cid', '') if isinstance(publish_info, dict) else None
                                
                                # 如果已有发布者且不是当前客户端，尝试停止旧的发布者
                                if publish_cid and publish_cid != client_id:
                                    logger.warning(f"on_publish回调：检测到流 {stream_path} 已有发布者 (client_id={publish_cid})，尝试停止...")
                                    
                                    # 尝试断开发布者客户端连接
                                    client_api_url = f"http://{srs_host}:1985/api/v1/clients/{publish_cid}"
                                    try:
                                        stop_response = requests.delete(client_api_url, timeout=1)
                                        if stop_response.status_code in [200, 204]:
                                            logger.info(f"on_publish回调：已停止旧的发布者 {publish_cid}，允许新发布")
                                        else:
                                            logger.warning(f"on_publish回调：停止旧发布者失败 (状态码: {stop_response.status_code})")
                                    except Exception as e:
                                        logger.warning(f"on_publish回调：停止旧发布者异常: {str(e)}")
                                
                                break
                except requests.exceptions.Timeout:
                    logger.debug(f"on_publish回调：检查现有流超时，跳过检查")
                except Exception as e:
                    logger.debug(f"on_publish回调：检查现有流时出错: {str(e)}")
            except Exception as e:
                logger.debug(f"on_publish回调：异步检查流冲突时出错: {str(e)}")
        
        # 启动后台线程处理流冲突检查（不阻塞回调响应）
        threading.Thread(target=check_and_stop_existing_stream_async, daemon=True).start()
        
        # 立即返回允许发布（不等待流冲突检查完成）
        return jsonify({
            'code': 0,
            'msg': None
        })
    except Exception as e:
        logger.error(f"on_publish回调异常: {str(e)}", exc_info=True)
        # 发生异常时也允许发布，避免影响正常流程
        return jsonify({'code': 0, 'msg': None})


def _parse_srs_dvr_segment_start_from_filename(absolute_file_path: str):
    """从 SRS DVR 文件名解析片段开始时间（毫秒时间戳）。

    约定文件名：``[timestamp].flv``，timestamp 为片段开始时刻（毫秒）。
    """
    from datetime import datetime as dt

    filename = os.path.basename(absolute_file_path)
    stem, ext = os.path.splitext(filename)
    if ext.lower() != '.flv' or not stem.isdigit():
        return None
    try:
        ts = int(stem)
        if ts > 10**12:
            return dt.fromtimestamp(ts / 1000.0)
        return dt.fromtimestamp(float(ts))
    except (ValueError, OSError):
        return None


def _parse_srs_dvr_path_date(absolute_file_path: str):
    """从 SRS DVR 路径解析 date_dir 与 record_time（片段开始时间）。

    约定：``.../playbacks/<app>/<stream>/YYYY/MM/DD/<timestamp>.flv``
    优先用文件名中的毫秒时间戳；否则回退 mtime/目录日期。
    返回 ``(date_dir, record_time)``；无法解析时返回 ``(None, None)``。
    """
    from datetime import datetime as dt

    segment_start = _parse_srs_dvr_segment_start_from_filename(absolute_file_path)
    parts = [p for p in absolute_file_path.replace("\\", "/").split("/") if p]
    try:
        if "playbacks" not in parts:
            return None, None
        i = parts.index("playbacks")
        if len(parts) < i + 7:
            return None, None
        y, mo, d = parts[i + 3], parts[i + 4], parts[i + 5]
        if len(y) != 4 or not y.isdigit() or not mo.isdigit() or not d.isdigit():
            return None, None
        date_dir = f"{y}/{mo}/{d}"
        if segment_start is not None:
            return date_dir, segment_start
        try:
            record_time = dt.fromtimestamp(os.path.getmtime(absolute_file_path))
        except OSError:
            try:
                record_time = dt(int(y), int(mo), int(d))
            except ValueError:
                return None, None
        return date_dir, record_time
    except (ValueError, IndexError, OSError):
        return None, None


def _srs_dvr_min_file_bytes() -> int:
    try:
        return max(512, int((os.getenv("SRS_DVR_MIN_FILE_BYTES") or "8192").strip()))
    except Exception:
        return 8192


def _wait_dvr_file_stable(absolute_file_path: str, max_retries: int = 20, retry_interval: float = 0.5) -> int:
    """等待 DVR 文件大小稳定且达到最小有效体积。返回 0 表示未就绪。"""
    min_bytes = _srs_dvr_min_file_bytes()
    for attempt in range(max_retries):
        if not os.path.exists(absolute_file_path):
            if attempt < max_retries - 1:
                time.sleep(retry_interval)
            continue
        try:
            size1 = os.path.getsize(absolute_file_path)
            time.sleep(0.2)
            size2 = os.path.getsize(absolute_file_path)
            if size1 == size2 and size1 >= min_bytes:
                return size1
        except OSError:
            pass
        if attempt < max_retries - 1:
            time.sleep(retry_interval)
    return 0


def _ffprobe_video_duration_seconds(video_path: str) -> float:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                video_path,
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0 and result.stdout.strip():
            return max(0.0, float(result.stdout.strip()))
    except Exception:
        pass
    return 0.0


def _extract_thumbnail_ffmpeg(video_path: str, frame_position: float = 0.1) -> Optional[np.ndarray]:
    """使用 ffmpeg 抽帧（FLV 等格式比 OpenCV CAP_ANY 更可靠）。"""
    duration = _ffprobe_video_duration_seconds(video_path)
    seek_sec = max(0.0, duration * frame_position) if duration > 0 else 0.0
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        str(seek_sec),
        "-i",
        video_path,
        "-map",
        "0:v:0",
        "-frames:v",
        "1",
        "-q:v",
        "2",
        "-f",
        "image2pipe",
        "-vcodec",
        "mjpeg",
        "pipe:1",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        if result.returncode != 0 or not result.stdout:
            return None
        frame = cv2.imdecode(np.frombuffer(result.stdout, dtype=np.uint8), cv2.IMREAD_COLOR)
        return frame
    except Exception as e:
        logger.debug(f"ffmpeg 抽帧失败: {video_path}, error={e}")
        return None


def _extract_thumbnail_opencv(video_path: str, frame_position: float = 0.1) -> Optional[np.ndarray]:
    """仅使用 FFMPEG 后端，避免 CAP_ANY 将纯数字文件名误判为图片序列。"""
    abs_video_path = os.path.abspath(video_path)
    cap = cv2.VideoCapture(abs_video_path, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        cap.release()
        return None
    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            ret, frame = cap.read()
            return frame if ret and frame is not None else None
        target_frame = max(1, int(total_frames * frame_position))
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        ret, frame = cap.read()
        return frame if ret and frame is not None else None
    finally:
        cap.release()


def extract_thumbnail_from_video(video_path, output_path=None, frame_position=0.1):
    """从视频文件中抽取一帧作为封面
    
    Args:
        video_path: 视频文件路径
        output_path: 输出图片路径，如果为None则返回图像数据
        frame_position: 抽取位置（0.0-1.0，0.1表示视频的10%位置）
    
    Returns:
        如果output_path为None，返回图像数据（numpy array），否则返回True/False
    """
    try:
        if not os.path.exists(video_path):
            logger.error(f"视频文件不存在: {video_path}")
            return None if output_path is None else False

        if not os.access(video_path, os.R_OK):
            logger.error(f"视频文件不可读: {video_path}")
            return None if output_path is None else False

        file_size = os.path.getsize(video_path)
        min_bytes = _srs_dvr_min_file_bytes()
        if file_size < min_bytes:
            logger.warning(
                f"视频文件过小，无法抽封面: {video_path}, size={file_size} bytes, min={min_bytes}"
            )
            return None if output_path is None else False

        abs_video_path = os.path.abspath(video_path)
        frame = _extract_thumbnail_ffmpeg(abs_video_path, frame_position)
        if frame is None:
            frame = _extract_thumbnail_opencv(abs_video_path, frame_position)

        if frame is None:
            logger.error(f"无法从视频中读取帧: {abs_video_path}, size={file_size}")
            return None if output_path is None else False

        if output_path:
            cv2.imwrite(output_path, frame)
            return True
        return frame

    except Exception as e:
        logger.error(f"抽取视频封面失败: {video_path}, error={str(e)}", exc_info=True)
        return None if output_path is None else False


def _resolve_srs_container_path_to_host(local_path: str) -> str:
    """将 SRS 回调中的容器内路径解析为当前进程可访问的宿主机路径。

    SRS 侧 dvr 文件路径通常为容器视角（如 /data/playbacks/...）。compose 约定宿主机 /data 映射为容器
    /data。若 VIDEO 在宿主机直接运行且本机尚未挂载 /data，则需把前缀 /data 映射到 SRS_HOST_DATA_ROOT
    （默认与约定一致为 /data；可通过环境变量覆盖）。若原路径已存在（如在 VIDEO 容器内已挂载 /data），则保持不变。
    """
    if not local_path:
        return local_path
    container_root = (os.getenv("SRS_CONTAINER_DATA_ROOT") or "/data").rstrip("/\\")
    try:
        p = os.path.normpath(local_path)
    except Exception:
        return local_path
    if not (p == container_root or p.startswith(container_root + os.sep)):
        return local_path
    if os.path.lexists(p):
        return local_path
    host_root = (os.getenv("SRS_HOST_DATA_ROOT") or "").strip()
    if not host_root:
        host_root = "/data"
    else:
        host_root = os.path.expanduser(os.path.expandvars(host_root))
    host_root = os.path.normpath(host_root)
    try:
        rel = os.path.relpath(p, container_root)
    except ValueError:
        return local_path
    return os.path.join(host_root, rel)


@camera_bp.route('/callback/on_dvr', methods=['POST'])
def on_dvr_callback():
    """SRS 录像生成回调（兼容旧路径 /video/camera/callback/on_dvr）。

    MEDIA_UPLOAD_MODE=kafka 时仅入队 Kafka；否则同步走 dvr_upload_service。
    集群 Hook 推荐使用 /video/media/hook/srs/on_dvr。
    """
    from app.services.dvr_device_resolver import resolve_stream_identity_from_hook
    from app.services.dvr_upload_service import process_dvr_event
    from app.services.media_kafka_service import (
        build_event_from_srs_hook,
        enqueue_srs_dvr_hook,
        is_hybrid_upload_mode,
        is_kafka_upload_mode,
    )

    try:
        data = request.get_json(silent=True) or {}
        if not data:
            logger.warning("on_dvr回调：请求数据为空")
            return jsonify({'code': 0, 'msg': None})
        if not data.get('stream') and not data.get('file'):
            return jsonify({'code': 0, 'msg': None})
        task_id, device_id, _ = resolve_stream_identity_from_hook(
            data.get('stream', ''), data.get('file', '')
        )
        if is_kafka_upload_mode():
            enqueue_srs_dvr_hook(data, device_id=device_id, task_id=task_id)
            if not is_hybrid_upload_mode():
                return jsonify({'code': 0, 'msg': None})
        event = build_event_from_srs_hook(data, device_id=device_id, task_id=task_id)
        if is_hybrid_upload_mode() or not is_kafka_upload_mode():
            process_dvr_event(event)
        return jsonify({'code': 0, 'msg': None})
    except Exception as e:
        logger.error(f"on_dvr回调处理失败: {str(e)}", exc_info=True)
        return jsonify({'code': 0, 'msg': None})


# legacy on_dvr 同步上传逻辑已迁移至 app.services.dvr_upload_service


# ------------------------- 设备目录管理接口 -------------------------
@camera_bp.route('/directory/list', methods=['GET'])
def list_directories():
    """查询目录列表（树形结构）"""
    try:
        from app.services.gb28181_sync_service import (
            ensure_directory_layout,
            sync_gb28181_channels_to_devices,
        )
        from sqlalchemy import func

        ensure_directory_layout()
        try:
            sync_gb28181_channels_to_devices(strict=False)
        except Exception as e:
            logger.warning(f'目录列表加载前国标同步失败: {e}')

        count_rows = (
            db.session.query(Device.directory_id, func.count(Device.id))
            .group_by(Device.directory_id)
            .all()
        )
        device_count_by_dir = {dir_id: cnt for dir_id, cnt in count_rows if dir_id is not None}

        def build_tree(parent_id=None):
            """递归构建目录树"""
            directories = DeviceDirectory.query.filter_by(parent_id=parent_id).order_by(
                DeviceDirectory.sort_order, DeviceDirectory.id
            ).all()
            result = []
            for directory in directories:
                directory_dict = {
                    'id': directory.id,
                    'name': directory.name,
                    'parent_id': directory.parent_id,
                    'description': directory.description,
                    'sort_order': directory.sort_order,
                    'snap_save_time': getattr(directory, 'snap_save_time', 1),
                    'record_save_time': getattr(directory, 'record_save_time', 1),
                    'is_default': camera_service.is_default_directory(directory),
                    'device_count': device_count_by_dir.get(directory.id, 0),
                    'created_at': directory.created_at.isoformat() if directory.created_at else None,
                    'updated_at': directory.updated_at.isoformat() if directory.updated_at else None,
                    'children': build_tree(directory.id),
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


def _device_monitor_tree_node(device, nvr_by_ip=None):
    """分屏监控树中的设备节点（仅含播放与展示所需字段）。"""
    from app.services.nvr_service import infer_nvr_link_from_source
    from app.services.stream_url_sync_service import resolve_device_stream_urls

    d = _to_dict(device)
    rtmp_stream, http_stream, ai_rtmp_stream, ai_http_stream = resolve_device_stream_urls(device)
    source = (d.get('source') or '').strip()
    is_gb28181 = source.lower().startswith('gb28181://')
    device_kind = d.get('device_kind') or ('gb28181' if is_gb28181 else 'direct')
    nvr_id = d.get('nvr_id')
    nvr_channel = int(d.get('nvr_channel') or 0)
    nvr = d.get('nvr') if isinstance(d.get('nvr'), dict) else None
    if not nvr_id and nvr and nvr.get('id'):
        nvr_id = nvr.get('id')
    if not nvr_id and not is_gb28181 and source:
        inferred_id, inferred_ch = infer_nvr_link_from_source(source, nvr_by_ip=nvr_by_ip)
        if inferred_id:
            nvr_id = inferred_id
            if not nvr_channel and inferred_ch:
                nvr_channel = inferred_ch
            device_kind = 'nvr_channel'
    elif device_kind == 'direct' and nvr_id:
        device_kind = 'nvr_channel'
    return {
        'type': 'device',
        'id': d['id'],
        'name': d.get('name') or d['id'],
        'http_stream': http_stream or d.get('http_stream'),
        'rtmp_stream': rtmp_stream or d.get('rtmp_stream'),
        'ai_http_stream': ai_http_stream or d.get('ai_http_stream'),
        'ai_rtmp_stream': ai_rtmp_stream or d.get('ai_rtmp_stream'),
        'online': d.get('online'),
        'directory_id': d.get('directory_id'),
        'device_kind': device_kind,
        'source': source or None,
        'nvr_id': nvr_id,
        'nvr_channel': nvr_channel,
        'nvr_label': d.get('nvr_label'),
    }


@camera_bp.route('/directory/monitor-tree', methods=['GET'])
def get_directory_monitor_tree():
    """分屏监控用目录设备树：目录嵌套 + 各目录下设备（未分组设备已归入默认分组）。"""
    try:
        from app.services.gb28181_sync_service import (
            ensure_directory_layout,
            sync_gb28181_channels_to_devices,
        )
        from app.services.nvr_service import build_nvr_ip_index

        ensure_directory_layout()
        # 默认跳过 WVP 全量同步，避免设备多时接口超时；手动「刷新」走 sync-gb28181
        skip_sync = request.args.get('skip_sync', '1').lower() in ('1', 'true', 'yes')
        if not skip_sync:
            try:
                sync_gb28181_channels_to_devices(strict=False)
            except Exception as e:
                logger.warning(f'分屏监控树加载前国标同步失败: {e}')
        nvr_by_ip = build_nvr_ip_index()

        def build_tree(parent_id=None):
            directories = DeviceDirectory.query.filter_by(parent_id=parent_id).order_by(
                DeviceDirectory.sort_order, DeviceDirectory.id
            ).all()
            result = []
            for directory in directories:
                devices = Device.query.filter_by(directory_id=directory.id).order_by(
                    Device.updated_at.desc()
                ).all()
                result.append({
                    'type': 'directory',
                    'id': directory.id,
                    'name': directory.name,
                    'parent_id': directory.parent_id,
                    'sort_order': directory.sort_order,
                    'snap_save_time': getattr(directory, 'snap_save_time', 1),
                    'record_save_time': getattr(directory, 'record_save_time', 1),
                    'is_default': camera_service.is_default_directory(directory),
                    'device_count': len(devices),
                    'children': build_tree(directory.id),
                    'devices': [_device_monitor_tree_node(d, nvr_by_ip) for d in devices],
                })
            return result

        tree = build_tree()

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'tree': tree,
                'unassigned_devices': [],
            },
        })
    except Exception as e:
        logger.error(f'获取分屏监控树失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'获取分屏监控树失败: {str(e)}'}), 500


@camera_bp.route('/directory/validate-json', methods=['POST'])
def validate_directory_json():
    """校验设备目录 JSON（结构、禁止默认分组、摄像头不重复）。"""
    try:
        from app.services.directory_json_sync_service import (
            DirectoryJsonError,
            parse_directory_json_payload,
            validate_directory_json_tree,
        )

        data = request.get_json()
        if data is None:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        tree = parse_directory_json_payload(data)
        validate_directory_json_tree(tree)
        return jsonify({'code': 0, 'msg': '校验通过'})
    except DirectoryJsonError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'校验目录 JSON 失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'校验目录 JSON 失败: {str(e)}'}), 500


@camera_bp.route('/directory/sync-json', methods=['POST'])
def sync_directory_json():
    """按 JSON 同步设备目录（服务端校验摄像头不重复后写入）。"""
    try:
        from app.services.directory_json_sync_service import (
            DirectoryJsonError,
            parse_directory_json_payload,
            sync_directory_from_json,
        )

        data = request.get_json()
        if data is None:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        tree = parse_directory_json_payload(data)
        sync_directory_from_json(tree)
        return jsonify({'code': 0, 'msg': '目录同步成功'})
    except DirectoryJsonError as e:
        db.session.rollback()
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f'同步目录 JSON 失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'同步目录 JSON 失败: {str(e)}'}), 500


@camera_bp.route('/directory/sync-gb28181', methods=['POST'])
def sync_gb28181_directory_devices():
    """手动从 WVP 同步国标通道到 device 表（默认分组）。"""
    try:
        from app.services.gb28181_sync_service import (
            Gb28181SyncError,
            backfill_gb28181_ai_stream_urls,
            sync_gb28181_channels_from_payload,
            sync_gb28181_channels_to_devices,
        )

        body = request.get_json(silent=True) or {}
        if isinstance(body, dict) and isinstance(body.get('data'), dict):
            inner = body['data']
            if 'channels' in inner:
                body = inner
        payload_channels = body.get('channels') if isinstance(body, dict) else None
        if isinstance(payload_channels, list) and len(payload_channels) > 0:
            stats = sync_gb28181_channels_from_payload(payload_channels, strict=True)
        else:
            stats = sync_gb28181_channels_to_devices(strict=True)
        created = int(stats.get('created') or 0)
        try:
            backfill_gb28181_ai_stream_urls()
        except Exception as e:
            logger.warning(f'国标设备 AI 推流地址回填异常: {e}')
        total_gb = Device.query.filter(Device.source.ilike('gb28181://%')).count()
        wvp_count = int(stats.get('wvp_device_count') or 0)
        channels_seen = int(stats.get('channels_seen') or 0)
        msg = '国标设备同步成功'
        if wvp_count > 0 and total_gb == 0:
            msg = (
                f'WVP 发现 {wvp_count} 个国标设备、解析 {channels_seen} 个通道，'
                '但未写入设备库，请检查 VIDEO 日志与数据库'
            )
        elif wvp_count == 0:
            msg = '未从 WVP 拉取到国标设备，请检查 GATEWAY_URL / GB28181_SERVICE_URL 与 WVP 服务'
        return jsonify({
            'code': 0,
            'msg': msg,
            'data': {
                'created': created,
                'total_gb_devices': total_gb,
                'wvp_device_count': wvp_count,
                'channels_seen': channels_seen,
                'api_base': stats.get('api_base'),
                'upsert_errors': stats.get('upsert_errors') or [],
            },
        })
    except Gb28181SyncError as e:
        logger.error(f'同步国标设备失败: {e}')
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'同步国标设备失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'同步国标设备失败: {str(e)}'}), 500


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
        if name == camera_service.DEFAULT_DIRECTORY_NAME and not parent_id:
            return jsonify({'code': 400, 'msg': '「默认分组」为系统保留名称，请使用其他目录名'}), 400
        
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
        directory = DeviceDirectory.query.get(directory_id)
        if not directory:
            return jsonify({'code': 400, 'msg': f'目录不存在: ID={directory_id}'}), 400
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400

        if camera_service.is_default_directory(directory):
            if 'name' in data and data.get('name', '').strip() != directory.name:
                return jsonify({'code': 400, 'msg': '默认分组不可重命名'}), 400
            if 'parent_id' in data and data.get('parent_id') != directory.parent_id:
                return jsonify({'code': 400, 'msg': '默认分组不可移动'}), 400
        
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

        propagated = {}
        try:
            if 'snap_save_time' in data:
                from app.services.space_save_time_service import (
                    update_directory_save_time, SPACE_KIND_SNAP,
                )
                _, snap_updated = update_directory_save_time(
                    directory_id, SPACE_KIND_SNAP, data.get('snap_save_time'), commit=False,
                )
                propagated['snap_updated'] = snap_updated
            if 'record_save_time' in data:
                from app.services.space_save_time_service import (
                    update_directory_save_time, SPACE_KIND_RECORD,
                )
                _, record_updated = update_directory_save_time(
                    directory_id, SPACE_KIND_RECORD, data.get('record_save_time'), commit=False,
                )
                propagated['record_updated'] = record_updated
        except ValueError as ve:
            db.session.rollback()
            return jsonify({'code': 400, 'msg': str(ve)}), 400
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'msg': '目录更新成功',
            'data': {
                'id': directory.id,
                'name': directory.name,
                'parent_id': directory.parent_id,
                'description': directory.description,
                'sort_order': directory.sort_order,
                'snap_save_time': getattr(directory, 'snap_save_time', 1),
                'record_save_time': getattr(directory, 'record_save_time', 1),
                **propagated,
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
        directory = DeviceDirectory.query.get(directory_id)
        if not directory:
            return jsonify({'code': 400, 'msg': f'目录不存在: ID={directory_id}'}), 400

        if camera_service.is_default_directory(directory):
            return jsonify({'code': 400, 'msg': '默认分组不可删除'}), 400
        
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
        directory = DeviceDirectory.query.get(directory_id)
        if not directory:
            return jsonify({'code': 400, 'msg': f'目录不存在: ID={directory_id}'}), 400

        if camera_service.is_default_directory(directory):
            from app.services.gb28181_sync_service import sync_gb28181_channels_to_devices

            try:
                sync_gb28181_channels_to_devices(strict=False)
            except Exception as e:
                logger.warning(f'默认分组设备列表加载前国标同步失败: {e}')

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
        
        # 确保当前页的设备都有对应的抓拍空间和录像空间
        for device in pagination.items:
            try:
                camera_service.ensure_device_spaces(device.id)
            except Exception as e:
                logger.warning(f'检查设备 {device.id} 空间时出错: {str(e)}')
        
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
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'code': 400, 'msg': f'设备不存在: ID={device_id}'}), 400
        data = request.get_json()
        
        # 检查参数是否存在（兼容处理：允许directory_id为None/null来解除关联）
        if 'directory_id' not in data:
            return jsonify({'code': 400, 'msg': 'directory_id参数不能为空'}), 400
        
        directory_id = data.get('directory_id')
        
        # 如果directory_id为None、null或0，移回默认分组
        if directory_id is None or directory_id == 0:
            device.directory_id = camera_service.get_or_create_default_directory().id
        else:
            # 验证目录是否存在
            directory = DeviceDirectory.query.get(directory_id)
            if not directory:
                return jsonify({'code': 400, 'msg': '目录不存在'}), 400
            device.directory_id = directory_id

        from app.services.space_save_time_service import sync_device_spaces_to_directory
        sync_device_spaces_to_directory(device.id, device.directory_id)
        
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
        directory = DeviceDirectory.query.get(directory_id)
        if not directory:
            return jsonify({'code': 400, 'msg': f'目录不存在: ID={directory_id}'}), 400
        
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


@camera_bp.route('/device/conflicts', methods=['GET'])
def get_device_conflicts():
    """获取正在使用的摄像头ID列表（用于推流转发或算法任务）"""
    try:
        task_type = request.args.get('task_type', '').strip()  # 'stream_forward' 或 'algorithm'
        
        conflict_device_ids = set()
        
        if task_type == 'stream_forward':
            # 获取所有正在运行的算法任务使用的摄像头
            running_algorithm_tasks = AlgorithmTask.query.filter(
                and_(
                    AlgorithmTask.is_enabled == True,
                    AlgorithmTask.run_status == 'running'
                )
            ).all()
            
            for task in running_algorithm_tasks:
                if task.devices:
                    for device in task.devices:
                        conflict_device_ids.add(device.id)
        elif task_type == 'algorithm':
            # 获取所有正在运行的推流转发任务使用的摄像头（只根据 is_enabled=True 判断）
            running_stream_forward_tasks = StreamForwardTask.query.filter(
                StreamForwardTask.is_enabled == True
            ).all()
            
            for task in running_stream_forward_tasks:
                if task.devices:
                    for device in task.devices:
                        conflict_device_ids.add(device.id)
        else:
            # 获取所有正在使用的摄像头（推流转发和算法任务）
            running_algorithm_tasks = AlgorithmTask.query.filter(
                and_(
                    AlgorithmTask.is_enabled == True,
                    AlgorithmTask.run_status == 'running'
                )
            ).all()
            
            running_stream_forward_tasks = StreamForwardTask.query.filter(
                StreamForwardTask.is_enabled == True
            ).all()
            
            for task in running_algorithm_tasks:
                if task.devices:
                    for device in task.devices:
                        conflict_device_ids.add(device.id)
            
            for task in running_stream_forward_tasks:
                if task.devices:
                    for device in task.devices:
                        conflict_device_ids.add(device.id)
        
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': list(conflict_device_ids)
        })
    except Exception as e:
        logger.error(f'获取摄像头冲突列表失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500
