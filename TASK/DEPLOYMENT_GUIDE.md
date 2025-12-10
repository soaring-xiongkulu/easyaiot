# TASK模块部署和测试指南

## ✅ 编译成功后的步骤

### 阶段1：基础测试（RTSP连接）

#### 1.1 不启用AI，仅测试RTSP拉流

```powershell
cd F:\EASYLOT\easyaiot-main\TASK\build\Release
.\TASK.exe ..\..\config\test_rtsp_only.ini
```

**预期输出：**
```
============================================================
[STARTING] TASK module initializing...
[CONFIG] Config file: ..\..\config\test_rtsp_only.ini
============================================================
[CONFIG] Reading section: [video]
[CONFIG] Reading section: [ai]
...
[INIT] Step 1: Initializing YOLO detector...
[INIT] YOLO detector initialized successfully (AI disabled)
[INIT] Step 2: Initializing media player...
[INIT] Initializing media player
[INIT] Media player initialized successfully
...
[OK] All components initialized successfully!
System running... Press Ctrl+C to exit
```

**如果成功：** 说明RTSP连接正常，继续下一步
**如果失败：** 检查RTSP URL和摄像头连接

---

### 阶段2：下载YOLO模型

#### 2.1 自动下载（推荐）

```powershell
cd F:\EASYLOT\easyaiot-main\TASK
.\scripts\download_yolo_model.ps1
```

#### 2.2 手动下载

如果自动下载失败：

1. **下载YOLOv11n模型**
   - URL: https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov11n.onnx
   - 大小: 约6MB
   - 保存到: `F:\EASYLOT\easyaiot-main\TASK\models\yolov11n.onnx`

2. **创建类别文件**
   - 位置: `F:\EASYLOT\easyaiot-main\TASK\models\coco.names`
   - 内容: 80个COCO类别（person, car, dog等）

---

### 阶段3：完整功能测试（启用AI）

```powershell
cd F:\EASYLOT\easyaiot-main\TASK\build\Release
.\TASK.exe ..\..\config\test.ini
```

**预期输出：**
```
[INIT] Step 1: Initializing YOLO detector...
[INIT] Model path: F:/EASYLOT/easyaiot-main/TASK/models/yolov11n.onnx
[INIT] Loading YOLO model with 3 threads...
[YOLO] Creating 3 YOLO engine instances...
[YOLO] Loading model instance 1/3...
[YOLO] Creating ONNX Runtime environment...
[YOLO] Using CPU execution provider
[YOLO] Loading model: F:/EASYLOT/easyaiot-main/TASK/models/yolov11n.onnx
[YOLO] Model loaded successfully
[YOLO] Using default COCO classes (80 classes)
[YOLO] Instance 1 loaded successfully
...
[OK] TASK service started successfully!
System running... Press Ctrl+C to exit
```

---

## 🔄 下一步：集成AI模块

### Step 1: 创建TaskManager（进程管理器）

**位置：** `AI/app/services/task_manager.py`

**功能：**
- 启动/停止TASK进程
- 监控TASK进程状态
- 生成配置文件
- 管理多个TASK实例

### Step 2: 添加告警回调API

**位置：** `AI/app/blueprints/alarm_callback.py`

**功能：**
- 接收TASK模块的HTTP告警回调
- 保存告警记录到数据库
- 推送告警到前端（WebSocket）

### Step 3: 前端集成

**功能：**
- 创建RTSP推理任务时调用TaskManager
- 显示实时推理结果
- 接收和展示告警信息

---

## 📊 当前架构

```
┌─────────────┐
│   前端WEB   │
│  (Vue.js)   │
└──────┬──────┘
       │ HTTP API
┌──────▼──────┐      启动/管理      ┌────────────┐
│  AI模块     │◄──────────────────►│ TASK模块   │
│  (Python)   │                     │  (C++)     │
│             │                     │            │
│ TaskManager │◄───── 告警回调 ─────┤ AlarmHook  │
└─────────────┘                     └──────┬─────┘
                                           │
                                    ┌──────▼──────┐
                                    │ 摄像头RTSP  │
                                    └─────────────┘
```

---

## 🚀 快速开始

### 选项A：先测试TASK模块独立运行

```powershell
# 1. 测试RTSP连接
cd F:\EASYLOT\easyaiot-main\TASK\build\Release
.\TASK.exe ..\..\config\test_rtsp_only.ini

# 2. 下载模型
cd F:\EASYLOT\easyaiot-main\TASK
.\scripts\download_yolo_model.ps1

# 3. 测试AI推理
cd build\Release
.\TASK.exe ..\..\config\test.ini
```

### 选项B：直接集成到AI模块

跳过独立测试，直接实现：
1. TaskManager进程管理器
2. 告警回调API
3. 前端集成

---

## 📝 配置文件说明

### test_rtsp_only.ini
- 仅测试RTSP拉流
- AI推理：禁用
- 告警检测：禁用
- 适合：初次测试

### test.ini
- 完整功能测试
- AI推理：启用
- 告警检测：可选
- 适合：模型下载后测试

---

## ⚠️ 注意事项

1. **首次运行**
   - 确保摄像头在线（`rtsp://admin:sr336699@192.168.1.64:554`）
   - 先测试RTSP连接，再启用AI

2. **性能考虑**
   - AI推理（3线程）：CPU占用30-50%
   - 内存占用：约500MB
   - 建议：使用子码流（102）进行AI分析

3. **调试技巧**
   - 查看日志输出判断问题
   - Ctrl+C可以安全退出
   - 检查配置文件路径是否正确

---

## 🆘 常见问题

### Q1: RTSP连接失败
**A:** 检查摄像头IP、用户名、密码是否正确

### Q2: 模型加载失败
**A:** 确认模型文件路径和格式（ONNX）

### Q3: 进程无法启动
**A:** 检查DLL文件是否完整（vcpkg和ONNX Runtime）

---

**接下来选择：**
- ✅ 选项A：先独立测试TASK模块
- ✅ 选项B：直接集成到AI模块
