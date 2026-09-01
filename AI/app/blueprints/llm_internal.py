"""
大模型（LLM）告警事件研判内部接口（供 iot-sink 独立队列消费方调用）。

- POST /model/llm/internal/judge
- 流程：取智能体（rag_expert）→ 组装 system_prompt（含 RAG 知识检索）→
  图片：下载 → base64 → invoke_vision；视频：ffmpeg 窗口切片 → base64 → invoke_video
  → JSON 结构化输出解析（失败一次 invoke_chat 纠错）→ 返回结论。
- 鉴权：配置 AI_INTERNAL_TOKEN 时校验 X-Internal-Token 头；未配置仅限内网部署。
"""
from __future__ import annotations

import base64
import json
import logging
import os
import re
import time
import mimetypes
from typing import Any, Dict, Optional

import requests
from flask import Blueprint, current_app, jsonify, request

from db_models import LLMModel, RagExpert, RagKnowledgeSegment, RagKnowledgeSet, db
from app.services.llm_gateway_client import invoke_chat, invoke_vision, invoke_video
from app.services.rag_service import retrieve_segments
from app.services.llm_video_clip_service import make_video_clip

llm_internal_bp = Blueprint('llm_internal', __name__)
logger = logging.getLogger(__name__)

DEFAULT_IMAGE_MAX_BYTES = 15 * 1024 * 1024  # 图片 base64 前上限 15MB
MAX_IMAGE_BYTES = int(os.getenv('LLM_JUDGE_MAX_IMAGE_BYTES', DEFAULT_IMAGE_MAX_BYTES))
RAG_TOP_K = 4
OUTPUT_JSON_RE = re.compile(r'\{.*\}', re.DOTALL)

DEFAULT_SYSTEM_PROMPT = (
    '你是告警事件研判专家。请基于提供的检测信息与{media_desc}，判断算法告警事件是否真实成立。'
    '严格只输出一个 JSON 对象，不要输出任何其他文字。'
)
DEFAULT_USER_PROMPT = (
    '检测对象：{object_name}；事件类型：{event}；检测详情：{detections_json}。\n'
    '请判断该事件是否真实成立（排除误报：光照变化、遮挡、雨雾、重影、动物等干扰），'
    '并输出 JSON：{{"confirm": true或false, "confidence": 0到1, '
    '"reason": "简短理由", "attributes": {{可选补充字段}}}}'
)

INTERNAL_TOKEN = os.getenv('AI_INTERNAL_TOKEN', '')


def ok(data=None, msg='success'):
    return jsonify({'code': 0, 'msg': msg, 'data': data})


def _check_internal_auth() -> Optional[Dict[str, Any]]:
    """内部鉴权：配置了 token 才校验，未配置仅提示（内网部署）。"""
    if not INTERNAL_TOKEN:
        return None
    provided = request.headers.get('X-Internal-Token', '')
    if provided != INTERNAL_TOKEN:
        return {'code': 403, 'msg': 'X-Internal-Token 校验失败'}, 403
    return None


def _resolve_model(model_id: Optional[int]) -> LLMModel:
    if model_id:
        model = LLMModel.query.get(model_id)
        if model is None:
            raise ValueError(f'大模型不存在: model_id={model_id}')
        return model
    active = LLMModel.query.filter_by(is_active=True).first()
    if active is None:
        raise ValueError('未启用任何大模型，请先在模型配置中启用')
    return active


def _resolve_agent(agent_id: int) -> RagExpert:
    agent = RagExpert.query.get(agent_id)
    if agent is None:
        raise ValueError(f'智能体不存在: agent_id={agent_id}')
    if not agent.is_enabled:
        raise ValueError(f'智能体已停用: {agent.name}')
    return agent


def _build_rag_context(agent: RagExpert, query: str) -> str:
    """按智能体关联知识集检索 Top-K 片段，拼成参考上下文。"""
    segment_ids = []
    for knowledge_set in agent.knowledge_sets:
        for segment in knowledge_set.segments:
            if segment.is_enabled:
                segment_ids.append(segment.id)
    if not segment_ids:
        return ''
    try:
        hits = retrieve_segments(segment_ids, query, limit=RAG_TOP_K)
    except Exception as exc:
        logger.warning('RAG 检索失败（降级为无知识上下文）: %s', exc)
        return ''
    if not hits:
        return ''
    blocks = []
    for hit in hits:
        blocks.append(f'- [{hit["document_name"]}] {hit["content"]}')
    return '参考知识（来自智能体知识库，仅作判断依据，不得照抄输出）：\n' + '\n'.join(blocks)


def _render_prompt(agent: RagExpert, context: Dict[str, Any],
                   prompt_override: Optional[str]) -> str:
    detections = context.get('detections') or []
    detections_json = json.dumps(detections, ensure_ascii=False)[:2000]
    template = {
        'object_name': context.get('object') or '未知目标',
        'event': context.get('event') or 'detection',
        'detections_json': detections_json,
    }
    user_prompt = prompt_override or DEFAULT_USER_PROMPT
    try:
        rendered = user_prompt.format(**template)
    except Exception:
        rendered = user_prompt
    return rendered


def _parse_json_output(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    match = OUTPUT_JSON_RE.search(text)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def _extract_judgement(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """归一化模型输出：confirm/confidence/reason/attributes。"""
    confirm = parsed.get('confirm', parsed.get('is_valid', None))
    if isinstance(confirm, str):
        confirm = confirm.strip().lower() in ('true', 'yes', '是', '成立', '1')
    confidence = parsed.get('confidence', parsed.get('score', None))
    try:
        confidence = float(confidence) if confidence is not None else None
        if confidence is not None:
            confidence = max(0.0, min(1.0, confidence))
    except (TypeError, ValueError):
        confidence = None
    reason = parsed.get('reason', parsed.get('explanation', '')) or ''
    attributes = parsed.get('attributes') or {}
    if not isinstance(attributes, dict):
        attributes = {'extra': attributes}
    return {
        'confirm': bool(confirm) if confirm is not None else None,
        'confidence': confidence,
        'reason': str(reason),
        'attributes': attributes,
    }


def _repair_json(text: str, model: LLMModel) -> Optional[Dict[str, Any]]:
    """JSON 解析失败时用一次纯文本对话让模型重新输出 JSON。"""
    try:
        result = invoke_chat(model, [
            {'role': 'user', 'content':
                f'以下是模型对图片/视频的输出，请只提取其中的判断结论并严格输出 JSON '
                f'{{"confirm": true或false, "confidence": 0到1, "reason": "简短理由"}}，不要解释。\n\n{text[:3000]}'},
        ])
        return _parse_json_output(result.get('response', ''))
    except Exception as exc:
        logger.warning('JSON 纠错失败: %s', exc)
        return None


def _fetch_image_base64(image_url: str) -> tuple[str, str]:
    """下载图片转 base64；优先走 MinIO 客户端（内部域名），失败回退 HTTP。"""
    from app.services.minio_service import ModelService, parse_minio_download_url

    bucket, object_key = parse_minio_download_url(image_url)
    if bucket and object_key:
        import tempfile
        fd, path = tempfile.mkstemp(suffix='.jpg')
        os.close(fd)
        try:
            success, error = ModelService.download_from_minio(bucket, object_key, path)
            if success:
                with open(path, 'rb') as f:
                    data = f.read()
                if len(data) > MAX_IMAGE_BYTES:
                    raise ValueError(f'图片超过 {MAX_IMAGE_BYTES} 字节限制')
                mime = mimetypes.guess_type(object_key)[0] or 'image/jpeg'
                return base64.b64encode(data).decode('utf-8'), mime
            logger.warning('MinIO 下载失败，回退 HTTP: %s', error)
        except Exception as exc:
            logger.warning('MinIO 下载异常，回退 HTTP: %s', exc)
        finally:
            if os.path.exists(path):
                os.unlink(path)
    resp = requests.get(image_url, timeout=30)
    resp.raise_for_status()
    if len(resp.content) > MAX_IMAGE_BYTES:
        raise ValueError(f'图片超过 {MAX_IMAGE_BYTES} 字节限制')
    mime = (resp.headers.get('Content-Type') or '').split(';', 1)[0]
    if not mime.startswith('image/'):
        mime = mimetypes.guess_type(image_url.split('?', 1)[0])[0] or 'image/jpeg'
    return base64.b64encode(resp.content).decode('utf-8'), mime


def _build_system_prompt(agent: RagExpert, media_desc: str, rag_context: str) -> str:
    system = agent.system_prompt or DEFAULT_SYSTEM_PROMPT
    system = system.replace('{media_desc}', media_desc)
    parts = [system]
    if rag_context:
        parts.append(rag_context)
    parts.append('输出要求：仅输出一个 JSON 对象：{"confirm": true或false, "confidence": 0到1, "reason": "简短理由", "attributes": {...}}')
    return '\n\n'.join(parts)


@llm_internal_bp.route('/judge', methods=['POST'])
def judge():
    """告警事件大模型研判（iot-sink 内部调用）。"""
    started = time.time()
    auth_error = _check_internal_auth()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]
    try:
        payload = request.get_json(silent=True) or {}
        media = payload.get('media') or {}
        agent_id = payload.get('agent_id')
        if not agent_id:
            return jsonify({'code': 400, 'msg': 'agent_id 必填'}), 400
        agent = _resolve_agent(int(agent_id))
        model = _resolve_model(payload.get('model_id'))

        media_type = str(payload.get('media_type') or media.get('media_type') or 'image').lower()
        if media_type not in ('image', 'video'):
            return jsonify({'code': 400, 'msg': f'media_type 必须为 image|video'}), 400

        context = payload.get('context') or {}
        prompt_override = payload.get('prompt_override')
        user_prompt = _render_prompt(agent, context, prompt_override)
        rag_context = _build_rag_context(agent, user_prompt[:500])

        media_used = media_type
        image_base64 = None
        video_base64 = None

        if media_type == 'image':
            image_url = media.get('image_url') or media.get('url')
            if not image_url:
                return jsonify({'code': 400, 'msg': 'image 模式缺少 media.image_url'}), 400
            image_base64, image_mime = _fetch_image_base64(image_url)
            system_prompt = _build_system_prompt(agent, '图片', rag_context)
            result = invoke_vision(
                model, image_base64, user_prompt, mode='inference',
                system_prompt=system_prompt, mime_type=image_mime,
            )
            response_text = result.get('response', '')
        else:
            video_url = media.get('record_path') or media.get('url')
            if not video_url:
                return jsonify({'code': 400, 'msg': 'video 模式缺少 media.record_path'}), 400
            pre = int(media.get('pre_seconds', 5) or 5)
            post = int(media.get('post_seconds', 10) or 10)
            max_sec = int(media.get('max_seconds', 30) or 30)
            if pre + post <= 0:
                return jsonify({'code': 400, 'msg': '视频窗口为空（pre_seconds+post_seconds 需大于 0）'}), 400
            clip_path, clip_error = make_video_clip(video_url, pre, post, max_sec)
            if clip_path is None:
                return jsonify({'code': 500, 'msg': f'视频切片失败: {clip_error}'}), 500
            try:
                with open(clip_path, 'rb') as f:
                    video_base64 = base64.b64encode(f.read()).decode('utf-8')
            finally:
                if os.path.exists(clip_path):
                    os.unlink(clip_path)
            system_prompt = _build_system_prompt(agent, '视频', rag_context)
            result = invoke_video(
                model, video_base64, None, user_prompt, mode='inference',
                system_prompt=system_prompt,
            )
            response_text = result.get('response', '')

        parsed = _parse_json_output(response_text)
        if parsed is None:
            logger.info('研判输出非 JSON，尝试纠错: %s', response_text[:200])
            parsed = _repair_json(response_text, model)
        judgement = _extract_judgement(parsed) if parsed else {
            'confirm': None, 'confidence': None,
            'reason': '模型输出无法解析为 JSON', 'attributes': {},
        }

        data = {
            'confirm': judgement['confirm'],
            'confidence': judgement['confidence'],
            'reason': judgement['reason'],
            'structured': judgement['attributes'],
            'raw_response': response_text,
            'usage': result.get('usage'),
            'mode': result.get('mode', 'inference'),
            'media_used': media_used,
            'duration_ms': int((time.time() - started) * 1000),
        }
        logger.info('LLM 研判完成 agent=%s model=%s media=%s confirm=%s duration=%sms',
                    agent.id, model.id, media_used, judgement['confirm'], data['duration_ms'])
        return ok(data)
    except ValueError as exc:
        return jsonify({'code': 400, 'msg': str(exc)}), 400
    except Exception as exc:
        logger.error('LLM 研判失败: %s', exc, exc_info=True)
        return jsonify({'code': 500, 'msg': f'研判失败: {exc}'}), 500
