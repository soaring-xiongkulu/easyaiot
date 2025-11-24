# ============================================
# AI服务 Docker Compose 管理脚本 (Windows)
# ============================================
# 使用方法：
#   .\install_win.ps1 [命令]
#
# 可用命令：
#   install    - 安装并启动服务（首次运行）
#   start      - 启动服务
#   stop       - 停止服务
#   restart    - 重启服务
#   status     - 查看服务状态
#   logs       - 查看服务日志
#   build      - 重新构建镜像
#   clean      - 清理容器和镜像
#   update     - 更新并重启服务
# ============================================

$ErrorActionPreference = "Stop"

# 颜色定义
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# 脚本目录
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $SCRIPT_DIR

# 检查命令是否存在
function Test-Command {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# 检查 Docker 是否安装
function Test-Docker {
    if (-not (Test-Command "docker")) {
        Write-Error "Docker 未安装，请先安装 Docker Desktop"
        Write-Host "安装指南: https://docs.docker.com/get-docker/"
        exit 1
    }
    $version = docker --version
    Write-Success "Docker 已安装: $version"
}

# 检查 Docker Compose 是否安装
function Test-DockerCompose {
    # 先检查 docker-compose 命令
    if (Test-Command "docker-compose") {
        $script:COMPOSE_CMD = "docker-compose"
        $version = docker-compose --version
        Write-Success "Docker Compose 已安装: $version"
        return $true
    }
    
    # 再检查 docker compose 插件
    $result = docker compose version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $script:COMPOSE_CMD = "docker compose"
        Write-Success "Docker Compose 已安装: $result"
        return $true
    }
    
    # 如果都不存在，报错
    Write-Error "Docker Compose 未安装，请先安装 Docker Compose"
    Write-Host "安装指南: https://docs.docker.com/compose/install/"
    exit 1
}

# 检查 GPU 支持
$script:GPU_AVAILABLE = $false
$script:GPU_HARDWARE_DETECTED = $false

# 架构检测
$script:ARCH = ""
$script:DOCKER_PLATFORM = ""
$script:BASE_IMAGE = ""

# 检测服务器架构并验证是否支持
function Get-Architecture {
    Write-Info "检测服务器架构..."
    $arch = (Get-WmiObject Win32_Processor).Architecture
    
    switch ($arch) {
        0 { # x86
            $script:ARCH = "x86_64"
            $script:DOCKER_PLATFORM = "linux/amd64"
            $script:BASE_IMAGE = "pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime"
            Write-Success "检测到架构: x86_64"
            Write-Info "使用 PyTorch CUDA 镜像: $script:BASE_IMAGE"
        }
        5 { # ARM
            Write-Error "检测到 ARM 架构"
            Write-Error "NVIDIA 官方的 CUDA 容器化只支持 x86_64 架构"
            Write-Error "ARM 服务器不支持容器化部署，部署已终止"
            Write-Host ""
            Write-Info "如需在 ARM 服务器上运行，请考虑："
            Write-Info "1. 使用原生 Python 环境直接运行（非容器化）"
            Write-Info "2. 使用支持 ARM 的 CPU 版本 PyTorch（性能较低）"
            exit 1
        }
        9 { # x64
            $script:ARCH = "x86_64"
            $script:DOCKER_PLATFORM = "linux/amd64"
            $script:BASE_IMAGE = "pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime"
            Write-Success "检测到架构: x86_64"
            Write-Info "使用 PyTorch CUDA 镜像: $script:BASE_IMAGE"
        }
        default {
            Write-Error "未识别的架构: $arch"
            Write-Error "本服务仅支持 x86_64 架构，部署已终止"
            exit 1
        }
    }
    
    # 导出环境变量供docker-compose使用
    $env:DOCKER_PLATFORM = $script:DOCKER_PLATFORM
    $env:BASE_IMAGE = $script:BASE_IMAGE
}

# 配置架构相关的docker-compose设置
function Set-Architecture {
    Write-Info "配置 Docker Compose 架构设置..."
    
    # 创建或更新 .env.arch 文件来存储架构配置
    $archFile = ".env.arch"
    if (-not (Test-Path $archFile) -or -not (Select-String -Path $archFile -Pattern "DOCKER_PLATFORM=" -Quiet)) {
        @"
# 架构配置（由install_win.ps1自动生成）
DOCKER_PLATFORM=$script:DOCKER_PLATFORM
BASE_IMAGE=$script:BASE_IMAGE
"@ | Out-File -FilePath $archFile -Encoding utf8
        Write-Success "已创建架构配置文件 .env.arch"
    } else {
        # 更新现有配置
        $content = Get-Content $archFile
        $content = $content | ForEach-Object {
            if ($_ -match "^DOCKER_PLATFORM=") {
                "DOCKER_PLATFORM=$script:DOCKER_PLATFORM"
            } elseif ($_ -match "^BASE_IMAGE=") {
                "BASE_IMAGE=$script:BASE_IMAGE"
            } else {
                $_
            }
        }
        $content | Out-File -FilePath $archFile -Encoding utf8
        Write-Info "已更新架构配置文件 .env.arch"
    }
    
    Write-Success "架构配置完成: $script:ARCH -> $script:DOCKER_PLATFORM"
}

# 检查 NVIDIA Container Toolkit（Windows上通过Docker Desktop配置）
function Test-NvidiaContainerToolkit {
    # Windows上通过Docker Desktop的WSL2后端支持GPU
    # 检查nvidia-smi是否可用
    if (Test-Command "nvidia-smi") {
        $result = nvidia-smi --query-gpu=name,driver_version --format=csv,noheader,nounits 2>&1
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
    }
    return $false
}

# 检查 GPU
function Test-GPU {
    if (Test-Command "nvidia-smi") {
        $script:GPU_HARDWARE_DETECTED = $true
        Write-Info "检测到 NVIDIA GPU:"
        $gpuInfo = nvidia-smi --query-gpu=name,driver_version --format=csv,noheader,nounits 2>&1
        if ($LASTEXITCODE -eq 0) {
            $gpuInfo | ForEach-Object {
                $parts = $_ -split ","
                Write-Host "  - GPU: $($parts[0].Trim()) (驱动版本: $($parts[1].Trim()))"
            }
            
            # Windows上GPU支持通过Docker Desktop配置
            Write-Info "Windows上GPU支持需要Docker Desktop启用WSL2后端和GPU支持"
            Write-Info "请确保Docker Desktop已正确配置GPU支持"
            $script:GPU_AVAILABLE = $true
        } else {
            Write-Warning "无法获取GPU信息"
            $script:GPU_AVAILABLE = $false
        }
    } else {
        Write-Warning "未检测到 NVIDIA GPU，将使用 CPU 模式运行"
        $script:GPU_HARDWARE_DETECTED = $false
        $script:GPU_AVAILABLE = $false
    }
}

# 配置 GPU 支持（如果可用）
function Set-GPU {
    if ($script:GPU_AVAILABLE) {
        Write-Info "启用 GPU 支持..."
        # 读取docker-compose.yaml并取消注释GPU配置
        if (Test-Path "docker-compose.yaml") {
            $content = Get-Content "docker-compose.yaml" -Raw
            if ($content -match "(?s)# deploy:.*?#\s+capabilities: \[gpu\]") {
                $content = $content -replace "(?s)# deploy:.*?#\s+capabilities: \[gpu\]", ($matches[0] -replace "# ", "")
                $content | Out-File -FilePath "docker-compose.yaml" -Encoding utf8 -NoNewline
                Write-Success "GPU 配置已启用"
            }
        }
    } else {
        Write-Info "使用 CPU 模式（GPU 配置已禁用）"
        # 确保GPU配置被注释
        if (Test-Path "docker-compose.yaml") {
            $content = Get-Content "docker-compose.yaml" -Raw
            if ($content -match "(?s)deploy:.*?capabilities: \[gpu\]" -and $content -notmatch "(?s)# deploy:.*?#\s+capabilities: \[gpu\]") {
                $content = $content -replace "(?s)(\s+)deploy:", "`$1# deploy:"
                $content = $content -replace "(?s)(\s+)resources:", "`$1# resources:"
                $content = $content -replace "(?s)(\s+)reservations:", "`$1# reservations:"
                $content = $content -replace "(?s)(\s+)devices:", "`$1# devices:"
                $content = $content -replace "(?s)(\s+)- driver: nvidia", "`$1# - driver: nvidia"
                $content = $content -replace "(?s)(\s+)count: all", "`$1# count: all"
                $content = $content -replace "(?s)(\s+)capabilities: \[gpu\]", "`$1# capabilities: [gpu]"
                $content | Out-File -FilePath "docker-compose.yaml" -Encoding utf8 -NoNewline
            }
        }
    }
}

# 检查并创建 Docker 网络
function Test-Network {
    Write-Info "检查 Docker 网络 easyaiot-network..."
    $networks = docker network ls --format "{{.Name}}" 2>&1
    if ($networks -notcontains "easyaiot-network") {
        Write-Info "网络 easyaiot-network 不存在，正在创建..."
        $result = docker network create easyaiot-network 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "网络 easyaiot-network 已创建"
        } else {
            Write-Error "无法创建网络 easyaiot-network"
            exit 1
        }
    } else {
        Write-Info "网络 easyaiot-network 已存在"
    }
}

# 创建必要的目录
function New-Directories {
    Write-Info "创建必要的目录..."
    @("data/uploads", "data/datasets", "data/models", "data/inference_results", "static/models", "temp_uploads", "model") | ForEach-Object {
        if (-not (Test-Path $_)) {
            New-Item -ItemType Directory -Path $_ -Force | Out-Null
        }
    }
    Write-Success "目录创建完成"
}

# 创建 .env.docker 文件（用于Docker部署）
function New-EnvFile {
    if (-not (Test-Path ".env.docker")) {
        Write-Info ".env.docker 文件不存在，正在创建..."
        if (Test-Path "env.example") {
            Copy-Item "env.example" ".env.docker"
            Write-Success ".env.docker 文件已从 env.example 创建"
            
            # 自动配置中间件连接信息（使用Docker服务名称）
            Write-Info "自动配置中间件连接信息..."
            
            # 更新配置
            $content = Get-Content ".env.docker"
            $content = $content | ForEach-Object {
                if ($_ -match "^DATABASE_URL=") {
                    "DATABASE_URL=postgresql://postgres:iot45722414822@PostgresSQL:5432/iot-ai20"
                } elseif ($_ -match "^NACOS_SERVER=") {
                    "NACOS_SERVER=Nacos:8848"
                } elseif ($_ -match "^MINIO_ENDPOINT=") {
                    "MINIO_ENDPOINT=MinIO:9000"
                } elseif ($_ -match "^MINIO_SECRET_KEY=") {
                    "MINIO_SECRET_KEY=basiclab@iot975248395"
                } elseif ($_ -match "^NACOS_PASSWORD=") {
                    "NACOS_PASSWORD=basiclab@iot78475418754"
                } elseif ($_ -match "^NACOS_NAMESPACE=") {
                    "NACOS_NAMESPACE="
                } else {
                    $_
                }
            }
            $content | Out-File -FilePath ".env.docker" -Encoding utf8
            Write-Success "中间件连接信息已自动配置"
            Write-Info "如需修改其他配置，请编辑 .env.docker 文件"
        } else {
            Write-Error "env.example 文件不存在，无法创建 .env.docker 文件"
            exit 1
        }
    } else {
        Write-Info ".env.docker 文件已存在"
        Write-Info "检查并更新中间件连接信息..."
        
        $content = Get-Content ".env.docker"
        $updated = $false
        $content = $content | ForEach-Object {
            if ($_ -match "^DATABASE_URL=.*(localhost|postgres-server)") {
                $updated = $true
                "DATABASE_URL=postgresql://postgres:iot45722414822@PostgresSQL:5432/iot-ai20"
            } elseif ($_ -match "^NACOS_SERVER=.*(14\.18\.122\.2|localhost|nacos-server)") {
                $updated = $true
                "NACOS_SERVER=Nacos:8848"
            } elseif ($_ -match "^MINIO_ENDPOINT=.*(localhost|minio-server)") {
                $updated = $true
                "MINIO_ENDPOINT=MinIO:9000"
            } elseif ($_ -match "^NACOS_NAMESPACE=.*" -and $_ -notmatch "^NACOS_NAMESPACE=$") {
                $updated = $true
                "NACOS_NAMESPACE="
            } else {
                $_
            }
        }
        if ($updated) {
            $content | Out-File -FilePath ".env.docker" -Encoding utf8
            Write-Info "已更新中间件连接信息"
        }
    }
}

# 安装服务
function Install-Service {
    Write-Info "开始安装 AI 服务..."
    
    Test-Docker
    Test-DockerCompose
    Get-Architecture
    Set-Architecture
    Test-Network
    Test-GPU
    Set-GPU
    New-Directories
    New-EnvFile
    
    Write-Info "构建 Docker 镜像..."
    Write-Info "架构: $script:ARCH, 平台: $script:DOCKER_PLATFORM, 基础镜像: $script:BASE_IMAGE"
    
    $env:BASE_IMAGE = $script:BASE_IMAGE
    $buildOutput = & $COMPOSE_CMD build 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "镜像构建失败"
        exit 1
    }
    $buildOutput | Select-String -Pattern "(error|warning|failed|失败|警告)" -CaseSensitive:$false
    
    Write-Info "启动服务..."
    & $COMPOSE_CMD up -d --quiet-pull 2>&1 | Where-Object { $_ -notmatch "^(Creating|Starting|Pulling|Waiting|Container)" }
    
    Write-Success "服务安装完成！"
    Write-Info "等待服务启动..."
    Start-Sleep -Seconds 5
    
    # 检查服务状态
    Get-Status
    
    Write-Info "服务访问地址: http://localhost:5000"
    Write-Info "健康检查地址: http://localhost:5000/actuator/health"
    Write-Info "查看日志: .\install_win.ps1 logs"
}

# 启动服务
function Start-Service {
    Write-Info "启动服务..."
    Test-Docker
    Test-DockerCompose
    Test-Network
    
    if (-not (Test-Path ".env.docker")) {
        Write-Warning ".env.docker 文件不存在，正在创建..."
        New-EnvFile
    }
    
    & $COMPOSE_CMD up -d --quiet-pull 2>&1 | Where-Object { $_ -notmatch "^(Creating|Starting|Pulling|Waiting|Container)" }
    Write-Success "服务已启动"
    Get-Status
}

# 停止服务
function Stop-Service {
    Write-Info "停止服务..."
    Test-Docker
    Test-DockerCompose
    
    & $COMPOSE_CMD down --remove-orphans 2>&1 | Where-Object { $_ -notmatch "^(Stopping|Removing|Network)" }
    Write-Success "服务已停止"
}

# 重启服务
function Restart-Service {
    Write-Info "重启服务..."
    Test-Docker
    Test-DockerCompose
    
    & $COMPOSE_CMD restart 2>&1 | Where-Object { $_ -notmatch "^(Restarting)" }
    Write-Success "服务已重启"
    Get-Status
}

# 查看服务状态
function Get-Status {
    Write-Info "服务状态:"
    Test-Docker
    Test-DockerCompose
    
    & $COMPOSE_CMD ps 2>&1 | Select-Object -First 20
    
    Write-Host ""
    Write-Info "容器健康状态:"
    $containers = docker ps --filter "name=ai-service" --format "{{.Names}}" 2>&1
    if ($containers -contains "ai-service") {
        docker ps --filter "name=ai-service" --format "table {{.Names}}`t{{.Status}}" 2>&1
        
        $health = docker inspect --format='{{.State.Health.Status}}' ai-service 2>&1
        if ($health -and $health -ne "N/A") {
            Write-Host "健康状态: $health"
        }
    } else {
        Write-Warning "服务未运行"
    }
}

# 查看日志
function Get-Logs {
    param([string]$Follow = "")
    Test-Docker
    Test-DockerCompose
    
    if ($Follow -eq "-f" -or $Follow -eq "--follow") {
        Write-Info "实时查看日志（按 Ctrl+C 退出）..."
        & $COMPOSE_CMD logs -f
    } else {
        Write-Info "查看最近日志..."
        & $COMPOSE_CMD logs --tail=100
    }
}

# 构建镜像
function Build-Image {
    Write-Info "重新构建 Docker 镜像..."
    Test-Docker
    Test-DockerCompose
    Get-Architecture
    Set-Architecture
    
    Write-Info "架构: $script:ARCH, 平台: $script:DOCKER_PLATFORM, 基础镜像: $script:BASE_IMAGE"
    $env:BASE_IMAGE = $script:BASE_IMAGE
    $buildOutput = & $COMPOSE_CMD build --no-cache 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "镜像构建失败"
        exit 1
    }
    $buildOutput | Select-String -Pattern "(error|warning|failed|失败|警告)" -CaseSensitive:$false
    Write-Success "镜像构建完成"
}

# 清理服务
function Clear-Service {
    $response = Read-Host "这将删除容器、镜像和数据卷，确定要继续吗？(y/N)"
    
    if ($response -match "^[yY]") {
        Test-Docker
        Test-DockerCompose
        Write-Info "停止并删除容器..."
        & $COMPOSE_CMD down -v --remove-orphans 2>&1 | Where-Object { $_ -notmatch "^(Stopping|Removing|Network)" }
        
        Write-Info "删除镜像..."
        docker rmi ai-service:latest 2>&1 | Out-Null
        
        Write-Success "清理完成"
    } else {
        Write-Info "已取消清理操作"
    }
}

# 更新服务
function Update-Service {
    Write-Info "更新服务..."
    Test-Docker
    Test-DockerCompose
    Get-Architecture
    Set-Architecture
    Test-Network
    
    Write-Info "拉取最新代码..."
    $result = git pull 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Git pull 失败，继续使用当前代码"
    }
    
    Write-Info "重新构建镜像..."
    Write-Info "架构: $script:ARCH, 平台: $script:DOCKER_PLATFORM, 基础镜像: $script:BASE_IMAGE"
    $env:BASE_IMAGE = $script:BASE_IMAGE
    $buildOutput = & $COMPOSE_CMD build 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "镜像构建失败"
        exit 1
    }
    $buildOutput | Select-String -Pattern "(error|warning|failed|失败|警告)" -CaseSensitive:$false
    
    Write-Info "重启服务..."
    & $COMPOSE_CMD up -d --quiet-pull 2>&1 | Where-Object { $_ -notmatch "^(Creating|Starting|Pulling|Waiting|Container)" }
    
    Write-Success "服务更新完成"
    Get-Status
}

# 显示帮助信息
function Show-Help {
    Write-Host "AI服务 Docker Compose 管理脚本"
    Write-Host ""
    Write-Host "使用方法:"
    Write-Host "  .\install_win.ps1 [命令]"
    Write-Host ""
    Write-Host "可用命令:"
    Write-Host "  install    - 安装并启动服务（首次运行）"
    Write-Host "  start      - 启动服务"
    Write-Host "  stop       - 停止服务"
    Write-Host "  restart    - 重启服务"
    Write-Host "  status     - 查看服务状态"
    Write-Host "  logs       - 查看服务日志"
    Write-Host "  logs -f    - 实时查看服务日志"
    Write-Host "  build      - 重新构建镜像"
    Write-Host "  clean      - 清理容器和镜像"
    Write-Host "  update     - 更新并重启服务"
    Write-Host "  help       - 显示此帮助信息"
    Write-Host ""
}

# 主函数
function Main {
    param([string]$Command = "help", [string]$Arg = "")
    
    switch ($Command.ToLower()) {
        "install" {
            Install-Service
        }
        "start" {
            Start-Service
        }
        "stop" {
            Stop-Service
        }
        "restart" {
            Restart-Service
        }
        "status" {
            Get-Status
        }
        "logs" {
            Get-Logs -Follow $Arg
        }
        "build" {
            Build-Image
        }
        "clean" {
            Clear-Service
        }
        "update" {
            Update-Service
        }
        { $_ -in @("help", "--help", "-h") } {
            Show-Help
        }
        default {
            Write-Error "未知命令: $Command"
            Write-Host ""
            Show-Help
            exit 1
        }
    }
}

# 运行主函数
$command = if ($args.Count -gt 0) { $args[0] } else { "help" }
$arg = if ($args.Count -gt 1) { $args[1] } else { "" }
Main -Command $command -Arg $arg

