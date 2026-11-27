"""解析 AI 推理流实际发布到的 SRS 主机。"""
from __future__ import annotations

import logging
import os
import socket
from collections.abc import Callable


DEFAULT_SRS_HOST_CANDIDATES = (
    '127.0.0.1',
    'localhost',
    'srs-server',
    'srs',
    'host.docker.internal',
)


def _port_is_open(host: str, port: int, timeout: float = 0.25) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def resolve_srs_publish_host(
    configured_host: str | None = None,
    *,
    port: int = 1935,
    probe: Callable[[str, int], bool] | None = None,
) -> str:
    """显式配置优先，否则探测 host 网络与 bridge 网络中的常见 SRS 地址。"""
    configured = (
        configured_host
        if configured_host is not None
        else os.getenv('MODEL_AI_SRS_HOST', '')
    ).strip()
    if configured:
        return configured

    check = probe or _port_is_open
    raw_candidates = os.getenv('MODEL_AI_SRS_HOST_CANDIDATES', '')
    candidates = tuple(
        item.strip() for item in raw_candidates.split(',') if item.strip()
    ) or DEFAULT_SRS_HOST_CANDIDATES
    for host in candidates:
        if check(host, port):
            logging.info('AI 推理流选用 SRS 发布地址: %s:%s', host, port)
            return host

    logging.warning('未探测到可用 SRS，暂按本机地址发布: 127.0.0.1:%s', port)
    return '127.0.0.1'


def resolve_srs_play_host() -> str:
    """返回给浏览器的地址不能暴露 Docker 内部服务名。"""
    return (os.getenv('MODEL_AI_SRS_PLAY_HOST') or '127.0.0.1').strip() or '127.0.0.1'
