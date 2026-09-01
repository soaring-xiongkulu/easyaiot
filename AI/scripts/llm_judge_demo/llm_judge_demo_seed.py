#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大模型（LLM）后处理 demo 造数脚本
==================================
为「算法任务 × 智能体研判」新功能造演示数据：
  1. 智能体：LLM-DEMO-视频研判专家 / LLM-DEMO-图片研判专家（AI 模块 rag_expert，走 REST）
  2. 算法任务：LLM-DEMO-实时研判 / LLM-DEMO-抓拍研判（直插 VIDEO 库，含 llm_post_process_enabled）
  3. 研判规则：实时任务 3 条（视频门控/图片回写/兜底）+ 抓拍任务 1 条（图片门控）
  4. 告警：6 条，覆盖 confirmed / rejected / error / pending / 无研判 五种展示形态

幂等：按名称/关联ID查重，重复执行不产生重复数据。
用法:
  python3 llm_judge_demo_seed.py            # 幂等造数（缺啥补啥）
  python3 llm_judge_demo_seed.py --reset    # 先删除 demo 数据再重建
依赖: psycopg2（VIDEO/AI 均为 PostgreSQL），urllib 标准库
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from urllib import request, error as url_error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..'))
VIDEO_DIR = os.path.join(REPO_ROOT, 'VIDEO')
AI_DIR = os.path.join(REPO_ROOT, 'AI')

AI_API = os.environ.get('AI_API_BASE', 'http://localhost:5000')

DEMO_PREFIX = 'LLM-DEMO-'
DEMO_TASK_NAMES = ['LLM-DEMO-实时研判', 'LLM-DEMO-抓拍研判']
DEMO_DEVICE_ID = '1787822551242498128'  # CH1-192.168.1.64（真实设备）
DEMO_DEVICE_NAME = 'CH1-192.168.1.64'


def log(msg: str):
    print(msg)


def ok(msg: str):
    print(f'  ✓ {msg}')


def warn(msg: str):
    print(f'  ! {msg}')


# ---------------- 数据库连接 ----------------

def load_database_url(project_dir: str, default_db: str) -> str:
    """从 .env 读取 DATABASE_URL。"""
    env_path = os.path.join(project_dir, '.env')
    if os.path.exists(env_path):
        with open(env_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('DATABASE_URL='):
                    return line.split('=', 1)[1].strip().strip('"').strip("'")
    return f'postgresql://postgres:postgres@localhost:5432/{default_db}'


def connect(project_dir: str, default_db: str):
    import psycopg2

    url = load_database_url(project_dir, default_db)
    # postgresql://user:pass@host:port/db
    rest = url.split('://', 1)[1]
    cred, host_part = rest.split('@', 1)
    user, _, password = cred.partition(':')
    host, _, db = host_part.partition(':')
    dbname = db.split('/')[1] if '/' in db else db
    port = db.split('/')[0] if '/' in db else '5432'
    return psycopg2.connect(host=host, port=int(port), user=user, password=password, dbname=dbname)


# ---------------- AI REST ----------------

def api(method: str, path: str, body: dict | None = None) -> dict:
    url = f'{AI_API}{path}'
    data = json.dumps(body).encode() if body is not None else None
    req = request.Request(url, data=data, method=method,
                          headers={'Content-Type': 'application/json'})
    try:
        with request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except url_error.HTTPError as e:
        raise RuntimeError(f'AI API {method} {path} -> HTTP {e.code}: {e.read().decode()[:200]}')


def existing_knowledge_set_ids() -> list[int]:
    """取现有知识集（专家创建要求知识集非空，复用 RAG demo 的知识集）。"""
    try:
        resp = api('GET', '/model/rag/knowledge-sets')
        sets = resp.get('data', []) or []
        return [int(s['id']) for s in sets[:2]]
    except Exception as e:
        warn(f'查询知识集失败: {e}')
        return []


def ensure_experts() -> dict:
    """按名称复用/创建两个研判智能体，返回 {名称: id}。"""
    experts = api('GET', '/model/rag/experts').get('data', [])
    set_ids = existing_knowledge_set_ids()
    result = {}
    specs = {
        'LLM-DEMO-视频研判专家': {
            'category': '智能研判',
            'system_prompt': (
                '你是视频事件研判专家。根据提供的告警图片/视频片段与检测信息，判断告警事件是否真实成立。'
                '输出 JSON：{"confirm": true/false, "confidence": 0~1, "reason": "简要中文理由"}。'
                '理由须结合画面中可见的目标与行为，不得臆测；画面不足以判断时 confirm 置 false 并说明。'
            ),
            'welcome_message': '我是视频事件研判专家，负责对告警视频片段做二次确认。',
        },
        'LLM-DEMO-图片研判专家': {
            'category': '智能研判',
            'system_prompt': (
                '你是告警图片研判专家。根据告警事件图片与检测框信息，判断告警是否成立。'
                '输出 JSON：{"confirm": true/false, "confidence": 0~1, "reason": "简要中文理由"}。'
                '看图说话，依据图中可见内容判断；图不清晰或无法判断时 confirm 置 false。'
            ),
            'welcome_message': '我是图片研判专家，负责对告警事件图片做快速复核。',
        },
    }
    for name, spec in specs.items():
        existing = [e for e in experts if e.get('name') == name]
        if existing:
            result[name] = existing[0]['id']
            ok(f'复用智能体 [{existing[0]["id"]}] {name}')
            continue
        resp = api('POST', '/model/rag/experts', {
            'name': name,
            'category': spec['category'],
            'system_prompt': spec['system_prompt'],
            'welcome_message': spec['welcome_message'],
            'knowledge_set_ids': set_ids,
        })
        eid = resp.get('data', {}).get('id')
        result[name] = eid
        ok(f'创建智能体 [{eid}] {name}')
    return result


def active_model_id() -> int | None:
    """取第一个激活的大模型（规则绑定用，可空=智能体默认模型）。"""
    try:
        resp = api('GET', '/model/llm/list?page=1&pageSize=100')
        data = resp.get('data', {})
        items = data.get('list', []) if isinstance(data, dict) else data
        for m in items or []:
            if m.get('is_active'):
                log(f'  绑定激活大模型 [{m["id"]}] {m.get("name")}')
                return int(m['id'])
    except Exception as e:
        warn(f'查询激活大模型失败（规则将使用智能体默认模型）: {e}')
    return None


# ---------------- Schema ensure（与服务启动 ensure 一致，幂等） ----------------

SCHEMA_DDL = [
    "ALTER TABLE algorithm_task ADD COLUMN IF NOT EXISTS llm_post_process_enabled BOOLEAN DEFAULT FALSE",
    "ALTER TABLE alert ADD COLUMN IF NOT EXISTS llm_judge_status VARCHAR(20)",
    "ALTER TABLE alert ADD COLUMN IF NOT EXISTS llm_judge_detail TEXT",
    """
    CREATE TABLE IF NOT EXISTS algorithm_task_llm_rule (
      id SERIAL PRIMARY KEY,
      task_id INTEGER NOT NULL,
      rule_name VARCHAR(100) NOT NULL,
      match_objects TEXT,
      match_events TEXT,
      agent_id INTEGER NOT NULL,
      model_id INTEGER,
      judge_mode VARCHAR(10) NOT NULL DEFAULT 'image',
      video_pre_seconds INTEGER DEFAULT 5,
      video_post_seconds INTEGER DEFAULT 10,
      video_max_seconds INTEGER DEFAULT 30,
      secondary_judge BOOLEAN DEFAULT FALSE,
      fail_policy VARCHAR(10) NOT NULL DEFAULT 'skip',
      prompt_override TEXT,
      require_json BOOLEAN DEFAULT TRUE,
      min_interval_sec INTEGER DEFAULT 0,
      priority SMALLINT DEFAULT 5,
      enabled BOOLEAN DEFAULT TRUE,
      created_at TIMESTAMP,
      updated_at TIMESTAMP,
      UNIQUE (task_id, rule_name)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS algorithm_llm_judge_result (
      id SERIAL PRIMARY KEY,
      correlation_id VARCHAR(64) NOT NULL,
      alert_id INTEGER NOT NULL,
      task_id INTEGER,
      device_id VARCHAR(100),
      rule_id INTEGER,
      agent_id INTEGER,
      model_id INTEGER,
      judge_mode VARCHAR(10),
      media_url VARCHAR(500),
      prompt TEXT,
      raw_response TEXT,
      confirm BOOLEAN,
      confidence FLOAT,
      reason TEXT,
      structured TEXT,
      duration_ms INTEGER,
      status VARCHAR(20) NOT NULL DEFAULT 'pending',
      error_msg TEXT,
      created_at TIMESTAMP,
      updated_at TIMESTAMP
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_llm_judge_result_corr ON algorithm_llm_judge_result (correlation_id)",
    "CREATE INDEX IF NOT EXISTS idx_llm_judge_result_alert ON algorithm_llm_judge_result (alert_id)",
    "CREATE INDEX IF NOT EXISTS idx_llm_rule_task ON algorithm_task_llm_rule (task_id)",
]


def ensure_schema(cur):
    log('== Schema ensure（新列/新表，幂等） ==')
    for stmt in SCHEMA_DDL:
        cur.execute(stmt)
    cur.execute(
        'ALTER TABLE algorithm_llm_judge_result '
        'ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP'
    )
    ok('algorithm_task.llm_post_process_enabled / alert.llm_judge_* / 规则表 / 研判结果表 已就绪')


# ---------------- 算法任务 ----------------

TASK_BASE = dict(
    detect_conf=0.5,
    extract_interval=12,
    tracking_enabled=False,
    tracking_similarity_threshold=0.2,
    tracking_max_age=25,
    tracking_smooth_alpha=0.25,
    alert_event_enabled=True,
    alert_event_suppress_time=5,
    face_detection_enabled=False,
    plate_detection_enabled=False,
    face_matching_enabled=False,
    plate_matching_enabled=False,
    alert_notification_enabled=False,
    alarm_suppress_time=300,
    frame_skip=25,
    status=0,
    is_enabled=False,
    run_status='stopped',
    schedule_policy='local',
    prefer_gpu=False,
    total_frames=0,
    total_detections=0,
    total_captures=0,
    sam_supplement_enabled=False,
    motion_gate_enabled=False,
    pose_analysis_enabled=False,
    pose_intent_enabled=False,
    post_process_enabled=False,
    post_process_replicas=1,
    defense_mode='full',
    executor='python',
    llm_post_process_enabled=True,
)


def ensure_tasks(cur) -> dict:
    """创建/复用 demo 任务，返回 {task_name: task_id}。"""
    log('== 算法任务 ==')
    now = datetime.now(timezone.utc)
    result = {}
    for name in DEMO_TASK_NAMES:
        cur.execute('SELECT id FROM algorithm_task WHERE task_name = %s', (name,))
        row = cur.fetchone()
        if row:
            result[name] = row[0]
            ok(f'复用任务 [{row[0]}] {name}')
            # 确保总开关开启（老数据可能未开启）
            cur.execute('UPDATE algorithm_task SET llm_post_process_enabled = TRUE WHERE id = %s', (row[0],))
            continue
        values = dict(TASK_BASE)
        values.update(
            task_name=name,
            task_code=f'demo-{uuid.uuid4().hex[:12]}',
            task_type='realtime' if '实时' in name else 'snap',
            created_at=now,
            updated_at=now,
        )
        if values['task_type'] == 'snap':
            values['cron_expression'] = '*/5 * * * *'
        cols = ', '.join(values)
        marks = ', '.join(['%s'] * len(values))
        cur.execute(f'INSERT INTO algorithm_task ({cols}) VALUES ({marks})', list(values.values()))
        cur.execute('SELECT id FROM algorithm_task WHERE task_name = %s', (name,))
        task_id = cur.fetchone()[0]
        cur.execute('INSERT INTO algorithm_task_device (task_id, device_id, created_at) VALUES (%s, %s, %s)',
                    (task_id, DEMO_DEVICE_ID, now))
        result[name] = task_id
        ok(f'创建任务 [{task_id}] {name}（device={DEMO_DEVICE_ID}）')
    return result


# ---------------- 研判规则 ----------------

def ensure_rules(cur, task_ids: dict, experts: dict, model_id: int | None) -> dict:
    """创建/复用规则，返回 {rule_name: rule_id}。"""
    log('== 研判规则 ==')
    now = datetime.now(timezone.utc)
    video_expert = experts['LLM-DEMO-视频研判专家']
    image_expert = experts['LLM-DEMO-图片研判专家']
    rt_task = task_ids['LLM-DEMO-实时研判']
    snap_task = task_ids['LLM-DEMO-抓拍研判']

    rules = [
        # 实时任务：未戴安全帽 -> 视频窗口 + 门控（确认才发通知，失败抑制）
        dict(task_id=rt_task, rule_name='未戴安全帽-视频门控确认',
             match_objects=json.dumps(['person'], ensure_ascii=False), match_events=None,
             agent_id=video_expert, model_id=model_id,
             judge_mode='video', video_pre_seconds=5, video_post_seconds=10, video_max_seconds=30,
             secondary_judge=True, fail_policy='reject',
             prompt_override=None, require_json=True, min_interval_sec=0, priority=10, enabled=True),
        # 实时任务：区域入侵 -> 图片研判，仅回写（后置增强）
        dict(task_id=rt_task, rule_name='区域入侵-图片回写增强',
             match_objects=None, match_events=json.dumps(['intrusion'], ensure_ascii=False),
             agent_id=image_expert, model_id=model_id,
             judge_mode='image', video_pre_seconds=5, video_post_seconds=10, video_max_seconds=30,
             secondary_judge=False, fail_policy='skip',
             prompt_override=None, require_json=True, min_interval_sec=0, priority=5, enabled=True),
        # 实时任务：兜底（全部事件）-> 图片研判，节流 60 秒
        dict(task_id=rt_task, rule_name='兜底-全对象图片研判',
             match_objects=None, match_events=None,
             agent_id=image_expert, model_id=None,
             judge_mode='image', video_pre_seconds=5, video_post_seconds=10, video_max_seconds=30,
             secondary_judge=False, fail_policy='skip',
             prompt_override=None, require_json=True, min_interval_sec=60, priority=1, enabled=True),
        # 抓拍任务：图片门控（确认才发通知，失败放行）
        dict(task_id=snap_task, rule_name='抓拍-图片门控',
             match_objects=None, match_events=None,
             agent_id=video_expert, model_id=model_id,
             judge_mode='image', video_pre_seconds=5, video_post_seconds=10, video_max_seconds=30,
             secondary_judge=True, fail_policy='confirm',
             prompt_override=None, require_json=True, min_interval_sec=0, priority=5, enabled=True),
    ]
    result = {}
    for r in rules:
        cur.execute('SELECT id FROM algorithm_task_llm_rule WHERE task_id = %s AND rule_name = %s',
                    (r['task_id'], r['rule_name']))
        row = cur.fetchone()
        if row:
            result[r['rule_name']] = row[0]
            ok(f'复用规则 [{row[0]}] {r["rule_name"]}')
            continue
        values = dict(r)
        values['created_at'] = now
        values['updated_at'] = now
        cols = ', '.join(values)
        marks = ', '.join(['%s'] * len(values))
        cur.execute(f'INSERT INTO algorithm_task_llm_rule ({cols}) VALUES ({marks})', list(values.values()))
        cur.execute('SELECT id FROM algorithm_task_llm_rule WHERE task_id = %s AND rule_name = %s',
                    (r['task_id'], r['rule_name']))
        rid = cur.fetchone()[0]
        result[r['rule_name']] = rid
        ok(f'创建规则 [{rid}] {r["rule_name"]}（{r["judge_mode"]}, 门控={r["secondary_judge"]}）')
    return result


# ---------------- 告警 ----------------

def alert_payload(task_id: int, task_name: str, object_: str, event: str, region: str | None,
                  minutes_ago: int, llm: dict | None, status: str | None, detail: dict | None,
                  corr_suffix: str) -> dict:
    """构造 alert 行。llm=None 表示该告警未参与研判（对照组）。corr_suffix 固定用于幂等去重。"""
    information = {
        'detections': [{'class_name': object_, 'confidence': 0.87}],
        'task_type': 'realtime' if '实时' in task_name else 'snap',
    }
    if llm is not None:
        node = {'status': llm}
        if detail is not None:
            node['detail'] = detail
        information['llm'] = node
    now = datetime.now(timezone.utc)
    return dict(
        object=object_,
        event=event,
        region=region,
        information=json.dumps(information, ensure_ascii=False),
        time=now - timedelta(minutes=minutes_ago),
        device_id=DEMO_DEVICE_ID,
        device_name=DEMO_DEVICE_NAME,
        task_type='realtime' if '实时' in task_name else 'snap',
        task_id=task_id,
        task_name=task_name,
        correlation_id=f'llm-demo-alert-{corr_suffix}',
        notification_sent=False,
        llm_judge_status=status,
        llm_judge_detail=json.dumps(detail, ensure_ascii=False) if detail else None,
    )


def ensure_alerts(cur, task_ids: dict, experts: dict, rules: dict, model_id: int | None):
    """创建 6 条告警（按 correlation_id 去重），返回创建的条数。"""
    log('== 告警数据（information.llm 展示形态） ==')
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    video_expert = experts['LLM-DEMO-视频研判专家']
    image_expert = experts['LLM-DEMO-图片研判专家']
    rt_task = task_ids['LLM-DEMO-实时研判']
    snap_task = task_ids['LLM-DEMO-抓拍研判']

    def llm_detail(confirm, confidence, reason, attributes, judge_mode, agent_id, rule_name,
                   duration_ms):
        return {
            'confirm': confirm,
            'confidence': confidence,
            'reason': reason,
            'attributes': attributes,
            'duration_ms': duration_ms,
            'model_id': model_id,
            'agent_id': agent_id,
            'judge_mode': judge_mode,
            'rule_id': rules.get(rule_name),
            'correlation_id': None,  # 与 alert.correlation_id 对齐（展示层不依赖）
            'judged_at': now_ms - 60000,
        }

    rows = [
        # 1. 实时-未戴安全帽：视频门控研判确认（成立）
        alert_payload(rt_task, 'LLM-DEMO-实时研判', 'person', 'no_helmet', '东门通道', 8,
                      'confirmed', 'confirmed',
                      llm_detail(True, 0.92, '画面中人员未佩戴安全帽，且无佩戴痕迹，符合未戴安全帽告警特征，事件成立。',
                                 {'violation': 'no_helmet', 'count': 1, 'suggest': '通知现场巡检'},
                                 'video', video_expert, '未戴安全帽-视频门控确认', 1863), '01'),
        # 2. 实时-区域入侵：图片研判驳回（不成立）
        alert_payload(rt_task, 'LLM-DEMO-实时研判', 'person', 'intrusion', '围墙西侧', 23,
                      'rejected', 'rejected',
                      llm_detail(False, 0.78, '画面中人员位于警戒线外侧的公共通道，未进入禁入区域，判定为误报。',
                                 {'inside_zone': False, 'distance': '2.3m'},
                                 'image', image_expert, '区域入侵-图片回写增强', 940), '02'),
        # 3. 实时-人员摔倒：研判调用失败
        alert_payload(rt_task, 'LLM-DEMO-实时研判', 'person', 'fall', '车间B区', 41,
                      'error', 'error',
                      dict(confirm=None, confidence=None, reason=None, attributes=None,
                           duration_ms=None, model_id=model_id, agent_id=video_expert,
                           judge_mode='video', rule_id=rules.get('兜底-全对象图片研判'),
                           correlation_id=None, judged_at=now_ms - 2400000), '03'),
        # 4. 实时-人员聚集：对照组（未配置规则命中/未参与研判）
        alert_payload(rt_task, 'LLM-DEMO-实时研判', 'person', 'crowd', '食堂门口', 55,
                      None, None, None, '04'),
        # 5. 抓拍-未戴安全帽：门控研判确认（图片）
        alert_payload(snap_task, 'LLM-DEMO-抓拍研判', 'person', 'no_helmet', '装卸区', 6,
                      'confirmed', 'confirmed',
                      llm_detail(True, 0.88, '抓拍画面清晰，人员未佩戴安全帽，事件成立。',
                                 {'violation': 'no_helmet', 'count': 1},
                                 'image', video_expert, '抓拍-图片门控', 1120), '05'),
        # 6. 抓拍-未戴安全帽：待研判（已投递独立队列）
        alert_payload(snap_task, 'LLM-DEMO-抓拍研判', 'person', 'no_helmet', '装卸区', 2,
                      'pending', 'pending', None, '06'),
    ]
    created = 0
    for row in rows:
        cur.execute('SELECT id FROM alert WHERE correlation_id = %s', (row['correlation_id'],))
        if cur.fetchone():
            continue
        values = dict(row)
        cols = ', '.join(values)
        marks = ', '.join(['%s'] * len(values))
        cur.execute(f'INSERT INTO alert ({cols}) VALUES ({marks})', list(values.values()))
        created += 1
    ok(f'告警就绪（新建 {created} 条，含 confirmed/rejected/error/pending/对照组）')
    return created


# ---------------- 主流程 ----------------

def main():
    parser = argparse.ArgumentParser(description='大模型（LLM）后处理 demo 造数')
    parser.add_argument('--reset', action='store_true', help='先删除 demo 数据再重建')
    args = parser.parse_args()

    vconn = connect(VIDEO_DIR, 'iot-video20')
    vconn.autocommit = False
    try:
        cur = vconn.cursor()
        if args.reset:
            log('== 清理 demo 数据 ==')
            cur.execute("DELETE FROM alert WHERE task_name LIKE %s", (DEMO_PREFIX + '%',))
            cur.execute("DELETE FROM algorithm_task_llm_rule WHERE task_id IN "
                        "(SELECT id FROM algorithm_task WHERE task_name LIKE %s)", (DEMO_PREFIX + '%',))
            cur.execute("DELETE FROM algorithm_task_device WHERE task_id IN "
                        "(SELECT id FROM algorithm_task WHERE task_name LIKE %s)", (DEMO_PREFIX + '%',))
            cur.execute("DELETE FROM algorithm_task WHERE task_name LIKE %s", (DEMO_PREFIX + '%',))
            ok('已删除 demo 任务/规则/告警')

        ensure_schema(cur)
        experts = ensure_experts()
        model_id = active_model_id()
        task_ids = ensure_tasks(cur)
        rules = ensure_rules(cur, task_ids, experts, model_id)
        ensure_alerts(cur, task_ids, experts, rules, model_id)
        vconn.commit()
    except Exception:
        vconn.rollback()
        raise
    finally:
        vconn.close()

    # ---------------- 汇总 ----------------
    vconn = connect(VIDEO_DIR, 'iot-video20')
    try:
        cur = vconn.cursor()
        cur.execute('SELECT count(*) FROM algorithm_task WHERE task_name LIKE %s', (DEMO_PREFIX + '%',))
        tasks = cur.fetchone()[0]
        cur.execute('SELECT count(*) FROM algorithm_task_llm_rule WHERE task_id IN '
                    '(SELECT id FROM algorithm_task WHERE task_name LIKE %s)', (DEMO_PREFIX + '%',))
        rule_count = cur.fetchone()[0]
        cur.execute('SELECT count(*) FROM alert WHERE task_name LIKE %s', (DEMO_PREFIX + '%',))
        alerts = cur.fetchone()[0]
    finally:
        vconn.close()

    print()
    log('=' * 62)
    log('Demo 数据就绪：任务 %s | 规则 %s | 告警 %s' % (tasks, rule_count, alerts))
    log('=' * 62)
    log('浏览器检查指引：')
    log('  1. 算法任务页 -> LLM-DEMO-实时研判 -> 编辑 -> 大模型（LLM）后处理区块')
    log('     -> 「管理研判规则」查看 3 条规则（视频门控/图片回写/兜底）')
    log('  2. 抓拍任务 LLM-DEMO-抓拍研判 同样可查看「抓拍-图片门控」规则')
    log('  3. 告警页查看 6 条 demo 告警 -> 详情弹窗底部「大模型研判」展示各状态')
    log('     （事件成立/不成立/失败/待研判，以及对照组无研判区块）')
    warn('注意：若 VIDEO/AI 服务尚未重启加载新代码，请先重启：')
    warn('  - VIDEO 服务需重启以注册 /video/algorithm/llm-rule 接口并识别 llm_post_process_enabled')
    warn('  - AI 服务需重启以注册 /model/llm/internal/judge 接口（真实研判链路）')
    warn('  - 重启后服务启动时的 ensure 迁移与脚本幂等兼容，无需重复执行本脚本')


if __name__ == '__main__':
    main()
