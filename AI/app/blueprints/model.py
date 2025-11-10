"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import os
import shutil
import uuid
from operator import or_
from flask import Blueprint, request, jsonify
from flask import redirect, url_for, flash, render_template
from app.services.minio_service import ModelService
from models import TrainTask
from models import db, Model
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
            'imageUrl': p.image_url
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
        if ModelService.upload_to_minio(bucket_name, object_key, temp_path):
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
    model = Model.query.get_or_404(model_id)
    model_name = model.name

    model_path = os.path.join('data/datasets', str(model_id))
    if os.path.exists(model_path):
        shutil.rmtree(model_path)

    db.session.delete(model)
    db.session.commit()

    flash(f'项目 "{model_name}" 已删除', 'success')
    return redirect(url_for('main.index'))


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