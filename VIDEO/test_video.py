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
VIDEO_FILE = VIDEO_DIR / "video2.mp4"
RTMP_URL = "rtmp://localhost:1935/live/1764341204704370850"

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


def tail_docker_log_follow(container_id, log_path="/data/srs.log"):
    """
    实时输出 Docker 容器的日志（类似 tail -f）
    
    Args:
        container_id: Docker 容器ID或名称
        log_path: 容器内日志文件路径
    """
    try:
        cmd = ["docker", "exec", container_id, "tail", "-f", log_path]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        print(f"✅ 开始实时输出日志 (按 Ctrl+C 停止)\n")
        
        try:
            # 实时输出 stdout
            while True:
                if process.poll() is not None:
                    # 进程已结束
                    remaining = process.stdout.read()
                    if remaining:
                        print(remaining.rstrip())
                    break
                
                line = process.stdout.readline()
                if line:
                    print(line.rstrip())
                else:
                    # 如果没有新行，稍微等待一下
                    time.sleep(0.1)
            
            # 检查是否有错误输出
            stderr_output = process.stderr.read()
            if stderr_output:
                print(f"\n⚠️  错误输出: {stderr_output.strip()}")
            
            # 检查退出码
            if process.returncode != 0:
                print(f"\n❌ 进程异常退出 (退出码: {process.returncode})")
            
        except KeyboardInterrupt:
            print("\n\n🛑 收到停止信号，正在停止日志输出...")
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            print("✅ 日志输出已停止")
            
    except FileNotFoundError:
        print("❌ Docker 未安装或不在 PATH 中")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 实时输出日志时出错: {str(e)}")
        sys.exit(1)


def find_srs_container():
    """
    自动查找 SRS Docker 容器
    
    Returns:
        容器ID或名称，如果未找到则返回None
    """
    import subprocess
    
    try:
        # 首先尝试通过容器名称查找（最常见的名称）
        common_names = ['srs-server', 'srs', 'srs-server-1']
        for name in common_names:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={name}", "--format", "{{.ID}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                container_id = result.stdout.strip().split('\n')[0]
                print(f"✅ 找到 SRS 容器: {name} ({container_id})")
                return container_id
        
        # 如果通过名称找不到，尝试通过镜像名称查找
        result = subprocess.run(
            ["docker", "ps", "--filter", "ancestor=ossrs/srs", "--format", "{{.ID}}\t{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.strip():
                    parts = line.strip().split('\t')
                    container_id = parts[0]
                    container_name = parts[1] if len(parts) > 1 else container_id
                    print(f"✅ 找到 SRS 容器: {container_name} ({container_id})")
                    return container_id
        
        # 如果还是找不到，列出所有运行中的容器供用户参考
        print("❌ 未找到 SRS 容器")
        print("\n💡 正在运行的容器:")
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.ID}}\t{{.Names}}\t{{.Image}}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            print(result.stdout)
        print("\n💡 提示:")
        print("   1. 确保 SRS 容器正在运行")
        print("   2. 使用 --docker-container CONTAINER_ID 手动指定容器ID")
        print("   3. 使用 --logs 实时输出日志")
        
        return None
        
    except FileNotFoundError:
        print("❌ Docker 未安装或不在 PATH 中")
        return None
    except Exception as e:
        print(f"❌ 查找 SRS 容器时出错: {str(e)}")
        return None


def read_docker_log(container_id, log_path="/data/srs.log", tail_lines=30):
    """
    从 Docker 容器读取日志
    
    Args:
        container_id: Docker 容器ID或名称
        log_path: 容器内日志文件路径
        tail_lines: 读取最后N行
    
    Returns:
        日志文本内容
    """
    try:
        cmd = ["docker", "exec", container_id, "tail", "-n", str(tail_lines), log_path]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"❌ 读取 Docker 日志失败: {result.stderr}")
            return None
        
        return result.stdout
            
    except FileNotFoundError:
        print("❌ Docker 未安装或不在 PATH 中")
        return None
    except subprocess.TimeoutExpired:
        print("❌ 读取 Docker 日志超时")
        return None
    except Exception as e:
        print(f"❌ 读取 Docker 日志时出错: {str(e)}")
        return None


def start_streaming(rtmp_url=None, video_file=None, loop=True, log_level="info",
                    preset="ultrafast", video_bitrate="500k", audio_bitrate="64k",
                    fps=None, scale=None, threads=None, gop_size=30, no_audio=False):
    """
    启动视频推流（优化版本：低CPU占用、低推流速度）
    
    Args:
        rtmp_url: RTMP 推流地址，默认为 rtmp://localhost:1935/live/1764341204704370850
        video_file: 视频文件路径，默认为 VIDEO/video/video2.mp4
        loop: 是否循环播放，默认为 True
        log_level: ffmpeg 日志级别，默认为 info
        preset: 编码预设，默认为 ultrafast（最快，最低CPU）
        video_bitrate: 视频比特率，默认为 500k（降低推流速度）
        audio_bitrate: 音频比特率，默认为 64k
        fps: 目标帧率，None 表示使用原始帧率，降低帧率可减少CPU
        scale: 分辨率缩放，格式如 "640:360"，None 表示不缩放
        threads: 编码线程数，None 表示自动，降低可减少CPU占用
        gop_size: GOP大小（关键帧间隔），增大可减少CPU
        no_audio: 是否禁用音频，禁用可减少CPU占用
    """
    global ffmpeg_process
    
    if rtmp_url is None:
        rtmp_url = RTMP_URL
    if video_file is None:
        video_file = VIDEO_FILE
    
    # 构建 ffmpeg 命令（优化参数以降低CPU和推流速度）
    cmd = [
        "ffmpeg",
        "-re",  # 以原始帧率读取输入
        "-stream_loop", "-1" if loop else "0",  # -1 表示无限循环，0 表示不循环
        "-i", str(video_file),  # 输入文件
    ]
    
    # 视频编码参数（优化以降低CPU）
    cmd.extend(["-c:v", "libx264"])  # 视频编码器
    cmd.extend(["-preset", preset])  # 编码预设：ultrafast 最快，CPU占用最低
    # 移除 -tune zerolatency，因为它会增加CPU使用
    
    # 降低视频比特率以减少推流速度
    cmd.extend(["-b:v", video_bitrate])
    
    # 设置GOP大小，增大可减少关键帧频率，降低CPU
    cmd.extend(["-g", str(gop_size)])
    
    # 限制帧率以降低CPU和推流速度
    if fps is not None:
        cmd.extend(["-r", str(fps)])
    
    # 分辨率缩放以降低CPU和推流速度
    if scale is not None:
        cmd.extend(["-vf", f"scale={scale}"])
    
    # 限制编码线程数以降低CPU占用
    if threads is not None:
        cmd.extend(["-threads", str(threads)])
    
    # 音频编码参数（优化以降低CPU）
    if no_audio:
        cmd.extend(["-an"])  # 禁用音频
    else:
        cmd.extend(["-c:a", "aac"])  # 音频编码器
        cmd.extend(["-b:a", audio_bitrate])  # 降低音频比特率
    
    # 输出格式和地址
    cmd.extend([
        "-f", "flv",  # 输出格式
        "-loglevel", log_level,  # 日志级别
        rtmp_url  # RTMP 推流地址
    ])
    
    print(f"\n🚀 开始推流（优化模式：低CPU占用）...")
    print(f"   视频文件: {video_file}")
    print(f"   推流地址: {rtmp_url}")
    print(f"   循环播放: {'是' if loop else '否'}")
    print(f"   编码预设: {preset}")
    print(f"   视频比特率: {video_bitrate}")
    print(f"   音频比特率: {'禁用' if no_audio else audio_bitrate}")
    if fps is not None:
        print(f"   目标帧率: {fps} fps")
    if scale is not None:
        print(f"   分辨率缩放: {scale}")
    if threads is not None:
        print(f"   编码线程数: {threads}")
    print(f"   GOP大小: {gop_size}")
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
        stderr_output = ""
        while True:
            if ffmpeg_process.poll() is not None:
                # 进程已结束，读取剩余输出
                remaining = ffmpeg_process.stderr.read()
                if remaining:
                    stderr_output += remaining
                break
            
            # 读取一行错误输出
            line = ffmpeg_process.stderr.readline()
            if line:
                stderr_output += line
                # 过滤掉一些不重要的信息
                if log_level == "error" or "error" in line.lower() or "warning" in line.lower():
                    print(line.strip())
            
            time.sleep(0.1)
        
        # 如果有输出，显示完整信息
        if stderr_output:
            print("\n📋 ffmpeg 输出:")
            print(stderr_output)
        
        # 检查退出码
        return_code = ffmpeg_process.returncode
        if return_code != 0:
            print(f"\n❌ 推流进程异常退出 (退出码: {return_code})")
            
            # 检查是否是RTMP连接错误
            if stderr_output:
                error_lower = stderr_output.lower()
                if "error opening output" in error_lower or "input/output error" in error_lower:
                    print("\n💡 可能的原因和解决方案：")
                    print("   1. RTMP服务器未运行或连接被拒绝")
                    print(f"      - 请确保RTMP服务器（SRS）在 {rtmp_url.split('://')[1].split('/')[0]} 上运行")
                    print("      - 检查SRS服务状态: docker ps | grep srs 或 systemctl status srs")
                    print("   2. SRS HTTP回调服务未运行（常见原因）")
                    print("      - SRS配置了on_publish回调，但回调服务未启动")
                    print("      - 请确保VIDEO服务在端口6000上运行，或网关服务在端口48080上运行")
                    print("      - 检查服务: docker ps | grep video 或检查VIDEO服务状态")
                    print("      - 查看SRS日志确认回调URL: http://127.0.0.1:48080/admin-api/video/camera/callback/on_publish")
                    print("   3. RTMP服务器地址不正确")
                    print(f"      - 当前地址: {rtmp_url}")
                    print("      - 请使用 --rtmp 参数指定正确的RTMP地址")
                    print("   4. 网络连接问题")
                    print("      - 请检查防火墙设置")
                    print("      - 请检查网络连接")
                    print("\n📝 排查步骤：")
                    print(f"   1. 运行诊断工具: python {Path(__file__).parent / 'diagnose_rtmp_issue.py'}")
                    print(f"   2. 检查RTMP端口: netstat -tuln | grep 1935")
                    print(f"   3. 检查VIDEO服务端口: netstat -tuln | grep 6000")
                    print(f"   4. 检查网关服务端口: netstat -tuln | grep 48080")
                    print(f"   5. 查看SRS日志确认具体错误信息")
                    print(f"   6. 测试RTMP连接: telnet localhost 1935")
                    print("\n🔧 临时解决方案（仅用于测试）：")
                    print("   如果VIDEO服务未运行，可以使用临时mock回调服务器：")
                    print(f"   python {Path(__file__).parent / 'mock_callback_server.py'}")
                    print("   然后确保SRS可以访问到mock服务器地址")
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
  # 使用默认配置推流（已优化：低CPU占用、低推流速度）
  python test_video.py
  
  # 指定自定义 RTMP 地址
  python test_video.py --rtmp rtmp://192.168.1.100:1935/live/stream1
  
  # 指定自定义视频文件
  python test_video.py --video /path/to/video.mp4
  
  # 不循环播放（只播放一次）
  python test_video.py --no-loop
  
  # 进一步降低CPU占用：降低帧率到15fps
  python test_video.py --fps 15
  
  # 降低分辨率和帧率以进一步减少CPU占用
  python test_video.py --scale 640:360 --fps 15
  
  # 禁用音频以降低CPU占用
  python test_video.py --no-audio
  
  # 限制编码线程数（如2个线程）
  python test_video.py --threads 2
  
  # 降低视频比特率到300k（进一步降低推流速度）
  python test_video.py --video-bitrate 300k
  
  # 组合优化：最低CPU占用配置
  python test_video.py --fps 15 --scale 640:360 --video-bitrate 300k --no-audio --threads 2
  
  # 实时输出SRS日志（自动查找容器）
  python test_video.py --logs
  
  # 实时输出SRS日志（指定容器ID）
  python test_video.py --logs --docker-container 8f37de7c0680
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
    
    parser.add_argument(
        '--preset',
        type=str,
        choices=['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow'],
        default='ultrafast',
        help='编码预设，ultrafast 最快但质量较低，可降低CPU占用 (默认: ultrafast)'
    )
    
    parser.add_argument(
        '--video-bitrate',
        type=str,
        default='500k',
        help='视频比特率，降低可减少推流速度和CPU占用 (默认: 500k)'
    )
    
    parser.add_argument(
        '--audio-bitrate',
        type=str,
        default='64k',
        help='音频比特率 (默认: 64k)'
    )
    
    parser.add_argument(
        '--fps',
        type=int,
        default=None,
        help='目标帧率，降低可减少CPU占用和推流速度 (默认: 使用原始帧率)'
    )
    
    parser.add_argument(
        '--scale',
        type=str,
        default=None,
        help='分辨率缩放，格式如 "640:360"，降低可减少CPU占用 (默认: 不缩放)'
    )
    
    parser.add_argument(
        '--threads',
        type=int,
        default=None,
        help='编码线程数，降低可减少CPU占用 (默认: 自动)'
    )
    
    parser.add_argument(
        '--gop-size',
        type=int,
        default=30,
        help='GOP大小（关键帧间隔），增大可减少CPU占用 (默认: 30)'
    )
    
    parser.add_argument(
        '--no-audio',
        action='store_true',
        help='禁用音频，可减少CPU占用'
    )
    
    parser.add_argument(
        '--logs',
        action='store_true',
        help='实时输出SRS日志（类似 tail -f）。会自动查找SRS容器，或使用--docker-container指定'
    )
    
    parser.add_argument(
        '--docker-container',
        type=str,
        default=None,
        metavar='CONTAINER_ID',
        help='Docker容器ID或名称（用于实时输出日志）。如果不指定，会自动查找SRS容器'
    )
    
    parser.add_argument(
        '--docker-log-path',
        type=str,
        default='/data/srs.log',
        help='Docker容器内日志文件路径 (默认: /data/srs.log)'
    )
    
    args = parser.parse_args()
    
    # 如果是实时输出日志
    if args.logs:
        print("=" * 60)
        print("📋 实时输出SRS日志")
        print("=" * 60)
        
        # 查找容器
        container_id = args.docker_container
        if not container_id:
            container_id = find_srs_container()
            if not container_id:
                print("\n❌ 无法找到SRS容器，请使用 --docker-container 指定容器ID")
                sys.exit(1)
        
        print(f"容器ID: {container_id}")
        print(f"日志路径: {args.docker_log_path}\n")
        
        # 注册信号处理器以便优雅退出
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 实时输出日志
        tail_docker_log_follow(
            container_id,
            log_path=args.docker_log_path
        )
        
        sys.exit(0)
    
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
        log_level=args.log_level,
        preset=args.preset,
        video_bitrate=args.video_bitrate,
        audio_bitrate=args.audio_bitrate,
        fps=args.fps,
        scale=args.scale,
        threads=args.threads,
        gop_size=args.gop_size,
        no_audio=args.no_audio
    )


if __name__ == "__main__":
    main()

