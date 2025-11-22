"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import os
import shutil
import uuid
import tempfile
from datetime import datetime
from operator import or_
from urllib.parse import urlparse, parse_qs
from flask import Blueprint, request, jsonify, send_file
from flask import redirect, url_for, flash, render_template
from app.services.minio_service import ModelService
from app.utils.yolo_validator import validate_yolo_model
from app.utils.image_utils import download_default_model_image
from db_models import TrainTask
from db_models import db, Model, InferenceTask
from sqlalchemy.exc import IntegrityError

model_bp = Blueprint('model', __name__)
logger = logging.getLogger(__name__)

@model_bp.route('/list', methods=['GET'])
def models():
    try:
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 10))
        search = request.args.get('search', '').strip()

        if page_no < 1 or page_size < 1:
            return jsonify({'code': 400, 'msg': '参数错误：pageNo和pageSize必须为正整数'}), 400

        query = Model.query
        if search:
            query = query.filter(
                or_(
                    Model.name.ilike(f'%{search}%'),
                    Model.description.ilike(f'%{search}%')
                )
            )

        pagination = query.paginate(
            page=page_no,
            per_page=page_size,
            error_out=False
        )

        model_list = [{
            'id': p.id,
            'name': p.name,
            'version': p.version,
            'description': p.description,
            'created_at': p.created_at.isoformat() if p.created_at else None,
            'updated_at': p.updated_at.isoformat() if p.updated_at else None,
            'imageUrl': p.image_url,
            'model_path': p.model_path,
            'onnx_model_path': p.onnx_model_path
        } for p in pagination.items]

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': model_list,
            'total': pagination.total
        })

    except ValueError:
        return jsonify({'code': 400, 'msg': '参数类型错误：pageNo和pageSize需为整数'}), 400
    except Exception as e:
        logger.error(f'分页查询失败: {str(e)}')
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500


@model_bp.route('/<int:model_id>/publish', methods=['POST'])
def publish_model(model_id):
    try:
        data = request.get_json()
        train_task_id = data.get('train_task_id')
        version = data.get('version', '1.0.0')

        if not train_task_id:
            return jsonify({'code': 400, 'msg': '缺少训练记录ID参数'}), 400

        model = Model.query.get_or_404(model_id)
        train_task = TrainTask.query.get_or_404(train_task_id)

        if train_task.model_id != model_id:
            return jsonify({'code': 400, 'msg': '训练记录不属于该模型'}), 400

        model_path = train_task.minio_model_path or train_task.best_model_path
        if not model_path:
            return jsonify({'code': 400, 'msg': '训练记录中未找到有效模型路径'}), 400

        # 检查模型名称+版本是否已存在（排除自身）
        existing_model = Model.query.filter(
            db.func.lower(Model.name) == db.func.lower(model.name),
            Model.version == version,
            Model.id != model_id
        ).first()

        if existing_model:
            return jsonify({
                'code': 400,
                'msg': f'模型"{model.name}"版本"{version}"已存在，请使用其他版本号'
            }), 400

        model.model_path = model_path
        model.train_task_id = train_task_id
        model.version = version
        db.session.commit()

        logger.info(f"模型 {model_id} 版本 {version} 已发布")
        return jsonify({
            'code': 0,
            'msg': '模型发布成功',
            'data': {
                'model_id': model_id,
                'version': version,
                'model_path': model_path
            }
        })

    except Exception as e:
        logger.error(f"发布模型失败: {str(e)}")
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@model_bp.route('/<int:model_id>/train_tasks', methods=['GET'])
def get_model_train_tasks(model_id):
    try:
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 10))

        query = TrainTask.query.filter_by(model_id=model_id)
        pagination = query.paginate(page=page_no, per_page=page_size, error_out=False)

        records = [{
            'id': record.id,
            'start_time': record.start_time.isoformat(),
            'end_time': record.end_time.isoformat() if record.end_time else None,
            'status': record.status,
            'minio_model_path': record.minio_model_path,
            'best_model_path': record.best_model_path
        } for record in pagination.items]

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': records,
            'total': pagination.total
        })

    except Exception as e:
        logger.error(f"获取训练记录失败: {str(e)}")
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500


@model_bp.route('/image_upload', methods=['POST'])
def upload_model_file():
    if 'file' not in request.files:
        return jsonify({'code': 400, 'msg': '未找到文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'msg': '未选择文件'}), 400

    # 初始化变量
    temp_path = None
    try:
        ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{ext}"

        # 创建临时目录和文件
        temp_dir = 'temp_uploads'
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, unique_filename)
        file.save(temp_path)

        bucket_name = 'models'
        object_key = f"images/{unique_filename}"

        # 上传到MinIO
        upload_success, upload_error = ModelService.upload_to_minio(bucket_name, object_key, temp_path)
        if upload_success:
            # 生成URL（直接拼接字符串）
            download_url = f"/api/v1/buckets/{bucket_name}/objects/download?prefix={object_key}"

            return jsonify({
                'code': 0,
                'msg': '文件上传成功',
                'data': {
                    'url': download_url,
                    'fileName': file.filename
                }
            })
        else:
            return jsonify({'code': 500, 'msg': '文件上传到MinIO失败'}), 500

    except Exception as e:
        logger.error(f"图片上传失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500

    finally:
        # 确保删除临时文件（无论上传成功与否）
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.info(f"临时文件已删除: {temp_path}")
            except OSError as e:
                logger.error(f"删除临时文件失败: {temp_path}, 错误: {str(e)}")


@model_bp.route('/upload', methods=['POST'])
def upload_custom_model():
    """
    上传用户自定义YOLO模型（支持yolov8和yolov11）
    
    请求参数:
    - file: 模型文件（.pt或.onnx格式，multipart/form-data）
    - name: 模型名称（可选，如果提供则保存到数据库）
    - description: 模型描述（可选）
    - version: 模型版本（可选，默认V1.0.0）
    - save_to_db: 是否保存到数据库（可选，默认false）
    """
    if 'file' not in request.files:
        return jsonify({'code': 400, 'msg': '未找到文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'msg': '未选择文件'}), 400

    # 检查文件扩展名
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.pt', '.onnx']:
        return jsonify({'code': 400, 'msg': '只支持.pt和.onnx格式的YOLO模型文件'}), 400

    # 获取可选参数
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    version = request.form.get('version', 'V1.0.0').strip()
    save_to_db = request.form.get('save_to_db', 'false').lower() == 'true'

    temp_path = None
    try:
        # 生成唯一文件名
        unique_filename = f"{uuid.uuid4().hex}{ext}"

        # 创建临时目录和文件
        temp_dir = 'temp_uploads'
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, unique_filename)
        file.save(temp_path)

        # 验证模型文件
        yolo_version = None
        detection_method = None
        
        if ext == '.onnx':
            # 验证ONNX模型
            try:
                from app.utils.onnx_validator import validate_onnx_model
                yolo_version, detection_method = validate_onnx_model(temp_path)
                if yolo_version is None:
                    return jsonify({
                        'code': 400,
                        'msg': '无法确定ONNX模型版本，请确保上传的是有效的YOLO ONNX模型文件'
                    }), 400
                
                if yolo_version not in ['yolov8', 'yolov11']:
                    return jsonify({
                        'code': 400,
                        'msg': f'不支持的YOLO版本: {yolo_version}，仅支持yolov8和yolov11'
                    }), 400
                
                logger.info(f"ONNX模型版本验证成功: {yolo_version} (检测方法: {detection_method})")
            except ImportError as e:
                return jsonify({
                    'code': 500,
                    'msg': f'ONNX模型验证失败: {str(e)}'
                }), 500
            except Exception as e:
                error_msg = str(e)
                logger.error(f"ONNX模型验证失败: {error_msg}")
                return jsonify({
                    'code': 400,
                    'msg': f'ONNX模型验证失败: {error_msg}'
                }), 400
        else:
            # 验证YOLO模型版本（必须是yolov8或yolov11）
            try:
                yolo_version, detection_method = validate_yolo_model(temp_path)
                if yolo_version is None:
                    return jsonify({
                        'code': 400,
                        'msg': '无法确定模型版本，请确保上传的是有效的YOLO模型文件'
                    }), 400
                
                if yolo_version not in ['yolov8', 'yolov11']:
                    return jsonify({
                        'code': 400,
                        'msg': f'不支持的YOLO版本: {yolo_version}，仅支持yolov8和yolov11'
                    }), 400
                
                logger.info(f"模型版本验证成功: {yolo_version} (检测方法: {detection_method})")
            except ImportError as e:
                return jsonify({
                    'code': 500,
                    'msg': f'模型验证失败: {str(e)}'
                }), 500
            except Exception as e:
                error_msg = str(e)
                logger.error(f"模型验证失败: {error_msg}")
                
                # 检查是否是YOLOv5或其他不兼容模型的明确错误
                if '检测到YOLOv5模型' in error_msg or '检测到YOLOv' in error_msg:
                    # 直接返回明确的错误信息（已经包含了详细的说明）
                    return jsonify({
                        'code': 400,
                        'msg': error_msg
                    }), 400
                else:
                    # 其他错误，返回通用错误信息
                    return jsonify({
                        'code': 400,
                        'msg': f'模型验证失败: {error_msg}'
                    }), 400

        # 上传到MinIO
        bucket_name = 'models'
        # 根据文件类型选择不同的存储路径
        if ext == '.onnx':
            object_key = f"yolo/{yolo_version}/onnx/{unique_filename}"
        else:
            object_key = f"yolo/{yolo_version}/{unique_filename}"

        upload_success, upload_error = ModelService.upload_to_minio(bucket_name, object_key, temp_path)
        if not upload_success:
            error_msg = upload_error or '文件上传到MinIO失败'
            return jsonify({'code': 500, 'msg': error_msg}), 500

        # 生成下载URL
        download_url = f"/api/v1/buckets/{bucket_name}/objects/download?prefix={object_key}"
        minio_path = f"{bucket_name}/{object_key}"

        response_data = {
            'code': 0,
            'msg': '模型上传成功',
            'data': {
                'url': download_url,
                'minio_path': minio_path,
                'fileName': file.filename,
                'yolo_version': yolo_version,
                'detection_method': detection_method,
                'model_format': 'onnx' if ext == '.onnx' else 'pt'
            }
        }

        # 如果指定保存到数据库，则创建模型记录
        if save_to_db:
            # 设置默认名称（如果未提供）
            if not name:
                # 基于文件名生成默认名称，去除扩展名
                base_name = os.path.splitext(file.filename)[0]
                if not base_name:
                    base_name = "custom_model"
                # 添加时间戳确保唯一性
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name = f"{base_name}_{timestamp}"
                logger.info(f"使用默认模型名称: {name}")

            # 设置默认描述（如果未提供）
            if not description:
                description = f"用户上传的{yolo_version.upper()}自定义模型"
                logger.info(f"使用默认模型描述: {description}")

            # 处理默认图片（如果未提供imageUrl）
            image_url = request.form.get('imageUrl', '').strip()
            default_image_path = None
            
            if not image_url:
                try:
                    # 下载默认图片到临时目录
                    temp_dir = 'temp_uploads'
                    os.makedirs(temp_dir, exist_ok=True)
                    default_image_filename = f"default_model_{uuid.uuid4().hex}.png"
                    default_image_path = os.path.join(temp_dir, default_image_filename)
                    
                    if download_default_model_image(default_image_path):
                        # 上传默认图片到MinIO
                        bucket_name = 'models'
                        image_object_key = f"images/{default_image_filename}"
                        
                        upload_success, upload_error = ModelService.upload_to_minio(bucket_name, image_object_key, default_image_path)
                        if upload_success:
                            image_url = f"/api/v1/buckets/{bucket_name}/objects/download?prefix={image_object_key}"
                            logger.info(f"默认图片已上传: {image_url}")
                        else:
                            logger.warning("默认图片上传到MinIO失败，继续使用空图片URL")
                            image_url = None
                    else:
                        logger.warning("默认图片下载失败，继续使用空图片URL")
                        image_url = None
                except Exception as e:
                    logger.error(f"处理默认图片失败: {str(e)}")
                    image_url = None
                finally:
                    # 清理临时图片文件
                    if default_image_path and os.path.exists(default_image_path):
                        try:
                            os.remove(default_image_path)
                        except OSError as e:
                            logger.warning(f"删除临时图片文件失败: {str(e)}")

            # 检查模型名称+版本是否已存在
            existing_model = Model.query.filter(
                db.func.lower(Model.name) == db.func.lower(name),
                Model.version == version
            ).first()

            if existing_model:
                return jsonify({
                    'code': 400,
                    'msg': f'模型"{name}"版本"{version}"已存在，请使用其他名称或版本号'
                }), 400

            try:
                # 创建模型记录，保存MinIO下载URL到model_path字段
                model = Model(
                    name=name,
                    description=description,
                    model_path=download_url if ext != '.onnx' else None,  # PT模型保存到model_path
                    onnx_model_path=download_url if ext == '.onnx' else None,  # ONNX模型保存到onnx_model_path
                    version=version,
                    image_url=image_url if image_url else None
                )
                db.session.add(model)
                db.session.commit()

                response_data['data']['model_id'] = model.id
                response_data['data']['model_name'] = model.name
                response_data['data']['model_version'] = model.version
                response_data['data']['model_description'] = model.description
                response_data['data']['image_url'] = model.image_url
                logger.info(f"模型已保存到数据库: {model.id} - {model.name}")
            except IntegrityError as e:
                db.session.rollback()
                logger.error(f"模型名称冲突: {str(e)}")
                return jsonify({
                    'code': 400,
                    'msg': f'模型名称"{name}"版本"{version}"已存在，请使用其他名称或版本号'
                }), 400
            except Exception as e:
                db.session.rollback()
                logger.error(f"保存模型到数据库失败: {str(e)}")
                # 即使数据库保存失败，文件已上传成功，返回警告信息
                response_data['msg'] = f'模型上传成功，但保存到数据库失败: {str(e)}'
                response_data['code'] = 201  # 部分成功

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"模型上传失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500

    finally:
        # 确保删除临时文件（无论上传成功与否）
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.info(f"临时文件已删除: {temp_path}")
            except OSError as e:
                logger.error(f"删除临时文件失败: {temp_path}, 错误: {str(e)}")


@model_bp.route('/create', methods=['POST'])
def create_model():
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        file_path = data.get('filePath', '')
        image_url = data.get('imageUrl', '')
        version = data.get('version', 'V1.0.0')

        if not name:
            return jsonify({'code': 400, 'msg': '模型名称不能为空'}), 400

        # 检查模型名称+版本是否已存在
        existing_model = Model.query.filter(
            db.func.lower(Model.name) == db.func.lower(name),
            Model.version == version
        ).first()

        if existing_model:
            return jsonify({
                'code': 400,
                'msg': f'模型"{name}"版本"{version}"已存在，请使用其他名称或版本号'
            }), 400

        # 创建模型记录
        model = Model(
            name=name,
            description=description,
            model_path=file_path,
            image_url=image_url,
            version=version
        )
        db.session.add(model)
        db.session.commit()

        return jsonify({
            'code': 0,
            'msg': '模型创建成功',
            'data': {
                'id': model.id,
                'name': model.name,
                'version': model.version,
                'filePath': model.model_path,
                'imageUrl': model.image_url
            }
        })

    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"模型名称冲突: {str(e)}")
        return jsonify({
            'code': 400,
            'msg': f'模型名称"{name}"版本"{version}"已存在，请使用其他名称或版本号'
        }), 400

    except Exception as e:
        db.session.rollback()
        logger.error(f"创建模型失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


@model_bp.route('/<int:model_id>/update', methods=['PUT'])
def update_model(model_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400

        model = Model.query.get_or_404(model_id)
        new_name = data.get('name', model.name)
        new_version = data.get('version', model.version)

        # 检查模型名称+版本是否已存在（排除自身）
        if new_name != model.name or new_version != model.version:
            existing_model = Model.query.filter(
                db.func.lower(Model.name) == db.func.lower(new_name),
                Model.version == new_version,
                Model.id != model_id
            ).first()

            if existing_model:
                return jsonify({
                    'code': 400,
                    'msg': f'模型"{new_name}"版本"{new_version}"已存在，请使用其他名称或版本号'
                }), 400

        # 更新允许的字段
        if 'name' in data:
            model.name = data['name']
        if 'version' in data:
            model.version = data['version']
        if 'description' in data:
            model.description = data['description']
        if 'filePath' in data:
            model.model_path = data['filePath']
        if 'imageUrl' in data:
            model.image_url = data['imageUrl']

        db.session.commit()

        return jsonify({
            'code': 0,
            'msg': '模型更新成功',
            'data': {
                'id': model.id,
                'name': model.name,
                'version': model.version,
                'filePath': model.model_path,
                'imageUrl': model.image_url
            }
        })

    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"模型名称冲突: {str(e)}")
        return jsonify({
            'code': 400,
            'msg': f'模型名称"{new_name}"版本"{new_version}"已存在，请使用其他名称或版本号'
        }), 400

    except Exception as e:
        db.session.rollback()
        logger.error(f"更新模型失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


@model_bp.route('/<int:model_id>/delete', methods=['POST'])
def delete_model(model_id):
    try:
        model = Model.query.get_or_404(model_id)
        model_name = model.name

        # 自动删除相关的推理任务记录
        inference_tasks = InferenceTask.query.filter_by(model_id=model_id).all()
        inference_tasks_count = len(inference_tasks)
        if inference_tasks_count > 0:
            for task in inference_tasks:
                db.session.delete(task)
            logger.info(f"已自动删除 {inference_tasks_count} 个关联的推理任务")

        # 检查是否有相关的训练任务记录
        train_tasks_count = TrainTask.query.filter_by(model_id=model_id).count()
        if train_tasks_count > 0:
            return jsonify({
                'code': 400,
                'msg': f'无法删除模型"{model_name}"，该模型正在被{train_tasks_count}个训练任务使用。请先删除相关的训练任务后再试。'
            }), 400

        # 删除本地数据集目录（如果存在）
        model_path = os.path.join('data/datasets', str(model_id))
        if os.path.exists(model_path):
            try:
                shutil.rmtree(model_path)
                logger.info(f"已删除模型数据集目录: {model_path}")
            except Exception as e:
                logger.warning(f"删除模型数据集目录失败: {model_path}, 错误: {str(e)}")

        # 删除数据库记录
        db.session.delete(model)
        db.session.commit()

        # 构建成功消息
        success_msg = f'模型"{model_name}"已成功删除'
        if inference_tasks_count > 0:
            success_msg += f'，并已自动删除 {inference_tasks_count} 个关联的推理任务'

        logger.info(f"模型已删除: {model_id} - {model_name}，关联推理任务数: {inference_tasks_count}")
        return jsonify({
            'code': 0,
            'msg': success_msg
        })

    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"删除模型失败（外键约束）: {str(e)}")
        return jsonify({
            'code': 400,
            'msg': f'无法删除模型，该模型正在被其他记录使用。请先删除相关的关联记录后再试。'
        }), 400

    except Exception as e:
        db.session.rollback()
        logger.error(f"删除模型失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


@model_bp.route('/ota_check', methods=['GET'])
def ota_check():
    try:
        model_name = request.args.get('model_name', '')
        current_version = request.args.get('version', '1.0.0')
        device_type = request.args.get('device_type', 'cpu')

        if not model_name:
            return jsonify({'code': 400, 'msg': '缺少必要参数：model_name'}), 400

        latest_model = Model.query.filter(
            Model.name == model_name,
            Model.version > current_version
        ).order_by(Model.created_at.desc()).first()

        if not latest_model:
            return jsonify({
                'code': 0,
                'msg': '当前已是最新版本',
                'has_update': False
            })

        model_path = select_model_format(latest_model, device_type)
        if not model_path:
            return jsonify({'code': 404, 'msg': '未找到适合该设备的模型格式'}), 404

        return jsonify({
            'code': 0,
            'msg': '发现新版本',
            'has_update': True,
            'update_info': {
                'model_id': latest_model.id,
                'model_name': latest_model.name,
                'new_version': latest_model.version,
                'release_date': latest_model.created_at.isoformat(),
                'model_path': model_path,
                'change_log': f"模型升级到版本 {latest_model.version}",
                'file_size': get_model_size(model_path)
            }
        })

    except Exception as e:
        logger.error(f"OTA检查失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


def select_model_format(model, device_type):
    if device_type == 'gpu' and model.tensorrt_model_path:
        return model.tensorrt_model_path
    if model.onnx_model_path:
        return model.onnx_model_path
    return model.model_path


def get_model_size(model_path):
    return {
        'bytes': 1024000,
        'human_readable': '1.02 MB'
    }


def parse_minio_url(url: str):
    """
    解析MinIO下载URL，提取bucket和object_key
    格式: /api/v1/buckets/{bucket_name}/objects/download?prefix={object_key}
    """
    try:
        parsed = urlparse(url)
        path_parts = parsed.path.split('/')
        
        # 提取bucket名称
        if len(path_parts) >= 5 and path_parts[3] == 'buckets':
            bucket_name = path_parts[4]
        else:
            return None, None
        
        # 提取object_key
        query_params = parse_qs(parsed.query)
        object_key = query_params.get('prefix', [None])[0]
        
        return bucket_name, object_key
    except Exception as e:
        logger.error(f"解析MinIO URL失败: {url}, 错误: {str(e)}")
        return None, None


@model_bp.route('/<int:model_id>/download', methods=['GET'])
def download_model(model_id):
    """下载模型文件"""
    try:
        model = Model.query.get_or_404(model_id)
        
        # 优先使用 model_path，如果没有则使用 onnx_model_path
        model_path = model.model_path or model.onnx_model_path
        
        # 如果模型表中没有路径，尝试从TrainTask中获取最新的已完成训练的模型路径
        if not model_path:
            train_task = TrainTask.query.filter_by(
                model_id=model_id,
                status='completed'
            ).order_by(TrainTask.end_time.desc()).first()
            
            if train_task and train_task.minio_model_path:
                model_path = train_task.minio_model_path
                logger.info(f"从训练任务中获取模型路径: {model_path}")
        
        if not model_path:
            return jsonify({
                'code': 404,
                'msg': '该模型没有可下载的文件'
            }), 404

        # 解析MinIO URL
        bucket_name, object_key = parse_minio_url(model_path)
        
        if not bucket_name or not object_key:
            # 如果不是MinIO URL格式，尝试直接使用路径
            # 假设格式为 bucket_name/object_key
            if '/' in model_path:
                parts = model_path.split('/', 1)
                bucket_name = parts[0]
                object_key = parts[1]
            else:
                return jsonify({
                    'code': 400,
                    'msg': '无法解析模型文件路径'
                }), 400

        # 创建临时文件
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pt')
        tmp_file.close()

        # 从MinIO下载
        success, error_msg = ModelService.download_from_minio(bucket_name, object_key, tmp_file.name)
        if not success:
            return jsonify({
                'code': 404 if error_msg and '不存在' in error_msg else 500,
                'msg': error_msg or '从MinIO下载文件失败'
            }), 404 if error_msg and '不存在' in error_msg else 500

        # 确定文件扩展名
        file_ext = '.onnx' if model.onnx_model_path and not model.model_path else '.pt'
        download_name = f"{model.name}_{model.version or 'v1.0.0'}{file_ext}"

        # 发送文件
        return send_file(
            tmp_file.name,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/octet-stream'
        )

    except Exception as e:
        logger.error(f"下载模型失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500