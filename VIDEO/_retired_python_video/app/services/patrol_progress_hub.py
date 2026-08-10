"""
巡检进度 SSE 订阅中心：心跳/状态变更时向已连接客户端推送。
"""
from __future__ import annotations

import queue
import threading
from typing import Dict, List

_subscribers: Dict[int, List[queue.Queue]] = {}
_lock = threading.Lock()


def subscribe(session_id: int) -> queue.Queue:
    q: queue.Queue = queue.Queue(maxsize=64)
    with _lock:
        _subscribers.setdefault(session_id, []).append(q)
    return q


def unsubscribe(session_id: int, q: queue.Queue) -> None:
    with _lock:
        subs = _subscribers.get(session_id)
        if not subs:
            return
        try:
            subs.remove(q)
        except ValueError:
            pass
        if not subs:
            _subscribers.pop(session_id, None)


def publish(session_id: int, event_type: str, data: dict) -> None:
    payload = {'type': event_type, 'data': data}
    with _lock:
        subs = list(_subscribers.get(session_id, []))
    for q in subs:
        try:
            q.put_nowait(payload)
        except queue.Full:
            try:
                q.get_nowait()
            except queue.Empty:
                pass
            try:
                q.put_nowait(payload)
            except queue.Full:
                pass
