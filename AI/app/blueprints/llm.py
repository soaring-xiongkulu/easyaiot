"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import base64
import json
import logging
import tempfile
import os
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from flask import Blueprint, request, jsonify
import requests

from db_models import LLMModel, db

llm_bp = Blueprint('llm', __name__)
logger = logging.getLogger(__name__)

# 阿里云百炼 API 端点（兼容模式）
DASHSCOPE_API_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DASHSCOPE_API_CHAT_URL = f"{DASHSCOPE_API_BASE_URL}/chat/completions"


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
        
        query = LLMModel.query
        
        if name:
            query = query.filter(LLMModel.name.like(f'%{name}%'))
        if service_type:
            query = query.filter(LLMModel.service_type == service_type)
        if vendor:
            query = query.filter(LLMModel.vendor == vendor)
        if model_type:
            query = query.filter(LLMModel.model_type == model_type)
        
        total = query.count()
        models = query.order_by(LLMModel.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'list': [model.to_dict() for model in models],
                'total': total
            }
        })
    except Exception as e:
        logger.error(f"获取大模型列表失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/detail/<int:model_id>', methods=['GET'])
def get_llm_detail(model_id):
    """获取大模型详情"""
    try:
        model = LLMModel.query.get(model_id)
        if not model:
            return jsonify({'code': 404, 'msg': '模型不存在'}), 404
        
        data = model.to_dict()
        # 返回完整的api_key用于编辑
        data['api_key'] = model.api_key
        
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
        
        model = LLMModel(
            name=data.get('name'),
            service_type=service_type,
            vendor=data.get('vendor', 'aliyun' if service_type == 'online' else 'local'),
            model_type=data.get('model_type', 'vision'),
            model_name=data.get('model_name'),
            base_url=data.get('base_url'),
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


@llm_bp.route('/activate/<int:model_id>', methods=['POST'])
def activate_llm(model_id):
    """激活大模型（同时取消其他模型的激活状态）"""
    try:
        model = LLMModel.query.get(model_id)
        if not model:
            return jsonify({'code': 404, 'msg': '模型不存在'}), 404
        
        # 取消所有模型的激活状态
        LLMModel.query.update({LLMModel.is_active: False})
        
        # 激活当前模型
        model.is_active = True
        model.status = 'active'
        model.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'msg': '激活成功',
            'data': model.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"激活大模型失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/test/<int:model_id>', methods=['POST'])
def test_llm(model_id):
    """测试大模型连接"""
    try:
        model = LLMModel.query.get(model_id)
        if not model:
            return jsonify({'code': 404, 'msg': '模型不存在'}), 404
        
        # 根据服务类型和供应商构建测试请求
        if model.service_type == 'local':
            # 本地服务测试
            test_result = test_local_llm(model)
        elif model.vendor == 'aliyun':
            # 阿里云QWENVL3测试
            test_result = test_aliyun_qwenvl3(model)
        else:
            # 其他线上供应商的测试逻辑
            test_result = test_generic_llm(model)
        
        # 更新测试结果
        model.last_test_time = datetime.utcnow()
        model.last_test_result = json.dumps(test_result, ensure_ascii=False)
        if test_result.get('success'):
            model.status = 'active'
        else:
            model.status = 'error'
        
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
    """获取激活的大模型"""
    return LLMModel.query.filter_by(is_active=True).first()


def build_api_url(base_url: str) -> str:
    """构建API端点URL"""
    if base_url.endswith('/'):
        return f"{base_url}v1/chat/completions"
    else:
        return f"{base_url}/v1/chat/completions"


def build_headers(model: LLMModel) -> Dict[str, str]:
    """构建请求头"""
    headers = {'Content-Type': 'application/json'}
    if model.api_key:
        headers['Authorization'] = f'Bearer {model.api_key}'
    return headers


def enhance_prompt_by_mode(prompt: str, mode: str) -> str:
    """根据模式增强提示词"""
    mode_prompts = {
        'inference': f"作为视觉推理专家，请分析这个视频：{prompt}",
        'understanding': prompt,  # 理解模式使用原始提示词
        'deep-thinking': f"作为深度思考专家，请对这段视频进行多角度深度分析：{prompt}"
    }
    return mode_prompts.get(mode, prompt)


def process_stream_response(response) -> Tuple[str, Optional[Dict]]:
    """处理流式响应"""
    full_response = ""
    usage_info = None
    
    for line in response.iter_lines():
        if not line:
            continue
        
        line_text = line.decode('utf-8')
        
        # 处理 SSE 格式
        if line_text.startswith('data: '):
            data_str = line_text[6:]  # 移除 'data: ' 前缀
            
            if data_str == '[DONE]':
                break
            
            try:
                data = json.loads(data_str)
                
                # 提取文本内容
                if 'choices' in data and len(data['choices']) > 0:
                    delta = data['choices'][0].get('delta', {})
                    if 'content' in delta:
                        content_text = delta['content']
                        full_response += content_text
                
                # 提取使用情况
                if 'usage' in data:
                    usage_info = data['usage']
            
            except json.JSONDecodeError:
                continue
    
    return full_response, usage_info


# ==================== 测试函数 ====================

def test_aliyun_qwenvl3(model: LLMModel) -> dict:
    """测试阿里云QWENVL3模型"""
    try:
        headers = build_headers(model)
        api_url = build_api_url(model.base_url)
        
        payload = {
            "model": model.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": "你好，请回复'测试成功'"
                }
            ],
            "max_tokens": 100,
            "temperature": model.temperature
        }
        
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=model.timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'message': '连接测试成功',
                'response': result.get('choices', [{}])[0].get('message', {}).get('content', '')
            }
        else:
            return {
                'success': False,
                'message': f'连接测试失败: {response.status_code}',
                'error': response.text
            }
    except Exception as e:
        return {
            'success': False,
            'message': f'连接测试异常: {str(e)}',
            'error': str(e)
        }


def test_generic_llm(model: LLMModel) -> dict:
    """测试通用LLM模型"""
    try:
        headers = build_headers(model)
        api_url = build_api_url(model.base_url)
        
        payload = {
            "model": model.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": "Hello, please reply 'Test successful'"
                }
            ],
            "max_tokens": 100
        }
        
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=model.timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'message': '连接测试成功',
                'response': result.get('choices', [{}])[0].get('message', {}).get('content', '')
            }
        else:
            return {
                'success': False,
                'message': f'连接测试失败: {response.status_code}',
                'error': response.text
            }
    except Exception as e:
        return {
            'success': False,
            'message': f'连接测试异常: {str(e)}',
            'error': str(e)
        }


def test_local_llm(model: LLMModel) -> dict:
    """测试本地LLM模型服务"""
    try:
        headers = build_headers(model)
        api_url = build_api_url(model.base_url)
        
        payload = {
            "model": model.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": "你好，请回复'测试成功'"
                }
            ],
            "max_tokens": 100,
            "temperature": model.temperature
        }
        
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=model.timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'message': '本地服务连接测试成功',
                'response': result.get('choices', [{}])[0].get('message', {}).get('content', '')
            }
        else:
            return {
                'success': False,
                'message': f'本地服务连接测试失败: {response.status_code}',
                'error': response.text
            }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'message': '无法连接到本地服务，请检查服务是否启动',
            'error': 'Connection refused'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'本地服务连接测试异常: {str(e)}',
            'error': str(e)
        }


@llm_bp.route('/vision/analyze', methods=['POST'])
def vision_analyze():
    """使用激活的大模型进行视觉分析"""
    try:
        model = get_active_model()
        if not model:
            return jsonify({'code': 400, 'msg': '请先激活一个大模型'}), 400
        
        # 检查是否有文件上传
        if 'image' not in request.files:
            return jsonify({'code': 400, 'msg': '未找到图像文件'}), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'code': 400, 'msg': '未选择图像文件'}), 400
        
        # 获取提示词
        prompt = request.form.get('prompt', '请分析这张图片，描述其中的内容。')
        
        # 保存上传的图像文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_image:
            image_file.save(temp_image.name)
            image_path = temp_image.name
        
        try:
            # 编码图像为base64
            with open(image_path, 'rb') as f:
                image_data = f.read()
                base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # 构建请求
            if model.service_type == 'local':
                result = call_local_vision_llm(model, base64_image, prompt)
            elif model.vendor == 'aliyun':
                result = call_aliyun_qwenvl3(model, base64_image, prompt)
            else:
                result = call_generic_vision_llm(model, base64_image, prompt)
            
            return jsonify({
                'code': 0,
                'msg': '分析成功',
                'data': result
            })
        finally:
            # 清理临时文件
            if os.path.exists(image_path):
                os.unlink(image_path)
    
    except Exception as e:
        logger.error(f"视觉分析失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


# ==================== 视觉模型调用函数 ====================

def call_aliyun_qwenvl3(model: LLMModel, base64_image: str, prompt: str) -> dict:
    """调用阿里云QWENVL3模型（图片）"""
    headers = build_headers(model)
    api_url = build_api_url(model.base_url)
    
    payload = {
        "model": model.model_name,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": model.max_tokens,
        "temperature": model.temperature
    }
    
    response = requests.post(
        api_url,
        headers=headers,
        json=payload,
        timeout=model.timeout
    )
    
    response.raise_for_status()
    result = response.json()
    
    return {
        'response': result.get('choices', [{}])[0].get('message', {}).get('content', ''),
        'raw_result': result
    }


def call_generic_vision_llm(model: LLMModel, base64_image: str, prompt: str) -> dict:
    """调用通用视觉大模型（图片）"""
    headers = build_headers(model)
    api_url = build_api_url(model.base_url)
    
    payload = {
        "model": model.model_name,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": model.max_tokens,
        "temperature": model.temperature
    }
    
    response = requests.post(
        api_url,
        headers=headers,
        json=payload,
        timeout=model.timeout
    )
    
    response.raise_for_status()
    result = response.json()
    
    return {
        'response': result.get('choices', [{}])[0].get('message', {}).get('content', ''),
        'raw_result': result
    }


def call_local_vision_llm(model: LLMModel, base64_image: str, prompt: str) -> dict:
    """调用本地视觉大模型服务（图片）"""
    headers = build_headers(model)
    api_url = build_api_url(model.base_url)
    
    payload = {
        "model": model.model_name,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": model.max_tokens,
        "temperature": model.temperature
    }
    
    response = requests.post(
        api_url,
        headers=headers,
        json=payload,
        timeout=model.timeout
    )
    
    response.raise_for_status()
    result = response.json()
    
    return {
        'response': result.get('choices', [{}])[0].get('message', {}).get('content', ''),
        'raw_result': result
    }


# ==================== 视频模型调用函数 ====================

def call_aliyun_video_with_mode(
    model: LLMModel, 
    video_base64: Optional[str] = None, 
    video_url: Optional[str] = None, 
    prompt: str = '', 
    mode: str = 'inference',
    stream: bool = True
) -> dict:
    """调用阿里云视频大模型（支持不同模式，视频）"""
    headers = build_headers(model)
    api_url = build_api_url(model.base_url)
    
    # 构建消息内容
    content = []
    
    # 添加视频内容
    if video_base64:
        video_content = {
            "type": "video_url",
            "video_url": {
                "url": f"data:video/mp4;base64,{video_base64}"
            }
        }
        content.append(video_content)
    elif video_url:
        video_content = {
            "type": "video_url",
            "video_url": {
                "url": video_url
            }
        }
        content.append(video_content)
    else:
        raise ValueError("必须提供 video_base64 或 video_url 之一")
    
    # 根据模式调整提示词
    if mode == 'inference':
        enhanced_prompt = f"作为视觉推理专家，请分析这个视频：{prompt}"
    elif mode == 'understanding':
        enhanced_prompt = prompt  # 理解模式使用原始提示词
    else:
        enhanced_prompt = enhance_prompt_by_mode(prompt, mode)
    
    # 添加文本提示
    content.append({
        "type": "text",
        "text": enhanced_prompt
    })
    
    # 构建请求体
    payload = {
        "model": model.model_name,
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ],
        "stream": stream,
        "max_tokens": model.max_tokens,
        "temperature": model.temperature
    }
    
    # 深度思考模式可能需要更多的token
    if mode == 'deep-thinking':
        payload["max_tokens"] = min(model.max_tokens * 2, 8000)
    
    timeout = model.timeout * 3 if mode == 'deep-thinking' else model.timeout * 2
    
    response = requests.post(
        api_url,
        headers=headers,
        json=payload,
        timeout=timeout,
        stream=stream
    )
    
    response.raise_for_status()
    
    if stream:
        # 处理流式响应
        full_response, usage_info = process_stream_response(response)
        return {
            'response': full_response,
            'usage': usage_info,
            'mode': mode
        }
    else:
        # 处理非流式响应
        result = response.json()
        return {
            'response': result.get('choices', [{}])[0].get('message', {}).get('content', ''),
            'raw_result': result,
            'mode': mode
        }


def call_generic_video_llm(
    model: LLMModel, 
    video_base64: Optional[str] = None, 
    video_url: Optional[str] = None, 
    prompt: str = '', 
    mode: str = 'inference',
    stream: bool = True
) -> dict:
    """调用通用视频大模型（支持不同模式，视频）"""
    headers = build_headers(model)
    api_url = build_api_url(model.base_url)
    
    # 构建消息内容
    content = []
    
    # 添加视频内容
    if video_base64:
        video_content = {
            "type": "video_url",
            "video_url": {
                "url": f"data:video/mp4;base64,{video_base64}"
            }
        }
        content.append(video_content)
    elif video_url:
        video_content = {
            "type": "video_url",
            "video_url": {
                "url": video_url
            }
        }
        content.append(video_content)
    else:
        raise ValueError("必须提供 video_base64 或 video_url 之一")
    
    # 根据模式调整提示词
    enhanced_prompt = enhance_prompt_by_mode(prompt, mode)
    if mode == 'understanding':
        enhanced_prompt = prompt  # 理解模式使用原始提示词
    
    # 添加文本提示
    content.append({
        "type": "text",
        "text": enhanced_prompt
    })
    
    # 构建请求体
    payload = {
        "model": model.model_name,
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ],
        "stream": stream,
        "max_tokens": model.max_tokens,
        "temperature": model.temperature
    }
    
    if mode == 'deep-thinking':
        payload["max_tokens"] = min(model.max_tokens * 2, 8000)
    
    timeout = model.timeout * 3 if mode == 'deep-thinking' else model.timeout * 2
    
    response = requests.post(
        api_url,
        headers=headers,
        json=payload,
        timeout=timeout,
        stream=stream
    )
    
    response.raise_for_status()
    
    if stream:
        full_response, usage_info = process_stream_response(response)
        return {
            'response': full_response,
            'usage': usage_info,
            'mode': mode
        }
    else:
        result = response.json()
        return {
            'response': result.get('choices', [{}])[0].get('message', {}).get('content', ''),
            'raw_result': result,
            'mode': mode
        }


@llm_bp.route('/vision/inference', methods=['POST'])
def vision_inference():
    """大模型视觉推理接口"""
    try:
        model = get_active_model()
        if not model:
            return jsonify({'code': 400, 'msg': '请先激活一个大模型'}), 400
        
        # 检查是否有文件上传
        if 'image' not in request.files:
            return jsonify({'code': 400, 'msg': '未找到图像文件'}), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'code': 400, 'msg': '未选择图像文件'}), 400
        
        # 获取提示词，默认为视觉推理提示
        prompt = request.form.get('prompt', '请对这张图片进行视觉推理，分析图片中的对象、场景和可能的行为。')
        
        # 保存上传的图像文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_image:
            image_file.save(temp_image.name)
            image_path = temp_image.name
        
        try:
            # 编码图像为base64
            with open(image_path, 'rb') as f:
                image_data = f.read()
                base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # 构建请求（视觉推理模式）
            if model.service_type == 'local':
                result = call_vision_llm_with_mode(model, base64_image, prompt, 'inference')
            elif model.vendor == 'aliyun':
                result = call_aliyun_vision_with_mode(model, base64_image, prompt, 'inference')
            else:
                result = call_vision_llm_with_mode(model, base64_image, prompt, 'inference')
            
            return jsonify({
                'code': 0,
                'msg': '视觉推理成功',
                'data': result
            })
        finally:
            # 清理临时文件
            if os.path.exists(image_path):
                os.unlink(image_path)
    
    except Exception as e:
        logger.error(f"视觉推理失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/vision/understanding', methods=['POST'])
def vision_understanding():
    """大模型视觉理解接口"""
    try:
        model = get_active_model()
        if not model:
            return jsonify({'code': 400, 'msg': '请先激活一个大模型'}), 400
        
        # 检查是否有文件上传
        if 'image' not in request.files:
            return jsonify({'code': 400, 'msg': '未找到图像文件'}), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'code': 400, 'msg': '未选择图像文件'}), 400
        
        # 获取提示词，默认为视觉理解提示
        prompt = request.form.get('prompt', '请深入理解这张图片的内容，包括场景描述、对象关系、情感色彩和潜在含义。')
        
        # 保存上传的图像文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_image:
            image_file.save(temp_image.name)
            image_path = temp_image.name
        
        try:
            # 编码图像为base64
            with open(image_path, 'rb') as f:
                image_data = f.read()
                base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # 构建请求（视觉理解模式）
            if model.service_type == 'local':
                result = call_vision_llm_with_mode(model, base64_image, prompt, 'understanding')
            elif model.vendor == 'aliyun':
                result = call_aliyun_vision_with_mode(model, base64_image, prompt, 'understanding')
            else:
                result = call_vision_llm_with_mode(model, base64_image, prompt, 'understanding')
            
            return jsonify({
                'code': 0,
                'msg': '视觉理解成功',
                'data': result
            })
        finally:
            # 清理临时文件
            if os.path.exists(image_path):
                os.unlink(image_path)
    
    except Exception as e:
        logger.error(f"视觉理解失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/vision/deep-thinking', methods=['POST'])
def vision_deep_thinking():
    """大模型深度思考接口"""
    try:
        model = get_active_model()
        if not model:
            return jsonify({'code': 400, 'msg': '请先激活一个大模型'}), 400
        
        # 检查是否有文件上传
        if 'image' not in request.files:
            return jsonify({'code': 400, 'msg': '未找到图像文件'}), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'code': 400, 'msg': '未选择图像文件'}), 400
        
        # 获取提示词，默认为深度思考提示
        prompt = request.form.get('prompt', '请对这张图片进行深度思考和分析，包括：1. 图片中的关键信息；2. 可能的原因和背景；3. 潜在的影响和后果；4. 相关的建议和解决方案。')
        
        # 保存上传的图像文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_image:
            image_file.save(temp_image.name)
            image_path = temp_image.name
        
        try:
            # 编码图像为base64
            with open(image_path, 'rb') as f:
                image_data = f.read()
                base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # 构建请求（深度思考模式）
            if model.service_type == 'local':
                result = call_vision_llm_with_mode(model, base64_image, prompt, 'deep-thinking')
            elif model.vendor == 'aliyun':
                result = call_aliyun_vision_with_mode(model, base64_image, prompt, 'deep-thinking')
            else:
                result = call_vision_llm_with_mode(model, base64_image, prompt, 'deep-thinking')
            
            return jsonify({
                'code': 0,
                'msg': '深度思考成功',
                'data': result
            })
        finally:
            # 清理临时文件
            if os.path.exists(image_path):
                os.unlink(image_path)
    
    except Exception as e:
        logger.error(f"深度思考失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


# ==================== 视频推理和理解接口 ====================

@llm_bp.route('/video/inference', methods=['POST'])
def video_inference():
    """大模型视频推理接口"""
    try:
        # 获取激活的模型
        model = get_active_model()
        if not model:
            return jsonify({'code': 400, 'msg': '请先激活一个大模型'}), 400
        
        # 获取视频数据（支持文件上传或URL）
        video_base64 = None
        video_url = None
        
        # 检查是否有文件上传
        if 'video' in request.files:
            video_file = request.files['video']
            if video_file.filename:
                # 保存上传的视频文件
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
                    video_file.save(temp_video.name)
                    video_path = temp_video.name
                    
                    try:
                        # 编码视频为base64
                        with open(video_path, 'rb') as f:
                            video_data = f.read()
                            video_base64 = base64.b64encode(video_data).decode('utf-8')
                    finally:
                        if os.path.exists(video_path):
                            os.unlink(video_path)
        
        # 检查是否有视频URL
        if not video_base64:
            video_url = request.form.get('video_url') or request.json.get('video_url') if request.is_json else None
        
        if not video_base64 and not video_url:
            return jsonify({'code': 400, 'msg': '请提供视频文件或视频URL'}), 400
        
        # 获取提示词，默认为视频推理提示
        prompt = request.form.get('prompt') or (request.json.get('prompt') if request.is_json else None)
        if not prompt:
            prompt = '请分析这个视频中的对象、场景和可能的行为。'
        
        # 构建请求（视频推理模式）
        if model.service_type == 'local':
            result = call_generic_video_llm(model, video_base64, video_url, prompt, 'inference', stream=True)
        elif model.vendor == 'aliyun':
            result = call_aliyun_video_with_mode(model, video_base64, video_url, prompt, 'inference', stream=True)
        else:
            result = call_generic_video_llm(model, video_base64, video_url, prompt, 'inference', stream=True)
        
        return jsonify({
            'code': 0,
            'msg': '视频推理成功',
            'data': result
        })
    
    except Exception as e:
        logger.error(f"视频推理失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/video/understanding', methods=['POST'])
def video_understanding():
    """大模型视频理解接口"""
    try:
        # 获取激活的模型
        model = get_active_model()
        if not model:
            return jsonify({'code': 400, 'msg': '请先激活一个大模型'}), 400
        
        # 获取视频数据（支持文件上传或URL）
        video_base64 = None
        video_url = None
        
        # 检查是否有文件上传
        if 'video' in request.files:
            video_file = request.files['video']
            if video_file.filename:
                # 保存上传的视频文件
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
                    video_file.save(temp_video.name)
                    video_path = temp_video.name
                    
                    try:
                        # 编码视频为base64
                        with open(video_path, 'rb') as f:
                            video_data = f.read()
                            video_base64 = base64.b64encode(video_data).decode('utf-8')
                    finally:
                        if os.path.exists(video_path):
                            os.unlink(video_path)
        
        # 检查是否有视频URL
        if not video_base64:
            video_url = request.form.get('video_url') or request.json.get('video_url') if request.is_json else None
        
        if not video_base64 and not video_url:
            return jsonify({'code': 400, 'msg': '请提供视频文件或视频URL'}), 400
        
        # 获取提示词，默认为视频理解提示
        prompt = request.form.get('prompt') or (request.json.get('prompt') if request.is_json else None)
        if not prompt:
            prompt = '请描述这个视频的内容。'
        
        # 构建请求（视频理解模式）
        if model.service_type == 'local':
            result = call_generic_video_llm(model, video_base64, video_url, prompt, 'understanding', stream=True)
        elif model.vendor == 'aliyun':
            result = call_aliyun_video_with_mode(model, video_base64, video_url, prompt, 'understanding', stream=True)
        else:
            result = call_generic_video_llm(model, video_base64, video_url, prompt, 'understanding', stream=True)
        
        return jsonify({
            'code': 0,
            'msg': '视频理解成功',
            'data': result
        })
    
    except Exception as e:
        logger.error(f"视频理解失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


def call_aliyun_vision_with_mode(model: LLMModel, base64_image: str, prompt: str, mode: str) -> dict:
    """调用阿里云视觉大模型（支持不同模式，图片）"""
    headers = build_headers(model)
    api_url = build_api_url(model.base_url)
    
    enhanced_prompt = enhance_prompt_by_mode(prompt, mode)
    if mode == 'understanding':
        # 理解模式使用原始提示词，但添加前缀
        enhanced_prompt = f"作为视觉理解专家，请深入理解这张图片：{prompt}"
    
    payload = {
        "model": model.model_name,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": enhanced_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": model.max_tokens,
        "temperature": model.temperature
    }
    
    # 深度思考模式可能需要更多的token
    if mode == 'deep-thinking':
        payload["max_tokens"] = min(model.max_tokens * 2, 8000)
    
    timeout = model.timeout * 2 if mode == 'deep-thinking' else model.timeout
    response = requests.post(
        api_url,
        headers=headers,
        json=payload,
        timeout=timeout
    )
    
    response.raise_for_status()
    result = response.json()
    
    return {
        'response': result.get('choices', [{}])[0].get('message', {}).get('content', ''),
        'raw_result': result,
        'mode': mode
    }


def call_vision_llm_with_mode(model: LLMModel, base64_image: str, prompt: str, mode: str) -> dict:
    """调用通用视觉大模型（支持不同模式，图片）"""
    headers = build_headers(model)
    api_url = build_api_url(model.base_url)
    
    enhanced_prompt = enhance_prompt_by_mode(prompt, mode)
    if mode == 'understanding':
        enhanced_prompt = f"作为视觉理解专家，请深入理解这张图片：{prompt}"
    
    payload = {
        "model": model.model_name,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": enhanced_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": model.max_tokens,
        "temperature": model.temperature
    }
    
    if mode == 'deep-thinking':
        payload["max_tokens"] = min(model.max_tokens * 2, 8000)
    
    timeout = model.timeout * 2 if mode == 'deep-thinking' else model.timeout
    response = requests.post(
        api_url,
        headers=headers,
        json=payload,
        timeout=timeout
    )
    
    response.raise_for_status()
    result = response.json()
    
    return {
        'response': result.get('choices', [{}])[0].get('message', {}).get('content', ''),
        'raw_result': result,
        'mode': mode
    }
