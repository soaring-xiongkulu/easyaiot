"""Business-facing results from persisted POST alerts (independent of LLM jobs)."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

BUSINESS_PLUGINS = ('line_cross', 'region_enter_exit', 'dwell_timer', 'headcount_gate')


def business_results(information, region_id=None):
    if isinstance(information, str):
        try:
            information = json.loads(information)
        except (ValueError, TypeError):
            return {}
    if not isinstance(information, dict):
        return {}
    enrichment = information.get('enrichment')
    if not isinstance(enrichment, dict):
        return {}
    rules = enrichment.get('business_rules')
    if isinstance(rules, list):
        combined = {}
        for rule in rules:
            if not isinstance(rule, dict) or (region_id is not None and rule.get('region_id') != region_id):
                continue
            plugin, patch = rule.get('plugin'), rule.get('result')
            if plugin not in BUSINESS_PLUGINS or not isinstance(patch, dict):
                continue
            target = combined.setdefault(plugin, {})
            for key, value in patch.items():
                if isinstance(value, list):
                    target[key] = target.get(key, []) + value
                elif key == 'count':
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        target[key] = max(target.get(key, 0), value)
                else:
                    target[key] = value
        return combined
    if region_id is not None:
        combined = {}
        for plugin, events_key in [('line_cross', 'crossed'), ('region_enter_exit', 'events'), ('dwell_timer', 'dwells')]:
            patch = enrichment.get(plugin)
            if not isinstance(patch, dict):
                continue
            events = [e for e in (patch.get(events_key) or []) if isinstance(e, dict) and e.get('region_id') == region_id]
            if events:
                combined[plugin] = {**patch, events_key: events}
        return combined
    return {key: enrichment[key] for key in BUSINESS_PLUGINS
            if isinstance(enrichment.get(key), dict)}


def summarize_result(summary, results):
    for event in results.get('line_cross', {}).get('crossed') or []:
        if isinstance(event, dict):
            summary['crossings'] += 1
            direction = event.get('direction')
            if direction in ('forward', 'backward'):
                summary[direction] += 1
    for event in results.get('region_enter_exit', {}).get('events') or []:
        if isinstance(event, dict) and event.get('event') in ('enter', 'exit'):
            summary[event['event']] += 1
    if 'dwell_timer' in results:
        summary['dwell_alerts'] += 1
    count = results.get('headcount_gate', {}).get('count')
    if isinstance(count, (int, float)) and not isinstance(count, bool):
        summary['peak_count'] = max(summary['peak_count'], count)


def list_business_results(task_id, args):
    from models import Alert

    page = int(args.get('page', 1))
    size = int(args.get('page_size', 20))
    if page < 1 or not 1 <= size <= 100:
        raise ValueError('页码须大于 0，每页条数须为 1~100')
    now = datetime.now(timezone.utc)
    start = datetime.fromisoformat(args['start'].replace('Z', '+00:00')) if args.get('start') else now - timedelta(days=1)
    end = datetime.fromisoformat(args['end'].replace('Z', '+00:00')) if args.get('end') else now
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError('查询时间必须包含时区')
    if not timedelta(0) < end - start <= timedelta(days=31):
        raise ValueError('查询时间范围须在 31 天以内')
    start = start.astimezone(timezone.utc)
    end = end.astimezone(timezone.utc)
    plugin = args.get('plugin', '')
    region_id = int(args['region_id']) if args.get('region_id') else None
    if plugin and plugin not in BUSINESS_PLUGINS:
        raise ValueError('不支持的业务插件')
    query = Alert.query.filter(Alert.task_id == task_id, Alert.time >= start, Alert.time < end)
    if args.get('device_id'):
        query = query.filter(Alert.device_id == args['device_id'])
    # Select only lightweight columns; no image loading or LLM queue dependency.
    query = query.with_entities(Alert.id, Alert.time, Alert.device_id, Alert.device_name,
                                Alert.region, Alert.information)
    summary = dict.fromkeys(('crossings', 'forward', 'backward', 'enter', 'exit', 'dwell_alerts', 'peak_count'), 0)
    items = []
    total = 0
    for row in query.order_by(Alert.time.desc(), Alert.id.desc()).yield_per(500):
        results = business_results(row.information, region_id)
        if not results or (plugin and plugin not in results):
            continue
        summarize_result(summary, results)
        if (page - 1) * size <= total < page * size:
            event_time = row.time if row.time.tzinfo else row.time.replace(tzinfo=timezone.utc)
            items.append({'id': row.id, 'time': event_time.isoformat(), 'device_id': row.device_id,
                          'device_name': row.device_name, 'region': row.region, 'results': results})
        total += 1
    return {'items': items, 'total': total, 'summary': summary, 'page': page, 'page_size': size,
            'start': start.isoformat(), 'end': end.isoformat()}
