"""
大模型接入模板注册表 — 厂商差异收敛为「OpenAI 兼容协议 + 预置端点模板」。

新增厂商 = 在 LLM_TEMPLATES 加一个条目，零代码改动；
vendor 字段仅作为模板标识存储与展示，不再驱动任何调用分支。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class LLMTemplate:
    key: str                              # 模板标识，写回 LLMModel.vendor
    label: str                            # 页面显示名
    base_url: str                         # 预填 OpenAI 兼容端点（/v1 根地址，可为空由用户填写）
    doc_url: str = ''                     # 控制台/获取 Key 文档
    builtin_models: Tuple[str, ...] = ()  # 常见模型 ID 建议


LLM_TEMPLATES: Dict[str, LLMTemplate] = {
    'deepseek': LLMTemplate(
        key='deepseek', label='DeepSeek',
        base_url='https://api.deepseek.com/v1',
        doc_url='https://platform.deepseek.com/',
        builtin_models=('deepseek-v4-flash', 'deepseek-v4-pro', 'deepseek-v4-flash-vision-exp'),
    ),
    'dashscope': LLMTemplate(
        key='dashscope', label='阿里云百炼',
        base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
        doc_url='https://bailian.console.aliyun.com/',
        builtin_models=('qwen3.8-max', 'qwen3.8-max-preview', 'qwen3.7-max', 'qwen3.7-plus', 'qwen3.7-flash', 'qwen3.6-max-preview', 'qwen3.6-plus', 'qwen3.6-flash', 'qwen3.5-plus', 'qwen3.5-flash', 'qwen3.5-omni-plus', 'qwen3.5-omni-flash', 'qwen3-vl-plus', 'qwen3-vl-flash', 'qwen-vl-max'),
    ),
    'zhipu': LLMTemplate(
        key='zhipu', label='智谱 GLM',
        base_url='https://open.bigmodel.cn/api/paas/v4',
        doc_url='https://open.bigmodel.cn/',
        builtin_models=(
            'glm-5.3', 'glm-5.3-flash', 'glm-5.2', 'glm-5.1', 'glm-5-turbo', 'glm-5',
            'glm-4.7', 'glm-4.7-flashx', 'glm-4.7-flash', 'glm-4.6',
            'glm-4.5', 'glm-4.5-air', 'glm-4.5-airx', 'glm-4.5-flash',
            'glm-4-plus', 'glm-4-long', 'glm-4-air', 'glm-4-airx',
            'glm-4-flashx-250414', 'glm-4-flash-250414', 'glm-4-flash',
            'glm-5v-turbo', 'glm-4.6v', 'glm-4.6v-flash', 'glm-4.5v',
            'glm-4.1v-thinking-flashx', 'glm-4.1v-thinking-flash',
            'glm-4v-plus', 'glm-4v-flash', 'glm-ocr',
        ),
    ),
    'openai': LLMTemplate(
        key='openai', label='OpenAI',
        base_url='https://api.openai.com/v1',
        doc_url='https://platform.openai.com/',
        builtin_models=('gpt-5.6-sol', 'gpt-5.6', 'gpt-5.6-sol-pro', 'gpt-5.6-terra', 'gpt-5.6-luna', 'gpt-5.5', 'gpt-5.4-mini', 'gpt-4.1-mini'),
    ),
    'kimi': LLMTemplate(
        key='kimi', label='Kimi（月之暗面）',
        base_url='https://api.moonshot.cn/v1',
        doc_url='https://platform.moonshot.cn/',
        builtin_models=('kimi-k2.6', 'kimi-k2.7-code'),
    ),
    'anthropic': LLMTemplate(
        key='anthropic', label='Anthropic 兼容',
        base_url='',
        doc_url='https://console.anthropic.com/',
        builtin_models=(),
        # 官方 /v1/messages 协议不在支持范围；base_url 需填 OpenAI 兼容网关端点
    ),
    'claude': LLMTemplate(
        key='claude', label='Claude（Anthropic）',
        base_url='',
        doc_url='https://console.anthropic.com/',
        builtin_models=('claude-opus-4-7', 'claude-opus-4-6', 'claude-opus-4-5', 'claude-sonnet-4-6', 'claude-sonnet-4-5', 'claude-haiku-4-5'),
        # Claude 官方 API 为 /v1/messages 协议，需通过 OpenAI 兼容网关/中转接入；
        # base_url 填中转站的 OpenAI 兼容端点（如 https://xxx/v1）
    ),
    'custom': LLMTemplate(
        key='custom', label='自定义 OpenAI 兼容',
        base_url='',
        builtin_models=(),
    ),
}

def resolve_template(vendor: str) -> Optional[LLMTemplate]:
    """按模板 key 解析模板，未知返回 None。"""
    return LLM_TEMPLATES.get(vendor)


def list_templates() -> list:
    """模板列表（前端下拉用）。"""
    return [t.__dict__ | {'builtin_models': list(t.builtin_models)} for t in LLM_TEMPLATES.values()]
