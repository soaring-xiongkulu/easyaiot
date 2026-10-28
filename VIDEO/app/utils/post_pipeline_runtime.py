"""Shared runtime requirements for temporal POST plugins."""
import json


def needs_continuous_observations(task):
    raw = getattr(task, 'post_pipeline', None)
    try:
        steps = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, ValueError):
        return False
    return isinstance(steps, list) and any(
        isinstance(step, dict) and step.get('enabled') is not False and
        step.get('plugin') in ('line_cross', 'region_enter_exit', 'dwell_timer', 'headcount_gate')
        for step in steps
    )
