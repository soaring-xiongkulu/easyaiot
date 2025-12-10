#!/usr/bin/env python3
"""
测试视频深度思考大模型
根据阿里云百炼平台官方文档编写

API 文档参考：
https://bailian.console.aliyun.com/?spm=5176.29597918.J_C-NDPSQ8SFKWB4aef8i6I.4.298d7b08IRr02o&tab=doc#/doc/?type=model&url=2870973

@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import os
import sys
import base64
import argparse
import json
import requests
from dotenv import load_dotenv
from typing import Optional

# 添加VIDEO模块路径
video_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, video_root)

# 阿里云百炼 API 端点
DASHSCOPE_API_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DASHSCOPE_API_CHAT_URL = f"{DASHSCOPE_API_BASE_URL}/chat/completions"

# 支持的模型名称（深度思考模式）
SUPPORTED_MODELS = [
    "qwen-vl-plus",
    "qwen-vl-max",
    "qwen-vl-max-latest",
    "qwen3-vl-plus",
    "qwen3-vl-max",
    "qwen3-max-preview"
]


def parse_script_args():
    """解析脚本参数"""
    parser = argparse.ArgumentParser(
        description='测试视频深度思考大模型',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认设置测试视频（Base64编码）
  python test_video_deep_thinking.py /opt/projects/easyaiot/VIDEO/video/video2.mp4

  # 使用公网URL
  python test_video_deep_thinking.py --video-url https://example.com/video.mp4

  # 使用自定义提示词进行深度思考
  python test_video_deep_thinking.py /opt/projects/easyaiot/VIDEO/video/video2.mp4 \\
      --prompt "请对这个视频进行多角度深度分析"

  # 指定模型
  python test_video_deep_thinking.py /opt/projects/easyaiot/VIDEO/video/video2.mp4 \\
      --model qwen3-max-preview

  # 关闭思考模式（仅对支持混合思考的模型有效）
  python test_video_deep_thinking.py /opt/projects/easyaiot/VIDEO/video/video2.mp4 \\
      --disable-thinking
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
        default='请对这个视频进行多角度深度分析和思考。',
        help='提示词（默认: 请对这个视频进行多角度深度分析和思考。）'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default='qwen3-max-preview',
        choices=SUPPORTED_MODELS,
        help='模型名称（默认: qwen3-max-preview）'
    )
    
    parser.add_argument(
        '--disable-thinking',
        action='store_true',
        help='关闭思考模式（仅对支持混合思考的模型有效）'
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
    env_file = os.path.join(video_root, '.env' + (f'.{env_suffix}' if env_suffix else ''))
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


def call_video_deep_thinking_api(
    api_key: str,
    model: str,
    prompt: str,
    video_base64: Optional[str] = None,
    video_url: Optional[str] = None,
    enable_thinking: bool = True
) -> dict:
    """
    调用视频深度思考 API
    
    Args:
        api_key: API Key
        model: 模型名称
        prompt: 提示词
        video_base64: 视频文件的 base64 编码
        video_url: 视频文件的公网URL
        enable_thinking: 是否启用思考模式
    
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
    
    # 添加文本提示（深度思考模式：更注重多角度分析和推理）
    thinking_prompt = f"作为深度思考专家，请对这个视频进行多角度深度分析：{prompt}"
    content.append({
        "type": "text",
        "text": thinking_prompt
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
        "stream": True,
        "stream_options": {
            "include_usage": True
        }
    }
    
    # 添加思考模式参数
    # 注意：enable_thinking 是阿里云百炼的非标准参数，需要通过 extra_body 传入
    # 但 requests 库不支持 extra_body，我们尝试直接在 payload 中添加
    # 如果模型支持混合思考模式，可以通过此参数控制
    if enable_thinking:
        # 尝试在 payload 中添加 enable_thinking 参数
        # 某些API实现可能支持这种方式
        payload["enable_thinking"] = True
    
    print(f"🤖 正在调用视频深度思考 API...")
    print(f"   模型: {model}")
    print(f"   提示词: {prompt}")
    print(f"   思考模式: {'启用' if enable_thinking else '关闭'}")
    
    # 发送请求
    # 如果 enable_thinking 参数在 payload 中不起作用，可能需要使用 OpenAI SDK
    # 或者通过其他方式传递参数
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
    thinking_content = ""
    usage_info = None
    
    print(f"\n📝 思考过程:")
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
                
                # 提取思考内容（reasoning_content）
                if 'choices' in data and len(data['choices']) > 0:
                    choice = data['choices'][0]
                    
                    # 思考内容
                    if 'delta' in choice:
                        delta = choice['delta']
                        if 'reasoning_content' in delta:
                            thinking_text = delta['reasoning_content']
                            thinking_content += thinking_text
                            print(f"[思考] {thinking_text}", end='', flush=True)
                    
                    # 回复内容
                    delta = choice.get('delta', {})
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
    
    # 显示思考内容总结
    if thinking_content:
        print(f"\n💭 思考内容摘要:")
        print(f"   {thinking_content[:200]}..." if len(thinking_content) > 200 else thinking_content)
    
    # 显示使用情况
    if usage_info:
        print(f"\n📊 Token 使用情况:")
        print(f"   提示词 tokens: {usage_info.get('prompt_tokens', 'N/A')}")
        print(f"   完成 tokens: {usage_info.get('completion_tokens', 'N/A')}")
        print(f"   总 tokens: {usage_info.get('total_tokens', 'N/A')}")
    
    return {
        'response': full_response,
        'thinking': thinking_content,
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
    print("视频深度思考测试")
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
        result = call_video_deep_thinking_api(
            api_key=api_key,
            model=args.model,
            prompt=args.prompt,
            video_base64=video_base64,
            video_url=video_url,
            enable_thinking=not args.disable_thinking
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
