# 自动化标注功能说明

## 功能概述

已实现完整的自动化标注功能，包括：

1. 数据库表结构设计（`auto_label_task` / `auto_label_result`，含 **`model_id`**）
2. 后端 Python Flask API（`app/blueprints/auto_label.py`）
3. **进程内直连推理**（`InferenceService.detect_image_file`，**无需部署推理服务**）
4. 前端统一标注平台（`AnnotationTool` + `AILabelModal`）
5. 导入/导出（iot-dataset `/annotation/*`）

## 快速使用

1. **导入图片**：数据集详情 → 标注工具 →「添加」→ 导入/上传
2. **准备模型**：训练完成或上传模型，确认 **model_id** 对应记录 **有权重文件**（PT/ONNX 等）
3. **批量标注**：标注工具顶栏 →「AI 标注」→ **选择模型（model_id）** → 开启
4. **查看进度**：顶栏与进度条显示 `已处理/总数`
5. **验收修正**：抽查误检 → 划分用途 → 同步 Minio → 导出/训练

> **不需要** 为自动标注单独「模型部署 → 启动推理服务」。对外 API 推理、VIDEO 算法任务仍使用 deploy。

## 后端 API 摘要

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/model/dataset/dataset/{id}/auto-label/start` | 启动批量任务，`{ "model_id": N }` |
| GET | `/model/dataset/dataset/{id}/auto-label/task/{task_id}` | 查询进度 |
| GET | `/model/dataset/dataset/{id}/auto-label/tasks` | 任务列表 |
| POST | `/model/dataset/dataset/{id}/auto-label/image/{image_id}` | 单张标注（前端待接入） |

网关完整路径前缀：`/admin-api/model/...`

**请求示例：**

```json
{
  "model_id": 12,
  "confidence_threshold": 0.5
}
```

`model_service_id` 仍兼容，但 **推荐改用 model_id**。

## 前端组件

| 组件 | 路径 |
|------|------|
| 标注主界面 | `WEB/src/views/dataset/components/AnnotationTool/index.vue` |
| AI 弹窗 | `WEB/src/views/dataset/components/AutoLabel/AILabelModal/index.vue` |
| 导入 | `AutoLabel/ImportDatasetModal/index.vue` |
| 导出 | `AutoLabel/ExportDatasetModal/index.vue` |
| API | `WEB/src/api/device/auto-label.ts` |

> 独立服务 `AI/services/auto-labeling`（端口 8000）已弃用。

## 配置

```bash
# AI model-server .env
JAVA_BACKEND_URL=http://iot-gateway:48080

# 可选：自动标注性能
AUTO_LABEL_PREFETCH_WORKERS=2              # MinIO 下载预取并行度
AUTO_LABEL_PROGRESS_COMMIT_INTERVAL=10     # 进度落库间隔（张）
```

数据库表见 `.scripts/postgresql/iot-ai10.sql`，或由 `db.create_all()` / `ensure_auto_label_task_model_id_column()` 自动创建。

## 注意事项

1. **必须选择有权重的 model_id**，否则无法启动标注
2. **不再依赖** Nacos / deploy 推理服务（自动标注链路）
3. **标注格式** 与手工标注一致（归一化矩形 + `label` 类别名）
4. **任务完成后** 前端会自动同步数据集标签（从标注扫描创建）
5. Java `POST /dataset/{id}/auto-label` 为空桩，**请勿使用**；请走 model-server 接口

## 相关文档

- [AI 模块 README](README.md)
- [SAM 快速指南](SAM_README.md)
