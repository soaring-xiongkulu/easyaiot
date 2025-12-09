# 修复PowerShell脚本文件编码问题
# 使用方法: .\fix_encoding.ps1 -FilePath "C:\Users\admin\Desktop\fsdownload\push_video_to_srs.ps1"

param(
    [Parameter(Mandatory=$true)]
    [string]$FilePath
)

# 检查文件是否存在
if (-not (Test-Path $FilePath -PathType Leaf)) {
    Write-Host "错误: 文件不存在: $FilePath" -ForegroundColor Red
    exit 1
}

Write-Host "正在修复文件编码: $FilePath" -ForegroundColor Yellow

try {
    # 读取文件内容（尝试多种编码）
    $content = $null
    $encodings = @(
        [System.Text.Encoding]::UTF8,
        [System.Text.Encoding]::Default,
        [System.Text.Encoding]::ASCII
    )
    
    foreach ($encoding in $encodings) {
        try {
            $content = [System.IO.File]::ReadAllText($FilePath, $encoding)
            Write-Host "成功使用编码读取文件: $($encoding.EncodingName)" -ForegroundColor Green
            break
        } catch {
            continue
        }
    }
    
    if ($null -eq $content) {
        throw "无法读取文件内容"
    }
    
    # 保存为UTF-8 with BOM格式（PowerShell推荐格式）
    $utf8WithBom = New-Object System.Text.UTF8Encoding $true
    [System.IO.File]::WriteAllText($FilePath, $content, $utf8WithBom)
    
    Write-Host "文件编码已修复为 UTF-8 with BOM" -ForegroundColor Green
    Write-Host "现在可以重新运行脚本了" -ForegroundColor Cyan
    
} catch {
    Write-Host "错误: 修复文件编码失败: $_" -ForegroundColor Red
    exit 1
}
