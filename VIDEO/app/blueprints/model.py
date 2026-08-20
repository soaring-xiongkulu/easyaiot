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
import json
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from flask import Blueprint, request, jsonify, send_file
from flask import redirect, url_for, flash, render_template
from sqlalchemy import or_
from app.services.minio_service import ModelService
from app.utils.yolo_validator import validate_yolo_model
from app.utils.image_utils import download_default_model_image
from app.utils.model_class_utils import (
    dump_class_names_json,
    extract_class_names_from_model,
    parse_class_names_json,
)
from models import db, AiModel as Model
from sqlalchemy.exc import IntegrityError

model_bp = Blueprint('model', __name__)
logger = logging.getLogger(__name__)

_DEFAULT_MODEL_VERSION = '1.0.0'


def _normalize_model_version(version) -> str:
    """去掉版本号前导 v/V，统一存储为纯语义版本（如 1.0.0）。"""
    text = str(version or '').strip()
    if text.lower().startswith('v'):
        text = text[1:].lstrip()
    return text or _DEFAULT_MODEL_VERSION


def _serialize_model_class_fields(model: Model) -> dict:
    class_names = parse_class_names_json(model.class_names)
    selected_class_names = parse_class_names_json(model.selected_class_names)
    if not selected_class_names and class_names:
        selected_class_names = list(class_names)
    return {
        'class_names': class_names,
        'classNames': class_names,
        'selected_class_names': selected_class_names,
        'selectedClassNames': selected_class_names,
    }


def _serialize_model_provenance(model: Model) -> dict:
    return {
        'model_origin': getattr(model, 'model_origin', None) or 'upload',
        'origin_ref': getattr(model, 'origin_ref', None),
    }


def _serialize_model_item(model: Model) -> dict:
    return {
        'id': model.id,
        'name': model.name,
        'version': model.version,
        'description': model.description,
        'status': model.status if model.status is not None else 0,
        'created_at': model.created_at.isoformat() if model.created_at else None,
        'updated_at': model.updated_at.isoformat() if model.updated_at else None,
        'imageUrl': model.image_url,
        'model_path': model.model_path,
        'onnx_model_path': model.onnx_model_path,
        'torchscript_model_path': model.torchscript_model_path,
        'tensorrt_model_path': model.tensorrt_model_path,
        'openvino_model_path': model.openvino_model_path,
        **_serialize_model_class_fields(model),
        **_serialize_model_provenance(model),
    }


def _apply_model_provenance(model: Model, origin: str | None, origin_ref: str | None = None):
    if origin:
        model.model_origin = origin
    if origin_ref:
        model.origin_ref = origin_ref


def _apply_model_class_fields(model: Model, data: dict):
    class_names = data.get('classNames')
    if class_names is None:
        class_names = data.get('class_names')
    selected_class_names = data.get('selectedClassNames')
    if selected_class_names is None:
        selected_class_names = data.get('selected_class_names')

    if class_names is not None:
        parsed = parse_class_names_json(class_names)
        model.class_names = dump_class_names_json(parsed)
    if selected_class_names is not None:
        parsed_selected = parse_class_names_json(selected_class_names)
        model.selected_class_names = dump_class_names_json(parsed_selected)

@model_bp.route('/list', methods=['GET'])
def models():
    try:
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 10))
        search = request.args.get('search', '').strip()
        name = request.args.get('name', '').strip()
        version = request.args.get('version', '').strip()
        if version.lower().startswith('v'):
            version = version[1:].lstrip()

        if page_no < 1 or page_size < 1:
            return jsonify({'code': 400, 'msg': '参数错误：pageNo和pageSize必须为正整数'}), 400

        query = Model.query
        if name:
            query = query.filter(Model.name.ilike(f'%{name}%'))
        if version:
            query = query.filter(Model.version.ilike(f'%{version}%'))
        if search:
            query = query.filter(
                or_(
                    Model.name.ilike(f'%{search}%'),
                    Model.description.ilike(f'%{search}%')
                )
            )
        status_q = request.args.get('status', '').strip()
        if status_q != '':
            try:
                query = query.filter(Model.status == int(status_q))
            except ValueError:
                pass

        has_weights = request.args.get('has_weights', '').strip().lower()
        if has_weights in ('true', '1', 'yes', 'on'):
            query = query.filter(
                or_(
                    Model.model_path.isnot(None),
                    Model.onnx_model_path.isnot(None),
                    Model.torchscript_model_path.isnot(None),
                    Model.tensorrt_model_path.isnot(None),
                    Model.openvino_model_path.isnot(None),
                )
            )

        pagination = query.order_by(Model.created_at.desc()).paginate(
            page=page_no,
            per_page=page_size,
            error_out=False
        )

        model_list = [_serialize_model_item(p) for p in pagination.items]

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
    上传用户自定义YOLO模型（支持 yolov8、yolov11 和 yolov26）
    
    请求参数:
    - file: 模型文件（.pt或.onnx格式，multipart/form-data）
    - name: 模型名称（可选，如果提供则保存到数据库）
    - description: 模型描述（可选）
    - version: 模型版本（可选，默认1.0.0）
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
    version = _normalize_model_version(request.form.get('version', _DEFAULT_MODEL_VERSION))
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
                
                if yolo_version not in ['yolov8', 'yolov11', 'yolov26']:
                    return jsonify({
                        'code': 400,
                        'msg': f'不支持的YOLO版本: {yolo_version}，仅支持 yolov8、yolov11 和 yolov26'
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
            # 验证YOLO模型版本（必须是 yolov8、yolov11 或 yolov26）
            try:
                yolo_version, detection_method = validate_yolo_model(
                    temp_path,
                    original_filename=file.filename,
                )
                if yolo_version is None:
                    return jsonify({
                        'code': 400,
                        'msg': '无法确定模型版本，请确保上传的是有效的YOLO模型文件'
                    }), 400
                
                if yolo_version not in ['yolov8', 'yolov11', 'yolov26']:
                    return jsonify({
                        'code': 400,
                        'msg': f'不支持的YOLO版本: {yolo_version}，仅支持 yolov8、yolov11 和 yolov26'
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
                if (
                    '检测到YOLOv5' in error_msg
                    or 'models.yolo' in error_msg
                    or '检测到YOLOv' in error_msg
                ):
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

        # 提取模型类别标签
        class_names = extract_class_names_from_model(temp_path)
        selected_class_names = request.form.get('selectedClassNames') or request.form.get('selected_class_names')
        if selected_class_names:
            parsed_selected = parse_class_names_json(selected_class_names)
            if parsed_selected:
                selected_class_names_list = parsed_selected
            else:
                selected_class_names_list = class_names
        else:
            selected_class_names_list = class_names

        response_data = {
            'code': 0,
            'msg': '模型上传成功',
            'data': {
                'url': download_url,
                'minio_path': minio_path,
                'fileName': file.filename,
                'yolo_version': yolo_version,
                'detection_method': detection_method,
                'model_format': 'onnx' if ext == '.onnx' else 'pt',
                'class_names': class_names,
                'classNames': class_names,
                'selected_class_names': selected_class_names_list,
                'selectedClassNames': selected_class_names_list,
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
                    image_url=image_url if image_url else None,
                    class_names=dump_class_names_json(class_names),
                    selected_class_names=dump_class_names_json(selected_class_names_list),
                )
                _apply_model_provenance(model, 'upload')
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
        version = _normalize_model_version(data.get('version', _DEFAULT_MODEL_VERSION))
        status = 0
        if data.get('status') is not None:
            try:
                st = int(data['status'])
                if st in (0, 1, 2, 3):
                    status = st
            except (TypeError, ValueError):
                pass

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
            version=version,
            status=status
        )
        _apply_model_class_fields(model, data)
        origin = (data.get('model_origin') or data.get('modelOrigin') or 'upload').strip() or 'upload'
        origin_ref = data.get('origin_ref') or data.get('originRef')
        _apply_model_provenance(model, origin, origin_ref)
        db.session.add(model)
        db.session.commit()

        return jsonify({
            'code': 0,
            'msg': '模型创建成功',
            'data': {
                'id': model.id,
                'name': model.name,
                'version': model.version,
                'status': getattr(model, 'status', 0) or 0,
                'filePath': model.model_path,
                'imageUrl': model.image_url,
                **_serialize_model_class_fields(model),
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
        new_version = _normalize_model_version(data.get('version', model.version))

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
            model.version = _normalize_model_version(data['version'])
        if 'description' in data:
            model.description = data['description']
        if 'filePath' in data:
            model.model_path = data['filePath']
        if 'imageUrl' in data:
            model.image_url = data['imageUrl']
        if 'status' in data and data['status'] is not None:
            try:
                st = int(data['status'])
                if st in (0, 1, 2, 3):
                    model.status = st
            except (TypeError, ValueError):
                pass

        _apply_model_class_fields(model, data)

        db.session.commit()

        return jsonify({
            'code': 0,
            'msg': '模型更新成功',
            'data': {
                'id': model.id,
                'name': model.name,
                'version': model.version,
                'status': getattr(model, 'status', 0) or 0,
                'filePath': model.model_path,
                'imageUrl': model.image_url,
                **_serialize_model_class_fields(model),
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

        inference_tasks_count = 0

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


def resolve_minio_bucket_key(path: str):
    """
    将模型存储路径解析为 MinIO bucket 与 object_key。
    支持 API 下载 URL 与 bucket/object 相对路径（如 exports/model_3/onnx/model.onnx）。
    """
    if not path or not str(path).strip():
        return None, None
    path = str(path).strip()
    bucket_name, object_key = parse_minio_url(path)
    if bucket_name and object_key:
        return bucket_name, object_key
    if '/' in path:
        parts = path.split('/', 1)
        return parts[0], parts[1]
    return None, None


def _iter_model_storage_paths(model: Model):
    """按优先级返回可用于解析类别的模型文件路径（优先 .pt 权重）。"""
    seen = set()
    for path in (model.model_path, model.onnx_model_path):
        if path and path not in seen:
            seen.add(path)
            yield path


@model_bp.route('/<int:model_id>/download', methods=['GET'])
def download_model(model_id):
    """下载模型文件"""
    try:
        model = Model.query.get_or_404(model_id)
        
        # 优先使用 model_path，如果没有则使用 onnx_model_path
        model_path = model.model_path or model.onnx_model_path
        
        if not model_path:
            return jsonify({
                'code': 404,
                'msg': '该模型没有可下载的文件'
            }), 404

        bucket_name, object_key = resolve_minio_bucket_key(model_path)
        if not bucket_name or not object_key:
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
        download_name = f"{model.name}_{model.version or _DEFAULT_MODEL_VERSION}{file_ext}"

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

# 解析并返回模型识别标签（已有模型可补全 class_names）
@model_bp.route('/<int:model_id>/classes', methods=['GET'])
def get_model_classes(model_id):
    temp_path = None
    try:
        model = Model.query.get_or_404(model_id)
        stored_names = parse_class_names_json(model.class_names)
        if stored_names:
            selected = parse_class_names_json(model.selected_class_names) or stored_names
            return jsonify({
                'code': 0,
                'msg': 'success',
                'data': {
                    'class_names': stored_names,
                    'classNames': stored_names,
                    'selected_class_names': selected,
                    'selectedClassNames': selected,
                }
            })

        candidate_paths = list(_iter_model_storage_paths(model))
        if not candidate_paths:
            return jsonify({'code': 404, 'msg': '该模型没有可解析的模型文件'}), 404

        class_names = []
        last_error = '无法解析模型文件路径'
        for model_path in candidate_paths:
            bucket_name, object_key = resolve_minio_bucket_key(model_path)
            if not bucket_name or not object_key:
                last_error = f'无法解析模型文件路径: {model_path}'
                continue

            ext = os.path.splitext(object_key)[1] or '.pt'
            temp_fd, temp_path = tempfile.mkstemp(suffix=ext)
            os.close(temp_fd)
            try:
                success, error_msg = ModelService.download_from_minio(bucket_name, object_key, temp_path)
                if not success:
                    last_error = error_msg or '下载模型文件失败'
                    continue
                class_names = extract_class_names_from_model(temp_path)
                if class_names:
                    break
            finally:
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass
                temp_path = None

        if not class_names:
            return jsonify({'code': 404, 'msg': last_error or '未能从模型文件中提取检测类别'}), 404

        selected = parse_class_names_json(model.selected_class_names) or class_names
        model.class_names = dump_class_names_json(class_names)
        if not model.selected_class_names:
            model.selected_class_names = dump_class_names_json(class_names)
        db.session.commit()

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'class_names': class_names,
                'classNames': class_names,
                'selected_class_names': selected if selected else class_names,
                'selectedClassNames': selected if selected else class_names,
            }
        })
    except Exception as e:
        logger.error(f"获取模型标签失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


# 根据模型id 获取模型信息
@model_bp.route('/<int:model_id>', methods=['GET'])
def get_model(model_id):
    try:
        model = Model.query.get_or_404(model_id)
        model_name = model.name
        return jsonify({
            'code': 0,
            'msg': '获取模型成功:'+model_name,
            'data': {
                'id': model.id,
                'name': model_name,
                'version': model.version,
                'status': getattr(model, 'status', 0) or 0,
                'model_path': model.model_path,
                'onnx_model_path': model.onnx_model_path,
                'torchscript_model_path': model.torchscript_model_path,
                'tensorrt_model_path': model.tensorrt_model_path,
                'openvino_model_path': model.openvino_model_path,
                **_serialize_model_class_fields(model),
                **_serialize_model_provenance(model),
            },
            'has_update': False
        })
    except Exception as e:
        logger.error(f"获取模型失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


@model_bp.route('/<int:model_id>/sync-to-cluster', methods=['POST'])
def sync_model_to_cluster(model_id):
    """将模型权重预同步至集群 CephFS（AI_MODELS_DIR/{model_id}/）。"""
    try:
        model = Model.query.get(model_id)
        if not model:
            return jsonify({'code': 404, 'msg': f'模型 {model_id} 不存在'}), 404

        from model_resolver import (
            is_cluster_synced,
            model_record_from_orm,
            resolve_cluster_model_path,
            sync_model_weights_to_cluster,
        )

        def _minio_download(bucket: str, key: str, dest: str):
            return ModelService.download_from_minio(bucket, key, dest)

        record = model_record_from_orm(model)
        if is_cluster_synced(model_id):
            path = resolve_cluster_model_path(model_id)
            return jsonify({
                'code': 0,
                'msg': '模型已在集群缓存',
                'data': {'model_id': model_id, 'cluster_path': path, 'synced': True},
            })

        ok, msg, path = sync_model_weights_to_cluster(
            model_id, record, download_fn=_minio_download,
        )
        if not ok:
            return jsonify({'code': 500, 'msg': msg}), 500
        return jsonify({
            'code': 0,
            'msg': msg,
            'data': {'model_id': model_id, 'cluster_path': path, 'synced': True},
        })
    except Exception as e:
        logger.error('集群模型同步失败 model_id=%s: %s', model_id, e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'同步失败: {e}'}), 500


@model_bp.route('/sync-to-cluster/batch', methods=['POST'])
def sync_models_to_cluster_batch():
    """批量预同步模型至集群共享存储。"""
    try:
        data = request.get_json(silent=True) or {}
        raw_ids = data.get('model_ids') or data.get('modelIds') or []
        if not raw_ids:
            return jsonify({'code': 400, 'msg': '请提供 model_ids'}), 400

        from model_resolver import ensure_models_on_cluster, model_record_from_orm

        def _fetch(mid: int):
            m = Model.query.get(mid)
            return model_record_from_orm(m) if m else None

        def _minio_download(bucket: str, key: str, dest: str):
            return ModelService.download_from_minio(bucket, key, dest)

        ok, errors = ensure_models_on_cluster(raw_ids, _fetch, download_fn=_minio_download)
        if not ok:
            return jsonify({'code': 500, 'msg': '; '.join(errors), 'data': {'errors': errors}}), 500
        return jsonify({'code': 0, 'msg': '全部模型已同步', 'data': {'model_ids': raw_ids}})
    except Exception as e:
        logger.error('批量集群模型同步失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'同步失败: {e}'}), 500


# 在模型推理时进行模型下载
@model_bp.route('/download_model_forVideo', methods=['POST'])
def download_model_forVideo():
    try:
        data = request.get_json()
        bucket_name = data.get('bucket_name')
        object_key = data.get('object_key')
        destination_path = data.get('destination_path')
        # ① 参数校验（逻辑修正）
        if not bucket_name or not object_key or not destination_path:
            logger.warning("缺少必要参数")
            return jsonify({
                'code': 400,
                'msg': '请传递必要的参数'
            }), 400
        # ② 执行下载
        success, error_msg = ModelService.download_from_minio(
            bucket_name, object_key, destination_path
        )
        if not success:
            raise Exception(f"从MinIO下载文件失败: {bucket_name}/{object_key}. {error_msg or ''}")
        # ③ 正确返回成功状态
        return jsonify({
            'code': 0,
            'msg': f'模型下载成功，请在 {destination_path} 查看'
        }), 200
    except Exception as e:
        logger.error(f"在模型推理时进行模型下载失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500
