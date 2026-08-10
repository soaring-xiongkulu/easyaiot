import logging
import os
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

import requests

from app.utils.ip_utils import resolve_ipv4_for_stream_urls

_logger = logging.getLogger(__name__)

_GB28181_API_PORT = 48088


GB28181_SOURCE_PREFIX = 'gb28181://'


def is_gb28181_source(source: Optional[str]) -> bool:
    return bool(source and source.strip().lower().startswith(GB28181_SOURCE_PREFIX))


def parse_gb28181_source(source: Optional[str]) -> Optional[Tuple[str, str]]:
    if not is_gb28181_source(source):
        return None

    parsed = urlparse(source.strip())
    device_id = (parsed.netloc or '').strip()
    channel_id = (parsed.path or '').strip('/ ')
    if not device_id or not channel_id:
        return None
    return device_id, channel_id


def _gb28181_http_timeout(default: int = 60) -> int:
    """点播 HTTP 读超时（秒）。WVP play 为 DeferredResult，默认 play-timeout 可达 180s。"""
    raw = (os.getenv('GB28181_HTTP_READ_TIMEOUT') or '').strip()
    if not raw:
        return default
    try:
        return max(5, int(raw))
    except ValueError:
        return default


def _host_ip_for_gb28181_api() -> str:
    """与 camera_service / iot-gb28181 MediaConfig 一致：优先 POD_IP、HOST_IP，再探测宿主机内网 IP。"""
    for key in ('POD_IP', 'HOST_IP'):
        ip = (os.getenv(key) or '').strip()
        if ip and ip != '127.0.0.1':
            return ip
    detected = resolve_ipv4_for_stream_urls()
    if detected:
        return detected
    return '127.0.0.1'


def _direct_gb28181_api_bases() -> List[str]:
    """直连 WVP /api 的候选根地址（去重、保序）。"""
    host = _host_ip_for_gb28181_api()
    candidates = [
        f'http://127.0.0.1:{_GB28181_API_PORT}/api',
        f'http://localhost:{_GB28181_API_PORT}/api',
    ]
    if host not in ('127.0.0.1', 'localhost'):
        candidates.append(f'http://{host}:{_GB28181_API_PORT}/api')
    seen = set()
    out: List[str] = []
    for base in candidates:
        if base not in seen:
            seen.add(base)
            out.append(base)
    return out


def _candidate_bases() -> Iterable[str]:
    seen: set[str] = set()
    ordered: List[str] = []

    def _add(base: str) -> None:
        b = (base or '').strip().rstrip('/')
        if b and b not in seen:
            seen.add(b)
            ordered.append(b)

    configured_base = (os.getenv('GB28181_SERVICE_URL') or '').strip().rstrip('/')
    if configured_base:
        _add(configured_base)

    gateway_url = (os.getenv('GATEWAY_URL') or '').strip().rstrip('/')
    if gateway_url:
        if gateway_url.endswith('/admin-api'):
            _add(f'{gateway_url}/gb28181')
        else:
            _add(f'{gateway_url}/admin-api/gb28181')

    for base in _direct_gb28181_api_bases():
        _add(base)

    return ordered


def _build_play_url(base_url: str, device_id: str, channel_id: str) -> str:
    base = base_url.rstrip('/')
    if base.endswith('/api'):
        return f'{base}/play/start/{device_id}/{channel_id}'
    return f'{base}/play/start/{device_id}/{channel_id}'


def _body_suggests_hevc_rtmp(body: dict) -> bool:
    """播放接口返回的 RTMP 地址若标明 HEVC/H.265，OpenCV 内置 FFmpeg 拉 RTMP(FLV) 常失败 (codec_id=0)。"""
    if not isinstance(body, dict):
        return False
    for key in ('rtmp', 'rtmps'):
        u = body.get(key)
        if not isinstance(u, str) or not u.strip():
            continue
        lu = u.lower()
        if 'h265' in lu or 'hevc' in lu:
            return True
    return False


def _gb28181_play_candidates(body: dict) -> Tuple[List[Optional[str]], Dict[str, Any]]:
    """
    按协议顺序返回候选播放地址，并附带策略元数据（用于日志与排障）。

    默认 (GB28181_PLAY_PROTOCOL=rtmp_first) 将 RTMP 置于 RTSP 之前：
    ZLMediaKit 在「RTMP 协议无读者」时会触发 on_stream_none_reader；WVP/iot-gb28181
    在 streamOnDemand=true 时会对国标 rtp 流返回 close。若仅使用 RTSP 拉流，则
    RTMP 侧始终无读者，约 streamNoneReaderDelayMS（常配 20s）后整路流被释放，
    实时算法仍用 OpenCV/FFmpeg 拉流会表现为灰屏/断流。以 RTMP 作为输入时，拉流端
    会占用 RTMP 读者，可保持流存活。

    若环境仅通 RTSP 或拉 RTMP 失败，可设 GB28181_PLAY_PROTOCOL=rtsp_first 恢复旧顺序。

    GB28181_HEVC_RTSP_FIRST（默认 1）：当播放接口返回的 RTMP 地址含 HEVC/H.265 线索时，
    在仍为 rtmp_first 策略的前提下自动改为「先 RTSP」——用于规避 OpenCV VideoCapture 对
    RTMP+HEVC 无法建解码器的问题。若因此出现 ZLM「无 RTMP 读者断流」，可调大
    streamNoneReaderDelayMS，或设 GB28181_HEVC_RTSP_FIRST=0 并改用带 libx265 的 FFmpeg 构建 OpenCV。
    """
    flv_block = [
        body.get('flv'),
        body.get('https_flv'),
        body.get('ws_flv'),
    ]
    other = [
        body.get('fmp4'),
        body.get('hls'),
        body.get('rtc'),
        body.get('rtcs'),
    ]
    mode = (os.getenv('GB28181_PLAY_PROTOCOL') or 'rtmp_first').strip().lower()
    hevc_rtsp_first = (os.getenv('GB28181_HEVC_RTSP_FIRST', '1').strip().lower() not in (
        '0', 'false', 'no', 'off',
    ))
    hevc_hint = _body_suggests_hevc_rtmp(body if isinstance(body, dict) else {})

    meta: Dict[str, Any] = {
        'play_protocol': mode,
        'hevc_rtsp_first_env_on': hevc_rtsp_first,
        'hevc_hint': hevc_hint,
        'branch': 'rtmp_first',
    }

    if mode in ('rtsp_first', 'rtsp', 'legacy'):
        meta['branch'] = 'rtsp_first'
        candidates = [
            body.get('rtsp'),
            body.get('rtsps'),
            body.get('rtmp'),
            body.get('rtmps'),
            *flv_block,
            *other,
        ]
        return candidates, meta

    if hevc_rtsp_first and hevc_hint:
        meta['branch'] = 'hevc_rtsp_first'
        candidates = [
            body.get('rtsp'),
            body.get('rtsps'),
            body.get('rtmp'),
            body.get('rtmps'),
            *flv_block,
            *other,
        ]
        return candidates, meta

    meta['branch'] = 'rtmp_first'
    candidates = [
        body.get('rtmp'),
        body.get('rtmps'),
        body.get('rtsp'),
        body.get('rtsps'),
        *flv_block,
        *other,
    ]
    return candidates, meta


def _format_gb28181_choice_log(chosen_url: str, meta: Dict[str, Any]) -> str:
    """单行说明：最终选用协议与选路原因（便于对照 ZLM / OpenCV 灰屏问题）。"""
    scheme = urlparse(chosen_url).scheme.lower() if chosen_url else ''
    branch = meta.get('branch', '')
    branch_tip = {
        'rtsp_first': '接口顺序优先RTSP',
        'rtmp_first': '接口顺序优先RTMP(占读者保活)',
        'hevc_rtsp_first': 'HEVC+RTMP线索则优先RTSP(OpenCV兼容)',
    }.get(branch, branch)
    hevc_on = '开启' if meta.get('hevc_rtsp_first_env_on') else '关闭'
    hint = '是' if meta.get('hevc_hint') else '否'
    zlm_tip = ''
    if branch == 'hevc_rtsp_first':
        zlm_tip = '；若仅RTSP读者导致ZLM断流可调大streamNoneReaderDelayMS或子码流改H.264'
    elif branch == 'rtsp_first':
        zlm_tip = '；若RTMP长期无读者可能被ZLM回收，可调streamNoneReaderDelayMS或改用rtmp_first'
    return (
        f'选用={scheme or "?"} | {branch_tip} | PLAY_PROTOCOL={meta.get("play_protocol")} | '
        f'HEVC线索={hint} | HEVC_RTSP_FIRST={hevc_on}{zlm_tip}'
    )


def _unwrap_wvp_play_body(payload: dict) -> Tuple[Optional[dict], Optional[str]]:
    """解析 WVP 播放接口 JSON：外层 code=0 时，流地址可能在 data 或 data.data（StreamContent）。"""
    if not isinstance(payload, dict):
        return None, 'invalid payload'
    body = payload.get('data') if isinstance(payload.get('data'), dict) else payload
    if not isinstance(body, dict):
        return None, 'empty play response'

    inner_code = body.get('code')
    if inner_code is not None and inner_code not in (0, 200):
        return None, (body.get('msg') or f'WVP play code={inner_code}').strip()

    nested = body.get('data')
    if isinstance(nested, dict) and _all_play_urls_from_body(nested):
        return nested, None
    if _all_play_urls_from_body(body):
        return body, None
    return None, None


def _extract_stream_url_and_meta(payload: dict) -> Tuple[Optional[str], Dict[str, Any]]:
    body, err = _unwrap_wvp_play_body(payload if isinstance(payload, dict) else {})
    if not isinstance(body, dict):
        return None, {'wvp_error': err} if err else {}
    candidates, meta = _gb28181_play_candidates(body)
    chosen = next((url for url in candidates if isinstance(url, str) and url.strip()), None)
    if err:
        meta['wvp_error'] = err
    return chosen, meta


def _extract_stream_url(payload: dict) -> Optional[str]:
    url, _ = _extract_stream_url_and_meta(payload)
    return url


def _all_play_urls_from_body(body: dict) -> List[str]:
    """播放接口 data 中全部可播放 URL（去重、保序）。"""
    if not isinstance(body, dict):
        return []
    keys = (
        'rtmp', 'rtmps', 'rtsp', 'rtsps',
        'flv', 'https_flv', 'ws_flv',
        'fmp4', 'hls', 'rtc', 'rtcs',
    )
    seen = set()
    out: List[str] = []
    for key in keys:
        val = body.get(key)
        if not isinstance(val, str):
            continue
        u = val.strip()
        if not u or u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


def _fetch_gb28181_play_body(
    source: Optional[str],
    *,
    timeout: Optional[int] = None,
) -> Tuple[Optional[Tuple[str, str]], Optional[dict], List[str]]:
    """返回 (device_id, channel_id), play body, errors。"""
    parsed = parse_gb28181_source(source)
    if not parsed:
        return None, None, ['invalid gb28181 source']

    device_id, channel_id = parsed
    headers = {}
    jwt_token = (os.getenv('JWT_TOKEN') or '').strip()
    if jwt_token:
        headers['X-Authorization'] = f'Bearer {jwt_token}'

    http_timeout = timeout if timeout is not None else _gb28181_http_timeout()
    errors: List[str] = []
    for base_url in _candidate_bases():
        play_url = _build_play_url(base_url, device_id, channel_id)
        try:
            response = requests.get(play_url, headers=headers, timeout=http_timeout)
            response.raise_for_status()
            payload = response.json()
            body, wvp_err = _unwrap_wvp_play_body(payload if isinstance(payload, dict) else {})
            if isinstance(body, dict):
                return parsed, body, errors
            errors.append(f'{base_url}: {wvp_err or "未返回可播放流地址"}')
        except Exception as exc:
            errors.append(f'{base_url}: {exc}')
    return parsed, None, errors


def resolve_gb28181_alternate_pull_url(
    source: Optional[str],
    current_url: str,
    *,
    prefer_schemes: Tuple[str, ...] = ('rtsp', 'rtsps'),
    timeout: Optional[int] = None,
    logger=None,
) -> Optional[str]:
    """
    OpenCV 拉 GB28181 的 RTMP 失败时，从播放接口选取备用地址（默认 RTSP）。

    用于 rtmp_first 保活策略与 OpenCV RTMP 不兼容时的自动降级。
    """
    if not is_gb28181_source(source) or not (current_url or '').strip():
        return None

    _disable = (os.getenv('GB28181_OPENCV_RTMP_FALLBACK_RTSP', '1').strip().lower()
                in ('0', 'false', 'no', 'off'))
    if _disable:
        return None

    parsed, body, errors = _fetch_gb28181_play_body(source, timeout=timeout)
    if not parsed or not body:
        return None

    device_id, channel_id = parsed
    current = current_url.strip()
    current_scheme = urlparse(current).scheme.lower()
    candidates = _all_play_urls_from_body(body)

    for scheme in prefer_schemes:
        for url in candidates:
            if urlparse(url).scheme.lower() == scheme and url != current:
                log_fn = logger.warning if logger else _logger.warning
                log_fn(
                    f'GB28181 OpenCV 拉流降级: {device_id}/{channel_id} '
                    f'{current_scheme} -> {scheme} | {current} -> {url}'
                )
                return url

    for url in candidates:
        if url != current and urlparse(url).scheme.lower() != current_scheme:
            log_fn = logger.warning if logger else _logger.warning
            log_fn(
                f'GB28181 OpenCV 拉流降级(其它协议): {device_id}/{channel_id} '
                f'{current} -> {url}'
            )
            return url

    if logger and errors:
        logger.debug(
            f'GB28181 无可用备用拉流地址: {device_id}/{channel_id}, errors={"; ".join(errors)}'
        )
    return None


def _fixture_resolve_map() -> Dict[str, str]:
    """
    Parity / offline fixture map so CAP-GB28181-SRC can certify without WVP.

    Env GB28181_FIXTURE_MAP:
      - JSON object: {"gb28181://dev/ch":"rtsp://..."} or file path
      - or semicolon pairs: gb28181://dev/ch=file://...;gb28181://a/b=rtsp://...
    """
    raw = (os.getenv('GB28181_FIXTURE_MAP') or '').strip()
    if not raw:
        return {}
    if raw.startswith('{'):
        try:
            import json

            data = json.loads(raw)
            if isinstance(data, dict):
                return {
                    str(k).strip(): str(v).strip()
                    for k, v in data.items()
                    if str(k).strip() and str(v).strip()
                }
        except Exception:
            return {}
    out: Dict[str, str] = {}
    for part in raw.split(';'):
        part = part.strip()
        if not part or '=' not in part:
            continue
        key, val = part.split('=', 1)
        key, val = key.strip(), val.strip()
        if key and val:
            out[key] = val
    return out


def resolve_gb28181_source(
    source: Optional[str],
    *,
    timeout: Optional[int] = None,
    logger=None,
) -> Optional[str]:
    parsed = parse_gb28181_source(source)
    if not parsed:
        return source

    device_id, channel_id = parsed
    src = (source or '').strip()
    fixture = _fixture_resolve_map().get(src)
    if fixture:
        log_fn = logger.info if logger else _logger.info
        log_fn(
            f'GB28181源解析成功(夹具映射): {device_id}/{channel_id} -> {fixture} | CAP-GB28181-SRC'
        )
        return fixture

    headers = {}
    jwt_token = (os.getenv('JWT_TOKEN') or '').strip()
    if jwt_token:
        headers['X-Authorization'] = f'Bearer {jwt_token}'

    http_timeout = timeout if timeout is not None else _gb28181_http_timeout()
    errors = []
    for base_url in _candidate_bases():
        play_url = _build_play_url(base_url, device_id, channel_id)
        try:
            response = requests.get(play_url, headers=headers, timeout=http_timeout)
            response.raise_for_status()
            payload = response.json()
            stream_url, meta = _extract_stream_url_and_meta(payload if isinstance(payload, dict) else {})
            if stream_url:
                detail = _format_gb28181_choice_log(stream_url, meta)
                log_fn = logger.info if logger else _logger.info
                log_fn(
                    f'GB28181源解析成功: {device_id}/{channel_id} -> {stream_url} | {detail} (via {base_url})'
                )
                return stream_url
            wvp_err = meta.get('wvp_error') if isinstance(meta, dict) else None
            errors.append(f'{base_url}: {wvp_err or "未返回可播放流地址"}')
        except Exception as exc:
            errors.append(f'{base_url}: {exc}')

    if logger:
        logger.error(
            f'GB28181源解析失败: {device_id}/{channel_id}, errors={"; ".join(errors)}'
        )
    return None
