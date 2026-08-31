"""
统一大模型调用引擎 — 全平台唯一出站通道。

所有厂商（百炼 / DeepSeek / 智谱 / OpenAI / Anthropic 兼容端点 / 本地 vLLM 等）
统一走 OpenAI 兼容协议 /chat/completions；vendor / model_type / service_type
不再产生任何调用分支。
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

# 各业务模式的提示词增强（与重构前行为一致；图片/视频措辞区分）
VISION_PROMPT_BY_MODE = {
    'inference': '作为视觉推理专家，请分析这张图片：{prompt}',
    'understanding': '作为视觉理解专家，请深入理解这张图片：{prompt}',
    'deep-thinking': '作为深度思考专家，请对这张图片进行多角度深度分析：{prompt}',
}
VIDEO_PROMPT_BY_MODE = {
    'inference': '作为视觉推理专家，请分析这个视频：{prompt}',
    'understanding': '{prompt}',  # 理解模式使用原始提示词
    'deep-thinking': '作为深度思考专家，请对这段视频进行多角度深度分析：{prompt}',
}


def build_chat_url(base_url: str) -> str:
    """构建 chat/completions 端点：兼容 /v1 结尾、/v4 等 GNOME 版本段、已含完整路径三种写法。"""
    url = (base_url or '').strip().rstrip('/')
    if url.endswith('/chat/completions'):
        return url
    # /v1、/v4 等版本段结尾（如 智谱 paas/v4）直接追加；其余补 /v1 前缀
    if re.search(r'/v\d+$', url) or '/v1' in url:
        return f"{url}/chat/completions"
    return f"{url}/v1/chat/completions"


def build_headers(api_key: str) -> Dict[str, str]:
    headers = {'Content-Type': 'application/json'}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    return headers


def enhance_prompt(prompt: str, mode: Optional[str], media: str = 'vision') -> str:
    """按模式增强提示词；mode 为空返回原始提示词。"""
    if not mode:
        return prompt
    table = VISION_PROMPT_BY_MODE if media == 'vision' else VIDEO_PROMPT_BY_MODE
    return table.get(mode, '{prompt}').format(prompt=prompt)


def build_vision_messages(prompt: str, image_data_url: str) -> List[dict]:
    """图片多模态消息（OpenAI 兼容 content 数组）。"""
    return [{
        'role': 'user',
        'content': [
            {'type': 'text', 'text': prompt},
            {'type': 'image_url', 'image_url': {'url': image_data_url}},
        ],
    }]


def build_video_messages(prompt: str, video_url: str) -> List[dict]:
    """视频多模态消息（video_url 结构，百炼兼容模式与主流多模态端点通用）。"""
    return [{
        'role': 'user',
        'content': [
            {'type': 'video_url', 'video_url': {'url': video_url}},
            {'type': 'text', 'text': prompt},
        ],
    }]


def call_openai_compatible(
    model,
    messages: List[dict],
    stream: bool = False,
    timeout: Optional[int] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> requests.Response:
    """全平台唯一出站函数：向启用模型端点发起 chat/completions 请求。"""
    url = build_chat_url(model.base_url)
    payload: Dict[str, Any] = {
        'model': model.model_name,
        'messages': messages,
        'stream': stream,
        'max_tokens': max_tokens if max_tokens is not None else model.max_tokens,
        'temperature': temperature if temperature is not None else model.temperature,
    }
    logger.info(
        f"LLM 调用: model={model.model_name} url={url} stream={stream} "
        f"max_tokens={payload['max_tokens']} temperature={payload['temperature']} timeout={timeout}s"
    )
    start = time.time()

    def do_request() -> requests.Response:
        return requests.post(
            url,
            headers=build_headers(model.api_key),
            json=payload,
            timeout=timeout,
            stream=stream,
        )

    response = do_request()
    # 厂商参数差异自动降级重试（顺序：temperature→1 为 KIMI K2 等强制要求；max_tokens→max_completion_tokens 为 OpenAI gpt-5.x 等）
    if response.status_code >= 400:
        try:
            err_msg = str(response.json().get('error', {}).get('message', ''))
        except Exception:
            err_msg = ''
        if 'temperature' in err_msg and 'only 1 is allowed' in err_msg:
            logger.warning(f"厂商要求 temperature 必须为 1，自动降级重试: {err_msg[:120]}")
            payload['temperature'] = 1
            response = do_request()
        elif 'max_tokens' in payload and 'max_tokens' in err_msg and 'max_completion_tokens' in err_msg:
            logger.warning(f"厂商不支持 max_tokens 参数，改用 max_completion_tokens 重试: {err_msg[:120]}")
            payload['max_completion_tokens'] = payload.pop('max_tokens')
            response = do_request()
    logger.info(f"LLM 响应: status={response.status_code} 耗时={time.time() - start:.2f}s")
    try:
        response.raise_for_status()
        return response
    except requests.exceptions.Timeout:
        logger.error(f"LLM 请求超时 (耗时: {time.time() - start:.2f}s, 超时设置: {timeout}s)")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"LLM 请求失败 (耗时: {time.time() - start:.2f}s): {str(e)}")
        if getattr(e, 'response', None) is not None:
            logger.error(f"响应状态码: {e.response.status_code}, 响应内容: {e.response.text[:500]}")
        raise


def extract_text(result: dict) -> str:
    """从非流式响应 JSON 提取回复文本。"""
    try:
        return result.get('choices', [{}])[0].get('message', {}).get('content', '')
    except (AttributeError, IndexError, TypeError):
        return ''


def process_stream_response(response) -> tuple:
    """聚合流式 SSE 响应，返回 (完整文本, usage)。"""
    full_response = ''
    usage_info = None
    for line in response.iter_lines():
        if not line:
            continue
        line_text = line.decode('utf-8')
        if not line_text.startswith('data: '):
            continue
        data_str = line_text[6:]
        if data_str == '[DONE]':
            break
        try:
            data = json.loads(data_str)
        except ValueError:
            continue
        choices = data.get('choices') or []
        if choices:
            delta = choices[0].get('delta', {}) or {}
            if 'content' in delta and delta['content']:
                full_response += delta['content']
        if 'usage' in data:
            usage_info = data['usage']
    return full_response, usage_info


def invoke_vision(model, base64_image: str, prompt: str, mode: Optional[str] = None) -> dict:
    """图片调用。mode=None 保持 analyze 契约（不增强提示词、无 mode 键）。"""
    text = enhance_prompt(prompt, mode, media='vision')
    messages = build_vision_messages(text, f"data:image/jpeg;base64,{base64_image}")

    max_tokens = model.max_tokens
    timeout = model.timeout
    if mode == 'deep-thinking':
        max_tokens = min(model.max_tokens * 2, 8000)
        timeout = model.timeout * 2

    response = call_openai_compatible(model, messages, stream=False, timeout=timeout, max_tokens=max_tokens)
    result = response.json()
    response_text = extract_text(result)
    logger.info(f"LLM 图片调用成功: 返回 {len(response_text)} 字符")
    if 'usage' in result:
        logger.info(f"Token 使用: {result.get('usage')}")

    data = {'response': response_text, 'raw_result': result}
    if mode:
        data['mode'] = mode
    return data


def invoke_video(model, video_base64: Optional[str], video_url: Optional[str], prompt: str, mode: str) -> dict:
    """视频调用（内部流式请求、聚合后返回，与重构前契约一致）。"""
    if not video_base64 and not video_url:
        raise ValueError('必须提供 video_base64 或 video_url 之一')

    if video_base64:
        video_ref = f"data:video/mp4;base64,{video_base64}"
    else:
        video_ref = video_url

    text = enhance_prompt(prompt, mode, media='video')
    messages = build_video_messages(text, video_ref)

    max_tokens = min(model.max_tokens * 2, 8000) if mode == 'deep-thinking' else model.max_tokens
    timeout = model.timeout * 3 if mode == 'deep-thinking' else model.timeout * 2

    response = call_openai_compatible(model, messages, stream=True, timeout=timeout, max_tokens=max_tokens)
    full_response, usage_info = process_stream_response(response)
    logger.info(f"LLM 视频调用成功: 返回 {len(full_response)} 字符")
    if usage_info:
        logger.info(f"Token 使用: {usage_info}")
    return {'response': full_response, 'usage': usage_info, 'mode': mode}


def invoke_chat(model, messages: List[dict], stream: bool = False, timeout: Optional[int] = None) -> dict:
    """纯文本/多模态对话调用，返回 {'response', 'usage', 'raw_result'}。"""
    response = call_openai_compatible(model, messages, stream=stream, timeout=timeout)
    if stream:
        full_response, usage_info = process_stream_response(response)
        return {'response': full_response, 'usage': usage_info, 'raw_result': None}
    result = response.json()
    return {'response': extract_text(result), 'usage': result.get('usage'), 'raw_result': result}


def test_model(model) -> dict:
    """连通性测试（统一实现，替代原 aliyun/generic/local 三套分支）。"""
    try:
        response = call_openai_compatible(
            model,
            [{'role': 'user', 'content': "你好，请回复'测试成功'"}],
            stream=False,
            timeout=model.timeout,
            max_tokens=100,
        )
        result = response.json()
        return {
            'success': True,
            'message': '连接测试成功',
            'response': extract_text(result),
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'message': '无法连接到模型服务，请检查 base_url 与服务是否可用',
            'error': 'Connection refused',
        }
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'message': f'连接测试超时（{model.timeout} 秒）',
            'error': 'Timeout',
        }
    except requests.exceptions.RequestException as e:
        detail = ''
        if getattr(e, 'response', None) is not None:
            detail = e.response.text[:500]
        return {
            'success': False,
            'message': f'连接测试失败: {getattr(e.response, "status_code", "") or str(e)}',
            'error': detail or str(e),
        }
    except Exception as e:
        return {'success': False, 'message': f'连接测试异常: {str(e)}', 'error': str(e)}
