from flask import Blueprint

import logging
import os
import shutil
from operator import or_
from flask import request, jsonify, redirect, url_for, flash, render_template
from models import db, Model, TrainingRecord

model_bp = Blueprint('model', __name__)

logger = logging.getLogger(__name__)

@model_bp.route('/models', methods=['GET'])
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
            'code': 200,
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


@model_bp.route('/api/model/<int:model_id>/publish', methods=['POST'])
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
            'code': 200,
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


@model_bp.route('/model/<int:model_id>/training_records', methods=['GET'])
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
            'code': 200,
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

@model_bp.route('/model/<int:model_id>')
def model_detail(model_id):
    model = Model.query.get_or_404(model_id)
    return render_template('model_detail.html', model=model)

@model_bp.route('/model/create', methods=['POST'])
def create_model():
    name = request.form.get('name')
    description = request.form.get('description')

    if not name:
        flash('项目名称不能为空', 'error')
        return redirect(url_for('main.index'))

    model = Model(name=name, description=description)
    db.session.add(model)
    db.session.commit()

    flash(f'项目 "{name}" 创建成功', 'success')
    return redirect(url_for('main.model_detail', model_id=model.id))

@model_bp.route('/api/model/<int:model_id>/update', methods=['PUT'])
def update_model(model_id):
    """更新模型信息接口"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400

        # 获取模型记录
        model = Model.query.get_or_404(model_id)

        # 允许更新的字段列表
        allowed_fields = ['name', 'description', 'version']

        # 更新允许的字段
        for field in allowed_fields:
            if field in data:
                setattr(model, field, data[field])

        # 处理特殊字段更新
        if 'training_record_id' in data:
            # 验证训练记录是否存在且属于该模型
            training_record = TrainingRecord.query.get(data['training_record_id'])
            if training_record and training_record.model_id == model_id:
                model.training_record_id = training_record.id
                model.model_path = training_record.minio_model_path or training_record.best_model_path
            else:
                return jsonify({
                    'code': 400,
                    'msg': '无效的训练记录ID或记录不属于该模型'
                }), 400

        # 保存更改
        db.session.commit()

        # 返回更新后的模型信息
        updated_model = {
            'id': model.id,
            'name': model.name,
            'description': model.description,
            'version': model.version,
            'training_record_id': model.training_record_id,
            'model_path': model.model_path
        }

        return jsonify({
            'code': 200,
            'msg': '模型更新成功',
            'data': updated_model
        })

    except Exception as e:
        logger.error(f"模型更新失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500

@model_bp.route('/model/<int:model_id>/delete', methods=['POST'])
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


@model_bp.route('/api/model/ota_check', methods=['GET'])
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
                'code': 200,
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
            'code': 200,
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