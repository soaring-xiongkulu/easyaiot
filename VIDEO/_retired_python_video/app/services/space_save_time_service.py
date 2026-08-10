"""
空间保存时间：目录默认值继承、设备自定义、批量联动更新
"""
import logging
from datetime import timedelta

from app.utils.service_urls import save_time_cutoff_naive
from models import db, Device, DeviceDirectory, SnapSpace, RecordSpace

logger = logging.getLogger(__name__)

# 单位：小时。默认每设备保留 1 小时
DEFAULT_SAVE_TIME = 1
MIN_SAVE_TIME_HOURS = 1
SPACE_KIND_SNAP = 'snap'
SPACE_KIND_RECORD = 'record'


def validate_save_time(save_time):
    """校验保存时长：0=永久，或 >=1 小时。"""
    if save_time is None:
        raise ValueError('保存时间不能为空')
    try:
        save_time = int(save_time)
    except (TypeError, ValueError) as exc:
        raise ValueError('保存时间必须为整数') from exc
    if save_time == 0 or save_time >= MIN_SAVE_TIME_HOURS:
        return save_time
    raise ValueError('保存时间须为 0（永久）或不少于 1 小时')


def save_time_to_timedelta(save_time):
    """将保存时长（小时）转为 timedelta；0 表示永久（调用方需自行跳过清理）。"""
    save_time = int(save_time)
    if save_time <= 0:
        return None
    return timedelta(hours=save_time)


def save_time_cutoff_naive(save_time_hours):
    """见 app.utils.service_urls.save_time_cutoff_naive（此处保留 re-export 兼容旧引用）。"""
    from app.utils.service_urls import save_time_cutoff_naive as _cutoff
    return _cutoff(save_time_hours)


def get_directory_save_time(directory, space_kind):
    """获取目录级默认保存时长（小时）。"""
    if not directory:
        return DEFAULT_SAVE_TIME
    if space_kind == SPACE_KIND_SNAP:
        return directory.snap_save_time if directory.snap_save_time is not None else DEFAULT_SAVE_TIME
    return directory.record_save_time if directory.record_save_time is not None else DEFAULT_SAVE_TIME


def get_device_directory(device_id):
    """获取设备所属目录。"""
    device = Device.query.get(device_id)
    if not device or not device.directory_id:
        return None
    return DeviceDirectory.query.get(device.directory_id)


def resolve_save_time_for_device(device_id, space_kind):
    """创建设备空间时解析应写入的保存时长（小时，跟随目录，非自定义）。"""
    directory = get_device_directory(device_id)
    return get_directory_save_time(directory, space_kind)


def get_directory_save_time_by_id(directory_id, space_kind):
    if not directory_id:
        return DEFAULT_SAVE_TIME
    directory = DeviceDirectory.query.get(directory_id)
    return get_directory_save_time(directory, space_kind)


def propagate_directory_save_time(directory_id, space_kind, save_time, commit=False):
    """目录默认值变更时，同步更新目录下所有非自定义设备空间。"""
    save_time = validate_save_time(save_time)
    devices = Device.query.filter_by(directory_id=directory_id).all()
    updated = 0
    SpaceModel = SnapSpace if space_kind == SPACE_KIND_SNAP else RecordSpace
    for device in devices:
        space = SpaceModel.query.filter_by(device_id=device.id).first()
        if space and not space.save_time_custom:
            space.save_time = save_time
            updated += 1
    if commit:
        db.session.commit()
    logger.info(
        '目录 %s %s 保存时间联动更新: save_time=%s, updated=%s',
        directory_id, space_kind, save_time, updated,
    )
    return updated


def update_directory_save_time(directory_id, space_kind, save_time, commit=True):
    """更新目录默认保存时间并联动非自定义设备。"""
    directory = DeviceDirectory.query.get(directory_id)
    if not directory:
        raise ValueError(f'目录不存在: ID={directory_id}')
    save_time = validate_save_time(save_time)
    if space_kind == SPACE_KIND_SNAP:
        directory.snap_save_time = save_time
    else:
        directory.record_save_time = save_time
    db.session.flush()
    updated = propagate_directory_save_time(directory_id, space_kind, save_time, commit=commit)
    return directory, updated


def sync_device_spaces_to_directory(device_id, directory_id=None):
    """设备变更目录后，将非自定义空间的保存时间同步为新目录默认值。"""
    directory = DeviceDirectory.query.get(directory_id) if directory_id else None
    for space_kind, SpaceModel in ((SPACE_KIND_SNAP, SnapSpace), (SPACE_KIND_RECORD, RecordSpace)):
        space = SpaceModel.query.filter_by(device_id=device_id).first()
        if space and not space.save_time_custom:
            space.save_time = get_directory_save_time(directory, space_kind)


def apply_space_save_time_update(space, space_kind, save_time=None, save_time_custom=None):
    """更新设备空间保存时间，处理自定义/跟随分组或目录逻辑。"""
    from app.services.space_group_save_time_service import resolve_inherited_save_time

    if save_time_custom is False:
        space.save_time_custom = False
        if space.device_id:
            space.save_time = resolve_inherited_save_time(space.device_id, space_kind)
        return space
    if save_time is not None:
        space.save_time = validate_save_time(save_time)
        space.save_time_custom = True if save_time_custom is None else bool(save_time_custom)
    elif save_time_custom is not None:
        space.save_time_custom = bool(save_time_custom)
        if not space.save_time_custom and space.device_id:
            space.save_time = resolve_inherited_save_time(space.device_id, space_kind)
    return space


def _enrich_space_dict(data, space, space_kind):
    from app.services.space_group_save_time_service import (
        get_group_save_time_for_device,
        resolve_device_group,
    )

    device_id = data.get('device_id')
    directory = get_device_directory(device_id) if device_id else None
    directory_save_time = get_directory_save_time(directory, space_kind)
    data['directory_save_time'] = directory_save_time
    data['directory_id'] = directory.id if directory else None

    group_save_time = get_group_save_time_for_device(device_id, space_kind) if device_id else None
    data['group_save_time'] = group_save_time
    device = Device.query.get(device_id) if device_id else None
    group_type, group_key = resolve_device_group(device)
    if group_type:
        data['group_type'] = group_type
        data['group_key'] = group_key

    if space and not space.save_time_custom:
        data['effective_save_time'] = data.get('save_time', directory_save_time)
    else:
        data['effective_save_time'] = data.get('save_time', DEFAULT_SAVE_TIME)
    return data


def enrich_snap_space_dict(data, space=None):
    """补充目录/分组默认值与有效保存时间字段。"""
    return _enrich_space_dict(data, space, SPACE_KIND_SNAP)


def enrich_record_space_dict(data, space=None):
    """补充目录/分组默认值与有效保存时间字段。"""
    return _enrich_space_dict(data, space, SPACE_KIND_RECORD)
