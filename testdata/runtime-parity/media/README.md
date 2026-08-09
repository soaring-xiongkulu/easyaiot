# Runtime Parity 标准媒体夹具

> Phase 0：仓库内仅放 **≤5MB** 样本或占位说明；大文件走 CI 缓存 / LFS / 下载脚本。

## 夹具 ID 与用途

| 夹具 ID | 内容 | 时长 | 用途 |
|---------|------|------|------|
| `media_person_roi_30s` | 单人走动，已知 bbox 黄金 JSON | 30s@25fps | 检测/追踪/告警基线 |
| `media_static_30s` | 空场景 | 30s | 负例 / 心跳 lifecycle |
| `media_multi_person_60s` | 2–4 人交叉 | 60s | 追踪 ID 稳定性（P1） |

完整矩阵见 `docs/runtime-parity/reports/06-equivalence-testbed.md` §2.3。

## 获取大文件

```bash
# 约定脚本（待 CI 接入）；从内部镜像或对象存储拉取
scripts/fetch_parity_media.sh --id media_person_roi_30s
```

Windows 可手动将 MP4 放入本目录，文件名与 manifest `media_id` 对应，例如：

- `media_person_roi_30s.mp4`
- `media_static_30s.mp4`

## RTSP 回放

本地 RTSP 由 `docs/runtime-parity/testbed/docker-compose.media.yml` 或 Windows 原生 MediaMTX/ffmpeg 提供。  
**两侧 executor 必须使用同一 relay URL**（见 testbed README）。
