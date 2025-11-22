"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import os
import shutil
from datetime import datetime

from flask import Blueprint, request, jsonify
from flask import render_template
from sqlalchemy import desc

from db_models import db, Model, TrainTask, ExportRecord

train_task_bp = Blueprint('train_task', __name__)
logger = logging.getLogger(__name__)


# 训练记录分页查询
@train_task_bp.route('/list', methods=['GET'])
def train_tasks():
    try:
        # 获取分页参数和模型名称过滤
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 10))
        model_name = request.args.get('model_name')  # 参数名改为 model_name
        status_filter = request.args.get('status')

        # 参数验证
        if page_no < 1 or page_size < 1:
            return jsonify({
                'code': 400,
                'msg': '参数错误：pageNo和pageSize必须为正整数'
            }), 400

        # 构建基础查询（关联 Model 表）
        query = db.session.query(
            TrainTask,
            Model.name.label('model_name')  # 明确获取模型名称
        )

        # 应用模型名称模糊匹配
        if model_name:
            # 使用 ilike 实现不区分大小写的模糊查询
            query = query.filter(Model.name.ilike(f'%{model_name}%'))

        # 应用状态过滤
        if status_filter in ['running', 'completed', 'failed']:
            query = query.filter(TrainTask.status == status_filter)

        # 按开始时间倒序排列
        query = query.order_by(desc(TrainTask.start_time))

        # 执行分页
        pagination = query.paginate(
            page=page_no,
            per_page=page_size,
            error_out=False
        )

        # 构建响应数据
        records = []
        for task, model_name in pagination.items:  # 解构查询结果
            records.append({
                'id': task.id,
                'model_id': task.model_id,
                'model_name': model_name,  # 直接使用关联查询结果
                'dataset_path': task.dataset_path,
                'hyperparameters': task.hyperparameters,
                'start_time': task.start_time.isoformat() if task.start_time else None,
                'progress': task.progress,
                'end_time': task.end_time.isoformat() if task.end_time else None,
                'status': task.status,
                'metrics_path': task.metrics_path,
                'train_results_path': task.train_results_path,
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
@train_task_bp.route('/<int:record_id>')
def train_detail(record_id):
    try:
        # 根据ID查询训练记录
        record = TrainTask.query.get(record_id)
        if not record:
            return jsonify({
                'code': 404,
                'msg': f'训练记录ID {record_id} 不存在'
            }), 404

        # 构建响应数据
        data = {
            'id': record.id,
            'model_id': record.model_id,
            'model_name': record.model.name if record.model else '',
            'dataset_path': record.dataset_path,
            'hyperparameters': record.hyperparameters,
            'start_time': record.start_time.isoformat() if record.start_time else None,
            'end_time': record.end_time.isoformat() if record.end_time else None,
            'status': record.status,
            'progress': record.progress,
            'metrics_path': record.metrics_path,
            'train_log': record.train_log,
            'checkpoint_dir': record.checkpoint_dir
        }

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': data
        })

    except Exception as e:
        logger.error(f'获取训练记录详情失败: {str(e)}')
        return jsonify({
            'code': 500,
            'msg': '服务器内部错误'
        }), 500


# 创建训练记录
@train_task_bp.route('/create', methods=['POST'])
def create_train():
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
        new_record = TrainTask(
            model_id=model_id,
            dataset_path=dataset_path,
            hyperparameters=data.get('hyperparameters', '{}'),
            status='running',
            train_log=f"logs/train_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            checkpoint_dir=f"checkpoints/train_{datetime.now().strftime('%Y%m%d_%H%M%S')}/"
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
@train_task_bp.route('/update/<int:record_id>', methods=['POST'])
def update_train(record_id):
    try:
        record = TrainTask.query.get_or_404(record_id)
        data = request.json

        # 更新训练记录字段
        if 'status' in data:
            record.status = data['status']

        if 'metrics' in data:
            # 保存指标到文件
            metrics_path = f"metrics/train_{record_id}.json"
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
@train_task_bp.route('/delete/<int:record_id>', methods=['DELETE'])
def delete_train(record_id):
    try:
        record = TrainTask.query.get_or_404(record_id)

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


# 发布训练记录为正式模型
@train_task_bp.route('/publish/<int:record_id>', methods=['POST'])
def publish_train_task(record_id):
    try:
        # 获取训练记录
        record = TrainTask.query.get_or_404(record_id)
        
        # 获取前端传入的版本号
        data = request.json

        # 验证模型路径是否存在
        if not record.minio_model_path:
            return jsonify({
                'code': 400,
                'msg': '训练记录没有有效的模型路径'
            }), 400

        # 获取关联的模型
        model = Model.query.get_or_404(record.model_id)

        # 更新模型的模型路径
        model.model_path = record.minio_model_path
        model.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'code': 0,
            'msg': '模型发布成功',
            'data': {
                'model_id': model.id,
                'model_path': model.model_path,
            }
        })

    except Exception as e:
        logger.error(f'发布训练记录失败: {str(e)}')
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': '服务器内部错误'
        }), 500