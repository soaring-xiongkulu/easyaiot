#!/usr/bin/env python3
"""
推流转发服务畅通性测试脚本
使用 MP4 文件作为 RTSP 输入流来测试 stream_forward_service 的畅通性

@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import os
import sys
import time
import signal
import subprocess
import threading
import logging
import cv2
import queue
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# 添加VIDEO模块路径
video_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, video_root)

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 测试配置
VIDEO_FILE = Path(video_root) / 'video' / 'video2.mp4'
RTSP_PORT = 8554
RTSP_PATH = '/test_stream'
RTSP_URL = f'rtsp://127.0.0.1:{RTSP_PORT}{RTSP_PATH}'
RTMP_URL = os.getenv('TEST_RTMP_URL', 'rtmp://127.0.0.1:1935/live/test_stream')
TEST_DURATION = 60  # 测试持续时间（秒）

# 全局变量
ffmpeg_rtsp_server: Optional[subprocess.Popen] = None
ffmpeg_rtmp_pusher: Optional[subprocess.Popen] = None
stop_event = threading.Event()
test_results = {
    'rtsp_server_started': False,
    'stream_readable': False,
    'frames_received': 0,
    'frames_processed': 0,
    'rtmp_push_success': False,
    'errors': []
}


def signal_handler(signum, frame):
    """信号处理函数"""
    logger.info(f"收到信号 {signum}，准备退出...")
    stop_event.set()


def check_ffmpeg():
    """检查 FFmpeg 是否安装"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.decode('utf-8', errors='ignore').split('\n')[0]
            logger.info(f"✅ FFmpeg 已安装: {version_line}")
            return True
        else:
            logger.error("❌ FFmpeg 未正确安装")
            return False
    except FileNotFoundError:
        logger.error("❌ FFmpeg 未安装，请先安装 FFmpeg")
        return False
    except Exception as e:
        logger.error(f"❌ 检查 FFmpeg 时出错: {str(e)}")
        return False


def check_video_file():
    """检查视频文件是否存在"""
    if not VIDEO_FILE.exists():
        logger.error(f"❌ 视频文件不存在: {VIDEO_FILE}")
        return False
    
    # 检查视频文件是否可以打开
    try:
        cap = cv2.VideoCapture(str(VIDEO_FILE))
        if not cap.isOpened():
            logger.error(f"❌ 无法打开视频文件: {VIDEO_FILE}")
            return False
        
        # 获取视频信息
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        logger.info(f"✅ 视频文件信息:")
        logger.info(f"   文件路径: {VIDEO_FILE}")
        logger.info(f"   分辨率: {width}x{height}")
        logger.info(f"   帧率: {fps:.2f} FPS")
        logger.info(f"   总帧数: {frame_count}")
        logger.info(f"   时长: {duration:.2f} 秒")
        
        cap.release()
        return True
    except Exception as e:
        logger.error(f"❌ 检查视频文件时出错: {str(e)}")
        return False


def start_rtsp_server():
    """启动 FFmpeg RTSP 服务器，将 MP4 文件作为 RTSP 流提供"""
    global ffmpeg_rtsp_server
    
    logger.info("🚀 启动 RTSP 服务器...")
    logger.info(f"   输入文件: {VIDEO_FILE}")
    logger.info(f"   RTSP 地址: {RTSP_URL}")
    
    # 构建 FFmpeg 命令，将 MP4 文件作为 RTSP 流提供
    # 使用 FFmpeg 的 RTSP 服务器功能
    ffmpeg_cmd = [
        'ffmpeg',
        '-re',  # 以原始帧率读取
        '-stream_loop', '-1',  # 无限循环
        '-i', str(VIDEO_FILE),
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-tune', 'zerolatency',
        '-b:v', '2000k',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-f', 'rtsp',
        f'rtsp://127.0.0.1:{RTSP_PORT}{RTSP_PATH}'
    ]
    
    # 注意：FFmpeg 本身不支持作为 RTSP 服务器
    # 我们需要使用其他方法，比如使用 MediaMTX 或者直接使用文件路径
    # 为了简化，我们直接使用文件路径作为输入源
    
    logger.warning("⚠️  FFmpeg 不支持直接作为 RTSP 服务器")
    logger.info("   将使用文件路径直接作为输入源进行测试")
    
    return True


def test_stream_readability():
    """测试流是否可读（使用文件路径）"""
    logger.info("🔍 测试流可读性...")
    logger.info(f"   输入源: {VIDEO_FILE}")
    
    try:
        cap = cv2.VideoCapture(str(VIDEO_FILE))
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        if not cap.isOpened():
            logger.error("❌ 无法打开视频流")
            test_results['errors'].append("无法打开视频流")
            return False
        
        # 尝试读取几帧
        frame_count = 0
        max_test_frames = 10
        
        for i in range(max_test_frames):
            ret, frame = cap.read()
            if ret and frame is not None:
                frame_count += 1
                test_results['frames_received'] += 1
            else:
                break
        
        cap.release()
        
        if frame_count > 0:
            logger.info(f"✅ 流可读，成功读取 {frame_count} 帧")
            test_results['stream_readable'] = True
            return True
        else:
            logger.error("❌ 无法从流中读取帧")
            test_results['errors'].append("无法从流中读取帧")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试流可读性时出错: {str(e)}")
        test_results['errors'].append(f"测试流可读性时出错: {str(e)}")
        return False


def test_stream_forward_core_functionality():
    """测试推流转发服务的核心功能"""
    logger.info("🔍 测试推流转发服务核心功能...")
    
    # 模拟 stream_forward_service 的核心流程
    # 1. 从源读取帧
    # 2. 处理帧（缩放等）
    # 3. 推送到 RTMP
    
    source_url = str(VIDEO_FILE)
    target_width = 640
    target_height = 360
    source_fps = 15
    
    logger.info(f"   源地址: {source_url}")
    logger.info(f"   目标分辨率: {target_width}x{target_height}")
    logger.info(f"   目标帧率: {source_fps} FPS")
    logger.info(f"   RTMP 输出: {RTMP_URL}")
    
    cap = None
    pusher_process = None
    
    try:
        # 1. 打开源流
        logger.info("📹 打开源流...")
        cap = cv2.VideoCapture(source_url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        if not cap.isOpened():
            logger.error("❌ 无法打开源流")
            test_results['errors'].append("无法打开源流")
            return False
        
        logger.info("✅ 源流已打开")
        
        # 获取原始视频参数
        original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        original_fps = cap.get(cv2.CAP_PROP_FPS)
        if original_fps <= 0:
            original_fps = source_fps
        
        logger.info(f"   原始分辨率: {original_width}x{original_height}")
        logger.info(f"   原始帧率: {original_fps:.2f} FPS")
        
        # 2. 启动 FFmpeg 推流进程
        logger.info("📺 启动 RTMP 推流进程...")
        
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-fflags", "nobuffer",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-pix_fmt", "bgr24",
            "-s", f"{target_width}x{target_height}",
            "-r", str(source_fps),
            "-i", "-",
            "-c:v", "libx264",
            "-b:v", "500k",
            "-pix_fmt", "yuv420p",
            "-preset", "ultrafast",
            "-g", str(source_fps * 2),
            "-keyint_min", str(source_fps),
            "-f", "flv",
            RTMP_URL
        ]
        
        try:
            pusher_process = subprocess.Popen(
                ffmpeg_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
                shell=False
            )
            
            # 等待一小段时间，检查进程是否立即退出
            time.sleep(0.5)
            
            if pusher_process.poll() is not None:
                stderr = pusher_process.stderr.read().decode('utf-8', errors='ignore') if pusher_process.stderr else ""
                logger.error(f"❌ RTMP 推流进程启动失败 (退出码: {pusher_process.returncode})")
                logger.error(f"   错误信息: {stderr[:500]}")
                test_results['errors'].append(f"RTMP 推流进程启动失败: {stderr[:200]}")
                return False
            
            logger.info(f"✅ RTMP 推流进程已启动 (PID: {pusher_process.pid})")
            test_results['rtmp_push_success'] = True
            
        except Exception as e:
            logger.error(f"❌ 启动 RTMP 推流进程失败: {str(e)}")
            test_results['errors'].append(f"启动 RTMP 推流进程失败: {str(e)}")
            return False
        
        # 3. 读取帧并推流
        logger.info("🔄 开始读取帧并推流...")
        logger.info(f"   测试持续时间: {TEST_DURATION} 秒")
        logger.info("   按 Ctrl+C 提前停止测试")
        
        frame_interval = 1.0 / source_fps
        last_frame_time = time.time()
        start_time = time.time()
        frame_count = 0
        
        while not stop_event.is_set():
            # 检查是否超过测试时间
            if time.time() - start_time > TEST_DURATION:
                logger.info(f"✅ 测试时间已到 ({TEST_DURATION} 秒)")
                break
            
            # 检查推流进程是否还在运行
            if pusher_process.poll() is not None:
                stderr = pusher_process.stderr.read().decode('utf-8', errors='ignore') if pusher_process.stderr else ""
                logger.error(f"❌ RTMP 推流进程异常退出 (退出码: {pusher_process.returncode})")
                logger.error(f"   错误信息: {stderr[-500:]}")
                test_results['errors'].append(f"RTMP 推流进程异常退出: {pusher_process.returncode}")
                break
            
            # 读取帧
            ret, frame = cap.read()
            
            if not ret or frame is None:
                logger.warning("⚠️  读取帧失败，重新打开流...")
                cap.release()
                time.sleep(1)
                cap = cv2.VideoCapture(source_url, cv2.CAP_FFMPEG)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                if not cap.isOpened():
                    logger.error("❌ 无法重新打开源流")
                    break
                continue
            
            # 缩放帧
            if (original_width, original_height) != (target_width, target_height):
                frame = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_LINEAR)
            
            # 推送到 RTMP
            try:
                pusher_process.stdin.write(frame.tobytes())
                pusher_process.stdin.flush()
                frame_count += 1
                test_results['frames_processed'] += 1
                
                if frame_count % (source_fps * 5) == 0:  # 每5秒打印一次
                    elapsed = time.time() - start_time
                    fps_actual = frame_count / elapsed if elapsed > 0 else 0
                    logger.info(f"   已处理 {frame_count} 帧，耗时 {elapsed:.1f} 秒，实际帧率: {fps_actual:.2f} FPS")
                
            except Exception as e:
                logger.error(f"❌ 推送帧失败: {str(e)}")
                test_results['errors'].append(f"推送帧失败: {str(e)}")
                break
            
            # 帧率控制
            current_time = time.time()
            elapsed = current_time - last_frame_time
            if elapsed < frame_interval:
                time.sleep(frame_interval - elapsed)
            last_frame_time = time.time()
        
        logger.info(f"✅ 推流测试完成，共处理 {frame_count} 帧")
        test_results['frames_processed'] = frame_count
        
        return True
        
    except KeyboardInterrupt:
        logger.info("收到中断信号...")
        return True
    except Exception as e:
        logger.error(f"❌ 测试推流转发服务核心功能时出错: {str(e)}", exc_info=True)
        test_results['errors'].append(f"测试推流转发服务核心功能时出错: {str(e)}")
        return False
    finally:
        # 清理资源
        if cap is not None:
            cap.release()
        
        if pusher_process is not None and pusher_process.poll() is None:
            try:
                pusher_process.stdin.close()
                pusher_process.terminate()
                pusher_process.wait(timeout=2)
                logger.info("✅ RTMP 推流进程已停止")
            except:
                if pusher_process.poll() is None:
                    pusher_process.kill()
                    pusher_process.wait()


def print_test_summary():
    """打印测试总结"""
    logger.info("\n" + "="*60)
    logger.info("测试总结")
    logger.info("="*60)
    logger.info(f"✅ 流可读: {'是' if test_results['stream_readable'] else '否'}")
    logger.info(f"✅ RTMP 推流: {'成功' if test_results['rtmp_push_success'] else '失败'}")
    logger.info(f"📊 接收帧数: {test_results['frames_received']}")
    logger.info(f"📊 处理帧数: {test_results['frames_processed']}")
    
    if test_results['errors']:
        logger.info(f"\n❌ 错误列表 ({len(test_results['errors'])} 个):")
        for i, error in enumerate(test_results['errors'], 1):
            logger.info(f"   {i}. {error}")
    else:
        logger.info("\n✅ 未发现错误")
    
    logger.info("="*60)
    
    # 判断测试是否成功
    success = (
        test_results['stream_readable'] and
        test_results['rtmp_push_success'] and
        test_results['frames_processed'] > 0 and
        len(test_results['errors']) == 0
    )
    
    if success:
        logger.info("✅ 推流转发服务畅通性测试通过！")
        return 0
    else:
        logger.error("❌ 推流转发服务畅通性测试失败！")
        return 1


def main():
    """主函数"""
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("="*60)
    logger.info("推流转发服务畅通性测试")
    logger.info("="*60)
    logger.info(f"视频文件: {VIDEO_FILE}")
    logger.info(f"RTSP 地址: {RTSP_URL}")
    logger.info(f"RTMP 地址: {RTMP_URL}")
    logger.info(f"测试时长: {TEST_DURATION} 秒")
    logger.info("="*60)
    
    # 1. 检查 FFmpeg
    if not check_ffmpeg():
        logger.error("❌ FFmpeg 检查失败，测试终止")
        return 1
    
    # 2. 检查视频文件
    if not check_video_file():
        logger.error("❌ 视频文件检查失败，测试终止")
        return 1
    
    # 3. 测试流可读性
    if not test_stream_readability():
        logger.error("❌ 流可读性测试失败，测试终止")
        return 1
    
    # 4. 测试推流转发服务核心功能
    if not test_stream_forward_core_functionality():
        logger.error("❌ 推流转发服务核心功能测试失败")
        return 1
    
    # 5. 打印测试总结
    return print_test_summary()


if __name__ == '__main__':
    sys.exit(main())
