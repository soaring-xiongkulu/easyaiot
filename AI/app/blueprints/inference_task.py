import os
import uuid
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify

from app.services.inference_service import InferenceService
from models import db, InferenceTask
from app.services.model_service import ModelService

inference_task_bp = Blueprint('inference_task', __name__)
logger = logging.getLogger(__name__)

# ========== 文件上传接口 ==========
@inference_task_bp.route('/upload_input', methods=['POST'])
def upload_input_file():
    """上传推理输入文件（图片/视频）"""
    if 'file' not in request.files:
        return jsonify({'code': 400, 'msg': '未找到文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'msg': '未选择文件'}), 400

    temp_path = None
    try:
        # 获取文件扩展名并生成唯一文件名
        ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{ext}"

        # 创建临时目录和文件
        temp_dir = 'temp_uploads'
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, unique_filename)
        file.save(temp_path)

        # 上传到MinIO
        bucket_name = 'inference-inputs'
        object_key = f"inputs/{unique_filename}"

        if ModelService.upload_to_minio(bucket_name, object_key, temp_path):
            # 生成URL
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
        logger.error(f"输入文件上传失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500
    finally:
        # 确保删除临时文件
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError as e:
                logger.error(f"删除临时文件失败: {temp_path}, 错误: {str(e)}")

# ========== 推理任务管理接口 ==========
@inference_task_bp.route('/create', methods=['POST'])
def create_Inference_task():
    """创建推理任务（任务开始时调用）"""
    data = request.json
    required_fields = ['model_id', 'inference_type']
    if not all(field in data for field in required_fields):
        return jsonify({'code': 400, 'msg': '缺少必要字段: model_id, inference_type'}), 400

    # 根据推理类型验证输入源
    inference_type = data['inference_type']
    input_source = data.get('input_source', '')

    if inference_type == 'rtsp':
        if not input_source or not input_source.startswith('rtsp://'):
            return jsonify({'code': 400, 'msg': 'RTSP流地址格式不正确'}), 400
    elif inference_type in ['image', 'video']:
        if not input_source:
            return jsonify({'code': 400, 'msg': '请提供输入源URL'}), 400
    else:
        return jsonify({'code': 400, 'msg': f'不支持的推理类型: {inference_type}'}), 400

    new_record = InferenceTask(
        model_id=data['model_id'],
        inference_type=inference_type,
        input_source=input_source,
        status='PROCESSING'  # 初始状态为处理中
    )

    try:
        db.session.add(new_record)
        db.session.commit()
        return jsonify({
            'code': 0,
            'msg': '推理任务创建成功',
            'data': {
                'id': new_record.id,
                'start_time': new_record.start_time.isoformat()
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建推理任务失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'数据库错误: {str(e)}'}), 500

@inference_task_bp.route('/update/<int:record_id>', methods=['PUT'])
def update_Inference_task(record_id):
    """更新推理任务"""
    record = InferenceTask.query.get_or_404(record_id)
    data = request.json

    # 更新字段
    updatable_fields = ['status', 'processed_frames', 'output_path',
                        'stream_output_url', 'error_message']
    for field in updatable_fields:
        if field in data:
            setattr(record, field, data[field])

    # 结束状态处理
    if data.get('status') in ['COMPLETED', 'FAILED']:
        record.end_time = datetime.utcnow()
        if record.start_time:
            record.processing_time = (record.end_time - record.start_time).total_seconds()

    try:
        db.session.commit()
        return jsonify({'code': 0, 'msg': '记录更新成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新记录失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'更新失败: {str(e)}'}), 500

@inference_task_bp.route('/list', methods=['GET'])
def get_inference_tasks():
    """分页查询推理任务"""
    try:
        # 获取分页参数
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 10))
        model_id = request.args.get('model_id')
        status = request.args.get('status')

        # 参数验证
        if page_no < 1 or page_size < 1:
            return jsonify({'code': 400, 'msg': '参数错误：pageNo和pageSize必须为正整数'}), 400

        # 构建查询
        query = InferenceTask.query
        if model_id:
            query = query.filter_by(model_id=model_id)
        if status:
            query = query.filter_by(status=status)

        # 执行分页查询
        pagination = query.order_by(InferenceTask.start_time.desc()).paginate(
            page=page_no, per_page=page_size, error_out=False
        )

        # 构建响应数据
        records = [{
            'id': r.id,
            'model_id': r.model_id,
            'status': r.status,
            'input_source': r.input_source,
            'start_time': r.start_time.isoformat(),
            'processing_time': r.processing_time
        } for r in pagination.items]

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': records,
            'total': pagination.total
        })
    except ValueError:
        return jsonify({'code': 400, 'msg': '参数类型错误：pageNo和pageSize需为整数'}), 400
    except Exception as e:
        logger.error(f"获取推理任务失败: {str(e)}")
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500

@inference_task_bp.route('/detail/<int:record_id>', methods=['GET'])
def get_Inference_task_detail(record_id):
    """获取单条推理任务的详细信息"""
    try:
        record = InferenceTask.query.get_or_404(record_id)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'id': record.id,
                'model_id': record.model_id,
                'input_source': record.input_source,
                'output_path': record.output_path,
                'stream_output_url': record.stream_output_url,
                'status': record.status,
                'processed_frames': record.processed_frames,
                'start_time': record.start_time.isoformat(),
                'end_time': record.end_time.isoformat() if record.end_time else None,
                'processing_time': record.processing_time,
                'error_message': record.error_message
            }
        })
    except Exception as e:
        logger.error(f"获取推理任务详情失败: {str(e)}")
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500

@inference_task_bp.route('/delete/<int:record_id>', methods=['DELETE'])
def delete_Inference_task(record_id):
    """删除推理任务"""
    try:
        record = InferenceTask.query.get_or_404(record_id)
        db.session.delete(record)
        db.session.commit()
        return jsonify({'code': 0, 'msg': '记录已删除'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除记录失败: {str(e)}")
        return jsonify({'code': 500, 'msg': f'删除失败: {str(e)}'}), 500

# ========== 执行推理接口 ==========
@inference_task_bp.route('/<int:model_id>/inference/run', methods=['POST'])
def run_inference(model_id):
    """执行推理任务"""
    data = request.json
    required_fields = ['inference_type', 'input_source']
    if not all(field in data for field in required_fields):
        return jsonify({'code': 400, 'msg': '缺少必要参数'}), 400

    # 创建推理任务
    record_data = {
        'model_id': model_id,
        'inference_type': data['inference_type'],
        'input_source': data['input_source']
    }
    record_resp = create_Inference_task()
    if record_resp[1] != 200:  # 注意状态码判断
        return record_resp

    record_id = record_resp.json['data']['id']
    record = InferenceTask.query.get(record_id)

    try:
        # 初始化推理服务
        inference_service = InferenceService(model_id)

        # 根据类型执行推理
        inference_type = data['inference_type']
        if inference_type == 'image':
            result = inference_service.inference_image(data['input_source'])
            record.output_path = result.get('output_path')
        elif inference_type == 'video':
            result = inference_service.inference_video(data['input_source'])
            record.output_path = result.get('output_path')
        elif inference_type == 'rtsp':
            result = inference_service.inference_rtsp(data['input_source'])
            record.stream_output_url = result.get('stream_url')
        else:
            raise ValueError(f'不支持的推理类型: {inference_type}')

        # 更新记录状态
        record.status = 'COMPLETED' if inference_type != 'rtsp' else 'STREAMING'
        record.end_time = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'code': 0,
            'msg': '推理执行成功',
            'data': {
                'record_id': record_id,
                'result': result
            }
        })
    except Exception as e:
        # 错误处理
        record.status = 'FAILED'
        record.error_message = str(e)
        record.end_time = datetime.utcnow()
        db.session.commit()

        logger.error(f"推理失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'推理执行失败: {str(e)}',
            'data': {'record_id': record_id}
        })

# ========== 全局异常处理 ==========
@inference_task_bp.errorhandler(404)
def handle_not_found(e):
    return jsonify({'code': 404, 'msg': '资源不存在'}), 404

@inference_task_bp.errorhandler(500)
def handle_server_error(e):
    logger.error(f'服务器内部错误: {str(e)}')
    return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500