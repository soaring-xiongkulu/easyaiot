# RUNTIME 原画 / AI 并排预览工具

对比 **推流转发原画**（SRS `live/{device_id}`）与 **算法 RUNTIME AI 带框**（SRS `ai/{device_id}`）的浏览器预览页。

适用于验证：

- forward-only（`task_type=forward`）与 realtime AI 是否都在推流
- 原画 / AI 的 OSD 时间差（延时）
- AI 叠框样式是否正常

---

## 文件

| 文件 | 说明 |
|------|------|
| `index.html` | 并排预览页（flv.js，低缓冲） |
| `serve_runtime_viewer.py` | 启本地 HTTP + 探测 SRS 流 |
| `README.md` | 本文档 |

---

## 前置条件

1. **SRS** 已启动，HTTP-FLV 端口通常为 **8080**（API 多为 **1985**）
2. 对应设备已在跑：
   - 推流转发 → `http://{host}:8080/live/{device_id}.flv`
   - 算法 RUNTIME（executor=cpp）→ `http://{host}:8080/ai/{device_id}.flv`
3. 浏览器建议 **Chrome / Edge**（需支持 MSE + flv.js）

---

## 快速开始

在仓库 `VIDEO` 目录下：

```bash
cd /projects/new/easyaiot/VIDEO

# 启动预览页（默认监听 0.0.0.0:8899，并探测流）
python3 tools/runtime_stream_viewer/serve_runtime_viewer.py \
  --device-id 1786351452026243807 \
  --host 172.16.13.220:8080
```

终端会打印本机 / 局域网地址，例如：

```text
本机打开 : http://127.0.0.1:8899/index.html?host=172.16.13.220%3A8080&device_id=...
局域网   : http://172.16.13.220:8899/index.html?host=...
```

浏览器打开任一链接即可。页面上可改 `host` / `device_id` 后点「应用并播放」。

---

## 仅探测流（不启 HTTP）

```bash
python3 tools/runtime_stream_viewer/serve_runtime_viewer.py --probe-only \
  --device-id 1786351452026243807 \
  --host 172.16.13.220:8080
```

成功时类似：

```text
live : OK  (HTTP 200 Content-Type=video/x-flv ...)
ai   : OK  (HTTP 200 Content-Type=video/x-flv ...)
结果: 原画与 AI 均可达
```

退出码：`0` 双通，`1` 部分/全失败，`2` 参数错误。

---

## 参数与环境变量

| 参数 | 环境变量 | 默认 | 说明 |
|------|----------|------|------|
| `--host` | `SRS_HTTP_HOST` | `127.0.0.1:8080` | SRS HTTP-FLV 主机:端口 |
| `--device-id` | `RUNTIME_VIEWER_DEVICE_ID` | 空 | 设备 ID |
| `--live-app` | — | `live` | 原画 SRS app |
| `--ai-app` | — | `ai` | AI SRS app |
| `--bind` | `RUNTIME_VIEWER_BIND` | `0.0.0.0` | HTTP 监听地址 |
| `--port` | `RUNTIME_VIEWER_PORT` | `8899` | HTTP 端口 |
| `--srs-api` | `SRS_API` | `http://127.0.0.1:1985` | SRS HTTP API |
| `--probe-only` | — | — | 只探测，不启服务 |
| `--no-probe` | — | — | 启服务前跳过探测 |
| `--timeout` | — | `3` | 探测超时（秒） |

页面也支持 URL 查询参数：

```text
?host=172.16.13.220:8080&device_id=xxx&live_app=live&ai_app=ai
```

---

## 典型联调路径（NVR CH1 示例）

1. 确认推流转发任务在跑（`executor=cpp`，原画进 `live/`）
2. 确认算法 realtime 任务在跑（`executor=cpp`，AI 进 `ai/`）
3. 启动本工具并打开页面，对比：
   - 左/上：**原画 live**
   - 右/下：**AI 带框**
4. 看 OSD 时间戳判断延时；看绿色框是否与 VIDEO python 路径一致

相关配置生成：

- 推流转发 ini：`VIDEO/app/services/runtime_config_service.py` → `generate_stream_forward_runtime_ini`
- 算法 ini：同文件 → `generate_runtime_ini`
- RUNTIME 叠框：`RUNTIME/src/pipeline/Pipeline.cpp` → `drawDetectionOverlay`

---

## 常见问题

### 页面打不开 / 连接被拒绝

- 确认脚本已启动，且防火墙放行 `--port`（默认 8899）
- WEB 管理台 `8888` 与本工具无关；本工具只依赖 SRS + 本机 HTTP

### 一路黑屏 / 报 flv 错误

- `--probe-only` 看哪一路 FAIL
- 检查 VIDEO 里对应任务是否 `is_enabled`、RUNTIME 进程是否存在
- 确认 `device_id` 与 SRS 流名一致（不要带 `.flv`）

### 原画比 AI 慢 / AI 框又粗又糊

- 原画与 AI 应尽量都走主码流做质量对比；子码流（如海康 `102`）分辨率低，放大后框会显得粗糊
- 播放器已关 stash；若仍慢，查 NVR 码流本身 OSD，而非仅看浏览器

### flv.js CDN 加载失败

页面默认从 `cdn.jsdelivr.net` 拉 flv.js。若内网无外网，可把 `flv.min.js` 下到本目录并改 `index.html` 里的 `<script src=...>` 为相对路径。

---

## 与旧临时页的关系

此前临时页在 `/tmp/nvr_runtime_viewer.html`（硬编码 CH1）。请改用本目录工具；参数化后可复用任意 `device_id`。
