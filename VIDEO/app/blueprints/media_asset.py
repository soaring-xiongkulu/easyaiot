"""录像策略、统一媒体资产索引和安全播放路由。"""
import hashlib
import hmac
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import requests
from flask import Blueprint, Response, jsonify, redirect, request, send_file, stream_with_context

from minio import Minio

from models import Alert, db, Device, MediaAsset
from app.services.media_asset_service import (
    get_or_default_policy,
    query_assets,
    report_assets,
    parse_timestamp,
    upsert_media_asset,
    update_recording_policy,
)
from app.utils.media_path_security import resolve_allowed_media_file
from app.utils.node_client import get_node


media_asset_bp = Blueprint('media_asset', __name__)
logger = logging.getLogger(__name__)


def _internal_token_valid() -> bool:
    expected = (os.getenv('MEDIA_INTERNAL_TOKEN') or '').strip()
    provided = (request.headers.get('X-Media-Internal-Token') or '').strip()
    return bool(expected and provided and hmac.compare_digest(expected, provided))


def _internal_node_id():
    if not _internal_token_valid():
        return None
    try:
        return int(request.headers.get('X-Node-Id') or '')
    except (TypeError, ValueError):
        return None


def _direct_play_signature(asset_id: str, expires: int) -> str:
    secret = (os.getenv('MEDIA_INTERNAL_TOKEN') or '').strip()
    if not secret:
        return ''
    message = f'{asset_id}:{expires}'.encode('utf-8')
    return hmac.new(secret.encode('utf-8'), message, hashlib.sha256).hexdigest()


def _direct_play_token_valid(asset_id: str) -> bool:
    try:
        expires = int(request.args.get('expires') or 0)
    except (TypeError, ValueError):
        return False
    if expires < int(time.time()) or expires > int(time.time()) + 600:
        return False
    provided = (request.args.get('signature') or '').strip()
    expected = _direct_play_signature(asset_id, expires)
    return bool(expected and provided and hmac.compare_digest(expected, provided))


def _effective_storage(device):
    if not device.ingress_node_id:
        return {'mode': 'central_shared', 'state': 'active', 'node_id': None}
    try:
        node = get_node(int(device.ingress_node_id))
        return {
            'mode': node.get('recordingStorageMode') or 'central_shared',
            'state': node.get('recordingStorageState') or 'active',
            'generation': node.get('recordingStorageGeneration') or 1,
            'node_id': device.ingress_node_id,
        }
    except Exception as exc:
        logger.warning('读取设备 %s 的节点录像模式失败: %s', device.id, exc)
        return {'mode': 'unknown', 'state': 'unavailable', 'node_id': device.ingress_node_id}


@media_asset_bp.route('/recording/policies/<device_id>', methods=['GET'])
def get_policy(device_id):
    try:
        policy = get_or_default_policy(device_id)
        payload = policy.to_dict()
        payload['effective_storage'] = _effective_storage(Device.query.get(device_id))
        return jsonify({'code': 0, 'msg': 'success', 'data': payload})
    except ValueError as exc:
        return jsonify({'code': 404, 'msg': str(exc)}), 404


@media_asset_bp.route('/recording/policies/<device_id>', methods=['PUT'])
def put_policy(device_id):
    try:
        device = Device.query.get(device_id)
        if not device:
            raise ValueError(f'设备不存在: {device_id}')
        effective = _effective_storage(device)
        if effective['mode'] == 'unknown' or effective['state'] not in ('active',):
            return jsonify({'code': 409, 'msg': '接入节点录像存储配置尚未生效，请稍后再保存设备录像策略'}), 409
        policy = update_recording_policy(device_id, request.get_json(silent=True) or {})
        payload = policy.to_dict()
        payload['effective_storage'] = effective
        return jsonify({'code': 0, 'msg': '录像策略已更新', 'data': payload})
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'code': 400, 'msg': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        logger.exception('更新设备录像策略失败')
        return jsonify({'code': 500, 'msg': str(exc)}), 500


@media_asset_bp.route('/recording/assets', methods=['GET'])
def list_assets():
    try:
        result = query_assets(
            device_id=request.args.get('device_id'),
            begin=request.args.get('begin'),
            end=request.args.get('end'),
            asset_type=request.args.get('asset_type'),
            status=request.args.get('status'),
            page_no=request.args.get('pageNo', 1),
            page_size=request.args.get('pageSize', 100),
        )
        node_cache = {}
        for item in result['items']:
            storage_node_id = item.get('storage_node_id')
            if item.get('storage_scope') != 'edge' or storage_node_id is None:
                item['availability'] = 'online'
                continue
            if storage_node_id not in node_cache:
                try:
                    node_cache[storage_node_id] = get_node(int(storage_node_id)).get('status') == 'online'
                except Exception:
                    node_cache[storage_node_id] = False
            item['availability'] = 'online' if node_cache[storage_node_id] else 'node_offline'
        return jsonify({'code': 0, 'msg': 'success', 'data': result['items'], 'total': result['total']})
    except ValueError as exc:
        return jsonify({'code': 400, 'msg': str(exc)}), 400


@media_asset_bp.route('/internal/media/assets/report-batch', methods=['POST'])
def report_asset_batch():
    node_id = _internal_node_id()
    if node_id is None:
        return jsonify({'code': 403, 'msg': '节点媒体上报身份无效'}), 403
    if request.content_length and request.content_length > 2 * 1024 * 1024:
        return jsonify({'code': 413, 'msg': '批量上报请求不能超过 2 MiB'}), 413
    data = request.get_json(silent=True) or {}
    items = data.get('items') or []
    if not isinstance(items, list) or not items or len(items) > 500:
        return jsonify({'code': 400, 'msg': 'items 必须包含 1～500 条资产'}), 400
    try:
        get_node(node_id)
        results = report_assets(items, node_id)
        return jsonify({'code': 0, 'msg': 'success', 'data': results})
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'code': 400, 'msg': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        logger.exception('边缘资产批量上报失败 node=%s', node_id)
        return jsonify({'code': 503, 'msg': str(exc)}), 503


@media_asset_bp.route('/internal/media/events/report-batch', methods=['POST'])
def report_edge_events():
    """边缘事件可靠补报；与 Kafka 通知链路并行，按 correlation_id 幂等。"""
    node_id = _internal_node_id()
    if node_id is None:
        return jsonify({'code': 403, 'msg': '节点事件上报身份无效'}), 403
    data = request.get_json(silent=True) or {}
    items = data.get('items') or []
    if not isinstance(items, list) or not items or len(items) > 500:
        return jsonify({'code': 400, 'msg': 'items 必须包含 1～500 条事件'}), 400
    try:
        from app.services.alert_service import create_alert
        results = []
        for raw in items:
            event = dict(raw or {})
            device_id = str(event.get('device_id') or '').strip()
            _validate_node_device(node_id, device_id)
            # 边缘绝对路径永不进入中心事件表，媒体由 asset_id 完成回调关联。
            event['image_path'] = None
            event['image_url'] = None
            event['record_path'] = None
            event['edge_node_id'] = node_id
            event.pop('_edge_image_asset_id', None)
            row = create_alert(event)
            results.append({'correlation_id': event.get('correlation_id'), 'alert_id': row.get('id')})
        return jsonify({'code': 0, 'msg': 'success', 'data': results})
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'code': 400, 'msg': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        logger.exception('边缘事件批量补报失败 node=%s', node_id)
        return jsonify({'code': 503, 'msg': str(exc)}), 503


def _event_minio_client():
    endpoint = (os.getenv('MINIO_UPLOAD_ENDPOINT') or os.getenv('MINIO_ENDPOINT') or 'localhost:9000').strip()
    endpoint = endpoint.removeprefix('http://').removeprefix('https://').rstrip('/')
    secure = (os.getenv('MINIO_UPLOAD_SECURE') or os.getenv('MINIO_SECURE') or 'false').lower() == 'true'
    return Minio(
        endpoint,
        access_key=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
        secret_key=os.getenv('MINIO_SECRET_KEY', ''),
        secure=secure,
    )


def _validate_node_device(node_id: int, device_id: str):
    get_node(node_id)
    device = Device.query.get(device_id)
    if not device:
        raise ValueError(f'设备不存在: {device_id}')
    if device.ingress_node_id is not None and int(device.ingress_node_id) != node_id:
        raise ValueError('节点只能上传其接入设备的事件媒体')
    return device


@media_asset_bp.route('/internal/media/assets/upload-ticket', methods=['POST'])
def create_event_upload_ticket():
    """签发最长 5 分钟的事件媒体 MinIO PUT 地址，边缘无需保存 MinIO 凭证。"""
    node_id = _internal_node_id()
    if node_id is None:
        return jsonify({'code': 403, 'msg': '节点媒体上传身份无效'}), 403
    data = request.get_json(silent=True) or {}
    asset_type = str(data.get('asset_type') or '').strip().lower()
    if asset_type not in ('alert_image', 'event_clip'):
        return jsonify({'code': 400, 'msg': '上传凭证仅支持 alert_image/event_clip'}), 400
    try:
        device_id = str(data.get('device_id') or '').strip()
        _validate_node_device(node_id, device_id)
        asset_id = str(data.get('asset_id') or '')
        suffix = Path(str(data.get('filename') or '')).suffix.lower()
        allowed_suffixes = {'.jpg', '.jpeg', '.png', '.webp'} if asset_type == 'alert_image' else {'.mp4', '.flv'}
        if suffix not in allowed_suffixes:
            suffix = '.jpg' if asset_type == 'alert_image' else '.mp4'
        bucket = (os.getenv('EVENT_MEDIA_BUCKET') or 'event-media').strip()
        day = datetime.now(timezone.utc).strftime('%Y/%m/%d')
        object_key = f'events/{node_id}/{device_id}/{day}/{asset_id}{suffix}'
        asset = upsert_media_asset({
            'asset_id': asset_id,
            'asset_type': asset_type,
            'device_id': device_id,
            'source_node_id': node_id,
            'storage_scope': 'central',
            'storage_backend': 'minio',
            'bucket_name': bucket,
            'object_key': object_key,
            'status': 'uploading',
            'start_time': data.get('start_time') or data.get('event_time'),
            'end_time': data.get('end_time'),
            'duration_ms': data.get('duration_ms'),
            'file_size': data.get('file_size'),
            'content_type': data.get('content_type'),
            'checksum': data.get('checksum'),
        }, authenticated_node_id=node_id)
        client = _event_minio_client()
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
        upload_url = client.presigned_put_object(bucket, object_key, expires=timedelta(minutes=5))
        return jsonify({'code': 0, 'msg': 'success', 'data': {
            'asset_id': asset.id,
            'upload_url': upload_url,
            'expires_in': 300,
        }})
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'code': 400, 'msg': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        logger.exception('签发事件媒体上传凭证失败 node=%s', node_id)
        return jsonify({'code': 503, 'msg': str(exc)}), 503


def _link_completed_event_asset(asset, data):
    correlation_id = str(data.get('correlation_id') or '').strip()
    alert = Alert.query.filter_by(correlation_id=correlation_id).first() if correlation_id else None
    if alert is None and data.get('event_time'):
        event_time = parse_timestamp(data.get('event_time'))
        if event_time is not None:
            # Alert 的历史时区写法混合，用宽窗口再按设备匹配作兼容。
            begin = event_time - timedelta(minutes=5)
            end = event_time + timedelta(minutes=5)
            alert = (Alert.query.filter(Alert.device_id == asset.device_id,
                                        Alert.time >= begin, Alert.time <= end)
                     .order_by(Alert.time.desc()).first())
    if alert is None:
        return False
    asset.alert_id = alert.id
    play_url = f'/video/media/assets/{asset.id}/content'
    if asset.asset_type == 'alert_image':
        alert.image_asset_id = asset.id
        alert.image_url = play_url
    else:
        alert.record_asset_id = asset.id
        alert.record_path = play_url
    return True


@media_asset_bp.route('/internal/media/assets/upload-complete', methods=['POST'])
def complete_event_upload():
    node_id = _internal_node_id()
    if node_id is None:
        return jsonify({'code': 403, 'msg': '节点媒体上传身份无效'}), 403
    data = request.get_json(silent=True) or {}
    try:
        asset = MediaAsset.query.get(str(data.get('asset_id') or ''))
        if not asset or asset.source_node_id is None or int(asset.source_node_id) != node_id:
            return jsonify({'code': 404, 'msg': '上传资产不存在'}), 404
        stat = _event_minio_client().stat_object(asset.bucket_name, asset.object_key)
        asset.status = 'ready'
        asset.file_size = stat.size
        asset.etag = stat.etag
        asset.updated_at = datetime.now(timezone.utc)
        linked = _link_completed_event_asset(asset, data)
        db.session.commit()
        return jsonify({'code': 0, 'msg': 'success', 'data': {'asset_id': asset.id, 'linked': linked}})
    except Exception as exc:
        db.session.rollback()
        logger.exception('确认事件媒体上传失败 node=%s', node_id)
        return jsonify({'code': 503, 'msg': str(exc)}), 503


@media_asset_bp.route('/internal/edge-media/health', methods=['GET'])
def edge_media_health():
    if not _internal_token_valid():
        return jsonify({'code': 403, 'msg': '边缘媒体访问令牌无效'}), 403
    from app.services.edge_media_spool_service import spool_status
    root = os.path.realpath(os.path.expanduser(
        os.getenv('EDGE_RECORDING_ROOT') or os.getenv('MEDIA_HOST_DATA_ROOT') or '/data/local-storage'
    ))
    try:
        stat = os.statvfs(root)
        storage = {
            'root_ready': os.path.isdir(root) and os.access(root, os.W_OK),
            'total_bytes': stat.f_blocks * stat.f_frsize,
            'free_bytes': stat.f_bavail * stat.f_frsize,
        }
    except OSError as exc:
        storage = {'root_ready': False, 'error': str(exc)}
    return jsonify({
        'code': 0,
        'msg': 'success',
        'data': {
            'mode': os.getenv('RECORDING_STORAGE_MODE', 'central_shared'),
            'generation': int(os.getenv('RECORDING_STORAGE_GENERATION') or 1),
            'storage': storage,
            'spool': spool_status(),
        },
    })


@media_asset_bp.route('/internal/edge-media/spool/flush', methods=['POST'])
def edge_media_flush():
    if not _internal_token_valid():
        return jsonify({'code': 403, 'msg': '边缘媒体访问令牌无效'}), 403
    from app.services.edge_storage_maintenance_service import run_edge_maintenance_cycle
    return jsonify({'code': 0, 'msg': 'success', 'data': run_edge_maintenance_cycle()})


def _asset_or_error(asset_id):
    asset = MediaAsset.query.get(asset_id)
    if not asset:
        return None, (jsonify({'code': 404, 'msg': '媒体资产不存在'}), 404)
    if asset.status in ('pending', 'uploading', 'failed'):
        return None, (jsonify({'code': 409, 'msg': f'媒体资产尚未就绪: {asset.status}'}), 409)
    if asset.status == 'deleted':
        return None, (jsonify({'code': 410, 'msg': '媒体资产已删除或过期'}), 410)
    return asset, None


@media_asset_bp.route('/media/assets/<asset_id>/content', methods=['GET', 'HEAD'])
def asset_content(asset_id):
    asset, error = _asset_or_error(asset_id)
    if error:
        return error
    if asset.storage_scope == 'central' and asset.storage_backend == 'minio':
        prefix = quote(asset.object_key, safe='')
        return redirect(f'/api/v1/buckets/{asset.bucket_name}/objects/download?prefix={prefix}', code=302)
    if asset.storage_scope == 'central' and asset.storage_backend == 'local':
        try:
            root = os.getenv('MEDIA_HOST_DATA_ROOT', '/mnt/easyaiot-media')
            path = resolve_allowed_media_file(os.path.join(root, asset.object_key), extra_roots=[root])
            if path is None:
                raise FileNotFoundError(asset.object_key)
            return send_file(path, conditional=True, mimetype=asset.content_type)
        except (FileNotFoundError, ValueError, PermissionError):
            return jsonify({'code': 410, 'msg': '中心媒体文件不存在'}), 410
    policy = get_or_default_policy(asset.device_id)
    if policy.playback_route_mode == 'direct':
        direct_url = _direct_edge_asset_url(asset)
        if direct_url:
            return redirect(direct_url, code=302)
    # auto 默认经主节点代理，确保浏览器无法直达边缘网络时仍可播放。
    return _proxy_edge_asset(asset)


def _direct_edge_asset_url(asset):
    try:
        node = get_node(int(asset.storage_node_id))
        if node.get('status') != 'online':
            return None
        base = str(node.get('mediaPublicUrl') or '').strip().rstrip('/')
        if not base.startswith(('http://', 'https://')):
            return None
        expires = int(time.time()) + 300
        signature = _direct_play_signature(asset.id, expires)
        if not signature:
            return None
        return (f'{base}/video/internal/edge-media/assets/{asset.id}/content'
                f'?expires={expires}&signature={signature}')
    except Exception as exc:
        logger.warning('生成边缘资产直连地址失败 asset=%s: %s', asset.id, exc)
        return None


def _proxy_edge_asset(asset):
    try:
        node = get_node(int(asset.storage_node_id))
        if node.get('status') != 'online':
            return jsonify({'code': 503, 'msg': '边缘节点离线，录像暂不可播放'}), 503
        base = str(node.get('mediaPublicUrl') or '').strip().rstrip('/')
        if not base.startswith(('http://', 'https://')):
            return jsonify({'code': 503, 'msg': '边缘节点未配置可用的录像访问地址'}), 503
        url = f'{base}/video/internal/edge-media/assets/{asset.id}/content'
        headers = {'X-Media-Internal-Token': os.getenv('MEDIA_INTERNAL_TOKEN', '')}
        for name in ('Range', 'If-Range', 'If-Modified-Since'):
            if request.headers.get(name):
                headers[name] = request.headers[name]
        upstream = requests.request(
            request.method, url, headers=headers, stream=request.method == 'GET', timeout=(5, 60),
        )
        response_headers = {}
        for name in ('Content-Type', 'Content-Length', 'Content-Range', 'Accept-Ranges',
                     'Last-Modified', 'ETag'):
            if upstream.headers.get(name):
                response_headers[name] = upstream.headers[name]
        if request.method == 'HEAD':
            upstream.close()
            return Response(status=upstream.status_code, headers=response_headers)

        @stream_with_context
        def generate():
            try:
                yield from upstream.iter_content(chunk_size=1024 * 1024)
            finally:
                upstream.close()

        return Response(generate(), status=upstream.status_code, headers=response_headers)
    except requests.RequestException as exc:
        logger.warning('代理边缘资产失败 asset=%s node=%s: %s', asset.id, asset.storage_node_id, exc)
        return jsonify({'code': 503, 'msg': '边缘录像访问失败'}), 503


@media_asset_bp.route('/internal/edge-media/assets/<asset_id>/content', methods=['GET', 'HEAD'])
def edge_asset_content(asset_id):
    if not (_internal_token_valid() or _direct_play_token_valid(asset_id)):
        return jsonify({'code': 403, 'msg': '边缘媒体访问令牌无效'}), 403
    asset, error = _asset_or_error(asset_id)
    if error:
        return error
    if asset.storage_scope != 'edge' or asset.storage_backend != 'local':
        return jsonify({'code': 404, 'msg': '边缘本地资产不存在'}), 404
    try:
        root = os.getenv('EDGE_RECORDING_ROOT', '/data/local-storage')
        path = resolve_allowed_media_file(os.path.join(root, asset.object_key), extra_roots=[root])
        if path is None:
            raise FileNotFoundError(asset.object_key)
        return send_file(path, conditional=True, mimetype=asset.content_type)
    except FileNotFoundError:
        return jsonify({'code': 410, 'msg': '边缘媒体文件已不存在'}), 410
    except (ValueError, PermissionError):
        return jsonify({'code': 403, 'msg': '边缘媒体路径非法'}), 403
