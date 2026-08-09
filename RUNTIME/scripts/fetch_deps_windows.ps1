#Requires -Version 5.1
<#
.SYNOPSIS
  Fetch Windows x64 vendor deps for RUNTIME (Phase 1).

.DESCRIPTION
  Default is dry-run: prints URLs and target paths only.
  Use -Execute to download and extract ONNX Runtime CPU zip into vendor/win-x64/.

.EXAMPLE
  .\fetch_deps_windows.ps1
  .\fetch_deps_windows.ps1 -Execute
#>
[CmdletBinding()]
param(
    [switch]$Execute
)

$ErrorActionPreference = "Stop"

$OrtVersion = if ($env:ORT_VERSION) { $env:ORT_VERSION } else { "1.23.2" }
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RuntimeRoot = Resolve-Path (Join-Path $ScriptDir "..")
$VendorRoot = Join-Path $RuntimeRoot "vendor\win-x64"
$OrtZipName = "onnxruntime-win-x64-$OrtVersion.zip"
$OrtUrl = "https://github.com/microsoft/onnxruntime/releases/download/v$OrtVersion/$OrtZipName"
$OrtDestZip = Join-Path $VendorRoot $OrtZipName
$OrtExtractRoot = Join-Path $VendorRoot "onnxruntime"

$Plan = @(
    @{
        Name = "ONNX Runtime CPU (x64)"
        Url  = $OrtUrl
        Zip  = $OrtDestZip
        Into = $OrtExtractRoot
        Note = "Official Microsoft zip; expect include/ + lib/onnxruntime.{lib,dll}"
    }
    @{
        Name = "OpenCV + FFmpeg + glog/jsoncpp/curl"
        Url  = "(conda-forge or vcpkg — not downloaded by this script)"
        Zip  = $null
        Into = Join-Path $VendorRoot "opencv"
        Note = "Install via: conda create -n easyaiot-runtime -c conda-forge opencv ffmpeg glog jsoncpp libcurl cmake"
    }
)

Write-Host "[RUNTIME] vendor root: $VendorRoot"
Write-Host "[RUNTIME] ORT version: $OrtVersion"
Write-Host ""

foreach ($item in $Plan) {
    Write-Host "=== $($item.Name) ==="
    Write-Host "  URL:  $($item.Url)"
    if ($item.Zip) {
        Write-Host "  ZIP:  $($item.Zip)"
    }
    Write-Host "  INTO: $($item.Into)"
    Write-Host "  NOTE: $($item.Note)"
    Write-Host ""
}

if (-not $Execute) {
    Write-Host "[dry-run] No files downloaded. Re-run with -Execute to fetch ORT."
    exit 0
}

New-Item -ItemType Directory -Force -Path $VendorRoot | Out-Null

if (-not (Test-Path $OrtDestZip)) {
    Write-Host "[download] $OrtUrl"
    Invoke-WebRequest -Uri $OrtUrl -OutFile $OrtDestZip -UseBasicParsing
} else {
    Write-Host "[skip] zip exists: $OrtDestZip"
}

$Staging = Join-Path $VendorRoot "_staging_ort"
if (Test-Path $Staging) {
    Remove-Item -Recurse -Force $Staging
}
New-Item -ItemType Directory -Force -Path $Staging | Out-Null

Write-Host "[extract] $OrtDestZip -> $Staging"
Expand-Archive -Path $OrtDestZip -DestinationPath $Staging -Force

$Inner = Get-ChildItem -Path $Staging -Directory | Select-Object -First 1
if (-not $Inner) {
    throw "ORT zip layout unexpected: no top-level directory under $Staging"
}

if (Test-Path $OrtExtractRoot) {
    Remove-Item -Recurse -Force $OrtExtractRoot
}
New-Item -ItemType Directory -Force -Path $OrtExtractRoot | Out-Null
Copy-Item -Path (Join-Path $Inner.FullName "*") -Destination $OrtExtractRoot -Recurse -Force
Remove-Item -Recurse -Force $Staging

Write-Host "[done] ONNX Runtime SDK at: $OrtExtractRoot"
Write-Host "Configure: cmake -G `"Visual Studio 16 2019`" -A x64 -B build -DONNXRUNTIME_ROOT=`"$OrtExtractRoot`""
