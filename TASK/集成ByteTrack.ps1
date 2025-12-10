# ByteTrack集成脚本
# 将deploy/ncnn/cpp中的文件复制到src/bytetrack目录

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ByteTrack C++ 文件集成脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 创建目标目录
Write-Host "[1/3] 创建目录 src/bytetrack..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "src/bytetrack" | Out-Null

# 2. 复制头文件
Write-Host "[2/3] 复制头文件..." -ForegroundColor Yellow
$headerFiles = @(
    "BYTETracker.h",
    "STrack.h",
    "kalmanFilter.h",
    "lapjv.h",
    "dataType.h"
)

foreach ($file in $headerFiles) {
    $source = "deploy/ncnn/cpp/include/$file"
    $dest = "src/bytetrack/$file"
    if (Test-Path $source) {
        Copy-Item $source -Destination $dest -Force
        Write-Host "  ✅ 已复制: $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 未找到: $file" -ForegroundColor Red
    }
}

# 3. 复制源文件
Write-Host "[3/3] 复制源文件..." -ForegroundColor Yellow
$sourceFiles = @(
    "BYTETracker.cpp",
    "STrack.cpp",
    "kalmanFilter.cpp",
    "lapjv.cpp",
    "utils.cpp"
)

foreach ($file in $sourceFiles) {
    $source = "deploy/ncnn/cpp/src/$file"
    $dest = "src/bytetrack/$file"
    if (Test-Path $source) {
        Copy-Item $source -Destination $dest -Force
        Write-Host "  ✅ 已复制: $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 未找到: $file" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ✅ ByteTrack文件集成完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "已复制文件到: src/bytetrack/" -ForegroundColor White
Write-Host ""
Write-Host "下一步操作：" -ForegroundColor Yellow
Write-Host "1. 查看 src/bytetrack/ 目录确认文件" -ForegroundColor White
Write-Host "2. 修改 CMakeLists.txt 添加这些文件" -ForegroundColor White
Write-Host "3. 重新编译项目" -ForegroundColor White
Write-Host ""

# 列出复制的文件
Write-Host "复制的文件列表：" -ForegroundColor Cyan
Get-ChildItem "src/bytetrack/" | Format-Table Name, Length -AutoSize

# 将deploy/ncnn/cpp中的文件复制到src/bytetrack目录

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ByteTrack C++ 文件集成脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 创建目标目录
Write-Host "[1/3] 创建目录 src/bytetrack..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "src/bytetrack" | Out-Null

# 2. 复制头文件
Write-Host "[2/3] 复制头文件..." -ForegroundColor Yellow
$headerFiles = @(
    "BYTETracker.h",
    "STrack.h",
    "kalmanFilter.h",
    "lapjv.h",
    "dataType.h"
)

foreach ($file in $headerFiles) {
    $source = "deploy/ncnn/cpp/include/$file"
    $dest = "src/bytetrack/$file"
    if (Test-Path $source) {
        Copy-Item $source -Destination $dest -Force
        Write-Host "  ✅ 已复制: $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 未找到: $file" -ForegroundColor Red
    }
}

# 3. 复制源文件
Write-Host "[3/3] 复制源文件..." -ForegroundColor Yellow
$sourceFiles = @(
    "BYTETracker.cpp",
    "STrack.cpp",
    "kalmanFilter.cpp",
    "lapjv.cpp",
    "utils.cpp"
)

foreach ($file in $sourceFiles) {
    $source = "deploy/ncnn/cpp/src/$file"
    $dest = "src/bytetrack/$file"
    if (Test-Path $source) {
        Copy-Item $source -Destination $dest -Force
        Write-Host "  ✅ 已复制: $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 未找到: $file" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ✅ ByteTrack文件集成完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "已复制文件到: src/bytetrack/" -ForegroundColor White
Write-Host ""
Write-Host "下一步操作：" -ForegroundColor Yellow
Write-Host "1. 查看 src/bytetrack/ 目录确认文件" -ForegroundColor White
Write-Host "2. 修改 CMakeLists.txt 添加这些文件" -ForegroundColor White
Write-Host "3. 重新编译项目" -ForegroundColor White
Write-Host ""

# 列出复制的文件
Write-Host "复制的文件列表：" -ForegroundColor Cyan
Get-ChildItem "src/bytetrack/" | Format-Table Name, Length -AutoSize

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 