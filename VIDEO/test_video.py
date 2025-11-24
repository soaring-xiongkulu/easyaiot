#!/usr/bin/env python3
"""
视频推流测试脚本
使用 ffmpeg 循环推流视频文件到 RTMP 服务器
"""
import os
import sys
import subprocess
import signal
import time
import argparse
from pathlib import Path

# 获取脚本所在目录
SCRIPT_DIR = Path(__file__).parent.absolute()
VIDEO_DIR = SCRIPT_DIR / "video"
VIDEO_FILE = VIDEO_DIR / "video1.mp4"
RTMP_URL = "rtmp://localhost:1935/live/video1"

# 全局变量用于存储 ffmpeg 进程
ffmpeg_process = None


def check_ffmpeg():
    """检查 ffmpeg 是否已安装"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✅ ffmpeg 已安装")
            # 打印版本信息的第一行
            version_line = result.stdout.split('\n')[0]
            print(f"   {version_line}")
            return True
        else:
            print("❌ ffmpeg 未正确安装")
            return False
    except FileNotFoundError:
        print("❌ ffmpeg 未安装，请先安装 ffmpeg")
        print("   Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("   macOS: brew install ffmpeg")
        print("   Windows: 从 https://ffmpeg.org/download.html 下载")
        return False
    except Exception as e:
        print(f"❌ 检查 ffmpeg 时出错: {str(e)}")
        return False


def check_video_file():
    """检查视频文件是否存在"""
    if not VIDEO_FILE.exists():
        print(f"❌ 视频文件不存在: {VIDEO_FILE}")
        print(f"   请确保文件存在于: {VIDEO_DIR}")
        return False
    print(f"✅ 视频文件存在: {VIDEO_FILE}")
    return True


def start_streaming(rtmp_url=None, video_file=None, loop=True, log_level="info"):
    """
    启动视频推流
    
    Args:
        rtmp_url: RTMP 推流地址，默认为 rtmp://localhost:1935/live/video1
        video_file: 视频文件路径，默认为 VIDEO/video/video1.mp4
        loop: 是否循环播放，默认为 True
        log_level: ffmpeg 日志级别，默认为 info
    """
    global ffmpeg_process
    
    if rtmp_url is None:
        rtmp_url = RTMP_URL
    if video_file is None:
        video_file = VIDEO_FILE
    
    # 构建 ffmpeg 命令
    cmd = [
        "ffmpeg",
        "-re",  # 以原始帧率读取输入
        "-stream_loop", "-1" if loop else "0",  # -1 表示无限循环，0 表示不循环
        "-i", str(video_file),  # 输入文件
        "-c:v", "libx264",  # 视频编码器
        "-preset", "veryfast",  # 编码速度预设
        "-tune", "zerolatency",  # 零延迟调优
        "-c:a", "aac",  # 音频编码器
        "-b:v", "2000k",  # 视频比特率
        "-b:a", "128k",  # 音频比特率
        "-f", "flv",  # 输出格式
        "-loglevel", log_level,  # 日志级别
        rtmp_url  # RTMP 推流地址
    ]
    
    print(f"\n🚀 开始推流...")
    print(f"   视频文件: {video_file}")
    print(f"   推流地址: {rtmp_url}")
    print(f"   循环播放: {'是' if loop else '否'}")
    print(f"\n📺 推流命令: {' '.join(cmd)}\n")
    
    try:
        # 启动 ffmpeg 进程
        ffmpeg_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        print(f"✅ 推流进程已启动 (PID: {ffmpeg_process.pid})")
        print(f"   按 Ctrl+C 停止推流\n")
        
        # 实时输出 stderr（ffmpeg 的输出在 stderr）
        while True:
            if ffmpeg_process.poll() is not None:
                # 进程已结束
                stderr_output = ffmpeg_process.stderr.read()
                if stderr_output:
                    print("\n📋 ffmpeg 输出:")
                    print(stderr_output)
                break
            
            # 读取一行错误输出
            line = ffmpeg_process.stderr.readline()
            if line:
                # 过滤掉一些不重要的信息
                if log_level == "error" or "error" in line.lower() or "warning" in line.lower():
                    print(line.strip())
            
            time.sleep(0.1)
        
        # 检查退出码
        return_code = ffmpeg_process.returncode
        if return_code != 0:
            print(f"\n❌ 推流进程异常退出 (退出码: {return_code})")
        else:
            print(f"\n✅ 推流进程正常退出")
        
    except KeyboardInterrupt:
        print("\n\n🛑 收到停止信号，正在停止推流...")
        stop_streaming()
    except Exception as e:
        print(f"\n❌ 推流过程中出错: {str(e)}")
        stop_streaming()
        sys.exit(1)


def stop_streaming():
    """停止推流"""
    global ffmpeg_process
    
    if ffmpeg_process is not None:
        try:
            # 发送 SIGTERM 信号
            ffmpeg_process.terminate()
            
            # 等待进程结束，最多等待 5 秒
            try:
                ffmpeg_process.wait(timeout=5)
                print("✅ 推流进程已停止")
            except subprocess.TimeoutExpired:
                # 如果 5 秒后还没结束，强制杀死
                print("⚠️  进程未响应，强制终止...")
                ffmpeg_process.kill()
                ffmpeg_process.wait()
                print("✅ 推流进程已强制停止")
        except Exception as e:
            print(f"❌ 停止推流时出错: {str(e)}")
        finally:
            ffmpeg_process = None


def signal_handler(sig, frame):
    """信号处理器，用于优雅退出"""
    print("\n\n🛑 收到中断信号")
    stop_streaming()
    sys.exit(0)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='视频推流测试脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认配置推流
  python test_video.py
  
  # 指定自定义 RTMP 地址
  python test_video.py --rtmp rtmp://192.168.1.100:1935/live/stream1
  
  # 指定自定义视频文件
  python test_video.py --video /path/to/video.mp4
  
  # 不循环播放（只播放一次）
  python test_video.py --no-loop
  
  # 显示详细日志
  python test_video.py --log-level debug
        """
    )
    
    parser.add_argument(
        '--rtmp',
        type=str,
        default=RTMP_URL,
        help=f'RTMP 推流地址 (默认: {RTMP_URL})'
    )
    
    parser.add_argument(
        '--video',
        type=str,
        default=str(VIDEO_FILE),
        help=f'视频文件路径 (默认: {VIDEO_FILE})'
    )
    
    parser.add_argument(
        '--no-loop',
        action='store_true',
        help='不循环播放（只播放一次）'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['quiet', 'panic', 'fatal', 'error', 'warning', 'info', 'verbose', 'debug', 'trace'],
        default='info',
        help='ffmpeg 日志级别 (默认: info)'
    )
    
    args = parser.parse_args()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 60)
    print("📹 视频推流测试工具")
    print("=" * 60)
    
    # 检查依赖
    if not check_ffmpeg():
        sys.exit(1)
    
    # 检查视频文件
    video_path = Path(args.video)
    if not video_path.exists():
        print(f"❌ 视频文件不存在: {video_path}")
        sys.exit(1)
    print(f"✅ 视频文件存在: {video_path}")
    
    # 开始推流
    start_streaming(
        rtmp_url=args.rtmp,
        video_file=video_path,
        loop=not args.no_loop,
        log_level=args.log_level
    )


if __name__ == "__main__":
    main()

