# 自动化标注功能说明

## 功能概述

已实现完整的自动化标注功能，包括：
1. 数据库表结构设计
2. 后端 Python Flask API
3. 前端 Vue 组件
4. 导出 ZIP 功能

## 数据库表结构

### auto_label_task（自动化标注任务表）
- `id`: 主键
- `dataset_id`: 数据集ID
- `model_service_id`: AI服务ID（外键关联ai_service表）
- `status`: 状态（PENDING/PROCESSING/COMPLETED/FAILED）
- `total_images`: 总图片数
- `processed_images`: 已处理图片数
- `success_count`: 成功标注数
- `failed_count`: 失败数
- `confidence_threshold`: 置信度阈值
- `created_at`: 创建时间
- `updated_at`: 更新时间
- `started_at`: 开始时间
- `completed_at`: 完成时间
- `error_message`: 错误信息

### auto_label_result（自动化标注结果表）
- `id`: 主键
- `task_id`: 任务ID（外键关联auto_label_task表）
- `dataset_image_id`: 数据集图片ID
- `annotations`: 标注结果JSON
- `status`: 状态（SUCCESS/FAILED）
- `error_message`: 错误信息
- `created_at`: 创建时间

## 后端 API

### 1. 启动自动化标注任务
```
POST /dataset/{dataset_id}/auto-label/start
请求体:
{
  "model_service_id": 1,
  "confidence_threshold": 0.5
}
```

### 2. 获取任务状态
```
GET /dataset/{dataset_id}/auto-label/task/{task_id}
```

### 3. 获取任务列表
```
GET /dataset/{dataset_id}/auto-label/tasks?page=1&page_size=10
```

### 4. 导出标注数据集
```
POST /dataset/{dataset_id}/auto-label/export
请求体:
{
  "task_id": 1,  // 可选，不提供则导出所有已标注的图片
  "train_ratio": 0.7,
  "val_ratio": 0.2,
  "test_ratio": 0.1,
  "format": "yolo"
}
```

## 前端组件

### 位置
- 组件: `/WEB/src/views/dataset/components/AutoLabel/index.vue`
- API: `/WEB/src/api/device/auto-label.ts`
- 已添加到 DatasetDetail 的 tab 列表中

### 功能
1. 查看任务列表
2. 创建新的标注任务
3. 查看任务详情（实时刷新进度）
4. 导出标注后的数据集为ZIP

## 配置说明

### 环境变量
需要在 `.env` 文件中配置：
```bash
# Java后端地址（用于获取数据集图片列表）
JAVA_BACKEND_URL=http://localhost:8080
```

### 数据库迁移
运行应用时，数据库表会自动创建（通过 `db.create_all()`）。

如果需要手动创建表，可以执行：
```python
from db_models import db, AutoLabelTask, AutoLabelResult
db.create_all()
```

## 使用流程

1. **准备AI服务**
   - 确保有运行中的AI服务（通过模型部署功能部署）
   - AI服务状态必须为 `running`

2. **创建标注任务**
   - 进入数据集详情页面
   - 点击"自动化标注" tab
   - 点击"新建标注任务"
   - 选择AI服务和置信度阈值
   - 点击确定启动任务

3. **查看任务进度**
   - 在任务列表中查看任务状态
   - 点击"查看详情"查看详细进度
   - 处理中的任务会自动刷新状态

4. **导出数据集**
   - 任务完成后，点击"导出数据集"
   - 设置训练集/验证集/测试集比例
   - 选择导出格式（目前支持YOLO格式）
   - 点击确定下载ZIP文件

## 注意事项

1. **Java后端集成**
   - 后端代码中通过HTTP调用Java后端API获取图片列表
   - 需要确保 `JAVA_BACKEND_URL` 环境变量配置正确
   - Java后端API路径：`/dataset/image/page` 和 `/dataset/image/get`

2. **MinIO路径解析**
   - 图片路径格式：`/api/v1/buckets/{bucket}/objects/download?prefix={object_key}`
   - 代码中已实现路径解析功能

3. **推理服务调用**
   - 使用 `ClusterInferenceService.inference_via_cluster` 调用推理服务
   - 需要确保AI服务正常运行且可访问

4. **异步任务处理**
   - 标注任务在后台异步执行
   - 使用线程池处理，不会阻塞主线程

5. **错误处理**
   - 任务失败会记录错误信息
   - 单个图片处理失败不会影响整个任务

## 待优化项

1. 支持更多导出格式（COCO、Pascal VOC等）
2. 支持批量任务管理
3. 支持任务暂停/恢复
4. 优化大数据集的处理性能
5. 添加任务通知功能
