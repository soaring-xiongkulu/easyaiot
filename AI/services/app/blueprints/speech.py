"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import io
import logging
import wave

from flask import Blueprint, request, jsonify
from app.services.speech_service import upload_audio, get_recognition_result, wait_for_result, extract_text_from_result, \
    get_service_stats

speech_bp = Blueprint('speech', __name__)
logger = logging.getLogger(__name__)

@speech_bp.route('/upload', methods=['POST'])
def upload_audio_file():
    """
    上传音频文件进行语音识别
    """
    try:
        # 检查文件是否存在
        if 'file' not in request.files:
            return jsonify({'code': 400, 'msg': '未找到音频文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'code': 400, 'msg': '未选择文件'}), 400

        # 获取其他参数
        language = request.form.get('language', 'cn')
        hot_words = request.form.get('hot_words', '')
        frontend_duration = request.form.get('duration', type=float, default=0)

        # 读取文件数据
        audio_data = file.read()
        file_size = len(audio_data)

        # 计算音频时长（优先使用后端计算的结果）
        duration = calculate_audio_duration(audio_data)

        # 如果后端计算失败，使用前端传递的时长（如果有）
        if duration is None:
            if frontend_duration > 0:
                duration = frontend_duration
                logger.info(f"使用前端提供的音频时长: {duration}秒")
            else:
                return jsonify({
                    'code': 400,
                    'msg': '无法计算音频时长，请确保音频格式正确或在前端提供时长参数'
                }), 400
        else:
            logger.info(f"计算得到的音频时长: {duration}秒")

        # 验证必要参数
        if duration <= 0:
            return jsonify({'code': 400, 'msg': '音频时长必须大于0'}), 400

        # 调用语音识别服务
        result = upload_audio(
            audio_data=audio_data,
            filename=file.filename,
            file_size=file_size,
            duration=duration,
            language=language,
            hot_words=hot_words
        )

        # 处理服务返回结果
        if result.get('success'):
            return jsonify({
                'code': 0,
                'msg': '音频上传成功',
                'data': {
                    'order_id': result.get('order_id'),
                    'status': result.get('descInfo'),
                    'estimated_wait_time': result.get('content').get('taskEstimateTime')
                }
            })
        else:
            error_msg = result.get('error', '未知错误')
            logger.error(f"音频上传失败: {error_msg}")
            return jsonify({
                'code': 500,
                'msg': f'音频上传失败: {error_msg}'
            }), 500

    except Exception as e:
        logger.error(f"音频上传处理异常: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


@speech_bp.route('/result/<order_id>', methods=['GET'])
def get_speech_result(order_id):
    """
    获取语音识别结果
    """
    try:
        # 获取查询参数
        wait = request.args.get('wait', 'false').lower() == 'true'
        max_wait_time = request.args.get('max_wait_time', type=int)
        poll_interval = request.args.get('poll_interval', type=int)

        # 调用服务获取结果
        if wait:
            result = wait_for_result(
                order_id=order_id,
                max_wait_time=max_wait_time,
                poll_interval=poll_interval
            )
        else:
            result = get_recognition_result(order_id)

        # 处理服务返回结果
        if result.get('success'):
            # 提取识别文本
            text = extract_text_from_result(result)

            return jsonify({
                'code': 0,
                'msg': '获取结果成功',
                'data': {
                    'order_id': order_id,
                    'status': result.get('status'),
                    'text': text,
                    'raw_result': result  # 包含原始结果供调试
                }
            })
        else:
            error_msg = result.get('error', '未知错误')
            status = result.get('status')

            # 根据状态码返回不同信息
            if status == 0 or status == 1:
                # 排队中或处理中
                return jsonify({
                    'code': 1,
                    'msg': '识别处理中',
                    'data': {
                        'order_id': order_id,
                        'status': status,
                        'estimated_wait_time': result.get('estimatedWaitTime')
                    }
                })
            else:
                # 错误状态
                logger.error(f"语音识别失败: {error_msg}, 订单ID: {order_id}")
                return jsonify({
                    'code': 500,
                    'msg': f'识别失败: {error_msg}',
                    'data': {
                        'order_id': order_id,
                        'status': status
                    }
                }), 500

    except Exception as e:
        logger.error(f"获取识别结果异常: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


@speech_bp.route('/stats', methods=['GET'])
def get_speech_stats():
    """
    获取语音识别服务统计信息
    """
    try:
        stats = get_service_stats()

        return jsonify({
            'code': 0,
            'msg': '成功获取统计信息',
            'data': stats
        })

    except Exception as e:
        logger.error(f"获取统计信息异常: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


@speech_bp.route('/languages', methods=['GET'])
def get_supported_languages():
    """
    获取支持的语音识别语言列表
    """
    try:
        # 从配置中获取支持的语言
        from app.config.xunfei_config import get_xunfei_config
        config = get_xunfei_config()

        return jsonify({
            'code': 0,
            'msg': '成功获取支持的语言',
            'data': {
                'supported_languages': config.get('supported_languages', {})
            }
        })

    except Exception as e:
        logger.error(f"获取支持语言异常: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


def calculate_audio_duration(audio_data):
    """
    计算音频文件的时长（秒）

    Args:
        audio_data: 音频文件的二进制数据

    Returns:
        float: 音频时长（秒），如果计算失败则返回None
    """
    try:
        with wave.open(io.BytesIO(audio_data)) as audio_file:
            frames = audio_file.getnframes()
            rate = audio_file.getframerate()
            duration = frames / float(rate)
            return duration
    except Exception as e:
        logger.warning(f"无法通过wave模块计算音频时长: {str(e)}")

    try:
        # 如果wave模块失败，尝试其他方法（例如使用第三方库）
        # 这里可以添加其他音频处理库的支持，如pydub、librosa等
        # 示例: 使用pydub (需要安装)
        # from pydub import AudioSegment
        # audio = AudioSegment.from_file(io.BytesIO(audio_data))
        # return len(audio) / 1000.0  # 转换为秒

        logger.info("考虑安装pydub库以支持更多音频格式: pip install pydub")
        return None
    except ImportError:
        logger.warning("pydub未安装，无法计算复杂音频格式的时长")
        return None