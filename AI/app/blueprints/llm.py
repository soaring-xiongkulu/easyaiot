"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import datetime
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

@llm_bp.route('/detection/advanced/object', methods=['POST'])
def perform_advanced_object_detection():
    """
    执行大模型物体识别，支持复杂场景和多种输出格式
    ---
    tags: [高级检测]
    consumes:
      - multipart/form-data
    parameters:
      - name: image
        in: formData
        type: file
        required: true
        description: 待检测的图像文件
      - name: targets
        in: formData
        type: string
        required: false
        description: '检测目标列表JSON数组，如["person", "vehicle", "license_plate"]'
      - name: output_type
        in: formData
        type: string
        enum: [bbox, points, polygon]
        default: bbox
        description: 输出类型
      - name: normalized
        in: formData
        type: boolean
        default: true
        description: 是否使用归一化坐标
      - name: render
        in: formData
        type: boolean
        default: false
        description: 是否渲染标注结果
    responses:
      200:
        description: 物体识别成功
      400:
        description: 请求参数错误
      500:
        description: 服务器内部错误
    """
    try:
        # 检查是否有文件上传
        if 'image' not in request.files:
            return jsonify({'code': 400, 'msg': '未找到图像文件'}), 400

        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'code': 400, 'msg': '未选择图像文件'}), 400

        # 获取表单数据
        targets_str = request.form.get('targets', '[]')
        output_type = request.form.get('output_type', 'bbox')
        normalized = request.form.get('normalized', 'true').lower() == 'true'
        render = request.form.get('render', 'false').lower() == 'true'

        try:
            targets = json.loads(targets_str) if targets_str else []
        except json.JSONDecodeError:
            return jsonify({'code': 400, 'msg': 'targets格式错误，必须是有效JSON数组'}), 400

        # 保存上传的图像文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_image:
            image_file.save(temp_image.name)
            image_path = temp_image.name

        try:
            # 执行大模型物体识别
            success, result, error_message = llm_service.perform_advanced_object_detection(
                image_path=image_path,
                targets=targets,
                output_type=output_type,
                normalized=normalized,
                render=render
            )

            if success:
                return jsonify({
                    'code': 0,
                    'msg': '大模型物体识别成功',
                    'data': result
                })
            else:
                return jsonify({
                    'code': 400,
                    'msg': error_message,
                    'data': {}
                })

        finally:
            # 清理临时文件
            if os.path.exists(image_path):
                os.unlink(image_path)

    except Exception as e:
        logger.error(f"大模型物体识别失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/detection/advanced/ocr', methods=['POST'])
def perform_advanced_ocr_recognition():
    """
    执行大模型OCR识别，支持多语言和结构化提取
    ---
    tags: [高级检测]
    consumes:
      - multipart/form-data
    parameters:
      - name: image
        in: formData
        type: file
        required: true
        description: 待识别的图像文件
      - name: languages
        in: formData
        type: string
        required: false
        description: '支持的语言列表JSON数组，如["ch", "en"]'
      - name: extract_structures
        in: formData
        type: boolean
        default: false
        description: 是否提取结构化信息
      - name: specific_targets
        in: formData
        type: string
        required: false
        description: '特定提取目标JSON数组，如["amount", "date", "company_name"]'
    responses:
      200:
        description: OCR识别成功
      400:
        description: 请求参数错误
      500:
        description: 服务器内部错误
    """
    try:
        # 检查是否有文件上传
        if 'image' not in request.files:
            return jsonify({'code': 400, 'msg': '未找到图像文件'}), 400

        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'code': 400, 'msg': '未选择图像文件'}), 400

        # 获取表单数据
        languages_str = request.form.get('languages', '[]')
        extract_structures = request.form.get('extract_structures', 'false').lower() == 'true'
        specific_targets_str = request.form.get('specific_targets', '[]')

        try:
            languages = json.loads(languages_str) if languages_str else []
            specific_targets = json.loads(specific_targets_str) if specific_targets_str else []
        except json.JSONDecodeError:
            return jsonify({'code': 400, 'msg': '参数格式错误，必须是有效JSON数组'}), 400

        # 保存上传的图像文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_image:
            image_file.save(temp_image.name)
            image_path = temp_image.name

        try:
            # 执行大模型OCR识别
            success, result, error_message = llm_service.perform_advanced_ocr_recognition(
                image_path=image_path,
                languages=languages,
                extract_structures=extract_structures,
                specific_targets=specific_targets
            )

            if success:
                return jsonify({
                    'code': 0,
                    'msg': '大模型OCR识别成功',
                    'data': result
                })
            else:
                return jsonify({
                    'code': 400,
                    'msg': error_message,
                    'data': {}
                })

        finally:
            # 清理临时文件
            if os.path.exists(image_path):
                os.unlink(image_path)

    except Exception as e:
        logger.error(f"大模型OCR识别失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/batch/process', methods=['POST'])
def batch_process_images():
    """
    批量处理多个图像
    ---
    tags: [批量处理]
    consumes:
      - application/json
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            image_paths:
              type: array
              items:
                type: string
              description: 图像路径列表
            task_type:
              type: string
              enum: [detection, ocr]
              default: detection
              description: 任务类型
            task_params:
              type: object
              description: 任务特定参数
    responses:
      200:
        description: 批量处理成功
      400:
        description: 请求参数错误
      500:
        description: 服务器内部错误
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400

        image_paths = data.get('image_paths', [])
        task_type = data.get('task_type', 'detection')
        task_params = data.get('task_params', {})

        if not image_paths:
            return jsonify({'code': 400, 'msg': '图像路径列表不能为空'}), 400

        # 验证图像文件是否存在
        for image_path in image_paths:
            if not os.path.exists(image_path):
                return jsonify({'code': 400, 'msg': f'图像文件不存在: {image_path}'}), 400

        # 执行批量处理
        results = llm_service.batch_process_images(
            image_paths=image_paths,
            task_type=task_type,
            **task_params
        )

        successful_count = sum(1 for success, _, _ in results if success)
        failed_count = len(results) - successful_count

        return jsonify({
            'code': 0,
            'msg': f'批量处理完成，成功: {successful_count}, 失败: {failed_count}',
            'data': {
                'results': [
                    {
                        'success': success,
                        'data': result_data,
                        'error_message': error_message
                    }
                    for success, result_data, error_message in results
                ],
                'summary': {
                    'total': len(results),
                    'successful': successful_count,
                    'failed': failed_count
                }
            }
        })

    except Exception as e:
        logger.error(f"批量处理失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/service/status', methods=['GET'])
def get_service_status():
    """
    获取LLM服务状态信息
    ---
    tags: [服务管理]
    responses:
      200:
        description: 服务状态信息
      500:
        description: 服务器内部错误
    """
    try:
        # 检查服务配置状态
        is_configured = llm_service.is_service_configured()

        # 测试连接性
        connectivity_status = {}
        if is_configured:
            is_connected, message = llm_service.verify_service_connectivity()
            connectivity_status = {
                'connected': is_connected,
                'message': message
            }

        # 获取配置详情
        config_details = llm_service.retrieve_configuration_details()

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'configured': is_configured,
                'connectivity': connectivity_status,
                'config_details': config_details,
                'timestamp': datetime.now().isoformat()
            }
        })

    except Exception as e:
        logger.error(f"获取服务状态失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/detection/supported/categories', methods=['GET'])
def get_supported_categories():
    """
    获取支持的检测类别列表
    ---
    tags: [检测管理]
    responses:
      200:
        description: 支持的检测类别列表
      500:
        description: 服务器内部错误
    """
    try:
        # 这里可以返回系统支持的检测类别
        supported_categories = [
            {'id': 'person', 'name': '人员检测', 'description': '识别图像中的所有人员'},
            {'id': 'face', 'name': '人脸检测', 'description': '精确检测面部区域'},
            {'id': 'vehicle', 'name': '车辆检测', 'description': '识别各种类型的车辆'},
            {'id': 'license_plate', 'name': '车牌识别', 'description': '检测和识别车辆牌照信息'},
            {'id': 'helmet', 'name': '安全帽检测', 'description': '检测人员是否佩戴安全头盔'},
            {'id': 'reflective_vest', 'name': '反光衣检测', 'description': '识别安全反光服装'},
            {'id': 'intrusion', 'name': '区域入侵检测', 'description': '识别未经授权进入限制区域'},
            {'id': 'fire', 'name': '火焰检测', 'description': '检测明火或烟雾'},
            {'id': 'weapon', 'name': '武器检测', 'description': '识别危险武器携带'},
            {'id': 'text', 'name': '文本检测', 'description': '检测图像中的文本内容'}
        ]

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'categories': supported_categories,
                'total_count': len(supported_categories)
            }
        })

    except Exception as e:
        logger.error(f"获取支持类别失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@llm_bp.route('/system/health', methods=['GET'])
def system_health():
    """
    系统健康检查端点
    ---
    tags: [系统管理]
    responses:
      200:
        description: 系统健康状态
      500:
        description: 系统不健康
    """
    try:
        # 检查所有关键组件状态
        health_status = {
            'llm_service': llm_service.is_service_configured(),
            'api_connectivity': False,
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy'
        }

        # 测试API连接性
        if health_status['llm_service']:
            is_connected, _ = llm_service.verify_service_connectivity()
            health_status['api_connectivity'] = is_connected
            health_status['status'] = 'healthy' if is_connected else 'degraded'
        else:
            health_status['status'] = 'degraded'

        status_code = 200 if health_status['status'] == 'healthy' else 503

        return jsonify({
            'code': 0,
            'msg': '系统健康检查完成',
            'data': health_status
        }), status_code

    except Exception as e:
        logger.error(f"系统健康检查失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'系统健康检查失败: {str(e)}',
            'data': {
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat()
            }
        }), 500