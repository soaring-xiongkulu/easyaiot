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

@model_bp.route('/model/<int:model_id>/publish', methods=['POST'])
def publish_model(model_id):
    """发布模型接口：从训练记录中选择模型并更新模型路径"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400

        training_record_id = data.get('training_record_id')
        if not training_record_id:
            return jsonify({'code': 400, 'msg': '缺少训练记录ID参数'}), 400

        # 获取模型和训练记录
        model = Model.query.get_or_404(model_id)
        training_record = TrainingRecord.query.get_or_404(training_record_id)

        # 验证训练记录属于该模型
        if training_record.model_id != model_id:
            return jsonify({'code': 400, 'msg': '训练记录不属于该模型'}), 400

        # 获取模型路径（优先使用Minio路径）
        model_path = training_record.minio_model_path or training_record.best_model_path
        if not model_path:
            return jsonify({'code': 400, 'msg': '训练记录中未找到有效模型路径'}), 400

        # 更新模型信息
        model.model_path = model_path
        model.training_record_id = training_record_id
        db.session.commit()

        # 记录发布日志
        logger.info(f"模型 {model_id} 已发布，使用训练记录 {training_record_id}，路径: {model_path}")

        return jsonify({
            'code': 200,
            'msg': '模型发布成功',
            'data': {
                'model_id': model_id,
                'model_name': model.name,
                'model_path': model_path,
                'training_record_id': training_record_id
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
