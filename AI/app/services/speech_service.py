"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import base64
import hashlib
import hmac
import json
import logging
import time
import os
import uuid
import tempfile
from typing import Dict, Any, Optional
from urllib.parse import urlencode
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config.xunfei_config import get_xunfei_config, validate_language
from app.services.minio_service import ModelService
from models import SpeechRecord, db

logger = logging.getLogger(__name__)


class SpeechService:
    def __init__(self):
        self.config = get_xunfei_config()
        self.session = self._create_session()
        self.request_count = 0
        self.success_count = 0
        self.last_request_time = 0
        self.rate_limit_delay = 0.1  # 默认100ms延迟避免速率限制
        self.minio_bucket_name = "speech-audios"  # MinIO存储桶名称
        self._validate_config()
        logger.info("语音识别服务初始化完成")

    def _validate_config(self):
        """验证配置是否有效"""
        if not self.config['app_id'] or self.config['app_id'] == '07fd57d6':
            logger.warning("使用默认App ID，可能需要替换为实际值")

        if not self.config['secret_key'] or self.config['secret_key'] == 'b16ed9e1cef762967b79145b69811eb6':
            logger.warning("使用默认Secret Key，可能需要替换为实际值")

    def _create_session(self) -> requests.Session:
        """创建带有重试机制的会话"""
        session = requests.Session()

        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _generate_signature(self) -> str:
        """
        生成API请求签名（使用讯飞官方算法）
        参考官方Demo: MD5(appId+ts) + HMAC-SHA1
        """
        ts = str(int(time.time()))
        self.ts = ts  # 保存时间戳供其他方法使用

        # 第一步: 计算MD5(appId+ts)
        appid_ts = self.config['app_id'] + ts
        m2 = hashlib.md5()
        m2.update(appid_ts.encode('utf-8'))
        md5_result = m2.hexdigest()

        # 第二步: 使用HMAC-SHA1计算签名
        md5_bytes = md5_result.encode('utf-8')
        secret_key_bytes = self.config['secret_key'].encode('utf-8')

        signa = hmac.new(secret_key_bytes, md5_bytes, hashlib.sha1).digest()
        signa_base64 = base64.b64encode(signa).decode('utf-8')

        return signa_base64

    def _rate_limit(self):
        """实施速率限制"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time

        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)

        self.last_request_time = time.time()

    def _make_request(self, url: str, method: str = "POST", data: Optional[bytes] = None,
                      params: Optional[Dict] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        发送API请求
        修改: data参数改为bytes类型，用于发送原始音频数据
        """
        self._rate_limit()
        self.request_count += 1

        # 修改请求头，使用适用于二进制数据的Content-Type
        headers = {
            'Content-Type': 'application/json' if data is None else 'application/octet-stream',
            'User-Agent': 'XunfeiSpeechService/1.0'
        }

        try:
            if method.upper() == "POST":
                # 修改: 对于上传请求，使用data参数发送二进制数据
                response = self.session.post(
                    url,
                    data=data,  # 直接发送二进制数据
                    params=params,
                    headers=headers,
                    timeout=timeout or self.config['upload_timeout']
                )
            else:
                response = self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=timeout or self.config['result_timeout']
                )

            response.raise_for_status()
            result = response.json()
            self.success_count += 1

            logger.debug(f"API请求成功: {url}")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {str(e)}")
            return {
                'success': False,
                'error': f"请求失败: {str(e)}",
                'code': getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }
        except json.JSONDecodeError as e:
            logger.error(f"响应解析失败: {str(e)}")
            return {
                'success': False,
                'error': f"响应解析失败: {str(e)}"
            }

    def _upload_to_minio(self, audio_data: bytes, filename: str) -> Optional[str]:
        """
        上传音频文件到MinIO
        """
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_file:
                tmp_file.write(audio_data)
                tmp_path = tmp_file.name

            # 生成唯一的文件名
            ext = os.path.splitext(filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{ext}"
            object_key = f"audios/{unique_filename}"

            # 上传到MinIO
            if ModelService.upload_to_minio(self.minio_bucket_name, object_key, tmp_path):
                # 生成访问URL
                audio_url = f"/api/v1/buckets/{self.minio_bucket_name}/objects/download?prefix={object_key}"
                logger.info(f"音频文件已上传到MinIO: {audio_url}")

                # 删除临时文件
                os.unlink(tmp_path)
                return audio_url
            else:
                logger.error("音频文件上传到MinIO失败")
                os.unlink(tmp_path)
                return None

        except Exception as e:
            logger.error(f"上传音频到MinIO失败: {str(e)}")
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)
            return None

    def _save_speech_record(self, order_id: str, filename: str, file_size: int, duration: int,
                            audio_url: Optional[str] = None, status = "UPLOADED",
                            error_message: Optional[str] = None) -> Optional[SpeechRecord]:
        """
        保存语音识别记录到数据库
        """
        try:
            speech_record = SpeechRecord(
                order_id=order_id,
                filename=filename,
                file_size=file_size,
                duration=duration,
                status=status,
                error_message=error_message,
                audio_file_path=audio_url
            )

            db.session.add(speech_record)
            db.session.commit()

            logger.info(f"语音识别记录已保存到数据库，订单ID: {order_id}")
            return speech_record

        except Exception as e:
            db.session.rollback()
            logger.error(f"保存语音识别记录失败: {str(e)}")
            return None

    def _update_speech_record(self, order_id: str, recognized_text: Optional[str] = None,
                              confidence: Optional[float] = None, status = "COMPLETED",
                              error_message: Optional[str] = None) -> bool:
        """
        更新语音识别记录
        """
        try:
            speech_record = SpeechRecord.query.filter_by(order_id=order_id).first()
            if not speech_record:
                logger.error(f"未找到订单ID对应的记录: {order_id}")
                return False

            if recognized_text is not None:
                speech_record.recognized_text = recognized_text
            if confidence is not None:
                speech_record.confidence = confidence
            if status:
                speech_record.status = status
            if error_message is not None:
                speech_record.error_message = error_message

            speech_record.completed_at = db.func.now()

            db.session.commit()
            logger.info(f"语音识别记录已更新，订单ID: {order_id}")
            return True

        except Exception as e:
            db.session.rollback()
            logger.error(f"更新语音识别记录失败: {str(e)}")
            return False

    def upload_audio(self, audio_data: bytes, filename: str, file_size: int,
                     duration: int, language: "cn", hot_words: Optional[str] = None) -> Dict[str, Any]:
        """
        上传音频文件进行识别，并保存到MinIO和数据库
        修改: 按照讯飞API要求调整参数传递方式和数据格式
        """
        # 验证语言类型
        if not validate_language(language):
            return {
                'success': False,
                'error': f"不支持的语言类型: {language}",
                'supported_languages': list(self.config['supported_languages'].keys())
            }

        # 先上传到MinIO
        audio_url = self._upload_to_minio(audio_data, filename)

        # 生成签名和时间戳
        signa = self._generate_signature()
        timestamp = self.ts

        # 准备请求参数（通过URL查询字符串传递）
        params = {
            'appId': self.config['app_id'],
            'signa': signa,
            'ts': timestamp,
            'fileSize': file_size,
            'fileName': filename,
            'duration': int(duration),
            'language': language
        }

        # 添加热词(如果有)
        if hot_words:
            params['hotWord'] = hot_words

        logger.info(f"上传音频文件: {filename}, 大小: {file_size}字节, 时长: {duration}秒")

        # 发送请求（直接发送二进制音频数据）
        result = self._make_request(
            self.config['upload_url'],
            method="POST",
            data=audio_data,  # 直接发送二进制数据，不要Base64编码
            params=params
        )

        # 添加额外信息
        if 'success' not in result:
            # 讯飞API成功代码为'000000'
            result['success'] = result.get('code') == '000000'

        # 保存到数据库
        order_id = result.get('content', {}).get('orderId') if result.get('success') else None
        if order_id:
            error_msg = result.get('error') if not result.get('success') else None
            status = "UPLOADED" if result.get('success') else "FAILED"

            self._save_speech_record(
                order_id=order_id,
                filename=filename,
                file_size=file_size,
                duration=int(duration),
                audio_url=audio_url,
                status=status,
                error_message=error_msg
            )

            # 将订单ID添加到结果中
            result['order_id'] = order_id

        if not result.get('success'):
            logger.error(f"音频上传失败: {result.get('error', '未知错误')}")

        return result

    def get_recognition_result(self, order_id: str) -> Dict[str, Any]:
        """
        获取识别结果并更新数据库
        修改: 按照讯飞API要求调整参数传递方式
        """
        # 生成签名和时间戳
        signa = self._generate_signature()
        timestamp = self.ts

        # 准备请求参数（通过URL查询字符串传递）
        params = {
            'appId': self.config['app_id'],
            'signa': signa,
            'ts': timestamp,
            'orderId': order_id,
            'resultType': 'transfer'  # 添加结果类型参数
        }

        logger.debug(f"查询识别结果, 订单ID: {order_id}")

        # 发送请求
        result = self._make_request(
            self.config['result_url'],
            method="GET",
            params=params
        )

        # 添加额外信息
        if 'success' not in result:
            # 根据讯飞API文档，status=4表示成功，failType=0表示无错误
            content = result.get('content', {})
            order_info = content.get('orderInfo', {})
            result['success'] = order_info.get('status') == 4 and order_info.get('failType', 1) == 0

        # 更新数据库记录
        if result.get('success'):
            recognized_text = self.extract_text_from_result(result)
            confidence = self.extract_confidence_from_result(result)

            self._update_speech_record(
                order_id=order_id,
                recognized_text=recognized_text,
                confidence=confidence,
                status="COMPLETED"
            )
        else:
            error_msg = result.get('descInfo', '识别失败')
            self._update_speech_record(
                order_id=order_id,
                status="FAILED",
                error_message=error_msg
            )

        return result

    def extract_confidence_from_result(self, result: Dict[str, Any]) -> float:
        """
        从识别结果中提取置信度
        """
        try:
            # 尝试从结果中提取置信度信息
            content = result.get('content', {})
            order_result = content.get('orderResult', '{}')

            if isinstance(order_result, str):
                order_result = json.loads(order_result)

            if 'lattice' in order_result and isinstance(order_result['lattice'], list):
                for lattice in order_result['lattice']:
                    if 'json_1best' in lattice:
                        json_1best = json.loads(lattice['json_1best'])
                        if 'st' in json_1best and 'sc' in json_1best['st']:
                            return float(json_1best['st']['sc'])

            return 0.0
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"提取置信度时发生错误: {str(e)}")
            return 0.0

    def wait_for_result(self, order_id: str, max_wait_time: Optional[int] = None,
                        poll_interval: Optional[int] = None) -> Dict[str, Any]:
        """
        等待识别结果完成并更新数据库
        """
        max_wait = max_wait_time or self.config['max_wait_time']
        interval = poll_interval or self.config['poll_interval']

        start_time = time.time()
        last_status = None

        logger.info(f"开始等待识别结果, 订单ID: {order_id}, 超时: {max_wait}秒")

        # 先更新状态为处理中
        self._update_speech_record(order_id, status="PROCESSING")

        while time.time() - start_time < max_wait:
            result = self.get_recognition_result(order_id)

            # 检查状态
            content = result.get('content', {})
            order_info = content.get('orderInfo', {})
            status = order_info.get('status')

            # 状态发生变化时记录日志
            if status != last_status:
                status_desc = self._get_status_description(status)
                logger.info(f"识别状态: {status_desc} ({status})")
                last_status = status

            # 状态4表示完成
            if status == 4:
                return result

            # 状态5表示失败
            if status == 5:
                error_msg = order_info.get('error', '识别失败')
                logger.error(f"识别失败: {error_msg}")
                return result

            # 等待下一次轮询
            time.sleep(interval)

        # 超时处理
        logger.warning(f"获取识别结果超时, 订单ID: {order_id}")
        self._update_speech_record(
            order_id=order_id,
            status="FAILED",
            error_message="获取结果超时"
        )

        return {
            'success': False,
            'error': '获取结果超时',
            'status': 3,  # 超时状态
            'orderId': order_id
        }

    def _get_status_description(self, status: int) -> str:
        """获取状态码描述"""
        status_descriptions = {
            0: '排队中',
            1: '处理中',
            2: '识别完成',
            3: '识别超时',
            4: '处理完成',
            5: '处理失败'
        }
        return status_descriptions.get(status, f'未知状态({status})')

    def extract_text_from_result(self, result: Dict[str, Any]) -> str:
        """
        从识别结果中提取文本
        修改: 调整解析逻辑以匹配讯飞API的实际返回格式
        """
        try:
            content = result.get('content', {})
            order_result = content.get('orderResult', '{}')

            # 处理orderResult可能是字符串的情况
            if isinstance(order_result, str):
                try:
                    order_result = json.loads(order_result)
                except json.JSONDecodeError:
                    logger.error("orderResult不是有效的JSON字符串")
                    return ""

            # 尝试从lattice2字段提取文本
            if 'lattice2' in order_result and isinstance(order_result['lattice2'], list):
                text_segments = []
                for item in order_result['lattice2']:
                    if 'json_1best' in item:
                        # 修改点：不再使用json.loads，因为json_1best已经是字典
                        json_1best = item['json_1best']

                        # 检查json_1best是否是字符串，如果是则尝试解析
                        if isinstance(json_1best, str):
                            try:
                                json_1best = json.loads(json_1best)
                            except json.JSONDecodeError:
                                logger.warning("json_1best不是有效的JSON字符串")
                                continue

                        # 确保json_1best是字典类型
                        if not isinstance(json_1best, dict):
                            continue

                        try:
                            if 'st' in json_1best and 'rt' in json_1best['st']:
                                for rt_item in json_1best['st']['rt']:
                                    if 'ws' in rt_item:
                                        for ws_item in rt_item['ws']:
                                            if 'cw' in ws_item:
                                                for cw_item in ws_item['cw']:
                                                    if 'w' in cw_item and cw_item['w'].strip():
                                                        text_segments.append(cw_item['w'])
                        except (KeyError, TypeError):
                            continue

                if text_segments:
                    return ''.join(text_segments)

            # 尝试从lattice字段提取文本（利旧）
            if 'lattice' in order_result and isinstance(order_result['lattice'], list):
                text_segments = []
                for lattice in order_result['lattice']:
                    if 'json_1best' in lattice:
                        # 修改点：不再使用json.loads，因为json_1best已经是字典
                        json_1best = lattice['json_1best']

                        # 检查json_1best是否是字符串，如果是则尝试解析
                        if isinstance(json_1best, str):
                            try:
                                json_1best = json.loads(json_1best)
                            except json.JSONDecodeError:
                                logger.warning("json_1best不是有效的JSON字符串")
                                continue

                        # 确保json_1best是字典类型
                        if not isinstance(json_1best, dict):
                            continue

                        try:
                            if 'st' in json_1best and 'rt' in json_1best['st']:
                                for rt_item in json_1best['st']['rt']:
                                    if 'ws' in rt_item:
                                        for ws_item in rt_item['ws']:
                                            if 'cw' in ws_item:
                                                for cw_item in ws_item['cw']:
                                                    if 'w' in cw_item and cw_item['w'].strip():
                                                        text_segments.append(cw_item['w'])
                        except (KeyError, TypeError):
                            continue

                if text_segments:
                    return ''.join(text_segments)

            # 尝试直接提取content字段
            if 'content' in result:
                return result['content']

            logger.warning("无法从结果中提取文本，结果格式未知")
            return ""

        except Exception as e:
            logger.error(f"提取文本时发生错误: {str(e)}")
            return ""

    def get_service_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        return {
            'request_count': self.request_count,
            'success_count': self.success_count,
            'success_rate': (self.success_count / self.request_count * 100) if self.request_count > 0 else 0,
            'config': {k: v for k, v in self.config.items() if k not in ['secret_key']}
        }


# 创建全局服务实例
speech_service = SpeechService()


# 便捷函数
def upload_audio(audio_data: bytes, filename: str, file_size: int,
                 duration: int, language: "cn", hot_words: Optional[str] = None) -> Dict[str, Any]:
    """上传音频文件进行识别"""
    return speech_service.upload_audio(audio_data, filename, file_size, duration, language, hot_words)


def get_recognition_result(order_id: str) -> Dict[str, Any]:
    """获取识别结果"""
    return speech_service.get_recognition_result(order_id)


def wait_for_result(order_id: str, max_wait_time: Optional[int] = None,
                    poll_interval: Optional[int] = None) -> Dict[str, Any]:
    """等待识别结果完成"""
    return speech_service.wait_for_result(order_id, max_wait_time, poll_interval)


def extract_text_from_result(result: Dict[str, Any]) -> str:
    """从识别结果中提取文本"""
    return speech_service.extract_text_from_result(result)


def get_service_stats() -> Dict[str, Any]:
    """获取服务统计信息"""
    return speech_service.get_service_stats()