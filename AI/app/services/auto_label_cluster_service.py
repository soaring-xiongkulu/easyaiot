"""
自动标注集群队列调度：多摄像头子任务排队、节点负载均衡、远程 Worker 下发。
"""
import json
import logging
import os
import socket
import threading
import time
from typing import Any

from db_models import db, AutoLabelTask, AutoLabelSubTask, beijing_now
from app.utils.node_remote_python import is_platform_node, resolve_ai_bundle_python

logger = logging.getLogger(__name__)

WORKLOAD_TYPE_AUTO_LABEL = 'auto_label'
_COORDINATOR_THREAD: threading.Thread | None = None
_COORDINATOR_STOP = threading.Event()
_COORDINATOR_INTERVAL = int(os.getenv('AUTO_LABEL_QUEUE_POLL_SEC', '5'))


def _control_plane_base_url() -> str:
    host = os.getenv('AI_CONTROL_HOST') or os.getenv('POD_IP') or os.getenv('HOST_IP')
    port = os.getenv('FLASK_RUN_PORT', '5000')
    if not host:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            host = s.getsockname()[0]
            s.close()
        except Exception:
            host = '127.0.0.1'
    return os.getenv('AI_CONTROL_URL', f'http://{host}:{port}').rstrip('/')


def _platform_worker_command(env: dict[str, str], gpu_ids: str | None = None) -> tuple[list[str], dict[str, str]]:
    """控制面节点由 Agent 管理进程，但 Worker 在现有 AI 容器内运行。"""
    container_name = os.getenv('PLATFORM_AI_CONTAINER_NAME', 'ai-service').strip() or 'ai-service'
    container_root = os.getenv('PLATFORM_AI_CONTAINER_ROOT', '/app').rstrip('/') or '/app'
    container_python = os.getenv('PLATFORM_AI_CONTAINER_PYTHON', '/opt/conda/bin/python').strip()
    worker_dir = os.path.join(container_root, 'services', 'auto_label_worker')
    worker_script = os.path.join(worker_dir, 'run_worker.py')

    deploy_env = {key: str(value) for key, value in env.items() if value is not None}
    deploy_env['AI_ROOT'] = container_root
    if gpu_ids:
        deploy_env['CUDA_VISIBLE_DEVICES'] = str(gpu_ids)
        deploy_env['GPU_IDS'] = str(gpu_ids)

    command = ['docker', 'exec', '-w', worker_dir]
    for key in sorted(deploy_env):
        command.extend(['-e', key])
    command.extend([container_name, container_python, worker_script])
    return command, deploy_env


def create_camera_subtasks(
    parent_task: AutoLabelTask,
    frame_tasks: list[dict],
    pipeline_config: dict,
) -> list[AutoLabelSubTask]:
    """为每个摄像头创建排队子任务。"""
    subtasks: list[AutoLabelSubTask] = []
    base_priority = parent_task.queue_priority or 0
    for idx, ft in enumerate(frame_tasks):
        ft_id = ft.get('id')
        stream_url = (ft.get('rtmpUrl') or '').strip()
        if not stream_url:
            raise ValueError(f'帧捕获任务 {ft.get("taskName") or ft_id} 无可用视频流地址')
        sub_cfg = {
            'duration_hours': pipeline_config.get('duration_hours', 8),
            'capture_interval_sec': pipeline_config.get('capture_interval_sec', 30),
            'auto_export': pipeline_config.get('auto_export', False),
            'keep_annotated_images_only': pipeline_config.get('keep_annotated_images_only', True),
            'strategy': pipeline_config.get('strategy'),
        }
        st = AutoLabelSubTask(
            parent_task_id=parent_task.id,
            dataset_id=parent_task.dataset_id,
            frame_task_id=ft_id,
            frame_task_name=ft.get('taskName') or f'camera-{ft_id}',
            rtmp_url=stream_url,
            subtask_type='capture_label',
            status='QUEUED',
            queue_position=base_priority * 1000 + idx,
            config_json=json.dumps(sub_cfg, ensure_ascii=False),
        )
        db.session.add(st)
        subtasks.append(st)
    db.session.flush()
    return subtasks


def dispatch_subtask_to_node(subtask: AutoLabelSubTask, exclude_node_ids: list[int] | None = None) -> bool:
    """将子任务调度到集群节点并下发 Worker。"""
    from app.utils import node_client

    if not node_client.is_remote_deploy_enabled():
        logger.warning('远程部署未启用，子任务 %s 无法调度到集群', subtask.id)
        return False

    parent = AutoLabelTask.query.get(subtask.parent_task_id)
    if not parent:
        return False

    workload_id = f'auto-label-subtask-{subtask.id}'
    subtask.workload_id = workload_id
    subtask.status = 'DISPATCHING'
    db.session.commit()

    try:
        allocation = node_client.allocate_node(
            WORKLOAD_TYPE_AUTO_LABEL,
            workload_id,
            capabilities=['ai_inference'],
            gpu_count=1,
            prefer_gpu=True,
            sticky=True,
            exclude_node_ids=exclude_node_ids or None,
        )
        node = node_client.get_node(allocation['nodeId'])
    except Exception as e:
        subtask.status = 'QUEUED'
        subtask.error_message = f'节点调度失败: {e}'
        db.session.commit()
        logger.warning('子任务 %s 调度失败: %s', subtask.id, e)
        return False

    node_id = allocation['nodeId']
    host = allocation.get('host') or ''
    gpu_ids = allocation.get('gpuIds')

    subtask.assigned_node_id = node_id
    subtask.assigned_node_host = host

    cfg = {}
    if subtask.config_json:
        try:
            cfg = json.loads(subtask.config_json)
        except Exception:
            cfg = {}

    text_prompts = []
    if parent.text_prompts:
        try:
            text_prompts = json.loads(parent.text_prompts)
        except Exception:
            text_prompts = []

    ai_root_remote = os.getenv('NODE_REMOTE_AI_ROOT', '/opt/easyaiot/AI')
    env = {
        'SUBTASK_ID': str(subtask.id),
        'PARENT_TASK_ID': str(parent.id),
        'DATASET_ID': str(parent.dataset_id),
        'FRAME_TASK_ID': str(subtask.frame_task_id or ''),
        'RTMP_URL': subtask.rtmp_url or '',
        'DURATION_HOURS': str(cfg.get('duration_hours', 8)),
        'CAPTURE_INTERVAL_SEC': str(cfg.get('capture_interval_sec', 30)),
        'INITIAL_CAPTURED_COUNT': str(subtask.captured_count or 0),
        'INITIAL_LABELED_COUNT': str(subtask.labeled_count or 0),
        'INITIAL_FAILED_COUNT': str(subtask.failed_count or 0),
        'KEEP_ANNOTATED_IMAGES_ONLY': (
            'true' if cfg.get('keep_annotated_images_only', True) else 'false'
        ),
        'TEXT_PROMPTS': json.dumps(text_prompts, ensure_ascii=False),
        'STRATEGY_JSON': json.dumps(cfg.get('strategy') or {}, ensure_ascii=False),
        'ANNOTATION_TYPE': parent.annotation_type or 'rectangle',
        'CONFIDENCE_THRESHOLD': str(parent.confidence_threshold or 0.45),
        'RETURN_MASKS': 'true' if parent.return_masks else 'false',
        'JAVA_BACKEND_URL': os.getenv('JAVA_BACKEND_URL', 'http://localhost:48080'),
        'AI_CONTROL_URL': _control_plane_base_url(),
        'SAM_ENABLED': os.getenv('SAM_ENABLED', 'true'),
        'AI_ROOT': ai_root_remote,
        'JWT_TOKEN': os.getenv('JWT_TOKEN', ''),
    }

    log_dir = os.path.join(ai_root_remote, 'logs', 'auto_label', str(subtask.id))
    if is_platform_node(node):
        command, env = _platform_worker_command(env, gpu_ids=gpu_ids)
        work_dir = os.getenv('PLATFORM_AGENT_WORK_DIR', '/tmp')
        logger.info('子任务 %s 命中控制面节点，将在 AI 容器内运行', subtask.id)
    else:
        work_dir = os.path.join(ai_root_remote, 'services', 'auto_label_worker')
        python_exec = resolve_ai_bundle_python(ai_root_remote)
        worker_script = os.path.join(ai_root_remote, 'services', 'auto_label_worker', 'run_worker.py')
        command = [python_exec, worker_script]

    try:
        result = node_client.deploy_workload(
            node_id=node_id,
            workload_type=WORKLOAD_TYPE_AUTO_LABEL,
            workload_id=workload_id,
            command=command,
            work_dir=work_dir,
            log_dir=log_dir,
            env=env,
            gpu_ids=gpu_ids,
        )
        subtask.status = 'RUNNING'
        subtask.started_at = beijing_now()
        subtask.error_message = None
        db.session.commit()
        logger.info(
            '子任务 %s 已下发 node=%s host=%s pid=%s',
            subtask.id, node_id, host, result.get('pid'),
        )
        return True
    except Exception as e:
        subtask.status = 'QUEUED'
        subtask.assigned_node_id = None
        subtask.assigned_node_host = None
        subtask.error_message = f'Worker 下发失败: {e}'
        node_client.release_binding(WORKLOAD_TYPE_AUTO_LABEL, workload_id)
        db.session.commit()
        logger.error('子任务 %s Worker 下发失败: %s', subtask.id, e)
        return False


def process_queue_once(app) -> int:
    """处理一轮队列：将 QUEUED 子任务分发到不同节点。"""
    dispatched = 0
    with app.app_context():
        subtasks = (
            AutoLabelSubTask.query.filter_by(status='QUEUED')
            .order_by(AutoLabelSubTask.queue_position.asc(), AutoLabelSubTask.id.asc())
            .limit(int(os.getenv('AUTO_LABEL_QUEUE_BATCH', '8')))
            .all()
        )
        if not subtasks:
            return 0

        assigned_nodes: list[int] = []
        for st in subtasks:
            parent = AutoLabelTask.query.get(st.parent_task_id)
            if not parent or parent.status in ('COMPLETED', 'FAILED', 'CANCELLED', 'PAUSED'):
                if parent and parent.status == 'PAUSED':
                    continue
                st.status = 'FAILED'
                st.error_message = '父任务已结束'
                continue
            ok = dispatch_subtask_to_node(st, exclude_node_ids=assigned_nodes)
            if ok and st.assigned_node_id:
                if parent.status == 'PENDING':
                    parent.status = 'PROCESSING'
                    parent.started_at = parent.started_at or beijing_now()
                dispatched += 1
                assigned_nodes.append(int(st.assigned_node_id))

        db.session.commit()
        _aggregate_parent_tasks(app)
    return dispatched


def update_subtask_progress(subtask_id: int, payload: dict[str, Any], app=None) -> AutoLabelSubTask | None:
    """Worker 心跳回调，更新子任务进度。"""
    st = AutoLabelSubTask.query.get(subtask_id)
    if not st:
        return None

    for key in ('captured_count', 'labeled_count', 'failed_count', 'processed_images'):
        if key in payload:
            current = int(getattr(st, key, 0) or 0)
            setattr(st, key, max(current, int(payload[key])))

    status = payload.get('status')
    if status in ('RUNNING', 'COMPLETED', 'FAILED'):
        st.status = status
    if status == 'COMPLETED':
        st.completed_at = beijing_now()
    if status == 'FAILED':
        st.error_message = payload.get('error_message') or st.error_message
        st.completed_at = beijing_now()
        _release_subtask_binding(st)

    if payload.get('log'):
        _append_parent_log(st.parent_task_id, f'[摄像头 {st.frame_task_name}] {payload["log"]}')

    db.session.commit()
    _aggregate_parent_tasks(app)
    return st


def _release_subtask_binding(subtask: AutoLabelSubTask) -> None:
    if not subtask.workload_id:
        return
    try:
        from app.utils import node_client
        node_client.release_binding(WORKLOAD_TYPE_AUTO_LABEL, subtask.workload_id)
    except Exception as e:
        logger.warning('释放子任务绑定失败 subtask=%s: %s', subtask.id, e)


def _append_parent_log(task_id: int, message: str) -> None:
    task = AutoLabelTask.query.get(task_id)
    if not task or not task.pipeline_config:
        return
    try:
        cfg = json.loads(task.pipeline_config)
    except Exception:
        cfg = {}
    logs = cfg.get('logs') if isinstance(cfg.get('logs'), list) else []
    logs.append({'time': beijing_now().isoformat(timespec='seconds'), 'message': message})
    cfg['logs'] = logs[-80:]
    task.pipeline_config = json.dumps(cfg, ensure_ascii=False)


def _aggregate_parent_tasks(app=None) -> None:
    """汇总子任务进度到父任务。"""
    parents = (
        AutoLabelTask.query.filter(
            AutoLabelTask.execution_mode == 'cluster',
            AutoLabelTask.status.in_(['PENDING', 'PROCESSING']),
        ).all()
    )
    for parent in parents:
        subtasks = list(parent.subtasks.all())
        if not subtasks:
            continue

        total_captured = sum(s.captured_count or 0 for s in subtasks)
        total_labeled = sum(s.labeled_count or 0 for s in subtasks)
        total_failed = sum(s.failed_count or 0 for s in subtasks)

        try:
            cfg = json.loads(parent.pipeline_config) if parent.pipeline_config else {}
        except Exception:
            cfg = {}
        prev_labeled = int(cfg.get('total_labeled') or parent.success_count or 0)
        cfg['captured_count'] = total_captured
        cfg['labeled_count'] = total_labeled
        cfg['total_labeled'] = total_labeled
        cfg['pipeline_status'] = _derive_pipeline_status(subtasks)
        cfg['active_workers'] = sum(1 for s in subtasks if s.status in ('DISPATCHING', 'RUNNING'))
        cfg['queued_subtasks'] = sum(1 for s in subtasks if s.status == 'QUEUED')
        parent.pipeline_config = json.dumps(cfg, ensure_ascii=False)
        parent.success_count = total_labeled
        parent.failed_count = total_failed
        parent.processed_images = total_captured + total_labeled
        parent.total_images = max(total_captured, total_labeled)

        if app and parent.status == 'PROCESSING' and total_labeled > prev_labeled:
            try:
                from app.services.auto_label_orchestrator import on_label_batch_complete
                on_label_batch_complete(parent, app)
            except Exception as e:
                logger.warning('集群父任务阶段检查失败 task=%s: %s', parent.id, e)

        terminal = {'COMPLETED', 'FAILED'}
        if all(s.status in terminal for s in subtasks):
            if any(s.status == 'FAILED' for s in subtasks):
                parent.status = 'FAILED'
                failed_names = [s.frame_task_name for s in subtasks if s.status == 'FAILED']
                parent.error_message = f'部分摄像头子任务失败: {", ".join(failed_names[:5])}'
            else:
                parent.status = 'COMPLETED'
                if cfg.get('auto_export'):
                    _trigger_parent_export(parent)
            parent.completed_at = beijing_now()
            cfg['pipeline_status'] = 'done' if parent.status == 'COMPLETED' else 'failed'
            parent.pipeline_config = json.dumps(cfg, ensure_ascii=False)

    db.session.commit()


def _derive_pipeline_status(subtasks: list[AutoLabelSubTask]) -> str:
    if any(s.status == 'RUNNING' for s in subtasks):
        return 'labeling'
    if any(s.status in ('QUEUED', 'DISPATCHING') for s in subtasks):
        return 'collecting'
    if all(s.status == 'COMPLETED' for s in subtasks):
        return 'done'
    return 'collecting'


def _trigger_parent_export(parent: AutoLabelTask) -> None:
    """父任务全部完成后触发自动打包（控制面执行）。"""
    import requests

    try:
        cfg = json.loads(parent.pipeline_config) if parent.pipeline_config else {}
        text_prompts = []
        if parent.text_prompts:
            try:
                text_prompts = json.loads(parent.text_prompts)
            except Exception:
                text_prompts = []
        if not text_prompts:
            return
        java_base = os.getenv(
            'JAVA_BACKEND_URL',
            os.getenv('GATEWAY_URL', 'http://localhost:48080'),
        ).rstrip('/')
        export_url = f'{java_base}/admin-api/dataset/{parent.dataset_id}/annotation/export'
        body = {
            'trainRatio': float(cfg.get('export_train_ratio', 0.7)),
            'valRatio': float(cfg.get('export_val_ratio', 0.2)),
            'testRatio': float(cfg.get('export_test_ratio', 0.1)),
            'sampleSelection': 'all',
            'selectedClasses': text_prompts,
            'exportPrefix': f'sam_cluster_{parent.dataset_id}',
        }
        resp = requests.post(export_url, json=body, timeout=1800)
        if resp.ok:
            cfg['packaged'] = True
            _append_parent_log(parent.id, '集群流水线已完成自动打包导出')
        else:
            _append_parent_log(parent.id, f'自动打包失败: HTTP {resp.status_code}')
        parent.pipeline_config = json.dumps(cfg, ensure_ascii=False)
    except Exception as e:
        _append_parent_log(parent.id, f'自动打包异常: {e}')


def start_cluster_pipeline(app, task_id: int) -> None:
    """启动集群模式流水线：仅创建子任务并入队，由协调器分发。"""
    with app.app_context():
        task = AutoLabelTask.query.get(task_id)
        if not task:
            return
        task.status = 'PENDING'
        try:
            cfg = json.loads(task.pipeline_config) if task.pipeline_config else {}
        except Exception:
            cfg = {}
        cfg['pipeline_status'] = 'queued'
        cfg['mode'] = 'cluster_pipeline'
        task.pipeline_config = json.dumps(cfg, ensure_ascii=False)
        db.session.commit()
        process_queue_once(app)


def _coordinator_loop(app) -> None:
    while not _COORDINATOR_STOP.is_set():
        try:
            n = process_queue_once(app)
            if n:
                logger.debug('队列调度本轮下发 %s 个子任务', n)
        except Exception as e:
            logger.error('自动标注队列调度异常: %s', e, exc_info=True)
        _COORDINATOR_STOP.wait(_COORDINATOR_INTERVAL)


def start_auto_label_queue_coordinator(app) -> None:
    global _COORDINATOR_THREAD
    if _COORDINATOR_THREAD and _COORDINATOR_THREAD.is_alive():
        return
    _COORDINATOR_STOP.clear()
    _COORDINATOR_THREAD = threading.Thread(target=_coordinator_loop, args=(app,), daemon=True)
    _COORDINATOR_THREAD.start()
