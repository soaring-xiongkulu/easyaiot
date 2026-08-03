"""封装 .scripts/docker 统一安装脚本的界面化任务执行（Linux / macOS / Windows）。"""
from __future__ import annotations

import logging
import os
import platform
import queue
import re
import shutil
import signal
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger('easyaiot-panel.stack')

# CSI / 简单 ESC 序列（颜色、光标移动等）
_ANSI_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

# 桌面端仅镜像部署时禁用的动作
DESKTOP_BLOCKED_ACTIONS = frozenset({'build', 'build-runtime', 'clean-build-runtime'})

# Windows GUI 宿主下调用 docker/bash 必须隐藏控制台，否则会反复闪黑框
_WIN_NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000) if os.name == 'nt' else 0
_WIN_NEW_GROUP = (
    getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0x00000200) if os.name == 'nt' else 0
)


def _win_run_kwargs() -> Dict[str, Any]:
    if not _WIN_NO_WINDOW:
        return {}
    return {'creationflags': _WIN_NO_WINDOW}


def detect_host_platform() -> Dict[str, Any]:
    """识别宿主机平台，并给出对应的一键部署脚本。"""
    system = (platform.system() or '').strip()
    machine = (platform.machine() or '').strip()
    key = system.lower()
    if key == 'darwin':
        os_key = 'macos'
        label = 'macOS'
        script_name = 'install_mac.sh'
        deploy_supported = True
        message = (
            '当前运行在 macOS 上。一键部署走「仅镜像」模式（install_mac.sh）：'
            '拉取预构建镜像后启动，不支持本地 docker build / build-runtime。'
        )
        hint = '请确保已安装 Docker Desktop，并建议 brew install bash（bash 4+）。'
    elif key.startswith('win'):
        os_key = 'windows'
        label = 'Windows'
        script_name = 'install_windows.sh'
        deploy_supported = True
        message = (
            '当前运行在 Windows 上。一键部署走「仅镜像」模式（install_windows.sh）：'
            '拉取预构建镜像后启动，不支持本地 docker build / build-runtime。'
        )
        hint = '请确保 Docker Desktop 已启动，且 PATH 中有 Git Bash（或 WSL bash）。'
    elif key == 'linux':
        os_key = 'linux'
        label = 'Linux'
        script_name = 'install_linux.sh'
        deploy_supported = True
        message = ''
        hint = ''
    else:
        os_key = key or 'unknown'
        label = system or '未知系统'
        script_name = 'install_linux.sh'
        deploy_supported = False
        message = f'当前系统（{label}）暂不支持 PANEL 一键部署。'
        hint = '请在 Linux / macOS / Windows（Docker Desktop）环境使用部署菜单。'

    return {
        'os': os_key,
        'system': system,
        'label': label,
        'machine': machine,
        'deploySupported': deploy_supported,
        'desktopImageOnly': os_key in ('macos', 'windows'),
        'message': message,
        'hint': hint,
        'scriptName': script_name,
    }


def _is_wsl_system_bash(path: str) -> bool:
    """识别 Windows 自带的 WSL 启动器 bash（不宜直接跑宿主机 Git Bash 脚本）。"""
    norm = (path or '').replace('/', '\\').lower()
    return norm.endswith('\\system32\\bash.exe') or norm.endswith('\\sysnative\\bash.exe')


def resolve_bash_executable() -> str:
    """解析可用的 bash（Windows 上优先 Git Bash，避免误用 system32\\bash.exe）。"""
    is_win = os.name == 'nt' or (platform.system() or '').lower().startswith('win')
    if is_win:
        candidates = [
            os.path.expandvars(r'%ProgramFiles%\Git\bin\bash.exe'),
            os.path.expandvars(r'%ProgramFiles%\Git\usr\bin\bash.exe'),
            os.path.expandvars(r'%ProgramFiles(x86)%\Git\bin\bash.exe'),
            os.path.expandvars(r'%LocalAppData%\Programs\Git\bin\bash.exe'),
            r'C:\Program Files\Git\bin\bash.exe',
            r'C:\Program Files\Git\usr\bin\bash.exe',
        ]
        for path in candidates:
            if path and os.path.isfile(path):
                return path
        found = shutil.which('bash')
        if found and not _is_wsl_system_bash(found):
            return found
        raise FileNotFoundError(
            '未找到 Git Bash。Windows 请安装 Git for Windows（不要仅依赖 system32\\bash.exe / WSL）。'
        )
    found = shutil.which('bash')
    if found:
        return found
    raise FileNotFoundError('未找到 bash，请确保 bash 在 PATH 中。')


def _is_docker_bridge_ip(ip: str) -> bool:
    """Docker 默认桥接网段 172.17.0.0/16–172.31.0.0/16。"""
    parts = (ip or '').split('.')
    if len(parts) != 4:
        return False
    try:
        a, b = int(parts[0]), int(parts[1])
    except ValueError:
        return False
    return a == 172 and 17 <= b <= 31


def _running_in_container() -> bool:
    if os.path.exists('/.dockerenv'):
        return True
    try:
        with open('/proc/1/cgroup', 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        return bool(re.search(r'(docker|containerd|kubepods|/libpod)', text))
    except OSError:
        return False


def detect_lan_host_ip() -> Optional[str]:
    """
    探测可用于媒体回调的宿主机局域网 IP。
    PANEL 容器内本机网卡是桥接地址，需经 docker --network=host 探测。
    """
    explicit = (os.environ.get('HOST_IP') or '').strip()
    if explicit:
        return explicit

    docker = shutil.which('docker')
    if docker and _running_in_container():
        for image in (
            'alpine:latest',
            'docker.m.daocloud.io/library/alpine:latest',
            'busybox:latest',
        ):
            try:
                inspect = subprocess.run(
                    [docker, 'image', 'inspect', image],
                    capture_output=True,
                    timeout=5,
                    check=False,
                    **_win_run_kwargs(),
                )
                if inspect.returncode != 0:
                    continue
                probe = subprocess.run(
                    [
                        docker, 'run', '--rm', '--network=host',
                        '--entrypoint', 'sh', image, '-c',
                        "ip -4 route get 1.1.1.1 2>/dev/null | sed -n 's/.*src \\([0-9.]*\\).*/\\1/p'",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                    **_win_run_kwargs(),
                )
                ip = (probe.stdout or '').strip().splitlines()[0].strip() if probe.stdout else ''
                if ip and not _is_docker_bridge_ip(ip):
                    return ip
            except (OSError, subprocess.TimeoutExpired, IndexError):
                continue

    # 非容器或探测失败：尽力用本机路由
    try:
        out = subprocess.run(
            ['ip', 'route', 'get', '1.1.1.1'],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
            **_win_run_kwargs(),
        )
        m = re.search(r'\bsrc\s+(\d+\.\d+\.\d+\.\d+)', out.stdout or '')
        if m and not _is_docker_bridge_ip(m.group(1)):
            return m.group(1)
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def _sanitize_log(text: str) -> str:
    """去掉终端颜色码，并把 \\r 进度刷新收成可读纯文本。"""
    if not text:
        return ''
    text = _ANSI_RE.sub('', text)
    if '\r' not in text:
        return text
    lines: List[str] = []
    for line in text.split('\n'):
        if '\r' in line:
            line = line.rsplit('\r', 1)[-1]
        lines.append(line)
    return '\n'.join(lines)

SAFE_ACTIONS = {
    'start', 'stop', 'restart', 'status', 'logs', 'profile',
    'verify', 'check', 'update', 'pull', 'build', 'build-runtime',
    'analyze-logs', 'analyze-disk', 'install',
}
DANGEROUS_ACTIONS = {'clean', 'clean-build-runtime'}
ALLOWED_ACTIONS = SAFE_ACTIONS | DANGEROUS_ACTIONS

# 部署脚本模块（与 install_linux.sh MODULES / 运行时构建模块对齐）
STACK_MODULE_OPTIONS = [
    {'value': '.scripts/docker', 'label': '基础服务'},
    {'value': 'DEVICE', 'label': 'Device 服务'},
    {'value': 'AI', 'label': 'AI 服务'},
    {'value': 'VIDEO', 'label': 'Video 服务'},
    {'value': 'WEB', 'label': 'Web 前端'},
    {'value': 'APP', 'label': 'App 移动端'},
    {'value': 'VISUALIZE', 'label': '可视化编辑器'},
    {'value': 'TRANSFORM', 'label': '系统对接'},
]
RUNTIME_BUILD_MODULE_OPTIONS = [
    {'value': 'DEVICE', 'label': 'DEVICE'},
    {'value': 'AI', 'label': 'AI'},
    {'value': 'VIDEO', 'label': 'VIDEO'},
    {'value': 'WEB', 'label': 'WEB'},
    {'value': 'APP', 'label': 'APP'},
    {'value': 'VISUALIZE', 'label': 'VISUALIZE'},
    {'value': 'TRANSFORM', 'label': 'TRANSFORM'},
]
BUILD_ARCH_OPTIONS = [
    {'value': 'all', 'label': '全部架构'},
    {'value': 'amd64', 'label': '仅 amd64'},
    {'value': 'arm64', 'label': '仅 arm64'},
]
# 允许经 API 透传的环境变量（白名单）
ALLOWED_JOB_ENV_KEYS = {
    'EASYAIOT_DEPLOY_PROFILE',
    'EASYAIOT_SKIP_IMAGE_PROMPT',
    'EASYAIOT_SKIP_BUILD',
    'EASYAIOT_RUNTIME_FORCE_PULL',
    'EASYAIOT_RUNTIME_BUILD_ARCH',
    'EASYAIOT_RUNTIME_BUILD_MODULE',
    'EASYAIOT_RUNTIME_FORCE_REBUILD',
    'PARALLEL_BUILD',
    'PARALLEL_MODULES',
    'FORCE_NETWORK_RECREATE',
    'HOST_IP',
}

# 用于扫描宿主机上残留/外部启动的部署脚本进程
DEPLOY_SCRIPT_MARKERS = (
    'install_linux.sh',
    'install_linux_arm.sh',
    'install_linux_kylin.sh',
    'install_mac.sh',
    'install_windows.sh',
    'install_windows.ps1',
    'install_middleware_linux.sh',
    'install_middleware_mac.sh',
    'install_middleware_desktop.sh',
    'install_desktop_common.sh',
    'runtime_image.sh',
    'build-runtime',
)
DEPLOY_CMD_HINTS = (
    'easyaiot',
    'EASYAIOT_DEPLOY_PROFILE',
    '.scripts/docker',
)


@dataclass
class Job:
    id: str
    action: str
    args: List[str] = field(default_factory=list)
    status: str = 'queued'  # queued|running|success|failed|cancelled
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    exit_code: Optional[int] = None
    log: str = ''
    error: str = ''
    _proc: Any = field(default=None, repr=False)


class StackOps:
    def __init__(
        self,
        project_root: str,
        install_script: str,
        allow_dangerous: bool = False,
        job_timeout: int = 7200,
        max_log_chars: int = 400_000,
        max_job_history: int = 15,
    ):
        self.project_root = project_root
        self.install_script = install_script
        self.allow_dangerous = allow_dangerous
        self.job_timeout = job_timeout
        self.max_log_chars = max_log_chars
        self.max_job_history = max(1, int(max_job_history))
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()

    def read_profile(self) -> Dict[str, Any]:
        stamp = os.path.join(
            self.project_root, '.scripts', 'docker', '.deploy_profile'
        )
        profile = os.environ.get('EASYAIOT_DEPLOY_PROFILE', '').strip()
        if not profile and os.path.isfile(stamp):
            try:
                with open(stamp, encoding='utf-8') as f:
                    profile = f.read().strip()
            except OSError:
                profile = ''
        if not profile:
            profile = 'full'
        desc = {
            'mini': '边缘精简版（推荐 ≥ 4 GB）',
            'standard': '标准版（推荐 ≥ 16 GB）',
            'full': '完整版（推荐 ≥ 20 GB）',
        }.get(profile, profile)
        return {
            'profile': profile,
            'description': desc,
            'stampFile': stamp if os.path.isfile(stamp) else None,
            'installScript': self.install_script,
            'installScriptExists': os.path.isfile(self.install_script),
            'projectRoot': self.project_root,
            'platform': detect_host_platform(),
        }

    def list_actions(self) -> List[Dict[str, Any]]:
        items = [
            {
                'action': 'install',
                'label': '安装并启动',
                'category': 'lifecycle',
                'dangerous': False,
                'desc': '首次安装，按部署形态拉起服务',
                'supportsImageMode': True,
            },
            {
                'action': 'start',
                'label': '启动全部',
                'category': 'lifecycle',
                'dangerous': False,
                'desc': '启动中间件与业务服务',
            },
            {
                'action': 'stop',
                'label': '停止全部',
                'category': 'lifecycle',
                'dangerous': False,
                'desc': '停止所有模块服务',
            },
            {
                'action': 'restart',
                'label': '重启全部',
                'category': 'lifecycle',
                'dangerous': False,
                'desc': '按序重启所有服务',
            },
            {
                'action': 'update',
                'label': '更新重启',
                'category': 'lifecycle',
                'dangerous': False,
                'desc': '更新镜像并重启（可选手动拉取或本地重建；桌面端仅拉取）',
                'supportsImageMode': True,
            },
            {
                'action': 'pull',
                'label': '拉取镜像',
                'category': 'image',
                'dangerous': False,
                'desc': '从仓库拉取预构建运行时镜像',
            },
            {
                'action': 'build',
                'label': '本地构建',
                'category': 'image',
                'dangerous': False,
                'desc': '各模块本地 docker build（耗时较长；桌面端不可用）',
                'supportsParallelBuild': True,
            },
            {
                'action': 'build-runtime',
                'label': '构建运行时',
                'category': 'image',
                'dangerous': False,
                'desc': '构建/推送运行时镜像到远程仓库（桌面端不可用）',
                'argKey': 'module',
                'argLabel': '目标模块',
                'argOptional': True,
                'argOptions': RUNTIME_BUILD_MODULE_OPTIONS,
                'supportsBuildArch': True,
            },
            {
                'action': 'check',
                'label': '环境检查',
                'category': 'diagnose',
                'dangerous': False,
                'desc': '检查 Docker / Compose 是否可用',
            },
            {
                'action': 'status',
                'label': '查看状态',
                'category': 'diagnose',
                'dangerous': False,
                'desc': '打印各模块容器状态',
            },
            {
                'action': 'verify',
                'label': '健康验证',
                'category': 'diagnose',
                'dangerous': False,
                'desc': '验证关键服务是否就绪',
            },
            {
                'action': 'profile',
                'label': '部署形态',
                'category': 'diagnose',
                'dangerous': False,
                'desc': '显示当前 mini/standard/full 与服务范围',
            },
            {
                'action': 'logs',
                'label': '模块日志',
                'category': 'diagnose',
                'dangerous': False,
                'desc': '查看模块安装脚本日志（可选指定模块）',
                'argKey': 'module',
                'argLabel': '模块',
                'argOptional': True,
                'argOptions': STACK_MODULE_OPTIONS,
            },
            {
                'action': 'analyze-logs',
                'label': '日志分析',
                'category': 'diagnose',
                'dangerous': False,
                'desc': '合并多模块近期日志，便于排查',
            },
            {
                'action': 'analyze-disk',
                'label': '磁盘分析',
                'category': 'diagnose',
                'dangerous': False,
                'desc': '项目相关目录磁盘占用',
            },
            {
                'action': 'clean',
                'label': '清理容器镜像',
                'category': 'maintain',
                'dangerous': True,
                'desc': '清理所有容器和镜像（危险）',
            },
            {
                'action': 'clean-build-runtime',
                'label': '清理构建缓存',
                'category': 'maintain',
                'dangerous': True,
                'desc': '清理 build-runtime 产物（先停业务服务；桌面端不可用）',
            },
        ]
        plat = detect_host_platform()
        if plat.get('desktopImageOnly'):
            items = [x for x in items if x['action'] not in DESKTOP_BLOCKED_ACTIONS]
        return items

    def list_meta(self) -> Dict[str, Any]:
        plat = detect_host_platform()
        script_exists = os.path.isfile(self.install_script)
        deploy_supported = bool(plat.get('deploySupported')) and script_exists
        message = plat.get('message') or ''
        hint = plat.get('hint') or ''
        script_name = str(plat.get('scriptName') or os.path.basename(self.install_script))
        desktop_only = bool(plat.get('desktopImageOnly'))
        if plat.get('deploySupported') and not script_exists:
            message = (
                f'未找到部署脚本：{self.install_script}。'
                '请确认已挂载 EasyAIoT 仓库根目录 / 安装包内置 runtime，'
                '或设置正确的 INSTALL_SCRIPT / EASYAIOT_ROOT。'
            )
            hint = f'缺少 {script_name} 时无法执行部署操作。'
            deploy_supported = False

        image_modes = [{'value': 'pull', 'label': '拉取预构建镜像（推荐）'}]
        if not desktop_only:
            image_modes.append({'value': 'local', 'label': '本地构建镜像'})

        categories = [
            {'key': 'lifecycle', 'label': '部署', 'desc': '安装 · 启停 · 更新'},
            {
                'key': 'image',
                'label': '镜像',
                'desc': '拉取预构建' if desktop_only else '拉取 · 构建 · 推送',
            },
            {'key': 'diagnose', 'label': '诊断', 'desc': '检查 · 状态 · 分析'},
            {'key': 'maintain', 'label': '维护', 'desc': '清理 · 进程'},
        ]

        return {
            'categories': categories,
            'modules': STACK_MODULE_OPTIONS,
            'runtimeModules': RUNTIME_BUILD_MODULE_OPTIONS,
            'buildArchs': BUILD_ARCH_OPTIONS,
            'imageModes': image_modes,
            'allowDangerous': self.allow_dangerous,
            'actions': self.list_actions(),
            'platform': plat,
            'deploySupported': deploy_supported,
            'deployMessage': message,
            'deployHint': hint,
            'desktopImageOnly': desktop_only,
            'installScript': self.install_script,
            'installScriptExists': script_exists,
            'scriptName': script_name,
        }

    def assert_deploy_supported(self) -> None:
        meta = self.list_meta()
        if meta.get('deploySupported'):
            return
        raise RuntimeError(meta.get('deployMessage') or '当前环境不支持一键部署')

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            return self._job_to_dict(job)

    def list_jobs(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if limit is None:
            limit = self.max_job_history
        limit = max(1, int(limit))
        with self._lock:
            jobs = sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)
            return [self._job_to_dict(j) for j in jobs[:limit]]

    def _prune_jobs_locked(self) -> None:
        """保留最近 max_job_history 条任务；不删除仍在排队/运行中的任务。"""
        if len(self._jobs) <= self.max_job_history:
            return
        finished = sorted(
            (j for j in self._jobs.values() if j.status not in ('queued', 'running')),
            key=lambda j: j.created_at,
        )
        while len(self._jobs) > self.max_job_history and finished:
            oldest = finished.pop(0)
            self._jobs.pop(oldest.id, None)

    def start_job(
        self,
        action: str,
        extra_args: Optional[List[str]] = None,
        profile: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        env_extra: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        action = (action or '').strip().lower()
        if action not in ALLOWED_ACTIONS:
            raise ValueError(f'不支持的操作: {action}')
        self.assert_deploy_supported()
        plat = detect_host_platform()
        if plat.get('desktopImageOnly') and action in DESKTOP_BLOCKED_ACTIONS:
            raise ValueError(
                f'{plat.get("label") or "桌面端"} 仅支持镜像部署，不支持「{action}」。'
                '请使用 pull / install / update。'
            )
        if action in DANGEROUS_ACTIONS and not self.allow_dangerous:
            raise ValueError('危险操作已禁用，请在 panel.env 设置 PANEL_ALLOW_DANGEROUS=1')
        if not os.path.isfile(self.install_script):
            raise FileNotFoundError(f'安装脚本不存在: {self.install_script}')

        opts = options or {}
        args = list(extra_args or [])
        module = str(opts.get('module') or '').strip()
        if module and action in ('logs', 'build-runtime'):
            args = [module]

        job = Job(id=uuid.uuid4().hex[:12], action=action, args=args)
        with self._lock:
            self._jobs[job.id] = job
            self._prune_jobs_locked()

        env = os.environ.copy()
        if profile:
            env['EASYAIOT_DEPLOY_PROFILE'] = profile
        env.setdefault('EASYAIOT_DEPLOY_PROFILE', self.read_profile()['profile'])
        env['DEBIAN_FRONTEND'] = 'noninteractive'
        env['EASYAIOT_NONINTERACTIVE'] = '1'
        env['TERM'] = 'dumb'
        env['NO_COLOR'] = '1'
        env['FORCE_COLOR'] = '0'
        # 面板调用一律非交互
        env['EASYAIOT_FROM_MENU'] = '0'
        env.setdefault('EASYAIOT_ROOT', self.project_root)

        image_mode = str(opts.get('imageMode') or '').strip().lower()
        # 桌面端强制拉取预构建镜像
        if plat.get('desktopImageOnly'):
            image_mode = 'pull'
        if image_mode == 'pull':
            env['EASYAIOT_SKIP_IMAGE_PROMPT'] = '1'
            env['EASYAIOT_SKIP_BUILD'] = '1'
            env['EASYAIOT_RUNTIME_FORCE_PULL'] = '1'
        elif image_mode == 'local':
            env['EASYAIOT_SKIP_IMAGE_PROMPT'] = '1'
            env['EASYAIOT_SKIP_BUILD'] = '0'
            env.pop('EASYAIOT_RUNTIME_FORCE_PULL', None)

        build_arch = str(opts.get('buildArch') or '').strip().lower()
        if build_arch and build_arch != 'all':
            env['EASYAIOT_RUNTIME_BUILD_ARCH'] = build_arch
        elif build_arch == 'all':
            env.pop('EASYAIOT_RUNTIME_BUILD_ARCH', None)

        if opts.get('parallelBuild') in (True, '1', 'true', 'yes'):
            env['PARALLEL_BUILD'] = 'true'
        if opts.get('parallelModules') in (True, '1', 'true', 'yes'):
            env['PARALLEL_MODULES'] = 'true'
        if opts.get('forceRebuild') in (True, '1', 'true', 'yes'):
            env['EASYAIOT_RUNTIME_FORCE_REBUILD'] = '1'

        if env_extra:
            for k, v in env_extra.items():
                key = str(k).strip()
                if key in ALLOWED_JOB_ENV_KEYS and v is not None:
                    env[key] = str(v)

        # PANEL 容器内自动注入真实宿主机 IP，避免媒体地址写成 172.x 桥接地址
        if not (env.get('HOST_IP') or '').strip():
            lan_ip = detect_lan_host_ip()
            if lan_ip:
                env['HOST_IP'] = lan_ip
                logger.info('PANEL 注入 HOST_IP=%s', lan_ip)

        # clean 需要确认 y；无 TTY 时必须主动写入 stdin
        stdin_payload = b'y\n' if action == 'clean' else None

        t = threading.Thread(
            target=self._run_job,
            args=(job, env, stdin_payload),
            daemon=True,
        )
        t.start()
        return self._job_to_dict(job)

    def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """停止正在执行的部署任务（杀掉安装脚本进程组）。"""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                raise KeyError(f'任务不存在: {job_id}')
            if job.status not in ('queued', 'running'):
                return self._job_to_dict(job)
            proc = job._proc
            job.status = 'cancelled'
            job.error = '用户停止部署'
            job.log = (job.log or '') + '\n[PANEL] 用户请求停止部署，正在终止任务...\n'

        if proc is not None and proc.poll() is None:
            self._kill_proc_tree(proc)
        # 同时清理可能残留的同名部署脚本进程
        try:
            self.kill_deploy_processes(kill_all=True)
        except Exception:
            logger.exception('清理部署进程失败')
        return self.get_job(job_id) or {'id': job_id, 'status': 'cancelled'}

    def list_deploy_processes(self) -> List[Dict[str, Any]]:
        """扫描宿主机上的 EasyAIoT 部署相关进程。"""
        try:
            import psutil
        except ImportError as e:
            raise RuntimeError('缺少 psutil，无法检测部署进程') from e

        my_pid = os.getpid()
        owned_pids = set()
        with self._lock:
            for job in self._jobs.values():
                proc = job._proc
                if proc is not None and proc.poll() is None and proc.pid:
                    owned_pids.add(proc.pid)

        rows: List[Dict[str, Any]] = []
        for proc in psutil.process_iter(
            ['pid', 'ppid', 'name', 'cmdline', 'create_time', 'username', 'status', 'cwd']
        ):
            try:
                info = proc.info
                pid = int(info.get('pid') or 0)
                if not pid or pid == my_pid:
                    continue
                cmdline = [str(x) for x in (info.get('cmdline') or [])]
                if not cmdline:
                    continue
                marker = self._match_deploy_marker(cmdline)
                if not marker:
                    continue
                cmd = ' '.join(cmdline)
                cwd = ''
                try:
                    cwd = info.get('cwd') or proc.cwd() or ''
                except (psutil.Error, OSError):
                    cwd = ''
                rows.append(
                    {
                        'pid': pid,
                        'ppid': int(info.get('ppid') or 0),
                        'name': info.get('name') or os.path.basename(cmdline[0]) or 'unknown',
                        'cmd': cmd[:600],
                        'marker': marker,
                        'cwd': cwd[:300],
                        'user': info.get('username') or '',
                        'status': info.get('status') or '',
                        'startedAt': info.get('create_time') or 0,
                        'ownedByPanel': pid in owned_pids or int(info.get('ppid') or 0) in owned_pids,
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        rows.sort(key=lambda r: (r.get('startedAt') or 0), reverse=True)
        return rows

    @staticmethod
    def _match_deploy_marker(cmdline: List[str]) -> Optional[str]:
        """只匹配真正在执行部署脚本的进程，避免命令行文本误伤。"""
        if not cmdline:
            return None
        joined = ' '.join(cmdline)
        # 排除 IDE/沙箱等把脚本名写进参数的进程
        if 'cursorsandbox' in joined or 'CURSOR_SANDBOX' in joined:
            return None
        exe = os.path.basename(cmdline[0])
        if exe in {'cursorsandbox', 'rg', 'grep', 'ag', 'less', 'more', 'tail', 'head', 'cat'}:
            return None

        for idx, arg in enumerate(cmdline):
            base = os.path.basename(arg)
            for marker in DEPLOY_SCRIPT_MARKERS:
                if base != marker and not arg.endswith('/' + marker):
                    continue
                if marker in ('runtime_image.sh', 'build-runtime'):
                    if not any(h in joined for h in DEPLOY_CMD_HINTS):
                        continue
                # argv0 就是脚本，或 bash/sh 正在执行该脚本
                if idx == 0:
                    return marker
                if exe in {'bash', 'sh', 'dash', 'zsh', 'bash.exe', 'sh.exe'} or cmdline[0].endswith(
                    ('/bash', '/sh', '/dash', '/zsh', '\\bash.exe', '\\sh.exe', '/bash.exe')
                ):
                    return marker
                # PowerShell 直接跑 install_windows.ps1
                if marker.endswith('.ps1') and (
                    exe.lower() in {'powershell', 'powershell.exe', 'pwsh', 'pwsh.exe'}
                    or 'powershell' in exe.lower()
                ):
                    return marker
        return None

    def kill_deploy_processes(
        self,
        pids: Optional[List[int]] = None,
        kill_all: bool = False,
    ) -> Dict[str, Any]:
        """杀掉指定或全部检测到的部署进程（优先杀进程组）。"""
        try:
            import psutil
        except ImportError as e:
            raise RuntimeError('缺少 psutil，无法停止部署进程') from e

        detected = self.list_deploy_processes()
        if kill_all or not pids:
            target_pids = [int(p['pid']) for p in detected]
        else:
            wanted = {int(x) for x in pids}
            target_pids = [int(p['pid']) for p in detected if int(p['pid']) in wanted]
            missing = wanted - set(target_pids)
            if missing:
                # 允许直接杀用户点选的 pid（只要仍存在）
                for pid in list(missing):
                    try:
                        psutil.Process(pid)
                        target_pids.append(pid)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

        killed: List[Dict[str, Any]] = []
        errors: List[str] = []
        for pid in sorted(set(target_pids)):
            try:
                self._kill_pid_tree(pid)
                killed.append({'pid': pid, 'ok': True})
            except Exception as e:
                errors.append(f'{pid}: {e}')
                killed.append({'pid': pid, 'ok': False, 'error': str(e)})

        # 同步把面板内 running 任务标为 cancelled
        with self._lock:
            for job in self._jobs.values():
                if job.status in ('queued', 'running'):
                    job.status = 'cancelled'
                    job.error = job.error or '用户停止部署进程'
                    job.finished_at = time.time()
                    job.log = (job.log or '') + '\n[PANEL] 已杀掉部署相关进程\n'

        return {
            'killed': killed,
            'errors': errors,
            'remaining': self.list_deploy_processes(),
            'totalKilled': sum(1 for x in killed if x.get('ok')),
        }

    @staticmethod
    def _kill_pid_tree(pid: int) -> None:
        import psutil

        try:
            proc = psutil.Process(pid)
        except psutil.NoSuchProcess:
            return

        children = proc.children(recursive=True)
        targets = children + [proc]

        if os.name != 'nt':
            # Unix：优先杀进程组（含 docker compose 子进程）
            try:
                os.killpg(pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError, OSError):
                for p in targets:
                    try:
                        p.terminate()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            gone, alive = psutil.wait_procs(targets, timeout=3)
            if not alive:
                return
            try:
                os.killpg(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                for p in alive:
                    try:
                        p.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            psutil.wait_procs(alive, timeout=2)
            return

        # Windows：无 killpg，逐个 terminate / kill
        for p in targets:
            try:
                p.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        gone, alive = psutil.wait_procs(targets, timeout=3)
        for p in alive:
            try:
                p.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        if alive:
            psutil.wait_procs(alive, timeout=2)

    @staticmethod
    def _kill_proc_tree(proc: subprocess.Popen) -> None:
        if proc.pid is None:
            return
        if os.name == 'nt':
            try:
                StackOps._kill_pid_tree(proc.pid)
            except Exception:
                try:
                    proc.terminate()
                except Exception:
                    pass
            try:
                proc.wait(timeout=3)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
            return

        try:
            # start_new_session=True 时，杀掉整个进程组（含 docker compose 子进程）
            os.killpg(proc.pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError, OSError):
            try:
                proc.terminate()
            except Exception:
                pass
        try:
            proc.wait(timeout=3)
            return
        except Exception:
            pass
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            try:
                proc.kill()
            except Exception:
                pass

    def _run_job(self, job: Job, env: Dict[str, str], stdin_payload: Optional[bytes] = None) -> None:
        job.status = 'running'
        job.started_at = time.time()
        cmd = [resolve_bash_executable(), self.install_script, job.action, *job.args]
        logger.info('启动任务 %s: %s', job.id, ' '.join(cmd))
        try:
            popen_kwargs: Dict[str, Any] = {
                'cwd': self.project_root,
                'env': env,
                'stdin': subprocess.PIPE if stdin_payload is not None else subprocess.DEVNULL,
                'stdout': subprocess.PIPE,
                'stderr': subprocess.STDOUT,
                'text': False,
                'bufsize': 0,
            }
            if os.name == 'nt':
                # 隐藏控制台 + 新进程组（便于停止）；GUI 宿主下缺 CREATE_NO_WINDOW 会反复闪黑框
                popen_kwargs['creationflags'] = _WIN_NO_WINDOW | _WIN_NEW_GROUP
            else:
                popen_kwargs['start_new_session'] = True

            proc = subprocess.Popen(cmd, **popen_kwargs)
            job._proc = proc
            if stdin_payload is not None and proc.stdin is not None:
                try:
                    proc.stdin.write(stdin_payload)
                    proc.stdin.flush()
                    proc.stdin.close()
                except (BrokenPipeError, OSError):
                    pass
            assert proc.stdout is not None
            merged_log = ''

            def _append(chunk: bytes) -> None:
                nonlocal merged_log
                if not chunk:
                    return
                # 容忍子进程输出中的非 UTF-8 字节，避免日志读取中断。
                text = chunk.decode('utf-8', errors='replace')
                if not text:
                    return
                merged_log = _sanitize_log(merged_log + text)
                if len(merged_log) > self.max_log_chars:
                    merged_log = merged_log[-self.max_log_chars :]
                # 实时刷新：让轮询中的前端能立即拿到最新日志。
                job.log = merged_log

            # Windows 上 select() 只能用于 socket，对管道会触发 WinError 10038；
            # 统一用读线程 + queue，Linux/macOS/Windows 都可用。
            out_q: queue.Queue = queue.Queue()

            def _reader() -> None:
                try:
                    while True:
                        chunk = proc.stdout.read(4096)
                        if not chunk:
                            break
                        out_q.put(chunk)
                except Exception:
                    pass
                finally:
                    out_q.put(None)

            reader = threading.Thread(
                target=_reader, name=f'job-{job.id}-stdout', daemon=True
            )
            reader.start()

            deadline = time.time() + self.job_timeout
            while True:
                if job.status == 'cancelled':
                    if proc.poll() is None:
                        self._kill_proc_tree(proc)
                    break
                if time.time() > deadline:
                    self._kill_proc_tree(proc)
                    job.error = f'超时（>{self.job_timeout}s）'
                    job.status = 'failed'
                    break

                try:
                    chunk = out_q.get(timeout=0.2)
                except queue.Empty:
                    # 进程已退出且读线程结束：再排空队列
                    if proc.poll() is not None and not reader.is_alive():
                        while True:
                            try:
                                leftover = out_q.get_nowait()
                            except queue.Empty:
                                break
                            if leftover is None:
                                break
                            _append(leftover)
                        break
                    continue

                if chunk is None:
                    break
                _append(chunk)

            reader.join(timeout=2)
            # 再排空一次，保留停止前的输出
            while True:
                try:
                    chunk = out_q.get_nowait()
                except queue.Empty:
                    break
                if chunk is None:
                    continue
                _append(chunk)

            job.log = merged_log or job.log
            if job.status == 'cancelled':
                job.exit_code = proc.poll()
            elif job.status != 'failed':
                job.exit_code = proc.wait()
                job.status = 'success' if job.exit_code == 0 else 'failed'
                if job.exit_code != 0 and not job.error:
                    job.error = f'退出码 {job.exit_code}'
        except Exception as e:
            logger.exception('任务失败 %s', job.id)
            if job.status != 'cancelled':
                job.status = 'failed'
                job.error = str(e)
        finally:
            job.finished_at = time.time()
            job._proc = None

    @staticmethod
    def _job_to_dict(job: Job) -> Dict[str, Any]:
        clean = _sanitize_log(job.log or '')
        return {
            'id': job.id,
            'action': job.action,
            'args': job.args,
            'status': job.status,
            'createdAt': job.created_at,
            'startedAt': job.started_at,
            'finishedAt': job.finished_at,
            'exitCode': job.exit_code,
            'error': job.error,
            'log': clean,
            'logTail': clean[-8000:] if clean else '',
        }
