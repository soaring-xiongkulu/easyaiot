"""本机模块发布：用工作区源码 build，再 restart 本机已有 compose。不碰 IDEA 容器。"""
from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import threading
import time
import uuid
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger('easyaiot-idea.publish')

PUBLISHABLE = (
    'DEVICE',
    'AI',
    'RTC',
    'VIDEO',
    'WEB',
    'APP',
    'VISUALIZE',
    'TRANSFORM',
    'PANEL',
    'SITE',
)
SKIP_REASON = {
    'IDEA': 'IDEA 自身不可作为发布目标',
    'RUNTIME': '无模块镜像替换路径，请提 PR',
    'NODE': '无模块镜像替换路径，请提 PR',
    'EDGE': '无模块镜像替换路径，请提 PR',
    'COMPILE': '打包工具，不发布为运行容器',
}
TOP_IGNORE = {
    '.github',
    '.gitee',
    '.scripts',
    '.doc',
    '.image',
    'docs',
    'IDEA',
}

INSTALL_SCRIPT = 'install_linux.sh'
IDEA_NAME_RE = re.compile(r'easyaiot-idea', re.I)


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


def guess_pr_url(origin: str, upstream: str = '') -> Dict[str, str]:
    def web(url: str) -> str:
        u = (url or '').strip()
        u = re.sub(r'\.git$', '', u)
        u = u.replace('git@github.com:', 'https://github.com/')
        u = u.replace('git@gitee.com:', 'https://gitee.com/')
        u = re.sub(r'^git@([^:]+):', r'https://\1/', u)
        return u

    origin_web = web(origin)
    upstream_web = web(upstream)
    host = ''
    try:
        host = (urlparse(origin_web).hostname or '').lower()
    except Exception:  # noqa: BLE001
        host = ''
    kind = 'other'
    pr = origin_web
    if 'gitee.com' in host:
        kind = 'gitee'
        base = upstream_web or origin_web
        pr = f'{base}/pulls/new'
    elif 'github.com' in host:
        kind = 'github'
        base = upstream_web or origin_web
        pr = f'{base}/compare'
    elif 'gitlab' in host or host.endswith('.git'):
        kind = 'gitlab'
        pr = f'{origin_web}/-/merge_requests/new'
    elif host and host not in ('github.com', 'gitee.com'):
        kind = 'gitlab'
        pr = f'{origin_web}/-/merge_requests/new'
    return {
        'origin_web': origin_web,
        'upstream_web': upstream_web,
        'kind': kind,
        'pr_url': pr,
    }


class PublishOps:
    def __init__(self, workspace_ops) -> None:
        self.ws = workspace_ops
        self.allow = _env('IDEA_ALLOW_LOCAL_PUBLISH', '1') not in ('0', 'false', 'no')
        here = os.path.dirname(os.path.abspath(__file__))
        self.host_root = os.path.abspath(
            _env('IDEA_HOST_PROJECT_ROOT') or os.path.dirname(here)
        )
        self.timeout = _env_int('IDEA_PUBLISH_TIMEOUT_SECONDS', 3600)
        self.helper_image = _env('IDEA_PUBLISH_HELPER_IMAGE', 'docker:24-cli')
        self.live_url = _env('IDEA_LIVE_URL')
        self._lock = threading.Lock()
        self._busy = False
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._current_id: Optional[str] = None
        os.makedirs(self.ws.data_dir, exist_ok=True)

    def _user_key(self, user: str) -> str:
        return self.ws._sanitize_user(user)

    def repo_paths(self, user: str) -> Dict[str, str]:
        key = self._user_key(user)
        container = os.path.join(self.ws.data_dir, key, 'easyaiot')
        host = os.path.join(self.ws.data_dir_host, key, 'easyaiot')
        git_dir = container if os.path.isdir(os.path.join(container, '.git')) or os.path.islink(container) else host
        if os.path.islink(git_dir):
            try:
                git_dir = os.path.realpath(git_dir)
            except OSError:
                pass
        return {
            'user': key,
            'git_dir': git_dir,
            'host_repo': host,
            'container_repo': container,
        }

    def live_url_for(self, request_host: Optional[str] = None) -> str:
        if self.live_url:
            return self.live_url
        host = self.ws.public_host
        if not host:
            host = (request_host or '127.0.0.1').split(':')[0]
        return f'{self.ws.public_scheme}://{host}:8888'

    def list_modules(self) -> List[Dict[str, Any]]:
        items = []
        for name in PUBLISHABLE:
            host_mod = os.path.join(self.host_root, name)
            script = os.path.join(host_mod, INSTALL_SCRIPT)
            items.append({
                'id': name,
                'publishable': True,
                'host_ready': os.path.isfile(script),
                'reason': '' if os.path.isfile(script) else f'本机未找到 {name}/{INSTALL_SCRIPT}',
            })
        for name, reason in SKIP_REASON.items():
            items.append({
                'id': name,
                'publishable': False,
                'host_ready': False,
                'reason': reason,
            })
        return items

    def _git(self, repo: str, *args: str) -> str:
        try:
            out = subprocess.check_output(
                ['git', '-c', 'safe.directory=*', '-C', repo, *args],
                stderr=subprocess.STDOUT,
                timeout=30,
            )
            return out.decode('utf-8', errors='replace')
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return ''

    def git_remotes(self, user: str) -> Dict[str, Any]:
        paths = self.repo_paths(user)
        repo = paths['git_dir']
        origin = self._git(repo, 'remote', 'get-url', 'origin').strip()
        upstream = self._git(repo, 'remote', 'get-url', 'upstream').strip()
        branch = self._git(repo, 'rev-parse', '--abbrev-ref', 'HEAD').strip()
        links = guess_pr_url(origin, upstream)
        return {
            'repo': repo,
            'exists': os.path.isdir(os.path.join(repo, '.git')) or os.path.isdir(repo),
            'origin': origin,
            'upstream': upstream or self.ws.git_url,
            'branch': branch,
            **links,
            'official': self.ws.git_url,
        }

    def _git_ok(self, repo: str, *args: str) -> None:
        subprocess.check_call(
            ['git', '-c', 'safe.directory=*', '-C', repo, *args],
            timeout=30,
        )

    def set_origin(self, user: str, origin_url: str) -> Dict[str, Any]:
        url = (origin_url or '').strip()
        if not url:
            raise RuntimeError('origin url 不能为空')
        if not re.match(r'^(https://|git@)', url):
            raise RuntimeError('请使用 https:// 或 git@ 仓库地址')
        paths = self.repo_paths(user)
        repo = paths['git_dir']
        if not os.path.isdir(repo):
            raise RuntimeError('工作区仓库还不存在，请先进入 IDE 完成 clone')
        current = self._git(repo, 'remote', 'get-url', 'origin').strip()
        if current:
            self._git_ok(repo, 'remote', 'set-url', 'origin', url)
        else:
            self._git_ok(repo, 'remote', 'add', 'origin', url)
        official = self.ws.git_url
        up = self._git(repo, 'remote', 'get-url', 'upstream').strip()
        if up:
            self._git_ok(repo, 'remote', 'set-url', 'upstream', official)
        else:
            self._git_ok(repo, 'remote', 'add', 'upstream', official)
        return self.git_remotes(user)

    def suggest(self, user: str) -> Dict[str, Any]:
        paths = self.repo_paths(user)
        repo = paths['git_dir']
        files: List[str] = []
        if os.path.isdir(repo):
            raw = self._git(repo, 'status', '--porcelain')
            for line in raw.splitlines():
                path = line[3:].strip()
                if ' -> ' in path:
                    path = path.split(' -> ', 1)[-1]
                if path:
                    files.append(path)
            base = ''
            for ref in ('upstream/main', 'origin/main', 'main'):
                if self._git(repo, 'rev-parse', '--verify', ref).strip():
                    base = ref
                    break
            if base:
                diff = self._git(repo, 'diff', '--name-only', f'{base}...HEAD')
                files.extend([p.strip() for p in diff.splitlines() if p.strip()])
        seen = set()
        uniq = []
        for f in files:
            if f not in seen:
                seen.add(f)
                uniq.append(f)
        counts: Dict[str, int] = {}
        for f in uniq:
            top = f.split('/', 1)[0]
            if top in TOP_IGNORE or top.startswith('.'):
                continue
            if top in SKIP_REASON:
                continue
            if top in PUBLISHABLE:
                counts[top] = counts.get(top, 0) + 1
        suggested = [{'id': k, 'files': v} for k, v in sorted(counts.items())]
        return {
            'repo': repo,
            'changed_files': uniq[:200],
            'suggested': suggested,
            'modules': self.list_modules(),
        }

    def current_job(self) -> Optional[Dict[str, Any]]:
        if self._current_id:
            return self._jobs.get(self._current_id)
        return None

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self._jobs.get(job_id)

    def start_job(
        self,
        user: str,
        modules: List[str],
        action: str = 'publish',
    ) -> Dict[str, Any]:
        if not self.allow:
            raise RuntimeError('本机发布已关闭（IDEA_ALLOW_LOCAL_PUBLISH=0）')
        mods = []
        for m in modules:
            name = (m or '').strip().upper()
            if not name:
                continue
            if name in SKIP_REASON or IDEA_NAME_RE.search(name):
                raise RuntimeError(f'拒绝发布 {name}')
            if name not in PUBLISHABLE:
                raise RuntimeError(f'不支持的模块: {name}')
            mods.append(name)
        if not mods:
            raise RuntimeError('请至少选择一个模块')
        if action not in ('publish', 'restart'):
            raise RuntimeError('action 必须是 publish 或 restart')
        paths = self.repo_paths(user)
        with self._lock:
            if self._busy:
                raise RuntimeError('已有发布任务进行中，请稍后再试')
            self._busy = True
            job_id = uuid.uuid4().hex[:12]
            job = {
                'id': job_id,
                'user': paths['user'],
                'modules': mods,
                'action': action,
                'status': 'queued',
                'log': '',
                'error': '',
                'created_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'finished_at': '',
            }
            self._jobs[job_id] = job
            self._current_id = job_id
        threading.Thread(
            target=self._run_job,
            args=(job_id, paths, mods, action),
            name=f'idea-publish-{job_id}',
            daemon=True,
        ).start()
        return job

    def _append(self, job: Dict[str, Any], line: str) -> None:
        job['log'] = (job.get('log') or '') + line
        if not line.endswith('\n'):
            job['log'] += '\n'
        if len(job['log']) > 400_000:
            job['log'] = job['log'][-300_000:]

    def _run_job(
        self,
        job_id: str,
        paths: Dict[str, str],
        modules: List[str],
        action: str,
    ) -> None:
        job = self._jobs[job_id]
        try:
            job['status'] = 'running'
            host_repo = paths['host_repo']
            for mod in modules:
                self._append(job, f'===== {action} {mod} =====')
                if action == 'publish':
                    src = os.path.join(host_repo, mod)
                    script = os.path.join(src, INSTALL_SCRIPT)
                    if not os.path.isfile(script):
                        raise RuntimeError(f'工作区没有 {mod}/{INSTALL_SCRIPT}，请先进入 IDE 完成全仓 clone')
                    self._run_script(job, src, INSTALL_SCRIPT, 'build')
                host_mod = os.path.join(self.host_root, mod)
                host_script = os.path.join(host_mod, INSTALL_SCRIPT)
                if not os.path.isfile(host_script):
                    raise RuntimeError(f'本机栈没有 {mod}/{INSTALL_SCRIPT}（IDEA_HOST_PROJECT_ROOT={self.host_root}）')
                self._run_script(job, host_mod, INSTALL_SCRIPT, 'restart')
                self._append(job, f'===== {mod} 完成 =====')
            job['status'] = 'success'
        except Exception as exc:  # noqa: BLE001
            logger.exception('publish job failed')
            job['status'] = 'error'
            job['error'] = str(exc)
            self._append(job, f'ERROR: {exc}')
        finally:
            job['finished_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            with self._lock:
                self._busy = False

    def _run_script(self, job: Dict[str, Any], workdir: str, script: str, command: str) -> None:
        env = os.environ.copy()
        env['EASYAIOT_SKIP_IMAGE_PROMPT'] = '1'
        env['DEBIAN_FRONTEND'] = 'noninteractive'
        local_script = os.path.join(workdir, script)
        # 本机直接跑（dev / 同路径挂载）
        if os.path.isfile(local_script) and os.path.samefile(workdir, workdir):
            try:
                proc = subprocess.Popen(
                    ['bash', script, command],
                    cwd=workdir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    env=env,
                    text=True,
                    bufsize=1,
                )
                assert proc.stdout is not None
                deadline = time.time() + self.timeout
                for line in proc.stdout:
                    self._append(job, line.rstrip('\n'))
                    if time.time() > deadline:
                        proc.kill()
                        raise RuntimeError('发布超时')
                rc = proc.wait()
                if rc != 0:
                    raise RuntimeError(f'{script} {command} 退出码 {rc}')
                return
            except FileNotFoundError:
                pass
        # 门户在容器内：用 docker.cli 在宿主机路径执行，避免 docker build 上下文路径不对
        self._run_via_docker_cli(job, workdir, script, command)

    def _run_via_docker_cli(self, job: Dict[str, Any], workdir: str, script: str, command: str) -> None:
        client = self.ws.client
        try:
            client.images.get(self.helper_image)
        except Exception:  # noqa: BLE001
            self._append(job, f'拉取辅助镜像 {self.helper_image} …')
            client.images.pull(self.helper_image)
        volumes = {
            '/var/run/docker.sock': {'bind': '/var/run/docker.sock', 'mode': 'rw'},
            workdir: {'bind': workdir, 'mode': 'rw'},
        }
        self._append(job, f'$ bash {script} {command}  (cwd={workdir})')
        container = client.containers.run(
            image=self.helper_image,
            command=['bash', script, command],
            volumes=volumes,
            working_dir=workdir,
            environment={
                'EASYAIOT_SKIP_IMAGE_PROMPT': '1',
                'DOCKER_HOST': 'unix:///var/run/docker.sock',
            },
            detach=True,
            network_mode='host',
        )
        try:
            deadline = time.time() + self.timeout
            for chunk in container.logs(stream=True, follow=True):
                text = chunk.decode('utf-8', errors='replace') if isinstance(chunk, bytes) else str(chunk)
                self._append(job, text.rstrip('\n'))
                if time.time() > deadline:
                    container.kill()
                    raise RuntimeError('发布超时')
            result = container.wait()
            code = int(result.get('StatusCode', 1))
            if code != 0:
                raise RuntimeError(f'{script} {command} 退出码 {code}')
        finally:
            try:
                container.remove(force=True)
            except Exception:  # noqa: BLE001
                pass
