"""PANEL HTTP API：容器管理 + 安装脚本界面化 + 拓扑；同时托管独立前端静态资源。"""
from __future__ import annotations

import logging
import os
import platform
import sys
import time
from typing import Any, Dict

import psutil
from flask import Flask, jsonify, request, send_from_directory

import docker_ops
from stack_ops import StackOps
from topology import build_topology

logger = logging.getLogger('easyaiot-panel.server')

PANEL_TOKEN = os.environ.get('PANEL_TOKEN', '')
PANEL_LISTEN_HOST = os.environ.get('PANEL_LISTEN_HOST', '0.0.0.0')
PANEL_LISTEN_PORT = int(os.environ.get('PANEL_LISTEN_PORT', '9200'))
PANEL_ALLOW_DANGEROUS = os.environ.get('PANEL_ALLOW_DANGEROUS', '1').strip().lower() in (
    '1', 'true', 'yes',
)
PANEL_JOB_TIMEOUT = int(os.environ.get('PANEL_JOB_TIMEOUT', '7200'))
PANEL_JOB_HISTORY_LIMIT = int(os.environ.get('PANEL_JOB_HISTORY_LIMIT', '15'))
# EasyAIoT WEB 管控台地址；空则按请求主机 + PANEL_WEB_PORT 自动拼
PANEL_WEB_URL = os.environ.get('PANEL_WEB_URL', '').strip()
PANEL_WEB_PORT = (os.environ.get('PANEL_WEB_PORT', '8888').strip() or '8888')
# 与 WEB/docker-compose.yaml 的 container_name/image（web-service）及历史命名对齐
_WEB_HINTS = ('web-service', 'easyaiot-web', 'iot-web', 'web-nginx', 'aiot-web')


def _is_frozen() -> bool:
    return bool(getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'))


def _bundle_dir() -> str:
    """源码目录，或 PyInstaller 解包目录（含 ui/dist）。"""
    if _is_frozen():
        return str(sys._MEIPASS)  # type: ignore[attr-defined]
    return os.path.dirname(os.path.abspath(__file__))


def _runtime_dir() -> str:
    """可执行文件所在目录（源码模式下等同源码目录）。"""
    if _is_frozen():
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def _install_script_markers() -> tuple:
    return (
        os.path.join('.scripts', 'docker', 'install_linux.sh'),
        os.path.join('.scripts', 'docker', 'install_linux_arm.sh'),
        os.path.join('.scripts', 'docker', 'install_linux_kylin.sh'),
        os.path.join('.scripts', 'docker', 'install_mac.sh'),
        os.path.join('.scripts', 'docker', 'install_windows.sh'),
        os.path.join('.scripts', 'docker', 'install_desktop_common.sh'),
    )


def _default_install_script_name() -> str:
    system = (platform.system() or '').lower()
    if system == 'darwin':
        return 'install_mac.sh'
    if system.startswith('win') or os.name == 'nt':
        return 'install_windows.sh'
    return 'install_linux.sh'


def _detect_project_root() -> str:
    """定位 EasyAIoT 仓库根：环境变量 > 可执行文件旁推断 > 向上查找 install 脚本。"""
    env = os.environ.get('EASYAIOT_ROOT', '').strip()
    if env:
        return os.path.abspath(env)

    markers = _install_script_markers()
    candidates = [
        os.path.abspath(os.path.join(_runtime_dir(), '..')),
        os.path.abspath(os.path.join(_runtime_dir(), 'runtime')),
        os.path.abspath(os.path.join(_bundle_dir(), '..')),
        os.getcwd(),
    ]
    # frozen 安装目录旁的 runtime/
    runtime_sibling = os.path.join(_runtime_dir(), 'runtime')
    if runtime_sibling not in candidates:
        candidates.insert(1, runtime_sibling)

    for start in candidates:
        cur = start
        for _ in range(6):
            for marker in markers:
                if os.path.isfile(os.path.join(cur, marker)):
                    return cur
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent
    return os.path.abspath(os.path.join(_runtime_dir(), '..'))


_HERE = _bundle_dir()
PROJECT_ROOT = _detect_project_root()
INSTALL_SCRIPT = os.environ.get(
    'INSTALL_SCRIPT',
    os.path.join(PROJECT_ROOT, '.scripts', 'docker', _default_install_script_name()),
)
if not os.path.isabs(INSTALL_SCRIPT):
    INSTALL_SCRIPT = os.path.join(PROJECT_ROOT, INSTALL_SCRIPT)


def _ui_index_path(static_dir: str) -> str:
    return os.path.join(static_dir, 'index.html')


def _is_ui_dir(static_dir: str) -> bool:
    return bool(static_dir) and os.path.isdir(static_dir) and os.path.isfile(_ui_index_path(static_dir))


def _static_dir_candidates() -> list[str]:
    """前端静态目录候选：安装目录优先于 PyInstaller 临时解压目录。

    onefile 会把资源解到 %TEMP%\\_MEI*；重启后杀软/清理可能删掉该目录里的文件，
    导致进程仍在但 / 变成 Werkzeug 404。exe 同级 ui/dist 更稳定。
    """
    env = os.environ.get('PANEL_STATIC_DIR', '').strip()
    out: list[str] = []
    if env:
        out.append(os.path.abspath(env))
    out.append(os.path.join(_runtime_dir(), 'ui', 'dist'))
    out.append(os.path.join(_HERE, 'ui', 'dist'))
    # 去重且保序
    seen: set[str] = set()
    uniq: list[str] = []
    for item in out:
        key = os.path.normcase(os.path.abspath(item))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(os.path.abspath(item))
    return uniq


def _resolve_static_dir() -> tuple[str, bool]:
    for candidate in _static_dir_candidates():
        if _is_ui_dir(candidate):
            return candidate, True
    fallback = _static_dir_candidates()[0]
    return fallback, False


STATIC_DIR, HAS_UI = _resolve_static_dir()

app = Flask(__name__, static_folder=None)
stack = StackOps(
    project_root=PROJECT_ROOT,
    install_script=INSTALL_SCRIPT,
    allow_dangerous=PANEL_ALLOW_DANGEROUS,
    job_timeout=PANEL_JOB_TIMEOUT,
    max_job_history=PANEL_JOB_HISTORY_LIMIT,
)


def _ok(data: Any = None):
    return jsonify({'code': 0, 'msg': 'success', 'data': data if data is not None else {}})


def _err(msg: str, code: int = 1, http_status: int = 400):
    return jsonify({'code': code, 'msg': msg, 'data': None}), http_status


def _check_token() -> bool:
    if not PANEL_TOKEN:
        return True
    return request.headers.get('X-Panel-Token', '') == PANEL_TOKEN


def _request_hostname() -> str:
    host = (request.host or '').split(',')[0].strip()
    if not host:
        return '127.0.0.1'
    if host.startswith('['):
        # [::1]:9200
        end = host.find(']')
        return host[1:end] if end > 0 else '127.0.0.1'
    if ':' in host and host.count(':') == 1:
        return host.split(':', 1)[0]
    return host


def _resolve_web_url() -> str:
    if PANEL_WEB_URL:
        return PANEL_WEB_URL.rstrip('/')
    host = _request_hostname()
    if host in ('0.0.0.0', ''):
        host = '127.0.0.1'
    return f'http://{host}:{PANEL_WEB_PORT}'


def _web_runtime() -> Dict[str, Any]:
    """探测 WEB 容器状态，供前端跳转与友好提示。"""
    found = None
    for c in docker_ops.list_containers(True):
        cname = (c.get('name') or '').lower()
        image = (c.get('image') or '').lower()
        if any(h in cname or h in image for h in _WEB_HINTS):
            found = c
            break

    url = _resolve_web_url()
    if not found:
        status = 'missing'
        message = '未检测到 WEB 容器，平台可能尚未部署。可先在「部署」中安装，或确认地址后仍尝试打开。'
    elif (found.get('state') or '').lower() == 'running':
        status = 'running'
        message = 'WEB 管控台运行中'
    else:
        status = 'stopped'
        message = (
            f"已找到 WEB 容器「{found.get('name') or ''}」，但当前未运行"
            f"（{found.get('status') or found.get('state') or 'stopped'}）。"
            '可先在「部署」中启动，或仍尝试打开。'
        )

    return {
        'url': url,
        'port': PANEL_WEB_PORT,
        'configured': bool(PANEL_WEB_URL),
        'running': status == 'running',
        'status': status,
        'message': message,
        'container': (found or {}).get('name') or '',
        'containerState': (found or {}).get('state') or '',
        'containerStatus': (found or {}).get('status') or '',
    }


@app.before_request
def auth_middleware():
    path = request.path or '/'
    # 健康检查与前端静态资源不鉴权；仅 /api/* 需要 Token
    if path == '/health':
        return None
    if path.startswith('/api/'):
        if not _check_token():
            return _err('PANEL 认证失败', 401, 401)
        return None
    return None


@app.get('/health')
def health():
    global STATIC_DIR, HAS_UI
    STATIC_DIR, HAS_UI = _resolve_static_dir()
    return _ok({
        'status': 'ok',
        'service': 'easyaiot-panel',
        'ui': HAS_UI,
        'staticDir': STATIC_DIR,
        'ts': time.time(),
    })


@app.get('/api/overview')
def overview():
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage(PROJECT_ROOT if os.path.isdir(PROJECT_ROOT) else '/')
    cpu_percent = psutil.cpu_percent(interval=0.2)
    profile = stack.read_profile()
    dinfo = docker_ops.docker_info()
    containers = docker_ops.list_containers(True)
    running = sum(1 for c in containers if (c.get('state') or '') == 'running')
    return _ok({
        'host': {
            'hostname': platform.node(),
            'system': platform.system(),
            'release': platform.release(),
            'machine': platform.machine(),
            'python': platform.python_version(),
            'cpuCount': psutil.cpu_count() or 0,
            'cpuPercent': cpu_percent,
            'memTotal': vm.total,
            'memUsed': vm.used,
            'memPercent': vm.percent,
            'diskTotal': disk.total,
            'diskUsed': disk.used,
            'diskPercent': disk.percent,
        },
        'docker': dinfo,
        'profile': profile,
        'containers': {
            'total': len(containers),
            'running': running,
            'stopped': len(containers) - running,
        },
        'projects': docker_ops.compose_projects(),
        'panel': {
            'listen': f'{PANEL_LISTEN_HOST}:{PANEL_LISTEN_PORT}',
            'tokenRequired': bool(PANEL_TOKEN),
            'allowDangerous': PANEL_ALLOW_DANGEROUS,
            'projectRoot': PROJECT_ROOT,
            'ui': HAS_UI,
            'platform': profile.get('platform') or {},
            'deploySupported': bool((profile.get('platform') or {}).get('deploySupported'))
            and bool(profile.get('installScriptExists')),
            'web': _web_runtime(),
        },
    })


@app.get('/api/links')
def links():
    """对外跳转链接（WEB 管控台等）。"""
    return _ok({'web': _web_runtime()})


@app.get('/api/containers')
def containers():
    all_flag = request.args.get('all', '1') != '0'
    with_stats = request.args.get('stats', '1') != '0'
    rows = docker_ops.list_containers(all_flag)
    stats: Dict[str, Any] = {}
    if with_stats:
        running_ids = [c['id'] for c in rows if c.get('state') == 'running' and c.get('id')]
        stats = docker_ops.container_stats(running_ids[:80] if running_ids else None)
    result = []
    for c in rows:
        cid = c.get('id') or ''
        st = stats.get(cid) or stats.get(cid[:12]) or stats.get(c.get('name') or '') or {}
        result.append({**c, 'stats': st or None})
    return _ok({'list': result, 'total': len(result)})


@app.get('/api/containers/<cid>/logs')
def container_logs(cid: str):
    tail = int(request.args.get('tail', '200'))
    text = docker_ops.container_logs(cid, tail=tail)
    return _ok({'id': cid, 'tail': tail, 'logs': text})


@app.post('/api/containers/<cid>/<action>')
def container_action(cid: str, action: str):
    if action not in ('start', 'stop', 'restart'):
        return _err(f'不支持的操作: {action}')
    res = docker_ops.control_container(cid, action)
    if not res.get('ok'):
        return _err(res.get('error') or '操作失败')
    return _ok(res)


@app.get('/api/images')
def images():
    rows = docker_ops.list_images()
    total_bytes = sum(int(r.get('sizeBytes') or 0) for r in rows)
    dangling = sum(1 for r in rows if r.get('dangling'))
    return _ok({
        'list': rows,
        'total': len(rows),
        'dangling': dangling,
        'totalBytes': total_bytes,
    })


@app.get('/api/images/catalog')
def images_catalog():
    profile = (request.args.get('profile') or '').strip().lower()
    if not profile:
        profile = (stack.read_profile().get('profile') or 'full')
    data = docker_ops.image_catalog(profile=profile)
    data['deployProfile'] = stack.read_profile()
    return _ok(data)


@app.get('/api/images/<path:image_ref>/inspect')
def image_inspect(image_ref: str):
    data = docker_ops.inspect_image(image_ref)
    if not data:
        return _err('镜像不存在或无法解析', http_status=404)
    return _ok({'id': image_ref, 'inspect': data})


@app.post('/api/images/<path:image_ref>/remove')
def image_remove(image_ref: str):
    body = request.get_json(force=True, silent=True) or {}
    force = bool(body.get('force'))
    res = docker_ops.remove_image(image_ref, force=force)
    if not res.get('ok'):
        return _err(res.get('error') or '删除失败')
    return _ok(res)


@app.post('/api/images/prune')
def image_prune():
    body = request.get_json(force=True, silent=True) or {}
    dangling_only = body.get('danglingOnly', True)
    if isinstance(dangling_only, str):
        dangling_only = dangling_only.strip().lower() not in ('0', 'false', 'no')
    res = docker_ops.prune_images(dangling_only=bool(dangling_only))
    if not res.get('ok'):
        return _err(res.get('error') or '清理失败')
    return _ok(res)


@app.get('/api/topology')
def topology():
    return _ok(build_topology())


@app.get('/api/profile')
def profile():
    return _ok(stack.read_profile())


@app.get('/api/stack/actions')
def stack_actions():
    return _ok({'actions': stack.list_actions(), 'allowDangerous': PANEL_ALLOW_DANGEROUS})


@app.get('/api/stack/meta')
def stack_meta():
    return _ok(stack.list_meta())


@app.get('/api/stack/jobs')
def stack_jobs():
    limit = int(request.args.get('limit', str(PANEL_JOB_HISTORY_LIMIT)))
    return _ok({'list': stack.list_jobs(limit=limit)})


@app.get('/api/stack/jobs/<job_id>')
def stack_job(job_id: str):
    job = stack.get_job(job_id)
    if not job:
        return _err('任务不存在', http_status=404)
    return _ok(job)


@app.post('/api/stack/run')
def stack_run():
    body = request.get_json(force=True, silent=True) or {}
    action = body.get('action') or ''
    args = body.get('args') or []
    profile = body.get('profile')
    options = body.get('options') or {}
    env_extra = body.get('env') or {}
    if not isinstance(args, list):
        return _err('args 必须是数组')
    if options is not None and not isinstance(options, dict):
        return _err('options 必须是对象')
    if env_extra is not None and not isinstance(env_extra, dict):
        return _err('env 必须是对象')
    try:
        job = stack.start_job(
            action,
            extra_args=[str(a) for a in args],
            profile=profile,
            options=options if isinstance(options, dict) else {},
            env_extra={str(k): str(v) for k, v in (env_extra or {}).items()},
        )
        return _ok(job)
    except Exception as e:
        logger.exception('启动任务失败')
        return _err(str(e))


@app.post('/api/stack/jobs/<job_id>/cancel')
def stack_job_cancel(job_id: str):
    try:
        job = stack.cancel_job(job_id)
        return _ok(job)
    except KeyError:
        return _err('任务不存在', http_status=404)
    except Exception as e:
        logger.exception('停止任务失败')
        return _err(str(e))


@app.get('/api/stack/processes')
def stack_processes():
    try:
        rows = stack.list_deploy_processes()
        return _ok({'list': rows, 'total': len(rows)})
    except Exception as e:
        logger.exception('检测部署进程失败')
        return _err(str(e))


@app.post('/api/stack/processes/kill')
def stack_processes_kill():
    body = request.get_json(force=True, silent=True) or {}
    pids = body.get('pids') or []
    kill_all = bool(body.get('all'))
    if pids and not isinstance(pids, list):
        return _err('pids 必须是数组')
    try:
        result = stack.kill_deploy_processes(
            pids=[int(x) for x in pids] if pids else None,
            kill_all=kill_all or not pids,
        )
        return _ok(result)
    except Exception as e:
        logger.exception('杀掉部署进程失败')
        return _err(str(e))


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def spa(path: str):
    """托管独立前端；未构建 UI 时返回 JSON 提示。"""
    global STATIC_DIR, HAS_UI
    if path.startswith('api/'):
        return _err('not found', http_status=404)

    # 每次请求重新探测：避免 _MEI* 临时目录被清理后仍用启动时的 HAS_UI 缓存
    static_dir, has_ui = _resolve_static_dir()
    STATIC_DIR, HAS_UI = static_dir, has_ui
    if not has_ui:
        return _ok({
            'name': 'EasyAIoT PANEL',
            'version': '0.1.0',
            'ui': False,
            'staticDir': static_dir,
            'hint': '前端未打包或静态资源丢失。请重装安装包，或设置 PANEL_STATIC_DIR 指向 ui/dist',
            'docs': 'GET /api/overview | /api/containers | /api/topology | /api/stack/actions',
        })

    try:
        if path:
            candidate = os.path.join(static_dir, path)
            if os.path.isfile(candidate):
                return send_from_directory(static_dir, path)
        if not os.path.isfile(_ui_index_path(static_dir)):
            HAS_UI = False
            return _ok({
                'name': 'EasyAIoT PANEL',
                'version': '0.1.0',
                'ui': False,
                'staticDir': static_dir,
                'hint': 'index.html 缺失，请重装 PANEL 或重新打包',
            })
        return send_from_directory(static_dir, 'index.html')
    except Exception:
        logger.exception('托管前端静态资源失败: %s', static_dir)
        return _err(f'静态资源不可用: {static_dir}', http_status=404)


def create_app() -> Flask:
    return app
