# ============================================
# PostgreSQL 连接测试脚本（Windows PowerShell）
# ============================================
# 用于测试从宿主机连接 PostgreSQL 数据库
# 使用方法：
#   .\test_postgresql_connection.ps1
# ============================================

$ErrorActionPreference = "Stop"

# PostgreSQL 连接配置
$DB_HOST = "127.0.0.1"
$DB_PORT = 5432
$DB_USER = "postgres"
$DB_PASSWORD = "iot45722414822"
$DB_NAME = "postgres"

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

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  $Title" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
}

Write-Section "PostgreSQL 连接测试工具"

# 检查 Docker 是否运行
Write-Info "检查 Docker 服务状态..."
try {
    docker ps | Out-Null
    Write-Success "Docker 服务正在运行"
} catch {
    Write-Error "无法访问 Docker，请确保 Docker 服务正在运行"
    exit 1
}

# 检查 PostgreSQL 容器是否存在
Write-Info "检查 PostgreSQL 容器状态..."
$containerExists = docker ps -a --filter "name=postgres-server" --format "{{.Names}}" 2>$null
if (-not $containerExists -or $containerExists -notmatch "postgres-server") {
    Write-Error "PostgreSQL 容器不存在"
    Write-Info "请先启动 PostgreSQL 容器："
    Write-Info "  cd .scripts\docker"
    Write-Info "  docker-compose up -d PostgresSQL"
    exit 1
}

# 检查容器是否在运行
$containerStatus = docker ps --filter "name=postgres-server" --format "{{.Status}}" 2>$null
if (-not $containerStatus) {
    Write-Warning "PostgreSQL 容器存在但未运行"
    Write-Info "正在启动容器..."
    docker start postgres-server 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "无法启动容器"
        exit 1
    }
    Write-Info "等待容器启动..."
    Start-Sleep -Seconds 5
    $containerStatus = docker ps --filter "name=postgres-server" --format "{{.Status}}" 2>$null
}

if ($containerStatus) {
    Write-Success "PostgreSQL 容器正在运行"
    Write-Info "容器状态: $containerStatus"
} else {
    Write-Error "PostgreSQL 容器无法启动"
    exit 1
}

# 等待 PostgreSQL 服务就绪（容器内）
Write-Info "等待 PostgreSQL 服务就绪（容器内）..."
$maxAttempts = 30
$attempt = 0
$isReady = $false

while ($attempt -lt $maxAttempts) {
    $result = docker exec postgres-server pg_isready -U postgres 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "PostgreSQL 服务已就绪（容器内）"
        $isReady = $true
        break
    }
    $attempt++
    if ($attempt % 5 -eq 0) {
        Write-Info "等待中... ($attempt/$maxAttempts)"
    }
    Start-Sleep -Seconds 2
}

if (-not $isReady) {
    Write-Error "PostgreSQL 服务未就绪（容器内）"
    Write-Info "查看容器日志: docker logs postgres-server"
    exit 1
}

# 检查端口是否监听
Write-Info "检查端口 $DB_PORT 是否监听..."
try {
    $portInfo = Get-NetTCPConnection -LocalPort $DB_PORT -ErrorAction SilentlyContinue
    if ($portInfo) {
        Write-Success "端口 $DB_PORT 正在监听"
        Write-Info "端口信息: $($portInfo | Select-Object -First 1 | Format-List | Out-String)"
    } else {
        Write-Warning "端口 $DB_PORT 未监听（可能无法从宿主机连接）"
    }
} catch {
    Write-Warning "无法检查端口状态"
}

# 测试连接（方法1: 使用 psql 客户端）
Write-Section "测试数据库连接"

$psqlPath = Get-Command psql -ErrorAction SilentlyContinue
if ($psqlPath) {
    Write-Info "使用 psql 客户端测试连接..."
    $env:PGPASSWORD = $DB_PASSWORD
    
    try {
        $versionQuery = "SELECT version();"
        $versionResult = psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c $versionQuery 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "psql 连接测试成功"
            Write-Info "PostgreSQL 版本信息:"
            $versionResult | ForEach-Object { Write-Host "  $_" }
            
            # 测试查询
            Write-Info "执行测试查询..."
            $testQuery = "SELECT 1 as test_value, current_database() as database, current_user as user;"
            $testResult = psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c $testQuery 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Success "查询测试成功"
                Write-Info "查询结果:"
                $testResult | ForEach-Object { Write-Host "  $_" }
            }
            
            # 列出所有数据库
            Write-Info "列出所有数据库..."
            $dbQuery = "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname;"
            $dbResult = psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c $dbQuery 2>&1
            if ($LASTEXITCODE -eq 0 -and $dbResult) {
                Write-Success "数据库列表:"
                $dbResult | Where-Object { $_.Trim() -ne "" } | ForEach-Object {
                    Write-Host "  - $($_.Trim())"
                }
            }
        } else {
            Write-Error "psql 连接测试失败"
            Write-Info "错误信息: $versionResult"
            
            # 尝试诊断问题
            Write-Info "诊断连接问题..."
            Write-Info "测试密码是否正确（通过容器内连接）..."
            $containerTest = docker exec postgres-server psql -U postgres -d postgres -c "SELECT 1;" 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Success "容器内连接正常"
                Write-Warning "可能的问题："
                Write-Info "  1. 密码不正确（宿主机连接需要密码认证）"
                Write-Info "  2. pg_hba.conf 配置不允许从宿主机连接"
                Write-Info "  3. 防火墙或网络配置问题"
                Write-Info ""
                Write-Info "建议运行修复脚本："
                Write-Info "  .\fix_postgresql_password.sh"
            } else {
                Write-Error "容器内连接也失败，请检查容器状态"
            }
            Remove-Item Env:\PGPASSWORD
            exit 1
        }
    } catch {
        Write-Error "psql 连接测试失败: $_"
        Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
        exit 1
    }
    
    Remove-Item Env:\PGPASSWORD
} else {
    Write-Warning "未安装 psql 客户端，跳过 psql 测试"
    Write-Info "安装 psql 客户端："
    Write-Info "  下载 PostgreSQL for Windows: https://www.postgresql.org/download/windows/"
    Write-Info "  或使用 Chocolatey: choco install postgresql"
}

# 测试连接（方法2: 使用 Test-NetConnection）
Write-Info "测试端口连通性..."
try {
    $connection = Test-NetConnection -ComputerName $DB_HOST -Port $DB_PORT -WarningAction SilentlyContinue
    if ($connection.TcpTestSucceeded) {
        Write-Success "端口 $DB_PORT 可达（使用 Test-NetConnection）"
    } else {
        Write-Warning "端口 $DB_PORT 不可达（使用 Test-NetConnection）"
    }
} catch {
    Write-Warning "无法测试端口连通性: $_"
}

# 测试连接（方法3: 使用 .NET）
Write-Info "使用 .NET 测试连接..."
try {
    Add-Type -AssemblyName System.Data
    
    $connectionString = "Host=$DB_HOST;Port=$DB_PORT;Username=$DB_USER;Password=$DB_PASSWORD;Database=$DB_NAME;Timeout=5;"
    
    # 尝试使用 Npgsql（如果已安装）
    $npgsqlLoaded = $false
    try {
        Add-Type -Path "Npgsql.dll" -ErrorAction Stop
        $npgsqlLoaded = $true
    } catch {
        # Npgsql 未安装，跳过
    }
    
    if (-not $npgsqlLoaded) {
        Write-Warning "Npgsql 未安装，跳过 .NET 测试"
        Write-Info "安装 Npgsql: Install-Package Npgsql"
    }
} catch {
    Write-Warning "无法进行 .NET 测试: $_"
}

# 总结
Write-Section "测试总结"
Write-Success "PostgreSQL 连接测试完成！"
Write-Info "连接信息："
Write-Info "  主机: $DB_HOST"
Write-Info "  端口: $DB_PORT"
Write-Info "  用户: $DB_USER"
Write-Info "  数据库: $DB_NAME"
Write-Host ""
Write-Info "如果连接失败，请检查："
Write-Info "  1. 容器是否正常运行: docker ps | Select-String postgres"
Write-Info "  2. 端口是否正确映射: docker port postgres-server"
Write-Info "  3. 密码是否正确: 运行 .\fix_postgresql_password.sh"
Write-Info "  4. pg_hba.conf 配置: docker exec postgres-server cat /var/lib/postgresql/data/pg_hba.conf"

