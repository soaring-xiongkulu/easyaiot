#!/usr/bin/env python3
"""
测试 QwenVL3 视频理解大模型
根据阿里云百炼平台官方文档编写

API 文档参考：
https://bailian.console.aliyun.com/?spm=5176.29597918.J_C-NDPSQ8SFKWB4aef8i6I.1.298d7b08IRr02o&tab=doc#/doc/?type=model&url=2877996

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

# 添加VIDEO模块路径
video_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, video_root)

# 阿里云百炼 API 端点
DASHSCOPE_API_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DASHSCOPE_API_CHAT_URL = f"{DASHSCOPE_API_BASE_URL}/chat/completions"

# 支持的模型名称
SUPPORTED_MODELS = [
    "qwen-vl-plus",
    "qwen-vl-max",
    "qwen3-vl-plus",
    "qwen3-vl-max"
]


def parse_script_args():
    """解析脚本参数"""
    parser = argparse.ArgumentParser(
        description='测试 QwenVL3 视频理解大模型',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认设置测试视频（提取多帧作为图片列表）
  python test_qwenvl3_video.py /opt/projects/easyaiot/VIDEO/video/video2.mp4

  # 指定提取的帧数
  python test_qwenvl3_video.py /opt/projects/easyaiot/VIDEO/video/video2.mp4 --num-frames 8

  # 使用自定义提示词
  python test_qwenvl3_video.py /opt/projects/easyaiot/VIDEO/video/video2.mp4 \\
      --prompt "请详细描述这个视频中的人物、动作和场景"

  # 使用视频文件直接上传（Base64编码，适用于小文件）
  python test_qwenvl3_video.py /opt/projects/easyaiot/VIDEO/video/video2.mp4 \\
      --use-video-file

  # 指定模型
  python test_qwenvl3_video.py /opt/projects/easyaiot/VIDEO/video/video2.mp4 \\
      --model qwen-vl-plus

  # 保存提取的帧到文件
  python test_qwenvl3_video.py /opt/projects/easyaiot/VIDEO/video/video2.mp4 \\
      --save-frames
        """
    )
    
    parser.add_argument(
        'video_path',
        type=str,
        help='视频文件路径'
    )
    
    parser.add_argument(
        '--num-frames',
        type=int,
        default=4,
        help='从视频中提取的帧数（默认: 4，用于图片列表模式）'
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
        default='qwen-vl-plus',
        choices=SUPPORTED_MODELS,
        help='模型名称（默认: qwen-vl-plus）'
    )
    
    parser.add_argument(
        '--use-video-file',
        action='store_true',
        help='直接使用视频文件（Base64编码），而不是提取帧作为图片列表'
    )
    
    parser.add_argument(
        '--save-frames',
        action='store_true',
        help='保存提取的帧到文件（保存为 test_frame_0.jpg, test_frame_1.jpg 等）'
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


def extract_frames_from_video(video_path: str, num_frames: int = 4) -> List[np.ndarray]:
    """
    从视频中提取多帧
    
    Args:
        video_path: 视频文件路径
        num_frames: 要提取的帧数
    
    Returns:
        提取的帧列表（numpy数组）
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"视频文件不存在: {video_path}")
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"无法打开视频文件: {video_path}")
    
    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps if fps > 0 else 0
        
        print(f"📹 视频信息:")
        print(f"   总帧数: {total_frames}")
        print(f"   帧率: {fps:.2f} fps")
        print(f"   分辨率: {width}x{height}")
        print(f"   时长: {duration:.2f} 秒")
        
        # 计算要提取的帧索引（均匀分布）
        if num_frames >= total_frames:
            frame_indices = list(range(total_frames))
        else:
            step = total_frames / (num_frames + 1)
            frame_indices = [int(step * (i + 1)) for i in range(num_frames)]
        
        frames = []
        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
                print(f"   ✅ 提取第 {idx} 帧")
            else:
                print(f"   ⚠️  无法读取第 {idx} 帧")
        
        if not frames:
            raise ValueError("未能提取任何帧")
        
        print(f"✅ 成功提取 {len(frames)} 帧")
        return frames
        
    finally:
        cap.release()


def frame_to_base64(frame: np.ndarray, quality: int = 95) -> str:
    """
    将 OpenCV 帧转换为 base64 编码的 JPEG 图像
    
    Args:
        frame: OpenCV 帧（numpy数组）
        quality: JPEG 质量 (1-100)
    
    Returns:
        base64 编码的字符串（不含 data URI 前缀）
    """
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
    success, buffer = cv2.imencode('.jpg', frame, encode_params)
    
    if not success:
        raise ValueError("无法编码图像为 JPEG")
    
    image_base64 = base64.b64encode(buffer).decode('utf-8')
    return image_base64


def video_file_to_base64(video_path: str) -> str:
    """
    将视频文件转换为 base64 编码
    
    Args:
        video_path: 视频文件路径
    
    Returns:
        base64 编码的字符串
    """
    with open(video_path, 'rb') as f:
        video_data = f.read()
        video_base64 = base64.b64encode(video_data).decode('utf-8')
    
    # 检查文件大小（Base64编码后不超过10MB）
    file_size_mb = len(video_data) / (1024 * 1024)
    if file_size_mb > 10:
        raise ValueError(
            f"视频文件过大 ({file_size_mb:.2f} MB)，Base64编码模式仅支持不超过10MB的文件。\n"
            "请使用 --num-frames 参数提取帧作为图片列表，或使用公网URL。"
        )
    
    print(f"✅ 视频文件已转换为 Base64（大小: {file_size_mb:.2f} MB）")
    return video_base64


def call_qwenvl3_video_api(
    api_key: str,
    model: str,
    prompt: str,
    video_frames: Optional[List[str]] = None,
    video_base64: Optional[str] = None
) -> dict:
    """
    调用 QwenVL3 视频理解 API
    
    Args:
        api_key: API Key
        model: 模型名称
        prompt: 提示词
        video_frames: 视频帧的 base64 列表（图片列表模式）
        video_base64: 视频文件的 base64 编码（视频文件模式）
    
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
    if video_frames:
        # 图片列表模式：将视频帧作为图片列表
        video_content = {
            "type": "video",
            "video": [f"data:image/jpeg;base64,{frame}" for frame in video_frames]
        }
        content.append(video_content)
        print(f"📸 使用图片列表模式（{len(video_frames)} 帧）")
    elif video_base64:
        # 视频文件模式：直接使用视频文件的 Base64 编码
        video_content = {
            "type": "video",
            "video": f"data:video/mp4;base64,{video_base64}"
        }
        content.append(video_content)
        print(f"🎬 使用视频文件模式（Base64编码）")
    else:
        raise ValueError("必须提供 video_frames 或 video_base64 之一")
    
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
        "modalities": ["text"],
        "stream": True
    }
    
    print(f"🤖 正在调用 QwenVL3 API...")
    print(f"   模型: {model}")
    print(f"   提示词: {prompt}")
    
    # 发送请求
    response = requests.post(
        DASHSCOPE_API_CHAT_URL,
        headers=headers,
        json=payload,
        timeout=120,
        stream=True
    )
    
    response.raise_for_status()
    
    # 处理流式响应
    full_response = ""
    usage_info = None
    
    print(f"\n📝 推理结果:")
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
    
    # 检查视频文件
    if not os.path.exists(args.video_path):
        print(f"❌ 错误: 视频文件不存在: {args.video_path}")
        sys.exit(1)
    
    print("=" * 60)
    print("QwenVL3 视频理解测试")
    print("=" * 60)
    print()
    
    try:
        if args.use_video_file:
            # 使用视频文件模式
            print("📹 正在读取视频文件...")
            video_base64 = video_file_to_base64(args.video_path)
            
            # 调用 API
            result = call_qwenvl3_video_api(
                api_key=api_key,
                model=args.model,
                prompt=args.prompt,
                video_base64=video_base64
            )
        else:
            # 使用图片列表模式（提取帧）
            print("📹 正在从视频中提取帧...")
            frames = extract_frames_from_video(args.video_path, args.num_frames)
            
            # 保存帧（可选）
            if args.save_frames:
                for i, frame in enumerate(frames):
                    frame_path = os.path.join(video_root, f'test_frame_{i}.jpg')
                    cv2.imwrite(frame_path, frame)
                    print(f"💾 已保存帧到: {frame_path}")
            
            # 转换为 base64
            print(f"\n🔄 正在将帧转换为 base64...")
            video_frames_base64 = [frame_to_base64(frame) for frame in frames]
            print(f"✅ 转换完成，共 {len(video_frames_base64)} 帧")
            
            # 调用 API
            result = call_qwenvl3_video_api(
                api_key=api_key,
                model=args.model,
                prompt=args.prompt,
                video_frames=video_frames_base64
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
