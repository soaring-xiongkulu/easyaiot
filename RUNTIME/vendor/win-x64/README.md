# RUNTIME Windows x64 vendor layout

Phase 1 目标：MSVC Release 产出 `RUNTIME.exe`，运行时从本目录（或等价路径）加载 ORT / OpenCV / FFmpeg DLL，**不**引入 rebekah 私有 CompatibleLib。

## 目录约定

```text
RUNTIME/vendor/win-x64/
├── onnxruntime/          # 官方 CPU 包解压（首选 G-1.2 前用 CPU）
│   ├── include/
│   ├── lib/
│   │   ├── onnxruntime.lib
│   │   └── onnxruntime.dll
│   └── (optional) lib/onnxruntime_providers_shared.dll
├── opencv/               # vcpkg / conda-forge 或手工拷贝的 bin/*.dll
├── ffmpeg/               # avcodec-*.dll, avformat-*.dll, avutil-*.dll, swscale-*.dll
└── deploy.env.ps1        # 生成 PATH 片段（待 Phase 1 脚本写入）
```

CMake 默认 `-DONNXRUNTIME_ROOT=%RUNTIME%/vendor/win-x64/onnxruntime`（见 `CMakeLists.txt` 中 `RUNTIME_VENDOR_ROOT`）。

## 获取依赖

```powershell
# 默认 dry-run，打印将下载的 URL
.\RUNTIME\scripts\fetch_deps_windows.ps1

# 实际拉取 ONNX Runtime CPU zip（约 50MB+）
.\RUNTIME\scripts\fetch_deps_windows.ps1 -Execute
```

OpenCV / FFmpeg / glog / jsoncpp / libcurl：推荐 **conda-forge** `easyaiot-runtime` 环境（`Library/bin` + `Library/lib`），或 vcpkg triplet `x64-windows`。本 vendor 树主要承载 **ORT 官方预编译包** 与部署时复制的运行时 DLL。

## 运行时 DLL 搜索路径（计划）

VIDEO daemon 拉起 `RUNTIME.exe` 前（或 `main` 最早阶段）：

1. `SetDllDirectoryA(<vendor>/onnxruntime/lib)` — ORT 及同目录附属 DLL  
2. 将 `opencv/bin`、`ffmpeg/bin` 追加到进程 `PATH`，或再次 `SetDllDirectory`（仅单目录；多目录用 `AddDllDirectory` + `PATH` 组合）  
3. 记录启动日志：`infer_ep=cpu|cuda|dml`（DirectML 为后续专题）

与 rebekah-learn 一致的原则：**重依赖不进链接期硬编码绝对路径**，发行包为 `RUNTIME.exe` + vendor 快照。

## 版本

与 Linux 对齐：`onnxruntime-*-1.23.2`（见 `install_linux.sh` 中 `ORT_VERSION`）。

## 禁止

- 不得从 rebekah `vendor/core` 复制任何 DLL  
- 不得将 CompatibleLib / 授权剥离 DLL 纳入本树
