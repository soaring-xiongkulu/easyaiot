"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import base64
import json
import logging
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any

import requests
from requests.exceptions import RequestException, Timeout

from models import LLMConfig

# 配置日志处理器
logging_handler = logging.getLogger(__name__)

class ModelType(Enum):
    """枚举定义支持的AI模型类型"""
    TEXT = "text"
    VISION = "vision"
    AUDIO = "audio"
    MULTIMODAL = "multimodal"


class LLMService:
    """
    大型语言模型服务接口，提供多模态AI能力调用
    支持与OpenAI兼容的API端点进行交互，包括文本、视觉、音频和多模态分析
    """

    # API端点常量
    CHAT_COMPLETION_ENDPOINT = "/v1/chat/completions"
    DEFAULT_REQUEST_TIMEOUT = 180  # 默认请求超时(秒)
    MAXIMUM_RETRY_ATTEMPTS = 3  # 最大重试次数

    def __init__(self):
        self.active_configuration: Optional[LLMConfig] = None
        self.http_session = requests.Session()
        self._initialize_active_configuration()

    def _initialize_active_configuration(self) -> Optional[LLMConfig]:
        """
        初始化并加载当前激活的LLM配置

        Returns:
            Optional[LLMConfig]: 已激活的配置对象，如无激活配置则返回None

        Raises:
            ConfigurationError: 当配置加载过程中发生严重错误时
        """
        try:
            self.active_configuration = LLMConfig.query.filter_by(is_active=True).first()
            if self.active_configuration:
                logging_handler.info(
                    f"已加载LLM配置: {self.active_configuration.name} "
                    f"({self.active_configuration.vendor}/{self.active_configuration.model})")
            else:
                logging_handler.warning("未找到激活的LLM配置")
            return self.active_configuration
        except Exception as error:
            # logging_handler.error(f"加载LLM配置失败: {error}")
            return None

    def refresh_configuration(self) -> None:
        """重新加载并刷新当前配置"""
        self._initialize_active_configuration()

    def validate_current_configuration(self) -> Tuple[bool, str]:
        """
        验证当前配置的完整性和有效性

        Returns:
            Tuple[bool, str]: (配置是否有效, 错误描述信息)
        """
        if not self.active_configuration:
            return False, "未找到激活的LLM配置"

        # 检查必要配置字段
        required_fields = ['base_url', 'api_key', 'model']
        for field in required_fields:
            if not getattr(self.active_configuration, field, None):
                return False, f"配置缺少必要字段: {field}"

        return True, "配置有效"

    def _construct_api_endpoint(self) -> str:
        """
        构建完整的API端点URL，支持多供应商格式

        Returns:
            str: 完整的API端点URL

        Raises:
            ValueError: 当当前配置无效时抛出
            ConfigurationError: 当供应商配置不支持时
        """
        is_valid, error_message = self.validate_current_configuration()
        if not is_valid:
            raise ValueError(error_message)

        base_url = self.active_configuration.base_url.rstrip('/')

        # 处理不同供应商的URL格式
        vendor_name = self.active_configuration.vendor.lower()
        if vendor_name in ['openai', 'azure_openai', 'anthropic']:
            # 标准OpenAI格式或Azure OpenAI
            if 'azure' in vendor_name and '.openai.azure.com' in base_url:
                # Azure OpenAI特殊格式
                if '/openai/deployments/' in base_url:
                    return base_url  # 已经是完整URL
                else:
                    api_version = self.active_configuration.api_version or '2024-02-15-preview'
                    return f"{base_url}/openai/deployments/{self.active_configuration.model}/chat/completions?api-version={api_version}"
            elif 'chat/completions' in base_url:
                return base_url  # 已经是完整端点
            else:
                return f"{base_url}{self.CHAT_COMPLETION_ENDPOINT}"
        else:
            # 其他供应商（Anthropic、Cohere等）
            if 'chat/completions' in base_url:
                return base_url
            else:
                # 假设其他供应商也使用OpenAI兼容的端点
                return f"{base_url}{self.CHAT_COMPLETION_ENDPOINT}"

    def is_service_configured(self) -> bool:
        """检查服务是否已正确配置"""
        is_valid, _ = self.validate_current_configuration()
        return is_valid

    def convert_image_to_base64(self, image_path: str) -> str:
        """
        将图像文件转换为Base64编码字符串

        Args:
            image_path: 图像文件路径

        Returns:
            str: Base64编码的图像数据

        Raises:
            FileNotFoundError: 当图像文件不存在时
            IOError: 当读取图像文件失败时
        """
        try:
            with open(image_path, "rb") as image_file:
                encoded_data = base64.b64encode(image_file.read()).decode('utf-8')
                logging_handler.debug(f"成功编码图像: {image_path}")
                return encoded_data
        except FileNotFoundError:
            logging_handler.error(f"图像文件不存在: {image_path}")
            raise
        except IOError as error:
            logging_handler.error(f"读取图像文件失败: {image_path}, 错误: {error}")
            raise

    def _prepare_request_headers(self) -> Dict[str, str]:
        """
        准备API请求头部信息

        Returns:
            Dict[str, str]: 请求头部字典
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.active_configuration.api_key}"
        }

        # 添加供应商特定的头部
        vendor_name = self.active_configuration.vendor.lower()
        if vendor_name == 'anthropic':
            headers["x-api-key"] = self.active_configuration.api_key
            headers["anthropic-version"] = self.active_configuration.api_version or "2023-06-01"
        elif vendor_name == 'azure_openai':
            headers["api-key"] = self.active_configuration.api_key

        return headers

    def _construct_request_payload(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """
        构建API请求负载数据

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Returns:
            Dict[str, Any]: 请求负载字典
        """
        payload = {
            "model": self.active_configuration.model,
            "messages": messages,
            "max_tokens": kwargs.get('max_tokens', 4000),
            "temperature": kwargs.get('temperature', 0.1),
            "top_p": kwargs.get('top_p', 0.9),
            "stream": kwargs.get('stream', False)
        }

        # 添加供应商特定参数
        if self.active_configuration.vendor.lower() == 'anthropic':
            payload["max_tokens"] = kwargs.get('max_tokens', 4096)

        # 移除None值的字段
        return {key: value for key, value in payload.items() if value is not None}

    def generate_security_detection_prompt(
            self,
            detection_categories: List[str],
            context: Optional[Dict[str, str]] = None,
            precision_level: str = "high",
            environment_type: str = "industrial",
            output_format: str = "detailed_json"
    ) -> str:
        """
        生成专业级安全监控目标检测提示词，支持多场景适配和精度控制

        Args:
            detection_categories: 检测类别列表，包括人员、车辆、行为等
            context: 上下文信息字典，包含监控场景、环境条件等
            precision_level: 检测精度要求('high'/'medium'/'low')
            environment_type: 环境类型('industrial'/'urban'/'residential'/'commercial')
            output_format: 输出格式要求('detailed_json'/'simplified_json')

        Returns:
            str: 精心构造的安全监控检测提示词字符串
        """
        # 基础角色和任务定义
        prompt_parts = [
            "# 智能安防视觉分析系统指令",
            "",
            "## 系统角色与使命",
            "角色: 高级安防监控分析专家，专注于多目标智能检测与安全预警",
            "使命: 通过精确的视觉分析，为安防系统提供可靠的目标检测和异常行为识别",
            "专业领域: 人员管控、车辆监控、行为分析、安全合规检查"
        ]

        # 添加上下文信息
        if context:
            context_info = ["## 监控场景上下文"]
            for key, value in context.items():
                context_info.append(f"- {key}: {value}")
            prompt_parts.extend(context_info)

        # 检测类别详细说明
        category_descriptions = {
            "person": "人员检测 - 识别图像中的所有人员，包括完整身体轮廓",
            "face": "人脸检测 - 精确检测面部区域，用于身份识别或情绪分析",
            "vehicle": "车辆检测 - 识别各种类型的车辆（轿车、卡车、工程车等）",
            "license_plate": "车牌识别 - 检测和识别车辆牌照信息",
            "helmet": "安全帽检测 - 检测人员是否佩戴安全头盔",
            "reflective_vest": "反光衣检测 - 识别安全反光服装的穿着情况",
            "safety_gloves": "安全手套检测 - 检查手部防护装备",
            "intrusion": "区域入侵检测 - 识别未经授权进入限制区域",
            "crowding": "人群聚集检测 - 监测人员密集程度和分布",
            "loitering": "徘徊检测 - 识别可疑徘徊行为",
            "fall_detection": "跌倒检测 - 检测人员跌倒情况",
            "smoking": "吸烟检测 - 识别违规吸烟行为",
            "fire": "火焰检测 - 检测明火或烟雾",
            "weapon": "武器检测 - 识别危险武器携带",
            "abandoned_object": "物品遗留检测 - 发现无人看管的可疑物品"
        }

        # 构建检测类别描述
        detection_desc = ["## 检测类别要求"]
        for category in detection_categories:
            if category in category_descriptions:
                detection_desc.append(f"- {category_descriptions[category]}")
            else:
                detection_desc.append(f"- {category}: 需要检测的特定目标")

        prompt_parts.extend(detection_desc)

        # 环境特定指导
        environment_guidance = {
            "industrial": [
                "## 工业环境检测规范",
                "- 重点关注安全装备合规性（安全帽、反光衣等）",
                "- 监控危险区域人员活动",
                "- 检测设备操作区域的安全隐患",
                "- 注意恶劣光照条件（强光、阴影、低光照）下的检测准确性"
            ],
            "urban": [
                "## 城市环境检测规范",
                "- 监控交通流量和车辆行为",
                "- 检测公共场所异常行为",
                "- 识别可疑人员和物品",
                "- 关注人群密集区域的安全状况"
            ],
            "residential": [
                "## 住宅环境检测规范",
                "- 重点检测区域入侵行为",
                "- 监控公共区域安全",
                "- 识别可疑徘徊和异常活动",
                "- 注意隐私保护要求"
            ],
            "commercial": [
                "## 商业环境检测规范",
                "- 监控客流密度和分布",
                "- 检测安全合规情况",
                "- 识别可疑行为和物品",
                "- 关注重点区域的安全状态"
            ]
        }

        prompt_parts.extend([""] + environment_guidance.get(environment_type, []))

        # 精度要求配置
        precision_standards = {
            "high": {
                "desc": "高精度检测（安全关键应用）",
                "requirements": [
                    "置信度阈值: ≥0.85",
                    "坐标精度: 6位小数",
                    "最小检测尺寸: 32×32像素",
                    "最大漏检率: <2%",
                    "最大误检率: <3%"
                ]
            },
            "medium": {
                "desc": "中等精度检测（一般监控应用）",
                "requirements": [
                    "置信度阈值: ≥0.75",
                    "坐标精度: 4位小数",
                    "最小检测尺寸: 24×24像素",
                    "最大漏检率: <5%",
                    "最大误检率: <7%"
                ]
            },
            "low": {
                "desc": "基本精度检测（辅助监控应用）",
                "requirements": [
                    "置信度阈值: ≥0.65",
                    "坐标精度: 6位小数",
                    "最小检测尺寸: 32×32像素",
                    "最大漏检率: <2%",
                    "最大误检率: <3%"
                ]
            }
        }

        precision_info = [
            "## 检测精度标准",
            f"精度等级: {precision_standards[precision_level]['desc']}"
        ]
        precision_info.extend(precision_standards[precision_level]['requirements'])
        prompt_parts.extend([""] + precision_info)

        # 检测技术规范
        prompt_parts.extend([
            "",
            "## 技术检测规范",
            "1. 多尺度检测: 能够检测不同大小的目标，从近景大目标到远景小目标",
            "2. 遮挡处理: 对部分遮挡目标仍能进行有效检测",
            "3. 光照适应性: 适应不同光照条件，包括逆光、低光照等挑战性环境",
            "4. 实时性要求: 处理速度满足实时监控需求（≥15fps）",
            "5. 抗干扰能力: 对复杂背景、天气变化（雨、雾、雪）有一定鲁棒性",
            "",
            "## 质量保证要求",
            "1. 可靠性: 检测结果稳定可靠，误报率控制在可接受范围内",
            "2. 一致性: 相同场景下的检测结果保持一致",
            "3. 可追溯性: 检测结果能够追溯到具体的图像证据",
            "4. 实时性: 满足监控系统的实时响应要求"
        ])

        # 输出格式规范
        if output_format == "detailed_json":
            output_schema = {
                "detection_results": {
                    "timestamp": "string (检测时间戳 ISO格式)",
                    "camera_id": "string (摄像头标识)",
                    "scene_type": "string (场景类型)",
                    "detected_objects": [
                        {
                            "object_id": "string (目标唯一标识)",
                            "category": "string (目标类别)",
                            "confidence": "float (检测置信度 0.0-1.0)",
                            "bbox": {
                                "x": "float (中心点x坐标)",
                                "y": "float (中心点y坐标)",
                                "width": "float (边界框宽度)",
                                "height": "float (边界框高度)"
                            },
                            "attributes": {
                                "orientation": "string (目标朝向)",
                                "status": "string (状态信息)",
                                "color": "string (颜色信息)",
                                "additional_info": "object (其他属性)"
                            }
                        }
                    ],
                    "environmental_conditions": {
                        "lighting": "string (光照条件)",
                        "weather": "string (天气状况)",
                        "overall_quality": "string (图像质量评估)"
                    },
                    "performance_metrics": {
                        "processing_time": "float (处理时间ms)",
                        "total_detections": "int (总检测数量)",
                        "confidence_avg": "float (平均置信度)"
                    }
                },
                "system_info": {
                    "version": "string (系统版本)",
                    "model_version": "string (模型版本)",
                    "inference_mode": "string (推理模式)"
                }
            }
        else:
            output_schema = {
                "objects": [
                    {
                        "label": "string",
                        "confidence": "float",
                        "x": "float",
                        "y": "float",
                        "width": "float",
                        "height": "float"
                    }
                ]
            }

        prompt_parts.extend([
            "",
            "## 输出格式要求",
            "严格遵循以下JSON格式规范:",
            json.dumps(output_schema, indent=2, ensure_ascii=False),
            "",
            "## 数据质量要求",
            "1. 坐标精度: 所有坐标值必须使用高精度浮点数",
            "2. 置信度: 准确反映检测可靠性，避免过度自信或保守",
            "3. 完整性: 包含所有要求的检测字段和信息",
            "4. 一致性: 相同类型的检测结果保持格式一致"
        ])

        # 最终执行要求
        prompt_parts.extend([
            "",
            "## 最终执行要求",
            "1. 全面性: 检测图像中的所有相关目标",
            "2. 准确性: 确保检测结果准确可靠",
            "3. 及时性: 在要求的时间内完成检测分析",
            "4. 一致性: 不同时间段的检测结果保持稳定",
            "5. 可解释性: 检测结果能够被理解和验证",
            "",
            "**重要原则: 安全性优于检测速度，准确性优于检测数量！**",
            "**核心目标: 通过可靠的视觉分析，为安防决策提供准确依据！**"
        ])

        return "\n".join(prompt_parts)

    def execute_vision_analysis(self, image_path: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        执行视觉分析API调用

        Args:
            image_path: 图像文件路径
            prompt: 分析提示词
            **kwargs: 额外参数

        Returns:
            Dict[str, Any]: API响应数据

        Raises:
            ValueError: 当配置无效时
            RequestException: 当API请求失败时
        """
        if not self.is_service_configured():
            raise ValueError("LLM服务未正确配置")

        try:
            # 编码图像
            base64_image = self.convert_image_to_base64(image_path)

            # 构建消息
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]

            # 构建请求
            headers = self._prepare_request_headers()
            payload = self._construct_request_payload(messages, **kwargs)
            api_url = self._construct_api_endpoint()

            # 设置超时和重试
            timeout = kwargs.get('timeout', self.DEFAULT_REQUEST_TIMEOUT)
            max_retries = kwargs.get('max_retries', self.MAXIMUM_RETRY_ATTEMPTS)

            # 发送请求（带重试机制）
            for attempt in range(max_retries):
                try:
                    response = self.http_session.post(
                        api_url,
                        headers=headers,
                        json=payload,
                        timeout=timeout,
                        proxies={'http': None, 'https': None}  # 禁用代理
                    )

                    response.raise_for_status()  # 检查HTTP错误

                    result = response.json()
                    logging_handler.info(f"API调用成功: {api_url}")
                    return result

                except Timeout:
                    if attempt == max_retries - 1:
                        logging_handler.error(f"API请求超时（尝试{attempt + 1}次）")
                        raise
                    logging_handler.warning(f"API请求超时，第{attempt + 1}次重试...")

                except RequestException as error:
                    if attempt == max_retries - 1:
                        logging_handler.error(f"API请求失败: {error}")
                        raise
                    logging_handler.warning(f"API请求失败，第{attempt + 1}次重试: {error}")

        except Exception as error:
            logging_handler.error(f"视觉API调用失败: {error}")
            raise

    def execute_vision_analysis(self, image_path: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        执行视觉分析API调用

        Args:
            image_path: 图像文件路径极速            prompt: 分析提示词
            **kwargs: 额外参数

        Returns:
            Dict[str, Any]: API响应数据

        Raises:
            ValueError: 当配置无效时
            RequestException: 当API请求失败时
        """
        if not self.is_service_configured():
            raise ValueError("LLM服务未正确配置")

        try:
            # 编码图像
            base64_image = self.convert_image_to_base64(image_path)

            # 构建消息
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]

            # 构建请求
            headers = self._prepare_request_headers()
            payload = self._construct_request_payload(messages, **kwargs)
            api_url = self._construct_api极速()

            # 设置超时和重试
            timeout = kwargs.get('timeout', self.DEFAULT_REQUEST_TIMEOUT)
            max_retries = kwargs.get('max_retries', self.MAXIMUM_RETRY_ATTEMPTS)

            # 发送请求（带重试机制）
            for attempt in range(max_retries):
                try:
                    response = self.http_session.post(
                        api_url,
                        headers=headers,
                        json=payload,
                        timeout=timeout,
                        proxies={'http': None, 'https': None}  # 禁用代理
                    )

                    response.raise_for_status()  # 检查HTTP错误

                    result = response.json()
                    logging_handler.info(f"API调用成功: {api_url}")
                    return result

                except Timeout:
                    if attempt == max_retries - 1:
                        logging_handler.error(f"API请求超时（尝试{attempt + 1}次）")
                        raise
                    logging_handler.warning(f"API请求超时，第{attempt + 1}次重试...")

                except RequestException as error:
                    if attempt == max_retries - 1:
                        logging_handler.error(f"API请求失败: {error}")
                        raise
                    logging_handler.warning(f"API请求失败，第{attempt + 1}次极速: {error}")

        except Exception as error:
            logging_handler.error(f"视觉API调用失败: {error}")
            raise

    def process_detection_results(self, api_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        处理API返回的检测结果

        Args:
            api_response: API响应字典

        Returns:
            List[Dict[str, Any]]: 解析后的检测结果列表
        """
        try:
            # 提取响应内容
            if 'choices' not in api_response or not api_response['choices']:
                logging_handler.warning("API响应缺少choices字段")
                return []

            content = api_response['choices'][0]['message']['content']
            logging_handler.debug(f"API原始响应: {content}")

            # 尝试解析JSON
            try:
                result_data = json.loads(content)
            except json.JSONDecodeError:
                # 尝试提取JSON部分
                result_data = self._parse_json_from_response(content)

            # 解析检测结果
            detected_objects = []
            if 'objects' in result_data:
                for obj in result_data['objects']:
                    if isinstance(obj, dict) and 'label' in obj:
                        detection = {
                            'label': obj['label'],
                            'confidence': float(obj.get('confidence', 0.8)),
                            'x': float(obj.get('x', 0.0)),
                            'y': float(obj.get('y', 0.0)),
                            'width': float(obj.get('width', 0.0)),
                            'height': float(obj.get('height', 0.0))
                        }
                        detected_objects.append(detection)

            logging_handler.info(f"解析到 {len(detected_objects)} 个检测结果")
            return detected_objects

        except Exception as error:
            logging_handler.error(f"解析检测结果失败: {error}")
            return []

    def _parse_json_from_response(self, content: str) -> Dict[str, Any]:
        """
        从响应内容中解析JSON数据

        Args:
            content: 响应内容

        Returns:
            Dict[str, Any]: 解析的JSON数据
        """
        import re

        # 尝试提取代码块中的JSON
        json_patterns = [
            r'```(?:json)?\s*(\{.*?\})\s*```',
            r'\{.*\}'
        ]

        for pattern in json_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                try:
                    json_str = match.group(1) if pattern.startswith('```') else match.group()
                    return json.load极速(json_str)
                except json.JSON极速:
                    continue

        # 如果所有尝试都失败，返回空结果
        return {"objects": []}

    def perform_object_detection(self, image_path: str, labels: List[str]) -> Tuple[bool, List[Dict], str]:
        """
        执行图像中的物体检测

        Args:
            image_path: 图像文件路径
            labels: 要检测的标签列表

        Returns:
            Tuple[bool, List[Dict], str]: (是否成功, 检测结果列表, 错误信息)
        """
        try:
            if not self.is_service_configured():
                return False, [], "LLM服务未配置"

            # 生成提示词
            prompt = self.generate_security_detection_prompt(labels)

            # 调用API
            api_response = self.execute_vision_analysis(image_path, prompt)

            # 解析结果
            detections = self.process_detection_results(api_response)

            return True, detections, ""

        except Exception as error:
            error_msg = f"物体检测失败: {str(error)}"
            logging_handler.error(error_msg)
            return False, [], error_msg

    def verify_service_connectivity(self) -> Tuple[bool, str]:
        """
        验证服务连接性

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            if not self.is_service_configured():
                return False, "LLM服务未配置"

            headers = self._prepare_request_headers()
            api_url = self._construct_api_endpoint()

            # 简单的测试请求
            test_payload = {
                "model": self.active_config.model,
                "messages": [{"role": "user", "content": "Test connection."}],
                "max_tokens": 5
            }

            response = self.http_session.post(
                api_url,
                headers=headers,
                json=test_payload,
                timeout=10
            )

            if response.status_code == 200:
                return True, "连接测试成功"
            else:
                return False, f"连接测试失败: {response.status_code} - {response.text}"

        except Exception as error:
            return False, f"连接测试失败: {str(error)}"

    def retrieve_configuration_details(self) -> Dict[str, Any]:
        """
        获取当前配置详细信息

        Returns:
            Dict[str, Any]: 配置信息字典
        """
        if not self.active_configuration:
            return {"status": "未配置"}

        return {
            "name": self.active_configuration.name,
            "vendor": self.active_configuration.vendor,
            "model": self.active_configuration.model,
            "model_type": self.active_configuration.model_type,
            "base_url": self.active_configuration.base_url,
            "is_active": self.active_configuration.is_active,
            "status": self.active_configuration.status
        }

    # ==================== 新增方法：大模型物体识别 ====================

    def perform_advanced_object_detection(self, image_path: str, targets: List[str] = None,
                                          output_type: str = "bbox", normalized: bool = True,
                                          render: bool = False) -> Tuple[bool, Dict[str, Any], str]:
        """
        执行大模型物体识别，支持复杂场景和多种输出格式

        Args:
            image_path: 图像文件路径
            targets: 要检测的目标类别列表，如为空则检测所有常见物体
            output_type: 输出类型，支持 'bbox'（边界框）、'points'（点）、'polygon'（多边形）
            normalized: 是否使用归一化坐标
            render: 是否渲染标注结果

        Returns:
            Tuple[bool, Dict[str, Any], str]: (是否成功, 检测结果字典, 错误信息)
        """
        try:
            if not self.is_service_configured():
                return False, {}, "LLM服务未配置"

            # 生成物体识别专用提示词
            prompt = self._generate_object_detection_prompt(targets, output_type, normalized)

            # 调用API
            api_response = self.execute_vision_analysis(image_path, prompt)

            # 解析大模型响应
            result = self._parse_advanced_detection_response(api_response, output_type)

            # 如果需要渲染，生成标注图像
            if render and 'annotations' in result:
                rendered_image = self._render_detection_results(image_path, result)
                result['rendered_image'] = rendered_image

            return True, result, ""

        except Exception as error:
            error_msg = f"大模型物体识别失败: {str(error)}"
            logging_handler.error(error_msg)
            return False, {}, error_msg

    def _generate_object_detection_prompt(self, targets: List[str], output_type: str, normalized: bool) -> str:
        """
        生成物体识别专用提示词

        Args:
            targets: 检测目标列表
            output_type: 输出类型
            normalized: 是否归一化坐标

        Returns:
            str: 生成的提示词
        """
        target_desc = "检测图像中的所有常见物体" if not targets else f"检测以下目标: {', '.join(targets)}"

        prompt = f"""
            你是一个通用物体识别系统，需要：
            - {target_desc}
            - 输出格式：{output_type}
            - 坐标系统：{"归一化坐标[x1, y1, x2, y2]" if normalized else "绝对坐标"}
            - 响应结构必须包含以下字段：
              * status: 处理状态
              * meta: 元数据（模型名称、图像尺寸）
              * annotations: 检测结果数组，每个包含：
                - label: 主标签
                - subLabel: 子标签（可选）
                - type: 标注类型（bbox/point/polygon）
                - coordinates: 坐标数据
                - confidence: 置信度(0-1)
                - position: 位置描述（可选）
                - color: 显示颜色（可选）

            请严格按照JSON格式输出结果，确保坐标精度和数据类型正确。
            """
        return prompt

    def _parse_advanced_detection_response(self, api_response: Dict[str, Any], output_type: str) -> Dict[str, Any]:
        """
        解析大模型物体识别响应

        Args:
            api_response: API响应
            output_type: 输出类型

        Returns:
            Dict[str, Any]: 解析后的结果
        """
        try:
            content = api_response['choices'][0]['message']['content']

            # 尝试从响应中提取JSON
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接查找JSON对象
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                json_str = json_match.group() if json_match else content

            result_data = json.loads(json_str)
            return result_data

        except Exception as error:
            logging_handler.error(f"解析检测响应失败: {error}")
            return {"status": "error", "message": str(error)}

    def _render_detection_results(self, image_path: str, result: Dict[str, Any]) -> str:
        """
        渲染检测结果到图像上

        Args:
            image_path: 原图像路径
            result: 检测结果

        Returns:
            str: Base64编码的渲染后图像
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            import numpy as np

            # 打开原图像
            image = Image.open(image_path).convert('RGB')
            draw = ImageDraw.Draw(image)

            # 获取图像尺寸
            width, height = image.size

            # 绘制每个标注
            for annotation in result.get('annotations', []):
                coords = annotation.get('coordinates', [])
                label = annotation.get('label', '')
                confidence = annotation.get('confidence', 0)

                if annotation.get('type') == 'bbox' and len(coords) >= 4:
                    # 处理边界框
                    if all(0 <= c <= 1 for c in coords):  # 归一化坐标
                        x1, y1, x2, y2 = [c * (width if i % 2 == 0 else height)
                                          for i, c in enumerate(coords[:4])]
                    else:  # 绝对坐标
                        x1, y1, x2, y2 = coords[:4]

                    # 绘制边界框
                    draw.rectangle([x1, y1, x2, y2], outline='red', width=2)

                    # 绘制标签
                    label_text = f"{label} ({confidence:.2f})"
                    draw.text((x1, y1 - 15), label_text, fill='red')

            # 转换为Base64
            import io
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            return base64.b64encode(buffered.getvalue()).decode('utf-8')

        except Exception as error:
            logging_handler.error(f"渲染检测结果失败: {error}")
            return ""

    # ==================== 新增方法：大模型OCR识别 ====================

    def perform_advanced_ocr_recognition(self, image_path: str, languages: List[str] = None,
                                         extract_structures: bool = False,
                                         specific_targets: List[str] = None) -> Tuple[bool, Dict[str, Any], str]:
        """
        执行大模型OCR识别，支持多语言和结构化提取

        Args:
            image_path: 图像文件路径
            languages: 支持的语言列表，如['ch', 'en']（中文、英文）
            extract_structures: 是否提取结构化信息
            specific_targets: 特定提取目标（如只提取金额、日期等）

        Returns:
            Tuple[bool, Dict[str, Any], str]: (是否成功, OCR结果字典, 错误信息)
        """
        try:
            if not self.is_service_configured():
                return False, {}, "LLM服务未配置"

            # 生成OCR专用提示词
            prompt = self._generate_ocr_prompt(languages, extract_structures, specific_targets)

            # 调用API
            api_response = self.execute_vision_analysis(image_path, prompt)

            # 解析OCR响应
            result = self._parse_ocr_response(api_response, extract_structures)

            return True, result, ""

        except Exception as error:
            error_msg = f"大模型OCR识别失败: {str(error)}"
            logging_handler.error(error_msg)
            return False, {}, error_msg

    def _generate_ocr_prompt(self, languages: List[str], extract_structures: bool,
                             specific_targets: List[str]) -> str:
        """
        生成OCR识别专用提示词

        Args:
            languages: 语言列表
            extract_structures: 是否提取结构
            specific_targets: 特定目标

        Returns:
            str: 生成的提示词
        """
        lang_desc = "支持中英日韩等20+语言" if not languages else f"支持语言: {', '.join(languages)}"

        target_desc = "提取所有文本内容"
        if specific_targets:
            target_desc = f"结构化提取以下内容: {', '.join(specific_targets)}"

        prompt = f"""
            你是一个多语言OCR系统，需要：
            - 识别任意方向文本（横向/纵向/倾斜）
            - {lang_desc}
            - {target_desc}
            - 输出格式必须包含：
              * status: 处理状态
              * meta: 元数据
              * text_regions: 文本区域数组，每个包含：
                - text: 识别文本
                - confidence: 置信度
                - bbox: 边界框坐标[x1, y1, x2, y2]
                - language: 语言类型
                - orientation: 文本方向

            {"- 对于结构化数据，请额外提供fields字段，包含提取的键值对" if extract_structures else ""}

            请严格按照JSON格式输出，确保文本识别准确率和坐标精度。
            """
        return prompt

    def _parse_ocr_response(self, api_response: Dict[str, Any], extract_structures: bool) -> Dict[str, Any]:
        """
        解析OCR响应

        Args:
            api_response: API响应
            extract_structures: 是否提取了结构

        Returns:
            Dict[str, Any]: 解析后的OCR结果
        """
        try:
            content = api_response['choices'][0]['message']['content']

            # 提取JSON
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                json_str = json_match.group() if json_match else content

            result_data = json.loads(json_str)
            return result_data

        except Exception as error:
            logging_handler.error(f"解析OCR响应失败: {error}")
            return {"status": "error", "message": str(error)}

    # ==================== 工具方法 ====================

    def batch_process_images(self, image_paths: List[str],
                             task_type: str = "detection",
                             **kwargs) -> List[Tuple[bool, Dict[str, Any], str]]:
        """
        批量处理图像

        Args:
            image_paths: 图像路径列表
            task_type: 任务类型 ('detection' 或 'ocr')
            **kwargs: 额外参数

        Returns:
            List[Tuple[bool, Dict[str, Any], str]]: 每个图像的处理结果
        """
        results = []
        for image_path in image_paths:
            if task_type == "detection":
                result = self.perform_advanced_object_detection(image_path, **kwargs)
            elif task_type == "ocr":
                result = self.perform_advanced_ocr_recognition(image_path, **kwargs)
            else:
                result = (False, {}, f"未知任务类型: {task_type}")
            results.append(result)
        return results
