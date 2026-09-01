"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025

大模型配置中心与能力接口。

模板化说明：
- 厂商差异收敛为 OpenAI 兼容协议模板（app/config/llm_templates.py），
  所有调用经 app/services/llm_gateway_client.py 统一出站，无厂商分支；
- vendor 仅作为模板标识存储，model_type 仅作展示字段，均不驱动调用逻辑；
- 全平台同一时刻仅启用 1 个模型（activate 互斥 + get_active_model 自愈收敛），
  所有能力接口强制使用当前启用模型。
"""
import base64
import json
import logging
import os
import tempfile
import uuid
from datetime import datetime
from typing import Optional

from flask import Blueprint, Response, jsonify, request

from db_models import LLMModel, db
from app.config.llm_templates import list_templates, resolve_template
from app.services.llm_gateway_client import (
    call_openai_compatible,
    invoke_chat,
    invoke_video,
    invoke_vision,
    test_model,
)
from app.services.llm_template_seed import is_placeholder_api_key
from app.services.minio_service import ModelService

llm_bp = Blueprint('llm', __name__)
logger = logging.getLogger(__name__)


def _model_dict(model: LLMModel) -> dict:
    """序列化模型配置，并派生 is_preset 标记（预置模板占位密钥 sk-placeholder-* → True，填入真实密钥后自动消失）。"""
    data = model.to_dict()
    data['is_preset'] = is_placeholder_api_key(model.api_key)
    return data


# ==================== 模板 ====================

@llm_bp.route('/templates', methods=['GET'])
def get_llm_templates():
    """大模型接入模板列表（前端下拉选择后自动填充 base_url 与常用模型）。"""
    return jsonify({
        'code': 0,
        'msg': 'success',
        'data': {
            'templates': list_templates(),
        }
    })


# ==================== 配置管理 ====================

@llm_bp.route('/list', methods=['GET'])
def get_llm_list():
    """获取大模型列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 10, type=int)
        name = request.args.get('name', '')
        service_type = request.args.get('service_type', '')
        vendor = request.args.get('vendor', '')
        model_type = request.args.get('model_type', '')
        is_active = request.args.get('is_active', '')

        query = LLMModel.query

        if name:
            query = query.filter(LLMModel.name.like(f'%{name}%'))
        if service_type:
            query = query.filter(LLMModel.service_type == service_type)
        if vendor:
            query = query.filter(LLMModel.vendor == vendor)
        if model_type:
            query = query.filter(LLMModel.model_type == model_type)
        # 如果指定了 is_active 参数，则过滤激活状态
        if is_active != '':
            is_active_bool = is_active.lower() in ('true', '1', 'yes')
            query = query.filter(LLMModel.is_active == is_active_bool)

        total = query.count()
        models = query.order_by(LLMModel.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'list': [_model_dict(model) for model in models],
                'total': total
            }
        })
    except Exception as e:
        logger.error(f"获取大模型列表失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/active-config', methods=['GET'])
def get_active_llm_config():
    """当前启用模型的完整配置（含完整 api_key），供 HARNESS LLM 网关等内部组件拉取。

    列表接口的 api_key 经 to_dict 脱敏，本接口是唯一返回完整密钥的通用出口；
    调用方（网关）只将密钥驻留内存，不落盘、不打日志。
    """
    try:
        model = LLMModel.query.filter_by(is_active=True).order_by(LLMModel.id).first()
        if not model:
            return jsonify({'code': 1, 'msg': '未启用大模型', 'data': None})
        data = model.to_dict()
        data['api_key'] = model.api_key  # 覆盖脱敏值，返回完整 key
        return jsonify({'code': 0, 'msg': 'success', 'data': data})
    except Exception as e:
        logger.error(f"获取启用大模型配置失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/detail/<int:model_id>', methods=['GET'])
def get_llm_detail(model_id):
    """获取大模型详情"""
    try:
        model = LLMModel.query.get(model_id)
        if not model:
            return jsonify({'code': 404, 'msg': '模型不存在'}), 404

        data = _model_dict(model)
        # 返回完整的api_key用于编辑
        data['api_key'] = model.api_key
        # 附加模板信息（vendor 为存量值时返回别名指向的模板）
        template = resolve_template(model.vendor)
        data['template'] = template.key if template else 'custom'
        data['template_label'] = template.label if template else '自定义 OpenAI 兼容'

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': data
        })
    except Exception as e:
        logger.error(f"获取大模型详情失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/create', methods=['POST'])
def create_llm():
    """创建大模型配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400

        # 检查名称是否已存在
        if LLMModel.query.filter_by(name=data.get('name')).first():
            return jsonify({'code': 400, 'msg': '模型名称已存在'}), 400

        service_type = data.get('service_type', 'online')
        # 验证：线上服务必须提供api_key，本地服务可选
        if service_type == 'online' and not data.get('api_key'):
            return jsonify({'code': 400, 'msg': '线上服务必须提供API密钥'}), 400
        # 验证：模型标识必填（厂商端点的模型 ID）
        if not data.get('model_name'):
            return jsonify({'code': 400, 'msg': 'model_name（模型标识）不能为空'}), 400

        base_url = data.get('base_url')
        if not base_url:
            # 未填端点时按模板预填
            template = resolve_template(data.get('vendor', ''))
            base_url = template.base_url if template else None
        if not base_url:
            return jsonify({'code': 400, 'msg': 'base_url 不能为空'}), 400

        model = LLMModel(
            name=data.get('name'),
            service_type=service_type,
            vendor=data.get('vendor', 'aliyun' if service_type == 'online' else 'local'),
            model_type=data.get('model_type', 'vision'),
            model_name=data.get('model_name'),
            base_url=base_url,
            api_key=data.get('api_key') if service_type == 'online' else data.get('api_key', ''),
            api_version=data.get('api_version'),
            temperature=data.get('temperature', 0.7),
            max_tokens=data.get('max_tokens', 2000),
            timeout=data.get('timeout', 60),
            description=data.get('description'),
            icon_url=data.get('icon_url'),
            is_active=False,
            status='inactive'
        )

        db.session.add(model)
        db.session.commit()

        return jsonify({
            'code': 0,
            'msg': '创建成功',
            'data': model.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建大模型配置失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/update/<int:model_id>', methods=['PUT'])
def update_llm(model_id):
    """更新大模型配置"""
    try:
        model = LLMModel.query.get(model_id)
        if not model:
            return jsonify({'code': 404, 'msg': '模型不存在'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400

        # 检查名称是否与其他模型冲突
        if 'name' in data and data['name'] != model.name:
            if LLMModel.query.filter_by(name=data['name']).first():
                return jsonify({'code': 400, 'msg': '模型名称已存在'}), 400

        # 更新字段
        if 'name' in data:
            model.name = data['name']
        if 'service_type' in data:
            service_type = data['service_type']
            model.service_type = service_type
            # 如果切换到线上服务且没有api_key，需要验证
            if service_type == 'online' and not model.api_key and 'api_key' not in data:
                return jsonify({'code': 400, 'msg': '线上服务必须提供API密钥'}), 400
        if 'vendor' in data:
            model.vendor = data['vendor']
        if 'model_type' in data:
            model.model_type = data['model_type']
        if 'model_name' in data:
            model.model_name = data['model_name']
        if 'base_url' in data:
            model.base_url = data['base_url']
        if 'api_key' in data:
            # 如果服务类型是线上，api_key不能为空
            if model.service_type == 'online' and not data['api_key']:
                return jsonify({'code': 400, 'msg': '线上服务必须提供API密钥'}), 400
            model.api_key = data['api_key']
        if 'api_version' in data:
            model.api_version = data.get('api_version')
        if 'temperature' in data:
            model.temperature = data['temperature']
        if 'max_tokens' in data:
            model.max_tokens = data['max_tokens']
        if 'timeout' in data:
            model.timeout = data['timeout']
        if 'description' in data:
            model.description = data.get('description')
        if 'icon_url' in data:
            model.icon_url = data.get('icon_url')

        model.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'code': 0,
            'msg': '更新成功',
            'data': model.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新大模型配置失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/delete/<int:model_id>', methods=['DELETE'])
def delete_llm(model_id):
    """删除大模型配置"""
    try:
        model = LLMModel.query.get(model_id)
        if not model:
            return jsonify({'code': 404, 'msg': '模型不存在'}), 404

        db.session.delete(model)
        db.session.commit()

        return jsonify({
            'code': 0,
            'msg': '删除成功'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除大模型配置失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/image_upload', methods=['POST'])
def upload_llm_image():
    """上传大模型图标图片"""
    if 'file' not in request.files:
        return jsonify({'code': 400, 'msg': '未找到文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'msg': '未选择文件'}), 400

    # 检查文件扩展名
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        return jsonify({'code': 400, 'msg': '只支持.jpg、.jpeg、.png、.gif、.webp格式的图片文件'}), 400

    # 初始化变量
    temp_path = None
    try:
        unique_filename = f"{uuid.uuid4().hex}{ext}"

        # 创建临时目录和文件
        temp_dir = 'temp_uploads'
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, unique_filename)
        file.save(temp_path)

        bucket_name = 'models'
        object_key = f"llm_images/{unique_filename}"

        # 上传到MinIO
        upload_success, upload_error = ModelService.upload_to_minio(bucket_name, object_key, temp_path)
        if upload_success:
            # 生成URL（直接拼接字符串）
            download_url = f"/api/v1/buckets/{bucket_name}/objects/download?prefix={object_key}"

            return jsonify({
                'code': 0,
                'msg': '图片上传成功',
                'data': {
                    'url': download_url,
                    'fileName': file.filename
                }
            })
        else:
            return jsonify({'code': 500, 'msg': '文件上传到MinIO失败'}), 500

    except Exception as e:
        logger.error(f"图片上传失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500

    finally:
        # 确保删除临时文件（无论上传成功与否）
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.info(f"临时文件已删除: {temp_path}")
            except OSError as e:
                logger.error(f"删除临时文件失败: {temp_path}, 错误: {str(e)}")


# ==================== 启用管控（全平台同时仅 1 个启用模型） ====================

@llm_bp.route('/activate/<int:model_id>', methods=['POST'])
def activate_llm(model_id):
    """启用大模型（互斥：先清空全部激活状态再启用目标；失败自动重试一次）"""
    last_error = None
    for attempt in (1, 2):
        try:
            model = LLMModel.query.get(model_id)
            if not model:
                return jsonify({'code': 404, 'msg': '模型不存在'}), 404

            # 预置模板数据拦截：占位密钥无法真实调用厂商，先引导填入真实密钥
            if is_placeholder_api_key(model.api_key):
                return jsonify({
                    'code': 400,
                    'msg': '这是预置模板数据，当前使用占位密钥（sk-placeholder-*），无法真实调用厂商接口。请先在编辑中填入真实 API 密钥后再启用',
                }), 400

            # 取消所有模型的激活状态（与启用目标同事务提交）
            LLMModel.query.update({LLMModel.is_active: False})

            model.is_active = True
            model.status = 'active'
            model.updated_at = datetime.utcnow()

            db.session.commit()
            logger.info(f"启用大模型: id={model.id}, name={model.name}（全平台唯一启用）")

            return jsonify({
                'code': 0,
                'msg': '激活成功',
                'data': model.to_dict()
            })
        except Exception as e:
            db.session.rollback()
            last_error = e
            logger.warning(f"激活大模型失败（第 {attempt} 次尝试）: {str(e)}")

    logger.error(f"激活大模型最终失败: {str(last_error)}")
    return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(last_error)}'}), 500


@llm_bp.route('/deactivate/<int:model_id>', methods=['POST'])
def deactivate_llm(model_id):
    """禁用大模型"""
    try:
        model = LLMModel.query.get(model_id)
        if not model:
            return jsonify({'code': 404, 'msg': '模型不存在'}), 404

        # 禁用当前模型
        model.is_active = False
        model.status = 'inactive'
        model.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'code': 0,
            'msg': '禁用成功',
            'data': model.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"禁用大模型失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


# ==================== 连通性测试 ====================

@llm_bp.route('/test/<int:model_id>', methods=['POST'])
def test_llm(model_id):
    """测试大模型连接（统一 OpenAI 兼容实现）"""
    try:
        model = LLMModel.query.get(model_id)
        if not model:
            return jsonify({'code': 404, 'msg': '模型不存在'}), 404

        # 预置模板数据拦截：占位密钥必然 401，直接引导填入真实密钥
        if is_placeholder_api_key(model.api_key):
            return jsonify({
                'code': 400,
                'msg': '这是预置模板数据，当前使用占位密钥（sk-placeholder-*）。请先在编辑中填入真实 API 密钥后再测试',
            }), 400

        test_result = test_model(model)

        # 更新测试结果（不改变状态，只记录测试时间和结果）
        model.last_test_time = datetime.utcnow()
        model.last_test_result = json.dumps(test_result, ensure_ascii=False)
        # 注意：测试结果不影响模型状态，状态只能通过启用/禁用操作改变

        db.session.commit()

        return jsonify({
            'code': 0,
            'msg': '测试完成',
            'data': test_result
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"测试大模型失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


# ==================== 工具函数 ====================

def get_active_model() -> Optional[LLMModel]:
    """获取当前启用的唯一大模型；发现多条激活记录时自愈收敛（按 id 最小者，行为确定）。"""
    actives = LLMModel.query.filter_by(is_active=True).order_by(LLMModel.id).all()
    if not actives:
        return None
    if len(actives) > 1:
        keep = actives[0]
        for extra in actives[1:]:
            extra.is_active = False
            extra.status = 'inactive'
        try:
            db.session.commit()
            logger.warning(
                f"检测到 {len(actives)} 条激活记录，已收敛到模型 id={keep.id}（{keep.name}）"
            )
        except Exception as e:
            db.session.rollback()
            logger.error(f"激活记录收敛失败: {str(e)}")
    return actives[0]


# ==================== 通用对话接口（平台统一能力入口） ====================

@llm_bp.route('/chat', methods=['POST'])
def chat():
    """通用大模型对话接口：使用当前启用模型，支持文本 + 可选图片/视频 URL。

    请求 JSON：{prompt, messages?: [{role, content}], context?: {...}, stream?: bool,
    files?: [{type: 'image'|'video', url}]}
    非流式返回 {code, msg, data:{response, usage, model}}；流式返回 SSE（data: {"content": ...} / data: [DONE]）
    """
    try:
        model = get_active_model()
        if not model:
            return jsonify({'code': 400, 'msg': '请先启用一个大模型'}), 400

        data = request.get_json(silent=True) or {}
        prompt = (data.get('prompt') or '').strip()

        # 平台助手可携带最近对话。只接受 user/assistant 文本，避免客户端注入 system
        # 指令；数量和单条长度均限制，防止浏览器长期会话无限膨胀。
        history = []
        for item in (data.get('messages') or [])[-20:]:
            role = item.get('role') if isinstance(item, dict) else None
            content = item.get('content') if isinstance(item, dict) else None
            if role in ('user', 'assistant') and isinstance(content, str) and content.strip():
                history.append({'role': role, 'content': content.strip()[:12000]})

        if not prompt and not history:
            return jsonify({'code': 400, 'msg': 'prompt 或 messages 不能为空'}), 400

        context = data.get('context') if isinstance(data.get('context'), dict) else {}
        page_title = str(context.get('pageTitle') or '')[:100]
        page_path = str(context.get('pagePath') or '')[:300]
        system_prompt = (
            '你是 EasyAIoT 平台智能助手。请使用简洁、准确、可操作的中文回答。'
            '优先结合用户当前所在页面给出操作路径；不知道实时平台数据时要明确说明，'
            '不得编造设备状态、告警数量或执行结果。'
        )
        if page_title or page_path:
            system_prompt += f' 用户当前页面：{page_title or "未知"}（{page_path or "未知路径"}）。'

        content_parts = []
        for f in (data.get('files') or []):
            ftype = (f.get('type') or 'image').lower()
            furl = f.get('url') or ''
            if not furl:
                continue
            if ftype == 'image':
                content_parts.append({'type': 'image_url', 'image_url': {'url': furl}})
            elif ftype == 'video':
                content_parts.append({'type': 'video_url', 'video_url': {'url': furl}})
        messages = [{'role': 'system', 'content': system_prompt}] + history
        # 兼容原有只传 prompt 的调用；新助手传 history 时，prompt 是本轮消息且不会重复。
        if prompt:
            if content_parts:
                messages.append({'role': 'user', 'content': [{'type': 'text', 'text': prompt}] + content_parts})
            else:
                messages.append({'role': 'user', 'content': prompt})

        logger.info(f"LLM 对话请求: 模型 id={model.id}（{model.model_name}）, stream={bool(data.get('stream'))}, 附件数={len(content_parts)}")

        if data.get('stream'):
            return Response(
                _sse_chat(model, messages),
                mimetype='text/event-stream',
                headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
            )

        result = invoke_chat(model, messages, stream=False, timeout=model.timeout)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'response': result['response'],
                'usage': result['usage'],
                'model': model.model_name,
            }
        })
    except Exception as e:
        logger.error(f"LLM 对话请求失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


def _sse_chat(model, messages):
    """流式对话生成器：厂商 SSE → 平台 SSE（data: {"content": ...} / [DONE]）。"""
    def generate():
        try:
            response = call_openai_compatible(model, messages, stream=True, timeout=model.timeout)
            for line in response.iter_lines():
                if not line:
                    continue
                text = line.decode('utf-8')
                if not text.startswith('data: '):
                    continue
                payload = text[6:]
                if payload == '[DONE]':
                    break
                try:
                    chunk = json.loads(payload)
                except ValueError:
                    continue
                choices = chunk.get('choices') or []
                delta = (choices[0].get('delta') or {}) if choices else {}
                piece = delta.get('content')
                if piece:
                    yield f"data: {json.dumps({'content': piece}, ensure_ascii=False)}\n\n"
            yield 'data: [DONE]\n\n'
        except Exception as e:
            logger.error(f"LLM 流式对话失败: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
    return generate()


# ==================== 业务能力接口（URL 与契约保持不变，内部统一走模板引擎） ====================

@llm_bp.route('/vision/analyze', methods=['POST'])
def vision_analyze():
    """使用启用的大模型进行视觉分析"""
    try:
        model = get_active_model()
        if not model:
            return jsonify({'code': 400, 'msg': '请先启用一个大模型'}), 400

        if 'image' not in request.files:
            return jsonify({'code': 400, 'msg': '未找到图像文件'}), 400

        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'code': 400, 'msg': '未选择图像文件'}), 400

        prompt = request.form.get('prompt', '请分析这张图片，描述其中的内容。')
        logger.info(f"视觉分析请求: 模型 id={model.id}（{model.model_name}）, 图片 {image_file.filename}, 提示词: {prompt}")

        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_image:
            image_file.save(temp_image.name)
            image_path = temp_image.name

        try:
            with open(image_path, 'rb') as f:
                base64_image = base64.b64encode(f.read()).decode('utf-8')

            result = invoke_vision(model, base64_image, prompt)

            logger.info(f"视觉分析成功: 返回 {len(result.get('response', ''))} 字符")
            return jsonify({'code': 0, 'msg': '分析成功', 'data': result})
        finally:
            if os.path.exists(image_path):
                os.unlink(image_path)

    except Exception as e:
        logger.error(f"视觉分析请求失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/vision/inference', methods=['POST'])
def vision_inference():
    """大模型视觉推理接口"""
    return _vision_with_mode('inference', '视觉推理', '视觉推理成功')


@llm_bp.route('/vision/understanding', methods=['POST'])
def vision_understanding():
    """大模型视觉理解接口"""
    return _vision_with_mode('understanding', '视觉理解', '视觉理解成功')


@llm_bp.route('/vision/deep-thinking', methods=['POST'])
def vision_deep_thinking():
    """大模型深度思考接口"""
    return _vision_with_mode('deep-thinking', '深度思考', '深度思考成功')


def _vision_with_mode(mode: str, label: str, success_msg: str):
    """图片能力接口公共实现（推理/理解/深度思考共用，仅模式不同）。"""
    try:
        model = get_active_model()
        if not model:
            return jsonify({'code': 400, 'msg': '请先启用一个大模型'}), 400

        if 'image' not in request.files:
            return jsonify({'code': 400, 'msg': '未找到图像文件'}), 400

        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'code': 400, 'msg': '未选择图像文件'}), 400

        prompt = request.form.get('prompt', '')
        logger.info(f"{label}请求: 模型 id={model.id}（{model.model_name}）, 模式: {mode}, 图片 {image_file.filename}, 提示词: {prompt}")

        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_image:
            image_file.save(temp_image.name)
            image_path = temp_image.name

        try:
            with open(image_path, 'rb') as f:
                base64_image = base64.b64encode(f.read()).decode('utf-8')

            result = invoke_vision(model, base64_image, prompt, mode=mode)

            logger.info(f"{label}成功: 返回 {len(result.get('response', ''))} 字符")
            return jsonify({'code': 0, 'msg': success_msg, 'data': result})
        finally:
            if os.path.exists(image_path):
                os.unlink(image_path)

    except Exception as e:
        logger.error(f"{label}请求失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/video/inference', methods=['POST'])
def video_inference():
    """大模型视频推理接口"""
    return _video_with_mode('inference', '视频推理', '视频推理成功',
                            default_prompt='请分析这个视频中的对象、场景和可能的行为。')


@llm_bp.route('/video/understanding', methods=['POST'])
def video_understanding():
    """大模型视频理解接口"""
    return _video_with_mode('understanding', '视频理解', '视频理解成功',
                            default_prompt='请描述这个视频的内容。')


def _video_with_mode(mode: str, label: str, success_msg: str, default_prompt: str):
    """视频能力接口公共实现（文件上传或 URL 二选一）。"""
    try:
        model = get_active_model()
        if not model:
            return jsonify({'code': 400, 'msg': '请先启用一个大模型'}), 400

        logger.info(f"{label}请求: 模型 id={model.id}（{model.model_name}）, 模式: {mode}")

        video_base64 = None
        video_url = None

        if 'video' in request.files:
            video_file = request.files['video']
            if video_file.filename:
                logger.info(f"视频文件名: {video_file.filename}")
                video_file.seek(0)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
                    video_file.save(temp_video.name)
                    video_path = temp_video.name
                    try:
                        with open(video_path, 'rb') as f:
                            video_base64 = base64.b64encode(f.read()).decode('utf-8')
                        logger.info(f"视频Base64编码长度: {len(video_base64)} 字符")
                    finally:
                        if os.path.exists(video_path):
                            os.unlink(video_path)

        if not video_base64:
            video_url = request.form.get('video_url') or request.json.get('video_url') if request.is_json else None

        if not video_base64 and not video_url:
            return jsonify({'code': 400, 'msg': '请提供视频文件或视频URL'}), 400

        prompt = request.form.get('prompt') or (request.json.get('prompt') if request.is_json else None) or default_prompt
        logger.info(f"提示词: {prompt}")

        result = invoke_video(model, video_base64, video_url, prompt, mode)

        logger.info(f"{label}成功: 返回 {len(result.get('response', ''))} 字符")
        return jsonify({'code': 0, 'msg': success_msg, 'data': result})

    except Exception as e:
        logger.error(f"{label}请求失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500
