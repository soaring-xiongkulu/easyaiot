"""NVR 记录与直连摄像头挂载关系（字段对齐 hiktools）。"""
from __future__ import annotations

import logging
import re
import time
from typing import Any
from urllib.parse import urlparse, quote

from models import Device, Nvr, db

logger = logging.getLogger(__name__)

_GENERIC_CAMERA_NAME = re.compile(r'^camera\s*0*\d+\s*$', re.IGNORECASE)


def _resolve_channel_display_name(
    raw_name: str | None,
    channel_id: int,
    nvr_ip: str,
    cam_ip: str = '',
) -> str:
    """将海康默认的 Camera 01 等重复名称替换为可区分名称。"""
    name = (raw_name or '').strip()
    if name and not _GENERIC_CAMERA_NAME.match(name):
        return name
    if cam_ip:
        return f'CH{channel_id}-{cam_ip}'
    return f'NVR-{nvr_ip}-CH{channel_id}'


def _refresh_generic_channel_names(nvr_id: int) -> None:
    """将库中仍为 Camera 01 等默认名的 NVR 通道改为可区分名称。"""
    nvr = Nvr.query.get(nvr_id)
    if not nvr:
        return
    nvr_ip = nvr.ip or ''
    changed = False
    for cam in Device.query.filter_by(nvr_id=nvr_id).all():
        ch = cam.nvr_channel or 0
        if ch <= 0:
            continue
        new_name = _resolve_channel_display_name(cam.name, ch, nvr_ip, (cam.ip or '').strip())
        if new_name != (cam.name or '').strip():
            cam.name = new_name
            changed = True
    if changed:
        db.session.commit()


def _ensure_nvr_stream_forward_task(nvr_id: int) -> None:
    """为 NVR 下全部 RTSP 挂载通道确保单一推流转发任务（更新/同步后调用）。"""
    try:
        from app.services.stream_forward_service import ensure_nvr_stream_forward_task
        ensure_nvr_stream_forward_task(nvr_id)
    except Exception as e:
        logger.warning(
            f'为 NVR {nvr_id} 自动创建/更新推流转发任务失败: {e}，不影响 NVR 保存',
        )


_VENDOR_LABELS = {
    'hikvision': '海康',
    'dahua': '大华',
    'huawei': '华为',
    'ezviz': '萤石',
    'xiaomi': '小米',
    'custom': '自定义',
}


def vendor_label(vendor: str | None) -> str:
    if not vendor:
        return ''
    return _VENDOR_LABELS.get(vendor, vendor)


def _camera_under_nvr_dict(cam: Device) -> dict[str, Any]:
    online = cam.channel_online
    online_text = '在线' if online is True else ('离线' if online is False else '—')
    return {
        'id': cam.id,
        'name': cam.name,
        'ip': cam.ip,
        'port': cam.port,
        'nvr_channel': cam.nvr_channel,
        'source': cam.source,
        'rtsp_url': cam.source,
        'rtmp_stream': cam.rtmp_stream,
        'http_stream': cam.http_stream,
        'ai_rtmp_stream': cam.ai_rtmp_stream,
        'ai_http_stream': cam.ai_http_stream,
        'rtsp_direct': cam.rtsp_direct,
        'model': cam.model,
        'serial': cam.serial_number,
        'serial_number': cam.serial_number,
        'mac': cam.mac,
        'manufacturer': cam.manufacturer,
        'online': cam.channel_online if cam.channel_online is not None else None,
        'online_text': online_text,
        'connection_status': cam.connection_status,
        'username': cam.username,
    }


def _nvr_to_dict(nvr: Nvr, *, include_cameras: bool = False) -> dict[str, Any]:
    sch = nvr.scheme or ('https' if (nvr.port or 80) in (443, 8443) else 'http')
    row: dict[str, Any] = {
        'id': nvr.id,
        'ip': nvr.ip,
        'port': nvr.port,
        'scheme': sch,
        'web_url': nvr.web_url,
        'username': nvr.username,
        'has_password': bool((nvr.password or '').strip()),
        'name': nvr.name,
        'device_name': nvr.name,
        'model': nvr.model,
        'vendor': nvr.vendor,
        'vendor_label': vendor_label(nvr.vendor),
        'serial_number': nvr.serial_number,
        'serial': nvr.serial_number,
        'firmware_version': nvr.firmware_version,
        'firmware': nvr.firmware_version,
        'device_type': nvr.device_type,
        'mac': nvr.mac,
        'rtsp_url': nvr.rtsp_url,
        'source': nvr.source,
        'rtsp_template': getattr(nvr, 'rtsp_template', None),
        'rtsp_port': getattr(nvr, 'rtsp_port', None),
    }
    cameras = list(nvr.cameras or [])
    if include_cameras:
        row['cameras'] = [_camera_under_nvr_dict(c) for c in cameras]
        row['camera_count'] = len(row['cameras'])
    else:
        row['camera_count'] = Device.query.filter_by(nvr_id=nvr.id).count()
    return row


def get_nvr(nvr_id: int, *, include_cameras: bool = False) -> dict[str, Any]:
    nvr = Nvr.query.get(nvr_id)
    if not nvr:
        raise ValueError(f'NVR {nvr_id} 不存在')
    return _nvr_to_dict(nvr, include_cameras=include_cameras)


def list_nvrs(*, include_cameras: bool = False) -> list[dict[str, Any]]:
    nvrs = Nvr.query.order_by(Nvr.ip, Nvr.id).all()
    return [_nvr_to_dict(n, include_cameras=include_cameras) for n in nvrs]


def _apply_nvr_fields(nvr: Nvr, info: dict[str, Any]) -> None:
    ip = (info.get('ip') or '').strip()
    if ip:
        nvr.ip = ip
    if 'port' in info and info.get('port') is not None:
        try:
            nvr.port = int(info.get('port') or 80)
        except (TypeError, ValueError):
            pass
    for field in (
        'username', 'password', 'name', 'model', 'vendor',
        'serial_number', 'firmware_version', 'device_type', 'mac',
        'scheme', 'rtsp_url', 'source', 'rtsp_template',
    ):
        if field not in info:
            continue
        val = info.get(field)
        if val is None:
            continue
        if isinstance(val, str) and val.strip() == '':
            continue
        setattr(nvr, field, val)
    if 'rtsp_port' in info and info.get('rtsp_port') is not None:
        try:
            nvr.rtsp_port = int(info.get('rtsp_port'))
        except (TypeError, ValueError):
            pass


def find_nvr_by_ip_port(ip: str, port: int | None = None) -> Nvr | None:
    """按 IP+端口查找 NVR，端口不匹配时回退到同 IP 首条记录。"""
    ip = (ip or '').strip()
    if not ip:
        return None
    try:
        p = int(port or 80)
    except (TypeError, ValueError):
        p = 80
    nvr = Nvr.query.filter_by(ip=ip, port=p).first()
    if nvr:
        return nvr
    return Nvr.query.filter_by(ip=ip).order_by(Nvr.id).first()


def merge_nvr_enum_credentials(
    ip: str,
    port: int,
    *,
    username: str | None,
    password: str | None,
    credentials: list[dict[str, Any]] | None,
) -> tuple[str | None, str | None, list[dict[str, Any]] | None]:
    """枚举通道前合并请求凭证与库中已登记 NVR 凭证（请求未填密码时使用库内值）。"""
    existing = find_nvr_by_ip_port(ip, port)
    user = (username or '').strip() or None
    pwd = password
    creds = list(credentials) if credentials else None

    if existing:
        if not user and existing.username:
            user = existing.username.strip() or None
        if (pwd is None or pwd == '') and existing.password:
            pwd = existing.password
        if existing.username and existing.password:
            pair = {'username': existing.username, 'password': existing.password}
            if creds is None:
                creds = [pair]
            elif not any(
                (c.get('username') or '').strip() == existing.username
                for c in creds
                if isinstance(c, dict)
            ):
                creds.insert(0, pair)

    if not user and not creds:
        return None, pwd, creds
    return user, pwd, creds


def get_or_create_nvr(info: dict[str, Any]) -> int:
    """按 id 或 IP+端口查找或创建 NVR，返回 nvr.id。"""
    ip = (info.get('ip') or '').strip()
    if not ip:
        raise ValueError('NVR IP 不能为空')
    try:
        port = int(info.get('port') or 80)
    except (TypeError, ValueError):
        port = 80

    raw_id = info.get('id')
    if raw_id is not None and raw_id != '':
        try:
            nvr_id = int(raw_id)
            nvr = Nvr.query.get(nvr_id)
            if nvr:
                conflict = Nvr.query.filter(
                    Nvr.ip == ip,
                    Nvr.port == port,
                    Nvr.id != nvr_id,
                ).first()
                if conflict:
                    raise ValueError(f'IP {ip}:{port} 已被其他 NVR 占用')
                _apply_nvr_fields(nvr, info)
                db.session.flush()
                return nvr.id
        except (TypeError, ValueError):
            pass

    nvr = Nvr.query.filter_by(ip=ip, port=port).first()
    if not nvr:
        nvr = Nvr.query.filter_by(ip=ip).order_by(Nvr.id).first()
    if not nvr:
        nvr = Nvr(ip=ip, port=port)
        db.session.add(nvr)

    _apply_nvr_fields(nvr, info)
    db.session.flush()
    return nvr.id


def delete_nvr(nvr_id: int) -> None:
    """删除 NVR 记录（挂载摄像头 nvr_id 由外键 SET NULL）。"""
    nvr = Nvr.query.get(nvr_id)
    if not nvr:
        raise ValueError(f'NVR {nvr_id} 不存在')
    db.session.delete(nvr)
    db.session.commit()


def batch_delete_nvrs(nvr_ids: list) -> dict:
    """批量删除 NVR，返回 deleted / failed / errors。"""
    if not nvr_ids:
        return {'deleted': 0, 'failed': 0, 'errors': []}

    deleted = 0
    errors: list[dict] = []
    seen = set()
    for raw_id in nvr_ids:
        try:
            nvr_id = int(raw_id)
        except (TypeError, ValueError):
            errors.append({'nvr_id': raw_id, 'msg': '无效的 NVR ID'})
            continue
        if nvr_id in seen:
            continue
        seen.add(nvr_id)
        try:
            delete_nvr(nvr_id)
            deleted += 1
        except ValueError as e:
            errors.append({'nvr_id': nvr_id, 'msg': str(e)})
        except Exception as e:
            logger.error(f'批量删除 NVR {nvr_id} 失败: {e}', exc_info=True)
            errors.append({'nvr_id': nvr_id, 'msg': str(e)})

    return {
        'deleted': deleted,
        'failed': len(errors),
        'errors': errors,
    }


def upsert_nvr(info: dict[str, Any]) -> dict[str, Any]:
    nvr_id = get_or_create_nvr(info)
    db.session.commit()
    _refresh_generic_channel_names(nvr_id)
    _ensure_nvr_stream_forward_task(nvr_id)
    return get_nvr(nvr_id, include_cameras=True)


def _vendor_to_camera_type(vendor: str | None) -> str:
    v = (vendor or '').strip().lower()
    if v in ('hikvision', '海康'):
        return 'hikvision'
    if v in ('dahua', '大华'):
        return 'dahua'
    return 'custom'


def _build_rtsp_from_template(
    template: str,
    *,
    ip: str,
    port: int,
    username: str,
    password: str,
    channel: int,
    subtype: int = 0,
) -> str:
    """根据自定义模板生成 RTSP URL。

    支持占位符：
      {username}  用户名
      {password}  密码
      {ip}        设备IP
      {port}      RTSP端口
      {channel}   通道号
      {subtype}   码流类型（0主码流 1子码流）
    """
    result = template
    result = result.replace('{username}', quote(username or '', safe=''))
    result = result.replace('{password}', quote(password or '', safe=''))
    result = result.replace('{ip}', ip)
    result = result.replace('{port}', str(port))
    result = result.replace('{channel}', str(channel))
    result = result.replace('{subtype}', str(subtype))

    if result.lower().startswith('rtsp://'):
        return result

    if result.startswith('/'):
        cred = ''
        if username or password:
            cred = f"{quote(username or '', safe='')}:{quote(password or '', safe='')}@"
        return f"rtsp://{cred}{ip}:{port}{result}"

    return result


def _resolve_channel_source(
    nvr: Nvr,
    ch: dict[str, Any],
    *,
    username: str,
    password: str,
    vendor: str | None,
    rtsp_template: str | None = None,
    rtsp_port: int | None = None,
) -> str | None:
    """按当前 NVR IP 生成经 NVR 取流的 RTSP，避免同步后仍残留旧 NVR 地址。"""
    try:
        channel_id = int(
            ch.get('channel_id') if ch.get('channel_id') is not None else ch.get('nvr_channel') or 0
        )
    except (TypeError, ValueError):
        return None
    if channel_id <= 0:
        return None

    rtsp_tmpl = rtsp_template or ch.get('rtsp_template') or getattr(nvr, 'rtsp_template', None)
    if rtsp_tmpl:
        rtsp_p = rtsp_port or ch.get('rtsp_port') or getattr(nvr, 'rtsp_port', None) or 554
        try:
            rtsp_p = int(rtsp_p)
        except (TypeError, ValueError):
            rtsp_p = 554
        return _build_rtsp_from_template(
            rtsp_tmpl,
            ip=nvr.ip or '',
            port=rtsp_p,
            username=username or nvr.username or '',
            password=password or nvr.password or '',
            channel=channel_id,
            subtype=0,
        )

    ch_rtsp = ch.get('rtsp_url') or ch.get('source')
    if ch_rtsp and isinstance(ch_rtsp, str) and ch_rtsp.strip():
        return ch_rtsp.strip()

    nvr_vendor = (ch.get('vendor') or vendor or nvr.vendor or 'hikvision').strip()
    from app.vendor.hiktools.core.models import Credential
    from app.vendor.hiktools.core.rtsp import build_nvr_channel_rtsp

    cred = Credential(username=username or nvr.username or '', password=password or nvr.password or '')
    return build_nvr_channel_rtsp(
        nvr_vendor,
        nvr.ip,
        channel_id,
        [cred],
        preferred=cred,
        channel_username=ch.get('username'),
    )


def _rtsp_source_host(source: str | None) -> str:
    return (urlparse(source or '').hostname or '').strip()


def _upsert_nvr_channel_device(
    nvr_id: int,
    nvr: Nvr,
    ch: dict[str, Any],
    *,
    username: str,
    password: str,
    vendor: str | None,
    rtsp_template: str | None = None,
    rtsp_port: int | None = None,
) -> bool:
    """将枚举通道直接关联到 NVR（仅写库，不 ONVIF、不连通性探测）。"""
    try:
        channel_id = int(
            ch.get('channel_id') if ch.get('channel_id') is not None else ch.get('nvr_channel') or 0
        )
    except (TypeError, ValueError):
        return False
    if channel_id <= 0:
        return False

    source = _resolve_channel_source(
        nvr, ch,
        username=username, password=password, vendor=vendor,
        rtsp_template=rtsp_template, rtsp_port=rtsp_port,
    )
    if not source:
        return False

    from app.services.camera_service import _generate_stream_urls, directory_id_for_new_device

    nvr_ip = nvr.ip or ''
    ch_vendor = ch.get('vendor') or vendor or nvr.vendor
    mfr = (vendor_label(ch_vendor) or ch_vendor or 'EasyAIoT').strip()
    model = (ch.get('model') or 'NVR-Channel').strip() or 'NVR-Channel'
    cam_ip = (ch.get('camera_ip') or ch.get('ip') or '').strip()
    name = _resolve_channel_display_name(ch.get('name'), channel_id, nvr_ip, cam_ip)
    try:
        cam_port = _normalize_ipc_display_port(int(ch.get('camera_port') or ch.get('port') or 554))
    except (TypeError, ValueError):
        cam_port = 554

    online = ch.get('online')
    conn = ch.get('connection_status') or ch.get('probe_error')
    rtsp_direct = ch.get('rtsp_direct')
    serial = ch.get('serial') or ch.get('serial_number') or ''

    from app.services.camera_service import find_existing_device_for_register

    existing = find_existing_device_for_register(
        ip=cam_ip,
        mac=(ch.get('mac') or '').strip(),
        serial_number=serial,
        nvr_id=nvr_id,
        nvr_channel=channel_id,
    )
    if existing:
        device_id = existing.id
        rtmp_stream, http_stream, ai_rtmp_stream, ai_http_stream = _generate_stream_urls(source, device_id)
        existing.nvr_id = int(nvr_id)
        existing.nvr_channel = channel_id
        if not existing.nvr_id:
            raise RuntimeError(f'通道 CH{channel_id} 关联 NVR 失败：nvr_id 为空')
        existing.name = name
        existing.source = source
        existing.rtmp_stream = rtmp_stream
        existing.http_stream = http_stream
        existing.ai_rtmp_stream = ai_rtmp_stream
        existing.ai_http_stream = ai_http_stream
        existing.ip = cam_ip
        existing.port = cam_port
        existing.username = username or nvr.username or ''
        existing.password = password if password is not None else (nvr.password or '')
        existing.manufacturer = mfr
        existing.model = model
        existing.serial_number = serial or existing.serial_number
        existing.mac = ch.get('mac') or existing.mac
        existing.rtsp_direct = rtsp_direct
        existing.channel_online = online
        existing.connection_status = conn
        return True

    device_id = str(time.time_ns())
    rtmp_stream, http_stream, ai_rtmp_stream, ai_http_stream = _generate_stream_urls(source, device_id)
    camera = Device(
        id=device_id,
        name=name,
        source=source,
        rtmp_stream=rtmp_stream,
        http_stream=http_stream,
        ai_rtmp_stream=ai_rtmp_stream,
        ai_http_stream=ai_http_stream,
        stream=0,
        ip=cam_ip,
        port=cam_port,
        username=username or nvr.username or '',
        password=password if password is not None else (nvr.password or ''),
        mac=ch.get('mac') or '',
        manufacturer=mfr,
        model=model,
        firmware_version=ch.get('firmware') or '',
        serial_number=serial,
        nvr_id=int(nvr_id),
        nvr_channel=channel_id,
        rtsp_direct=rtsp_direct,
        channel_online=online,
        connection_status=conn,
        directory_id=directory_id_for_new_device(),
    )
    if not camera.nvr_id:
        raise RuntimeError(f'通道 CH{channel_id} 创建失败：nvr_id 为空')
    db.session.add(camera)
    return True


def _link_channels_to_nvr(nvr_id: int, nvr_ip: str | None = None) -> int:
    """登记后兜底：RTSP 源指向本 NVR 但未写 nvr_id 的通道补全关联（不跨 NVR 抢占）。"""
    nvr = Nvr.query.get(nvr_id)
    if not nvr:
        return 0
    host = (nvr_ip or nvr.ip or '').strip()
    if not host:
        return 0
    fixed = 0
    for cam in Device.query.filter(Device.nvr_id.is_(None)).all():
        src = cam.source or ''
        if host not in src:
            continue
        if not is_nvr_channel_device(cam):
            continue
        cam.nvr_id = nvr_id
        fixed += 1
    return fixed


def bulk_register_nvr_channels(
    nvr_info: dict[str, Any],
    channels: list[dict[str, Any]],
    *,
    username: str = '',
    password: str = '',
    vendor: str | None = None,
    rtsp_template: str | None = None,
    rtsp_port: int | None = None,
) -> dict[str, Any]:
    """登记/更新 NVR，并按枚举结果批量关联通道（不逐台 ONVIF/连通性探测）。"""
    nvr_id = get_or_create_nvr(nvr_info)
    db.session.flush()
    nvr = Nvr.query.get(nvr_id)
    if not nvr:
        raise ValueError(f'NVR {nvr_id} 不存在')

    user = (username or nvr_info.get('username') or nvr.username or '').strip()
    pwd = password if password is not None else (nvr_info.get('password') or nvr.password or '')
    v = vendor or nvr_info.get('vendor') or nvr.vendor
    rtsp_tmpl = rtsp_template or nvr_info.get('rtsp_template') or getattr(nvr, 'rtsp_template', None)
    rtsp_p = rtsp_port or nvr_info.get('rtsp_port') or getattr(nvr, 'rtsp_port', None)
    if rtsp_p is not None:
        try:
            rtsp_p = int(rtsp_p)
        except (TypeError, ValueError):
            rtsp_p = None

    registered = 0
    skipped = 0
    errors: list[str] = []
    expected_channel_ids: set[int] = set()

    for ch in channels or []:
        try:
            ch_no = ch.get('channel_id', ch.get('nvr_channel', '?'))
            try:
                cid = int(
                    ch.get('channel_id') if ch.get('channel_id') is not None else ch.get('nvr_channel') or 0
                )
            except (TypeError, ValueError):
                cid = 0
            if cid > 0:
                expected_channel_ids.add(cid)
            if _upsert_nvr_channel_device(
                nvr_id, nvr, ch,
                username=user, password=pwd, vendor=v,
                rtsp_template=rtsp_tmpl, rtsp_port=rtsp_p,
            ):
                registered += 1
            else:
                skipped += 1
        except Exception as e:
            errors.append(f'CH{ch_no}: {e}')

    pruned = 0
    if expected_channel_ids:
        from models import DeviceDetectionRegion

        nvr_ip = (nvr.ip or '').strip()
        for cam in Device.query.filter_by(nvr_id=nvr_id).all():
            ch_no = int(cam.nvr_channel or 0)
            src_host = _rtsp_source_host(cam.source)
            stale_host = bool(nvr_ip and src_host and src_host != nvr_ip)
            if ch_no > 0 and ch_no in expected_channel_ids and not stale_host:
                continue
            for region in DeviceDetectionRegion.query.filter_by(device_id=cam.id).all():
                db.session.delete(region)
            db.session.delete(cam)
            pruned += 1
        if pruned:
            logger.info(f'NVR {nvr_id} 同步移除 {pruned} 路未挂载/旧地址通道')

    try:
        linked = _link_channels_to_nvr(nvr_id, nvr.ip)
        if linked:
            logger.info(f'NVR {nvr_id} 登记后补全 {linked} 条通道的 nvr_id')
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise RuntimeError(f'批量挂载提交失败: {e}') from e

    _ensure_nvr_stream_forward_task(nvr_id)
    result = get_nvr(nvr_id, include_cameras=True)
    result['register_stats'] = {
        'registered': registered,
        'skipped': skipped,
        'pruned': pruned,
        'errors': errors,
    }
    return result


def resolve_nvr_link(payload: dict[str, Any]) -> tuple[int | None, int]:
    """从注册/更新请求解析 nvr_id 与通道号。"""
    try:
        channel = int(payload.get('nvr_channel') if payload.get('nvr_channel') is not None else 0)
    except (TypeError, ValueError):
        channel = 0

    if 'nvr_id' in payload and payload.get('nvr_id') in (None, '', 0):
        return None, 0

    raw_id = payload.get('nvr_id')
    if raw_id is not None and raw_id != '' and raw_id != 0:
        try:
            return int(raw_id), channel
        except (TypeError, ValueError):
            pass

    nvr_obj = payload.get('nvr')
    if isinstance(nvr_obj, dict) and (nvr_obj.get('ip') or '').strip():
        return get_or_create_nvr(nvr_obj), channel

    nvr_ip = (payload.get('nvr_ip') or '').strip()
    if nvr_ip:
        nvr_id = get_or_create_nvr({
            'ip': nvr_ip,
            'port': payload.get('nvr_port', 80),
            'username': payload.get('nvr_username') or payload.get('username'),
            'password': payload.get('nvr_password') or payload.get('password'),
            'name': payload.get('nvr_name'),
            'model': payload.get('nvr_model'),
            'vendor': payload.get('nvr_vendor'),
            'serial_number': payload.get('nvr_serial'),
            'firmware_version': payload.get('nvr_firmware'),
            'device_type': payload.get('nvr_device_type'),
            'mac': payload.get('nvr_mac'),
            'scheme': payload.get('nvr_scheme'),
            'rtsp_url': payload.get('nvr_rtsp_url') or payload.get('rtsp_url'),
            'source': payload.get('nvr_source') or payload.get('source'),
        })
        return nvr_id, channel

    return None, channel


_WEB_PROBE_PORTS = frozenset({80, 443, 8000, 8443, 37777})


def _normalize_ipc_display_port(port: int | None) -> int:
    """NVR 枚举返回的 port 多为 IPC Web 端口，展示/存库用 RTSP 默认 554。"""
    try:
        p = int(port) if port is not None else 0
    except (TypeError, ValueError):
        return 554
    if p <= 0 or p in _WEB_PROBE_PORTS:
        return 554
    return p


def is_nvr_channel_device(camera: Device) -> bool:
    """是否 NVR 挂载通道（经 NVR/RTSP 取流，不应走单机 ONVIF）。"""
    if camera.nvr_id:
        return True
    ch = int(camera.nvr_channel or 0)
    model = (camera.model or '').strip()
    source = (camera.source or '').strip().lower()
    if ch > 0 and model == 'NVR-Channel':
        return True
    if model == 'NVR-Channel' and source.startswith('rtsp://'):
        if '/streaming/channels/' in source or 'channel=' in source:
            return True
    nvr_id, inferred_ch = infer_nvr_link_from_source(camera.source)
    if nvr_id and (ch > 0 or inferred_ch > 0):
        return True
    return False


def repair_nvr_channel_links(*, commit: bool = True) -> int:
    """将 nvr_id 因外键 SET NULL 等方式丢失的通道，按 RTSP 源重新关联到 NVR。"""
    nvr_by_ip = build_nvr_ip_index()
    fixed = 0
    q = Device.query.filter(Device.nvr_id.is_(None))
    for cam in q.all():
        if not is_nvr_channel_device(cam):
            continue
        nvr_id, inferred_ch = infer_nvr_link_from_source(cam.source, nvr_by_ip=nvr_by_ip)
        if not nvr_id:
            continue
        cam.nvr_id = nvr_id
        if inferred_ch and not int(cam.nvr_channel or 0):
            cam.nvr_channel = inferred_ch
        fixed += 1
    if fixed and commit:
        db.session.commit()
        logger.info(f'已修复 {fixed} 条 NVR 通道的 nvr_id 关联')
    return fixed


def build_nvr_ip_index() -> dict[str, int]:
    """NVR IP -> id，用于从 RTSP 源反查挂载关系。"""
    index: dict[str, int] = {}
    for nvr in Nvr.query.all():
        ip = (nvr.ip or '').strip()
        if ip and nvr.id:
            index[ip] = nvr.id
    return index


def infer_nvr_link_from_source(
    source: str | None,
    *,
    nvr_by_ip: dict[str, int] | None = None,
) -> tuple[int | None, int]:
    """
    从 RTSP 源推断 (nvr_id, nvr_channel)。
    海康 NVR：/Streaming/Channels/2301 -> 通道 23（stream_id // 100）。
    """
    text = (source or '').strip()
    if not text.lower().startswith('rtsp://'):
        return None, 0
    host = (urlparse(text).hostname or '').strip()
    if not host:
        return None, 0
    if nvr_by_ip is None:
        nvr_by_ip = build_nvr_ip_index()
    nvr_id = nvr_by_ip.get(host)
    if not nvr_id:
        return None, 0

    channel = 0
    m = re.search(r'/Streaming/Channels/(\d+)', text, re.I)
    if m:
        stream_id = int(m.group(1))
        channel = stream_id // 100 if stream_id >= 100 else stream_id
    else:
        m2 = re.search(r'[?&]channel=(\d+)', text, re.I)
        if m2:
            channel = int(m2.group(1))
    return nvr_id, channel


def nvr_fields_for_device(camera: Device) -> dict[str, Any]:
    """设备字典中附带的 NVR 摘要。"""
    if not camera.nvr_id:
        ch = camera.nvr_channel or 0
        if is_nvr_channel_device(camera):
            inferred_id, inferred_ch = infer_nvr_link_from_source(camera.source)
            if inferred_ch and not ch:
                ch = inferred_ch
            nvr = Nvr.query.get(inferred_id) if inferred_id else None
            if nvr:
                base = nvr.name or nvr.ip
                label = f'{base} / CH{ch}' if ch else base
                return {
                    'nvr_id': inferred_id,
                    'nvr_channel': ch,
                    'nvr_label': label,
                    'nvr': _nvr_to_dict(nvr, include_cameras=False),
                    'device_kind': 'nvr_channel',
                    'rtsp_direct': camera.rtsp_direct,
                    'channel_online': camera.channel_online,
                    'connection_status': camera.connection_status,
                }
            return {
                'nvr_id': inferred_id,
                'nvr_channel': ch,
                'nvr_label': None,
                'nvr': None,
                'device_kind': 'nvr_channel',
                'rtsp_direct': camera.rtsp_direct,
                'channel_online': camera.channel_online,
                'connection_status': camera.connection_status,
            }
        return {
            'nvr_id': None,
            'nvr_channel': ch,
            'nvr_label': None,
            'nvr': None,
            'device_kind': 'direct',
        }
    nvr = camera.nvr
    if not nvr:
        nvr = Nvr.query.get(camera.nvr_id)
    if not nvr:
        return {
            'nvr_id': camera.nvr_id,
            'nvr_channel': camera.nvr_channel or 0,
            'nvr_label': None,
            'nvr': None,
            'device_kind': 'nvr_channel',
        }
    ch = camera.nvr_channel or 0
    base = nvr.name or nvr.ip
    label = f'{base} / CH{ch}' if ch else base
    return {
        'nvr_id': camera.nvr_id,
        'nvr_channel': ch,
        'nvr_label': label,
        'nvr': _nvr_to_dict(nvr, include_cameras=False),
        'device_kind': 'nvr_channel',
        'rtsp_direct': camera.rtsp_direct,
        'channel_online': camera.channel_online,
        'connection_status': camera.connection_status,
    }
