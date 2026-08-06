# EasyAIoT RTC 模块

基于 [go2rtc](https://github.com/AlexxIT/go2rtc) 的 RTC 模块，为 EasyAIoT 平台提供消费级摄像头 P2P/私有协议桥接能力。

## 支持的平台

| 平台 | 协议 | 双向对讲 | 接入方式 |
|------|------|----------|----------|
| **Tapo** (TP-Link) | `tapo://` | ✅ | 云密码 / MD5·SHA256 哈希 |
| **Tuya** (涂鸦) | `tuya://` | ✅ | Tuya Smart / Cloud API |
| **Ring** | `ring://` | ✅ | OAuth / refresh_token |
| **Nest** (Google) | `nest://` | — | Google Device Access API |
| **Xiaomi** (米家) | `xiaomi://` | ✅ | WebUI 账号绑定 |
| **Wyze** | `wyze://` | ✅ | WebUI + Developer API Key |
| **DoorBird** | `doorbird://` | ✅ | 本地用户名密码 |
| **GoPro** | `gopro://` | — | USB/Wi-Fi 本地发现 |
| **Roborock** (石头) | `roborock://` | ✅ | WebUI 账号绑定 |

底层协议实现均来自 go2rtc 源码（`vendor/go2rtc/internal/*`），RTC 模块提供：

- **统一管理 API** — 平台化注册流、获取播放地址
- **Docker 一体化部署** — go2rtc + Python 管理服务同容器
- **与 VIDEO 模块对接** — 桥接后的 RTSP/WebRTC 流可推入 SRS/ZLM

## 架构

```
┌─────────────────────────────────────────────────┐
│  EasyAIoT WEB / VIDEO                           │
│  摄像头管理 · 流转发 · 算法任务                    │
└────────────────────┬────────────────────────────┘
                     │ HTTP API (:6100)
┌────────────────────▼────────────────────────────┐
│  RTC 管理服务 (Python Flask)                     │
│  /api/platforms  /api/streams  /actuator/health │
└────────────────────┬────────────────────────────┘
                     │ go2rtc REST API (:1984)
┌────────────────────▼────────────────────────────┐
│  go2rtc (Go, vendor/go2rtc)                     │
│  Tapo · Tuya · Ring · Nest · Xiaomi · Wyze ...  │
└────────────────────┬────────────────────────────┘
                     │ P2P / 私有协议
┌────────────────────▼────────────────────────────┐
│  消费级摄像头 / 门铃 / 扫地机 / GoPro             │
└─────────────────────────────────────────────────┘
```

## 快速开始

### 1. 拉取 go2rtc 源码

```bash
bash RTC/install_linux.sh vendor
```

源码位于 `RTC/vendor/go2rtc/`，由 install 脚本从 GitHub 拉取。

### 2. 构建并启动

```bash
bash RTC/install_linux.sh start
```

服务端口：

| 服务 | 端口 | 说明 |
|------|------|------|
| RTC 管理 API | **6100** | 平台注册、流管理、健康检查 |
| go2rtc Web UI | **1984** | 原生 Web 界面（账号绑定、设备发现） |
| go2rtc RTSP | **8554** | 标准 RTSP 输出 |
| go2rtc WebRTC | **8555** | WebRTC 播放 |

### 3. 注册摄像头流

**Tapo 示例：**

```bash
curl -X POST http://localhost:6100/api/streams \
  -H "Content-Type: application/json" \
  -d '{
    "name": "tapo_living_room",
    "platform": "tapo",
    "params": {
      "host": "192.168.1.123",
      "password": "your-cloud-password"
    }
  }'
```

**Wyze 示例（需先在 go2rtc WebUI 完成账号绑定获取参数）：**

```bash
curl -X POST http://localhost:6100/api/streams \
  -H "Content-Type: application/json" \
  -d '{
    "name": "wyze_front",
    "platform": "wyze",
    "params": {
      "host": "192.168.1.124",
      "uid": "WYZEUID...",
      "enr": "...",
      "mac": "AABBCCDDEEFF",
      "model": "HL_CAM4"
    }
  }'
```

**直接使用 go2rtc 源流 URL：**

```bash
curl -X POST http://localhost:6100/api/streams \
  -H "Content-Type: application/json" \
  -d '{
    "name": "custom_cam",
    "source": "tapo://password@192.168.1.125"
  }'
```

### 4. 获取播放地址

```bash
curl http://localhost:6100/api/streams/tapo_living_room/play
```

返回 WebRTC、HLS、RTSP、MJPEG 等播放 URL。

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/platforms` | 列出支持的平台及字段定义 |
| GET | `/api/platforms/{id}` | 平台详情 |
| GET | `/api/streams` | 列出所有流（代理 go2rtc） |
| POST | `/api/streams` | 注册流（platform+params 或 source） |
| DELETE | `/api/streams/{name}` | 删除流 |
| GET | `/api/streams/{name}/play` | 获取播放地址 |
| POST | `/api/streams/build-url` | 预览流 URL（不注册） |
| GET | `/actuator/health` | 健康检查 |

## 与 VIDEO / WEB 全链路集成

平台已完成端到端打通：

```
WEB 添加设备 → VIDEO /register/device/rtc-live → RTC /api/streams → go2rtc
     ↓
Device.source = rtsp://127.0.0.1:8554/{id}
     ↓
stream_forward → SRS /live/{id}.flv → Jessibuca 播放
```

### VIDEO API（前缀 `/video/camera`）

| 端点 | 说明 |
|------|------|
| `GET /rtc/config` | RTC / go2rtc 公共配置 |
| `GET /rtc/platforms` | 平台列表（代理 RTC 服务） |
| `POST /rtc/build-url` | 预览源流 URL |
| `POST /register/device/rtc-live` | 一键注册（go2rtc + VIDEO 设备 + SRS 转发） |

环境变量（`VIDEO/env.example`）：

```bash
RTC_SERVICE_URL=http://127.0.0.1:6100
RTC_GO2RTC_WEB_URL=/dev-api/go2rtc
RTC_RTSP_HOST=127.0.0.1
RTC_RTSP_PORT=8554
```

### WEB 前端

- **添加设备 → RTC 平台** Tab：动态表单，支持 9 大平台
- **接入 RTC 摄像头** 快捷按钮
- go2rtc WebUI 经 nginx `/dev-api/go2rtc/` 反代（OAuth 绑定）

### 删除联动

删除 VIDEO 设备时，若 `hardware_id` 以 `rtc:` 开头，自动调用 RTC 清理 go2rtc 流。

## 目录结构

```
RTC/
├── vendor/go2rtc/          # go2rtc 上游源码（git clone）
├── app/
│   ├── blueprints/         # Flask API 路由
│   ├── models/             # 平台数据模型
│   └── services/           # go2rtc 客户端、流管理、平台注册表
├── config/
│   └── go2rtc.yaml.template
├── Dockerfile              # 多阶段：编译 go2rtc + Python 运行时
├── docker-compose.yaml
├── docker-entrypoint.sh
├── install_linux.sh
├── run.py
├── requirements.txt
└── env.example
```

## 开发

```bash
# 本地 Python 开发（需独立运行 go2rtc）
bash RTC/install_linux.sh dev

# 重新构建镜像
bash RTC/install_linux.sh rebuild

# 更新 go2rtc 源码
bash RTC/install_linux.sh vendor
```

## 注意事项

- **网络模式**：默认 `host` 网络，P2P 摄像头需局域网直连
- **OAuth 平台**：Ring/Nest/Xiaomi/Wyze/Roborock 首次配置需 go2rtc WebUI
- **Tuya**：不支持 Smart Life 账号，需 Tuya Smart App
- **Nest**：需 Google Device Access 付费 API
- **安全**：生产环境请配置 `GO2RTC_USERNAME` / `GO2RTC_PASSWORD`

## 许可证

- RTC 封装层：遵循 EasyAIoT 项目许可
- go2rtc：MIT License（[AlexxIT/go2rtc](https://github.com/AlexxIT/go2rtc)）
