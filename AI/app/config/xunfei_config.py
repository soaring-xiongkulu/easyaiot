"""
@author 翱翔的雄库鲁
讯飞语音识别API配置
"""

import os
from typing import Optional

# 讯飞语音识别API配置
XUNFEI_APP_ID = os.getenv('XUNFEI_APP_ID', '你的APP_ID')
XUNFEI_SECRET_KEY = os.getenv('XUNFEI_SECRET_KEY', '你的SECRET_KEY')

# API地址配置
XUNFEI_BASE_URL = "https://raasr.xfyun.cn/v2/api"
XUNFEI_UPLOAD_URL = f"{XUNFEI_BASE_URL}/upload"
XUNFEI_RESULT_URL = f"{XUNFEI_BASE_URL}/getResult"

# 默认配置
DEFAULT_LANGUAGE = "cn"  # 默认中文识别
DEFAULT_SAMPLE_RATE = 16000  # 16kHz采样率适合语音识别
DEFAULT_CHANNELS = 1  # 单声道
DEFAULT_AUDIO_FORMAT = "wav"  # WAV格式

# 超时配置
UPLOAD_TIMEOUT = 60  # 上传超时时间（秒）
RESULT_TIMEOUT = 30  # 查询结果超时时间（秒）
MAX_WAIT_TIME = 300  # 最大等待时间（秒）
POLL_INTERVAL = 3  # 轮询间隔（秒）

# 音频文件限制
MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50MB
MAX_AUDIO_DURATION = 600  # 10分钟

# 支持的语言类型
SUPPORTED_LANGUAGES = {
    'cn': '中文（通用方言）',
    'en': '英文',
    'ja': '日语',
    'ko': '韩语',
    'ru': '俄语',
    'fr': '法语',
    'es': '西班牙语',
    'vi': '越南语',
    'ar': '阿拉伯语',
    'cn_xinanese': '西南官话',
    'cn_cantonese': '粤语',
    'cn_henanese': '河南话',
    'cn_uyghur': '维吾尔语',
    'cn_tibetan': '藏语',
    'de': '德语',
    'it': '意大利语',
    'pt': '葡萄牙语',
    'th': '泰语',
    'hi': '印地语'
}

# 支持的音频格式
SUPPORTED_AUDIO_FORMATS = ['wav', 'mp3', 'm4a', 'aac', 'flac', 'speex']

# FFmpeg配置
FFMPEG_EXECUTABLE = os.getenv('FFMPEG_PATH', 'ffmpeg')  # FFmpeg可执行文件路径
FFPROBE_EXECUTABLE = os.getenv('FFPROBE_PATH', 'ffprobe')  # FFprobe可执行文件路径


def get_xunfei_config() -> dict:
    """
    获取讯飞API配置
    
    Returns:
        配置字典
    """
    return {
        'app_id': XUNFEI_APP_ID,
        'secret_key': XUNFEI_SECRET_KEY,
        'base_url': XUNFEI_BASE_URL,
        'upload_url': XUNFEI_UPLOAD_URL,
        'result_url': XUNFEI_RESULT_URL,
        'default_language': DEFAULT_LANGUAGE,
        'default_sample_rate': DEFAULT_SAMPLE_RATE,
        'default_channels': DEFAULT_CHANNELS,
        'default_audio_format': DEFAULT_AUDIO_FORMAT,
        'upload_timeout': UPLOAD_TIMEOUT,
        'result_timeout': RESULT_TIMEOUT,
        'max_wait_time': MAX_WAIT_TIME,
        'poll_interval': POLL_INTERVAL,
        'max_audio_size': MAX_AUDIO_SIZE,
        'max_audio_duration': MAX_AUDIO_DURATION,
        'supported_languages': SUPPORTED_LANGUAGES,
        'supported_audio_formats': SUPPORTED_AUDIO_FORMATS,
        'ffmpeg_executable': FFMPEG_EXECUTABLE,
        'ffprobe_executable': FFPROBE_EXECUTABLE
    }


def validate_language(language: str) -> bool:
    """
    验证语言类型是否支持
    
    Args:
        language: 语言代码
        
    Returns:
        True如果支持，False否则
    """
    return language in SUPPORTED_LANGUAGES


def validate_audio_format(format_name: str) -> bool:
    """
    验证音频格式是否支持
    
    Args:
        format_name: 音频格式名称
        
    Returns:
        True如果支持，False否则
    """
    return format_name.lower() in SUPPORTED_AUDIO_FORMATS


def get_language_description(language: str) -> Optional[str]:
    """
    获取语言类型的描述
    
    Args:
        language: 语言代码
        
    Returns:
        语言描述，如果不支持返回None
    """
    return SUPPORTED_LANGUAGES.get(language)


if __name__ == "__main__":
    # 测试配置
    config = get_xunfei_config()
    print("讯飞语音识别配置:")
    for key, value in config.items():
        if key not in ['secret_key']:  # 不显示敏感信息
            print(f"  {key}: {value}")
    
    print(f"\n支持的语言数量: {len(SUPPORTED_LANGUAGES)}")
    print(f"支持的音频格式: {SUPPORTED_AUDIO_FORMATS}")
