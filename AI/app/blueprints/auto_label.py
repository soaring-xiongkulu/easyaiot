"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
自动化标注功能蓝图
"""
import os
import json
import logging
import tempfile
import zipfile
import threading
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from sqlalchemy import text

from db_models import db, AutoLabelTask, AutoLabelResult, AIService
from app.services.cluster_inference_service import ClusterInferenceService
from app.services.minio_service import ModelService

auto_label_bp = Blueprint('auto_label', __name__)
logger = logging.getLogger(__name__)


@auto_label_bp.route('/dataset/<int:dataset_id>/auto-label/start', methods=['POST'])
def start_auto_label(dataset_id):
    """启动自动化标注任务"""
    try:
        data = request.json or {}
        model_service_id = data.get('model_service_id')
        confidence_threshold = float(data.get('confidence_threshold', 0.5))
        
        if not model_service_id:
            return jsonify({'code': 400, 'msg': '请选择AI服务'}), 400
        
        # 验证AI服务是否存在
        ai_service = AIService.query.get(model_service_id)
        if not ai_service:
            return jsonify({'code': 404, 'msg': 'AI服务不存在'}), 404
        
        if ai_service.status != 'running':
            return jsonify({'code': 400, 'msg': 'AI服务未运行'}), 400
        
        # 创建标注任务
        task = AutoLabelTask(
            dataset_id=dataset_id,
            model_service_id=model_service_id,
            confidence_threshold=confidence_threshold,
            status='PENDING'
        )
        db.session.add(task)
        db.session.commit()
        
        # 异步执行标注任务
        thread = threading.Thread(target=execute_auto_label_task, args=(task.id,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'code': 0,
            'msg': '自动化标注任务已启动',
            'data': {
                'task_id': task.id
            }
        })
        
    except Exception as e:
        logger.error(f"启动自动化标注任务失败: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'启动任务失败: {str(e)}'}), 500


@auto_label_bp.route('/dataset/<int:dataset_id>/auto-label/task/<int:task_id>', methods=['GET'])
def get_auto_label_task(dataset_id, task_id):
    """获取自动化标注任务状态"""
    try:
        task = AutoLabelTask.query.filter_by(id=task_id, dataset_id=dataset_id).first()
        if not task:
            return jsonify({'code': 404, 'msg': '任务不存在'}), 404
        
        task_dict = task.to_dict()
        # 添加关联的AI服务信息
        if task.model_service:
            task_dict['model_service'] = task.model_service.to_dict()
        
        return jsonify({
            'code': 0,
            'msg': '获取成功',
            'data': task_dict
        })
        
    except Exception as e:
        logger.error(f"获取任务状态失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'获取失败: {str(e)}'}), 500


@auto_label_bp.route('/dataset/<int:dataset_id>/auto-label/tasks', methods=['GET'])
def list_auto_label_tasks(dataset_id):
    """获取数据集的所有自动化标注任务列表"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        
        tasks = AutoLabelTask.query.filter_by(dataset_id=dataset_id)\
            .order_by(AutoLabelTask.created_at.desc())\
            .paginate(page=page, per_page=page_size, error_out=False)
        
        # 构建任务列表，包含关联的AI服务信息
        task_list = []
        for task in tasks.items:
            task_dict = task.to_dict()
            if task.model_service:
                task_dict['model_service'] = task.model_service.to_dict()
            task_list.append(task_dict)
        
        return jsonify({
            'code': 0,
            'msg': '获取成功',
            'data': {
                'list': task_list,
                'total': tasks.total,
                'page': page,
                'page_size': page_size
            }
        })
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'获取失败: {str(e)}'}), 500


@auto_label_bp.route('/dataset/<int:dataset_id>/auto-label/export', methods=['POST'])
def export_labeled_dataset(dataset_id):
    """导出标注后的数据集为ZIP"""
    try:
        data = request.json or {}
        task_id = data.get('task_id')
        train_ratio = float(data.get('train_ratio', 0.7))
        val_ratio = float(data.get('val_ratio', 0.2))
        test_ratio = float(data.get('test_ratio', 0.1))
        export_format = data.get('format', 'yolo')  # yolo, coco, etc.
        
        # 验证比例
        if abs(train_ratio + val_ratio + test_ratio - 1.0) > 0.01:
            return jsonify({'code': 400, 'msg': '训练集、验证集、测试集比例之和必须为1'}), 400
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        zip_filename = f"dataset_{dataset_id}_{timestamp}.zip"
        zip_path = os.path.join(temp_dir, zip_filename)
        
        # 获取数据集图片和标注
        if task_id:
            # 从指定任务导出
            task = AutoLabelTask.query.filter_by(id=task_id, dataset_id=dataset_id).first()
            if not task:
                return jsonify({'code': 404, 'msg': '任务不存在'}), 404
            
            results = AutoLabelResult.query.filter_by(task_id=task_id, status='SUCCESS').all()
        else:
            # 导出所有已标注的图片
            results = AutoLabelResult.query.join(AutoLabelTask)\
                .filter(AutoLabelTask.dataset_id == dataset_id)\
                .filter(AutoLabelResult.status == 'SUCCESS')\
                .all()
        
        if not results:
            return jsonify({'code': 400, 'msg': '没有可导出的标注数据'}), 400
        
        # 创建ZIP文件
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if export_format == 'yolo':
                _export_yolo_format(zipf, dataset_id, results, train_ratio, val_ratio, test_ratio, temp_dir)
            else:
                return jsonify({'code': 400, 'msg': f'不支持的导出格式: {export_format}'}), 400
        
        # 返回文件
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=zip_filename,
            mimetype='application/zip'
        )
        
    except Exception as e:
        logger.error(f"导出数据集失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'导出失败: {str(e)}'}), 500


def execute_auto_label_task(task_id):
    """执行自动化标注任务（异步）"""
    task = None
    try:
        task = AutoLabelTask.query.get(task_id)
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return
        
        task.status = 'PROCESSING'
        task.started_at = datetime.now()
        db.session.commit()
        
        # 获取AI服务
        ai_service = AIService.query.get(task.model_service_id)
        if not ai_service:
            raise Exception('AI服务不存在')
        
        # 从Java后端获取数据集图片列表
        # 这里需要调用Java后端的API获取图片列表
        # 暂时使用直接查询数据库的方式（如果Python可以直接访问PostgreSQL）
        # 或者通过HTTP调用Java后端API
        
        # 模拟获取图片列表（实际应该从Java后端获取）
        # 这里假设通过HTTP调用Java后端API
        import requests
        from flask import current_app
        
        # 获取数据集图片列表
        # 注意：这里需要根据实际的后端API地址调整
        java_backend_url = os.getenv('JAVA_BACKEND_URL', 'http://localhost:8080')
        response = requests.get(
            f"{java_backend_url}/dataset/image/page",
            params={'dataset_id': task.dataset_id, 'page_size': 1000},
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f'获取图片列表失败: {response.text}')
        
        images_data = response.json()
        if images_data.get('code') != 0:
            raise Exception(f'获取图片列表失败: {images_data.get("msg")}')
        
        images = images_data.get('data', {}).get('list', [])
        task.total_images = len(images)
        db.session.commit()
        
        success_count = 0
        failed_count = 0
        
        # 处理每张图片
        for idx, image in enumerate(images):
            try:
                image_id = image.get('id')
                image_path = image.get('path')  # MinIO路径
                
                if not image_path:
                    logger.warning(f"图片 {image_id} 没有路径，跳过")
                    failed_count += 1
                    continue
                
                # 调用AI服务进行推理
                # 从MinIO下载图片到临时文件
                bucket_name, object_key = _parse_minio_path(image_path)
                if not bucket_name or not object_key:
                    logger.warning(f"无法解析图片路径: {image_path}")
                    failed_count += 1
                    continue
                
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                temp_file.close()
                
                success, error_msg = ModelService.download_from_minio(bucket_name, object_key, temp_file.name)
                if not success:
                    logger.error(f"下载图片失败: {error_msg}")
                    failed_count += 1
                    continue
                
                # 调用推理服务
                # 这里需要根据实际的推理服务接口调整
                # 假设使用cluster inference service
                result = ClusterInferenceService.inference_via_cluster(
                    model_id=ai_service.model_id,
                    model_format=ai_service.format or 'onnx',
                    model_version=ai_service.model_version or '1.0',
                    file_path=temp_file.name,
                    parameters={
                        'conf_thres': task.confidence_threshold,
                        'iou_thres': 0.45
                    }
                )
                
                # 解析推理结果并转换为标注格式
                annotations = _parse_inference_result(result, image.get('width'), image.get('heigh'))
                
                # 保存标注结果
                label_result = AutoLabelResult(
                    task_id=task_id,
                    dataset_image_id=image_id,
                    annotations=json.dumps(annotations, ensure_ascii=False),
                    status='SUCCESS'
                )
                db.session.add(label_result)
                
                # 更新Java后端的图片标注信息
                # 调用Java后端API更新annotations字段
                update_response = requests.put(
                    f"{java_backend_url}/dataset/image/update",
                    json={
                        'id': image_id,
                        'annotations': json.dumps(annotations, ensure_ascii=False)
                    },
                    timeout=10
                )
                
                if update_response.status_code != 200:
                    logger.warning(f"更新图片标注失败: {image_id}")
                
                success_count += 1
                
                # 清理临时文件
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                
            except Exception as e:
                logger.error(f"处理图片失败: {str(e)}", exc_info=True)
                failed_count += 1
                
                # 记录失败结果
                label_result = AutoLabelResult(
                    task_id=task_id,
                    dataset_image_id=image.get('id', 0),
                    status='FAILED',
                    error_message=str(e)
                )
                db.session.add(label_result)
            
            # 更新进度
            task.processed_images = idx + 1
            task.success_count = success_count
            task.failed_count = failed_count
            db.session.commit()
        
        # 完成任务
        task.status = 'COMPLETED'
        task.completed_at = datetime.now()
        db.session.commit()
        
        logger.info(f"自动化标注任务完成: task_id={task_id}, success={success_count}, failed={failed_count}")
        
    except Exception as e:
        logger.error(f"执行自动化标注任务失败: {str(e)}", exc_info=True)
        if task:
            task.status = 'FAILED'
            task.error_message = str(e)
            task.completed_at = datetime.now()
            db.session.commit()


def _parse_minio_path(path):
    """解析MinIO路径，返回bucket和object_key"""
    # 格式: /api/v1/buckets/{bucket}/objects/download?prefix={object_key}
    from urllib.parse import urlparse, parse_qs
    
    try:
        parsed = urlparse(path)
        path_parts = parsed.path.split('/')
        
        if len(path_parts) >= 5 and path_parts[3] == 'buckets':
            bucket_name = path_parts[4]
        else:
            return None, None
        
        query_params = parse_qs(parsed.query)
        object_key = query_params.get('prefix', [None])[0]
        
        return bucket_name, object_key
    except Exception as e:
        logger.error(f"解析MinIO路径失败: {path}, 错误: {str(e)}")
        return None, None


def _parse_inference_result(result, image_width, image_height):
    """解析推理结果，转换为标注格式"""
    annotations = []
    
    try:
        if not result or 'data' not in result:
            return annotations
        
        predictions = result.get('data', {}).get('predictions', [])
        
        for pred in predictions:
            # 根据实际推理结果格式解析
            # 假设格式: {'class': 'person', 'confidence': 0.95, 'bbox': [x1, y1, x2, y2]}
            class_name = pred.get('class', '')
            confidence = pred.get('confidence', 0)
            bbox = pred.get('bbox', [])
            
            if not class_name or not bbox or len(bbox) < 4:
                continue
            
            x1, y1, x2, y2 = bbox[:4]
            
            # 转换为多边形格式（矩形）
            annotation = {
                'class': class_name,
                'confidence': confidence,
                'points': [[x1, y1], [x2, y1], [x2, y2], [x1, y2]],
                'type': 'rectangle',
                'auto': True
            }
            annotations.append(annotation)
            
    except Exception as e:
        logger.error(f"解析推理结果失败: {str(e)}", exc_info=True)
    
    return annotations


def _export_yolo_format(zipf, dataset_id, results, train_ratio, val_ratio, test_ratio, temp_dir):
    """导出YOLO格式数据集"""
    import random
    import shutil
    from PIL import Image
    
    # 创建目录结构
    base_name = f"dataset_{dataset_id}"
    splits = ['train', 'val', 'test']
    for split in splits:
        zipf.writestr(f"{base_name}/{split}/images/.gitkeep", "")
        zipf.writestr(f"{base_name}/{split}/labels/.gitkeep", "")
    
    # 获取类别列表（从标注结果中提取）
    classes = set()
    for result in results:
        if result.annotations:
            anns = json.loads(result.annotations)
            for ann in anns:
                classes.add(ann.get('class', ''))
    
    classes = sorted(list(classes))
    class_to_id = {cls: idx for idx, cls in enumerate(classes)}
    
    # 创建data.yaml
    data_yaml = f"""path: .
train: train/images
val: val/images
test: test/images

nc: {len(classes)}
names: {classes}
"""
    zipf.writestr(f"{base_name}/data.yaml", data_yaml)
    
    # 随机分配数据集
    random.shuffle(results)
    total = len(results)
    train_end = int(total * train_ratio)
    val_end = train_end + int(total * val_ratio)
    
    train_results = results[:train_end]
    val_results = results[train_end:val_end]
    test_results = results[val_end:]
    
    # 处理每个分割
    for split_name, split_results in [('train', train_results), ('val', val_results), ('test', test_results)]:
        for result in split_results:
            try:
                # 从Java后端获取图片信息
                import requests
                java_backend_url = os.getenv('JAVA_BACKEND_URL', 'http://localhost:8080')
                image_response = requests.get(
                    f"{java_backend_url}/dataset/image/get",
                    params={'id': result.dataset_image_id},
                    timeout=10
                )
                
                if image_response.status_code != 200:
                    continue
                
                image_data = image_response.json()
                if image_data.get('code') != 0:
                    continue
                
                image_info = image_data.get('data', {})
                image_path = image_info.get('path')
                image_name = image_info.get('name', f"image_{result.dataset_image_id}.jpg")
                image_width = image_info.get('width', 0)
                image_height = image_info.get('heigh', 0)
                
                if not image_path or not image_width or not image_height:
                    continue
                
                # 下载图片
                bucket_name, object_key = _parse_minio_path(image_path)
                if not bucket_name or not object_key:
                    continue
                
                temp_image = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                temp_image.close()
                
                success, _ = ModelService.download_from_minio(bucket_name, object_key, temp_image.name)
                if not success:
                    continue
                
                # 添加图片到ZIP
                zipf.write(temp_image.name, f"{base_name}/{split_name}/images/{image_name}")
                
                # 生成YOLO格式标签
                annotations = json.loads(result.annotations) if result.annotations else []
                label_lines = []
                
                for ann in annotations:
                    class_name = ann.get('class', '')
                    if class_name not in class_to_id:
                        continue
                    
                    class_id = class_to_id[class_name]
                    points = ann.get('points', [])
                    
                    if len(points) >= 4:
                        # 计算边界框
                        xs = [p[0] for p in points]
                        ys = [p[1] for p in points]
                        x_min, x_max = min(xs), max(xs)
                        y_min, y_max = min(ys), max(ys)
                        
                        # 转换为YOLO格式（归一化）
                        center_x = ((x_min + x_max) / 2) / image_width
                        center_y = ((y_min + y_max) / 2) / image_height
                        width = (x_max - x_min) / image_width
                        height = (y_max - y_min) / image_height
                        
                        label_lines.append(f"{class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}")
                
                # 添加标签文件到ZIP
                label_name = os.path.splitext(image_name)[0] + '.txt'
                zipf.writestr(f"{base_name}/{split_name}/labels/{label_name}", '\n'.join(label_lines))
                
                # 清理临时文件
                if os.path.exists(temp_image.name):
                    os.unlink(temp_image.name)
                    
            except Exception as e:
                logger.error(f"导出图片失败: {str(e)}", exc_info=True)
                continue
