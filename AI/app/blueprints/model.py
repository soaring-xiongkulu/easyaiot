import logging
import os
import shutil
import uuid
from operator import or_
from flask import Blueprint, request, jsonify
from flask import redirect, url_for, flash, render_template
from app.services.model_service import ModelService
from models import TrainingRecord
from models import db, Model

model_bp = Blueprint('model', __name__)

logger = logging.getLogger(__name__)

@model_bp.route('/list', methods=['GET'])
def models():
    # 适配 pageNo 和 pageSize 参数
    try:
        page_no = int(request.args.get('pageNo', 1))  # 默认第1页
        page_size = int(request.args.get('pageSize', 10))  # 默认每页10条
        search = request.args.get('search', '').strip()

        # 参数校验
        if page_no < 1 or page_size < 1:
            return jsonify({
                'code': 400,
                'msg': '参数错误：pageNo和pageSize必须为正整数'
            }), 400

        # 构建查询（支持搜索）
        query = Model.query
        if search:
            query = query.filter(
                or_(
                    Model.name.ilike(f'%{search}%'),
                    Model.description.ilike(f'%{search}%')
                )
            )

        # 执行分页查询
        pagination = query.paginate(
            page=page_no,
            per_page=page_size,
            error_out=False
        )

        # 构建响应
        model_list = [{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'created_at': p.created_at.isoformat() if p.created_at else None
        } for p in pagination.items]

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': model_list,
            'pagination': {
                'pageNo': pagination.page,  # 当前页码
                'pageSize': pagination.per_page,  # 每页数量
                'totalItems': pagination.total,  # 总记录数
                'totalPages': pagination.pages  # 总页数
            }
        })

    except ValueError:  # 参数类型错误
        return jsonify({
            'code': 400,
            'msg': '参数类型错误：pageNo和pageSize需为整数'
        }), 400

    except Exception as e:
        logger.error(f'分页查询失败: {str(e)}')
        return jsonify({
            'code': 500,
            'msg': '服务器内部错误'
        }), 500


@model_bp.route('/<int:model_id>/publish', methods=['POST'])
def publish_model(model_id):
    try:
        data = request.get_json()
        training_record_id = data.get('training_record_id')
        version = data.get('version', '1.0.0')  # 获取版本号

        if not training_record_id:
            return jsonify({'code': 400, 'msg': '缺少训练记录ID参数'}), 400

        model = Model.query.get_or_404(model_id)
        training_record = TrainingRecord.query.get_or_404(training_record_id)

        if training_record.model_id != model_id:
            return jsonify({'code': 400, 'msg': '训练记录不属于该模型'}), 400

        model_path = training_record.minio_model_path or training_record.best_model_path
        if not model_path:
            return jsonify({'code': 400, 'msg': '训练记录中未找到有效模型路径'}), 400

        # 更新模型信息和版本号
        model.model_path = model_path
        model.training_record_id = training_record_id
        model.version = version  # 设置新版本号
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
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


@model_bp.route('/<int:model_id>/training_records', methods=['GET'])
def get_model_training_records(model_id):
    """获取模型关联的训练记录"""
    try:
        # 分页参数
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 10))

        # 查询训练记录
        query = TrainingRecord.query.filter_by(model_id=model_id)
        pagination = query.paginate(page=page_no, per_page=page_size, error_out=False)

        # 构建响应数据
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
            'pagination': {
                'pageNo': pagination.page,
                'pageSize': pagination.per_page,
                'totalItems': pagination.total,
                'totalPages': pagination.pages
            }
        })

    except Exception as e:
        logger.error(f"获取训练记录失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': '服务器内部错误'
        }), 500


@model_bp.route('/<int:model_id>')
def model_detail(model_id):
    model = Model.query.get_or_404(model_id)
    return render_template('model_detail.html', model=model)


# 新增模型文件上传接口
@model_bp.route('/upload', methods=['POST'])
def upload_model_file():
    if 'file' not in request.files:
        return jsonify({'code': 400, 'msg': '未找到文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'msg': '未选择文件'}), 400

    try:
        # 生成唯一文件名
        ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{ext}"

        # 临时保存文件
        temp_dir = 'temp_uploads'
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, unique_filename)
        file.save(temp_path)

        # 上传到Minio
        bucket_name = 'models'  # Minio存储桶名称
        object_key = f"models/{unique_filename}"

        if ModelService.upload_to_minio(bucket_name, object_key, temp_path):
            # 清理临时文件
            os.remove(temp_path)
            return jsonify({
                'code': 0,
                'msg': '文件上传成功',
                'data': {
                    'objectKey': object_key,
                    'fileName': file.filename
                }
            })
        else:
            return jsonify({'code': 500, 'msg': '文件上传到Minio失败'}), 500

    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


# 修改创建模型接口
@model_bp.route('/create', methods=['POST'])
def create_model():
    try:
        # 获取JSON数据
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400

        name = data.get('name')
        description = data.get('description', '')
        file_path = data.get('filePath', '')  # 获取Minio objectKey

        if not name:
            return jsonify({'code': 400, 'msg': '模型名称不能为空'}), 400

        # 创建模型记录
        model = Model(name=name, description=description, model_path=file_path)
        db.session.add(model)
        db.session.commit()

        return jsonify({
            'code': 0,
            'msg': '模型创建成功',
            'data': {
                'id': model.id,
                'name': model.name,
                'filePath': model.model_path
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


# 修改更新模型接口
@model_bp.route('/<int:model_id>/update', methods=['PUT'])
def update_model(model_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400

        model = Model.query.get_or_404(model_id)

        # 更新允许的字段
        if 'name' in data:
            model.name = data['name']
        if 'description' in data:
            model.description = data['description']
        if 'filePath' in data:  # 更新Minio objectKey
            model.model_path = data['filePath']

        db.session.commit()

        return jsonify({
            'code': 0,
            'msg': '模型更新成功',
            'data': {
                'id': model.id,
                'name': model.name,
                'filePath': model.model_path
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


@model_bp.route('/<int:model_id>/delete', methods=['POST'])
def delete_model(model_id):
    model = Model.query.get_or_404(model_id)
    model_name = model.name

    # 删除项目相关的所有文件
    model_path = os.path.join('data/datasets', str(model_id))
    if os.path.exists(model_path):
        shutil.rmtree(model_path)

    # 删除项目记录
    db.session.delete(model)
    db.session.commit()

    flash(f'项目 "{model_name}" 已删除', 'success')
    return redirect(url_for('main.index'))


@model_bp.route('/ota_check', methods=['GET'])
def ota_check():
    """模型OTA升级检测接口"""
    try:
        # 获取请求参数
        model_name = request.args.get('model_name', '')
        current_version = request.args.get('version', '1.0.0')
        device_type = request.args.get('device_type', 'cpu')  # 设备类型：cpu/gpu/npu

        if not model_name:
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数：model_name'
            }), 400

        # 查询最新版本的模型
        latest_model = Model.query.filter(
            Model.name == model_name,
            Model.version > current_version  # 版本号大于当前版本
        ).order_by(Model.created_at.desc()).first()

        if not latest_model:
            return jsonify({
                'code': 0,
                'msg': '当前已是最新版本',
                'has_update': False
            })

        # 根据设备类型选择模型格式
        model_path = select_model_format(latest_model, device_type)
        if not model_path:
            return jsonify({
                'code': 404,
                'msg': '未找到适合该设备的模型格式'
            }), 404

        # 返回升级信息
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
                'file_size': get_model_size(model_path)  # 获取模型文件大小
            }
        })

    except Exception as e:
        logger.error(f"OTA检查失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


def select_model_format(model, device_type):
    """根据设备类型选择最优模型格式"""
    # NPU设备优先使用RKNN格式
    if device_type == 'npu' and model.rknn_model_path:
        return model.rknn_model_path

    # GPU设备优先使用TensorRT格式
    if device_type == 'gpu' and model.tensorrt_model_path:
        return model.tensorrt_model_path

    # 通用设备使用ONNX格式
    if model.onnx_model_path:
        return model.onnx_model_path

    # 回退到原始模型
    return model.model_path


def get_model_size(model_path):
    """获取模型文件大小（模拟实现）"""
    # 实际项目中应从Minio获取文件元数据
    return {
        'bytes': 1024000,  # 文件字节数
        'human_readable': '1.02 MB'
    }
