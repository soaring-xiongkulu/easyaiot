# ============================================
# EasyAIoT 中间件部署脚本 (Windows)
# ============================================
# 使用方法：
#   .\install_middleware_win.ps1 [命令]
#
# 可用命令：
#   install    - 安装并启动所有中间件（首次运行）
#   start      - 启动所有中间件
#   stop       - 停止所有中间件
#   restart    - 重启所有中间件
#   status     - 查看所有中间件状态
#   logs       - 查看中间件日志
#   build      - 重新构建所有镜像
#   clean      - 清理所有容器和镜像
#   update     - 更新并重启所有中间件
# ============================================

$ErrorActionPreference = "Stop"

# 颜色定义（带日志功能）
function Write-Section {
    param([string]$Section)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  $Section" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
}

# 脚本所在目录
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $SCRIPT_DIR

$COMPOSE_FILE = Join-Path $SCRIPT_DIR "docker-compose.yml"

# 日志文件配置
$LOG_DIR = Join-Path $SCRIPT_DIR "logs"
if (-not (Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null
}
$LOG_FILE = Join-Path $LOG_DIR "install_middleware_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# 初始化日志文件
@"
=========================================
EasyAIoT 中间件部署脚本日志
开始时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
命令: $($args -join ' ')
=========================================

"@ | Out-File -FilePath $LOG_FILE -Encoding utf8

# 中间件服务列表
$script:MIDDLEWARE_SERVICES = @(
    "Nacos",
    "PostgresSQL",
    "TDengine",
    "Redis",
    "Kafka",
    "MinIO",
    "SRS",
    "NodeRED",
    "EMQX"
)

# 中间件端口映射
$script:MIDDLEWARE_PORTS = @{
    "Nacos" = "8848"
    "PostgresSQL" = "5432"
    "TDengine" = "6030"
    "Redis" = "6379"
    "Kafka" = "9092"
    "MinIO" = "9000"
    "SRS" = "1935"
    "NodeRED" = "1880"
    "EMQX" = "1883"
}

# 中间件健康检查端点
$script:MIDDLEWARE_HEALTH_ENDPOINTS = @{
    "Nacos" = "/nacos/actuator/health"
    "PostgresSQL" = ""
    "TDengine" = ""
    "Redis" = ""
    "Kafka" = ""
    "MinIO" = "/minio/health/live"
    "SRS" = "/api/v1/versions"
    "NodeRED" = "/"
    "EMQX" = "/api/v5/status"
}

# 日志输出函数（去掉颜色代码后写入日志文件）
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    # 去掉 ANSI 颜色代码（PowerShell中不需要）
    $cleanMessage = $Message
    $logEntry = "[$timestamp] $cleanMessage"
    Add-Content -Path $LOG_FILE -Value $logEntry -Encoding utf8
}

# 打印带颜色的消息（同时输出到日志文件）
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
    Write-Log "[INFO] $Message"
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
    Write-Log "[SUCCESS] $Message"
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
    Write-Log "[WARNING] $Message"
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
    Write-Log "[ERROR] $Message"
}

# 检查命令是否存在
function Test-Command {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# 检查 Git 是否已安装
function Test-Git {
    if (Test-Command "git") {
        $gitVersion = git --version 2>&1
        Write-Success "Git 已安装: $gitVersion"
        return $true
    }
    return $false
}

# 检查并提示安装 Git
function Test-AndRequireGit {
    if (Test-Git) {
        return $true
    }
    
    Write-Error "未检测到 Git"
    Write-Host ""
    Write-Info "Git 是运行此项目的必需组件"
    Write-Host ""
    Write-Warning "请按照以下步骤安装 Git："
    Write-Host ""
    Write-Info "Windows 系统安装方法："
    Write-Info "  1. 访问 https://git-scm.com/download/win"
    Write-Info "  2. 下载并安装 Git for Windows"
    Write-Info "  3. 安装完成后重新运行此脚本"
    Write-Host ""
    Write-Error "Git 是必需的，安装流程已终止"
    Write-Info "安装 Git 后，请重新运行此脚本"
    exit 1
}

# 检查 Node.js 版本
function Test-NodeJsVersion {
    if (Test-Command "node") {
        $nodeVersion = node -v
        $versionNumber = [int]($nodeVersion -replace 'v(\d+)\..*', '$1')
        if ($versionNumber -ge 20) {
            Write-Success "Node.js 已安装: $nodeVersion"
            return $true
        } else {
            Write-Warning "检测到 Node.js 版本较低: $nodeVersion，需要 20+ 版本"
            return $false
        }
    }
    return $false
}

# 检查并安装 Node.js 20+（Windows上提示手动安装）
function Test-AndInstallNodeJs20 {
    if (Test-NodeJsVersion) {
        return $true
    }
    
    Write-Warning "未检测到 Node.js 20+ 版本"
    Write-Host ""
    Write-Info "Node.js 20+ 是运行某些中间件服务的必需组件"
    Write-Host ""
    Write-Info "Windows 系统安装方法："
    Write-Info "  1. 访问 https://nodejs.org/"
    Write-Info "  2. 下载并安装 Node.js 20+ LTS 版本"
    Write-Info "  3. 安装完成后重新运行此脚本"
    Write-Host ""
    Write-Error "Node.js 20+ 是必需的，安装流程已终止"
    exit 1
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

# 检查端口是否被占用
function Test-Port {
    param([string]$Port)
    
    try {
        $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        if ($connections) {
            return $false
        }
    } catch {
        # 如果Get-NetTCPConnection不可用，使用netstat
        $netstat = netstat -ano | Select-String ":$Port "
        if ($netstat) {
            return $false
        }
    }
    
    return $true
}

# 检查所有中间件端口
function Test-AllPorts {
    Write-Info "检查中间件端口占用情况..."
    $allPortsFree = $true
    
    foreach ($service in $MIDDLEWARE_SERVICES) {
        $port = $MIDDLEWARE_PORTS[$service]
        if (-not (Test-Port -Port $port)) {
            Write-Warning "端口 $port ($service) 已被占用"
            $allPortsFree = $false
        } else {
            Write-Info "端口 $port ($service) 可用"
        }
    }
    
    if (-not $allPortsFree) {
        Write-Warning "部分端口被占用，可能影响服务启动"
        Write-Info "请检查并释放被占用的端口，或修改 docker-compose.yml 中的端口映射"
    }
    
    return $allPortsFree
}

# 安装服务
function Install-Service {
    Write-Section "安装 EasyAIoT 中间件服务"
    
    Test-Docker
    Test-DockerCompose
    Test-Network
    Test-AllPorts | Out-Null
    
    Write-Info "构建 Docker 镜像..."
    $buildOutput = & $COMPOSE_CMD build 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "镜像构建失败"
        exit 1
    }
    
    Write-Info "启动所有中间件服务..."
    & $COMPOSE_CMD up -d --quiet-pull 2>&1 | Where-Object { $_ -notmatch "^(Creating|Starting|Pulling|Waiting|Container)" }
    
    Write-Success "中间件服务安装完成！"
    Write-Info "等待服务启动..."
    Start-Sleep -Seconds 10
    
    # 检查服务状态
    Get-Status
    
    Write-Host ""
    Write-Info "中间件服务访问地址:"
    Write-Host "  - Nacos: http://localhost:8848/nacos (用户名/密码: nacos/nacos)"
    Write-Host "  - MinIO: http://localhost:9000 (用户名/密码: minioadmin/minioadmin)"
    Write-Host "  - NodeRED: http://localhost:1880"
    Write-Host "  - EMQX: http://localhost:18083 (用户名/密码: admin/public)"
    Write-Host ""
    Write-Info "查看日志: .\install_middleware_win.ps1 logs"
}

# 启动服务
function Start-Service {
    Write-Info "启动所有中间件服务..."
    Test-Docker
    Test-DockerCompose
    Test-Network
    
    & $COMPOSE_CMD up -d --quiet-pull 2>&1 | Where-Object { $_ -notmatch "^(Creating|Starting|Pulling|Waiting|Container)" }
    Write-Success "服务已启动"
    Get-Status
}

# 停止服务
function Stop-Service {
    Write-Info "停止所有中间件服务..."
    Test-Docker
    Test-DockerCompose
    
    & $COMPOSE_CMD down
    Write-Success "服务已停止"
}

# 重启服务
function Restart-Service {
    Write-Info "重启所有中间件服务..."
    Test-Docker
    Test-DockerCompose
    
    & $COMPOSE_CMD restart
    Write-Success "服务已重启"
    Get-Status
}

# 查看服务状态
function Get-Status {
    Write-Info "中间件服务状态:"
    Test-Docker
    Test-DockerCompose
    
    & $COMPOSE_CMD ps
    
    Write-Host ""
    Write-Info "容器健康状态:"
    foreach ($service in $MIDDLEWARE_SERVICES) {
        $containers = docker ps --filter "name=$service" --format "{{.Names}}" 2>&1
        if ($containers -contains $service) {
            docker ps --filter "name=$service" --format "table {{.Names}}`t{{.Status}}" 2>&1
        }
    }
}

# 查看日志
function Get-Logs {
    param([string]$Service = "", [string]$Follow = "")
    Test-Docker
    Test-DockerCompose
    
    if ([string]::IsNullOrEmpty($Service)) {
        if ($Follow -eq "-f" -or $Follow -eq "--follow") {
            Write-Info "实时查看所有中间件日志（按 Ctrl+C 退出）..."
            & $COMPOSE_CMD logs -f --tail=50
        } else {
            Write-Info "查看所有中间件最近日志（最近50行）..."
            & $COMPOSE_CMD logs --tail=50
        }
    } else {
        if ($Follow -eq "-f" -or $Follow -eq "--follow") {
            Write-Info "实时查看服务 $Service 的日志（按 Ctrl+C 退出）..."
            & $COMPOSE_CMD logs -f --tail=50 $Service
        } else {
            Write-Info "查看服务 $Service 最近日志（最近50行）..."
            & $COMPOSE_CMD logs --tail=50 $Service
        }
    }
}

# 构建镜像
function Build-Image {
    Write-Info "重新构建所有 Docker 镜像..."
    Test-Docker
    Test-DockerCompose
    
    & $COMPOSE_CMD build --no-cache
    Write-Success "镜像构建完成"
}

# 清理服务
function Clear-Service {
    $response = Read-Host "这将删除所有容器、镜像和数据卷，确定要继续吗？(y/N)"
    
    if ($response -match "^[yY]") {
        Test-Docker
        Test-DockerCompose
        Write-Info "停止并删除容器..."
        & $COMPOSE_CMD down -v --remove-orphans
        
        Write-Success "清理完成"
    } else {
        Write-Info "已取消清理操作"
    }
}

# 更新服务
function Update-Service {
    Write-Info "更新所有中间件服务..."
    Test-Docker
    Test-DockerCompose
    Test-Network
    
    Write-Info "拉取最新代码..."
    $result = git pull 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Git pull 失败，继续使用当前代码"
    }
    
    Write-Info "重新构建镜像..."
    & $COMPOSE_CMD build
    
    Write-Info "重启服务..."
    & $COMPOSE_CMD up -d --quiet-pull 2>&1 | Where-Object { $_ -notmatch "^(Creating|Starting|Pulling|Waiting|Container)" }
    
    Write-Success "服务更新完成"
    Get-Status
}

# 显示帮助信息
function Show-Help {
    Write-Host "EasyAIoT 中间件部署脚本"
    Write-Host ""
    Write-Host "使用方法:"
    Write-Host "  .\install_middleware_win.ps1 [命令] [服务名]"
    Write-Host ""
    Write-Host "可用命令:"
    Write-Host "  install    - 安装并启动所有中间件（首次运行）"
    Write-Host "  start      - 启动所有中间件"
    Write-Host "  stop       - 停止所有中间件"
    Write-Host "  restart    - 重启所有中间件"
    Write-Host "  status     - 查看所有中间件状态"
    Write-Host "  logs       - 查看所有中间件日志（最近50行）"
    Write-Host "  logs -f    - 实时查看所有中间件日志"
    Write-Host "  logs [服务名] - 查看指定服务日志"
    Write-Host "  build      - 重新构建所有镜像"
    Write-Host "  clean      - 清理所有容器和镜像"
    Write-Host "  update     - 更新并重启所有中间件"
    Write-Host "  help       - 显示此帮助信息"
    Write-Host ""
    Write-Host "可用服务:"
    $MIDDLEWARE_SERVICES | ForEach-Object {
        Write-Host "  - $_"
    }
    Write-Host ""
}

# 主函数
function Main {
    param([string]$Command = "help", [string]$Arg = "", [string]$Arg2 = "")
    
    switch ($Command.ToLower()) {
        "install" {
            Test-AndRequireGit
            Test-AndInstallNodeJs20 | Out-Null
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
            Get-Logs -Service $Arg -Follow $Arg2
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
$arg2 = if ($args.Count -gt 2) { $args[2] } else { "" }
Main -Command $command -Arg $arg -Arg2 $arg2

