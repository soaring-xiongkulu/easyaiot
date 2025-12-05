#!/bin/bash
# Ubuntu环境下使用ffmpeg将RTSP流推送到SRS服务器
# 使用方法: ./push_rtsp_to_srs.sh -u "rtsp://192.168.1.100:554/stream" -h "192.168.1.200" -p 1935 -a "live" -s "test"

# 默认参数
RTSP_URL=""
SRS_HOST="127.0.0.1"
SRS_PORT=1935
APP="live"
STREAM="test"
FFMPEG_PATH="ffmpeg"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 显示使用说明
show_usage() {
    echo "使用方法:"
    echo "  $0 -u <RTSP地址> [选项]"
    echo ""
    echo "必需参数:"
    echo "  -u, --url <RTSP地址>        RTSP源流地址"
    echo ""
    echo "可选参数:"
    echo "  -h, --host <SRS主机>        SRS服务器IP地址 (默认: 127.0.0.1)"
    echo "  -p, --port <SRS端口>        SRS服务器RTMP端口 (默认: 1935)"
    echo "  -a, --app <应用名>          应用名称 (默认: live)"
    echo "  -s, --stream <流名>         流名称 (默认: test)"
    echo "  -f, --ffmpeg <路径>         FFmpeg可执行文件路径 (默认: ffmpeg)"
    echo "  --help                      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 -u \"rtsp://192.168.1.100:554/stream\""
    echo "  $0 -u \"rtsp://192.168.1.100:554/stream\" -h \"192.168.1.200\""
    echo "  $0 -u \"rtsp://192.168.1.100:554/stream\" -h \"192.168.1.200\" -p 1935 -a \"camera\" -s \"camera01\""
    echo ""
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--url)
            RTSP_URL="$2"
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

# 检查必需参数
if [[ -z "$RTSP_URL" ]]; then
    echo -e "${RED}错误: 缺少RTSP源地址参数${NC}"
    echo ""
    show_usage
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
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}RTSP推流到SRS配置${NC}"
echo -e "${CYAN}========================================${NC}"
echo -e "${WHITE}RTSP源地址: $RTSP_URL${NC}"
echo -e "${WHITE}SRS服务器: $SRS_HOST:$SRS_PORT${NC}"
echo -e "${WHITE}应用名称: $APP${NC}"
echo -e "${WHITE}流名称: $STREAM${NC}"
echo -e "${GREEN}RTMP推流地址: $RTMP_URL${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# ffmpeg推流参数说明:
# -i: 输入源（RTSP流）
# -c:v copy: 视频编码器，使用copy避免重新编码（如果RTSP流是H.264）
# -c:a copy: 音频编码器，使用copy避免重新编码
# -f flv: 输出格式为FLV（RTMP协议要求）
# -rtsp_transport tcp: 使用TCP传输RTSP（更稳定，可选udp）
# -re: 按照原始帧率推流
# -loglevel info: 日志级别

echo -e "${YELLOW}开始推流...${NC}"
echo -e "${YELLOW}按 Ctrl+C 停止推流${NC}"
echo ""

# 执行ffmpeg推流命令
$FFMPEG_PATH \
    -rtsp_transport tcp \
    -i "$RTSP_URL" \
    -c:v copy \
    -c:a copy \
    -f flv \
    -re \
    "$RTMP_URL"

# 检查退出码
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo -e "${RED}推流失败，退出码: $EXIT_CODE${NC}"
    echo -e "${YELLOW}可能的原因:${NC}"
    echo -e "${YELLOW}  1. RTSP源地址无法访问${NC}"
    echo -e "${YELLOW}  2. SRS服务器未运行或地址不正确${NC}"
    echo -e "${YELLOW}  3. 网络连接问题${NC}"
    echo -e "${YELLOW}  4. RTSP流格式不支持（可能需要重新编码）${NC}"
    exit $EXIT_CODE
else
    echo ""
    echo -e "${GREEN}推流已停止${NC}"
fi



