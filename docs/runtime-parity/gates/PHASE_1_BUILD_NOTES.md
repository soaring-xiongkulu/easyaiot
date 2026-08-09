# Phase 1 — Windows MSVC 构建笔记

> 状态：G-1.1 **已达**（2026-08-09）  
> 关联门控：G-1.1（Release `RUNTIME.exe`）、G-1.2（`infer_ep` 探测，待下一波）

## 产物

| 项 | 值 |
|----|-----|
| 可执行文件 | `RUNTIME/build-win/Release/RUNTIME.exe` |
| 构建配置 | VS 2019 (v142) / x64 / Release |
| ORT 版本 | 1.23.2 CPU（`vendor/win-x64/onnxruntime/`） |
| 构建日志退出码 | `cmake --build ... --config Release` → **0** |

POST_BUILD 已将 `onnxruntime.dll` 复制到 exe 同目录。

## 依赖来源（本机实测）

| 库 | 来源 | 备注 |
|----|------|------|
| ONNX Runtime | `fetch_deps_windows.ps1 -Execute` | 官方 Microsoft zip |
| OpenCV 4.6 | conda-forge 包解压至 `vendor/win-x64/conda-pkgs/opencv/` | 或 `conda install -c conda-forge opencv` |
| FFmpeg 5.1 | 同上 `conda-pkgs/ffmpeg/` | base conda 未预装；`conda install` 因 OOM 未用 |
| jsoncpp | 同上 `conda-pkgs/jsoncpp/` | |
| glog / libcurl | `F:\anaconda\Library` | 已在 base 环境 |

**conda 备选（编排决策后可执行）：**

```powershell
conda create -n easyaiot-runtime -c conda-forge opencv ffmpeg glog jsoncpp libcurl cmake
conda activate easyaiot-runtime
```

## 构建命令（可复现）

```powershell
# 1) 拉取 ORT（若 vendor/onnxruntime 不存在）
.\RUNTIME\scripts\fetch_deps_windows.ps1 -Execute

# 2) 若 conda base 缺 opencv/ffmpeg/jsoncpp，可用脚本将 conda-forge 包解压到 vendor/win-x64/conda-pkgs/
#    （本机构建时已手工完成；目录已 gitignore）

# 3) 配置 + 编译
$cp = @(
  "$PWD\RUNTIME\vendor\win-x64\conda-pkgs\opencv\Library",
  "$PWD\RUNTIME\vendor\win-x64\conda-pkgs\ffmpeg\Library",
  "$PWD\RUNTIME\vendor\win-x64\conda-pkgs\jsoncpp\Library",
  "$env:CONDA_PREFIX\Library"
) -join ";"

cmake -G "Visual Studio 16 2019" -A x64 `
  -S RUNTIME -B RUNTIME/build-win `
  -DCMAKE_PREFIX_PATH="$cp" `
  -DONNXRUNTIME_ROOT="$PWD\RUNTIME\vendor\win-x64\onnxruntime"

cmake --build RUNTIME/build-win --config Release
```

## MSVC 补丁摘要（已合入）

- `CMakeLists.txt`：`/utf-8`、`GLOG_NO_ABBREVIATED_SEVERITIES`、Windows include 路径补全、移除 `opencv_geometry`（OpenCV 4.x 用 `imgproc`）
- `win_compat.h`：`runtime_widen_utf8()` 供 ORT `wchar_t` 模型路径
- `Yolov11Engine.cpp`：Windows 下 UTF-8→宽字符 Session 构造
- `Detech.cpp` / `SnapScheduler.cpp` / `PatrolScheduler.cpp`：`geometry.hpp` → `imgproc.hpp`
- `fetch_deps_windows.ps1`：robocopy 清理损坏的 `onnxruntime/` 目录（长路径）

## 运行时 DLL PATH（本地 smoke）

```powershell
$env:PATH = @(
  "RUNTIME\build-win\Release",
  "RUNTIME\vendor\win-x64\conda-pkgs\opencv\Library\bin",
  "RUNTIME\vendor\win-x64\conda-pkgs\ffmpeg\Library\bin",
  "$env:CONDA_PREFIX\Library\bin"
) -join ";"
.\RUNTIME\build-win\Release\RUNTIME.exe
```

## G-1.2 `infer_ep` 探测计划（未执行）

1. 准备最小 `config.ini`（含 ONNX 模型路径、`force_cpu=1`）
2. 启动 RUNTIME，检查日志行：`[YOLO] Model loaded successfully infer_ep=cpu`
3. 期望：`infer_ep=cpu`（当前仅链入 CPU EP；DirectML/CUDA 为后续专题）
4. 证据归档：daemon 日志片段写入 `PHASE_1_GATE.md`

## 已知风险 / 未完成

- `conda install` 在本机 solver OOM；长期应使用独立 `easyaiot-runtime` 环境或 vcpkg manifest
- `deploy.env.ps1` 尚未生成（VIDEO daemon 拉起前 PATH 仍须手工设置）
- G-1.3 / G-1.4 未开始
