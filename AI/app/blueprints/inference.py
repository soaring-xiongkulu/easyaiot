from flask import Blueprint, request, jsonify

from app.services.inference_service import InferenceService
from models import Model, InferenceRecord, db
from datetime import datetime
import logging

inference_bp = Blueprint('inference', __name__)

# ========== 推理记录管理接口 ==========
@inference_bp.route('/inference_records', methods=['POST'])
def create_inference_record():
    """创建推理记录（任务开始时调用）"""
    data = request.json
    required_fields = ['model_id', 'inference_type', 'input_source']
    if not all(field in data for field in required_fields):
        return jsonify({'error': '缺少必要字段: model_id, inference_type, input_source'}), 400

    new_record = InferenceRecord(
        model_id=data['model_id'],
        inference_type=data['inference_type'],
        input_source=data['input_source'],
        status='PROCESSING'  # 初始状态为处理中
    )

    try:
        db.session.add(new_record)
        db.session.commit()
        return jsonify({
            'id': new_record.id,
            'message': '推理记录创建成功',
            'start_time': new_record.start_time.isoformat()
        }), 201
    except Exception as e:
        db.session.rollback()
        logging.error(f"创建记录失败: {str(e)}")
        return jsonify({'error': f'数据库错误: {str(e)}'}), 500


@inference_bp.route('/inference_records/<int:record_id>', methods=['PUT'])
def update_inference_record(record_id):
    """更新推理记录状态和进度"""
    record = InferenceRecord.query.get_or_404(record_id)
    data = request.json

    # 更新核心字段
    updatable_fields = ['status', 'processed_frames', 'output_path',
                        'stream_output_url', 'error_message']
    for field in updatable_fields:
        if field in data:
            setattr(record, field, data[field])

    # 结束时更新时间和耗时
    if data.get('status') in ['COMPLETED', 'FAILED']:
        record.end_time = datetime.utcnow()
        if record.start_time:
            record.processing_time = (record.end_time - record.start_time).total_seconds()

    try:
        db.session.commit()
        return jsonify({'message': '记录更新成功'}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"更新记录失败: {str(e)}")
        return jsonify({'error': f'更新失败: {str(e)}'}), 500


@inference_bp.route('/inference_records', methods=['GET'])
def get_inference_records():
    """分页查询推理记录"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    model_id = request.args.get('model_id')
    status = request.args.get('status')

    query = InferenceRecord.query

    # 构建查询条件
    if model_id:
        query = query.filter_by(model_id=model_id)
    if status:
        query = query.filter_by(status=status)

    # 执行分页查询
    records = query.order_by(InferenceRecord.start_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'items': [{
            'id': r.id,
            'model_id': r.model_id,
            'status': r.status,
            'input_source': r.input_source,
            'start_time': r.start_time.isoformat(),
            'processing_time': r.processing_time
        } for r in records.items],
        'total': records.total,
        'page': records.page
    }), 200


@inference_bp.route('/inference_records/<int:record_id>', methods=['GET'])
def get_inference_record_detail(record_id):
    """获取单条推理记录的详细信息"""
    record = InferenceRecord.query.get_or_404(record_id)
    return jsonify({
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
    }), 200


@inference_bp.route('/inference_records/<int:record_id>', methods=['DELETE'])
def delete_inference_record(record_id):
    """删除推理记录"""
    record = InferenceRecord.query.get_or_404(record_id)
    try:
        db.session.delete(record)
        db.session.commit()
        return jsonify({'message': '记录已删除'}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"删除记录失败: {str(e)}")
        return jsonify({'error': f'删除失败: {str(e)}'}), 500


# ========== 全局异常处理 ==========
@inference_bp.errorhandler(404)
def handle_not_found(e):
    return jsonify({'error': '资源不存在'}), 404


@inference_bp.errorhandler(500)
def handle_server_error(e):
    logging.error(f'服务器内部错误: {str(e)}')
    return jsonify({'error': '服务器内部错误'}), 500


@inference_bp.route('/<int:model_id>/inference/run', methods=['POST'])
def run_inference(model_id):
    """执行模型推理（已集成记录管理）"""
    model = Model.query.get_or_404(model_id)

    # 创建推理记录
    record_data = {
        'model_id': model_id,
        'inference_type': request.form.get('inference_type'),
        'input_source': request.form.get('rtsp_url') or
                        request.files.get('image_file').filename or
                        request.files.get('video_file').filename
    }
    record_resp = create_inference_record()
    if record_resp[1] != 201:
        return record_resp
    record_id = record_resp.json['id']

    try:
        # 获取表单数据
        model_type = request.form.get('model_type')
        inference_type = request.form.get('inference_type')
        system_model = request.form.get('system_model')

        # 获取上传的文件
        model_file = request.files.get('model_file')
        image_file = request.files.get('image_file')
        video_file = request.files.get('video_file')
        rtsp_url = request.form.get('rtsp_url')

        # 创建推理管理器
        inference_manager = InferenceService(model_id)

        # 加载模型
        model = inference_manager.load_model(model_type, system_model, model_file)

        # 根据推理类型执行推理
        if inference_type == 'image':
            if not image_file or image_file.filename == '':
                return jsonify({
                    'success': False,
                    'error': '未选择图片文件'
                })

            result = inference_manager.inference_image(model, image_file)
            return jsonify({
                'success': True,
                'result': result
            })

        elif inference_type == 'video':
            if not video_file or video_file.filename == '':
                return jsonify({
                    'success': False,
                    'error': '未选择视频文件'
                })

            result = inference_manager.inference_video(model, video_file)
            return jsonify({
                'success': True,
                'result': result
            })

        elif inference_type == 'rtsp':
            if not rtsp_url:
                return jsonify({
                    'success': False,
                    'error': '未提供RTSP流地址'
                })

            result = inference_manager.inference_rtsp(model, rtsp_url)
            return jsonify({
                'success': True,
                'result': result
            })

        else:
            return jsonify({
                'success': False,
                'error': f'不支持的推理类型: {inference_type}'
            })

    except Exception as e:
        # 更新记录状态为失败
        update_inference_record(record_id, {'status': 'FAILED', 'error_message': str(e)})
        return jsonify({'success': False, 'error': str(e)})