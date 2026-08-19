from __future__ import annotations

import os
import shutil
import time
from typing import Dict, List

from sentinel.base import ComponentState, ProbeLevel, ProbeResult, SentinelContext
from sentinel import probe_steps as ps

from sentinel.registry_loader import load_functions_registry

# 兜底：功能 → 期望组件（优先读 registry/functions.yaml）
FUNCTION_COMPONENTS: Dict[str, List[str]] = {
    'algorithm': ['nfs_mount', 'runtime', 'ffmpeg', 'video_bundle_realtime'],
    'forward': ['srs_live', 'runtime', 'ffmpeg'],
    'live': ['docker', 'srs_live'],
    'train': ['nfs_mount', 'cuda', 'gpu_vram', 'model_train_bundle'],
    'llm': ['cuda', 'gpu_vram', 'llm_bundle'],
    'label': ['nfs_mount', 'runtime', 'video_bundle_realtime'],
    'infer': ['nfs_mount', 'runtime', 'video_bundle_realtime'],
    'mqtt': ['docker'],
    'nfs': ['nfs_mount'],
    'transform': ['runtime'],
}


def expected_components_for(functions: List[str]) -> List[str]:
    mapping = dict(FUNCTION_COMPONENTS)
    registry = load_functions_registry().get('functions') or {}
    if isinstance(registry, dict):
        for fn_id, spec in registry.items():
            if isinstance(spec, dict) and spec.get('components'):
                mapping[str(fn_id)] = [str(c) for c in spec['components']]
    ordered: List[str] = []
    seen = set()
    for fn in functions:
        for comp in mapping.get(fn, []):
            if comp not in seen:
                seen.add(comp)
                ordered.append(comp)
    return ordered


def _profiles_for(profile: str) -> List[str]:
    functions = [part.strip() for part in (profile or '').split(',') if part.strip()]
    return expected_components_for(functions)


def _timed_probe(fn):
    def wrapper(ctx: SentinelContext, level: ProbeLevel) -> ProbeResult:
        start = time.time()
        result = fn(ctx, level)
        result.duration_ms = int((time.time() - start) * 1000)
        result.probe_level = level
        return result
    return wrapper


@_timed_probe
def probe_runtime(ctx: SentinelContext, level: ProbeLevel) -> ProbeResult:
    runtime_bin = ps.resolve_runtime_bin(ctx.env)
    if not runtime_bin:
        return ProbeResult(ComponentState.UNAVAILABLE, 'RUNTIME 二进制不存在')
    evidence = {'path': runtime_bin}
    version = ps.read_runtime_version(runtime_bin)
    if version:
        evidence['version'] = version
    smoke = ps.smoke_runtime(runtime_bin)
    evidence['smoke'] = {
        'ok': bool(smoke.get('ok')),
        'code': smoke.get('code'),
        'stderr': (smoke.get('stderr') or '')[:400],
    }
    if not smoke.get('ok'):
        detail = (smoke.get('stderr') or smoke.get('stdout') or '无法执行 --version').strip()
        return ProbeResult(
            ComponentState.UNAVAILABLE,
            f'RUNTIME 无法执行（OS/ABI 不匹配或动态库缺失）: {detail[:240]}',
            evidence=evidence,
        )
    return ProbeResult(ComponentState.READY, evidence=evidence)


@_timed_probe
def probe_nfs_mount(ctx: SentinelContext, level: ProbeLevel) -> ProbeResult:
    if not ctx.cluster_mode:
        return ProbeResult(ComponentState.READY, evidence={'clusterMode': False})
    if ctx.nfs_mount_ready:
        root = (
            ctx.env.get('MEDIA_HOST_DATA_ROOT')
            or ctx.env.get('NFS_MOUNT_ROOT')
            or ctx.env.get('CEPH_MOUNT_ROOT')
            or '/mnt/easyaiot-media'
        )
        return ProbeResult(ComponentState.READY, evidence={'mountRoot': root, 'fs': 'nfs'})
    return ProbeResult(ComponentState.UNAVAILABLE, 'NFS 共享存储未挂载就绪')


@_timed_probe
def probe_cuda(ctx: SentinelContext, level: ProbeLevel) -> ProbeResult:
    if not ctx.gpu_info:
        return ProbeResult(ComponentState.UNAVAILABLE, '未检测到 GPU')
    names = [str(g.get('name') or '') for g in ctx.gpu_info]
    return ProbeResult(ComponentState.READY, evidence={'gpuCount': len(ctx.gpu_info), 'names': names})


@_timed_probe
def probe_gpu_vram(ctx: SentinelContext, level: ProbeLevel) -> ProbeResult:
    dep = ctx.component_states.get('cuda')
    if dep and dep.state == ComponentState.UNAVAILABLE:
        return ProbeResult(ComponentState.SKIPPED, f'depends cuda: {dep.reason}')
    free_mb = ps.sum_free_vram_mb(ctx.gpu_info)
    evidence = {'freeVramMb': round(free_mb, 1)}
    if free_mb <= 0 and ctx.gpu_info:
        return ProbeResult(ComponentState.DEGRADED, 'GPU 显存数据不可用', evidence=evidence)
    if free_mb < 2048:
        return ProbeResult(ComponentState.DEGRADED, f'空闲显存偏低: {free_mb:.0f}MB', evidence=evidence)
    return ProbeResult(ComponentState.READY, evidence=evidence)


@_timed_probe
def probe_srs_live(ctx: SentinelContext, level: ProbeLevel) -> ProbeResult:
    if not ps.port_open('127.0.0.1', 1935):
        return ProbeResult(ComponentState.UNAVAILABLE, 'RTMP 1935 端口未监听')
    evidence: Dict[str, object] = {'port1935': True}
    if level != ProbeLevel.L0:
        evidence['dockerSrs'] = ps.docker_running('srs')
        evidence['apiOk'] = ps.http_ok('http://127.0.0.1:1985/api/v1/summaries')
    return ProbeResult(ComponentState.READY, evidence=evidence)


@_timed_probe
def probe_ffmpeg(ctx: SentinelContext, level: ProbeLevel) -> ProbeResult:
    paths = [
        '/opt/easyaiot/tools/ffmpeg/bin/ffmpeg',
        '/opt/easyaiot/tools/ffmpeg/ffmpeg',
        shutil.which('ffmpeg') or '',
    ]
    for path in paths:
        if path and ps.file_executable(path):
            return ProbeResult(ComponentState.READY, evidence={'path': path})
    return ProbeResult(ComponentState.UNAVAILABLE, 'ffmpeg 不可用')


@_timed_probe
def probe_docker(ctx: SentinelContext, level: ProbeLevel) -> ProbeResult:
    result = ps.run_command(['docker', 'info'], timeout=5)
    if result['ok']:
        return ProbeResult(ComponentState.READY)
    return ProbeResult(ComponentState.UNAVAILABLE, 'Docker 不可用')


@_timed_probe
def probe_model_train_bundle(ctx: SentinelContext, level: ProbeLevel) -> ProbeResult:
    ai_root = ctx.env.get('AI_ROOT') or '/opt/easyaiot/AI'
    launcher = ps.bundle_launcher(ai_root, 'model_train')
    worker = os.path.join(ai_root, 'services', 'train_worker', 'run_worker.py')
    if ps.file_executable(launcher) and ps.file_exists(worker):
        return ProbeResult(ComponentState.READY, evidence={'launcher': launcher, 'worker': worker})
    missing = []
    if not ps.file_executable(launcher):
        missing.append('model_train bundle')
    if not ps.file_exists(worker):
        missing.append('train_worker')
    return ProbeResult(ComponentState.UNAVAILABLE, '、'.join(missing) + ' 缺失')


@_timed_probe
def probe_video_bundle_realtime(ctx: SentinelContext, level: ProbeLevel) -> ProbeResult:
    video_root = ctx.env.get('VIDEO_ROOT') or '/opt/easyaiot/VIDEO'
    launcher = ps.bundle_launcher(video_root, 'algorithm_realtime')
    script = os.path.join(video_root, 'services', 'realtime_algorithm_service', 'run_deploy.py')
    if ps.file_executable(launcher) and ps.file_exists(script):
        return ProbeResult(ComponentState.READY, evidence={'launcher': launcher})
    return ProbeResult(ComponentState.UNAVAILABLE, 'algorithm_realtime bundle 缺失')


@_timed_probe
def probe_llm_bundle(ctx: SentinelContext, level: ProbeLevel) -> ProbeResult:
    ai_root = ctx.env.get('AI_ROOT') or '/opt/easyaiot/AI'
    launcher = ps.bundle_launcher(ai_root, 'llm_service')
    script = os.path.join(ai_root, 'services', 'llm_service', 'run_deploy.py')
    if ps.file_executable(launcher) and ps.file_exists(script):
        return ProbeResult(ComponentState.READY, evidence={'launcher': launcher, 'script': script})
    missing = []
    if not ps.file_executable(launcher):
        missing.append('llm_service bundle')
    if not ps.file_exists(script):
        missing.append('llm_service/run_deploy.py')
    return ProbeResult(ComponentState.UNAVAILABLE, '、'.join(missing) + ' 缺失')


COMPONENT_PROBES = {
    'runtime': probe_runtime,
    'nfs_mount': probe_nfs_mount,
    'cuda': probe_cuda,
    'gpu_vram': probe_gpu_vram,
    'srs_live': probe_srs_live,
    'ffmpeg': probe_ffmpeg,
    'docker': probe_docker,
    'model_train_bundle': probe_model_train_bundle,
    'video_bundle_realtime': probe_video_bundle_realtime,
    'llm_bundle': probe_llm_bundle,
}

COMPONENT_DEPENDS: Dict[str, List[str]] = {
    'gpu_vram': ['cuda'],
    'llm_bundle': ['cuda'],
}
