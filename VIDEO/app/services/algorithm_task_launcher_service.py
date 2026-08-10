"""
算法任务服务启动器
用于自动启动算法任务相关的服务（抽帧器、推送器、排序器）

@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import os
import sys
import json
import subprocess
import logging
import threading
import signal
import time
from typing import Dict, Optional, Tuple
from datetime import datetime

from models import db, AlgorithmTask
from app.utils.node_remote_python import resolve_video_bundle_python
from .algorithm_task_daemon import AlgorithmTaskDaemon
from .snap_space_service import get_snap_space_by_device_id, create_snap_space_for_device

logger = logging.getLogger(__name__)

WORKLOAD_TYPE_ALGORITHM = 'algorithm_task'


def _start_post_process_cluster(task: AlgorithmTask) -> Tuple[bool, str]:
    from app.services.post_process_launcher_service import start_post_process_workers
    return start_post_process_workers(task)


def _stop_post_process_cluster(task_id: int, task: Optional[AlgorithmTask] = None) -> None:
    from app.services.post_process_launcher_service import stop_post_process_workers
    stop_post_process_workers(task_id, task)


# 存储已启动的守护进程对象（参考 AI 模块的 deploy_service.py）
_running_daemons: Dict[int, AlgorithmTaskDaemon] = {}
_daemons_lock = threading.Lock()
# 启动锁：防止并发启动同一个任务
_starting_tasks: Dict[int, threading.Lock] = {}
_starting_lock = threading.Lock()
# 停止请求代次：start/restart 会递增以作废尚未执行的异步 stop，避免 stop→start 竞态误杀新进程
_stop_request_id: Dict[int, int] = {}
_stop_request_lock = threading.Lock()


def _issue_stop_request(task_id: int) -> int:
    with _stop_request_lock:
        request_id = _stop_request_id.get(task_id, 0) + 1
        _stop_request_id[task_id] = request_id
        return request_id


def _cancel_pending_stop_requests(task_id: int) -> None:
    with _stop_request_lock:
        _stop_request_id[task_id] = _stop_request_id.get(task_id, 0) + 1


def _is_stop_request_current(task_id: int, request_id: int) -> bool:
    with _stop_request_lock:
        return _stop_request_id.get(task_id) == request_id


def _get_video_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _use_remote_deploy(task: AlgorithmTask) -> bool:
    from app.utils.node_client import is_remote_deploy_enabled
    if not is_remote_deploy_enabled():
        return False
    policy = getattr(task, 'schedule_policy', None) or 'local'
    return policy in ('auto', 'node')


def _heartbeat_stale(last_heartbeat, timeout_sec: int) -> bool:
    if not last_heartbeat:
        return True
    return (datetime.utcnow() - last_heartbeat).total_seconds() > timeout_sec


def _algorithm_heartbeat_failover_seconds() -> int:
    return max(30, int(os.getenv('ALGORITHM_HEARTBEAT_FAILOVER_SECONDS', '90')))


def _is_compute_node_online(node_id: int) -> bool:
    from app.utils import node_client
    try:
        node = node_client.get_node(node_id)
        return str(node.get('status') or '').lower() == 'online'
    except Exception as e:
        logger.warning('查询节点状态失败 node_id=%s: %s', node_id, e)
        return False


def _local_algorithm_daemon_running(task_id: int) -> bool:
    with _daemons_lock:
        if task_id not in _running_daemons:
            return False
        daemon = _running_daemons[task_id]
        return (
            daemon._running
            and daemon._process is not None
            and daemon._process.poll() is None
        )


def _algorithm_task_service_healthy(task: AlgorithmTask) -> bool:
    """判断算法任务服务是否仍在运行（本机守护进程 / 远程心跳）。"""
    if _local_algorithm_daemon_running(task.id):
        return True

    timeout = _algorithm_heartbeat_failover_seconds()
    if _heartbeat_stale(task.service_last_heartbeat, timeout):
        return False

    if _use_remote_deploy(task) and task.node_id:
        return _is_compute_node_online(int(task.node_id))

    return task.run_status in ('running', 'restarting')


def _parse_task_model_ids(task: AlgorithmTask) -> list:
    raw = getattr(task, 'model_ids', None)
    if not raw:
        return []
    try:
        ids = json.loads(raw) if isinstance(raw, str) else raw
        return [int(x) for x in ids]
    except (TypeError, ValueError, json.JSONDecodeError):
        return []


def _is_cluster_mode_enabled() -> bool:
    try:
        from cluster_storage import is_cluster_mode
        return is_cluster_mode()
    except ImportError:
        return os.getenv('CLUSTER_MODE', '').strip().lower() in ('1', 'true', 'yes', 'on')


def _ensure_task_models_on_cluster(task: AlgorithmTask) -> Tuple[bool, str]:
    """集群模式下将任务关联模型预同步至 CephFS 共享目录。"""
    if not _is_cluster_mode_enabled():
        return True, ''
    model_ids = _parse_task_model_ids(task)
    if not model_ids:
        return True, ''
    import requests
    ai_url = os.getenv('AI_SERVICE_URL', 'http://localhost:5000').rstrip('/')
    jwt = os.getenv('JWT_TOKEN', '')
    headers = {'Content-Type': 'application/json'}
    if jwt:
        headers['X-Authorization'] = f'Bearer {jwt}'
    try:
        resp = requests.post(
            f'{ai_url}/model/sync-to-cluster/batch',
            headers=headers,
            json={'model_ids': model_ids},
            timeout=(5, 300),
        )
        body = resp.json() if resp.content else {}
        if resp.status_code == 200 and body.get('code') == 0:
            logger.info('任务模型已预同步至集群 task_id=%s model_ids=%s', task.id, model_ids)
            return True, ''
        msg = body.get('msg') or resp.text or f'HTTP {resp.status_code}'
        logger.error('集群模型预同步失败 task_id=%s: %s', task.id, msg)
        return False, msg
    except Exception as e:
        logger.error('集群模型预同步异常 task_id=%s: %s', task.id, e, exc_info=True)
        return False, str(e)


def _task_capabilities(task_type: str) -> list:
    if task_type == 'snap':
        return ['algorithm_snap']
    if task_type == 'patrol':
        return ['algorithm_patrol']
    return ['algorithm_realtime']


def _resolve_video_control_url() -> str:
    gateway = os.getenv('JAVA_BACKEND_URL', os.getenv('GATEWAY_URL', 'http://localhost:48080')).rstrip('/')
    return f'{gateway}/admin-api/video'


def _inject_sam_supplement_env(env: dict, task) -> None:
    """将算法任务的 SAM 补充配置写入子进程环境变量。"""
    enabled = bool(getattr(task, 'sam_supplement_enabled', False))
    env['SAM_SUPPLEMENT_ENABLED'] = 'true' if enabled else 'false'
    if not enabled:
        return
    cfg = {}
    raw = getattr(task, 'sam_supplement_config', None)
    if raw:
        try:
            cfg = json.loads(raw) if isinstance(raw, str) else (raw or {})
        except Exception:
            cfg = {}
    env['SAM_SUPPLEMENT_CONFIG'] = json.dumps(cfg, ensure_ascii=False)
    env['SAM_PIPELINE_MODE'] = str(cfg.get('pipeline_mode', 'none'))
    prompts = cfg.get('text_prompts') or []
    env['SAM_TEXT_PROMPTS'] = ','.join(prompts) if isinstance(prompts, list) else str(prompts)
    env['SAM_CONF'] = str(cfg.get('conf', 0.45))
    env['SAM_TRIGGER'] = str(cfg.get('trigger', 'on_interval'))
    env['SAM_INTERVAL_FRAMES'] = str(cfg.get('interval_frames', 25))
    env['SAM_MERGE_IOU'] = str(cfg.get('merge_iou', 0.5))
    env['SAM_RETURN_MASKS'] = 'true' if cfg.get('return_masks', True) else 'false'
    ai_url = os.getenv('AI_SERVICE_URL')
    if ai_url:
        env['AI_SERVICE_URL'] = ai_url


def _inject_realtime_sampling_env(env: dict, task) -> None:
    """将实时任务的抽帧间隔与运动门控配置写入子进程环境变量。"""
    if getattr(task, 'task_type', '') != 'realtime':
        return
    enabled = getattr(task, 'motion_gate_enabled', False)
    env['MOTION_GATE_ENABLED'] = 'true' if enabled else 'false'
    raw = getattr(task, 'motion_gate_config', None)
    if raw:
        if isinstance(raw, str):
            env['MOTION_GATE_CONFIG'] = raw
        else:
            env['MOTION_GATE_CONFIG'] = json.dumps(raw, ensure_ascii=False)


def _build_task_deploy_env(task_id: int, task_type: str, log_path: str, server_host: str, task=None) -> dict:
    env = {}
    for key in (
        'DATABASE_URL', 'GATEWAY_URL', 'GB28181_SERVICE_URL', 'JWT_TOKEN', 'JAVA_BACKEND_URL',
        'GB28181_HTTP_READ_TIMEOUT', 'GB28181_PLAY_PROTOCOL', 'GB28181_HEVC_RTSP_FIRST',
        'GB28181_OPENCV_RTMP_FALLBACK_RTSP', 'POD_IP', 'HOST_IP', 'AI_SERVICE_URL',
        'USE_GPU', 'GPU_IDS', 'GPU_POLICY', 'INFER_GPU_POLICY', 'FFMPEG_GPU_POLICY',
        'CUDA_VISIBLE_DEVICES', 'NVIDIA_VISIBLE_DEVICES', 'ORT_EXECUTION_PROVIDERS',
        'KAFKA_BOOTSTRAP_SERVERS', 'MINIO_ENDPOINT', 'MINIO_ACCESS_KEY', 'MINIO_SECRET_KEY',
        'MINIO_SECURE', 'NACOS_SERVER', 'VIDEO_ENV',
        'CLUSTER_MODE', 'MEDIA_HOST_DATA_ROOT', 'MEDIA_RECORD_DIR', 'MEDIA_SNAP_DIR',
        'MEDIA_UPLOAD_MODE', 'MEDIA_SNAP_UPLOAD_MODE', 'ALERT_IMAGES_DIR',
        'IOT_SINK_API_URL', 'IOT_SINK_USE_GATEWAY', 'IOT_SINK_HOST', 'IOT_SINK_PORT',
        'EASYAIOT_DEPLOY_PROFILE', 'ALERT_HOOK_URL', 'ALERT_KEEP_LATEST',
        'VIDEO_SERVICE_HOST', 'VIDEO_SERVICE_URL', 'VIDEO_API_USE_GATEWAY',
        'FFMPEG_HWACCEL', 'FFMPEG_THREADS', 'FFMPEG_PRESET', 'FFMPEG_VIDEO_BITRATE', 'FFMPEG_GOP_SIZE',
        'AI_RTSP_TRANSPORT', 'OPENCV_FFMPEG_RTSP_TRANSPORT', 'FFMPEG_RTSP_TRANSPORT',
        'OPENCV_FFMPEG_CAPTURE_OPTIONS', 'RTSP_OPEN_TIMEOUT_MSEC', 'RTSP_READ_TIMEOUT_MSEC',
        'REALTIME_TARGET_STREAMS', 'REALTIME_THREAD_QUEUE_SIZE', 'REALTIME_MAX_MUXING_QUEUE_SIZE',
        'REALTIME_RW_TIMEOUT_US', 'REALTIME_RTSP_OPEN_TIMEOUT_US', 'REALTIME_NVENC_SKIP_TEST',
        'REALTIME_NVENC_PRESET', 'REALTIME_STREAM_STAGGER_SEC',
        'STREAM_FORWARD_TARGET_STREAMS', 'STREAM_FORWARD_THREAD_QUEUE_SIZE',
        'STREAM_FORWARD_MAX_MUXING_QUEUE_SIZE', 'STREAM_FORWARD_NVENC_SKIP_TEST',
        'STREAM_FORWARD_NVENC_PRESET', 'STREAM_FORWARD_RELAY_STAGGER_SEC',
    ):
        val = os.getenv(key)
        if val is not None and val != '':
            env[key] = val

    video_control_url = _resolve_video_control_url()
    video_service_port = os.getenv('FLASK_RUN_PORT', '6000')
    env['PYTHONUNBUFFERED'] = '1'
    env['TASK_ID'] = str(task_id)
    env['VIDEO_SERVICE_PORT'] = video_service_port
    env['VIDEO_CONTROL_URL'] = video_control_url
    if task_type == 'patrol':
        env['VIDEO_HEARTBEAT_URL'] = f'{video_control_url}/algorithm/heartbeat/patrol'
    else:
        env['VIDEO_HEARTBEAT_URL'] = f'{video_control_url}/algorithm/heartbeat/realtime'
    env['LOG_PATH'] = log_path
    env['POD_IP'] = server_host
    env['HOST_IP'] = server_host

    kafka_bootstrap = env.get('KAFKA_BOOTSTRAP_SERVERS', os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'))
    if 'Kafka' in kafka_bootstrap or 'kafka-server' in kafka_bootstrap:
        env['KAFKA_BOOTSTRAP_SERVERS'] = os.getenv('NODE_REMOTE_KAFKA', kafka_bootstrap)
    else:
        env['KAFKA_BOOTSTRAP_SERVERS'] = kafka_bootstrap
    from app.utils.node_remote_tools import apply_remote_toolchain_env
    apply_remote_toolchain_env(env)
    if task is not None:
        _inject_sam_supplement_env(env, task)
        _inject_realtime_sampling_env(env, task)
    return env


def _deploy_task_on_remote_node(task_id: int, task: AlgorithmTask) -> Tuple[bool, str, bool]:
    from app.utils import node_client
    from app.services.runtime_config_service import (
        normalize_executor,
        generate_runtime_ini_content,
        REMOTE_RUNTIME_BIN,
        REMOTE_RUNTIME_LD_LIBRARY_PATH,
    )

    ok, sync_msg = _ensure_task_models_on_cluster(task)
    if not ok:
        return (False, f'集群模型预同步失败: {sync_msg}', False)

    policy = getattr(task, 'schedule_policy', None) or 'local'
    target_node_id = getattr(task, 'target_node_id', None)
    if policy == 'node' and not target_node_id:
        return (False, '已选择指定节点但未配置目标节点', False)

    allocation = node_client.allocate_node(
        WORKLOAD_TYPE_ALGORITHM,
        str(task_id),
        capabilities=_task_capabilities(task.task_type),
        target_node_id=target_node_id if policy == 'node' else None,
        prefer_gpu=getattr(task, 'prefer_gpu', True),
        sticky=True,
    )

    node_id = allocation['nodeId']
    host = allocation['host']
    gpu_ids = allocation.get('gpuIds')

    video_root_remote = os.getenv('NODE_REMOTE_VIDEO_ROOT', '/opt/easyaiot/VIDEO')
    log_dir = os.path.join(video_root_remote, 'logs', f'task_{task_id}')
    executor = normalize_executor(getattr(task, 'executor', None) or 'cpp')
    files = None
    work_dir = video_root_remote

    if executor == 'cpp':
        if task.task_type not in ('realtime', 'snap', 'patrol'):
            return (False, f'executor=cpp 不支持任务类型: {task.task_type}', False)
        # 远程 cpp 依赖节点已分发 RUNTIME；未安装时给出可操作提示
        try:
            rt_check = node_client.check_runtime_cpp_ready(int(node_id))
            ready = bool(rt_check.get('runtimeReady') or rt_check.get('success'))
            if not ready:
                detail = (rt_check.get('message') or '').strip() or 'RUNTIME 未安装或不可用'
                return (
                    False,
                    f'节点 {host} 未就绪高性能执行器：{detail}。'
                    f'请先在 WEB「节点管理 → 业务运行时分发」对该节点「分发 RUNTIME」，'
                    f'或在该节点执行原子安装：VIDEO_BASE_URL=http://<中心VIDEO>:6000 '
                    f'bash .scripts/docker/install_linux.sh runtime',
                    False,
                )
            # 版本不一致仅告警，不阻断启动（便于运维窗口内手工升级）
            try:
                from app.services.runtime_config_service import read_runtime_version_info
                local_info = read_runtime_version_info()
                local_ver = (local_info.get('version') or '').strip()
                node_ver = (
                    (rt_check.get('version') or '').strip()
                    or (rt_check.get('runtimeVersion') or '').strip()
                )
                version_match = rt_check.get('versionMatch')
                if local_ver and node_ver and local_ver != node_ver:
                    logger.warning(
                        '节点 RUNTIME 版本与控制面不一致 node_id=%s host=%s local=%s node=%s；'
                        '建议在「业务运行时分发」重新分发升级（本次仍继续启动）',
                        node_id, host, local_ver, node_ver,
                    )
                elif version_match is False:
                    logger.warning(
                        '节点 RUNTIME 版本与控制面标记不一致 node_id=%s host=%s check=%s',
                        node_id, host, rt_check.get('message'),
                    )
            except Exception as ver_e:
                logger.debug('RUNTIME 版本对照跳过: %s', ver_e)
        except Exception as e:
            logger.warning('检测节点 RUNTIME 失败 node_id=%s host=%s: %s', node_id, host, e)
            return (
                False,
                f'无法检测节点 {host} 的 RUNTIME 状态: {e}。'
                f'请确认节点在线、SSH 可用，并已分发 / 原子安装 RUNTIME',
                False,
            )
        remote_ini = os.path.join(log_dir, 'runtime.ini')
        try:
            ini_path, ini_content = generate_runtime_ini_content(
                task,
                log_dir,
                prefer_cluster_model=True,
                remote_ini_path=remote_ini,
            )
        except Exception as e:
            logger.error('生成远程 RUNTIME 配置失败: %s', e, exc_info=True)
            return (False, f'生成远程 RUNTIME 配置失败: {e}', False)
        command = [REMOTE_RUNTIME_BIN, ini_path]
        work_dir = '/opt/easyaiot/RUNTIME'
        env = _build_task_deploy_env(task_id, task.task_type, log_dir, host, task=task)
        env['VIDEO_ROOT'] = video_root_remote
        env['RUNTIME_BIN'] = REMOTE_RUNTIME_BIN
        env['LD_LIBRARY_PATH'] = REMOTE_RUNTIME_LD_LIBRARY_PATH
        env['USE_GPU'] = 'true' if getattr(task, 'prefer_gpu', True) else 'false'
        env['RUNTIME_PREFER_GPU'] = env['USE_GPU']
        if getattr(task, 'runtime_control_port', None):
            task.service_port = int(task.runtime_control_port)
        else:
            task.service_port = 8000 + (int(task_id) % 1000)
        files = [{'path': ini_path, 'content': ini_content, 'mode': '0644'}]
    else:
        service_dir = {
            'realtime': 'realtime_algorithm_service',
            'snap': 'snapshot_algorithm_service',
            'patrol': 'patrol_algorithm_service',
        }.get(task.task_type, 'realtime_algorithm_service')
        work_dir = os.path.join(video_root_remote, 'services', service_dir)
        bundle = {
            'snap': 'algorithm_snap',
            'patrol': 'algorithm_patrol',
        }.get(task.task_type, 'algorithm_realtime')
        python_exec = resolve_video_bundle_python(bundle, video_root_remote)
        deploy_script = os.path.join(work_dir, 'run_deploy.py')
        command = [python_exec, deploy_script]
        env = _build_task_deploy_env(task_id, task.task_type, log_dir, host, task=task)
        env['VIDEO_ROOT'] = video_root_remote

    result = node_client.deploy_workload(
        node_id=node_id,
        workload_type=WORKLOAD_TYPE_ALGORITHM,
        workload_id=str(task_id),
        command=command,
        work_dir=work_dir,
        log_dir=log_dir,
        env=env,
        gpu_ids=gpu_ids,
        files=files,
    )

    task.node_id = node_id
    task.service_server_ip = host
    task.service_process_id = result.get('pid')
    task.service_log_path = log_dir
    task.run_status = 'running'
    db.session.commit()

    logger.info(
        '算法任务远程部署成功 task_id=%s executor=%s node_id=%s host=%s pid=%s',
        task_id, executor, node_id, host, result.get('pid'),
    )
    return (True, f'已下发到节点 {host} ({executor})', False)


def _stop_remote_task(task_id: int, node_id: Optional[int]) -> None:
    if not node_id:
        return
    from app.utils import node_client
    try:
        node_client.stop_workload(node_id, WORKLOAD_TYPE_ALGORITHM, str(task_id))
    except Exception as e:
        logger.warning('远程停止算法任务失败 task_id=%s: %s', task_id, e)


def get_service_script_path(service_type: str) -> str:
    """获取服务脚本路径
    
    Args:
        service_type: 服务类型 ('realtime' 实时算法服务, 'snap' 抓拍算法服务)
    
    Returns:
        str: 服务脚本的绝对路径
    """
    # 当前文件: VIDEO/app/services/algorithm_task_launcher_service.py
    # 需要得到: VIDEO/ 目录
    # 使用3个os.path.dirname: services -> app -> VIDEO
    video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    service_paths = {
        'realtime': os.path.join(video_root, 'services', 'realtime_algorithm_service', 'run_deploy.py'),
        'snap': os.path.join(video_root, 'services', 'snapshot_algorithm_service', 'run_deploy.py'),
        'patrol': os.path.join(video_root, 'services', 'patrol_algorithm_service', 'run_deploy.py'),
    }
    
    return service_paths.get(service_type)


def _get_log_path(task_id: int) -> str:
    """获取日志文件路径（按任务ID）
    
    Args:
        task_id: 任务ID
    
    Returns:
        str: 日志目录路径
    """
    video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_base_dir = os.path.join(video_root, 'logs')
    log_dir = os.path.join(log_base_dir, f'task_{task_id}')
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def cleanup_orphaned_processes(task_id: int, extra_protected_pids: set = None):
    """清理遗留的进程（包括run_deploy.py和FFmpeg进程）
    
    Args:
        task_id: 算法任务ID
        extra_protected_pids: 额外需要保护的 PID（如刚启动、尚未写入 daemon._process 时）
    """
    # 仅清理实时算法服务 / RUNTIME，避免误杀 stream_forward 等同 TASK_ID 的 run_deploy
    realtime_deploy_marker = os.path.join('realtime_algorithm_service', 'run_deploy.py')
    runtime_ini_marker = f'task_{task_id}.ini'
    orphan_terminate_timeout = int(os.getenv('ALGORITHM_ORPHAN_TERMINATE_TIMEOUT', '12'))
    try:
        import psutil
        
        # 获取当前守护进程管理的进程PID（如果存在）
        protected_pids = set(extra_protected_pids or ())
        with _daemons_lock:
            if task_id in _running_daemons:
                daemon = _running_daemons[task_id]
                # 保护正在运行的守护进程管理的进程（即使_process为None，也可能正在启动中）
                if daemon._running:
                    if daemon._process:
                        try:
                            # 检查进程是否真的在运行
                            if daemon._process.poll() is None:
                                # 守护进程管理的进程还在运行，保护它及其子进程
                                protected_pids.add(daemon._process.pid)
                                try:
                                    # 获取所有子进程的PID
                                    parent_proc = psutil.Process(daemon._process.pid)
                                    for child in parent_proc.children(recursive=True):
                                        protected_pids.add(child.pid)
                                except (psutil.NoSuchProcess, psutil.AccessDenied):
                                    pass
                        except:
                            # poll失败，进程可能已经不存在，但不影响保护逻辑
                            pass
                    else:
                        # 进程为None但守护进程还在运行，说明可能正在启动中
                        # 为了安全起见，不清理任何进程（避免误杀正在启动的进程）
                        logger.debug(f"守护进程正在启动中（task_id={task_id}），跳过清理遗留进程")
                        return
        
        killed_count = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'environ']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if not cmdline:
                    continue
                
                cmdline_str = ' '.join(cmdline)
                is_python_deploy = realtime_deploy_marker in cmdline_str
                is_runtime_bin = (
                    runtime_ini_marker in cmdline_str
                    and (
                        'RUNTIME' in cmdline_str
                        or any(
                            str(arg).endswith('RUNTIME') or str(arg).endswith('RUNTIME.exe')
                            for arg in cmdline
                        )
                    )
                )
                if not is_python_deploy and not is_runtime_bin:
                    continue
                
                # 检查是否是目标任务进程
                is_target = False

                if is_runtime_bin:
                    try:
                        environ = proc.info.get('environ', {}) or {}
                        if environ.get('TASK_ID') and environ.get('TASK_ID') != str(task_id):
                            continue
                    except Exception:
                        pass
                    is_target = True
                
                # 检查脚本路径是否为实时算法服务
                script_path_match = any(
                    realtime_deploy_marker in str(arg) for arg in cmdline
                )
                if script_path_match and not is_target:
                    # 优先检查环境变量（最可靠）
                    try:
                        environ = proc.info.get('environ', {})
                        if environ:
                            proc_task_id = environ.get('TASK_ID')
                            if proc_task_id == str(task_id):
                                is_target = True
                            else:
                                # 环境变量不匹配，跳过
                                continue
                        else:
                            # 无法获取环境变量，尝试从命令行参数中提取（作为备选方案）
                            # 但只检查明确的环境变量格式，避免误判
                            found_task_id = None
                            for arg in cmdline:
                                arg_str = str(arg)
                                # 检查是否是环境变量格式：TASK_ID=xxx
                                if 'TASK_ID=' in arg_str:
                                    try:
                                        found_task_id = arg_str.split('TASK_ID=')[1].split()[0].strip()
                                        break
                                    except:
                                        pass
                            
                            if found_task_id == str(task_id):
                                is_target = True
                            else:
                                # 任务ID不匹配，跳过
                                continue
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # 如果无法获取环境变量，且无法从命令行提取，跳过（避免误杀）
                        logger.debug(f"无法获取进程 {proc.info['pid']} 的环境变量，跳过检查")
                        continue
                
                # 检查是否是FFmpeg进程（可能是run_deploy.py的子进程）
                # 重要：只清理算法任务相关的FFmpeg进程，不影响RTSP推流的FFmpeg进程
                is_ffmpeg = False
                if 'ffmpeg' in cmdline_str.lower():
                    try:
                        # 检查父进程是否是我们的run_deploy.py进程
                        parent = proc.parent()
                        if parent:
                            try:
                                parent_cmdline = parent.cmdline()
                                if not parent_cmdline:
                                    # 无法获取父进程命令行，跳过（避免误杀）
                                    continue
                                
                                # 检查父进程脚本路径
                                parent_script_match = False
                                for arg in parent_cmdline:
                                    if realtime_deploy_marker in str(arg):
                                        parent_script_match = True
                                        break
                                
                                # 只有父进程是run_deploy.py时才继续检查
                                if parent_script_match:
                                    try:
                                        parent_environ = parent.environ()
                                        # 必须同时满足：父进程是run_deploy.py 且 TASK_ID匹配
                                        if parent_environ and parent_environ.get('TASK_ID') == str(task_id):
                                            is_ffmpeg = True
                                        else:
                                            # 父进程是run_deploy.py但TASK_ID不匹配，跳过（避免误杀）
                                            continue
                                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                                        # 无法获取父进程环境变量，跳过（避免误杀）
                                        continue
                                else:
                                    # 父进程不是run_deploy.py，这是RTSP推流的FFmpeg进程，跳过
                                    continue
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                # 无法获取父进程信息，跳过（避免误杀）
                                continue
                        else:
                            # 没有父进程，跳过（避免误杀）
                            continue
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # 无法获取父进程，跳过（避免误杀）
                        continue
                
                if is_target or is_ffmpeg:
                    # 检查是否是受保护的进程（当前守护进程管理的进程）
                    proc_pid = proc.info['pid']
                    if proc_pid in protected_pids:
                        logger.debug(f"跳过受保护的进程: PID={proc_pid} (task_id={task_id})")
                        continue
                    
                    try:
                        logger.warning(f"🔍 发现遗留进程: PID={proc_pid}, CMD={' '.join(cmdline[:3])}...")
                        # 先尝试优雅终止
                        proc.terminate()
                        try:
                            proc.wait(timeout=orphan_terminate_timeout)
                            logger.info(f"✅ 遗留进程 {proc_pid} 已优雅终止")
                        except psutil.TimeoutExpired:
                            if proc.is_running():
                                proc.kill()
                                proc.wait(timeout=1)
                                logger.warning(f"⚠️ 遗留进程 {proc_pid} 已强制终止")
                        killed_count += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                        # 进程已经不存在或无权访问
                        pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # 进程已经不存在或无权访问，继续下一个
                continue
        
        if killed_count > 0:
            logger.info(f"🧹 清理了 {killed_count} 个遗留进程 (task_id={task_id})")
        else:
            logger.debug(f"未发现遗留进程 (task_id={task_id})")
            
    except ImportError:
        # psutil未安装，使用ps命令（Linux）
        try:
            protected_pids = set(extra_protected_pids or ())
            with _daemons_lock:
                if task_id in _running_daemons:
                    daemon = _running_daemons[task_id]
                    if daemon._running:
                        if daemon._process:
                            try:
                                if daemon._process.poll() is None:
                                    protected_pids.add(daemon._process.pid)
                            except Exception:
                                pass
                        else:
                            logger.debug(f"守护进程正在启动中（task_id={task_id}），跳过清理遗留进程")
                            return
            
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                pids_to_kill = []
                for line in lines:
                    if realtime_deploy_marker not in line or f'TASK_ID={task_id}' not in line:
                        continue
                    parts = line.split()
                    if len(parts) > 1:
                        try:
                            pid = int(parts[1])
                            if pid not in protected_pids:
                                pids_to_kill.append(pid)
                        except ValueError:
                            pass
                
                for pid in pids_to_kill:
                    try:
                        os.killpg(os.getpgid(pid), signal.SIGTERM)
                        time.sleep(orphan_terminate_timeout)
                        try:
                            os.killpg(os.getpgid(pid), signal.SIGKILL)
                        except (ProcessLookupError, OSError):
                            pass
                        logger.info(f"🧹 清理遗留进程: PID={pid} (task_id={task_id})")
                    except (ProcessLookupError, OSError):
                        pass
        except Exception as e:
            logger.warning(f"清理遗留进程失败: {str(e)}")
    except Exception as e:
        logger.warning(f"清理遗留进程时出错: {str(e)}")


def stop_service_process(task_id: int, service_type: str, stop_request_id: int = None):
    """停止服务进程
    
    Args:
        task_id: 算法任务ID
        service_type: 服务类型 ('realtime' 统一服务)
        stop_request_id: 异步停止请求代次；若已过期则跳过
    """
    if stop_request_id is not None and not _is_stop_request_current(task_id, stop_request_id):
        logger.info('跳过过期停止请求: task_id=%s', task_id)
        return

    # 等待启动完成（如果正在启动）
    with _starting_lock:
        if task_id in _starting_tasks:
            task_start_lock = _starting_tasks[task_id]
            # 尝试获取锁（如果正在启动，会等待）
            if task_start_lock.acquire(blocking=True, timeout=5):
                task_start_lock.release()
    
    task = None
    was_remote = False
    try:
        task = AlgorithmTask.query.get(task_id)
        was_remote = bool(task and task.node_id)
    except RuntimeError:
        # stop_algorithm_task 在后台线程执行 teardown 时无 Flask 上下文，仅做本机进程清理
        logger.debug('无 Flask 应用上下文，跳过远程任务数据库操作: task_id=%s', task_id)

    if was_remote and task:
        _stop_remote_task(task_id, task.node_id)
        task.node_id = None
        task.service_process_id = None
        task.run_status = 'stopped'
        db.session.commit()

    _stop_post_process_cluster(task_id, task)

    daemon_to_join = None
    with _daemons_lock:
        if task_id in _running_daemons:
            daemon = _running_daemons[task_id]
            try:
                daemon.stop()
                logger.info(f"✅ 停止{service_type}服务成功: task_id={task_id}")
            except Exception as e:
                logger.error(f"❌ 停止{service_type}服务失败: task_id={task_id}, error={str(e)}")
            finally:
                del _running_daemons[task_id]
                daemon_to_join = daemon
    if daemon_to_join and not daemon_to_join.join_daemon_thread(timeout=15):
        logger.warning('任务 %s 守护线程未在 15s 内结束', task_id)

    if not was_remote:
        cleanup_orphaned_processes(task_id)
    
    # 清理启动锁
    with _starting_lock:
        if task_id in _starting_tasks:
            del _starting_tasks[task_id]


def stop_all_task_services(task_id: int, stop_request_id: int = None):
    """停止任务的所有服务
    
    Args:
        task_id: 算法任务ID
        stop_request_id: 异步停止请求代次；若已过期则跳过
    """
    stop_service_process(task_id, 'realtime', stop_request_id=stop_request_id)


def restart_task_services(task_id: int) -> bool:
    """重启任务的所有服务（使用守护进程的 restart 方法）
    
    Args:
        task_id: 算法任务ID
    
    Returns:
        bool: 是否成功重启服务
    """
    _cancel_pending_stop_requests(task_id)
    task = AlgorithmTask.query.get(task_id)
    if task and _use_remote_deploy(task):
        _stop_remote_task(task_id, task.node_id)
        _stop_post_process_cluster(task_id, task)
        success, _, _ = _deploy_task_on_remote_node(task_id, task)
        if success:
            task = AlgorithmTask.query.get(task_id)
            if task:
                _start_post_process_cluster(task)
        return success

    with _daemons_lock:
        if task_id in _running_daemons:
            daemon = _running_daemons[task_id]
            try:
                daemon.restart()
                logger.info(f"✅ 重启任务 {task_id} 的服务成功")
                return True
            except Exception as e:
                logger.error(f"❌ 重启任务 {task_id} 的服务失败: {str(e)}")
                return False
        else:
            logger.warning(f"任务 {task_id} 的服务未运行，无法重启")
            return False


def start_task_services(task_id: int, task: AlgorithmTask) -> Tuple[bool, str, bool]:
    """启动算法任务的所有服务（使用守护进程管理）
    
    Args:
        task_id: 算法任务ID
        task: AlgorithmTask对象
    
    Returns:
        tuple[bool, str, bool]: (是否成功, 消息, 是否已运行)
            - 是否成功: True表示成功或已运行，False表示失败
            - 消息: 描述性消息
            - 是否已运行: True表示服务已在运行，False表示新启动
    """
    # 获取或创建任务专用的启动锁（防止并发启动）
    with _starting_lock:
        if task_id not in _starting_tasks:
            _starting_tasks[task_id] = threading.Lock()
        task_start_lock = _starting_tasks[task_id]
    
    # 使用任务专用的启动锁，防止并发启动
    if not task_start_lock.acquire(blocking=False):
        logger.warning(f"任务 {task_id} 正在启动中，跳过重复启动")
        return (True, "任务正在启动中", True)
    
    # 作废尚未执行的异步 stop，避免 stop→start 竞态在数毫秒后误杀新守护进程
    _cancel_pending_stop_requests(task_id)
    
    try:
        # 实时/抓拍/巡检算法任务都需要启动服务进程
        if task.task_type in ['realtime', 'snap', 'patrol']:
            if _use_remote_deploy(task):
                failover_sec = _algorithm_heartbeat_failover_seconds()
                if task.node_id and not _heartbeat_stale(task.service_last_heartbeat, failover_sec):
                    if _is_compute_node_online(int(task.node_id)):
                        logger.info('任务 %s 已在远程节点 %s 运行，跳过重复部署', task_id, task.node_id)
                        ok_pp, _ = _start_post_process_cluster(task)
                        return (True, '任务已在远程节点运行', True) if ok_pp else (False, '后处理集群启动失败', False)
                if task.node_id:
                    logger.info(
                        '任务 %s 远程 node_id=%s 但分片未运行或心跳超时，重新部署',
                        task_id, task.node_id,
                    )
                    _stop_remote_task(task_id, task.node_id)
                    task.node_id = None
                    task.service_process_id = None
                    db.session.commit()
                result = _deploy_task_on_remote_node(task_id, task)
                if result[0]:
                    _start_post_process_cluster(task)
                return result

            ok, sync_msg = _ensure_task_models_on_cluster(task)
            if not ok:
                return (False, f'集群模型预同步失败: {sync_msg}', False)

            # 检查是否已经有运行的守护进程（在清理之前检查，避免误杀正在运行的进程）
            should_cleanup = True
            with _daemons_lock:
                if task_id in _running_daemons:
                    daemon = _running_daemons[task_id]
                    if daemon._running and daemon._process and daemon._process.poll() is None:
                        # 守护进程正在运行，不清理遗留进程（避免误杀）
                        should_cleanup = False
                        logger.debug(f'守护进程正在运行，跳过清理遗留进程 (task_id={task_id})')
            
            # 检查是否已经有运行的守护进程（在清理之前检查，避免误杀正在运行的进程）
            existing_daemon = None
            with _daemons_lock:
                if task_id in _running_daemons:
                    existing_daemon = _running_daemons[task_id]
                    # 守护线程已启动但子进程尚未 Popen（如 conda 查找期间），勿误判为失败并 stop
                    if existing_daemon._running and existing_daemon._process is None:
                        logger.warning(f"任务 {task_id} 的守护进程正在启动中，跳过重复启动")
                        return (True, "任务正在启动中", True)
                    if existing_daemon._running and existing_daemon._process and existing_daemon._process.poll() is None:
                        logger.warning(f"任务 {task_id} 的服务已在运行，跳过启动")
                        return (True, "任务运行中", True)
            
            # 只有在没有运行的守护进程时才清理遗留进程
            if should_cleanup:
                logger.debug(f'清理任务 {task_id} 的遗留进程...')
                cleanup_orphaned_processes(task_id)
                logger.debug(f'清理任务 {task_id} 的遗留进程完成')
            
            # 如果存在旧的守护进程但进程已停止，清理它
            if existing_daemon:
                with _daemons_lock:
                    if task_id in _running_daemons:
                        daemon = _running_daemons[task_id]
                        if not daemon._running or (daemon._process and daemon._process.poll() is not None):
                            logger.info('守护进程已停止或进程不存在，清理旧守护进程...')
                            try:
                                daemon.stop()
                            except:
                                pass
                            del _running_daemons[task_id]
                        elif daemon._process is None and not daemon._running:
                            # 守护进程已退出且从未拉起子进程，清理后重建
                            logger.info('守护进程已停止且未拉起子进程，清理并重新启动...')
                            try:
                                daemon.stop()
                            except:
                                pass
                            del _running_daemons[task_id]
            
            # 获取日志路径（与 AI 模块保持一致）
            log_path = _get_log_path(task_id)
            
            # 启动守护进程（传入所有必要参数，不需要数据库连接）
            logger.info(f'启动守护进程，任务ID: {task_id}, 任务类型: {task.task_type}')
            extra_env = {}
            _inject_sam_supplement_env(extra_env, task)
            _inject_realtime_sampling_env(extra_env, task)

            executor = (getattr(task, 'executor', None) or 'cpp').strip().lower()
            runtime_bin = None
            runtime_ini = None
            if executor in ('cpp', 'c++', 'runtime', 'cxx'):
                executor = 'cpp'
                if task.task_type not in ('realtime', 'snap', 'patrol'):
                    return (False, f'executor=cpp 不支持任务类型: {task.task_type}', False)
                try:
                    from .runtime_config_service import (
                        generate_runtime_ini,
                        ensure_runtime_bin_ready,
                        runtime_library_path_env,
                    )
                    runtime_bin = ensure_runtime_bin_ready(task)
                    runtime_ini = generate_runtime_ini(task, log_path)
                    lib_path = runtime_library_path_env()
                    if lib_path:
                        extra_env['LD_LIBRARY_PATH'] = lib_path
                    if getattr(task, 'runtime_control_port', None):
                        task.service_port = int(task.runtime_control_port)
                    else:
                        task.service_port = 8000 + (int(task_id) % 1000)
                    task.service_log_path = log_path
                    db.session.commit()
                except Exception as e:
                    logger.error('生成 RUNTIME 配置失败: %s', e, exc_info=True)
                    return (False, f'生成 RUNTIME 配置失败: {e}', False)

            daemon = None
            old_daemon_to_join = None
            with _daemons_lock:
                if task_id in _running_daemons:
                    old_daemon = _running_daemons[task_id]
                    if (
                        old_daemon._running
                        and old_daemon._process
                        and old_daemon._process.poll() is None
                    ):
                        logger.warning(f"任务 {task_id} 的守护进程已在运行，跳过重复创建")
                        return (True, "任务运行中", True)
                    if old_daemon._running:
                        try:
                            old_daemon.stop()
                            old_daemon_to_join = old_daemon
                        except Exception:
                            pass
                    del _running_daemons[task_id]
                daemon = AlgorithmTaskDaemon(
                    task_id=task_id,
                    log_path=log_path,
                    task_type=task.task_type,
                    extra_env=extra_env,
                    executor=executor,
                    runtime_bin=runtime_bin,
                    runtime_ini=runtime_ini,
                )
                _running_daemons[task_id] = daemon

            if old_daemon_to_join and not old_daemon_to_join.join_daemon_thread(timeout=15):
                logger.warning(
                    '任务 %s 的旧守护线程未在 15s 内结束，可能存在短暂并发',
                    task_id,
                )
            
            # 等待守护进程启动并获取进程PID（最多等待2秒）
            import time
            process_pid = None
            for _ in range(20):  # 等待最多2秒（20 * 0.1秒）
                time.sleep(0.1)
                if daemon._process is not None:
                    try:
                        if daemon._process.poll() is None:
                            process_pid = daemon._process.pid
                            break
                    except:
                        pass
                if not daemon._running:
                    # 守护进程已停止，退出等待
                    break
            
            task_type_name = {
                'realtime': '实时算法',
                'snap': '抓拍算法',
                'patrol': '巡检算法',
            }.get(task.task_type, task.task_type)
            logger.info(f"✅ 任务 {task_id} 的{task_type_name}服务启动成功（守护进程已启动）")
            _start_post_process_cluster(task)
            return (True, "启动成功", False)
        else:
            # 未知的任务类型
            logger.warning(f"未知的任务类型: {task.task_type}，跳过启动")
            return (False, f"未知的任务类型: {task.task_type}", False)
            
    except Exception as e:
        logger.error(f"❌ 启动任务 {task_id} 的服务失败: {str(e)}", exc_info=True)
        return (False, f"启动失败: {str(e)}", False)
    finally:
        # 释放启动锁
        task_start_lock.release()
        # 如果任务已停止，清理启动锁
        with _starting_lock:
            if task_id in _starting_tasks:
                # 检查任务是否还在运行
                with _daemons_lock:
                    if task_id not in _running_daemons:
                        # 任务已停止，清理启动锁
                        del _starting_tasks[task_id]


def auto_start_all_tasks(app=None):
    """自动启动所有启用的算法任务的服务
    
    Args:
        app: Flask应用实例（用于应用上下文）
    """
    try:
        if app:
            with app.app_context():
                _auto_start_all_tasks_internal()
        else:
            _auto_start_all_tasks_internal()
    except Exception as e:
        logger.error(f"❌ 自动启动算法任务服务失败: {str(e)}", exc_info=True)


def _auto_start_all_tasks_internal():
    """内部函数：自动启动所有启用的算法任务的服务"""
    try:
        # 查询所有启用的算法任务
        tasks = AlgorithmTask.query.filter_by(is_enabled=True).all()
        
        if not tasks:
            disabled = AlgorithmTask.query.filter_by(is_enabled=False).count()
            if disabled:
                logger.info(
                    '没有启用的算法任务，跳过服务启动（另有 %s 个已停用任务，需手动启动或 API 启用）',
                    disabled,
                )
            else:
                logger.info("没有启用的算法任务，跳过服务启动")
            return
        
        logger.info(f"发现 {len(tasks)} 个启用的算法任务，开始启动服务...")
        
        success_count = 0
        for task in tasks:
            try:
                # 检查任务是否有必需的配置
                if task.task_type == 'realtime':
                    # 实时算法任务需要模型ID列表
                    if not task.model_ids:
                        logger.warning(f"任务 {task.id} ({task.task_name}) 缺少模型ID配置，跳过")
                        continue
                elif task.task_type in ('snap', 'patrol'):
                    if not task.model_ids:
                        logger.warning(f"任务 {task.id} ({task.task_name}) 缺少模型ID配置，跳过")
                        continue
                    if not task.devices or len(task.devices) == 0:
                        logger.warning(f"任务 {task.id} ({task.task_name}) 没有关联的设备，跳过")
                        continue
                    if task.task_type == 'snap':
                        for device in task.devices:
                            try:
                                snap_space = get_snap_space_by_device_id(device.id)
                                if not snap_space:
                                    logger.info(f"为设备 {device.id} ({device.name or device.id}) 自动创建抓拍空间")
                                    create_snap_space_for_device(device.id, device.name)
                                else:
                                    logger.debug(f"设备 {device.id} 已有抓拍空间: {snap_space.space_name}")
                            except Exception as e:
                                logger.error(f"为设备 {device.id} 创建/获取抓拍空间失败: {str(e)}", exc_info=True)
                else:
                    logger.warning(f"任务 {task.id} ({task.task_name}) 未知的任务类型: {task.task_type}，跳过")
                    continue
                
                # 启动任务的服务
                success, msg, _ = start_task_services(task.id, task)
                if success:
                    success_count += 1
                    logger.info(f"✅ 任务 {task.id} ({task.task_name}) 的服务启动成功: {msg}")
                else:
                    logger.error(f"❌ 任务 {task.id} ({task.task_name}) 的服务启动失败: {msg}")
                    
            except Exception as e:
                logger.error(f"❌ 启动任务 {task.id} 的服务时出错: {str(e)}", exc_info=True)
        
        logger.info(f"✅ 自动启动完成: {success_count}/{len(tasks)} 个任务的服务启动成功")
        
    except Exception as e:
        logger.error(f"❌ 自动启动算法任务服务失败: {str(e)}", exc_info=True)


def recover_unhealthy_algorithm_tasks() -> int:
    """恢复已启用但进程已退出的算法任务，返回成功恢复数。"""
    tasks = AlgorithmTask.query.filter_by(is_enabled=True).all()
    recovered = 0
    for task in tasks:
        if _algorithm_task_service_healthy(task):
            continue
        try:
            logger.info(
                '算法任务 %s (%s) 服务未运行或心跳超时，尝试恢复',
                task.id, task.task_name,
            )
            success, msg, _ = start_task_services(task.id, task)
            if success:
                recovered += 1
                logger.info('算法任务 %s 恢复成功: %s', task.id, msg)
            else:
                logger.error('算法任务 %s 恢复失败: %s', task.id, msg)
        except Exception as e:
            logger.error('算法任务 %s 恢复异常: %s', task.id, e, exc_info=True)
    if recovered:
        logger.info('算法任务健康恢复完成: recovered=%s', recovered)
    return recovered


def cleanup_stopped_processes():
    """清理已停止的守护进程（守护进程会自动管理，此函数主要用于检查）"""
    with _daemons_lock:
        tasks_to_remove = []
        for task_id, daemon in _running_daemons.items():
            # 检查守护进程是否还在运行
            # 如果_process为None，说明守护进程可能正在启动中，不清理
            if not daemon._running:
                # 守护进程已停止
                logger.info(f"检测到守护进程已停止: task_id={task_id}")
                tasks_to_remove.append(task_id)
            elif daemon._process and daemon._process.poll() is not None:
                # 进程已退出
                logger.info(f"检测到守护进程的子进程已退出: task_id={task_id}")
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            try:
                _running_daemons[task_id].stop()
            except:
                pass
            del _running_daemons[task_id]


def stop_all_daemons():
    """停止所有守护进程（用于VIDEO服务关闭时清理）"""
    with _daemons_lock:
        if not _running_daemons:
            logger.info("没有运行的守护进程，无需停止")
            return
        
        logger.info(f"正在停止 {len(_running_daemons)} 个守护进程...")
        task_ids = list(_running_daemons.keys())
        
        for task_id in task_ids:
            try:
                daemon = _running_daemons[task_id]
                daemon.stop()
                logger.info(f"✅ 停止守护进程成功: task_id={task_id}")
            except Exception as e:
                logger.error(f"❌ 停止守护进程失败: task_id={task_id}, error={str(e)}")
            finally:
                if task_id in _running_daemons:
                    del _running_daemons[task_id]
        
        logger.info(f"✅ 所有守护进程已停止")

