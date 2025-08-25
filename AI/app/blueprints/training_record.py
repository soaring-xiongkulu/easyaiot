import logging
import os
import shutil
from datetime import datetime

from flask import Blueprint, request, jsonify
from flask import render_template
from sqlalchemy import desc

from models import db, Model, TrainingRecord, ExportRecord

training_record_bp = Blueprint('training_record', __name__, url_prefix='/training')
logger = logging.getLogger(__name__)


# 训练记录分页查询
@training_record_bp.route('/list', methods=['GET'])
def training_records():
    try:
        # 获取分页参数和模型ID过滤
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 10))
        model_id = request.args.get('model_id')
        status_filter = request.args.get('status')

        # 参数验证
        if page_no < 1 or page_size < 1:
            return jsonify({
                'code': 400,
                'msg': '参数错误：pageNo和pageSize必须为正整数'
            }), 400

        # 构建基础查询
        query = TrainingRecord.query

        # 应用模型ID过滤
        if model_id:
            query = query.filter(TrainingRecord.model_id == model_id)

        # 应用状态过滤
        if status_filter in ['running', 'completed', 'failed']:
            query = query.filter(TrainingRecord.status == status_filter)

        # 按开始时间倒序排列
        query = query.order_by(desc(TrainingRecord.start_time))

        # 执行分页
        pagination = query.paginate(
            page=page_no,
            per_page=page_size,
            error_out=False
        )

        # 构建响应数据
        records = []
        for record in pagination.items:
            records.append({
                'id': record.id,
                'model_id': record.model_id,
                'model_name': record.model.name if record.model else '',
                'dataset_path': record.dataset_path,
                'start_time': record.start_time.isoformat() if record.start_time else None,
                'end_time': record.end_time.isoformat() if record.end_time else None,
                'status': record.status,
                'metrics': record.metrics_path
            })

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': records,
            'total': pagination.total
        })

    except ValueError:
        return jsonify({
            'code': 400,
            'msg': '参数类型错误：pageNo和pageSize需为整数'
        }), 400
    except Exception as e:
        logger.error(f'训练记录查询失败: {str(e)}')
        return jsonify({
            'code': 500,
            'msg': '服务器内部错误'
        }), 500


# 训练记录详情
@training_record_bp.route('/<int:record_id>')
def training_detail(record_id):
    record = TrainingRecord.query.get_or_404(record_id)
    exports = ExportRecord.query.filter_by(model_id=record.model_id).all()

    return render_template('training_detail.html',
                           record=record,
                           exports=exports)


# 创建训练记录
@training_record_bp.route('/create', methods=['POST'])
def create_training():
    try:
        data = request.json
        model_id = data.get('model_id')
        dataset_path = data.get('dataset_path')

        # 参数验证
        if not model_id or not dataset_path:
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数：model_id 和 dataset_path'
            }), 400

        # 检查模型是否存在
        model = Model.query.get(model_id)
        if not model:
            return jsonify({
                'code': 404,
                'msg': '指定模型不存在'
            }), 404

        # 创建训练记录
        new_record = TrainingRecord(
            model_id=model_id,
            dataset_path=dataset_path,
            hyperparameters=data.get('hyperparameters', '{}'),
            status='running',
            train_log=f"logs/training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            checkpoint_dir=f"checkpoints/training_{datetime.now().strftime('%Y%m%d_%H%M%S')}/"
        )

        db.session.add(new_record)
        db.session.commit()

        # 创建日志和检查点目录
        os.makedirs(os.path.dirname(new_record.train_log), exist_ok=True)
        os.makedirs(new_record.checkpoint_dir, exist_ok=True)

        return jsonify({
            'code': 201,
            'msg': '训练记录创建成功',
            'data': {
                'record_id': new_record.id,
                'log_path': new_record.train_log,
                'checkpoint_dir': new_record.checkpoint_dir
            }
        })

    except Exception as e:
        logger.error(f'创建训练记录失败: {str(e)}')
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': '服务器内部错误'
        }), 500


# 更新训练记录状态
@training_record_bp.route('/update/<int:record_id>', methods=['POST'])
def update_training(record_id):
    try:
        record = TrainingRecord.query.get_or_404(record_id)
        data = request.json

        # 更新训练记录字段
        if 'status' in data:
            record.status = data['status']

        if 'metrics' in data:
            # 保存指标到文件
            metrics_path = f"metrics/training_{record_id}.json"
            os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
            with open(metrics_path, 'w') as f:
                f.write(data['metrics'])
            record.metrics_path = metrics_path

        if 'end_time' in data:
            record.end_time = datetime.fromisoformat(data['end_time'])

        if 'hyperparameters' in data:
            record.hyperparameters = data['hyperparameters']

        db.session.commit()

        return jsonify({
            'code': 0,
            'msg': '训练记录更新成功'
        })

    except Exception as e:
        logger.error(f'更新训练记录失败: {str(e)}')
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': '服务器内部错误'
        }), 500


# 删除训练记录
@training_record_bp.route('/delete/<int:record_id>', methods=['DELETE'])
def delete_training(record_id):
    try:
        record = TrainingRecord.query.get_or_404(record_id)

        # 删除关联文件
        if os.path.exists(record.train_log):
            os.remove(record.train_log)

        if os.path.exists(record.checkpoint_dir):
            shutil.rmtree(record.checkpoint_dir)

        if record.metrics_path and os.path.exists(record.metrics_path):
            os.remove(record.metrics_path)

        # 删除数据库记录
        db.session.delete(record)
        db.session.commit()

        return jsonify({
            'code': 0,
            'msg': '训练记录删除成功'
        })

    except Exception as e:
        logger.error(f'删除训练记录失败: {str(e)}')
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': '服务器内部错误'
        }), 500
