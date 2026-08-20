"""
edge 形态：模型管理初始化（无 MinIO / 无 AI 模块）。

- 元数据：与 AI 库 iot-ai10.sql 演示模型对齐，写入 VIDEO 库 model 表
- 权重/封面：从安装包 flat 种子目录同步到本地存储（目录历史名为 .scripts/minio，
  仅目录结构沿用 bucket/key，不启动 MinIO 服务）
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple

from sqlalchemy import text

from models import AiModel, db

logger = logging.getLogger(__name__)

# 与 .scripts/postgresql/iot-ai10.sql / AI 演示库一致
_EDGE_DEMO_MODELS: List[Dict[str, Any]] = [
    {
        'id': 1,
        'name': '人模型',
        'description': '用于识别人的AI算法',
        'model_path': '/api/v1/buckets/models/objects/download?prefix=yolo/yolov11/362479958ba04288b42ab1796f9afa57.pt',
        'image_url': '/api/v1/buckets/models/objects/download?prefix=images/69707887371944979f0fa32091e46b11.jpg',
        'version': '1.0.0',
    },
    {
        'id': 3,
        'name': '安全帽模型',
        'description': '识别安全帽的模型',
        'model_path': '/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/9e75951cea044845be8f8f1f2223c551.pt',
        'image_url': '/api/v1/buckets/models/objects/download?prefix=images/7e6ef2e33af64a18add7f91a66b6403e.jpg',
        'version': '1.0.1',
        'onnx_model_path': 'exports/model_3/onnx/model.onnx',
        'openvino_model_path': 'exports/model_3/openvino/model_openvino_model/',
        'class_names': '["head", "safehat"]',
        'selected_class_names': '["head", "safehat"]',
    },
    {
        'id': 5,
        'name': '反光衣模型',
        'description': '识别反光衣的模型',
        'model_path': '/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/c7b364e123a84f70a954403399c61dac.pt',
        'image_url': '/api/v1/buckets/models/objects/download?prefix=images/a36ab47d67044d6eb07d58aa399bd78b.png',
        'version': '1.0.0',
    },
    {
        'id': 6,
        'name': '睡岗模型',
        'description': '识别在岗位睡觉的模型',
        'model_path': '/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/21f8ba84e4e64d9a9de924d3eb246033.pt',
        'image_url': '/api/v1/buckets/models/objects/download?prefix=images/3e03ffae14114b29867b1dad357e9e23.png',
        'version': '1.0.0',
    },
    {
        'id': 7,
        'name': '火焰模型',
        'description': '识别火焰的模型',
        'model_path': '/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/df55c892173c4f3e96b3462e833f0e75.pt',
        'image_url': '/api/v1/buckets/models/objects/download?prefix=images/d81d3fe5476e4701a34b94e07cdc2820.png',
        'version': '1.0.0',
    },
    {
        'id': 8,
        'name': '吸烟模型',
        'description': '用于识别吸烟的模型',
        'model_path': '/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/baaab3e73fd74064ae42d57b0e170663.pt',
        'image_url': '/api/v1/buckets/models/objects/download?prefix=images/96e7070b3102445cb9f948849677d1ea.png',
        'version': '1.0.0',
    },
    {
        'id': 9,
        'name': '车牌模型',
        'description': '用于识别车牌的模型',
        'model_path': '/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/onnx/974487e51ee649b69bbdf691545976cd.onnx',
        'image_url': '/api/v1/buckets/models/objects/download?prefix=images/47e184f6949c4001b46e93a36259c750.png',
        'version': '1.0.0',
    },
    {
        'id': 10,
        'name': '打电话模型',
        'description': '用于识别打电话的模型',
        'model_path': '/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/onnx/6e25627aa8434831b4ddcee194b8be59.onnx',
        'image_url': '/api/v1/buckets/models/objects/download?prefix=images/ac4cdfd5ee5a4283a951d19cdf92e9e5.png',
        'version': '1.0.0',
    },
    {
        'id': 11,
        'name': '口罩模型',
        'description': '用于识别口罩的模型',
        'model_path': '/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/onnx/1c9a1e98bf114ffa990701292c41dd82.onnx',
        'image_url': '/api/v1/buckets/models/objects/download?prefix=images/fafd5c18743e41e2903dc9eaaa9d4722.png',
        'version': '1.0.0',
    },
    {
        'id': 12,
        'name': '道路积水模型',
        'description': '识别道路积水的模型',
        'model_path': '/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/onnx/f4e85385c70049efbf6bb748d2e2746f.onnx',
        'image_url': '/api/v1/buckets/models/objects/download?prefix=images/8153678ba3a346ae887a0a633e376217.png',
        'version': '1.0.0',
    },
    {
        'id': 13,
        'name': '跌倒检测模型',
        'description': '识别跌倒检测的模型',
        'model_path': '/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/onnx/f7bd3b98d1ea476c98761b57d42f73c4.onnx',
        'image_url': '/api/v1/buckets/models/objects/download?prefix=images/283c519096264729b82ac8f413ebf8a0.png',
        'version': '1.0.0',
    },
    {
        'id': 14,
        'name': '人脸检测模型',
        'description': '识别人脸的模型',
        'model_path': '/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/onnx/573ce175b4134208aa03d8bacfc76a4d.onnx',
        'image_url': '/api/v1/buckets/models/objects/download?prefix=images/77a9217ff3a048b1a1b672a105b18caf.png',
        'version': '1.0.0',
    },
]

_DEMO_NAMES = {item['name'] for item in _EDGE_DEMO_MODELS}
_DEMO_IDS = {item['id'] for item in _EDGE_DEMO_MODELS}


def _is_placeholder_row(row: AiModel) -> bool:
    name = (row.name or '').strip().lower()
    if name in {'edge-smoke-test', 'smoke-test', 'tmp', 'test'}:
        return True
    if name.startswith('edge-smoke') or name.startswith('tmp-'):
        return True
    return False


def _should_seed_metadata() -> bool:
    rows = AiModel.query.all()
    if not rows:
        return True
    # 仅占位/冒烟数据时允许覆盖初始化
    if all(_is_placeholder_row(r) for r in rows):
        return True
    # 已有真实用户模型则不覆盖；缺演示项时只补缺失 id
    return False


def _upsert_demo_models(*, replace_placeholders: bool) -> Tuple[int, int]:
    inserted = 0
    updated = 0
    now = datetime.utcnow()

    if replace_placeholders:
        for row in list(AiModel.query.all()):
            if _is_placeholder_row(row):
                db.session.delete(row)
        db.session.flush()

    existing_by_id = {m.id: m for m in AiModel.query.all()}
    existing_by_name = {m.name: m for m in AiModel.query.all()}

    for item in _EDGE_DEMO_MODELS:
        row = existing_by_id.get(item['id'])
        if row is None:
            conflict = existing_by_name.get(item['name'])
            if conflict is not None and conflict.id not in _DEMO_IDS:
                # 用户已用同名模型，跳过该演示项
                continue
            row = conflict

        payload = {
            'name': item['name'],
            'description': item.get('description'),
            'model_path': item.get('model_path'),
            'image_url': item.get('image_url'),
            'version': item.get('version') or '1.0.0',
            'status': 0,
            'class_names': item.get('class_names'),
            'selected_class_names': item.get('selected_class_names'),
            'onnx_model_path': item.get('onnx_model_path'),
            'torchscript_model_path': item.get('torchscript_model_path'),
            'tensorrt_model_path': item.get('tensorrt_model_path'),
            'openvino_model_path': item.get('openvino_model_path'),
            'model_origin': 'upload',
            'origin_ref': None,
            'updated_at': now,
        }

        if row is None:
            row = AiModel(id=item['id'], created_at=now, **payload)
            db.session.add(row)
            inserted += 1
        elif row.id in _DEMO_IDS or _is_placeholder_row(row) or row.name in _DEMO_NAMES:
            for key, value in payload.items():
                setattr(row, key, value)
            if row.id != item['id']:
                # 名称冲突但 id 不同：保留用户行，不强制改 id
                pass
            updated += 1

    db.session.commit()

    # 纠正序列，避免后续 create 撞演示 id
    try:
        db.session.execute(text(
            "SELECT setval(pg_get_serial_sequence('model', 'id'), "
            "GREATEST((SELECT COALESCE(MAX(id), 1) FROM model), 1))"
        ))
        db.session.commit()
    except Exception as exc:
        logger.debug('校正 model id 序列失败（可忽略）: %s', exc)
        db.session.rollback()

    return inserted, updated


def ensure_edge_model_seed() -> Dict[str, Any]:
    """edge 启动：同步本地种子文件 + 写入演示模型元数据。"""
    from app.utils.service_urls import is_edge_deploy_profile
    from app.services.local_storage_service import (
        get_minio_seed_data_root,
        migrate_seed_data_to_local_storage,
    )

    if not is_edge_deploy_profile():
        return {'skipped': True, 'reason': 'not-edge'}

    result: Dict[str, Any] = {'skipped': False}

    seed_root = get_minio_seed_data_root()
    copied, skipped = (0, 0)
    if seed_root:
        copied, skipped = migrate_seed_data_to_local_storage(
            buckets=['models'],
            skip_existing=True,
        )
        result['seed_root'] = seed_root
        result['files_copied'] = copied
        result['files_skipped'] = skipped
    else:
        result['seed_root'] = None
        logger.warning('edge 未找到模型种子目录，跳过权重/封面同步（元数据仍可初始化）')

    rows = AiModel.query.all()
    replace_placeholders = bool(rows) and all(_is_placeholder_row(r) for r in rows)
    need_full = (not rows) or replace_placeholders

    if need_full or any(AiModel.query.get(i) is None for i in _DEMO_IDS):
        inserted, updated = _upsert_demo_models(replace_placeholders=replace_placeholders or not rows)
        result['models_inserted'] = inserted
        result['models_updated'] = updated
    else:
        result['models_inserted'] = 0
        result['models_updated'] = 0

    return result
