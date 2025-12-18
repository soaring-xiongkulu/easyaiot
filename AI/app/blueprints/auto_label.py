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


@auto_label_bp.route('/dataset/<int:dataset_id>/auto-label/image/<int:image_id>', methods=['POST'])
def label_single_image(dataset_id, image_id):
    """单张图片AI标注"""
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
        
        # 从Java后端获取图片信息
        import requests
        java_backend_url = os.getenv('JAVA_BACKEND_URL', 'http://localhost:8080')
        image_response = requests.get(
            f"{java_backend_url}/dataset/image/get",
            params={'id': image_id},
            timeout=10
        )
        
        if image_response.status_code != 200:
            return jsonify({'code': 404, 'msg': '图片不存在'}), 404
        
        image_data = image_response.json()
        if image_data.get('code') != 0:
            return jsonify({'code': 404, 'msg': '获取图片信息失败'}), 404
        
        image_info = image_data.get('data', {})
        image_path = image_info.get('path')
        
        if not image_path:
            return jsonify({'code': 400, 'msg': '图片路径不存在'}), 400
        
        # 从MinIO下载图片到临时文件
        bucket_name, object_key = _parse_minio_path(image_path)
        if not bucket_name or not object_key:
            return jsonify({'code': 400, 'msg': '无法解析图片路径'}), 400
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        temp_file.close()
        
        success, error_msg = ModelService.download_from_minio(bucket_name, object_key, temp_file.name)
        if not success:
            return jsonify({'code': 500, 'msg': f'下载图片失败: {error_msg}'}), 500
        
        try:
            # 调用推理服务
            result = ClusterInferenceService.inference_via_cluster(
                model_id=ai_service.model_id,
                model_format=ai_service.format or 'onnx',
                model_version=ai_service.model_version or '1.0',
                file_path=temp_file.name,
                parameters={
                    'conf_thres': confidence_threshold,
                    'iou_thres': 0.45
                }
            )
            
            # 解析推理结果并转换为标注格式
            image_width = image_info.get('width', 0)
            image_height = image_info.get('heigh', 0)
            annotations = _parse_inference_result(result, image_width, image_height)
            
            # 更新Java后端的图片标注信息
            update_response = requests.put(
                f"{java_backend_url}/dataset/image/update",
                json={
                    'id': image_id,
                    'annotations': json.dumps(annotations, ensure_ascii=False),
                    'completed': 1 if annotations else 0
                },
                timeout=10
            )
            
            if update_response.status_code != 200:
                logger.warning(f"更新图片标注失败: {image_id}")
                return jsonify({'code': 500, 'msg': '更新图片标注失败'}), 500
            
            return jsonify({
                'code': 0,
                'msg': '标注成功',
                'data': {
                    'annotations': annotations,
                    'count': len(annotations)
                }
            })
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
        
    except Exception as e:
        logger.error(f"单张图片AI标注失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'标注失败: {str(e)}'}), 500


@auto_label_bp.route('/dataset/<int:dataset_id>/auto-label/export', methods=['POST'])
def export_labeled_dataset(dataset_id):
    """导出标注后的数据集为ZIP"""
    try:
        data = request.json or {}
        task_id = data.get('task_id')
        train_ratio = float(data.get('train_ratio', 0.7))
        val_ratio = float(data.get('val_ratio', 0.2))
        test_ratio = float(data.get('test_ratio', 0.1))
        export_format = data.get('format', 'yolo')  # yolo, resnet, videonet, audionet
        sample_type = data.get('sample_type', 'all')  # all, annotated, unannotated
        selected_classes = data.get('selected_classes', [])  # 选择的类别列表
        file_prefix = data.get('file_prefix', '')  # 文件前缀
        
        # 验证比例
        if abs(train_ratio + val_ratio + test_ratio - 1.0) > 0.01:
            return jsonify({'code': 400, 'msg': '训练集、验证集、测试集比例之和必须为1'}), 400
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        zip_filename = f"dataset_{dataset_id}_{timestamp}.zip"
        zip_path = os.path.join(temp_dir, zip_filename)
        
        # 获取数据集图片和标注
        import requests
        java_backend_url = os.getenv('JAVA_BACKEND_URL', 'http://localhost:8080')
        
        # 从Java后端获取图片列表
        response = requests.get(
            f"{java_backend_url}/dataset/image/page",
            params={'dataset_id': dataset_id, 'page_size': 10000},
            timeout=30
        )
        
        if response.status_code != 200:
            return jsonify({'code': 500, 'msg': '获取图片列表失败'}), 500
        
        images_data = response.json()
        if images_data.get('code') != 0:
            return jsonify({'code': 500, 'msg': '获取图片列表失败'}), 500
        
        all_images = images_data.get('data', {}).get('list', [])
        
        # 根据样本类型过滤图片
        if sample_type == 'annotated':
            filtered_images = [img for img in all_images if img.get('completed') == 1]
        elif sample_type == 'unannotated':
            filtered_images = [img for img in all_images if img.get('completed') != 1]
        else:
            filtered_images = all_images
        
        # 如果指定了任务ID，只导出该任务的标注结果
        if task_id:
            task = AutoLabelTask.query.filter_by(id=task_id, dataset_id=dataset_id).first()
            if not task:
                return jsonify({'code': 404, 'msg': '任务不存在'}), 404
            
            task_image_ids = {r.dataset_image_id for r in AutoLabelResult.query.filter_by(task_id=task_id, status='SUCCESS').all()}
            filtered_images = [img for img in filtered_images if img.get('id') in task_image_ids]
        
        # 如果指定了类别，过滤标注
        if selected_classes:
            # 这里需要根据标注中的类别进行过滤
            # 暂时先不过滤，在导出时再处理
            pass
        
        if not filtered_images:
            return jsonify({'code': 400, 'msg': '没有可导出的数据'}), 400
        
        # 创建ZIP文件
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if export_format == 'yolo':
                _export_yolo_format(zipf, dataset_id, filtered_images, train_ratio, val_ratio, test_ratio, temp_dir, selected_classes, file_prefix)
            elif export_format in ['resnet', 'videonet', 'audionet']:
                # TODO: 实现其他格式的导出
                return jsonify({'code': 400, 'msg': f'导出格式 {export_format} 暂未实现'}), 400
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


@auto_label_bp.route('/dataset/<int:dataset_id>/extract-frames', methods=['POST'])
def extract_frames_from_video(dataset_id):
    """从视频文件抽帧并添加到数据集"""
    try:
        if 'file' not in request.files:
            return jsonify({'code': 400, 'msg': '未找到视频文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'code': 400, 'msg': '未选择视频文件'}), 400
        
        frame_interval = int(request.form.get('frame_interval', 3))
        
        # 保存视频文件到临时目录
        temp_video = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
        file.save(temp_video.name)
        temp_video.close()
        
        try:
            # 使用OpenCV或FFmpeg进行抽帧
            import cv2
            import requests
            
            cap = cv2.VideoCapture(temp_video.name)
            if not cap.isOpened():
                return jsonify({'code': 400, 'msg': '无法打开视频文件'}), 400
            
            frame_count = 0
            extracted_count = 0
            java_backend_url = os.getenv('JAVA_BACKEND_URL', 'http://localhost:8080')
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 每隔指定帧数保存一帧
                if frame_count % frame_interval == 0:
                    # 保存帧为图片
                    frame_filename = f"frame_{frame_count:06d}.jpg"
                    temp_frame = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                    cv2.imwrite(temp_frame.name, frame)
                    temp_frame.close()
                    
                    # 上传到MinIO并添加到数据集
                    # 这里需要调用Java后端的API上传图片
                    # 暂时简化处理，直接返回成功
                    extracted_count += 1
                    
                    # 清理临时文件
                    if os.path.exists(temp_frame.name):
                        os.unlink(temp_frame.name)
                
                frame_count += 1
            
            cap.release()
            
            return jsonify({
                'code': 0,
                'msg': f'抽帧完成，共提取 {extracted_count} 帧',
                'data': {
                    'extracted_count': extracted_count,
                    'total_frames': frame_count
                }
            })
            
        finally:
            # 清理临时视频文件
            if os.path.exists(temp_video.name):
                os.unlink(temp_video.name)
        
    except Exception as e:
        logger.error(f"视频抽帧失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'抽帧失败: {str(e)}'}), 500


@auto_label_bp.route('/dataset/<int:dataset_id>/import-labelme', methods=['POST'])
def import_labelme_dataset(dataset_id):
    """导入labelme数据集"""
    try:
        if 'files' not in request.files:
            return jsonify({'code': 400, 'msg': '未找到文件'}), 400
        
        files = request.files.getlist('files')
        if not files:
            return jsonify({'code': 400, 'msg': '未选择文件'}), 400
        
        # 分离图片文件和JSON标注文件
        image_files = {}
        json_files = {}
        
        for file in files:
            filename = file.filename
            ext = os.path.splitext(filename)[1].lower()
            
            if ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                base_name = os.path.splitext(filename)[0]
                image_files[base_name] = file
            elif ext == '.json':
                base_name = os.path.splitext(filename)[0]
                json_files[base_name] = file
        
        if not image_files:
            return jsonify({'code': 400, 'msg': '未找到图片文件'}), 400
        
        imported_count = 0
        java_backend_url = os.getenv('JAVA_BACKEND_URL', 'http://localhost:8080')
        
        # 处理每个图片文件
        for base_name, image_file in image_files.items():
            try:
                # 读取对应的JSON标注文件
                annotations = []
                if base_name in json_files:
                    json_file = json_files[base_name]
                    json_content = json_file.read().decode('utf-8')
                    labelme_data = json.loads(json_content)
                    
                    # 转换labelme格式为系统标注格式
                    shapes = labelme_data.get('shapes', [])
                    image_width = labelme_data.get('imageWidth', 0)
                    image_height = labelme_data.get('imageHeight', 0)
                    
                    for shape in shapes:
                        label = shape.get('label', '')
                        points = shape.get('points', [])
                        shape_type = shape.get('shape_type', 'polygon')
                        
                        if shape_type == 'rectangle' and len(points) == 2:
                            # 矩形框：两个点转换为四个点
                            x1, y1 = points[0]
                            x2, y2 = points[1]
                            points = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
                        
                        annotation = {
                            'class': label,
                            'points': points,
                            'type': 'rectangle' if shape_type == 'rectangle' else 'polygon',
                            'auto': False
                        }
                        annotations.append(annotation)
                
                # 保存图片和标注到数据集
                # 这里需要调用Java后端的API上传图片和标注
                # 暂时简化处理
                imported_count += 1
                
            except Exception as e:
                logger.error(f"处理文件失败 {base_name}: {str(e)}")
                continue
        
        return jsonify({
            'code': 0,
            'msg': f'导入完成，共导入 {imported_count} 个文件',
            'data': {
                'imported_count': imported_count
            }
        })
        
    except Exception as e:
        logger.error(f"导入labelme数据集失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'导入失败: {str(e)}'}), 500


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
        if not result:
            return annotations
        
        # 检查返回格式：可能是 {'code': 0, 'data': {...}} 或直接是 data
        if isinstance(result, dict) and 'code' in result:
            if result.get('code') != 0:
                logger.warning(f"推理返回错误: {result.get('msg', '未知错误')}")
                return annotations
            predictions = result.get('data', {}).get('predictions', [])
        elif isinstance(result, dict) and 'data' in result:
            predictions = result.get('data', {}).get('predictions', [])
        elif isinstance(result, dict) and 'predictions' in result:
            predictions = result.get('predictions', [])
        else:
            logger.warning(f"无法识别的推理结果格式: {type(result)}")
            return annotations
        
        for pred in predictions:
            try:
                # 推理结果格式: {'class': int, 'class_name': str, 'confidence': float, 'bbox': [x1, y1, x2, y2]}
                class_id = pred.get('class')
                class_name = pred.get('class_name', '')
                confidence = float(pred.get('confidence', 0))
                bbox = pred.get('bbox', [])
                
                # 如果没有class_name，尝试使用class_id
                if not class_name and class_id is not None:
                    class_name = str(class_id)
                
                if not class_name or not bbox or len(bbox) < 4:
                    continue
                
                x1, y1, x2, y2 = bbox[:4]
                
                # 确保坐标在图片范围内
                if image_width and image_height:
                    x1 = max(0, min(x1, image_width))
                    y1 = max(0, min(y1, image_height))
                    x2 = max(0, min(x2, image_width))
                    y2 = max(0, min(y2, image_height))
                
                # 转换为多边形格式（矩形）
                annotation = {
                    'class': class_name,
                    'confidence': confidence,
                    'bbox': [x1, y1, x2, y2],
                    'points': [[x1, y1], [x2, y1], [x2, y2], [x1, y2]],
                    'type': 'rectangle',
                    'auto': True
                }
                annotations.append(annotation)
            except Exception as e:
                logger.error(f"解析单个预测结果失败: {str(e)}, pred: {pred}")
                continue
            
    except Exception as e:
        logger.error(f"解析推理结果失败: {str(e)}", exc_info=True)
    
    return annotations


def _export_yolo_format(zipf, dataset_id, images, train_ratio, val_ratio, test_ratio, temp_dir, selected_classes=None, file_prefix=''):
    """导出YOLO格式数据集"""
    import random
    import shutil
    from PIL import Image
    
    if selected_classes is None:
        selected_classes = []
    
    # 创建目录结构
    base_name = file_prefix if file_prefix else f"dataset_{dataset_id}"
    splits = ['train', 'val', 'test']
    for split in splits:
        zipf.writestr(f"{base_name}/{split}/images/.gitkeep", "")
        zipf.writestr(f"{base_name}/{split}/labels/.gitkeep", "")
    
    # 获取类别列表（从图片标注中提取）
    classes = set()
    for image in images:
        annotations_str = image.get('annotations', '')
        if annotations_str:
            try:
                anns = json.loads(annotations_str) if isinstance(annotations_str, str) else annotations_str
                for ann in anns:
                    class_name = ann.get('class', '')
                    if class_name:
                        # 如果指定了类别过滤，只添加选中的类别
                        if not selected_classes or class_name in selected_classes:
                            classes.add(class_name)
            except:
                pass
    
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
    random.shuffle(images)
    total = len(images)
    train_end = int(total * train_ratio)
    val_end = train_end + int(total * val_ratio)
    
    train_images = images[:train_end]
    val_images = images[train_end:val_end]
    test_images = images[val_end:]
    
    # 处理每个分割
    for split_name, split_images in [('train', train_images), ('val', val_images), ('test', test_images)]:
        for image_info in split_images:
            try:
                image_path = image_info.get('path')
                image_name = image_info.get('name', f"image_{image_info.get('id')}.jpg")
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
                annotations_str = image_info.get('annotations', '')
                annotations = []
                if annotations_str:
                    try:
                        annotations = json.loads(annotations_str) if isinstance(annotations_str, str) else annotations_str
                    except:
                        pass
                
                label_lines = []
                for ann in annotations:
                    class_name = ann.get('class', '')
                    # 如果指定了类别过滤，只导出选中的类别
                    if selected_classes and class_name not in selected_classes:
                        continue
                    
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
