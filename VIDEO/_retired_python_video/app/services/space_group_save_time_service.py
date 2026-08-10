"""
NVR / GB28181 分组存储策略：默认值持久化与组内非自定义设备联动
"""
import logging

from models import db, Device, SnapSpace, RecordSpace, SpaceGroupSavePolicy
from app.services.space_save_time_service import (
    DEFAULT_SAVE_TIME,
    SPACE_KIND_SNAP,
    SPACE_KIND_RECORD,
    get_directory_save_time,
    get_device_directory,
    validate_save_time,
)
from app.services.nvr_service import infer_nvr_link_from_source, is_nvr_channel_device
from app.utils.gb28181_source import is_gb28181_source, parse_gb28181_source

logger = logging.getLogger(__name__)

GROUP_TYPE_NVR = 'nvr'
GROUP_TYPE_GB28181 = 'gb28181'


def _space_model(space_kind):
    return SnapSpace if space_kind == SPACE_KIND_SNAP else RecordSpace


def resolve_device_group(device):
    """解析设备所属 NVR / GB28181 分组，返回 (group_type, group_key) 或 (None, None)。"""
    if not device:
        return None, None
    if is_gb28181_source(device.source) or (device.id or '').startswith('gb28181_'):
        parsed = parse_gb28181_source(device.source)
        if parsed:
            return GROUP_TYPE_GB28181, parsed[0]
        from app.services.gb28181_sync_service import parse_gb28181_virtual_device_id
        virtual = parse_gb28181_virtual_device_id(device.id)
        if virtual:
            return GROUP_TYPE_GB28181, virtual[0]
        return None, None
    if is_nvr_channel_device(device):
        nvr_id = device.nvr_id
        if not nvr_id:
            nvr_id, _ = infer_nvr_link_from_source(device.source)
        if nvr_id:
            return GROUP_TYPE_NVR, str(nvr_id)
    return None, None


def get_group_policy(group_type, group_key):
    return SpaceGroupSavePolicy.query.filter_by(
        group_type=group_type,
        group_key=str(group_key),
    ).first()


def get_or_create_group_policy(group_type, group_key):
    policy = get_group_policy(group_type, group_key)
    if policy:
        return policy
    policy = SpaceGroupSavePolicy(
        group_type=group_type,
        group_key=str(group_key),
        snap_save_time=DEFAULT_SAVE_TIME,
        record_save_time=DEFAULT_SAVE_TIME,
    )
    db.session.add(policy)
    db.session.flush()
    return policy


def get_group_save_time(group_type, group_key, space_kind):
    policy = get_group_policy(group_type, group_key)
    if not policy:
        return DEFAULT_SAVE_TIME
    if space_kind == SPACE_KIND_SNAP:
        return policy.snap_save_time if policy.snap_save_time is not None else DEFAULT_SAVE_TIME
    return policy.record_save_time if policy.record_save_time is not None else DEFAULT_SAVE_TIME


def get_group_save_time_for_device(device_id, space_kind):
    device = Device.query.get(device_id)
    group_type, group_key = resolve_device_group(device)
    if not group_type:
        return None
    policy = get_group_policy(group_type, group_key)
    if not policy:
        return None
    if space_kind == SPACE_KIND_SNAP:
        return policy.snap_save_time
    return policy.record_save_time


def resolve_inherited_save_time(device_id, space_kind):
    """非自定义设备继承顺序：分组默认 > 目录默认。"""
    group_type, group_key = resolve_device_group(Device.query.get(device_id))
    if group_type:
        policy = get_group_policy(group_type, group_key)
        if policy:
            if space_kind == SPACE_KIND_SNAP:
                return policy.snap_save_time if policy.snap_save_time is not None else DEFAULT_SAVE_TIME
            return policy.record_save_time if policy.record_save_time is not None else DEFAULT_SAVE_TIME
    directory = get_device_directory(device_id)
    return get_directory_save_time(directory, space_kind)


def _device_belongs_to_nvr(device, nvr_id):
    if not device:
        return False
    resolved = device.nvr_id
    if not resolved and is_nvr_channel_device(device):
        resolved, _ = infer_nvr_link_from_source(device.source)
    return resolved == nvr_id


def _device_belongs_to_gb_sip(device, sip_device_id):
    if not device:
        return False
    if is_gb28181_source(device.source):
        parsed = parse_gb28181_source(device.source)
        return bool(parsed and parsed[0] == sip_device_id)
    from app.services.gb28181_sync_service import parse_gb28181_virtual_device_id
    virtual = parse_gb28181_virtual_device_id(device.id)
    return bool(virtual and virtual[0] == sip_device_id)


def collect_group_device_ids(group_type, group_key):
    """收集分组下全部设备 ID。"""
    group_key = str(group_key).strip()
    ids = []
    if group_type == GROUP_TYPE_NVR:
        try:
            nvr_id = int(group_key)
        except ValueError:
            return ids
        direct = Device.query.filter_by(nvr_id=nvr_id).all()
        ids.extend(d.id for d in direct)
        seen = set(ids)
        for device in Device.query.filter(Device.nvr_id.is_(None)).all():
            if device.id in seen:
                continue
            if _device_belongs_to_nvr(device, nvr_id):
                ids.append(device.id)
                seen.add(device.id)
    elif group_type == GROUP_TYPE_GB28181:
        prefix = f'gb28181://{group_key}/'
        for device in Device.query.filter(Device.source.ilike(f'{prefix}%')).all():
            ids.append(device.id)
        virtual_prefix = f'gb28181_{group_key}_'
        for device in Device.query.filter(Device.id.ilike(f'{virtual_prefix}%')).all():
            if device.id not in ids:
                ids.append(device.id)
    return ids


def propagate_group_save_time(group_type, group_key, space_kind, save_time, commit=False):
    """分组默认保存时间变更时，联动更新组内非自定义设备空间。"""
    save_time = validate_save_time(save_time)
    device_ids = collect_group_device_ids(group_type, group_key)
    if not device_ids:
        return 0
    SpaceModel = _space_model(space_kind)
    updated = 0
    for device_id in device_ids:
        space = SpaceModel.query.filter_by(device_id=device_id).first()
        if space and not space.save_time_custom:
            space.save_time = save_time
            updated += 1
    if commit:
        db.session.commit()
    logger.info(
        '分组 %s:%s %s 保存时间联动更新: save_time=%s, updated=%s',
        group_type, group_key, space_kind, save_time, updated,
    )
    return updated


def update_group_save_time(group_type, group_key, space_kind, save_time, commit=True):
    """更新分组默认保存时间并联动非自定义子设备。"""
    group_type = (group_type or '').strip().lower()
    group_key = str(group_key or '').strip()
    if group_type not in (GROUP_TYPE_NVR, GROUP_TYPE_GB28181):
        raise ValueError(f'无效的分组类型: {group_type}')
    if not group_key:
        raise ValueError('分组标识不能为空')
    if group_type == GROUP_TYPE_NVR:
        try:
            int(group_key)
        except ValueError as exc:
            raise ValueError(f'无效的 NVR 分组标识: {group_key}') from exc

    save_time = validate_save_time(save_time)
    policy = get_or_create_group_policy(group_type, group_key)
    if space_kind == SPACE_KIND_SNAP:
        policy.snap_save_time = save_time
    else:
        policy.record_save_time = save_time
    db.session.flush()
    updated = propagate_group_save_time(group_type, group_key, space_kind, save_time, commit=commit)
    return policy, updated
