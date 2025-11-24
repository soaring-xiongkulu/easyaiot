# ============================================
# VIDEO服务 Docker Compose 管理脚本 (Windows)
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

# 检查并创建 Docker 网络（注意：使用host网络模式后，此函数不再需要，但保留以兼容其他服务）
function Test-Network {
    Write-Info "检查 Docker 网络 easyaiot-network..."
    Write-Info "注意：VIDEO服务使用host网络模式，不需要加入easyaiot-network网络"
    Write-Info "但中间件服务仍需要此网络，检查网络是否存在..."
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

# 清理 VIDEO 服务的 compose 容器网络缓存
function Clear-ComposeCache {
    Write-Info "清理 VIDEO 服务的 compose 容器网络缓存..."
    
    # 确保 COMPOSE_CMD 已设置
    if (-not $script:COMPOSE_CMD) {
        if (Test-Command "docker-compose") {
            $script:COMPOSE_CMD = "docker-compose"
        } elseif (docker compose version 2>&1 | Out-Null; $LASTEXITCODE -eq 0) {
            $script:COMPOSE_CMD = "docker compose"
        } else {
            Write-Warning "无法确定 docker-compose 命令，跳过缓存清理"
            return
        }
    }
    
    $composeFile = ""
    if (Test-Path "docker-compose.yml") {
        $composeFile = "docker-compose.yml"
    } elseif (Test-Path "docker-compose.yaml") {
        $composeFile = "docker-compose.yaml"
    } else {
        Write-Info "未找到 docker-compose 文件，跳过缓存清理"
        return
    }
    
    # 1. 停止并清理容器和网络连接
    Write-Info "执行 docker-compose down 清理容器和网络连接..."
    & $COMPOSE_CMD down 2>&1 | Out-Null
    
    Start-Sleep -Seconds 1
    
    # 2. 强制重新读取配置（这会清除 docker-compose 的配置缓存）
    Write-Info "强制重新读取配置以清除缓存..."
    $result = & $COMPOSE_CMD config 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "配置已重新验证"
    } else {
        Write-Warning "配置验证失败，但继续执行"
    }
    
    # 3. 清理可能的网络残留连接
    Write-Info "检查并清理网络残留连接..."
    $networkName = "easyaiot-network"
    $networkInfo = docker network inspect $networkName 2>&1
    if ($LASTEXITCODE -eq 0) {
        $containers = docker network inspect $networkName --format '{{range .Containers}}{{.Name}} {{end}}' 2>&1
        if ($containers -match "video") {
            Write-Info "发现残留的网络连接，正在清理..."
            $containers -split '\s+' | Where-Object { $_ -match "video" -and $_ } | ForEach-Object {
                $container = $_
                $exists = docker ps -a --format '{{.Names}}' 2>&1 | Select-String "^${container}$"
                if ($exists) {
                    Write-Info "断开容器网络连接: $container"
                    docker network disconnect -f $networkName $container 2>&1 | Out-Null
                }
            }
        }
    }
    
    # 4. 清理 docker-compose 的临时文件（如果存在）
    Write-Info "清理 docker-compose 临时文件..."
    Get-ChildItem -Path . -Filter ".docker-compose.*" -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
    @("docker-compose.override.yml", "docker-compose.override.yaml") | ForEach-Object {
        if (Test-Path $_) {
            Remove-Item $_ -Force -ErrorAction SilentlyContinue
        }
    }
    
    Write-Success "VIDEO 服务的 compose 缓存已清理完成"
}

# 创建 .env.docker 文件（用于Docker部署）
function New-EnvFile {
    if (-not (Test-Path ".env.docker")) {
        Write-Info ".env.docker 文件不存在，正在创建..."
        if (Test-Path "env.example") {
            Copy-Item "env.example" ".env.docker"
            Write-Success ".env.docker 文件已从 env.example 创建"
            
            # 自动配置中间件连接信息（使用localhost，因为使用host网络模式）
            Write-Info "自动配置中间件连接信息（使用host网络模式，通过localhost访问中间件）..."
            
            # 更新配置
            $content = Get-Content ".env.docker"
            $content = $content | ForEach-Object {
                if ($_ -match "^DATABASE_URL=") {
                    "DATABASE_URL=postgresql://postgres:iot45722414822@localhost:5432/iot-video20"
                } elseif ($_ -match "^NACOS_SERVER=") {
                    "NACOS_SERVER=localhost:8848"
                } elseif ($_ -match "^MINIO_ENDPOINT=") {
                    "MINIO_ENDPOINT=localhost:9000"
                } elseif ($_ -match "^MINIO_SECRET_KEY=") {
                    "MINIO_SECRET_KEY=basiclab@iot975248395"
                } elseif ($_ -match "^REDIS_HOST=") {
                    "REDIS_HOST=localhost"
                } elseif ($_ -match "^KAFKA_BOOTSTRAP_SERVERS=") {
                    "KAFKA_BOOTSTRAP_SERVERS=localhost:9092"
                } elseif ($_ -match "^TDENGINE_HOST=") {
                    "TDENGINE_HOST=localhost"
                } elseif ($_ -match "^NACOS_PASSWORD=") {
                    "NACOS_PASSWORD=basiclab@iot78475418754"
                } else {
                    $_
                }
            }
            $content | Out-File -FilePath ".env.docker" -Encoding utf8
            Write-Success "中间件连接信息已自动配置（使用host网络模式）"
            Write-Info "注意：使用host网络模式后，容器可以直接访问宿主机局域网，支持ONVIF摄像头发现"
            Write-Info "如需修改其他配置，请编辑 .env.docker 文件"
        } else {
            Write-Error "env.example 文件不存在，无法创建 .env.docker 文件"
            exit 1
        }
    } else {
        Write-Info ".env.docker 文件已存在"
        Write-Info "检查并更新中间件连接信息（使用host网络模式）..."
        
        $content = Get-Content ".env.docker"
        $updated = $false
        $content = $content | ForEach-Object {
            if ($_ -match "^DATABASE_URL=.*(PostgresSQL|postgres-server)") {
                $updated = $true
                "DATABASE_URL=postgresql://postgres:iot45722414822@localhost:5432/iot-video20"
            } elseif ($_ -match "^NACOS_SERVER=.*(14\.18\.122\.2|Nacos|nacos-server)") {
                $updated = $true
                "NACOS_SERVER=localhost:8848"
            } elseif ($_ -match "^MINIO_ENDPOINT=.*(MinIO|minio-server)") {
                $updated = $true
                "MINIO_ENDPOINT=localhost:9000"
            } elseif ($_ -match "^REDIS_HOST=.*(Redis|redis-server)") {
                $updated = $true
                "REDIS_HOST=localhost"
            } elseif ($_ -match "^KAFKA_BOOTSTRAP_SERVERS=.*(Kafka|kafka-server)") {
                $updated = $true
                "KAFKA_BOOTSTRAP_SERVERS=localhost:9092"
            } elseif ($_ -match "^TDENGINE_HOST=.*(TDengine|tdengine-server)") {
                $updated = $true
                "TDENGINE_HOST=localhost"
            } else {
                $_
            }
        }
        if ($updated) {
            $content | Out-File -FilePath ".env.docker" -Encoding utf8
            Write-Info "已更新中间件连接信息（使用host网络模式）"
        }
    }
}

# 安装服务
function Install-Service {
    Write-Info "开始安装 VIDEO 服务..."
    
    Test-Docker
    Test-DockerCompose
    Clear-ComposeCache
    Test-Network
    New-Directories
    New-EnvFile
    
    Write-Info "构建 Docker 镜像（减少输出）..."
    $buildOutput = & $COMPOSE_CMD build --progress=plain 2>&1
    $buildOutput | Select-String -Pattern "(Step|Successfully|ERROR|WARNING|built)" | ForEach-Object { Write-Host $_ }
    
    Write-Info "启动服务..."
    & $COMPOSE_CMD up -d --quiet-pull 2>&1 | Where-Object { $_ -ne "" }
    
    Write-Success "服务安装完成！"
    Write-Info "等待服务启动..."
    Start-Sleep -Seconds 5
    
    # 检查服务状态
    Get-Status
    
    Write-Info "服务访问地址: http://localhost:6000"
    Write-Info "健康检查地址: http://localhost:6000/actuator/health"
    Write-Info "查看日志: .\install_win.ps1 logs"
}

# 启动服务
function Start-Service {
    Write-Info "启动服务..."
    Test-Docker
    Test-DockerCompose
    Clear-ComposeCache
    Test-Network
    
    if (-not (Test-Path ".env.docker")) {
        Write-Warning ".env.docker 文件不存在，正在创建..."
        New-EnvFile
    }
    
    & $COMPOSE_CMD up -d --quiet-pull 2>&1 | Where-Object { $_ -ne "" }
    Write-Success "服务已启动"
    Get-Status
}

# 停止服务
function Stop-Service {
    Write-Info "停止服务..."
    Test-Docker
    Test-DockerCompose
    
    & $COMPOSE_CMD down
    Write-Success "服务已停止"
}

# 重启服务
function Restart-Service {
    Write-Info "重启服务..."
    Test-Docker
    Test-DockerCompose
    Clear-ComposeCache
    
    & $COMPOSE_CMD restart
    Write-Success "服务已重启"
    Get-Status
}

# 查看服务状态
function Get-Status {
    Write-Info "服务状态:"
    Test-Docker
    Test-DockerCompose
    
    & $COMPOSE_CMD ps
    
    Write-Host ""
    Write-Info "容器健康状态:"
    $containers = docker ps --filter "name=video-service" --format "{{.Names}}" 2>&1
    if ($containers -contains "video-service") {
        docker ps --filter "name=video-service" --format "table {{.Names}}`t{{.Status}}" 2>&1
        
        $health = docker inspect --format='{{.State.Health.Status}}' video-service 2>&1
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
        & $COMPOSE_CMD logs -f --tail=50
    } else {
        Write-Info "查看最近日志（最近50行）..."
        & $COMPOSE_CMD logs --tail=50
    }
}

# 构建镜像
function Build-Image {
    Write-Info "重新构建 Docker 镜像（减少输出）..."
    Test-Docker
    Test-DockerCompose
    
    $buildOutput = & $COMPOSE_CMD build --no-cache --progress=plain 2>&1
    $buildOutput | Select-String -Pattern "(Step|Successfully|ERROR|WARNING|built)" | ForEach-Object { Write-Host $_ }
    Write-Success "镜像构建完成"
}

# 清理服务
function Clear-Service {
    $response = Read-Host "这将删除容器、镜像和数据卷，确定要继续吗？(y/N)"
    
    if ($response -match "^[yY]") {
        Test-Docker
        Test-DockerCompose
        Write-Info "停止并删除容器..."
        & $COMPOSE_CMD down -v
        
        Write-Info "删除镜像..."
        docker rmi video-service:latest 2>&1 | Out-Null
        
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
    Clear-ComposeCache
    Test-Network
    
    Write-Info "拉取最新代码..."
    $result = git pull 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Git pull 失败，继续使用当前代码"
    }
    
    Write-Info "重新构建镜像（减少输出）..."
    $buildOutput = & $COMPOSE_CMD build --progress=plain 2>&1
    $buildOutput | Select-String -Pattern "(Step|Successfully|ERROR|WARNING|built)" | ForEach-Object { Write-Host $_ }
    
    Write-Info "重启服务..."
    & $COMPOSE_CMD up -d --quiet-pull 2>&1 | Where-Object { $_ -ne "" }
    
    Write-Success "服务更新完成"
    Get-Status
}

# 显示帮助信息
function Show-Help {
    Write-Host "VIDEO服务 Docker Compose 管理脚本"
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
    Write-Host "  logs       - 查看服务日志（最近50行）"
    Write-Host "  logs -f    - 实时查看服务日志（最近50行）"
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

