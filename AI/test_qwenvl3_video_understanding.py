#!/usr/bin/env python3
"""
测试视频理解大模型
根据阿里云百炼平台官方文档编写

API 文档参考：
https://bailian.console.aliyun.com/?spm=5176.29597918.J_C-NDPSQ8SFKWB4aef8i6I.4.298d7b08IRr02o&tab=doc#/doc/?type=model&url=2845871

@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import os
import sys
import base64
import argparse
import json
import cv2
import numpy as np
import requests
from dotenv import load_dotenv
from typing import List, Optional

# 添加AI模块路径
ai_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ai_root)

# 阿里云百炼 API 端点
DASHSCOPE_API_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DASHSCOPE_API_CHAT_URL = f"{DASHSCOPE_API_BASE_URL}/chat/completions"

# 支持的模型名称
SUPPORTED_MODELS = [
    "qwen-vl-plus",
    "qwen-vl-max",
    "qwen-vl-max-latest",
    "qwen3-vl-plus",
    "qwen3-vl-max"
]


def parse_script_args():
    """解析脚本参数"""
    parser = argparse.ArgumentParser(
        description='测试视频理解大模型',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认设置测试视频（Base64编码）
  python test_video_understanding.py /opt/projects/easyaiot/VIDEO/video/video2.mp4

  # 使用公网URL
  python test_video_understanding.py --video-url https://example.com/video.mp4

  # 使用自定义提示词
  python test_video_understanding.py /opt/projects/easyaiot/VIDEO/video/video2.mp4 \\
      --prompt "请详细描述这个视频中的人物、动作和场景"

  # 指定模型
  python test_video_understanding.py /opt/projects/easyaiot/VIDEO/video/video2.mp4 \\
      --model qwen-vl-max-latest
        """
    )
    
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--video-path',
        type=str,
        help='视频文件路径（本地文件）'
    )
    input_group.add_argument(
        '--video-url',
        type=str,
        help='视频文件URL（公网可访问）'
    )
    
    parser.add_argument(
        '--prompt',
        type=str,
        default='请描述这个视频的内容。',
        help='提示词（默认: 请描述这个视频的内容。）'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default='qwen-vl-max-latest',
        choices=SUPPORTED_MODELS,
        help='模型名称（默认: qwen-vl-max-latest）'
    )
    
    parser.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='API Key（如果不提供，将从环境变量 DASHSCOPE_API_KEY 读取）'
    )
    
    parser.add_argument(
        '--env',
        type=str,
        default='',
        help='指定环境配置文件，例如: --env=prod 会加载 .env.prod，默认加载 .env'
    )
    
    return parser.parse_args()


def load_environment(env_suffix: str = ''):
    """加载环境变量"""
    env_file = os.path.join(ai_root, '.env' + (f'.{env_suffix}' if env_suffix else ''))
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"✅ 已加载环境变量文件: {env_file}")
        return True
    else:
        print(f"⚠️  环境变量文件 {env_file} 不存在，尝试使用系统环境变量")
        return False


def get_api_key(provided_key: Optional[str] = None) -> str:
    """获取 API Key"""
    if provided_key:
        return provided_key
    
    api_key = os.getenv('DASHSCOPE_API_KEY')
    if not api_key:
        raise ValueError(
            "未找到 API Key！\n"
            "请通过以下方式之一提供 API Key：\n"
            "1. 使用 --api-key 参数\n"
            "2. 在 .env 文件中设置 DASHSCOPE_API_KEY\n"
            "3. 设置环境变量 DASHSCOPE_API_KEY"
        )
    
    return api_key


def video_file_to_base64(video_path: str) -> str:
    """
    将视频文件转换为 base64 编码
    
    Args:
        video_path: 视频文件路径
    
    Returns:
        base64 编码的字符串
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"视频文件不存在: {video_path}")
    
    with open(video_path, 'rb') as f:
        video_data = f.read()
        video_base64 = base64.b64encode(video_data).decode('utf-8')
    
    # 检查文件大小
    file_size_mb = len(video_data) / (1024 * 1024)
    print(f"✅ 视频文件已转换为 Base64（大小: {file_size_mb:.2f} MB）")
    
    return video_base64


def call_video_understanding_api(
    api_key: str,
    model: str,
    prompt: str,
    video_base64: Optional[str] = None,
    video_url: Optional[str] = None
) -> dict:
    """
    调用视频理解 API
    
    Args:
        api_key: API Key
        model: 模型名称
        prompt: 提示词
        video_base64: 视频文件的 base64 编码
        video_url: 视频文件的公网URL
    
    Returns:
        API 响应结果
    """
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # 构建消息内容
    content = []
    
    # 添加视频内容
    if video_base64:
        # Base64编码模式
        video_content = {
            "type": "video_url",
            "video_url": {
                "url": f"data:video/mp4;base64,{video_base64}"
            }
        }
        content.append(video_content)
        print(f"🎬 使用Base64编码模式")
    elif video_url:
        # 公网URL模式
        video_content = {
            "type": "video_url",
            "video_url": {
                "url": video_url
            }
        }
        content.append(video_content)
        print(f"🌐 使用公网URL模式: {video_url}")
    else:
        raise ValueError("必须提供 video_base64 或 video_url 之一")
    
    # 添加文本提示
    content.append({
        "type": "text",
        "text": prompt
    })
    
    # 构建请求体
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ],
        "stream": True
    }
    
    print(f"🤖 正在调用视频理解 API...")
    print(f"   模型: {model}")
    print(f"   提示词: {prompt}")
    
    # 发送请求
    response = requests.post(
        DASHSCOPE_API_CHAT_URL,
        headers=headers,
        json=payload,
        timeout=300,
        stream=True
    )
    
    response.raise_for_status()
    
    # 处理流式响应
    full_response = ""
    usage_info = None
    
    print(f"\n📝 理解结果:")
    print("-" * 60)
    
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
                        print(content_text, end='', flush=True)
                
                # 提取使用情况
                if 'usage' in data:
                    usage_info = data['usage']
            
            except json.JSONDecodeError:
                continue
    
    print()  # 换行
    print("-" * 60)
    
    # 显示使用情况
    if usage_info:
        print(f"\n📊 Token 使用情况:")
        print(f"   提示词 tokens: {usage_info.get('prompt_tokens', 'N/A')}")
        print(f"   完成 tokens: {usage_info.get('completion_tokens', 'N/A')}")
        print(f"   总 tokens: {usage_info.get('total_tokens', 'N/A')}")
    
    return {
        'response': full_response,
        'usage': usage_info
    }


def main():
    """主函数"""
    args = parse_script_args()
    
    # 加载环境变量
    load_environment(args.env)
    
    # 获取 API Key
    try:
        api_key = get_api_key(args.api_key)
    except ValueError as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)
    
    print("=" * 60)
    print("视频理解测试")
    print("=" * 60)
    print()
    
    try:
        video_base64 = None
        video_url = None
        
        if args.video_path:
            # 使用本地视频文件
            if not os.path.exists(args.video_path):
                print(f"❌ 错误: 视频文件不存在: {args.video_path}")
                sys.exit(1)
            
            print("📹 正在读取视频文件...")
            video_base64 = video_file_to_base64(args.video_path)
        elif args.video_url:
            # 使用公网URL
            video_url = args.video_url
            print(f"🌐 使用视频URL: {video_url}")
        
        # 调用 API
        result = call_video_understanding_api(
            api_key=api_key,
            model=args.model,
            prompt=args.prompt,
            video_base64=video_base64,
            video_url=video_url
        )
        
        print(f"\n" + "=" * 60)
        print("✅ 测试完成！")
        print("=" * 60)
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ API 请求失败: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"   错误详情: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
            except:
                print(f"   响应内容: {e.response.text[:500]}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
