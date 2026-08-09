#Requires -Version 5.1
<#
.SYNOPSIS
  Prepend RUNTIME Windows runtime DLL directories to PATH (G-1.2 smoke / VIDEO daemon).

.DESCRIPTION
  - onnxruntime.dll: POST_BUILD next to RUNTIME.exe (build-win/Release on PATH)
  - OpenCV / jsoncpp: vendor/win-x64/conda-pkgs (gitignored locally)
  - FFmpeg 5.x: conda-pkgs/ffmpeg (RUNTIME direct link: avformat-59, etc.)
  - FFmpeg 4.x: required by opencv_videoio460 (avformat-58, swscale-5, etc.)
    Install once: conda create -y -p RUNTIME/vendor/win-x64/_conda_ffmpeg4 -c conda-forge ffmpeg=4.4.2
  - glog / curl / lapack / zlib: conda base Library\bin

.EXAMPLE
  . .\RUNTIME\scripts\deploy.env.ps1
  .\RUNTIME\build-win\Release\RUNTIME.exe testdata\runtime-parity\config\g12_smoke.ini
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RuntimeRoot = Resolve-Path (Join-Path $ScriptDir "..")
$RepoRoot = Resolve-Path (Join-Path $RuntimeRoot "..")
$VendorRoot = Join-Path $RuntimeRoot "vendor\win-x64"
$BuildRelease = Join-Path $RuntimeRoot "build-win\Release"
$CondaPkgs = Join-Path $VendorRoot "conda-pkgs"

function Resolve-CondaLibraryBin {
    if ($env:CONDA_PREFIX) {
        $p = Join-Path $env:CONDA_PREFIX "Library\bin"
        if (Test-Path $p) { return $p }
    }
    foreach ($candidate in @(
            "F:\anaconda\Library\bin",
            "$env:USERPROFILE\anaconda3\Library\bin",
            "$env:USERPROFILE\miniconda3\Library\bin",
            "C:\ProgramData\anaconda3\Library\bin"
        )) {
        if (Test-Path $candidate) { return $candidate }
    }
    return $null
}

function Resolve-CondaPkgsRoot {
    if ($env:CONDA_PKGS_DIRS) {
        foreach ($d in ($env:CONDA_PKGS_DIRS -split ';')) {
            if (Test-Path $d) { return $d }
        }
    }
    foreach ($candidate in @(
            "F:\anaconda\pkgs",
            "$env:USERPROFILE\anaconda3\pkgs",
            "$env:USERPROFILE\miniconda3\pkgs"
        )) {
        if (Test-Path $candidate) { return $candidate }
    }
    return $null
}

function Resolve-FirstExistingBin {
    param([string[]]$Candidates)
    foreach ($c in $Candidates) {
        $bin = if ($c -match '\\bin$') { $c } else { Join-Path $c "Library\bin" }
        if (Test-Path $bin) { return $bin }
    }
    return $null
}

function Resolve-OpenCvFfmpeg4Bin {
    $candidates = @(
        (Join-Path $CondaPkgs "ffmpeg4"),
        (Join-Path $VendorRoot "_conda_ffmpeg4"),
        (Join-Path $VendorRoot "_staging_ffmpeg4")
    )
    Resolve-FirstExistingBin -Candidates $candidates
}

function Resolve-OpenCvExtraBins {
    $pkgsRoot = Resolve-CondaPkgsRoot
    if (-not $pkgsRoot) { return @() }
    $names = @("jasper-*", "libcblas-*", "liblapack-*")
    $bins = @()
    foreach ($pattern in $names) {
        $hit = Get-ChildItem -Path $pkgsRoot -Directory -Filter $pattern -ErrorAction SilentlyContinue |
            Sort-Object Name -Descending |
            Select-Object -First 1
        if ($hit) {
            $bin = Join-Path $hit.FullName "Library\bin"
            if (Test-Path $bin) { $bins += $bin }
        }
    }
    return $bins | Select-Object -Unique
}

$PathEntries = @(
    $BuildRelease,
    # Must precede conda base: opencv_dnn needs libprotobuf 3.21.x (base may ship 3.20)
    (Join-Path $CondaPkgs "libprotobuf\Library\bin"),
    (Join-Path $CondaPkgs "opencv\Library\bin"),
    (Join-Path $CondaPkgs "ffmpeg\Library\bin"),
    (Join-Path $CondaPkgs "jsoncpp\Library\bin")
)

$ffmpeg4Bin = Resolve-OpenCvFfmpeg4Bin
if ($ffmpeg4Bin) {
    $PathEntries += $ffmpeg4Bin
} else {
    Write-Warning "[deploy.env] FFmpeg 4.x not found (opencv_videoio needs avformat-58). Run: conda create -y -p RUNTIME/vendor/win-x64/_conda_ffmpeg4 -c conda-forge ffmpeg=4.4.2"
}

$condaBin = Resolve-CondaLibraryBin
if ($condaBin) {
    $PathEntries += $condaBin
} else {
    Write-Warning "[deploy.env] conda Library\bin not found; glog/curl/lapack DLLs may be missing."
}

$PathEntries += Resolve-OpenCvExtraBins

$missing = @()
foreach ($entry in ($PathEntries | Select-Object -Unique)) {
    if (-not (Test-Path $entry)) {
        $missing += $entry
    }
}
if ($missing.Count -gt 0) {
    Write-Warning "[deploy.env] Missing PATH entries (build or conda-pkgs may be absent):"
    $missing | ForEach-Object { Write-Warning "  $_" }
}

$prepend = ($PathEntries | Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique) -join ";"
if ($prepend) {
    $env:PATH = "$prepend;$env:PATH"
}

$env:RUNTIME_REPO_ROOT = $RepoRoot.Path
$env:RUNTIME_ROOT = $RuntimeRoot.Path
$env:RUNTIME_BIN = Join-Path $BuildRelease "RUNTIME.exe"

Write-Host "[deploy.env] RUNTIME_REPO_ROOT=$($env:RUNTIME_REPO_ROOT)"
Write-Host "[deploy.env] RUNTIME_BIN=$($env:RUNTIME_BIN)"
Write-Host "[deploy.env] Prepended $($($PathEntries | Select-Object -Unique).Count) entries to PATH"
