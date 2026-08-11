#!/bin/bash
# ============================================
# EasyAIoT 项目磁盘占用分析工具
# ============================================
# 分析项目多个关键位置的磁盘占用，输出易读报告，
# 帮助非技术人员快速判断是否为磁盘满、数据目录膨胀等问题。
#
# 用法:
#   ./analyze_disk_usage.sh
#   ./analyze_disk_usage.sh --save
#   ./analyze_disk_usage.sh --top 15
# ============================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# shellcheck source=deploy_profile.sh
source "${SCRIPT_DIR}/deploy_profile.sh"

SAVE_OUTPUT=false
TOP_N=10
MEDIA_TOP_N=10
REPORT_FILE=""

MINIO_DATA_DIR="${SCRIPT_DIR}/minio_data/data"
MINIO_RECORD_SPACE_DIR="${MINIO_DATA_DIR}/record-space"
MINIO_ALERT_IMAGES_DIR="${MINIO_DATA_DIR}/alert-images"
LOCAL_ALERT_IMAGES_DIR="${PROJECT_ROOT}/VIDEO/alert_images"

# SRS 本地录像目录候选（SRS 录制 → 上传 MinIO record-space → 默认删除本地；积压时与 MinIO 双重占用）
LOCAL_PLAYBACK_CANDIDATES=(
    "${MEDIA_RECORD_DIR:-}|MEDIA_RECORD_DIR（本地录像根目录）"
    "${SRS_RECORD_DIR:-}|SRS_RECORD_DIR（本地录像根目录）"
    "${EASYAIOT_MEDIA_ROOT:-/mnt/easyaiot-media}/playbacks|NFS 媒体根 playbacks（EASYAIOT_MEDIA_ROOT）"
    "${HOME}/easyaiot/media/playbacks|~/easyaiot/media/playbacks（无 sudo 本地 bind）"
    "${HOME}/easyaiot/data/playbacks|~/easyaiot/data/playbacks（历史路径）"
    "${SCRIPT_DIR}/srs_data/playbacks|中间件 srs_data/playbacks 挂载"
    "/data/playbacks|容器 /data/playbacks 常见宿主机映射"
)

# 本地告警图片中转（上传 MinIO alert-images 前落盘，与 VIDEO/iot-sink 卷挂载一致）
LOCAL_ALERT_IMAGE_CANDIDATES=(
    "${ALERT_IMAGES_DIR:-}|ALERT_IMAGES_DIR 环境变量"
    "${EASYAIOT_MEDIA_ROOT:-/mnt/easyaiot-media}/alert_images|NFS alert_images"
    "${HOME}/easyaiot/media/alert_images|~/easyaiot/media/alert_images"
    "${HOME}/easyaiot/data/alert_images|~/easyaiot/data/alert_images（历史）"
)

print_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
print_ok()      { echo -e "${GREEN}[OK]${NC} $1"; }
print_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_err()     { echo -e "${RED}[ERROR]${NC} $1"; }
print_section() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

show_help() {
    cat <<'EOF'
用法: ./analyze_disk_usage.sh [选项]

选项:
  --save           保存报告到 .scripts/docker/logs/disk_usage_*.log
  --top <n>        展示项目下最大的 n 个子目录（默认 10）
  -h, --help       显示帮助
EOF
}

human_du() {
    local path="$1"
    if [ ! -e "$path" ]; then
        echo "不存在"
        return 0
    fi
    local size
    size="$(du -sh "$path" 2>/dev/null | awk '{print $1; exit}')"
    if [ -n "$size" ]; then
        echo "$size"
    else
        echo "无法统计"
    fi
}

df_line() {
    local path="$1"
    if [ ! -e "$path" ]; then
        path="$PROJECT_ROOT"
    fi
    df -h "$path" 2>/dev/null | tail -1 | awk '{printf "挂载点=%s  总=%s  已用=%s(%s)  可用=%s\n", $6, $2, $3, $5, $4}'
}

parse_use_percent() {
    local path="$1"
    df "$path" 2>/dev/null | tail -1 | awk '{gsub(/%/,"",$5); print $5}'
}

print_path_row() {
    local label="$1"
    local rel="$2"
    local full="${PROJECT_ROOT}/${rel}"
    local size
    size="$(human_du "$full")"
    printf "  %-28s %8s   %s\n" "$label" "$size" "$rel"
}

print_path_row_abs() {
    local label="$1"
    local full="$2"
    local rel_hint="${3:-$full}"
    local size
    size="$(human_du "$full")"
    printf "  %-32s %8s   %s\n" "$label" "$size" "$rel_hint"
}

count_files_under() {
    local path="$1"
    local maxdepth="${2:-6}"
    if [ ! -d "$path" ]; then
        echo "0"
        return 0
    fi
    find "$path" -maxdepth "$maxdepth" -type f 2>/dev/null | wc -l | awk '{print $1}'
}

list_record_space_devices() {
    local path="$1"
    local top_n="$2"
    if [ ! -d "$path" ]; then
        echo "  (目录不存在)"
        return 0
    fi
    find "$path" -mindepth 1 -maxdepth 1 -type d 2>/dev/null \
        | while IFS= read -r device_dir; do
            [ -n "$device_dir" ] || continue
            local bytes device_id
            bytes="$(du -sb "$device_dir" 2>/dev/null | awk '{print $1}')"
            [ -n "$bytes" ] || continue
            device_id="$(basename "$device_dir")"
            [[ "$device_id" == *__XLDIR__* ]] && continue
            echo "$bytes $device_id"
        done \
        | sort -nr \
        | head -n "$top_n" \
        | while read -r bytes device_id; do
            printf "  %8s  device_id=%s\n" "$(bytes_to_human "$bytes")" "$device_id"
        done
}

bytes_to_human() {
    local bytes="$1"
    if command -v numfmt >/dev/null 2>&1; then
        numfmt --to=iec-i --suffix=B "$bytes" 2>/dev/null || echo "${bytes}B"
    else
        awk -v b="$bytes" 'BEGIN {
            split("B KiB MiB GiB TiB", u, " ");
            i = 1;
            while (b >= 1024 && i < 5) { b /= 1024; i++ }
            printf "%.1f%s", b, u[i]
        }'
    fi
}

list_record_space_by_date() {
    local path="$1"
    local top_n="$2"
    if [ ! -d "$path" ]; then
        echo "  (目录不存在)"
        return 0
    fi
    # 路径形如 record-space/<device_id>/YYYY/MM/DD，跨设备按日期汇总
    find "$path" -mindepth 4 -maxdepth 4 -type d 2>/dev/null \
        | while IFS= read -r day_dir; do
            [ -n "$day_dir" ] || continue
            local bytes date_key
            bytes="$(du -sb "$day_dir" 2>/dev/null | awk '{print $1}')"
            [ -n "$bytes" ] || continue
            date_key="$(echo "$day_dir" | awk -F/ '{print $(NF-2)"/"$(NF-1)"/"$NF}')"
            echo "$bytes $date_key"
        done \
        | awk '{ agg[$2] += $1 } END { for (k in agg) print agg[k], k }' \
        | sort -nr \
        | head -n "$top_n" \
        | while read -r bytes date_key; do
            printf "  %8s  %s\n" "$(bytes_to_human "$bytes")" "$date_key"
        done
}

list_alert_images_by_date() {
    local path="$1"
    local top_n="$2"
    if [ ! -d "$path" ]; then
        echo "  (目录不存在)"
        return 0
    fi
    # 路径形如 alert-images/YYYY/MM/DD
    find "$path" -mindepth 3 -maxdepth 3 -type d 2>/dev/null \
        | while IFS= read -r day_dir; do
            [ -n "$day_dir" ] || continue
            du -sh "$day_dir" 2>/dev/null
        done \
        | awk '{
            n = split($2, parts, "/");
            if (n >= 3) {
                key = parts[n-2] "/" parts[n-1] "/" parts[n];
                print $1, key
            }
        }' 2>/dev/null \
        | sort -hr \
        | head -n "$top_n" \
        | awk '{printf "  %8s  %s\n", $1, $2}'
}

_expand_path() {
    local raw="$1"
    raw="$(eval echo "$raw")"
    raw="$(echo "$raw" | sed "s|^~|${HOME}|")"
    echo "$raw"
}

_report_dir_if_exists() {
    local label="$1"
    local dir="$2"
    local hint="$3"
    dir="$(_expand_path "$dir")"
    if [ ! -e "$dir" ]; then
        printf "  %-36s %8s   %s\n" "$label" "不存在" "$hint"
        return 1
    fi
    print_path_row_abs "$label" "$dir" "$hint"
    return 0
}

_warn_if_large_dir() {
    local label="$1"
    local dir="$2"
    local warn_bytes="${3:-1073741824}"
    local bytes
    dir="$(_expand_path "$dir")"
    [ -e "$dir" ] || return 0
    bytes="$(du -sb "$dir" 2>/dev/null | awk '{print $1; exit}')"
    if [ -n "$bytes" ] && [ "$bytes" -gt "$warn_bytes" ] 2>/dev/null; then
        print_warn "${label} 占用 $(bytes_to_human "$bytes")，建议重点排查与清理"
    fi
}

_collect_unique_existing_dirs() {
    # 输出去重后的 "path|label" 列表（按首次出现顺序）
    local -a seen=()
    local entry raw label path norm
    for entry in "$@"; do
        raw="${entry%%|*}"
        label="${entry#*|}"
        [ -n "$raw" ] || continue
        path="$(_expand_path "$raw")"
        norm="$(readlink -f "$path" 2>/dev/null || echo "$path")"
        local dup=0 s
        for s in "${seen[@]}"; do
            [ "$s" = "$norm" ] && dup=1 && break
        done
        [ "$dup" -eq 1 ] && continue
        seen+=("$norm")
        echo "${path}|${label}"
    done
}

list_playback_subdirs() {
    local path="$1"
    local sub top_n
    path="$(_expand_path "$path")"
    [ -d "$path" ] || return 0
    echo "  子目录占用（live=监控流 / ai=算法流 / gb28181=国标流）:"
    for sub in live ai gb28181; do
        if [ -d "${path}/${sub}" ]; then
            printf "    %-8s %8s  %s/%s\n" "${sub}/" "$(human_du "${path}/${sub}")" "$path" "$sub"
        fi
    done
    if [ -d "${path}/live" ]; then
        echo "  live 下设备目录 Top ${MEDIA_TOP_N}:"
        find "${path}/live" -mindepth 1 -maxdepth 1 -type d 2>/dev/null \
            | while IFS= read -r dev_dir; do
                [ -n "$dev_dir" ] || continue
                local bytes dev_id flv_count
                bytes="$(du -sb "$dev_dir" 2>/dev/null | awk '{print $1}')"
                [ -n "$bytes" ] || continue
                dev_id="$(basename "$dev_dir")"
                flv_count="$(find "$dev_dir" -type f -name '*.flv' 2>/dev/null | wc -l | awk '{print $1}')"
                echo "$bytes $dev_id $flv_count"
            done \
            | sort -nr \
            | head -n "$MEDIA_TOP_N" \
            | while read -r bytes dev_id flv_count; do
                printf "    %8s  device=%s  flv=%s\n" "$(bytes_to_human "$bytes")" "$dev_id" "$flv_count"
            done
    fi
    local flv_total
    flv_total="$(find "$path" -type f -name '*.flv' 2>/dev/null | wc -l | awk '{print $1}')"
    print_info "本地 .flv 文件总数(估算): ${flv_total}"
}

collect_local_playbacks_report() {
    echo "【3】本地 SRS 录像目录 (playbacks — MinIO 上传前缓冲/回放读取)"
    print_info "流程：SRS 录制 → 本地 playbacks → 上传 MinIO record-space → 默认删除本地（PLAYBACK_DELETE_AFTER_UPLOAD）"
    print_info "若上传积压/失败，本地会与 MinIO 形成双重占用；查看回放时 mini 形态直接读本目录"
    echo ""
    printf "  %-36s %8s   %s\n" "目录说明" "占用" "路径"
    echo "  ------------------------------------------------------------------------------"

    local found=0 entry path label
    while IFS= read -r entry; do
        [ -n "$entry" ] || continue
        path="${entry%%|*}"
        label="${entry#*|}"
        if _report_dir_if_exists "$label" "$path" "$path"; then
            found=1
            local bytes
            path="$(_expand_path "$path")"
            bytes="$(du -sb "$path" 2>/dev/null | awk '{print $1; exit}')"
            _warn_if_large_dir "$label" "$path"
            if [ -n "$bytes" ] && [ "$bytes" -gt 4096 ] 2>/dev/null; then
                echo ""
                list_playback_subdirs "$path"
                echo ""
            fi
        fi
    done < <(_collect_unique_existing_dirs "${LOCAL_PLAYBACK_CANDIDATES[@]}")

    if [ "$found" -eq 0 ]; then
        print_warn "未发现本地 playbacks 目录（可能尚未录制或路径不在默认位置）"
    fi
    echo ""
}

collect_local_alert_images_report() {
    echo "【4】本地告警图片中转目录 (上传 MinIO alert-images 前)"
    print_info "算法/iot-sink 先将告警图写入本地，再异步上传 MinIO；未及时清理时会与【2】双重占用"
    echo ""
    printf "  %-36s %8s   %s\n" "目录说明" "占用" "路径"
    echo "  ------------------------------------------------------------------------------"

    local found=0 entry path label img_count
    while IFS= read -r entry; do
        [ -n "$entry" ] || continue
        path="${entry%%|*}"
        label="${entry#*|}"
        if _report_dir_if_exists "$label" "$path" "$path"; then
            found=1
            path="$(_expand_path "$path")"
            img_count="$(find "$path" -type f \( -name '*.jpg' -o -name '*.jpeg' -o -name '*.png' \) 2>/dev/null | wc -l | awk '{print $1}')"
            print_info "  图片文件数(估算): ${img_count}"
            _warn_if_large_dir "$label" "$path" 524288000
        fi
    done < <(_collect_unique_existing_dirs "${LOCAL_ALERT_IMAGE_CANDIDATES[@]}")

    if [ "$found" -eq 0 ]; then
        print_warn "未发现本地告警图片中转目录"
    fi
    echo ""
}

collect_alert_record_summary() {
    echo "【5】告警录像存储说明"
    ensure_deploy_profile
    if [ "${EASYAIOT_DEPLOY_PROFILE:-full}" = "mini" ]; then
        print_info "mini 形态：告警录像主要在【3】本地 playbacks，不一定写入 MinIO"
    else
        print_info "${EASYAIOT_DEPLOY_PROFILE} 形态：告警录像元数据 record_path 指向 MinIO record-space（见【1】）"
        print_info "在线回放走 MinIO 下载 API；本地【3】为 SRS 录制/upload 缓冲，不应长期堆积"
    fi
    echo ""
    print_info "排查提示:"
    echo "  - MinIO 录像膨胀 → 清理【1】record-space 过期日期目录"
    echo "  - 本地 playbacks 膨胀 → 检查 DVR 上传是否失败；确认 PLAYBACK_DELETE_AFTER_UPLOAD=true"
    echo "  - 告警图片膨胀 → 清理【2】MinIO alert-images 与【4】本地 alert_images"
    echo "  - 告警无录像 → 查【1】对应 device_id 时间点是否有 .flv，或【3】live 目录是否有残留"
}

collect_media_storage_report() {
    print_section "录像与告警媒体占用（重点分析）"
    print_info "以下目录通常是磁盘占用的主要来源（MinIO 归档 + 本地上传/回放缓冲），请优先关注。"
    echo ""

    # --- MinIO 监控录像 ---
    echo "【1】MinIO 监控录像 (record-space bucket)"
    print_path_row_abs "总占用" "$MINIO_RECORD_SPACE_DIR" ".scripts/docker/minio_data/data/record-space"
    if [ -d "$MINIO_RECORD_SPACE_DIR" ]; then
        local file_count
        file_count="$(count_files_under "$MINIO_RECORD_SPACE_DIR" 8)"
        print_info "录像文件数(估算): ${file_count}  |  MinIO 桶名: record-space"
        echo ""
        echo "  按设备目录 Top ${MEDIA_TOP_N}（device_id）:"
        list_record_space_devices "$MINIO_RECORD_SPACE_DIR" "$MEDIA_TOP_N"
        echo ""
        echo "  按日期 Top ${MEDIA_TOP_N}（YYYY/MM/DD，跨设备汇总）:"
        list_record_space_by_date "$MINIO_RECORD_SPACE_DIR" "$MEDIA_TOP_N"
    else
        print_warn "目录不存在，可能尚未产生 MinIO 录像或未部署 MinIO"
    fi
    echo ""

    # --- MinIO 告警图片 ---
    echo "【2】MinIO 告警图片 (alert-images bucket)"
    print_path_row_abs "总占用" "$MINIO_ALERT_IMAGES_DIR" ".scripts/docker/minio_data/data/alert-images"
    if [ -d "$MINIO_ALERT_IMAGES_DIR" ]; then
        local img_count
        img_count="$(count_files_under "$MINIO_ALERT_IMAGES_DIR" 6)"
        print_info "图片文件数(估算): ${img_count}  |  MinIO 桶名: alert-images"
        echo ""
        echo "  按日期 Top ${MEDIA_TOP_N}（YYYY/MM/DD）:"
        list_alert_images_by_date "$MINIO_ALERT_IMAGES_DIR" "$MEDIA_TOP_N"
    else
        print_warn "目录不存在，可能尚未产生告警图片或未部署 MinIO"
    fi
    echo ""

    collect_local_playbacks_report
    collect_local_alert_images_report
    collect_alert_record_summary
}

collect_key_paths_report() {
    print_section "关键目录占用（项目内）"
    printf "  %-28s %8s   %s\n" "说明" "占用" "路径"
    echo "  ------------------------------------------------------------------------------"

    print_path_row "项目根目录" "."
    print_path_row "Docker/中间件目录" ".scripts/docker"
    print_path_row "PostgreSQL 数据" ".scripts/docker/db_data"
    print_path_row "TDengine 数据" ".scripts/docker/taos_data"
    print_path_row "Redis 数据" ".scripts/docker/redis_data"
    print_path_row "Kafka 数据" ".scripts/docker/mq_data"
    print_path_row "MinIO 对象存储(合计)" ".scripts/docker/minio_data"
    print_path_row "  └ MinIO 监控录像" ".scripts/docker/minio_data/data/record-space"
    print_path_row "  └ MinIO 告警图片" ".scripts/docker/minio_data/data/alert-images"
    print_path_row "  └ 本地告警图(上传前)" "VIDEO/alert_images"
    print_path_row "Milvus 向量库" ".scripts/docker/milvus_data"
    print_path_row "SRS 配置/数据" ".scripts/docker/srs_data"
    print_path_row "NodeRED 数据" ".scripts/docker/nodered_data"
    print_path_row "Nacos 等中间件日志" ".scripts/docker/standalone-logs"
    print_path_row "安装/运行脚本日志" ".scripts/docker/logs"
    print_path_row "Device 模块" "DEVICE"
    print_path_row "AI 模块" "AI"
    print_path_row "RTC 模块" "RTC"
    print_path_row "Video 模块" "VIDEO"
    print_path_row "Web 模块" "WEB"
    print_path_row "App 模块" "APP"
}

collect_filesystem_report() {
    print_section "文件系统空间（宿主机）"
    print_info "项目所在分区:"
    df_line "$PROJECT_ROOT"
    echo ""
    print_info "根分区 (/):"
    df_line "/"

    local pct
    pct="$(parse_use_percent "$PROJECT_ROOT" 2>/dev/null || echo 0)"
    if [ "$pct" -ge 95 ] 2>/dev/null; then
        print_err "磁盘使用率 >= 95%，极可能导致服务启动失败或数据库异常！"
    elif [ "$pct" -ge 90 ] 2>/dev/null; then
        print_warn "磁盘使用率 >= 90%，建议尽快清理 MinIO 录像、Docker 镜像或旧日志。"
    else
        print_ok "项目分区空间尚有余量（使用率 ${pct}%）。"
    fi
}

collect_docker_report() {
    print_section "Docker 磁盘占用"
    if ! command -v docker >/dev/null 2>&1; then
        print_warn "Docker 未安装，跳过 Docker 统计"
        return 0
    fi
    if ! docker info >/dev/null 2>&1; then
        print_warn "无法连接 Docker daemon，跳过 Docker 统计"
        return 0
    fi

    local docker_root
    docker_root="$(docker info 2>/dev/null | awk -F': ' '/Docker Root Dir/{print $2}' | head -1)"
    if [ -n "$docker_root" ]; then
        print_info "Docker 数据目录: ${docker_root} ($(human_du "$docker_root"))"
        df_line "$docker_root"
    fi

    echo ""
    print_info "docker system df:"
    docker system df 2>/dev/null || print_warn "无法执行 docker system df"
}

collect_top_dirs_report() {
    print_section "项目内占用 Top ${TOP_N}（一级子目录/文件）"
    if ! command -v du >/dev/null 2>&1; then
        print_warn "du 命令不可用"
        return 0
    fi
    du -xh --max-depth=1 "$PROJECT_ROOT" 2>/dev/null \
        | sort -hr \
        | head -n "$((TOP_N + 1))" \
        | awk -v root="$PROJECT_ROOT" 'NR>1 {printf "  %8s  %s\n", $1, $2}'
}

collect_profile_hint() {
    print_section "部署形态与排查建议"
    ensure_deploy_profile
    print_info "当前部署形态: $(_deploy_profile_desc) (${EASYAIOT_DEPLOY_PROFILE})"
    echo ""
    echo "常见磁盘问题与处理建议:"
    echo "  1) MinIO 监控录像(record-space)过大 → 见【1】按设备/日期清理"
    echo "  2) 本地 playbacks 过大 → 见【3】检查 live/ai 子目录；确认 DVR 上传 MinIO 正常、PLAYBACK_DELETE_AFTER_UPLOAD=true"
    echo "  3) MinIO 告警图片(alert-images)过大 → 见【2】按日期清理"
    echo "  4) 本地 alert_images 过大 → 见【4】清理 VIDEO/alert_images 中已上传残留"
    echo "  5) 告警录像缺失 → full/standard 查【1】；mini 查【3】playbacks/live"
    echo "  6) Docker 镜像/容器过多 → cleanup_docker_space.sh 或 install_linux.sh clean（先备份）"
    echo "  7) 中间件日志膨胀 → standalone-logs 与 logs 目录"
    echo "  8) 磁盘满导致数据库异常 → 优先释放【1】【3】空间后 restart 服务"
}

parse_args() {
    while [ $# -gt 0 ]; do
        case "$1" in
            --save)
                SAVE_OUTPUT=true
                ;;
            --top)
                shift
                TOP_N="${1:-10}"
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                print_err "未知参数: $1"
                show_help
                exit 2
                ;;
        esac
        shift
    done
}

run_report() {
    local report=""
    report+="$( {
        echo "EasyAIoT 项目磁盘占用分析报告"
        echo "生成时间: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "项目路径: ${PROJECT_ROOT}"
        echo ""
        collect_filesystem_report
        collect_docker_report
        collect_media_storage_report
        collect_key_paths_report
        collect_top_dirs_report
        collect_profile_hint
    } 2>&1 )"

    echo "$report"

    if [ "$SAVE_OUTPUT" = true ]; then
        mkdir -p "${SCRIPT_DIR}/logs"
        REPORT_FILE="${SCRIPT_DIR}/logs/disk_usage_$(date +%Y%m%d_%H%M%S).log"
        echo "$report" > "$REPORT_FILE"
        print_ok "报告已保存: $REPORT_FILE"
        print_info "可将该文件直接提供给技术支持人员分析。"
    fi

    print_section "磁盘占用分析完成"
}

main() {
    parse_args "$@"
    run_report
}

main "$@"
