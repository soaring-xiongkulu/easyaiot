#!/usr/bin/env python3
"""
视频转码脚本：将其他格式的视频转换为MP4格式
支持单个文件或批量转换
"""
import os
import sys
import subprocess
import argparse
import json
from pathlib import Path
from typing import Optional, List, Dict
import time


def check_ffmpeg() -> bool:
    """检查 ffmpeg 是否已安装"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True
        return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_video_info(video_path: Path) -> Optional[Dict]:
    """获取视频信息"""
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path)
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return None
    except Exception as e:
        print(f"⚠️  获取视频信息失败: {str(e)}")
        return None


def format_duration(seconds: float) -> str:
    """格式化时长"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def convert_video(
    input_path: Path,
    output_path: Optional[Path] = None,
    quality: str = "medium",
    resolution: Optional[str] = None,
    bitrate: Optional[str] = None,
    fps: Optional[int] = None,
    audio: bool = True,
    overwrite: bool = False,
    show_progress: bool = True
) -> bool:
    """
    转换视频为MP4格式
    
    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径，如果为None则自动生成
        quality: 质量预设 (low, medium, high, veryhigh)
        resolution: 目标分辨率，格式如 "1920x1080" 或 "1280x720"
        bitrate: 视频码率，如 "2000k", "5M"
        fps: 目标帧率
        audio: 是否保留音频
        overwrite: 是否覆盖已存在的输出文件
        show_progress: 是否显示进度
    
    Returns:
        转换是否成功
    """
    if not input_path.exists():
        print(f"❌ 输入文件不存在: {input_path}")
        return False
    
    # 生成输出路径
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}.mp4"
    
    # 检查输出文件是否已存在
    if output_path.exists() and not overwrite:
        print(f"⚠️  输出文件已存在: {output_path}")
        response = input("是否覆盖? (y/n): ").strip().lower()
        if response != 'y':
            print("⏭️  跳过转换")
            return False
    
    # 获取视频信息
    print(f"\n📹 处理视频: {input_path.name}")
    video_info = get_video_info(input_path)
    if video_info:
        streams = video_info.get("streams", [])
        video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        if video_stream:
            width = video_stream.get("width", "?")
            height = video_stream.get("height", "?")
            codec = video_stream.get("codec_name", "?")
            duration = float(video_info.get("format", {}).get("duration", 0))
            print(f"   原始信息: {width}x{height}, 编码: {codec}, 时长: {format_duration(duration)}")
    
    # 构建ffmpeg命令
    cmd = ["ffmpeg", "-y" if overwrite else "-n", "-i", str(input_path)]
    
    # 视频编码参数
    video_filters = []
    
    # 分辨率设置
    if resolution:
        video_filters.append(f"scale={resolution}")
    
    # 帧率设置
    if fps:
        video_filters.append(f"fps={fps}")
    
    # 应用视频滤镜
    if video_filters:
        cmd.extend(["-vf", ",".join(video_filters)])
    
    # 视频编码器设置
    cmd.extend(["-c:v", "libx264"])
    
    # 质量预设
    quality_presets = {
        "low": ("veryfast", "1000k"),
        "medium": ("medium", "2000k"),
        "high": ("slow", "5000k"),
        "veryhigh": ("veryslow", "10000k")
    }
    
    preset, default_bitrate = quality_presets.get(quality, quality_presets["medium"])
    cmd.extend(["-preset", preset])
    cmd.extend(["-tune", "film"])  # 适合视频内容
    
    # 码率设置
    if bitrate:
        cmd.extend(["-b:v", bitrate])
    else:
        cmd.extend(["-b:v", default_bitrate])
    
    # 像素格式
    cmd.extend(["-pix_fmt", "yuv420p"])
    
    # 音频处理
    if audio:
        cmd.extend(["-c:a", "aac"])
        cmd.extend(["-b:a", "128k"])
    else:
        cmd.extend(["-an"])
    
    # 输出格式
    cmd.extend(["-f", "mp4"])
    
    # 进度显示
    if show_progress:
        cmd.extend([
            "-progress", "pipe:1",
            "-loglevel", "info"
        ])
    else:
        cmd.extend(["-loglevel", "error"])
    
    # 输出文件
    cmd.append(str(output_path))
    
    print(f"📤 输出文件: {output_path.name}")
    print(f"⚙️  质量: {quality}, 分辨率: {resolution or '保持原始'}, 码率: {bitrate or default_bitrate}")
    
    # 执行转换
    start_time = time.time()
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # 解析进度信息
        if show_progress:
            for line in process.stdout:
                if line.startswith("out_time_ms="):
                    try:
                        time_ms = int(line.split("=")[1].strip())
                        time_sec = time_ms / 1000000.0
                        if video_info and duration > 0:
                            progress = (time_sec / duration) * 100
                            print(f"\r   进度: {progress:.1f}% ({format_duration(time_sec)}/{format_duration(duration)})", end="", flush=True)
                    except:
                        pass
        
        process.wait()
        
        if process.returncode == 0:
            elapsed = time.time() - start_time
            file_size = output_path.stat().st_size / (1024 * 1024)  # MB
            print(f"\n✅ 转换成功! 耗时: {elapsed:.1f}秒, 文件大小: {file_size:.2f}MB")
            return True
        else:
            error_output = process.stderr.read()
            print(f"\n❌ 转换失败 (返回码: {process.returncode})")
            if error_output:
                print(f"   错误信息: {error_output[:200]}")
            return False
            
    except Exception as e:
        print(f"\n❌ 转换过程出错: {str(e)}")
        return False


def find_video_files(directory: Path, extensions: List[str] = None) -> List[Path]:
    """查找目录中的所有视频文件"""
    if extensions is None:
        extensions = [".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm", ".m4v", ".3gp", ".ts", ".mts"]
    
    video_files = []
    for ext in extensions:
        video_files.extend(directory.rglob(f"*{ext}"))
        video_files.extend(directory.rglob(f"*{ext.upper()}"))
    
    # 排除已经是MP4的文件（除非明确指定）
    return [f for f in video_files if f.suffix.lower() != ".mp4"]


def main():
    parser = argparse.ArgumentParser(
        description="视频转码工具：将其他格式的视频转换为MP4",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 转换单个文件
  python convert_to_mp4.py input.avi
  
  # 指定输出文件
  python convert_to_mp4.py input.avi -o output.mp4
  
  # 批量转换目录中的所有视频
  python convert_to_mp4.py -d ./videos
  
  # 高质量转换，指定分辨率
  python convert_to_mp4.py input.avi -q high -r 1920x1080
  
  # 自定义码率和帧率
  python convert_to_mp4.py input.avi -b 5000k --fps 30
  
  # 不保留音频
  python convert_to_mp4.py input.avi --no-audio
        """
    )
    
    parser.add_argument(
        "input",
        nargs="?",
        type=str,
        help="输入视频文件路径"
    )
    
    parser.add_argument(
        "-d", "--directory",
        type=str,
        help="批量转换目录中的所有视频文件"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="输出文件路径（仅单文件模式）"
    )
    
    parser.add_argument(
        "-q", "--quality",
        choices=["low", "medium", "high", "veryhigh"],
        default="medium",
        help="质量预设 (默认: medium)"
    )
    
    parser.add_argument(
        "-r", "--resolution",
        type=str,
        help="目标分辨率，格式如 '1920x1080' 或 '1280x720'"
    )
    
    parser.add_argument(
        "-b", "--bitrate",
        type=str,
        help="视频码率，如 '2000k' 或 '5M'"
    )
    
    parser.add_argument(
        "--fps",
        type=int,
        help="目标帧率"
    )
    
    parser.add_argument(
        "--no-audio",
        action="store_true",
        help="不保留音频"
    )
    
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="覆盖已存在的输出文件"
    )
    
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="不显示转换进度"
    )
    
    args = parser.parse_args()
    
    # 检查ffmpeg
    print("🔍 检查 ffmpeg...")
    if not check_ffmpeg():
        print("❌ ffmpeg 未安装，请先安装 ffmpeg")
        print("   Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("   macOS: brew install ffmpeg")
        print("   Windows: 从 https://ffmpeg.org/download.html 下载")
        sys.exit(1)
    print("✅ ffmpeg 已安装\n")
    
    # 处理输入
    success_count = 0
    fail_count = 0
    
    if args.directory:
        # 批量转换模式
        directory = Path(args.directory)
        if not directory.exists() or not directory.is_dir():
            print(f"❌ 目录不存在: {directory}")
            sys.exit(1)
        
        print(f"📁 扫描目录: {directory}")
        video_files = find_video_files(directory)
        
        if not video_files:
            print("⚠️  未找到需要转换的视频文件")
            sys.exit(0)
        
        print(f"📹 找到 {len(video_files)} 个视频文件\n")
        
        for i, video_file in enumerate(video_files, 1):
            print(f"\n[{i}/{len(video_files)}]")
            if convert_video(
                video_file,
                quality=args.quality,
                resolution=args.resolution,
                bitrate=args.bitrate,
                fps=args.fps,
                audio=not args.no_audio,
                overwrite=args.overwrite,
                show_progress=not args.no_progress
            ):
                success_count += 1
            else:
                fail_count += 1
    
    elif args.input:
        # 单文件转换模式
        input_path = Path(args.input)
        output_path = Path(args.output) if args.output else None
        
        if convert_video(
            input_path,
            output_path,
            quality=args.quality,
            resolution=args.resolution,
            bitrate=args.bitrate,
            fps=args.fps,
            audio=not args.no_audio,
            overwrite=args.overwrite,
            show_progress=not args.no_progress
        ):
            success_count += 1
        else:
            fail_count += 1
    else:
        parser.print_help()
        sys.exit(1)
    
    # 输出统计信息
    print("\n" + "="*50)
    print(f"📊 转换完成: 成功 {success_count} 个, 失败 {fail_count} 个")
    print("="*50)
    
    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

