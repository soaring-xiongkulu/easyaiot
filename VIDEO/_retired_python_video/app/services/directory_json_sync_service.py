"""
设备目录 JSON 校验与同步（与 WEB directoryJson.ts 规则一致）
"""
from __future__ import annotations

from typing import Any

from app.services.camera_service import (
    DEFAULT_DIRECTORY_NAME,
    get_or_create_default_directory,
    is_default_directory,
)
from models import Device, DeviceDirectory, db

DirectoryJsonError = ValueError


def _dir_path(parent_path: str, name: str) -> str:
    n = (name or '').strip()
    return f'{parent_path}/{n}' if parent_path else n


def parse_directory_json_payload(data: Any) -> list[dict]:
    """解析请求体：根数组或 { tree: [] }。"""
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get('tree'), list):
        return data['tree']
    raise DirectoryJsonError('请使用目录数组，或 { "tree": [...] }')


def _validate_node(node: Any, path: str) -> None:
    if not node or not isinstance(node, dict):
        raise DirectoryJsonError(f'{path} 须为对象')
    name = (node.get('name') or '').strip()
    if not name:
        raise DirectoryJsonError(f'{path}.name 不能为空')
    if name == DEFAULT_DIRECTORY_NAME:
        raise DirectoryJsonError('请勿在 JSON 中编辑「默认分组」，该分组由系统保留')
    devices = node.get('devices')
    if devices is not None:
        if not isinstance(devices, list) or any(
            not isinstance(x, str) or not str(x).strip() for x in devices
        ):
            raise DirectoryJsonError(f'{path}.devices 须为设备 ID 字符串数组')
    children = node.get('children')
    if children is not None:
        if not isinstance(children, list):
            raise DirectoryJsonError(f'{path}.children 须为数组')
        for i, child in enumerate(children):
            _validate_node(child, f'{path}.children[{i}]')


def assert_no_duplicate_devices(nodes: list[dict]) -> None:
    """整棵树中每个摄像头 ID 只能出现一次。"""
    seen: dict[str, str] = {}

    def walk(node_list: list[dict], parent_dir: str) -> None:
        for node in node_list:
            name = (node.get('name') or '').strip()
            dir_label = f'{parent_dir} / {name}' if parent_dir else name
            for raw_id in node.get('devices') or []:
                device_id = str(raw_id).strip()
                if not device_id:
                    continue
                first_dir = seen.get(device_id)
                if first_dir:
                    raise DirectoryJsonError(
                        f'摄像头「{device_id}」在「{first_dir}」与「{dir_label}」中重复，'
                        f'一个摄像头只能出现一次',
                    )
                seen[device_id] = dir_label
            children = node.get('children') or []
            if children:
                walk(children, dir_label)

    walk(nodes, '')


def validate_directory_json_tree(nodes: list[dict]) -> None:
    """校验目录 JSON 结构（不含默认分组、设备不重复）。"""
    if not isinstance(nodes, list):
        raise DirectoryJsonError('根节点须为数组')
    for i, node in enumerate(nodes):
        _validate_node(node, f'[{i}]')
    assert_no_duplicate_devices(nodes)


def _build_directory_forest(parent_id=None) -> list[dict]:
    directories = (
        DeviceDirectory.query.filter_by(parent_id=parent_id)
        .order_by(DeviceDirectory.sort_order, DeviceDirectory.id)
        .all()
    )
    return [
        {
            'id': d.id,
            'name': d.name,
            'parent_id': d.parent_id,
            'is_default': is_default_directory(d),
            'children': _build_directory_forest(d.id),
        }
        for d in directories
    ]


def _flatten_with_path(
    nodes: list[dict],
    parent_path: str = '',
) -> list[dict]:
    flat: list[dict] = []
    for d in nodes:
        path = _dir_path(parent_path, d['name'])
        flat.append({'id': d['id'], 'path': path, 'is_default': d.get('is_default')})
        flat.extend(_flatten_with_path(d.get('children') or [], path))
    return flat


def _find_in_forest(
    roots: list[dict],
    parent_id: int | None,
    name: str,
) -> dict | None:
    key = name.strip()
    if parent_id is None:
        for d in roots:
            if d['name'] == key:
                return d
        return None
    for d in roots:
        if d['id'] == parent_id:
            for c in d.get('children') or []:
                if c['name'] == key:
                    return c
            return None
        found = _find_in_forest(d.get('children') or [], parent_id, name)
        if found:
            return found
    return None


def _find_default_in_forest(roots: list[dict]) -> dict | None:
    for d in roots:
        if d.get('is_default') or d['name'] == DEFAULT_DIRECTORY_NAME:
            return d
        found = _find_default_in_forest(d.get('children') or [])
        if found:
            return found
    return None


def _collect_json_paths(nodes: list[dict], parent_path: str) -> set[str]:
    paths: set[str] = set()

    def walk(node_list: list[dict], prefix: str) -> None:
        for node in node_list:
            path = _dir_path(prefix, node.get('name') or '')
            paths.add(path)
            children = node.get('children') or []
            if children:
                walk(children, path)

    walk(nodes, parent_path)
    return paths


def _inject_into_forest(roots: list[dict], parent_id: int | None, entry: dict) -> None:
    if parent_id is None:
        roots.append(entry)
        return

    def walk(nodes: list[dict]) -> bool:
        for node in nodes:
            if node['id'] == parent_id:
                node.setdefault('children', []).append(entry)
                return True
            if walk(node.get('children') or []):
                return True
        return False

    walk(roots)


def _apply_parent_id(directory: DeviceDirectory, parent_id: int | None) -> None:
    """确保目录父级与 JSON 层级一致（根级 parent_id 为空）。"""
    if is_default_directory(directory):
        return
    if directory.parent_id != parent_id:
        directory.parent_id = parent_id
        db.session.flush()


def _ensure_directory(
    name: str,
    parent_id: int | None,
    roots: list[dict],
    path_cache: dict[str, int],
    parent_path: str,
) -> int:
    key = name.strip()
    path = _dir_path(parent_path, key)

    # 优先按数据库 parent_id 精确匹配
    row = DeviceDirectory.query.filter_by(name=key, parent_id=parent_id).first()
    if row and not (parent_id is None and is_default_directory(row)):
        _apply_parent_id(row, parent_id)
        path_cache[path] = row.id
        return row.id

    # JSON 根级：同名目录若挂在默认分组或其它父级下，提升到根（parent_id=null）
    if parent_id is None:
        default_dir = get_or_create_default_directory()
        for candidate in DeviceDirectory.query.filter_by(name=key).all():
            if is_default_directory(candidate):
                continue
            _apply_parent_id(candidate, None)
            path_cache[path] = candidate.id
            entry = {
                'id': candidate.id,
                'name': candidate.name,
                'parent_id': None,
                'is_default': False,
                'children': _build_directory_forest(candidate.id),
            }
            _inject_into_forest(roots, None, entry)
            return candidate.id

    existing = _find_in_forest(roots, parent_id, key)
    if existing:
        directory = DeviceDirectory.query.get(existing['id'])
        if directory:
            _apply_parent_id(directory, parent_id)
            path_cache[path] = directory.id
            return directory.id

    directory = DeviceDirectory(
        name=key,
        parent_id=parent_id,
        description='',
        sort_order=0,
    )
    db.session.add(directory)
    db.session.flush()
    _apply_parent_id(directory, parent_id)
    path_cache[path] = directory.id
    entry = {
        'id': directory.id,
        'name': directory.name,
        'parent_id': directory.parent_id,
        'is_default': False,
        'children': [],
    }
    _inject_into_forest(roots, parent_id, entry)
    return directory.id


def _sync_node(
    node: dict,
    parent_id: int | None,
    parent_path: str,
    roots: list[dict],
    path_cache: dict[str, int],
) -> None:
    dir_id = _ensure_directory(
        node.get('name') or '',
        parent_id,
        roots,
        path_cache,
        parent_path,
    )
    path = _dir_path(parent_path, node.get('name') or '')

    for raw_id in node.get('devices') or []:
        device_id = str(raw_id).strip()
        if not device_id:
            continue
        device = Device.query.get(device_id)
        if not device:
            raise DirectoryJsonError(f'设备不存在: {device_id}')
        device.directory_id = dir_id

    for child in node.get('children') or []:
        _sync_node(child, dir_id, path, roots, path_cache)


def _prune_extra_directories(roots: list[dict], keep_paths: set[str]) -> None:
    flat = _flatten_with_path(roots)
    to_remove = sorted(
        [d for d in flat if not d.get('is_default') and d['path'] not in keep_paths],
        key=lambda x: len(x['path'].split('/')),
        reverse=True,
    )
    for item in to_remove:
        directory = DeviceDirectory.query.get(item['id'])
        if not directory or is_default_directory(directory):
            continue
        child_count = DeviceDirectory.query.filter_by(parent_id=directory.id).count()
        device_count = Device.query.filter_by(directory_id=directory.id).count()
        if child_count or device_count:
            continue
        db.session.delete(directory)


def _normalize_json_root_parent_ids(nodes: list[dict]) -> None:
    """同步前：JSON 根目录项一律设为根级（parent_id=null），与默认分组同级。"""
    for node in nodes:
        key = (node.get('name') or '').strip()
        if not key or key == DEFAULT_DIRECTORY_NAME:
            continue
        for directory in DeviceDirectory.query.filter_by(name=key).all():
            if is_default_directory(directory):
                continue
            if directory.parent_id is not None:
                directory.parent_id = None
    db.session.flush()


def sync_directory_from_json(nodes: list[dict]) -> None:
    """校验通过后同步：JSON 根目录与「默认分组」同级（parent_id=null）。"""
    validate_directory_json_tree(nodes)

    get_or_create_default_directory()
    _normalize_json_root_parent_ids(nodes)
    roots = _build_directory_forest()

    path_cache: dict[str, int] = {}
    for item in _flatten_with_path(roots):
        path_cache[item['path']] = item['id']

    for node in nodes:
        _sync_node(node, None, '', roots, path_cache)

    db.session.commit()

    roots_after = _build_directory_forest()
    keep_paths = _collect_json_paths(nodes, '')
    keep_paths.add(DEFAULT_DIRECTORY_NAME)
    _prune_extra_directories(roots_after, keep_paths)
    db.session.commit()
