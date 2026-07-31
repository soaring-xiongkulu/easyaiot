#!/bin/bash
# EasyAIoT Docker Compose GPU 配置辅助（AI / VIDEO 共用）

GPU_AVAILABLE=false
GPU_HARDWARE_DETECTED=false

type print_info >/dev/null 2>&1 || print_info() { echo "[INFO] $1"; }
type print_warning >/dev/null 2>&1 || print_warning() { echo "[WARN] $1"; }
type print_success >/dev/null 2>&1 || print_success() { echo "[OK] $1"; }

check_gpu() {
    if ! command -v nvidia-smi >/dev/null 2>&1; then
        print_warning "未检测到 NVIDIA GPU，将使用 CPU 模式运行"
        GPU_HARDWARE_DETECTED=false
        GPU_AVAILABLE=false
        return
    fi

    GPU_HARDWARE_DETECTED=true
    print_info "检测到 NVIDIA GPU:"
    nvidia-smi --query-gpu=name,driver_version --format=csv,noheader,nounits 2>/dev/null | while IFS=, read -r name version; do
        echo "  - GPU: $name (驱动版本: $version)"
    done

    if ! nvidia-smi >/dev/null 2>&1; then
        print_warning "nvidia-smi 不可用，将使用 CPU 模式运行"
        GPU_AVAILABLE=false
        return
    fi

    if ! docker info --format '{{.Runtimes}}' 2>/dev/null | grep -q "nvidia"; then
        print_warning "Docker 未配置 NVIDIA runtime，将使用 CPU 模式运行"
        GPU_AVAILABLE=false
        return
    fi

    if docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi >/dev/null 2>&1; then
        print_success "NVIDIA Container Toolkit 已正确配置"
        GPU_AVAILABLE=true
        return
    fi

    print_warning "GPU 容器测试失败（NVML/CDI 不可用），将使用 CPU 模式运行"
    GPU_AVAILABLE=false
}

configure_compose_gpu() {
    local compose_file="${1:-docker-compose.yaml}"
    local env_file="${2:-.env.docker}"
    # 可选：服务名（默认 video-service，AI 也可传入 ai-service）
    local service_name="${3:-}"
    local override_file=".docker-compose.gpu.override.yaml"

    if [ ! -f "$compose_file" ]; then
        print_warning "未找到 compose 文件: $compose_file"
        return
    fi

    # 从 compose 推断首个服务名（未显式传入时）
    if [ -z "$service_name" ]; then
        service_name=$(awk '/^services:/{s=1; next} s && /^  [A-Za-z0-9_-]+:/{gsub(/:/,""); gsub(/^ +/,""); print; exit}' "$compose_file" 2>/dev/null || true)
        service_name="${service_name:-video-service}"
    fi

    if [ "$GPU_AVAILABLE" = true ]; then
        print_info "启用 GPU 支持..."
        rm -f "$override_file"
        if grep -qE '^[[:space:]]*# runtime: nvidia' "$compose_file"; then
            sed -i 's/^\([[:space:]]*\)# runtime: nvidia/\1runtime: nvidia/' "$compose_file"
        fi
        if grep -qE '^[[:space:]]*# deploy:' "$compose_file"; then
            sed -i '/^[[:space:]]*# deploy:/,/capabilities:.*gpu/ s/^\([[:space:]]*\)# /\1/' "$compose_file"
        fi
        # 去掉误留的 runtime: runc
        if grep -qE '^[[:space:]]*runtime: runc' "$compose_file"; then
            sed -i '/^[[:space:]]*runtime: runc/d' "$compose_file"
        fi
        if [ -f "$env_file" ] && grep -q '^USE_GPU=' "$env_file"; then
            sed -i 's/^USE_GPU=.*/USE_GPU=True/' "$env_file"
        fi
        print_success "GPU 配置已启用"
    else
        print_info "使用 CPU 模式（GPU 配置已禁用）"
        if grep -qE '^[[:space:]]*runtime: nvidia' "$compose_file"; then
            sed -i 's/^\([[:space:]]*\)runtime: nvidia/\1# runtime: nvidia/' "$compose_file"
        fi
        if grep -qE '^[[:space:]]*deploy:' "$compose_file" && ! grep -qE '^[[:space:]]*# deploy:' "$compose_file"; then
            sed -i '/^[[:space:]]*deploy:/,/capabilities:.*gpu/ s/^\([[:space:]]*\)/\1# /' "$compose_file"
        fi
        if [ -f "$env_file" ] && grep -q '^USE_GPU=' "$env_file"; then
            sed -i 's/^USE_GPU=.*/USE_GPU=False/' "$env_file"
        fi
        # daemon default-runtime=nvidia + 驱动未加载时，PyTorch 镜像（含 nvidia 标签）必须显式 runc
        {
            echo 'services:'
            echo "  ${service_name}:"
            echo '    runtime: runc'
            echo '    environment:'
            echo '      USE_GPU: "False"'
            echo '      NVIDIA_VISIBLE_DEVICES: ""'
        } > "$override_file"
        print_success "已写入 CPU override（runtime: runc）: $override_file"
    fi
}

# 返回 compose 附加 -f 参数（CPU/GPU override 存在时）
gpu_compose_file_args() {
    local base="${1:-docker-compose.yaml}"
    local override=".docker-compose.gpu.override.yaml"
    if [ -f "$override" ]; then
        echo "-f ${base} -f ${override}"
    else
        echo "-f ${base}"
    fi
}
