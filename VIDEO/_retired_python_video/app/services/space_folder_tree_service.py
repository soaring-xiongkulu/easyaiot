"""
存储空间文件夹树：NVR / GB28181 分组层级
"""
import logging
from collections import defaultdict

from models import db, Device, Nvr, RecordSpace, SnapSpace
from app.utils.gb28181_source import is_gb28181_source, parse_gb28181_source
from app.services.nvr_service import infer_nvr_link_from_source, is_nvr_channel_device

logger = logging.getLogger(__name__)

SPACE_KIND_SNAP = 'snap'
SPACE_KIND_RECORD = 'record'


def _space_model(space_kind):
    if space_kind == SPACE_KIND_SNAP:
        return SnapSpace
    if space_kind == SPACE_KIND_RECORD:
        return RecordSpace
    raise ValueError(f'无效的空间类型: {space_kind}')


def _format_nvr_name(nvr):
    base = (nvr.name or nvr.ip or f'NVR-{nvr.id}').strip()
    if not base.startswith('[NVR]'):
        base = f'[NVR] {base}'
    return base


def _format_gb_sip_name(sip_device_id):
    sip_device_id = (sip_device_id or '').strip()
    return f'[GB28181] {sip_device_id}' if sip_device_id else '[GB28181]'


def _resolve_nvr_id(device):
    if device.nvr_id:
        return device.nvr_id
    if is_nvr_channel_device(device):
        inferred_id, _ = infer_nvr_link_from_source(device.source)
        return inferred_id
    return None


def _resolve_gb_sip_id(device):
    if is_gb28181_source(device.source):
        parsed = parse_gb28181_source(device.source)
        return parsed[0] if parsed else None
    from app.services.gb28181_sync_service import parse_gb28181_virtual_device_id
    parsed = parse_gb28181_virtual_device_id(device.id)
    return parsed[0] if parsed else None


def _resolve_device_kind(device):
    if not device:
        return 'direct'
    if is_gb28181_source(device.source) or (device.id or '').startswith('gb28181_'):
        return 'gb28181'
    if is_nvr_channel_device(device):
        return 'nvr_channel'
    return 'direct'


def _space_to_node(space, device=None):
    data = space.to_dict()
    data['node_type'] = 'space'
    data['node_key'] = f'space_{space.id}'
    data['name'] = data.get('space_name') or ''
    data['device_kind'] = _resolve_device_kind(device)
    if device and data['device_kind'] == 'nvr_channel':
        data['nvr_channel'] = device.nvr_channel or 0
    return data


def _folder_group_save_time(folder_type, group_key, space_kind):
    from app.services.space_group_save_time_service import (
        GROUP_TYPE_GB28181,
        GROUP_TYPE_NVR,
        get_group_save_time,
    )
    group_type = GROUP_TYPE_NVR if folder_type == 'nvr' else GROUP_TYPE_GB28181
    return get_group_save_time(group_type, group_key, space_kind)


def _folder_node(folder_type, node_key, name, child_count, space_kind=None, group_key=None, **extra):
    node = {
        'node_type': 'folder',
        'folder_type': folder_type,
        'node_key': node_key,
        'name': name,
        'space_name': name,
        'child_count': child_count,
    }
    if space_kind and group_key is not None:
        node['group_save_time'] = _folder_group_save_time(folder_type, group_key, space_kind)
    node.update(extra)
    return node


def _normalize_parent_key(parent_key):
    key = (parent_key or '').strip() or 'root'
    return key


def _build_breadcrumbs(parent_key):
    crumbs = [{'key': 'root', 'name': '全部空间'}]
    if parent_key == 'root':
        return crumbs
    if parent_key.startswith('nvr_'):
        try:
            nvr_id = int(parent_key[4:])
        except ValueError:
            return crumbs
        nvr = Nvr.query.get(nvr_id)
        name = _format_nvr_name(nvr) if nvr else f'[NVR] NVR-{nvr_id}'
        crumbs.append({'key': parent_key, 'name': name})
    elif parent_key.startswith('gb_sip_'):
        sip_id = parent_key[7:]
        crumbs.append({'key': parent_key, 'name': _format_gb_sip_name(sip_id)})
    return crumbs


def _paginate(items, page_no, page_size):
    total = len(items)
    start = max(0, (page_no - 1) * page_size)
    end = start + page_size
    return items[start:end], total


def _load_spaces_with_devices(space_kind):
    SpaceModel = _space_model(space_kind)
    spaces = SpaceModel.query.filter(SpaceModel.device_id.isnot(None)).all()
    device_ids = [s.device_id for s in spaces if s.device_id]
    devices = {}
    if device_ids:
        for device in Device.query.filter(Device.id.in_(device_ids)).all():
            devices[device.id] = device
    return spaces, devices


def _classify_space(space, device):
    if not device:
        return 'direct', None
    if is_gb28181_source(device.source) or (device.id or '').startswith('gb28181_'):
        sip_id = _resolve_gb_sip_id(device)
        return ('gb_sip', sip_id) if sip_id else ('direct', None)
    nvr_id = _resolve_nvr_id(device)
    if nvr_id and is_nvr_channel_device(device):
        return 'nvr', nvr_id
    return 'direct', None


def _list_root_nodes(space_kind, page_no, page_size, parent_key):
    spaces, devices = _load_spaces_with_devices(space_kind)
    direct_spaces = []
    by_nvr = defaultdict(list)
    by_gb = defaultdict(list)

    for space in spaces:
        device = devices.get(space.device_id)
        kind, group_id = _classify_space(space, device)
        if kind == 'nvr':
            by_nvr[group_id].append((space, device))
        elif kind == 'gb_sip':
            by_gb[group_id].append((space, device))
        else:
            direct_spaces.append(space)

    nodes = []

    for nvr_id in sorted(by_nvr.keys()):
        nvr = Nvr.query.get(nvr_id)
        name = _format_nvr_name(nvr) if nvr else f'[NVR] NVR-{nvr_id}'
        nodes.append(_folder_node(
            'nvr', f'nvr_{nvr_id}', name, len(by_nvr[nvr_id]),
            space_kind=space_kind,
            group_key=nvr_id,
            nvr_id=nvr_id,
            ip=nvr.ip if nvr else None,
            port=nvr.port if nvr else None,
        ))

    for sip_id in sorted(by_gb.keys()):
        nodes.append(_folder_node(
            'gb28181', f'gb_sip_{sip_id}', _format_gb_sip_name(sip_id), len(by_gb[sip_id]),
            space_kind=space_kind,
            group_key=sip_id,
            sip_device_id=sip_id,
        ))

    direct_spaces.sort(key=lambda s: (s.space_name or '', s.id or 0))
    for space in direct_spaces:
        nodes.append(_space_to_node(space, devices.get(space.device_id)))

    items, total = _paginate(nodes, page_no, page_size)
    return {
        'items': items,
        'total': total,
        'page_no': page_no,
        'page_size': page_size,
        'parent_key': parent_key,
        'breadcrumbs': _build_breadcrumbs(parent_key),
    }


def _list_nvr_children(space_kind, nvr_id, page_no, page_size, parent_key):
    spaces, devices = _load_spaces_with_devices(space_kind)
    matched = []
    for space in spaces:
        device = devices.get(space.device_id)
        if not device:
            continue
        resolved_nvr_id = _resolve_nvr_id(device)
        if resolved_nvr_id == nvr_id and is_nvr_channel_device(device):
            matched.append((space, device))

    matched.sort(key=lambda pair: (
        pair[1].nvr_channel or 0,
        pair[0].space_name or '',
        pair[0].id or 0,
    ))
    nodes = [_space_to_node(space, device) for space, device in matched]
    items, total = _paginate(nodes, page_no, page_size)
    return {
        'items': items,
        'total': total,
        'page_no': page_no,
        'page_size': page_size,
        'parent_key': parent_key,
        'breadcrumbs': _build_breadcrumbs(parent_key),
    }


def _list_gb_children(space_kind, sip_device_id, page_no, page_size, parent_key):
    spaces, devices = _load_spaces_with_devices(space_kind)
    matched = []
    for space in spaces:
        device = devices.get(space.device_id)
        if not device:
            continue
        sip_id = _resolve_gb_sip_id(device)
        if sip_id == sip_device_id:
            matched.append((space, device))

    matched.sort(key=lambda pair: (pair[0].space_name or '', pair[0].id or 0))
    nodes = [_space_to_node(space, device) for space, device in matched]
    items, total = _paginate(nodes, page_no, page_size)
    return {
        'items': items,
        'total': total,
        'page_no': page_no,
        'page_size': page_size,
        'parent_key': parent_key,
        'breadcrumbs': _build_breadcrumbs(parent_key),
    }


def _search_space_nodes(space_kind, page_no, page_size, search):
    SpaceModel = _space_model(space_kind)
    query = SpaceModel.query
    pattern = f'%{search}%'
    query = query.filter(
        db.or_(
            SpaceModel.space_name.ilike(pattern),
            SpaceModel.device_id.ilike(pattern),
        )
    )
    query = query.order_by(SpaceModel.created_at.desc())
    pagination = query.paginate(page=page_no, per_page=page_size, error_out=False)
    device_ids = [s.device_id for s in pagination.items if s.device_id]
    devices = {}
    if device_ids:
        for device in Device.query.filter(Device.id.in_(device_ids)).all():
            devices[device.id] = device
    items = [
        _space_to_node(space, devices.get(space.device_id))
        for space in pagination.items
    ]
    return {
        'items': items,
        'total': pagination.total,
        'page_no': page_no,
        'page_size': page_size,
        'parent_key': 'root',
        'breadcrumbs': [{'key': 'root', 'name': '搜索结果'}],
        'is_search': True,
    }


def _list_all_leaf_nodes(space_kind, page_no, page_size, search=None):
    """返回全部叶子空间（供任务配置等下拉选择）。"""
    SpaceModel = _space_model(space_kind)
    query = SpaceModel.query.filter(SpaceModel.device_id.isnot(None))
    if search:
        pattern = f'%{search.strip()}%'
        query = query.filter(
            db.or_(
                SpaceModel.space_name.ilike(pattern),
                SpaceModel.device_id.ilike(pattern),
            )
        )
    query = query.order_by(SpaceModel.created_at.desc())
    pagination = query.paginate(page=page_no, per_page=page_size, error_out=False)
    device_ids = [s.device_id for s in pagination.items if s.device_id]
    devices = {}
    if device_ids:
        for device in Device.query.filter(Device.id.in_(device_ids)).all():
            devices[device.id] = device
    items = [
        _space_to_node(space, devices.get(space.device_id))
        for space in pagination.items
    ]
    return {
        'items': items,
        'total': pagination.total,
        'page_no': page_no,
        'page_size': page_size,
        'parent_key': 'root',
        'breadcrumbs': [{'key': 'root', 'name': '全部空间'}],
        'scope': 'leaves',
    }


def list_space_folder_nodes(space_kind, page_no=1, page_size=30, search=None, parent_key=None, scope=None):
    """按层级返回存储空间文件夹节点。"""
    if scope == 'leaves':
        return _list_all_leaf_nodes(space_kind, page_no, page_size, search)

    parent_key = _normalize_parent_key(parent_key)
    if search:
        return _search_space_nodes(space_kind, page_no, page_size, search.strip())

    if parent_key == 'root':
        return _list_root_nodes(space_kind, page_no, page_size, parent_key)
    if parent_key.startswith('nvr_'):
        try:
            nvr_id = int(parent_key[4:])
        except ValueError as exc:
            raise ValueError(f'无效的 parentKey: {parent_key}') from exc
        return _list_nvr_children(space_kind, nvr_id, page_no, page_size, parent_key)
    if parent_key.startswith('gb_sip_'):
        sip_device_id = parent_key[7:].strip()
        if not sip_device_id:
            raise ValueError(f'无效的 parentKey: {parent_key}')
        return _list_gb_children(space_kind, sip_device_id, page_no, page_size, parent_key)
    raise ValueError(f'无效的 parentKey: {parent_key}')
