"""Docker workspace lifecycle for EasyAIoT IDEA (code-server)."""
from __future__ import annotations

import logging
import os
import re
import secrets
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

import docker
from docker.errors import APIError, ImageNotFound, NotFound

from idle_reaper import ActivityStore

logger = logging.getLogger('easyaiot-idea.workspace')

LABEL_MANAGED = 'easyaiot.idea.managed'
LABEL_USER = 'easyaiot.idea.user'
LABEL_WS = 'easyaiot.idea.workspace'
LABEL_PASSWORD = 'easyaiot.idea.password'
LABEL_PORT = 'easyaiot.idea.port'
LABEL_CREATED = 'easyaiot.idea.created'


@dataclass
class WorkspaceInfo:
    id: str
    name: str
    user: str
    status: str
    port: int
    password: str
    url: str
    created_at: str
    container_id: str
    image: str
    last_active_at: str = ''
    idle_seconds: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _env(name: str, default: str = '') -> str:
    return os.environ.get(name, default).strip()


def _env_int(name: str, default: int) -> int:
    raw = _env(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


class WorkspaceOps:
    def __init__(self) -> None:
        self.client = docker.from_env()
        self.image = _env('IDEA_WORKSPACE_IMAGE', 'easyaiot/idea-workspace:latest')
        self.git_url = _env('IDEA_GIT_URL', 'https://gitee.com/volara/easyaiot.git')
        self.git_depth = _env('IDEA_GIT_DEPTH')
        self.git_reference = _env('IDEA_GIT_REFERENCE')
        self.port_start = _env_int('IDEA_PORT_START', 13338)
        self.port_end = _env_int('IDEA_PORT_END', 13437)
        self.cpus = float(_env('IDEA_CPUS', '2') or '2')
        self.memory = _env('IDEA_MEMORY', '4g') or '4g'
        self.max_per_user = _env_int('IDEA_MAX_WORKSPACES_PER_USER', 1)
        self.max_total = _env_int('IDEA_MAX_WORKSPACES', 50)
        # 容器内路径（用于 mkdir）；经 docker.sock 创建子容器时必须用宿主机路径绑定
        self.data_dir = os.path.abspath(_env('IDEA_DATA_DIR', './.data/workspaces') or './.data/workspaces')
        self.data_dir_host = os.path.abspath(
            _env('IDEA_DATA_DIR_HOST') or self.data_dir
        )
        self.public_host = _env('IDEA_PUBLIC_HOST')
        self.public_scheme = _env('IDEA_PUBLIC_SCHEME', 'http') or 'http'
        self.idle_hours = float(_env('IDEA_IDLE_TIMEOUT_HOURS', '8') or '8')
        self._ensure_coder_data_dir(self.data_dir)
        self.activity = ActivityStore(self.data_dir)

    @staticmethod
    def _ensure_coder_data_dir(path: str) -> None:
        """Create path and, when running as root, chown to coder (1000:1000)."""
        os.makedirs(path, exist_ok=True)
        try:
            if hasattr(os, 'geteuid') and os.geteuid() == 0:
                os.chown(path, 1000, 1000)
        except OSError as exc:
            logger.warning('chown %s to 1000:1000 failed: %s', path, exc)

    def _sanitize_user(self, user: str) -> str:
        cleaned = re.sub(r'[^a-zA-Z0-9_.-]+', '-', (user or 'anon').strip())[:48]
        return cleaned or 'anon'

    def _workspace_name(self, user: str) -> str:
        return f'easyaiot-idea-{self._sanitize_user(user)}'

    def _list_managed(self) -> List[Any]:
        return self.client.containers.list(
            all=True,
            filters={'label': f'{LABEL_MANAGED}=1'},
        )

    def _used_ports(self) -> set:
        used = set()
        for c in self._list_managed():
            raw = (c.labels or {}).get(LABEL_PORT, '')
            if raw.isdigit():
                used.add(int(raw))
        return used

    def _alloc_port(self) -> int:
        used = self._used_ports()
        for port in range(self.port_start, self.port_end + 1):
            if port not in used:
                return port
        raise RuntimeError(f'no free port in {self.port_start}-{self.port_end}')

    def _public_url(self, port: int, request_host: Optional[str] = None) -> str:
        host = self.public_host
        if not host:
            host = (request_host or '127.0.0.1').split(':')[0]
        return f'{self.public_scheme}://{host}:{port}'

    def _parse_created_ts(self, created_at: str) -> float:
        if not created_at:
            return time.time()
        try:
            # 2026-08-13T02:00:00Z
            return time.mktime(time.strptime(created_at, '%Y-%m-%dT%H:%M:%SZ')) - time.timezone
        except ValueError:
            return time.time()

    def _last_active_ts(self, workspace_id: str, created_at: str) -> float:
        stored = self.activity.get(workspace_id)
        if stored is not None:
            return stored
        return self._parse_created_ts(created_at)

    def _container_image_name(self, container: Any) -> str:
        """Read image ref from list/inspect attrs. Do not call container.image:
        docker-py inspects ImageID and 404s after rebuild/prune."""
        attrs = getattr(container, 'attrs', None) or {}
        config = attrs.get('Config') or {}
        candidates = [
            config.get('Image'),
            attrs.get('Image'),
            attrs.get('ImageID'),
        ]
        named = [
            str(c).strip()
            for c in candidates
            if c and str(c).strip() and not str(c).strip().startswith('sha256:')
        ]
        if named:
            return named[0]
        hashed = [str(c).strip() for c in candidates if c and str(c).strip()]
        return hashed[0] if hashed else self.image

    def _to_info(self, container: Any, request_host: Optional[str] = None) -> WorkspaceInfo:
        labels = container.labels or {}
        port = int(labels.get(LABEL_PORT, '0') or 0)
        password = labels.get(LABEL_PASSWORD, '')
        user = labels.get(LABEL_USER, '')
        ws_id = labels.get(LABEL_WS, container.name or container.short_id)
        created_at = labels.get(LABEL_CREATED, '')
        last_ts = self._last_active_ts(ws_id, created_at)
        return WorkspaceInfo(
            id=ws_id,
            name=container.name or '',
            user=user,
            status=container.status,
            port=port,
            password=password,
            url=self._public_url(port, request_host) if port else '',
            created_at=created_at,
            container_id=container.short_id,
            image=self._container_image_name(container),
            last_active_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(last_ts)),
            idle_seconds=max(0, int(time.time() - last_ts)),
        )

    def touch_activity(self, workspace_id: str) -> None:
        if workspace_id:
            self.activity.touch(workspace_id)

    def list_workspaces(
        self,
        user: Optional[str] = None,
        request_host: Optional[str] = None,
        viewer_user: Optional[str] = None,
        include_password: bool = False,
    ) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        want = self._sanitize_user(user) if user else None
        viewer = self._sanitize_user(viewer_user) if viewer_user else None
        for c in self._list_managed():
            try:
                info = self._to_info(c, request_host)
            except (NotFound, APIError) as exc:
                logger.warning('skip workspace %s: %s', getattr(c, 'name', '?'), exc)
                continue
            if want and info.user != want:
                continue
            row = info.to_dict()
            if include_password:
                # 本机门户匿名 / 服务令牌：可看密码（便于复制登录）
                row['owned'] = True if not viewer else (info.user == viewer)
            elif viewer:
                row['owned'] = info.user == viewer
                if info.user != viewer:
                    row['password'] = ''
            else:
                row['owned'] = False
                row['password'] = ''
            items.append(row)
        items.sort(key=lambda x: x.get('created_at') or '', reverse=True)
        return items

    def get_workspace(self, workspace_id: str, request_host: Optional[str] = None) -> Optional[Dict[str, Any]]:
        for c in self._list_managed():
            labels = c.labels or {}
            if labels.get(LABEL_WS) == workspace_id or c.name == workspace_id:
                return self._to_info(c, request_host).to_dict()
        return None

    def create_workspace(
        self,
        user: str,
        request_host: Optional[str] = None,
        password: Optional[str] = None,
        profile: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        user_key = self._sanitize_user(user)
        profile = profile or {}
        managed = self._list_managed()
        if len(managed) >= self.max_total:
            raise RuntimeError(f'workspace limit reached ({self.max_total})')

        existing_user = [
            c for c in managed
            if (c.labels or {}).get(LABEL_USER) == user_key
        ]
        if len(existing_user) >= self.max_per_user:
            # 复用已有工作区：若已停止则启动
            c = existing_user[0]
            try:
                if c.status != 'running':
                    c.start()
                    c.reload()
                info = self._to_info(c, request_host)
                self.touch_activity(info.id)
                return info.to_dict()
            except (NotFound, APIError) as exc:
                logger.warning('reuse workspace %s failed, recreating: %s', c.name, exc)
                try:
                    c.remove(force=True)
                except APIError:
                    pass
                managed = [x for x in managed if x.id != c.id]

        name = self._workspace_name(user_key)
        # 同名残留
        try:
            old = self.client.containers.get(name)
            old.remove(force=True)
        except NotFound:
            pass

        port = self._alloc_port()
        pwd = password or secrets.token_urlsafe(12)
        created = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        ws_id = f'{user_key}-{int(time.time())}'
        data_subdir = os.path.join(self.data_dir, user_key)
        self._ensure_coder_data_dir(data_subdir)
        # docker.sock 场景下 bind 源必须是宿主机路径
        host_bind_dir = os.path.join(self.data_dir_host, user_key)
        if os.path.abspath(host_bind_dir) != os.path.abspath(data_subdir):
            self._ensure_coder_data_dir(host_bind_dir)

        provider = str(profile.get('provider') or '')
        login = str(profile.get('login') or '')
        git_name = str(profile.get('name') or login or user_key)
        git_email = str(profile.get('email') or '')
        fork_url = str(profile.get('fork_url') or '')
        if not fork_url and provider and login:
            repo = os.path.basename(self.git_url.rstrip('/'))
            if repo.endswith('.git'):
                repo = repo[:-4]
            if provider == 'gitee':
                fork_url = f'https://gitee.com/{login}/{repo}.git'
            elif provider == 'github':
                fork_url = f'https://github.com/{login}/{repo}.git'

        env = {
            'PASSWORD': pwd,
            'IDEA_GIT_URL': self.git_url,
            'IDEA_GIT_DEPTH': self.git_depth,
            'IDEA_WORKSPACE_USER': user_key,
            'IDEA_OPEN_FOLDER': '/home/coder/easyaiot',
            'IDEA_GIT_PROVIDER': provider,
            'IDEA_GIT_LOGIN': login,
            'IDEA_GIT_NAME': git_name,
            'IDEA_GIT_EMAIL': git_email,
            'IDEA_FORK_URL': fork_url,
        }

        volumes = {
            host_bind_dir: {'bind': '/home/coder/project-data', 'mode': 'rw'},
        }
        git_ref_host = _env('IDEA_GIT_REFERENCE_HOST') or self.git_reference
        if git_ref_host and (os.path.isdir(self.git_reference) or os.path.isdir(git_ref_host)):
            volumes[git_ref_host] = {
                'bind': '/opt/git-reference/easyaiot.git',
                'mode': 'ro',
            }
            env['IDEA_GIT_REFERENCE'] = '/opt/git-reference/easyaiot.git'

        nano_cpus = int(self.cpus * 1e9)
        try:
            container = self.client.containers.run(
                image=self.image,
                name=name,
                detach=True,
                ports={'8080/tcp': port},
                environment=env,
                volumes=volumes,
                labels={
                    LABEL_MANAGED: '1',
                    LABEL_USER: user_key,
                    LABEL_WS: ws_id,
                    LABEL_PASSWORD: pwd,
                    LABEL_PORT: str(port),
                    LABEL_CREATED: created,
                },
                nano_cpus=nano_cpus,
                mem_limit=self.memory,
                restart_policy={'Name': 'unless-stopped'},
            )
        except ImageNotFound as exc:
            raise RuntimeError(
                f'image not found: {self.image}. Build with: bash IDEA/install.sh build-workspace'
            ) from exc
        except APIError as exc:
            raise RuntimeError(f'docker error: {exc.explanation or exc}') from exc

        container.reload()
        # 等待 code-server 就绪（最长约 90s，含首次 clone）
        deadline = time.time() + 90
        while time.time() < deadline:
            container.reload()
            if container.status == 'running':
                break
            time.sleep(1)
        info = self._to_info(container, request_host)
        self.touch_activity(info.id)
        return self._to_info(container, request_host).to_dict()

    def stop_workspace(self, workspace_id: str, request_host: Optional[str] = None) -> Dict[str, Any]:
        c = self._find(workspace_id)
        if not c:
            raise RuntimeError('workspace not found')
        if c.status == 'running':
            c.stop(timeout=20)
            c.reload()
        return self._to_info(c, request_host).to_dict()

    def start_workspace(self, workspace_id: str, request_host: Optional[str] = None) -> Dict[str, Any]:
        c = self._find(workspace_id)
        if not c:
            raise RuntimeError('workspace not found')
        if c.status != 'running':
            c.start()
            c.reload()
        self.touch_activity(workspace_id)
        return self._to_info(c, request_host).to_dict()

    def heartbeat(self, workspace_id: str, request_host: Optional[str] = None) -> Dict[str, Any]:
        c = self._find(workspace_id)
        if not c:
            raise RuntimeError('workspace not found')
        self.touch_activity(workspace_id)
        return self._to_info(c, request_host).to_dict()

    def open_file(self, workspace_id: str, file_path: str) -> Dict[str, Any]:
        """在已运行的 code-server 实例中打开文件（走 VS Code IPC，避免浏览器弹窗拦截）。"""
        c = self._find(workspace_id)
        if not c:
            raise RuntimeError('workspace not found')
        if c.status != 'running':
            raise RuntimeError('workspace is not running')

        raw = (file_path or '').strip().replace('\\', '/')
        if not raw:
            raise RuntimeError('file path required')
        raw = raw.lstrip('@')
        # 禁止路径穿越
        if '..' in raw.split('/'):
            raise RuntimeError('invalid file path')

        repo = '/home/coder/easyaiot'
        if raw.startswith(repo + '/'):
            abs_path = raw
        elif raw.startswith('/workspace/easyaiot/'):
            abs_path = repo + '/' + raw[len('/workspace/easyaiot/'):]
        elif raw.startswith('/'):
            # 仅允许仓库内绝对路径
            if not raw.startswith(repo + '/') and raw != repo:
                raise RuntimeError('path outside workspace')
            abs_path = raw
        else:
            rel = raw.replace('workspace/easyaiot/', '').replace('easyaiot/', '', 1)
            abs_path = f'{repo}/{rel.lstrip("/")}'

        # 通过容器内 remote-cli + IPC 打开，不触发浏览器 window.open
        script = f'''
set -e
ABS={abs_path!r}
SOCK="$(ls -t /tmp/vscode-ipc-*.sock 2>/dev/null | head -1 || true)"
if [ -n "$SOCK" ]; then
  export VSCODE_IPC_HOOK_CLI="$SOCK"
fi
CLI=""
for c in \\
  /usr/lib/code-server/lib/vscode/bin/remote-cli/code-linux.sh \\
  /usr/lib/code-server/lib/vscode/bin/remote-cli/code-server \\
  /usr/bin/code-server
do
  if [ -x "$c" ] || [ -f "$c" ]; then CLI="$c"; break; fi
done
if [ -z "$CLI" ]; then
  echo "code cli not found" >&2
  exit 127
fi
# -r 复用窗口；文件不存在时仍尝试打开（可能是新建）
bash "$CLI" -r "$ABS" 2>/dev/null || "$CLI" -r "$ABS"
echo OK
'''
        result = c.exec_run(
            ['bash', '-lc', script],
            user='coder',
            workdir='/home/coder',
            environment={'HOME': '/home/coder'},
        )
        exit_code = int(result.exit_code or 0)
        output = ''
        if isinstance(result.output, (bytes, bytearray)):
            output = result.output.decode('utf-8', errors='replace')
        else:
            output = str(result.output or '')
        if exit_code != 0:
            raise RuntimeError(f'open file failed (exit {exit_code}): {output.strip()[:300]}')
        self.touch_activity(workspace_id)
        return {'ok': True, 'path': abs_path, 'output': output.strip()[:200]}

    def delete_workspace(self, workspace_id: str, remove_data: bool = False) -> Dict[str, Any]:
        c = self._find(workspace_id)
        if not c:
            raise RuntimeError('workspace not found')
        info = self._to_info(c)
        user = info.user
        c.remove(force=True)
        self.activity.remove(workspace_id)
        if remove_data and user:
            # 仅删空标记文件，避免误删大仓；完整清理由运维脚本处理
            marker = os.path.join(self.data_dir, user, '.idea-deleted')
            try:
                os.makedirs(os.path.dirname(marker), exist_ok=True)
                with open(marker, 'w', encoding='utf-8') as f:
                    f.write(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
            except OSError:
                pass
        return {'deleted': True, 'id': workspace_id, 'user': user}

    def reap_idle_workspaces(self) -> Dict[str, Any]:
        if self.idle_hours <= 0:
            return {'stopped': [], 'idle_hours': self.idle_hours}
        limit = self.idle_hours * 3600
        stopped = []
        for c in self._list_managed():
            if c.status != 'running':
                continue
            info = self._to_info(c)
            if info.idle_seconds >= limit:
                logger.info(
                    'stopping idle workspace %s user=%s idle=%ss',
                    info.id,
                    info.user,
                    info.idle_seconds,
                )
                try:
                    c.stop(timeout=20)
                    stopped.append(info.id)
                except APIError as exc:
                    logger.warning('failed to stop %s: %s', info.id, exc)
        return {'stopped': stopped, 'idle_hours': self.idle_hours}

    def _find(self, workspace_id: str) -> Optional[Any]:
        for c in self._list_managed():
            labels = c.labels or {}
            if labels.get(LABEL_WS) == workspace_id or c.name == workspace_id:
                return c
        return None

    def stats(self) -> Dict[str, Any]:
        items = self._list_managed()
        running = sum(1 for c in items if c.status == 'running')
        return {
            'total': len(items),
            'running': running,
            'max_total': self.max_total,
            'image': self.image,
            'git_url': self.git_url,
            'port_range': [self.port_start, self.port_end],
            'data_dir': self.data_dir,
            'idle_timeout_hours': self.idle_hours,
        }
