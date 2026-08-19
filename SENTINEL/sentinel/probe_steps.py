from __future__ import annotations

import os
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib import request as urlrequest


def file_exists(path: str) -> bool:
    return bool(path) and os.path.isfile(path)


def file_executable(path: str) -> bool:
    return bool(path) and os.path.isfile(path) and os.access(path, os.X_OK)


def port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def http_ok(url: str, timeout: float = 2.0) -> bool:
    try:
        with urlrequest.urlopen(url, timeout=timeout) as resp:
            return 200 <= resp.status < 300
    except Exception:
        return False


def run_command(cmd: List[str], timeout: float = 8.0) -> Dict[str, Any]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {
            'ok': proc.returncode == 0,
            'stdout': (proc.stdout or '').strip(),
            'stderr': (proc.stderr or '').strip(),
            'code': proc.returncode,
        }
    except Exception as exc:
        return {'ok': False, 'stdout': '', 'stderr': str(exc), 'code': -1}


def docker_running(name_pattern: str) -> bool:
    result = run_command(['docker', 'ps', '--format', '{{.Names}}'], timeout=5)
    if not result['ok']:
        return False
    needle = (name_pattern or '').lower()
    for line in result['stdout'].splitlines():
        if needle and needle in line.lower():
            return True
    return False


def resolve_runtime_root(runtime_bin: str) -> Optional[str]:
    if not runtime_bin:
        return None
    bin_path = Path(runtime_bin)
    if bin_path.parent.name == 'bin':
        return str(bin_path.parent.parent)
    if bin_path.parent.name == 'build':
        return str(bin_path.parent.parent)
    return str(bin_path.parent)


def smoke_runtime(runtime_bin: str, timeout: float = 8.0) -> Dict[str, Any]:
    """真正 exec RUNTIME --version。文件存在不算就绪。"""
    root = resolve_runtime_root(runtime_bin) or '/opt/easyaiot/RUNTIME'
    smoke = os.path.join(root, 'scripts', 'smoke_runtime.sh')
    if os.path.isfile(smoke):
        result = run_command(['bash', smoke, root], timeout=timeout)
        result['ok'] = bool(result.get('ok')) and 'SMOKE_FAIL' not in (
            (result.get('stderr') or '') + '\n' + (result.get('stdout') or '')
        )
        return result
    env_sh = os.path.join(root, 'env.sh')
    script = (
        'unset LD_LIBRARY_PATH LD_PRELOAD; '
        + (f'. "{env_sh}"; ' if os.path.isfile(env_sh) else '')
        + f'"{runtime_bin}" --version'
    )
    return run_command(['bash', '-c', script], timeout=timeout)


def read_os_release() -> Dict[str, str]:
    data: Dict[str, str] = {}
    path = Path('/etc/os-release')
    if not path.is_file():
        return data
    try:
        for line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            value = value.strip().strip('"').strip("'")
            data[key.strip()] = value
    except OSError:
        return data
    return data


def os_family_from_release(os_release: Optional[Dict[str, str]] = None) -> str:
    info = os_release if os_release is not None else read_os_release()
    distro = (info.get('ID') or '').strip().lower()
    like = (info.get('ID_LIKE') or '').strip().lower()
    version_id = (info.get('VERSION_ID') or '').strip()
    major = 0
    digits = []
    for ch in version_id:
        if ch.isdigit():
            digits.append(ch)
        else:
            break
    if digits:
        major = int(''.join(digits))
    if distro == 'ubuntu':
        return f'ubuntu{major}' if major else 'ubuntu'
    if distro == 'debian':
        return f'debian{major}' if major else 'debian'
    if distro == 'openeuler':
        return f'openeuler{major}' if major else 'openeuler'
    if 'kylin' in distro:
        return f'kylin{major}' if major else 'kylin'
    named_el = {
        'rhel', 'centos', 'rocky', 'almalinux', 'ol', 'alinux',
        'opencloudos', 'anolis', 'tencentos',
    }
    if distro in named_el or any(token in like for token in ('rhel', 'centos', 'fedora')):
        if major >= 9:
            return 'el9'
        if major == 8:
            return 'el8'
        if major == 7:
            return 'el7'
        return 'el'
    slug = ''.join(ch for ch in distro if ch.isalnum())
    if not slug:
        return 'linux'
    return f'{slug}{major}' if major else slug


def resolve_runtime_bin(env: Dict[str, str]) -> Optional[str]:
    explicit = (env.get('RUNTIME_BIN') or os.environ.get('RUNTIME_BIN') or '').strip()
    candidates = []
    if explicit:
        candidates.append(explicit)
    candidates.extend([
        '/opt/easyaiot/RUNTIME/bin/RUNTIME',
        '/opt/easyaiot/RUNTIME/build/RUNTIME',
    ])
    for path in candidates:
        if file_executable(path):
            return path
    return None


def read_runtime_version(runtime_bin: str) -> Optional[str]:
    bin_path = Path(runtime_bin)
    version_files = []
    if bin_path.parent.name == 'bin':
        version_files.append(bin_path.parent.parent / 'VERSION')
    version_files.extend([
        bin_path.parent / 'VERSION',
        Path('/opt/easyaiot/RUNTIME/VERSION'),
        Path('/opt/easyaiot/RUNTIME/build/VERSION'),
    ])
    for vf in version_files:
        if not vf.is_file():
            continue
        try:
            for line in vf.read_text(encoding='utf-8', errors='ignore').splitlines():
                line = line.strip()
                if line.startswith('version='):
                    return line.split('=', 1)[1].strip().strip('"').strip("'")
                if line.startswith('VERSION='):
                    return line.split('=', 1)[1].strip().strip('"').strip("'")
        except OSError:
            continue
    result = run_command([runtime_bin, '--version'], timeout=5)
    if result['ok'] and result['stdout']:
        return result['stdout'].splitlines()[0][:120]
    return None


def bundle_launcher(root: str, bundle: str) -> str:
    return os.path.join(root, '.bundles', bundle, 'run-python.sh')


def sum_free_vram_mb(gpu_info: List[Dict[str, Any]]) -> float:
    total = 0.0
    for item in gpu_info or []:
        try:
            total_mb = float(item.get('mem_total_mb') or 0)
            used_mb = float(item.get('mem_used_mb') or 0)
            total += max(0.0, total_mb - used_mb)
        except (TypeError, ValueError):
            continue
    return total
