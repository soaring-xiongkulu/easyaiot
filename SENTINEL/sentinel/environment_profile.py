"""采集节点环境画像。"""
from __future__ import annotations

import os
import platform
import shutil
from typing import Any, Dict, List

from sentinel import probe_steps as ps


def collect_environment_profile(
    *,
    gpu_info: List[Dict[str, Any]] | None = None,
    cluster_mode: bool = False,
    nfs_mount_root: str = '',
    nfs_mount_ready: bool = False,
    ceph_mount_root: str = '',
    ceph_mount_ready: bool = False,
    agent_version: str = '',
    agent_port: int = 9100,
) -> Dict[str, Any]:
    os_release = ps.read_os_release()
    runtime_bin = ps.resolve_runtime_bin(os.environ)
    ffmpeg = next((p for p in (
        shutil.which('ffmpeg') or '',
        '/opt/easyaiot/tools/ffmpeg/bin/ffmpeg',
        '/opt/easyaiot/tools/ffmpeg/ffmpeg',
    ) if p and ps.file_executable(p)), None)
    docker_ok = ps.run_command(['docker', 'info'], timeout=3).get('ok', False)
    runtime_smoke = ps.smoke_runtime(runtime_bin) if runtime_bin else None
    return {
        'os': {
            'system': platform.system(),
            'release': platform.release(),
            'arch': platform.machine(),
            'id': os_release.get('ID') or '',
            'versionId': os_release.get('VERSION_ID') or '',
            'family': ps.os_family_from_release(os_release),
        },
        'agent': {
            'version': agent_version,
            'port': agent_port,
        },
        'gpu': gpu_info or [],
        'software': {
            'runtime': {
                'path': runtime_bin or '',
                'version': ps.read_runtime_version(runtime_bin) if runtime_bin else None,
                'executable': bool(runtime_smoke and runtime_smoke.get('ok')),
            },
            'python': platform.python_version(),
            'ffmpeg': ffmpeg if ps.file_executable(ffmpeg) else None,
            'docker': docker_ok,
        },
        'storage': {
            'cluster_mode': cluster_mode,
            'nfs_mount_root': nfs_mount_root or ceph_mount_root,
            'nfs_mount_ready': bool(nfs_mount_ready or ceph_mount_ready),
        },
        'network': {
            'srs_rtmp_port_open': ps.port_open('127.0.0.1', 1935),
        },
    }
