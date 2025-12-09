#!/bin/bash
# 将本地视频文件推流到SRS服务器
# 使用方法: ./push_video_to_srs.sh [选项]
# 默认推流文件: VIDEO/video/video2.mp4 (相对于项目根目录)
# 默认推流地址: rtmp://127.0.0.1:1935/live/test

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 默认参数
VIDEO_FILE=""
SRS_HOST="127.0.0.1"
SRS_PORT=1935
APP="live"
STREAM="test"
FFMPEG_PATH="ffmpeg"
LOOP=true
RE_ENCODE=false

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

# 显示使用说明
show_usage() {
    echo "使用方法:"
    echo "  $0 [选项]"
    echo ""
    echo "可选参数:"
    echo "  -v, --video <视频文件>        视频文件路径 (默认: 自动查找脚本同级目录的视频文件)"
    echo "  -h, --host <SRS主机>          SRS服务器IP地址 (默认: 127.0.0.1)"
    echo "  -p, --port <SRS端口>          SRS服务器RTMP端口 (默认: 1935)"
    echo "  -a, --app <应用名>            应用名称 (默认: live)"
    echo "  -s, --stream <流名>           流名称 (默认: test)"
    echo "  -f, --ffmpeg <路径>           FFmpeg可执行文件路径 (默认: ffmpeg)"
    echo "  --no-loop                     不循环播放（播放一次后退出）"
    echo "  --re-encode                   重新编码（兼容性更好，但CPU占用更高）"
    echo "  --help                        显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                                    # 使用默认配置推流"
    echo "  $0 -h \"192.168.1.200\"                # 推流到指定服务器"
    echo "  $0 -h \"192.168.1.200\" -s \"camera01\"  # 推流到指定服务器和流名"
    echo "  $0 -v \"/path/to/video.mp4\"           # 推流指定视频文件"
    echo "  $0 --no-loop                          # 播放一次后退出"
    echo "  $0 --re-encode                        # 使用重新编码模式"
    echo ""
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--video)
            # 如果传入的是相对路径，则相对于脚本目录
            if [[ "$2" != /* ]]; then
                VIDEO_FILE="$SCRIPT_DIR/$2"
            else
                VIDEO_FILE="$2"
            fi
            shift 2
            ;;
        -h|--host)
            SRS_HOST="$2"
            shift 2
            ;;
        -p|--port)
            SRS_PORT="$2"
            shift 2
            ;;
        -a|--app)
            APP="$2"
            shift 2
            ;;
        -s|--stream)
            STREAM="$2"
            shift 2
            ;;
        -f|--ffmpeg)
            FFMPEG_PATH="$2"
            shift 2
            ;;
        --no-loop)
            LOOP=false
            shift
            ;;
        --re-encode)
            RE_ENCODE=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}错误: 未知参数 '$1'${NC}"
            echo ""
            show_usage
            exit 1
            ;;
    esac
done

# 如果没有指定视频文件，则在脚本同级目录查找
if [[ -z "$VIDEO_FILE" ]]; then
    # 视频文件扩展名列表
    VIDEO_EXTENSIONS=("mp4" "avi" "mov" "mkv" "flv" "wmv" "webm" "m4v")
    FOUND_VIDEO=""
    
    for ext in "${VIDEO_EXTENSIONS[@]}"; do
        # 查找第一个匹配的视频文件
        FOUND_VIDEO=$(find "$SCRIPT_DIR" -maxdepth 1 -type f -iname "*.${ext}" | head -n 1)
        if [[ -n "$FOUND_VIDEO" ]]; then
            VIDEO_FILE="$FOUND_VIDEO"
            break
        fi
    done
    
    if [[ -z "$VIDEO_FILE" ]]; then
        echo -e "${RED}错误: 在脚本同级目录未找到视频文件${NC}"
        echo -e "${YELLOW}脚本目录: $SCRIPT_DIR${NC}"
        echo -e "${YELLOW}支持的视频格式: mp4, avi, mov, mkv, flv, wmv, webm, m4v${NC}"
        echo -e "${YELLOW}请将视频文件放在脚本同级目录，或使用 -v 参数指定视频文件路径${NC}"
        exit 1
    fi
fi

# 检查视频文件是否存在
if [[ ! -f "$VIDEO_FILE" ]]; then
    echo -e "${RED}错误: 视频文件不存在: $VIDEO_FILE${NC}"
    echo -e "${YELLOW}请检查文件路径是否正确，或使用 -v 参数指定视频文件路径${NC}"
    exit 1
fi

# 检查ffmpeg是否可用
if ! command -v "$FFMPEG_PATH" &> /dev/null; then
    echo -e "${RED}错误: 无法找到ffmpeg，请确保ffmpeg已安装并添加到PATH环境变量中${NC}"
    echo -e "${YELLOW}或者使用 -f 参数指定ffmpeg的完整路径，例如: -f '/usr/bin/ffmpeg'${NC}"
    echo ""
    echo "在Ubuntu上安装ffmpeg:"
    echo "  sudo apt update"
    echo "  sudo apt install -y ffmpeg"
    exit 1
fi

# 显示ffmpeg版本信息
FFMPEG_VERSION=$($FFMPEG_PATH -version 2>&1 | head -n 1)
echo -e "${GREEN}检测到ffmpeg: $FFMPEG_VERSION${NC}"

# 构建RTMP推流地址
RTMP_URL="rtmp://${SRS_HOST}:${SRS_PORT}/${APP}/${STREAM}"

# 显示配置信息
# 如果视频文件在脚本目录下，显示相对路径；否则显示绝对路径
if [[ "$VIDEO_FILE" == "$SCRIPT_DIR"/* ]]; then
    VIDEO_FILE_DISPLAY="${VIDEO_FILE#$SCRIPT_DIR/}"
    # 如果相对路径为空，则只显示文件名
    if [[ -z "$VIDEO_FILE_DISPLAY" ]]; then
        VIDEO_FILE_DISPLAY="$(basename "$VIDEO_FILE")"
    fi
else
    VIDEO_FILE_DISPLAY="$VIDEO_FILE"
fi

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}视频文件推流到SRS配置${NC}"
echo -e "${CYAN}========================================${NC}"
echo -e "${WHITE}视频文件: $VIDEO_FILE_DISPLAY${NC}"
echo -e "${WHITE}SRS服务器: $SRS_HOST:$SRS_PORT${NC}"
echo -e "${WHITE}应用名称: $APP${NC}"
echo -e "${WHITE}流名称: $STREAM${NC}"
echo -e "${GREEN}RTMP推流地址: $RTMP_URL${NC}"
if [ "$LOOP" = true ]; then
    echo -e "${WHITE}循环播放: 是${NC}"
else
    echo -e "${WHITE}循环播放: 否${NC}"
fi
if [ "$RE_ENCODE" = true ]; then
    echo -e "${WHITE}编码模式: 重新编码${NC}"
else
    echo -e "${WHITE}编码模式: 复制（copy）${NC}"
fi
echo -e "${CYAN}========================================${NC}"
echo ""

# ffmpeg推流参数说明:
# -i: 输入源（视频文件）
# -stream_loop -1: 无限循环播放（如果启用）
# -c:v copy: 视频编码器，使用copy避免重新编码（如果视频是H.264）
# -c:a copy: 音频编码器，使用copy避免重新编码
# -f flv: 输出格式为FLV（RTMP协议要求）
# -re: 按照原始帧率推流
# -fflags nobuffer: 禁用缓冲，降低延迟
# -flags low_delay: 低延迟模式
# -flvflags no_duration_filesize: FLV标志，避免写入文件大小和时长（适用于流媒体）

echo -e "${YELLOW}开始推流...${NC}"
echo -e "${YELLOW}按 Ctrl+C 停止推流${NC}"
echo ""

# 构建ffmpeg命令
FFMPEG_CMD="$FFMPEG_PATH -loglevel info"

# 添加循环播放参数
if [ "$LOOP" = true ]; then
    FFMPEG_CMD="$FFMPEG_CMD -stream_loop -1"
fi

# 添加输入文件
FFMPEG_CMD="$FFMPEG_CMD -i \"$VIDEO_FILE\""

# 添加编码参数
if [ "$RE_ENCODE" = true ]; then
    echo -e "${YELLOW}使用重新编码模式（兼容性更好，但CPU占用更高）${NC}"
    echo -e "${CYAN}FFmpeg命令参数:${NC}"
    echo -e "${GRAY}  -c:v libx264 -preset ultrafast -tune zerolatency${NC}"
    echo -e "${GRAY}  -c:a aac -b:a 128k${NC}"
    echo -e "${GRAY}  -f flv -re -fflags nobuffer -flags low_delay${NC}"
    echo ""
    FFMPEG_CMD="$FFMPEG_CMD -c:v libx264 -preset ultrafast -tune zerolatency -c:a aac -b:a 128k"
else
    echo -e "${YELLOW}使用copy模式（性能更好，但需要编码格式兼容）${NC}"
    echo -e "${CYAN}FFmpeg命令参数:${NC}"
    echo -e "${GRAY}  -c:v copy -c:a copy${NC}"
    echo -e "${GRAY}  -f flv -re -fflags nobuffer -flags low_delay${NC}"
    echo ""
    FFMPEG_CMD="$FFMPEG_CMD -c:v copy -c:a copy"
fi

# 添加输出参数
FFMPEG_CMD="$FFMPEG_CMD -f flv -re -fflags nobuffer -flags low_delay -flvflags no_duration_filesize \"$RTMP_URL\""

# 显示执行的命令（用于调试）
echo -e "${GRAY}执行命令: $FFMPEG_CMD${NC}"
echo ""

# 执行ffmpeg推流命令
eval $FFMPEG_CMD

# 检查退出码
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo -e "${RED}推流失败，退出码: $EXIT_CODE${NC}"
    echo ""
    echo -e "${YELLOW}可能的原因:${NC}"
    echo -e "${YELLOW}  1. 视频文件格式不支持或已损坏${NC}"
    echo -e "${YELLOW}  2. SRS服务器未运行或地址不正确${NC}"
    echo -e "${YELLOW}  3. 网络连接问题（防火墙、端口阻塞）${NC}"
    echo -e "${YELLOW}  4. 视频编码格式不兼容（H.265、G.711等，可能需要重新编码）${NC}"
    echo ""
    echo -e "${CYAN}故障排查建议:${NC}"
    echo -e "${WHITE}  1. 检查视频文件是否可播放: 使用VLC或其他播放器测试${NC}"
    echo -e "${WHITE}  2. 检查SRS服务器状态: 访问 http://${SRS_HOST}:1985/api/v1/streams/${NC}"
    echo -e "${WHITE}  3. 检查网络连接: ping $SRS_HOST${NC}"
    echo -e "${WHITE}  4. 尝试使用重新编码模式: 添加 --re-encode 参数${NC}"
    echo -e "${GRAY}     示例: $0 --re-encode${NC}"
    echo -e "${WHITE}  5. 查看FFmpeg详细日志（已启用info模式）${NC}"
    echo ""
    exit $EXIT_CODE
else
    echo ""
    echo -e "${GREEN}推流已停止${NC}"
fi

