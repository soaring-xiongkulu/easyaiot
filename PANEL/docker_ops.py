"""Docker 容器只读/控制操作（通过 docker CLI，不强制 docker SDK）。"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from typing import Any, Dict, List, Optional

logger = logging.getLogger('easyaiot-panel.docker')

# Windows GUI 宿主下调用 docker CLI 必须隐藏控制台，否则每次轮询都会闪黑框
_WIN_NO_WINDOW = (
    getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000) if os.name == 'nt' else 0
)


def docker_available() -> bool:
    return shutil.which('docker') is not None


def _run(args: List[str], timeout: int = 60) -> subprocess.CompletedProcess:
    # 强制 UTF-8：中文 Windows 下 text=True 用默认编码时，docker ps 大段 JSON
    # 可能被读成空串，导致容器列表恒为空；显式 utf-8 可稳定解析。
    kwargs: Dict[str, Any] = {
        'args': args,
        'capture_output': True,
        'text': True,
        'encoding': 'utf-8',
        'errors': 'replace',
        'timeout': timeout,
        'check': False,
    }
    if _WIN_NO_WINDOW:
        kwargs['creationflags'] = _WIN_NO_WINDOW
    return subprocess.run(**kwargs)


def _parse_json_lines(text: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in (text or '').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def docker_info() -> Dict[str, Any]:
    if not docker_available():
        return {'available': False, 'error': 'docker 未安装或不在 PATH'}
    cp = _run(['docker', 'info', '--format', '{{json .}}'], timeout=20)
    if cp.returncode != 0:
        return {'available': False, 'error': (cp.stderr or cp.stdout or 'docker info 失败').strip()}
    try:
        info = json.loads(cp.stdout.strip() or '{}')
    except json.JSONDecodeError:
        return {'available': False, 'error': 'docker info 输出无法解析'}
    return {
        'available': True,
        'serverVersion': info.get('ServerVersion'),
        'containers': info.get('Containers'),
        'containersRunning': info.get('ContainersRunning'),
        'containersPaused': info.get('ContainersPaused'),
        'containersStopped': info.get('ContainersStopped'),
        'images': info.get('Images'),
        'driver': info.get('Driver'),
        'memTotal': info.get('MemTotal'),
        'ncpu': info.get('NCPU'),
        'name': info.get('Name'),
        'operatingSystem': info.get('OperatingSystem'),
        'architecture': info.get('Architecture'),
    }


def list_containers(all_containers: bool = True) -> List[Dict[str, Any]]:
    if not docker_available():
        return []
    args = [
        'docker', 'ps',
        '-a' if all_containers else '',
        '--no-trunc',
        '--format', '{{json .}}',
    ]
    args = [a for a in args if a]
    cp = _run(args, timeout=30)
    if cp.returncode != 0:
        logger.warning('docker ps 失败: %s', cp.stderr)
        return []
    rows = _parse_json_lines(cp.stdout)
    result: List[Dict[str, Any]] = []
    for row in rows:
        names = (row.get('Names') or '').split(',')
        name = names[0].strip() if names else ''
        ports = row.get('Ports') or ''
        result.append({
            'id': row.get('ID') or row.get('Id') or '',
            'name': name,
            'image': row.get('Image') or '',
            'status': row.get('Status') or '',
            'state': (row.get('State') or '').lower(),
            'createdAt': row.get('CreatedAt') or '',
            'ports': ports,
            'labels': row.get('Labels') or '',
            'networks': row.get('Networks') or '',
            'command': row.get('Command') or '',
            'size': row.get('Size') or '',
            'mounts': row.get('Mounts') or '',
        })
    return result


def container_stats(ids: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
    """返回 container_id/name -> stats。"""
    if not docker_available():
        return {}
    args = ['docker', 'stats', '--no-stream', '--format', '{{json .}}']
    if ids:
        args.extend(ids)
    try:
        cp = _run(args, timeout=20)
    except subprocess.TimeoutExpired:
        logger.warning('docker stats 超时，跳过资源占用数据')
        return {}
    if cp.returncode != 0:
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for row in _parse_json_lines(cp.stdout):
        cid = row.get('ID') or row.get('Container') or ''
        name = row.get('Name') or ''
        item = {
            'id': cid,
            'name': name,
            'cpuPercent': _pct(row.get('CPUPerc')),
            'memUsage': row.get('MemUsage') or '',
            'memPercent': _pct(row.get('MemPerc')),
            'netIO': row.get('NetIO') or '',
            'blockIO': row.get('BlockIO') or '',
            'pids': row.get('PIDs') or '',
        }
        if cid:
            out[cid] = item
            out[cid[:12]] = item
        if name:
            out[name] = item
    return out


def _pct(raw: Any) -> float:
    if raw is None:
        return 0.0
    s = str(raw).strip().replace('%', '')
    try:
        return float(s)
    except ValueError:
        return 0.0


def inspect_container(cid: str) -> Optional[Dict[str, Any]]:
    if not docker_available() or not cid:
        return None
    cp = _run(['docker', 'inspect', cid], timeout=20)
    if cp.returncode != 0:
        return None
    try:
        data = json.loads(cp.stdout)
        return data[0] if data else None
    except (json.JSONDecodeError, IndexError, TypeError):
        return None


def container_logs(cid: str, tail: int = 200, timestamps: bool = True) -> str:
    if not docker_available():
        return 'docker 不可用'
    args = ['docker', 'logs', f'--tail={max(1, min(tail, 5000))}']
    if timestamps:
        args.append('--timestamps')
    args.append(cid)
    cp = _run(args, timeout=30)
    text = (cp.stdout or '') + (('\n' + cp.stderr) if cp.stderr else '')
    return text[-200000:] if len(text) > 200000 else text


def control_container(cid: str, action: str) -> Dict[str, Any]:
    action = (action or '').lower().strip()
    if action not in ('start', 'stop', 'restart'):
        return {'ok': False, 'error': f'不支持的操作: {action}'}
    if not docker_available():
        return {'ok': False, 'error': 'docker 不可用'}
    cp = _run(['docker', action, cid], timeout=120)
    if cp.returncode != 0:
        return {'ok': False, 'error': (cp.stderr or cp.stdout or f'{action} 失败').strip()}
    return {'ok': True, 'action': action, 'id': cid}


def list_networks() -> List[Dict[str, Any]]:
    if not docker_available():
        return []
    cp = _run(['docker', 'network', 'ls', '--format', '{{json .}}'], timeout=20)
    if cp.returncode != 0:
        return []
    return _parse_json_lines(cp.stdout)


def compose_projects() -> List[str]:
    """粗略列出 compose 项目名（来自容器 label）。"""
    projects = set()
    for c in list_containers(True):
        labels = c.get('labels') or ''
        for part in labels.split(','):
            if part.startswith('com.docker.compose.project='):
                projects.add(part.split('=', 1)[1])
    return sorted(projects)


def _parse_size_bytes(raw: Any) -> int:
    """解析 docker 展示的 Size 字符串（如 1.2GB / 345MB）为近似字节数。"""
    if raw is None:
        return 0
    if isinstance(raw, (int, float)):
        return int(raw)
    s = str(raw).strip().upper().replace(' ', '')
    if not s:
        return 0
    # 取 "virtual …" 前半段
    if '(' in s:
        s = s.split('(', 1)[0]
    units = [
        ('KIB', 1024),
        ('MIB', 1024 ** 2),
        ('GIB', 1024 ** 3),
        ('TIB', 1024 ** 4),
        ('KB', 1000),
        ('MB', 1000 ** 2),
        ('GB', 1000 ** 3),
        ('TB', 1000 ** 4),
        ('B', 1),
    ]
    for suffix, mul in units:
        if s.endswith(suffix):
            num = s[: -len(suffix)]
            try:
                return int(float(num) * mul)
            except ValueError:
                return 0
    try:
        return int(float(s))
    except ValueError:
        return 0


def list_images() -> List[Dict[str, Any]]:
    if not docker_available():
        return []
    cp = _run(
        ['docker', 'images', '--digests', '--no-trunc', '--format', '{{json .}}'],
        timeout=45,
    )
    if cp.returncode != 0:
        logger.warning('docker images 失败: %s', cp.stderr)
        return []
    result: List[Dict[str, Any]] = []
    for row in _parse_json_lines(cp.stdout):
        repo = (row.get('Repository') or '<none>').strip() or '<none>'
        tag = (row.get('Tag') or '<none>').strip() or '<none>'
        image_id = (row.get('ID') or row.get('Id') or '').strip()
        dangling = repo == '<none>' or tag == '<none>'
        size_raw = row.get('Size') or ''
        result.append({
            'id': image_id,
            'shortId': image_id.replace('sha256:', '')[:12] if image_id else '',
            'repository': repo,
            'tag': tag,
            'ref': f'{repo}:{tag}' if repo != '<none>' else image_id[:19] or '<none>',
            'digest': row.get('Digest') or '',
            'createdAt': row.get('CreatedAt') or '',
            'createdSince': row.get('CreatedSince') or '',
            'size': size_raw,
            'sizeBytes': _parse_size_bytes(size_raw),
            'dangling': dangling,
        })
    return result


def inspect_image(image_ref: str) -> Optional[Dict[str, Any]]:
    if not docker_available() or not image_ref:
        return None
    cp = _run(['docker', 'image', 'inspect', image_ref], timeout=30)
    if cp.returncode != 0:
        return None
    try:
        data = json.loads(cp.stdout)
        return data[0] if data else None
    except (json.JSONDecodeError, IndexError, TypeError):
        return None


def remove_image(image_ref: str, force: bool = False) -> Dict[str, Any]:
    if not image_ref:
        return {'ok': False, 'error': '镜像引用为空'}
    if not docker_available():
        return {'ok': False, 'error': 'docker 不可用'}
    args = ['docker', 'rmi']
    if force:
        args.append('-f')
    args.append(image_ref)
    cp = _run(args, timeout=120)
    if cp.returncode != 0:
        return {'ok': False, 'error': (cp.stderr or cp.stdout or '删除失败').strip()}
    return {
        'ok': True,
        'id': image_ref,
        'output': (cp.stdout or '').strip(),
    }


def prune_images(dangling_only: bool = True) -> Dict[str, Any]:
    """清理悬空镜像；dangling_only=False 时清理所有未被容器使用的镜像。"""
    if not docker_available():
        return {'ok': False, 'error': 'docker 不可用'}
    args = ['docker', 'image', 'prune', '-f']
    if not dangling_only:
        args.append('-a')
    cp = _run(args, timeout=180)
    if cp.returncode != 0:
        return {'ok': False, 'error': (cp.stderr or cp.stdout or '清理失败').strip()}
    return {
        'ok': True,
        'danglingOnly': dangling_only,
        'output': (cp.stdout or cp.stderr or '').strip(),
    }


# EasyAIoT 运行时镜像目录（与 .scripts/docker/runtime_image_common.sh 对齐）
_DEVICE_IMAGES = [
    ('aiot-gateway', 'iot-gateway', 'iot-gateway'),
    ('aiot-system', 'iot-module-system-biz', 'iot-system'),
    ('aiot-infra', 'iot-module-infra-biz', 'iot-infra'),
    ('aiot-device', 'iot-module-device-biz', 'iot-device'),
    ('aiot-dataset', 'iot-module-dataset-biz', 'iot-dataset'),
    ('aiot-node', 'iot-module-node-biz', 'iot-node'),
    ('aiot-visualize', 'iot-module-visualize-biz', 'iot-visualize'),
    ('aiot-tdengine', 'iot-module-tdengine-biz', 'iot-tdengine'),
    ('aiot-file', 'iot-module-file-biz', 'iot-file'),
    ('aiot-message', 'iot-module-message-biz', 'iot-message'),
    ('aiot-sink', 'iot-sink-biz', 'iot-sink'),
    ('aiot-gb28181', 'iot-gb28181-biz', 'iot-gb28181'),
]

_INDEPENDENT_IMAGES = [
    # remote, local, module, full_only, profile_dependent
    ('aiot-ai', 'ai-service', 'AI', False, False),
    ('aiot-video', 'video-service', 'VIDEO', False, False),
    ('aiot-web', 'web-service', 'WEB', False, True),
    ('aiot-panel', 'easyaiot/panel', 'PANEL', False, False),
    ('aiot-app', 'app-service', 'APP', True, False),
    ('aiot-visualize-web', 'visualize-service', 'VISUALIZE', True, False),
    ('aiot-transform', 'transform-service', 'TRANSFORM', True, False),
]

# mini / standard 形态下 DEVICE 跳过的 compose 服务（与 deploy_profile 粗对齐）
_DEVICE_SKIP_BY_PROFILE = {
    'edge': {
        'iot-gateway', 'iot-system', 'iot-infra', 'iot-device', 'iot-dataset', 'iot-node',
        'iot-visualize', 'iot-tdengine', 'iot-file', 'iot-message', 'iot-sink', 'iot-gb28181',
    },
    'mini': {
        'iot-gateway', 'iot-infra', 'iot-device', 'iot-dataset', 'iot-node',
        'iot-visualize', 'iot-tdengine', 'iot-file', 'iot-message', 'iot-sink', 'iot-gb28181',
    },
    'standard': {'iot-device', 'iot-tdengine', 'iot-visualize'},
    'full': set(),
}


def _local_ref(local_name: str, profile: str = 'full', tag: str = 'latest') -> str:
    if local_name == 'web-service' and profile in ('mini', 'standard'):
        return f'{local_name}:{tag}-{profile}'
    if profile in ('mini', 'standard') and local_name not in ('web-service', 'easyaiot/panel'):
        # 多数本地镜像不带形态后缀；web 例外
        return f'{local_name}:{tag}'
    return f'{local_name}:{tag}'


def _match_local_image(local_name: str, profile: str, images: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """在本机镜像列表中匹配项目本地名（兼容 tag / digest / 无 tag）。"""
    tag = 'latest'
    wanted = {
        _local_ref(local_name, profile, tag).lower(),
        f'{local_name}:{tag}'.lower(),
        local_name.lower(),
    }
    if local_name == 'web-service':
        wanted.update({
            f'web-service:{tag}-mini',
            f'web-service:{tag}-standard',
            f'web-service:{tag}',
        })
    # 精确 ref
    for img in images:
        ref = (img.get('ref') or '').lower()
        repo = (img.get('repository') or '').lower()
        if ref in wanted or repo == local_name.lower():
            return img
    # 仓库名包含（如 registry/.../iot-gateway）
    needle = local_name.lower().split('/')[-1]
    for img in images:
        repo = (img.get('repository') or '').lower()
        if repo.endswith('/' + needle) or repo == needle:
            return img
    return None


def _containers_using_image(local_name: str, containers: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    needle = local_name.lower()
    short = needle.split('/')[-1]
    hits: List[Dict[str, str]] = []
    for c in containers:
        image = (c.get('image') or '').lower()
        if needle in image or short in image.split('/')[-1]:
            hits.append({
                'name': c.get('name') or '',
                'id': (c.get('id') or '')[:12],
                'state': c.get('state') or '',
                'status': c.get('status') or '',
                'image': c.get('image') or '',
            })
    return hits


def image_catalog(profile: str = 'full') -> Dict[str, Any]:
    """按 EasyAIoT 模块列出期望镜像与本机就绪情况。"""
    profile = (profile or 'full').strip().lower()
    if profile not in ('mini', 'standard', 'full'):
        profile = 'full'
    images = list_images()
    containers = list_containers(True)
    skip_device = _DEVICE_SKIP_BY_PROFILE.get(profile, set())

    items: List[Dict[str, Any]] = []

    def add_item(
        *,
        module: str,
        remote: str,
        local: str,
        compose: str,
        required: bool,
        full_only: bool = False,
        profile_dependent: bool = False,
    ) -> None:
        matched = _match_local_image(local, profile, images)
        used = _containers_using_image(local, containers)
        present = matched is not None
        if not required:
            status = 'optional_missing' if not present else 'optional_ready'
        elif present:
            status = 'ready'
        else:
            status = 'missing'
        items.append({
            'module': module,
            'remote': remote,
            'local': local,
            'compose': compose,
            'expectedRef': _local_ref(local, profile),
            'required': required,
            'fullOnly': full_only,
            'profileDependent': profile_dependent,
            'present': present,
            'status': status,
            'image': matched,
            'containers': used,
            'runningContainers': sum(1 for u in used if u.get('state') == 'running'),
        })

    for remote, local, compose in _DEVICE_IMAGES:
        required = compose not in skip_device
        add_item(
            module='DEVICE',
            remote=remote,
            local=local,
            compose=compose,
            required=required,
        )

    for remote, local, module, full_only, profile_dep in _INDEPENDENT_IMAGES:
        if full_only and profile != 'full':
            required = False
        else:
            required = True
        # mini 形态通常不启 AI/VIDEO 等业务镜像时仍可能被拉取；保持 required=True 更贴近「要跑平台就该有」
        # PANEL 自身始终有用
        add_item(
            module=module,
            remote=remote,
            local=local,
            compose=local.split('/')[-1],
            required=required,
            full_only=full_only,
            profile_dependent=profile_dep,
        )

    ready = sum(1 for i in items if i['status'] in ('ready', 'optional_ready') and i['required'])
    missing = sum(1 for i in items if i['status'] == 'missing')
    optional_missing = sum(1 for i in items if i['status'] == 'optional_missing')
    required_total = sum(1 for i in items if i['required'])

    # 非目录内的本机镜像（方便清垃圾）
    catalog_locals = {i['local'].lower() for i in items}
    others = []
    for img in images:
        repo = (img.get('repository') or '').lower()
        short = repo.split('/')[-1]
        if repo in catalog_locals or short in {x.split('/')[-1] for x in catalog_locals}:
            continue
        if img.get('dangling'):
            continue
        others.append(img)

    return {
        'profile': profile,
        'summary': {
            'required': required_total,
            'ready': ready,
            'missing': missing,
            'optionalMissing': optional_missing,
            'otherImages': len(others),
            'totalLocalImages': len(images),
            'dangling': sum(1 for i in images if i.get('dangling')),
        },
        'modules': sorted({i['module'] for i in items}, key=lambda m: (m != 'DEVICE', m)),
        'items': items,
        'others': others,
    }
