#!/bin/bash

# ============================================
# MinIO 数据上传脚本
# ============================================
# 使用方法：
#   ./upload_minio_data.sh
#
# 功能：
#   1. 等待 MinIO 服务就绪
#   2. 创建必要的存储桶
#   3. 上传本地数据到 MinIO
#
# 选项：
#   --non-interactive  跳过控制台登录确认提示（供自动化脚本调用）
#   --prefer-mc        优先使用 Docker 版 mc 上传（CentOS7 推荐）
#   --force-mc         强制使用 mc，不使用 Python SDK
#   --force-python     强制使用 Python SDK
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 日志文件配置
LOG_DIR="${SCRIPT_DIR}/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/upload_minio_data_$(date +%Y%m%d_%H%M%S).log"

NON_INTERACTIVE=false
PREFER_MC=false
FORCE_MC=false
FORCE_PYTHON=false

MINIO_ENDPOINT="127.0.0.1:9000"
MINIO_ACCESS_KEY="minioadmin"
MINIO_SECRET_KEY="basiclab@iot975248395"
MINIO_MC_NETWORK="host"
MC_IMAGE="minio/mc:latest"

BUCKET_LIST=(
    "dataset" "datasets" "export-bucket" "inference-inputs"
    "inference-results" "models" "snap-space" "record-space" "alert-images"
    "plate-models" "plate-train-results" "plate-train-logs" "plate-inference-results"
)

# 初始化日志文件
echo "=========================================" >> "$LOG_FILE"
echo "MinIO 数据上传脚本日志" >> "$LOG_FILE"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "=========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 日志输出函数（去掉颜色代码后写入日志文件）
log_to_file() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    # 去掉 ANSI 颜色代码
    local clean_message=$(echo "$message" | sed -r "s/\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[mGK]//g")
    echo "[$timestamp] $clean_message" >> "$LOG_FILE"
}

# 打印带颜色的消息（同时输出到日志文件）
print_info() {
    local message="${BLUE}[INFO]${NC} $1"
    echo -e "$message"
    log_to_file "[INFO] $1"
}

print_success() {
    local message="${GREEN}[SUCCESS]${NC} $1"
    echo -e "$message"
    log_to_file "[SUCCESS] $1"
}

print_warning() {
    local message="${YELLOW}[WARNING]${NC} $1"
    echo -e "$message"
    log_to_file "[WARNING] $1"
}

print_error() {
    local message="${RED}[ERROR]${NC} $1"
    echo -e "$message"
    log_to_file "[ERROR] $1"
}

print_section() {
    local section="$1"
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}  $section${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    log_to_file ""
    log_to_file "========================================="
    log_to_file "  $section"
    log_to_file "========================================="
    log_to_file ""
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --non-interactive) NON_INTERACTIVE=true; shift ;;
            --prefer-mc) PREFER_MC=true; shift ;;
            --force-mc) FORCE_MC=true; PREFER_MC=true; shift ;;
            --force-python) FORCE_PYTHON=true; shift ;;
            -h|--help)
                sed -n '1,20p' "$0"
                exit 0
                ;;
            *) shift ;;
        esac
    done
}

is_centos7() {
    if [ -f /etc/redhat-release ] && grep -qi "centos.*7" /etc/redhat-release 2>/dev/null; then
        return 0
    fi
    if [ -f /etc/os-release ]; then
        # shellcheck source=/dev/null
        source /etc/os-release
        [ "${ID:-}" = "centos" ] && [ "${VERSION_ID%%.*}" = "7" ]
        return $?
    fi
    return 1
}

is_python36_or_older() {
    local ver
    ver=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || echo "0")
    local major minor
    major=$(echo "$ver" | cut -d. -f1)
    minor=$(echo "$ver" | cut -d. -f2)
    [ "${major:-0}" -lt 3 ] 2>/dev/null && return 0
    [ "${major:-0}" -eq 3 ] && [ "${minor:-0}" -le 6 ] 2>/dev/null
}

should_use_mc_upload() {
    [ "$FORCE_PYTHON" = true ] && return 1
    [ "$FORCE_MC" = true ] || [ "$PREFER_MC" = true ] && return 0
    is_centos7 || is_python36_or_older
}

# CentOS7: minio>=7.2 依赖 argon2-cffi 需编译，易缺 libffi/Python.h
install_minio_python_deps_centos7() {
    print_section "CentOS7 安装 MinIO Python SDK 依赖"

    if [ "$EUID" -eq 0 ]; then
        yum install -y gcc python3-devel libffi-devel openssl-devel 2>/dev/null || \
            yum install -y gcc python36-devel libffi-devel openssl-devel || {
            print_error "无法安装 gcc/python3-devel/libffi-devel"
            return 1
        }
    elif command -v sudo >/dev/null 2>&1; then
        sudo yum install -y gcc python3-devel libffi-devel openssl-devel 2>/dev/null || \
            sudo yum install -y gcc python36-devel libffi-devel openssl-devel || return 1
    else
        print_warning "需要 root 安装编译依赖，将尝试 mc 方式上传"
        return 1
    fi

    print_info "安装 minio==7.1.17（避免 argon2-cffi 编译）..."
    set +e
    pip3 install -i https://mirrors.huaweicloud.com/repository/pypi/simple \
        --trusted-host mirrors.huaweicloud.com \
        'minio==7.1.17' 'urllib3<2' 'certifi<2025' 2>&1 | tee -a "$LOG_FILE"
    local pip_rc=${PIPESTATUS[0]}
    if [ "$pip_rc" -ne 0 ]; then
        pip3 install 'minio==7.1.17' 'urllib3<2' 2>&1 | tee -a "$LOG_FILE"
        pip_rc=${PIPESTATUS[0]}
    fi
    set -e

    if [ "$pip_rc" -eq 0 ] && python3 -c "import minio" 2>/dev/null; then
        print_success "MinIO Python SDK 安装成功"
        return 0
    fi
    return 1
}

ensure_minio_python_sdk() {
    if python3 -c "import minio" 2>/dev/null; then
        return 0
    fi

    if is_centos7 || is_python36_or_older; then
        install_minio_python_deps_centos7 && return 0
    fi

    print_info "正在安装 minio Python 库..."
    python3 -m pip config set global.break-system-packages true >/dev/null 2>&1 || true
    set +e
    pip3 install minio >/dev/null 2>&1
    local rc=$?
    set -e
    [ "$rc" -eq 0 ] && python3 -c "import minio" 2>/dev/null
}

ensure_mc_image() {
    if docker image inspect "$MC_IMAGE" >/dev/null 2>&1; then
        return 0
    fi
    print_info "拉取 mc 客户端镜像 ${MC_IMAGE} ..."
    set +e
    for img in "docker.m.daocloud.io/minio/mc:latest" "$MC_IMAGE"; do
        if DOCKER_CONTENT_TRUST=0 docker pull "$img"; then
            [ "$img" != "$MC_IMAGE" ] && docker tag "$img" "$MC_IMAGE" 2>/dev/null || true
            set -e
            print_success "mc 镜像就绪: ${MC_IMAGE}"
            return 0
        fi
    done
    set -e
    print_error "无法拉取 minio/mc 镜像"
    return 1
}

# 在容器内执行 mc（minio/mc 镜像无 shell，需挂载配置目录复用 alias）
# 宿主机 9000 不通时走 easyaiot-network + minio-server:9000（与 resolve_minio_endpoint 一致）
mc_docker_run() {
    local mc_config_dir="$1"
    shift
    local net="${MINIO_MC_NETWORK:-host}"
    docker run --rm --network "$net" \
        -v "${mc_config_dir}:/root/.mc" \
        "$MC_IMAGE" "$@"
}

# 使用 Docker 版 mc 创建桶、设置公开策略并上传（CentOS7 无需 pip install minio）
init_minio_with_mc() {
    local minio_base_dir="${SCRIPT_DIR}/../minio"
    ensure_mc_image || return 1

    print_info "使用 Docker mc 客户端上传（--network host，无需 pip install minio）"

    local mc_config_dir
    mc_config_dir=$(mktemp -d /tmp/easyaiot-mc-config.XXXXXX 2>/dev/null || echo "/tmp/easyaiot-mc-config.$$")
    mkdir -p "$mc_config_dir"

    local mc_rc=0
    set +e
    mc_docker_run "$mc_config_dir" alias set easyaiot \
        "http://${MINIO_ENDPOINT}" "${MINIO_ACCESS_KEY}" "${MINIO_SECRET_KEY}" || mc_rc=1

    local bucket
    for bucket in "${BUCKET_LIST[@]}"; do
        mc_docker_run "$mc_config_dir" mb --ignore-existing "easyaiot/${bucket}" || mc_rc=1
        mc_docker_run "$mc_config_dir" anonymous set public "easyaiot/${bucket}" >/dev/null 2>&1 || true
        print_info "存储桶已就绪: ${bucket}"
    done

    local arg bucket_name dir_path object_prefix rel dest
    for arg in "$@"; do
        [ -z "$arg" ] && continue
        IFS=':' read -r bucket_name dir_path object_prefix <<< "$arg"
        [ -d "$dir_path" ] || continue
        rel="${dir_path#${minio_base_dir}/}"
        rel="${rel#/}"
        if [ -n "$object_prefix" ]; then
            dest="easyaiot/${bucket_name}/${object_prefix}"
        else
            dest="easyaiot/${bucket_name}"
        fi
        print_info "mc mirror: /data/${rel} -> ${dest}"
        docker run --rm --network "${MINIO_MC_NETWORK:-host}" \
            -v "${mc_config_dir}:/root/.mc" \
            -v "${minio_base_dir}:/data:ro" \
            "$MC_IMAGE" mirror --overwrite "/data/${rel}" "${dest}" || mc_rc=1
    done
    set -e

    rm -rf "$mc_config_dir"

    if [ "$mc_rc" -eq 0 ]; then
        print_success "mc 上传完成"
        return 0
    fi
    print_error "mc 上传部分失败"
    return 1
}

# 解析可用的 MinIO API 地址：优先宿主机发布端口，否则走 compose 网络（供 mc 容器访问）
resolve_minio_endpoint() {
    if curl -sf --connect-timeout 2 --max-time 5 \
        "http://127.0.0.1:9000/minio/health/live" >/dev/null 2>&1; then
        MINIO_ENDPOINT="127.0.0.1:9000"
        MINIO_MC_NETWORK="host"
        return 0
    fi
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx 'minio-server'; then
        if docker exec minio-server curl -sf --connect-timeout 2 --max-time 5 \
            "http://127.0.0.1:9000/minio/health/live" >/dev/null 2>&1 \
            || [ "$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' minio-server 2>/dev/null)" = "healthy" ]; then
            MINIO_ENDPOINT="minio-server:9000"
            MINIO_MC_NETWORK="easyaiot-network"
            return 0
        fi
    fi
    return 1
}

# 等待 MinIO 服务就绪（宿主机端口 / 容器内 / Docker healthy 任一即可）
_minio_is_ready() {
    resolve_minio_endpoint
}

wait_for_minio() {
    local max_attempts="${MINIO_READY_MAX_ATTEMPTS:-90}"
    local attempt=0

    print_info "等待 MinIO 服务就绪..."
    while [ $attempt -lt $max_attempts ]; do
        if _minio_is_ready; then
            print_success "MinIO 服务已就绪（${MINIO_ENDPOINT}，mc 网络: ${MINIO_MC_NETWORK:-host}）"
            return 0
        fi
        attempt=$((attempt + 1))
        if [ $((attempt % 10)) -eq 0 ]; then
            local st health
            st=$(docker inspect -f '{{.State.Status}}' minio-server 2>/dev/null || echo missing)
            health=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' minio-server 2>/dev/null || echo unknown)
            print_info "等待 MinIO 就绪... (${attempt}/${max_attempts})，容器: ${st}，健康: ${health}"
        fi
        sleep 2
    done

    print_error "MinIO 服务未就绪"
    return 1
}

# 初始化 MinIO 的 Python 脚本（临时文件）
create_minio_init_script() {
    local script_file=$(mktemp)
    cat > "$script_file" << 'PYTHON_SCRIPT'
#!/usr/bin/env python3
import sys
import os
from minio import Minio
from minio.error import S3Error
import mimetypes

def init_minio_buckets_and_upload():
    # MinIO 配置
    minio_endpoint = "localhost:9000"
    minio_access_key = "minioadmin"
    minio_secret_key = "basiclab@iot975248395"
    minio_secure = False
    
    # 存储桶列表
    buckets = ["dataset", "datasets", "export-bucket", "inference-inputs", "inference-results", "models", "snap-space", "alert-images"]
    
    # 数据集目录映射: (bucket_name, directory_path, object_prefix)
    # 参数格式: bucket1:dir1:prefix1 bucket2:dir2:prefix2 ...
    upload_tasks = []
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if ':' in arg:
                parts = arg.split(':')
                if len(parts) >= 2:
                    bucket_name = parts[0]
                    dir_path = parts[1]
                    prefix = parts[2] if len(parts) > 2 else ""
                    upload_tasks.append((bucket_name, dir_path, prefix))
    
    try:
        # 创建 MinIO 客户端
        client = Minio(
            minio_endpoint,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            secure=minio_secure
        )
        
        # 创建存储桶并统一设置公开读写策略
        import json
        created_buckets = 0
        public_policy = lambda bucket_name: {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": [
                        "s3:GetBucketLocation",
                        "s3:ListBucket",
                        "s3:ListBucketMultipartUploads"
                    ],
                    "Resource": [f"arn:aws:s3:::{bucket_name}"]
                },
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": [
                        "s3:ListMultipartUploadParts",
                        "s3:PutObject",
                        "s3:GetObject",
                        "s3:DeleteObject",
                        "s3:AbortMultipartUpload"
                    ],
                    "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                }
            ]
        }
        for bucket_name in buckets:
            try:
                if client.bucket_exists(bucket_name):
                    print(f"BUCKET_EXISTS:{bucket_name}")
                else:
                    client.make_bucket(bucket_name)
                    print(f"BUCKET_CREATED:{bucket_name}")
                    created_buckets += 1
                client.set_bucket_policy(bucket_name, json.dumps(public_policy(bucket_name)))
                print(f"BUCKET_POLICY_PUBLIC:{bucket_name}")
            except S3Error as e:
                print(f"BUCKET_ERROR:{bucket_name}:{str(e)}")
                sys.exit(1)
        
        print(f"BUCKETS_SUCCESS:{created_buckets}/{len(buckets)}")
        
        # 检查存储桶是否已有数据
        def bucket_has_objects(bucket_name, prefix=""):
            """检查存储桶是否已有对象（可选前缀）"""
            try:
                if prefix:
                    objects = list(client.list_objects(bucket_name, prefix=prefix, recursive=False))
                else:
                    objects = list(client.list_objects(bucket_name, recursive=False))
                return len(objects) > 0
            except:
                return False
        
        # 上传数据集（支持递归上传）
        total_upload_count = 0
        total_upload_success = 0
        
        def upload_file_recursive(bucket_name, local_path, object_prefix, root_dir):
            """递归上传文件"""
            upload_count = 0
            upload_success = 0
            
            if os.path.isfile(local_path):
                # 计算相对路径
                rel_path = os.path.relpath(local_path, root_dir)
                # 构建对象名称
                if object_prefix:
                    object_name = f"{object_prefix}/{rel_path}" if not object_prefix.endswith('/') else f"{object_prefix}{rel_path}"
                else:
                    object_name = rel_path
                
                # 统一路径分隔符为 /
                object_name = object_name.replace('\\', '/')
                
                try:
                    # 获取文件 MIME 类型
                    content_type, _ = mimetypes.guess_type(local_path)
                    if not content_type:
                        content_type = "application/octet-stream"
                    
                    # 上传文件
                    client.fput_object(
                        bucket_name,
                        object_name,
                        local_path,
                        content_type=content_type
                    )
                    print(f"UPLOAD_SUCCESS:{bucket_name}:{object_name}")
                    upload_success += 1
                except S3Error as e:
                    print(f"UPLOAD_ERROR:{bucket_name}:{object_name}:{str(e)}")
                upload_count += 1
            elif os.path.isdir(local_path):
                # 递归处理子目录
                for item in os.listdir(local_path):
                    item_path = os.path.join(local_path, item)
                    sub_count, sub_success = upload_file_recursive(bucket_name, item_path, object_prefix, root_dir)
                    upload_count += sub_count
                    upload_success += sub_success
            
            return upload_count, upload_success
        
        for bucket_name, dataset_dir, object_prefix in upload_tasks:
            if dataset_dir and os.path.isdir(dataset_dir):
                # 直接执行上传，不管存储桶是否已有数据
                upload_count, upload_success = upload_file_recursive(bucket_name, dataset_dir, object_prefix, dataset_dir)
                
                print(f"UPLOAD_RESULT:{bucket_name}:{upload_success}/{upload_count}")
                total_upload_count += upload_count
                total_upload_success += upload_success
            else:
                print(f"UPLOAD_SKIP:{bucket_name}:数据集目录不存在或无效: {dataset_dir}")
        
        if total_upload_count > 0:
            print(f"UPLOAD_TOTAL:{total_upload_success}/{total_upload_count}")
        
        print("INIT_SUCCESS")
        sys.exit(0)
        
    except Exception as e:
        print(f"INIT_ERROR:{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    init_minio_buckets_and_upload()
PYTHON_SCRIPT
    echo "$script_file"
}

# 初始化 MinIO 存储桶和数据
init_minio_with_python() {
    local python_script=$(create_minio_init_script)
    local output_file=$(mktemp)
    
    # 检查 Python 和 minio 库
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装，无法初始化 MinIO"
        rm -f "$python_script" "$output_file"
        return 1
    fi
    
    if ! ensure_minio_python_sdk; then
        print_error "无法安装 MinIO Python SDK"
        rm -f "$python_script" "$output_file"
        return 1
    fi
    
    # 执行 Python 脚本，传递所有参数（只给所有者添加执行权限，避免需要 root 权限）
    chmod u+x "$python_script"
    python3 "$python_script" "$@" > "$output_file" 2>&1
    local exit_code=$?
    
    # 解析输出
    local buckets_created=0
    local buckets_total=0
    local upload_success=0
    local upload_total=0
    
    while IFS= read -r line || [ -n "$line" ]; do
        if [[ $line == BUCKET_EXISTS:* ]]; then
            local bucket_name="${line#BUCKET_EXISTS:}"
            print_info "存储桶 $bucket_name 已存在，跳过创建"
        elif [[ $line == BUCKET_CREATED:* ]]; then
            local bucket_name="${line#BUCKET_CREATED:}"
            print_success "存储桶 $bucket_name 创建成功"
            buckets_created=$((buckets_created + 1))
        elif [[ $line == BUCKET_ERROR:* ]]; then
            local error="${line#BUCKET_ERROR:}"
            print_error "存储桶创建失败: $error"
        elif [[ $line == BUCKETS_SUCCESS:* ]]; then
            local result="${line#BUCKETS_SUCCESS:}"
            IFS='/' read -r created_count total_count <<< "$result"
            buckets_total=$total_count
            # 只在没有单独计算时使用汇总数据
            if [ $buckets_created -eq 0 ]; then
                buckets_created=$created_count
            fi
        elif [[ $line == UPLOAD_SUCCESS:* ]]; then
            local upload_info="${line#UPLOAD_SUCCESS:}"
            # 格式可能是 bucket:object_name 或 object_name
            if [[ $upload_info == *:* ]]; then
                local bucket_name="${upload_info%%:*}"
                local object_name="${upload_info#*:}"
                print_info "文件上传成功 [$bucket_name]: $object_name"
            else
                print_info "文件上传成功: $upload_info"
            fi
            upload_success=$((upload_success + 1))
        elif [[ $line == UPLOAD_ERROR:* ]]; then
            local error_info="${line#UPLOAD_ERROR:}"
            # 格式可能是 bucket:object_name:error 或 object_name:error
            if [[ $error_info == *:*:* ]]; then
                local parts=(${error_info//:/ })
                local bucket_name="${parts[0]}"
                local object_name="${parts[1]}"
                local error_msg="${error_info#${bucket_name}:${object_name}:}"
                print_warning "文件上传失败 [$bucket_name]: $object_name - $error_msg"
            else
                print_warning "文件上传失败: $error_info"
            fi
        elif [[ $line == UPLOAD_RESULT:* ]]; then
            local result="${line#UPLOAD_RESULT:}"
            # 格式可能是 bucket:success/total 或 success/total
            if [[ $result == *:* ]]; then
                local bucket_result="${result#*:}"
                IFS='/' read -r success_count total_count <<< "$bucket_result"
                upload_total=$((upload_total + total_count))
                upload_success=$((upload_success + success_count))
            else
                IFS='/' read -r success_count total_count <<< "$result"
                upload_total=$total_count
                if [ $upload_success -eq 0 ]; then
                    upload_success=$success_count
                fi
            fi
        elif [[ $line == UPLOAD_TOTAL:* ]]; then
            local result="${line#UPLOAD_TOTAL:}"
            IFS='/' read -r success_count total_count <<< "$result"
            upload_total=$total_count
            upload_success=$success_count
        elif [[ $line == UPLOAD_SKIP:* ]]; then
            local reason="${line#UPLOAD_SKIP:}"
            print_warning "跳过上传: $reason"
        elif [[ $line == INIT_ERROR:* ]]; then
            local error="${line#INIT_ERROR:}"
            print_error "MinIO 初始化失败: $error"
        fi
    done < "$output_file"
    
    # 清理临时文件
    rm -f "$python_script" "$output_file"
    
    if [ $exit_code -eq 0 ]; then
        if [ $buckets_total -gt 0 ]; then
            print_info "存储桶创建: ${GREEN}$buckets_created${NC} / $buckets_total"
        fi
        if [ $upload_total -gt 0 ]; then
            print_info "文件上传: ${GREEN}$upload_success${NC} / $upload_total"
        fi
        return 0
    else
        return 1
    fi
}

# 初始化 MinIO 存储桶和数据
init_minio() {
    print_section "初始化 MinIO 存储桶和数据"
    
    # 等待 MinIO 就绪
    if ! wait_for_minio; then
        print_error "MinIO 未就绪，无法初始化存储桶"
        return 1
    fi
    
    # MinIO 数据源目录
    local minio_base_dir="${SCRIPT_DIR}/../minio"
    
    # 定义存储桶和目录映射关系
    # 格式: "bucket_name:relative_path:object_prefix"
    # relative_path 相对于 minio_base_dir
    # object_prefix 是上传到存储桶时的对象前缀（可选）
    local bucket_mappings=(
        # 格式: "bucket_name:relative_path:object_prefix"
        # dataset/3 目录的内容上传到 dataset 存储桶，对象路径前缀为 "3"
        # 例如: dataset/3/xxx.jpg -> dataset 存储桶中的 3/xxx.jpg
        "dataset:dataset/3:3"
        # 其他目录直接上传到对应的存储桶，保持原有目录结构
        "datasets:datasets:"
        "export-bucket:export-bucket:"
        "inference-inputs:inference-inputs:"
        "inference-results:inference-results:"
        "models:models:"
        "snap-space:snap-space:"
        "plate-models:plate-models:"
        "plate-train-results:plate-train-results:"
        "plate-train-logs:plate-train-logs:"
        "plate-inference-results:plate-inference-results:"
        # alert-images 存储桶用于存储告警图片（不需要上传初始数据）
    )
    
    # 构建上传任务参数
    local upload_args=()
    
    for mapping in "${bucket_mappings[@]}"; do
        IFS=':' read -r bucket_name relative_path object_prefix <<< "$mapping"
        
        # 构建完整目录路径
        local full_dir_path="${minio_base_dir}/${relative_path}"
        
        # 检查目录是否存在
        if [ -d "$full_dir_path" ]; then
            # 如果 object_prefix 为空，则使用空字符串
            if [ -z "$object_prefix" ]; then
                upload_args+=("${bucket_name}:${full_dir_path}:")
            else
                upload_args+=("${bucket_name}:${full_dir_path}:${object_prefix}")
            fi
            print_info "找到目录: $full_dir_path -> 存储桶: $bucket_name${object_prefix:+ (前缀: $object_prefix)}"
        else
            print_warning "目录不存在，跳过: $full_dir_path"
        fi
    done
    
    local init_result=0
    local upload_method="python"
    if should_use_mc_upload; then
        upload_method="mc"
        print_info "上传方式: Docker mc（CentOS7 / 旧 Python 推荐）"
    fi

    run_upload() {
        if [ "$upload_method" = "mc" ]; then
            init_minio_with_mc "$@"
        else
            init_minio_with_python "$@"
        fi
    }

    if [ ${#upload_args[@]} -gt 0 ]; then
        if run_upload "${upload_args[@]}"; then
            print_success "MinIO 初始化完成！"
            init_result=0
        elif [ "$upload_method" = "python" ]; then
            print_warning "Python 上传失败，改用 Docker mc ..."
            upload_method="mc"
            run_upload "${upload_args[@]}" && init_result=0 || init_result=1
        else
            init_result=1
        fi
    else
        print_warning "没有可用的数据集目录，仅创建存储桶"
        if run_upload; then
            print_success "MinIO 存储桶创建完成！"
            init_result=0
        elif [ "$upload_method" = "python" ]; then
            upload_method="mc"
            run_upload && init_result=0 || init_result=1
        else
            init_result=1
        fi
    fi
    
    # 如果初始化成功，提示用户登录 MinIO 管理平台
    if [ $init_result -eq 0 ]; then
        echo ""
        print_section "MinIO 管理平台登录提示"
        echo ""
        print_warning "重要提示：为了确保图像数据能够正常显示，请登录一次 MinIO 管理平台"
        print_info "  访问地址: http://localhost:9001"
        print_info "  用户名: minioadmin"
        print_info "  密码: basiclab@iot975248395"
        echo ""
        print_info "登录后，系统会自动完成必要的初始化配置，图像数据才能正常显示"
        echo ""
        
        if [ "$NON_INTERACTIVE" = true ]; then
            print_info "非交互模式：请稍后访问 http://localhost:9001 登录一次控制台（图像显示需要）"
        fi
        while [ "$NON_INTERACTIVE" != true ]; do
            echo -ne "${YELLOW}[提示]${NC} 是否已经登录过 MinIO 管理平台？(y/N): "
            read -r response
            case "$response" in
                [yY][eE][sS]|[yY])
                    print_success "确认已登录 MinIO 管理平台，继续执行..."
                    break
                    ;;
                [nN][oO]|[nN]|"")
                    print_warning "建议稍后登录 MinIO 管理平台以确保图像数据正常显示"
                    print_info "您可以稍后访问: http://localhost:9001"
                    break
                    ;;
                *)
                    print_warning "请输入 y 或 n"
                    ;;
            esac
        done
    fi
    
    return $init_result
}

# 主函数
main() {
    parse_args "$@"
    print_section "开始 MinIO 数据上传"

    if init_minio; then
        print_success "MinIO 数据上传完成！"
        echo ""
        print_info "日志文件已保存到: $LOG_FILE"
        return 0
    else
        print_error "MinIO 数据上传失败"
        echo ""
        print_info "日志文件已保存到: $LOG_FILE"
        return 1
    fi
}

# 运行主函数
main "$@"

# 脚本结束时记录日志文件路径
if [ -n "$LOG_FILE" ] && [ -f "$LOG_FILE" ]; then
    echo "" >> "$LOG_FILE"
    echo "=========================================" >> "$LOG_FILE"
    echo "脚本结束时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
    echo "=========================================" >> "$LOG_FILE"
fi
