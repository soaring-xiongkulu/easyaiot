import logging
import json
import tempfile
import os
from flask import Blueprint, request, jsonify

# 配置日志
logger = logging.getLogger(__name__)

# 创建蓝图
llm_bp = Blueprint('llm', __name__)

# 初始化LLM服务
from app.services.llm_service import LLMService

llm_service = LLMService()

@llm_bp.route('/config/status', methods=['GET'])
def get_config_status():
    """
    获取当前LLM配置状态
    """
    try:
        config_details = llm_service.retrieve_configuration_details()
        is_valid, message = llm_service.validate_current_configuration()

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'config_details': config_details,
                'is_valid': is_valid,
                'validation_message': message
            }
        })
    except Exception as e:
        logger.error(f"获取配置状态失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/config/refresh', methods=['POST'])
def refresh_config():
    """
    刷新LLM配置
    """
    try:
        llm_service.refresh_configuration()
        return jsonify({
            'code': 0,
            'msg': '配置刷新成功',
            'data': llm_service.retrieve_configuration_details()
        })
    except Exception as e:
        logger.error(f"刷新配置失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/connectivity/test', methods=['GET'])
def test_connectivity():
    """
    测试LLM服务连接性
    """
    try:
        is_connected, message = llm_service.verify_service_connectivity()

        if is_connected:
            return jsonify({
                'code': 0,
                'msg': message,
                'data': {'connected': True}
            })
        else:
            return jsonify({
                'code': 400,
                'msg': message,
                'data': {'connected': False}
            })
    except Exception as e:
        logger.error(f"连接测试失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/detection/prompt/generate', methods=['POST'])
def generate_detection_prompt():
    """
    生成安全检测提示词
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400

        detection_categories = data.get('detection_categories', [])
        context = data.get('context', {})
        precision_level = data.get('precision_level', 'high')
        environment_type = data.get('environment_type', 'industrial')
        output_format = data.get('output_format', 'detailed_json')

        if not detection_categories:
            return jsonify({'code': 400, 'msg': '检测类别不能为空'}), 400

        prompt = llm_service.generate_security_detection_prompt(
            detection_categories=detection_categories,
            context=context,
            precision_level=precision_level,
            environment_type=environment_type,
            output_format=output_format
        )

        return jsonify({
            'code': 0,
            'msg': '提示词生成成功',
            'data': {
                'prompt': prompt,
                'detection_categories': detection_categories,
                'environment_type': environment_type
            }
        })
    except Exception as e:
        logger.error(f"生成提示词失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/vision/analysis', methods=['POST'])
def perform_vision_analysis():
    """
    执行视觉分析 - 使用execute_vision_analysis方法
    """
    try:
        # 检查是否有文件上传
        if 'image' not in request.files:
            return jsonify({'code': 400, 'msg': '未找到图像文件'}), 400

        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'code': 400, 'msg': '未选择图像文件'}), 400

        # 获取JSON数据
        data = request.form.to_dict()
        try:
            if data.get('prompt_data'):
                prompt_data = json.loads(data.get('prompt_data'))
            else:
                prompt_data = {}
        except json.JSONDecodeError:
            return jsonify({'code': 400, 'msg': 'prompt_data格式错误，必须是有效JSON'}), 400

        # 保存上传的图像文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_image:
            image_file.save(temp_image.name)
            image_path = temp_image.name

        try:
            # 生成或使用提供的提示词
            if 'prompt' in prompt_data:
                prompt = prompt_data['prompt']
            else:
                detection_categories = prompt_data.get('detection_categories', [])
                if not detection_categories:
                    return jsonify({'code': 400, 'msg': '未提供提示词或检测类别'}), 400

                prompt = llm_service.generate_security_detection_prompt(
                    detection_categories=detection_categories,
                    context=prompt_data.get('context', {}),
                    precision_level=prompt_data.get('precision_level', 'high'),
                    environment_type=prompt_data.get('environment_type', 'industrial'),
                    output_format=prompt_data.get('output_format', 'detailed_json')
                )

            # 执行视觉分析 - 使用execute_vision_analysis方法
            api_response = llm_service.execute_vision_analysis(
                image_path=image_path,
                prompt=prompt,
                max_tokens=prompt_data.get('max_tokens', 4000),
                temperature=prompt_data.get('temperature', 0.1),
                stream=prompt_data.get('stream', False)
            )

            # 处理检测结果
            detections = llm_service.process_detection_results(api_response)

            return jsonify({
                'code': 0,
                'msg': '视觉分析成功',
                'data': {
                    'detections': detections,
                    'raw_response': api_response,
                    'detection_count': len(detections)
                }
            })

        finally:
            # 清理临时文件
            if os.path.exists(image_path):
                os.unlink(image_path)

    except Exception as e:
        logger.error(f"视觉分析失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/detection/object', methods=['POST'])
def perform_object_detection():
    """
    执行物体检测 - 使用perform_object_detection方法
    """
    try:
        # 检查是否有文件上传
        if 'image' not in request.files:
            return jsonify({'code': 400, 'msg': '未找到图像文件'}), 400

        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'code': 400, 'msg': '未选择图像文件'}), 400

        # 获取检测标签
        data = request.form.to_dict()
        labels_str = data.get('labels', '[]')

        try:
            labels = json.loads(labels_str)
        except json.JSONDecodeError:
            return jsonify({'code': 400, 'msg': 'labels格式错误，必须是有效JSON数组'}), 400

        if not labels:
            return jsonify({'code': 400, 'msg': '检测标签不能为空'}), 400

        # 保存上传的图像文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_image:
            image_file.save(temp_image.name)
            image_path = temp_image.name

        try:
            # 执行物体检测 - 使用perform_object_detection方法
            success, detections, error_message = llm_service.perform_object_detection(
                image_path=image_path,
                labels=labels
            )

            if success:
                return jsonify({
                    'code': 0,
                    'msg': '物体检测成功',
                    'data': {
                        'detections': detections,
                        'detection_count': len(detections)
                    }
                })
            else:
                return jsonify({
                    'code': 400,
                    'msg': error_message,
                    'data': {'detections': []}
                })

        finally:
            # 清理临时文件
            if os.path.exists(image_path):
                os.unlink(image_path)

    except Exception as e:
        logger.error(f"物体检测失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/config/details', methods=['GET'])
def get_config_details():
    """
    获取当前配置的详细信息
    """
    try:
        config_details = llm_service.retrieve_configuration_details()
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': config_details
        })
    except Exception as e:
        logger.error(f"获取配置详情失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/service/configured', methods=['GET'])
def check_service_configured():
    """
    检查服务是否已配置
    """
    try:
        is_configured = llm_service.is_service_configured()
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {'configured': is_configured}
        })
    except Exception as e:
        logger.error(f"检查服务配置失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/image/encode', methods=['POST'])
def encode_image():
    """
    将图像编码为Base64
    """
    try:
        if 'image' not in request.files:
            return jsonify({'code': 400, 'msg': '未找到图像文件'}), 400

        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'code': 400, 'msg': '未选择图像文件'}), 400

        # 保存上传的图像文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_image:
            image_file.save(temp_image.name)
            image_path = temp_image.name

        try:
            # 编码图像
            base64_image = llm_service.convert_image_to_base64(image_path)

            return jsonify({
                'code': 0,
                'msg': '图像编码成功',
                'data': {
                    'base64_image': base64_image[:100] + '...'  # 只返回部分内容预览
                }
            })

        finally:
            # 清理临时文件
            if os.path.exists(image_path):
                os.unlink(image_path)

    except Exception as e:
        logger.error(f"图像编码失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/chat/completion', methods=['POST'])
def chat_completion():
    """
    通用聊天补全接口
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400

        messages = data.get('messages', [])
        if not messages:
            return jsonify({'code': 400, 'msg': '消息列表不能为空'}), 400

        # 构建请求参数
        request_params = {
            'max_tokens': data.get('max_tokens', 4000),
            'temperature': data.get('temperature', 0.1),
            'top_p': data.get('top_p', 0.9),
            'stream': data.get('stream', False)
        }

        # 准备请求头部和负载
        headers = llm_service._prepare_request_headers()
        payload = llm_service._construct_request_payload(messages, **request_params)
        api_url = llm_service._construct_api_endpoint()

        # 发送请求
        response = llm_service.http_session.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=llm_service.DEFAULT_REQUEST_TIMEOUT
        )

        response.raise_for_status()
        result = response.json()

        return jsonify({
            'code': 0,
            'msg': '聊天补全成功',
            'data': result
        })

    except Exception as e:
        logger.error(f"聊天补全失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500