# ============================================
# DEVICE模块 Docker Compose 管理脚本 (Windows)
# ============================================
# 用于管理DEVICE目录下的所有Docker服务
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

# 脚本所在目录
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$COMPOSE_FILE = Join-Path $SCRIPT_DIR "docker-compose.yml"

# 检查docker-compose是否存在
if (-not (Get-Command docker -ErrorAction SilentlyContinue) -and -not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Error "错误: 未找到docker或docker-compose命令"
    exit 1
}

# 使用docker compose（新版本）或docker-compose（旧版本）
if (docker compose version 2>&1 | Out-Null; $LASTEXITCODE -eq 0) {
    $script:DOCKER_COMPOSE = "docker compose"
} elseif (docker-compose version 2>&1 | Out-Null; $LASTEXITCODE -eq 0) {
    $script:DOCKER_COMPOSE = "docker-compose"
} else {
    Write-Error "错误: 未找到docker compose或docker-compose命令"
    exit 1
}

# 检查docker-compose.yml是否存在
function Test-ComposeFile {
    if (-not (Test-Path $COMPOSE_FILE)) {
        Write-Error "docker-compose.yml文件不存在: $COMPOSE_FILE"
        exit 1
    }
}

# 检查命令是否存在
function Test-Command {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# WEB目录路径
$WEB_DIR = Join-Path $SCRIPT_DIR "..\WEB"

# 创建WEB必要的目录
function New-WebDirectories {
    Write-Info "创建WEB必要的目录..."
    @("conf", "logs", "conf/ssl", "dist") | ForEach-Object {
        $path = Join-Path $WEB_DIR $_
        if (-not (Test-Path $path)) {
            New-Item -ItemType Directory -Path $path -Force | Out-Null
        }
    }
    Write-Success "WEB目录创建完成"
}

# 检查前端构建产物
function Test-WebDist {
    $distPath = Join-Path $WEB_DIR "dist"
    if (-not (Test-Path $distPath) -or (Get-ChildItem $distPath -ErrorAction SilentlyContinue | Measure-Object).Count -eq 0) {
        Write-Warning "WEB/dist 目录不存在或为空，需要先构建前端项目"
        Write-Info "运行: $($MyInvocation.MyCommand.Name) build-frontend"
        return $false
    }
    return $true
}

# 构建前端项目
function Build-Frontend {
    Write-Info "开始构建前端项目..."
    
    if (-not (Test-Path $WEB_DIR)) {
        Write-Error "WEB目录不存在: $WEB_DIR"
        exit 1
    }
    
    Push-Location $WEB_DIR
    
    # 检查 Node.js 和 pnpm
    if (-not (Test-Command "node")) {
        Write-Error "Node.js 未安装，请先安装 Node.js"
        Write-Host "安装指南: https://nodejs.org/"
        Pop-Location
        exit 1
    }
    
    $packageManager = ""
    if (-not (Test-Command "pnpm")) {
        Write-Warning "pnpm 未安装，尝试使用 npm..."
        if (-not (Test-Command "npm")) {
            Write-Error "npm 未安装，请先安装 Node.js"
            Pop-Location
            exit 1
        }
        $packageManager = "npm"
    } else {
        $packageManager = "pnpm"
    }
    
    Write-Info "使用包管理器: $packageManager"
    
    # 安装依赖
    if (-not (Test-Path "node_modules")) {
        Write-Info "安装依赖..."
        if ($packageManager -eq "pnpm") {
            pnpm install
        } else {
            npm install
        }
    }
    
    # 构建项目
    Write-Info "构建前端项目..."
    if ($packageManager -eq "pnpm") {
        pnpm build
    } else {
        npm run build
    }
    
    Write-Success "前端项目构建完成"
    Pop-Location
}

# 检查并构建Jar包（已废弃，现在在Docker容器中编译）
function Test-AndBuildJars {
    Write-Info "跳过宿主机Jar包检查（编译将在Docker容器中完成）..."
    # 不再需要在宿主机上编译，所有编译都在Docker容器中完成
}

# 构建所有镜像
function Build-Images {
    Write-Info "开始构建所有Docker镜像（在容器中编译，显示完整日志）..."
    Set-Location $SCRIPT_DIR
    # 注意：编译将在Docker容器中完成，不需要宿主机Maven环境
    
    $exitCode = 0
    & $DOCKER_COMPOSE build
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -ne 0) {
        Write-Error "镜像构建失败（退出码: $exitCode）"
        exit 1
    }
    
    Write-Success "镜像构建完成（所有编译在容器中完成）"
}

# 构建并启动所有服务
function Build-AndStart {
    Write-Info "开始构建并启动所有服务（在容器中编译，显示完整日志）..."
    Set-Location $SCRIPT_DIR
    # 注意：编译将在Docker容器中完成，不需要宿主机Maven环境
    
    $exitCode = 0
    & $DOCKER_COMPOSE up -d --build
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -ne 0) {
        Write-Error "服务构建或启动失败（退出码: $exitCode）"
        exit 1
    }
    
    # 验证容器是否真的创建了
    $containerCount = (& $DOCKER_COMPOSE ps -q 2>&1 | Measure-Object -Line).Lines
    if ($containerCount -eq 0) {
        Write-Error "警告：没有检测到运行的容器"
        Write-Info "请检查 docker-compose.yml 配置和依赖服务（如 Nacos、PostgreSQL、Redis 等）"
        Write-Info "尝试查看服务状态："
        & $DOCKER_COMPOSE ps
        exit 1
    }
    
    Write-Success "服务构建并启动完成（所有编译在容器中完成，共 $containerCount 个容器）"
}

# 启动所有服务
function Start-Services {
    Write-Info "启动所有服务..."
    Set-Location $SCRIPT_DIR
    # 使用 --quiet-pull 减少拉取镜像时的输出
    if ($DOCKER_COMPOSE -eq "docker compose") {
        & $DOCKER_COMPOSE up -d --quiet-pull 2>&1 | Select-String -Pattern "(Creating|Starting|Started|ERROR|WARNING)"
    } else {
        & $DOCKER_COMPOSE up -d 2>&1 | Select-String -Pattern "(Creating|Starting|Started|ERROR|WARNING)"
    }
    Write-Success "服务启动完成"
}

# 停止所有服务
function Stop-Services {
    Write-Info "停止所有服务..."
    Set-Location $SCRIPT_DIR
    & $DOCKER_COMPOSE down
    Write-Success "服务已停止"
}

# 重启所有服务
function Restart-Services {
    Write-Info "重启所有服务..."
    Set-Location $SCRIPT_DIR
    & $DOCKER_COMPOSE restart
    Write-Success "服务重启完成"
}

# 查看服务状态
function Show-Status {
    Write-Info "服务状态:"
    Set-Location $SCRIPT_DIR
    & $DOCKER_COMPOSE ps
}

# 查看日志
function Show-Logs {
    param([string]$Service = "")
    if ([string]::IsNullOrEmpty($Service)) {
        Write-Info "查看所有服务日志（最近50行，按Ctrl+C退出）..."
        Set-Location $SCRIPT_DIR
        & $DOCKER_COMPOSE logs -f --tail=50
    } else {
        Write-Info "查看服务 $Service 的日志（最近50行，按Ctrl+C退出）..."
        Set-Location $SCRIPT_DIR
        & $DOCKER_COMPOSE logs -f --tail=50 $Service
    }
}

# 查看特定服务的日志（最近50行）
function Show-LogsTail {
    param([string]$Service = "")
    if ([string]::IsNullOrEmpty($Service)) {
        Write-Info "查看所有服务最近50行日志..."
        Set-Location $SCRIPT_DIR
        & $DOCKER_COMPOSE logs --tail=50
    } else {
        Write-Info "查看服务 $Service 最近50行日志..."
        Set-Location $SCRIPT_DIR
        & $DOCKER_COMPOSE logs --tail=50 $Service
    }
}

# 重启特定服务
function Restart-Service {
    param([string]$Service)
    if ([string]::IsNullOrEmpty($Service)) {
        Write-Error "请指定要重启的服务名称"
        Write-Host "可用服务:"
        Set-Location $SCRIPT_DIR
        & $DOCKER_COMPOSE config --services
        exit 1
    }
    Write-Info "重启服务: $Service"
    Set-Location $SCRIPT_DIR
    & $DOCKER_COMPOSE restart $Service
    Write-Success "服务 $Service 重启完成"
}

# 停止特定服务
function Stop-Service {
    param([string]$Service)
    if ([string]::IsNullOrEmpty($Service)) {
        Write-Error "请指定要停止的服务名称"
        Write-Host "可用服务:"
        Set-Location $SCRIPT_DIR
        & $DOCKER_COMPOSE config --services
        exit 1
    }
    Write-Info "停止服务: $Service"
    Set-Location $SCRIPT_DIR
    & $DOCKER_COMPOSE stop $Service
    Write-Success "服务 $Service 已停止"
}

# 启动特定服务
function Start-Service {
    param([string]$Service)
    if ([string]::IsNullOrEmpty($Service)) {
        Write-Error "请指定要启动的服务名称"
        Write-Host "可用服务:"
        Set-Location $SCRIPT_DIR
        & $DOCKER_COMPOSE config --services
        exit 1
    }
    Write-Info "启动服务: $Service"
    Set-Location $SCRIPT_DIR
    & $DOCKER_COMPOSE up -d $Service
    Write-Success "服务 $Service 启动完成"
}

# 清理（停止并删除容器）
function Clear-Service {
    Write-Warning "这将停止并删除所有容器，但保留镜像"
    $response = Read-Host "确认继续? (y/N)"
    if ($response -match "^[yY]") {
        Set-Location $SCRIPT_DIR
        & $DOCKER_COMPOSE down
        Write-Success "清理完成"
    } else {
        Write-Info "操作已取消"
    }
}

# 完全清理（包括镜像）
function Clear-All {
    Write-Warning "这将停止并删除所有容器和镜像"
    $response = Read-Host "确认继续? (y/N)"
    if ($response -match "^[yY]") {
        Set-Location $SCRIPT_DIR
        & $DOCKER_COMPOSE down --rmi all
        Write-Success "完全清理完成"
    } else {
        Write-Info "操作已取消"
    }
}

# 更新服务（重新构建并重启）
function Update-Services {
    Write-Info "更新所有服务（在容器中重新构建并重启，显示完整日志）..."
    Set-Location $SCRIPT_DIR
    # 注意：编译将在Docker容器中完成，不需要宿主机Maven环境
    
    $exitCode = 0
    & $DOCKER_COMPOSE up -d --build --force-recreate
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -ne 0) {
        Write-Error "服务更新失败（退出码: $exitCode）"
        exit 1
    }
    
    # 验证容器是否真的创建了
    $containerCount = (& $DOCKER_COMPOSE ps -q 2>&1 | Measure-Object -Line).Lines
    if ($containerCount -eq 0) {
        Write-Error "警告：没有检测到运行的容器"
        Write-Info "请检查 docker-compose.yml 配置和依赖服务（如 Nacos、PostgreSQL、Redis 等）"
        Write-Info "尝试查看服务状态："
        & $DOCKER_COMPOSE ps
        exit 1
    }
    
    Write-Success "服务更新完成（所有编译在容器中完成，共 $containerCount 个容器）"
}

# 显示帮助信息
function Show-Help {
    Write-Host "DEVICE模块 Docker Compose 管理脚本"
    Write-Host ""
    Write-Host "用法: $($MyInvocation.MyCommand.Name) [命令] [选项]"
    Write-Host ""
    Write-Host "命令:"
    Write-Host "    build               构建所有Docker镜像（在容器中编译，无需宿主机Maven）"
    Write-Host "    start               启动所有服务"
    Write-Host "    stop                停止所有服务"
    Write-Host "    restart             重启所有服务"
    Write-Host "    status              查看服务状态"
    Write-Host "    logs [服务名]       查看日志（所有服务或指定服务，最近50行）"
    Write-Host "    logs-tail [服务名]  查看最近50行日志"
    Write-Host "    restart-service     重启指定服务"
    Write-Host "    stop-service        停止指定服务"
    Write-Host "    start-service       启动指定服务"
    Write-Host "    clean               清理（停止并删除容器，保留镜像）"
    Write-Host "    clean-all           完全清理（停止并删除容器和镜像）"
    Write-Host "    update              更新服务（在容器中重新构建并重启）"
    Write-Host "    install             安装（构建并启动所有服务，在容器中编译）"
    Write-Host "    help                显示此帮助信息"
    Write-Host ""
    Write-Host "示例:"
    Write-Host "    $($MyInvocation.MyCommand.Name) install                    # 构建并启动所有服务"
    Write-Host "    $($MyInvocation.MyCommand.Name) start                      # 启动所有服务"
    Write-Host "    $($MyInvocation.MyCommand.Name) logs iot-gateway           # 查看iot-gateway的日志"
    Write-Host "    $($MyInvocation.MyCommand.Name) restart-service iot-system # 重启iot-system服务"
    Write-Host "    $($MyInvocation.MyCommand.Name) status                     # 查看所有服务状态"
    Write-Host ""
    Write-Host "可用服务:"
    Write-Host "    - iot-gateway"
    Write-Host "    - iot-system"
    Write-Host "    - iot-infra"
    Write-Host "    - iot-device"
    Write-Host "    - iot-dataset"
    Write-Host "    - iot-tdengine"
    Write-Host "    - iot-file"
    Write-Host ""
}

# 主函数
function Main {
    param([string]$Command = "", [string]$Arg = "")
    
    Test-ComposeFile
    
    if ([string]::IsNullOrEmpty($Command)) {
        # 如果没有参数，显示交互式菜单
        Show-InteractiveMenu
        return
    }
    
    switch ($Command.ToLower()) {
        "build" {
            Build-Images
        }
        "start" {
            Start-Services
        }
        "stop" {
            Stop-Services
        }
        "restart" {
            Restart-Services
        }
        "status" {
            Show-Status
        }
        "logs" {
            Show-Logs -Service $Arg
        }
        "logs-tail" {
            Show-LogsTail -Service $Arg
        }
        "restart-service" {
            Restart-Service -Service $Arg
        }
        "stop-service" {
            Stop-Service -Service $Arg
        }
        "start-service" {
            Start-Service -Service $Arg
        }
        "clean" {
            Clear-Service
        }
        "clean-all" {
            Clear-All
        }
        "update" {
            Update-Services
        }
        { $_ -in @("install", "build-and-start") } {
            Build-AndStart
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

# 交互式菜单
function Show-InteractiveMenu {
    while ($true) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Blue
        Write-Host "  DEVICE模块 Docker Compose 管理" -ForegroundColor Blue
        Write-Host "========================================" -ForegroundColor Blue
        Write-Host "1) 安装/构建并启动所有服务"
        Write-Host "2) 启动所有服务"
        Write-Host "3) 停止所有服务"
        Write-Host "4) 重启所有服务"
        Write-Host "5) 查看服务状态"
        Write-Host "6) 查看日志（所有服务）"
        Write-Host "7) 查看日志（指定服务）"
        Write-Host "8) 重启指定服务"
        Write-Host "9) 停止指定服务"
        Write-Host "10) 启动指定服务"
        Write-Host "11) 更新服务（重新构建并重启）"
        Write-Host "12) 清理（删除容器，保留镜像）"
        Write-Host "13) 完全清理（删除容器和镜像）"
        Write-Host "0) 退出"
        Write-Host ""
        $choice = Read-Host "请选择操作 [0-13]"
        
        switch ($choice) {
            "1" {
                Build-AndStart
            }
            "2" {
                Start-Services
            }
            "3" {
                Stop-Services
            }
            "4" {
                Restart-Services
            }
            "5" {
                Show-Status
            }
            "6" {
                Show-Logs
            }
            "7" {
                Write-Host "可用服务:"
                Set-Location $SCRIPT_DIR
                & $DOCKER_COMPOSE config --services
                $serviceName = Read-Host "请输入服务名称"
                Show-Logs -Service $serviceName
            }
            "8" {
                Write-Host "可用服务:"
                Set-Location $SCRIPT_DIR
                & $DOCKER_COMPOSE config --services
                $serviceName = Read-Host "请输入服务名称"
                Restart-Service -Service $serviceName
            }
            "9" {
                Write-Host "可用服务:"
                Set-Location $SCRIPT_DIR
                & $DOCKER_COMPOSE config --services
                $serviceName = Read-Host "请输入服务名称"
                Stop-Service -Service $serviceName
            }
            "10" {
                Write-Host "可用服务:"
                Set-Location $SCRIPT_DIR
                & $DOCKER_COMPOSE config --services
                $serviceName = Read-Host "请输入服务名称"
                Start-Service -Service $serviceName
            }
            "11" {
                Update-Services
            }
            "12" {
                Clear-Service
            }
            "13" {
                Clear-All
            }
            "0" {
                Write-Info "退出"
                exit 0
            }
            default {
                Write-Error "无效选择，请重新输入"
            }
        }
    }
}

# 执行主函数
$command = if ($args.Count -gt 0) { $args[0] } else { "" }
$arg = if ($args.Count -gt 1) { $args[1] } else { "" }
Main -Command $command -Arg $arg

