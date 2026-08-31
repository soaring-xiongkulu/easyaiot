"""
大模型预置模板数据播种 — 一键部署初始化时按厂商模板各建一条可用的接入配置。

- 这些是真实可用的厂商模板数据（端点/模型/参数已按各厂商最佳实践预置），只差填入真实 API 密钥；
- 密钥统一为占位符（sk-placeholder-*，非真实 key），激活/测试接口会拦截并引导用户填入真实密钥；
- 仅当 llm_config 表完全为空时播种，绝不混入已有真实数据；
- 预置识别不落库（零迁移）：以 api_key 前缀 sk-placeholder- 派生 is_preset 标记，填入真实密钥后自动消失。
"""
import logging

from app.config.llm_templates import resolve_template

logger = logging.getLogger(__name__)

# 占位密钥统一前缀；预置模板识别与激活拦截均以此为准
PLACEHOLDER_API_KEY_PREFIX = 'sk-placeholder-'


def is_placeholder_api_key(api_key) -> bool:
    """是否为预置模板的占位密钥（None 不算）。"""
    return bool(api_key and str(api_key).startswith(PLACEHOLDER_API_KEY_PREFIX))


# 每个可预置端点的厂商模板一条配置；anthropic/custom 无预置 base_url，不播种
LLM_PRESET_MODELS = [
    {
        'name': 'DeepSeek 模板',
        'vendor': 'deepseek',
        'model_name': 'deepseek-v4-flash',
        'model_type': 'text',
        'temperature': 0.7,
        'max_tokens': 2000,
        'timeout': 60,
        'description': '预置模板：端点与参数已配置好，填入真实 API 密钥后即可启用',
    },
    {
        'name': '阿里云百炼 模板',
        'vendor': 'dashscope',
        'model_name': 'qwen3-vl-plus',
        'model_type': 'vision',
        'temperature': 0.7,
        'max_tokens': 2000,
        'timeout': 60,
        'description': '预置模板：端点与参数已配置好，填入真实 API 密钥后即可启用',
    },
    {
        'name': '智谱 GLM 模板',
        'vendor': 'zhipu',
        'model_name': 'glm-5.3',
        'model_type': 'text',
        'temperature': 0.7,
        'max_tokens': 2000,
        'timeout': 60,
        'description': '预置模板：端点与参数已配置好，填入真实 API 密钥后即可启用',
    },
    {
        'name': 'OpenAI 模板',
        'vendor': 'openai',
        'model_name': 'gpt-5.4-mini',
        'model_type': 'vision',
        'temperature': 0.7,
        'max_tokens': 2000,
        'timeout': 90,
        'description': '预置模板：端点与参数已配置好，填入真实 API 密钥后即可启用',
    },
    {
        'name': 'Kimi 模板',
        'vendor': 'kimi',
        'model_name': 'kimi-k2.6',
        'model_type': 'text',
        'temperature': 1.0,  # K2 系列强制 temperature=1
        'max_tokens': 2000,
        'timeout': 90,
        'description': '预置模板：端点与参数已配置好，填入真实 API 密钥后即可启用',
    },
    {
        'name': 'Claude 模板',
        'vendor': 'claude',
        'model_name': 'claude-sonnet-4-5',
        'model_type': 'text',
        'temperature': 0.7,
        'max_tokens': 2000,
        'timeout': 90,
        'description': '预置模板：Claude 官方为 /v1/messages 协议，需填写 OpenAI 兼容网关/中转端点与真实 API 密钥后启用',
    },
]


def ensure_llm_template_seed() -> dict:
    """llm_config 表为空时播种预置模板数据（幂等，重复启动不重复插入）。"""
    from db_models import LLMModel, db

    result = {'inserted': 0, 'skipped': 0}
    try:
        if LLMModel.query.first() is not None:
            result['skipped'] = len(LLM_PRESET_MODELS)
            return result  # 已有真实数据，绝不混入预置数据
        for item in LLM_PRESET_MODELS:
            if LLMModel.query.filter_by(name=item['name']).first() is not None:
                result['skipped'] += 1
                continue
            template = resolve_template(item['vendor'])
            model = LLMModel(
                name=item['name'],
                service_type='online',
                vendor=item['vendor'],
                model_type=item.get('model_type', 'vision'),
                model_name=item['model_name'],
                base_url=template.base_url if template else '',
                api_key=f"{PLACEHOLDER_API_KEY_PREFIX}{item['vendor']}",
                temperature=item.get('temperature', 0.7),
                max_tokens=item.get('max_tokens', 2000),
                timeout=item.get('timeout', 60),
                is_active=False,
                status='inactive',
                description=item['description'],
            )
            db.session.add(model)
            result['inserted'] += 1
        db.session.commit()
        if result['inserted']:
            logger.info(f"已播种 {result['inserted']} 条大模型预置模板数据（占位密钥 sk-placeholder-*，填入真实密钥后启用）")
    except Exception as e:
        db.session.rollback()
        logger.error(f"播种大模型预置模板数据失败: {str(e)}")
        result['error'] = str(e)
    return result
