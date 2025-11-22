"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import os
import uuid
import logging
import tempfile
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from flask import Blueprint, request, jsonify, current_app

from app.services.inference_service import InferenceService
from db_models import db, InferenceTask, Model
from app.services.minio_service import ModelService

inference_task_bp = Blueprint('inference_task', __name__)
logger = logging.getLogger(__name__)


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


def download_file_from_url(url: str, temp_dir: str = None) -> str:
    """
    从MinIO URL下载文件到临时文件
    返回临时文件路径
    """
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp()
    
    bucket_name, object_key = parse_minio_url(url)
    if not bucket_name or not object_key:
        raise ValueError(f"无法解析MinIO URL: {url}")
    
    # 生成临时文件路径
    filename = os.path.basename(object_key) or f"temp_{uuid.uuid4().hex}"
    temp_path = os.path.join(temp_dir, filename)
    
    # 从MinIO下载
    success, error_msg = ModelService.download_from_minio(bucket_name, object_key, temp_path)
    if not success:
        raise Exception(f"从MinIO下载文件失败: {bucket_name}/{object_key}. {error_msg or ''}")
    
    return temp_path

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

        upload_success, upload_error = ModelService.upload_to_minio(bucket_name, object_key, temp_path)
        if upload_success:
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

    # 验证并处理 model_id
    # 如果 model_id 为 0 或不存在于数据库中，设置为 None（表示使用默认模型）
    model_id = data['model_id']
    actual_model_id = None
    if model_id and model_id > 0:
        # 验证 model_id 是否存在
        model = Model.query.get(model_id)
        if model:
            actual_model_id = model_id
        else:
            logger.warning(f"模型 ID {model_id} 不存在，将使用默认模型")
            actual_model_id = None
    else:
        # model_id 为 0、None 或负数，使用默认模型
        logger.info(f"使用默认模型（model_id={model_id}）")
        actual_model_id = None

    new_record = InferenceTask(
        model_id=actual_model_id,
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
            'inference_type': r.inference_type,
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
                'inference_type': record.inference_type,
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
    """执行推理任务
    支持两种方式：
    1. 上传文件：POST multipart/form-data，包含file字段
    2. 使用URL：POST JSON，包含input_source字段（MinIO URL）
    """
    # 支持JSON和form-data两种请求格式
    if request.is_json:
        data = request.json
    else:
        data = request.form.to_dict()
        # 处理JSON字符串参数（如parameters）
        if 'parameters' in data and isinstance(data['parameters'], str):
            import json
            try:
                data['parameters'] = json.loads(data['parameters'])
            except:
                pass
    
    # 验证必要参数
    if 'inference_type' not in data:
        return jsonify({'code': 400, 'msg': '缺少必要参数: inference_type'}), 400
    
    inference_type = data['inference_type']
    input_source = data.get('input_source', '')
    
    # 验证输入源
    if inference_type == 'rtsp':
        if not input_source or not input_source.startswith('rtsp://'):
            return jsonify({'code': 400, 'msg': 'RTSP流地址格式不正确'}), 400
    elif inference_type in ['image', 'video']:
        # 对于图片和视频，必须提供input_source（URL）或文件上传
        if not input_source and 'file' not in request.files:
            return jsonify({'code': 400, 'msg': '请提供输入源URL（input_source）或上传文件（file）'}), 400
    else:
        return jsonify({'code': 400, 'msg': f'不支持的推理类型: {inference_type}'}), 400
    
    # 验证并处理 model_id
    # 如果 model_id 为 0 或不存在于数据库中，设置为 None（表示使用默认模型）
    actual_model_id = None
    model = None
    if model_id > 0:
        # 验证 model_id 是否存在
        model = Model.query.get(model_id)
        if model:
            actual_model_id = model_id
        else:
            logger.warning(f"模型 ID {model_id} 不存在，将使用默认模型")
            actual_model_id = None
    else:
        # model_id 为 0 或负数，使用默认模型
        logger.info(f"使用默认模型（model_id={model_id}）")
        actual_model_id = None
    
    # 处理输入源：如果是直接上传文件，需要先上传到MinIO获取URL
    actual_input_source = input_source
    uploaded_file_path = None
    
    if inference_type in ['image', 'video'] and 'file' in request.files and not input_source:
        # 直接上传文件，需要先上传到MinIO
        file = request.files['file']
        if file.filename:
            try:
                # 创建临时文件保存上传的文件
                temp_dir = tempfile.mkdtemp()
                ext = os.path.splitext(file.filename)[1]
                unique_filename = f"{uuid.uuid4().hex}{ext}"
                uploaded_file_path = os.path.join(temp_dir, unique_filename)
                file.save(uploaded_file_path)
                
                # 上传到MinIO
                bucket_name = 'inference-inputs'
                object_key = f"inputs/{unique_filename}"
                
                upload_success, upload_error = ModelService.upload_to_minio(bucket_name, object_key, uploaded_file_path)
                if upload_success:
                    # 生成MinIO URL
                    actual_input_source = f"/api/v1/buckets/{bucket_name}/objects/download?prefix={object_key}"
                else:
                    logger.error("文件上传到MinIO失败")
                    return jsonify({'code': 500, 'msg': '文件上传到MinIO失败'}), 500
            except Exception as e:
                logger.error(f"处理上传文件失败: {str(e)}")
                return jsonify({'code': 500, 'msg': f'处理上传文件失败: {str(e)}'}), 500
    
    # 创建任务记录
    new_record = InferenceTask(
        model_id=actual_model_id,
        inference_type=inference_type,
        input_source=actual_input_source or '',
        status='PROCESSING'
    )
    
    try:
        db.session.add(new_record)
        db.session.commit()
        record_id = new_record.id
        record = new_record
        
        if not record:
            return jsonify({'code': 404, 'msg': '推理任务不存在'}), 404

        # 获取模型文件路径（如果提供了默认模型路径）
        model_file_path = data.get('model_file_path')
        
        # 初始化推理服务 - 使用验证后的 actual_model_id
        inference_service = InferenceService(actual_model_id)
        
        # 如果提供了模型文件路径，设置使用该路径
        if model_file_path:
            # 构建完整的模型文件路径
            # 模型文件在AI目录根目录下
            app_root = current_app.root_path  # app目录路径
            ai_root = os.path.dirname(app_root)  # AI目录路径
            
            # 优先在AI目录下查找
            full_model_path = os.path.join(ai_root, model_file_path)
            full_model_path = os.path.abspath(full_model_path)
            
            # 如果AI目录下不存在，尝试其他位置
            if not os.path.exists(full_model_path):
                # 尝试从当前工作目录查找
                cwd = os.getcwd()
                if os.path.basename(cwd) == 'AI':
                    cwd_path = os.path.join(cwd, model_file_path)
                    if os.path.exists(cwd_path):
                        full_model_path = os.path.abspath(cwd_path)
                elif os.path.exists(os.path.join(cwd, 'AI', model_file_path)):
                    full_model_path = os.path.abspath(os.path.join(cwd, 'AI', model_file_path))
                elif os.path.exists(os.path.join(cwd, model_file_path)):
                    full_model_path = os.path.abspath(os.path.join(cwd, model_file_path))
            
            # 如果文件存在，设置使用该模型文件
            if os.path.exists(full_model_path):
                inference_service.set_model_path(full_model_path)
                logger.info(f"使用指定的模型文件: {full_model_path}")
            else:
                logger.warning(f"指定的模型文件不存在: {full_model_path}，将使用默认模型查找逻辑")
        
        # 获取推理参数
        parameters = data.get('parameters', {})

        # 根据类型执行推理
        inference_type = data['inference_type']
        temp_file_path = None
        temp_dir = None
        
        try:
            if inference_type == 'image':
                # 支持URL或直接文件上传
                if uploaded_file_path and os.path.exists(uploaded_file_path):
                    # 如果已经上传到MinIO并保存了临时文件，使用临时文件路径
                    result = inference_service.inference_image(uploaded_file_path, parameters, record_id)
                elif 'file' in request.files:
                    # 直接文件上传（未上传到MinIO的情况，应该不会发生，但保留作为fallback）
                    image_file = request.files['file']
                    # 重置文件指针到开头
                    image_file.seek(0)
                    result = inference_service.inference_image(image_file, parameters, record_id)
                else:
                    # 从URL下载文件，直接传递文件路径
                    temp_dir = tempfile.mkdtemp()
                    temp_file_path = download_file_from_url(data['input_source'], temp_dir)
                    # 直接传递文件路径字符串
                    result = inference_service.inference_image(temp_file_path, parameters, record_id)
                
                # 输出路径已在 inference_image 中更新，这里不需要再次更新
                
            elif inference_type == 'video':
                # 支持URL或直接文件上传
                if 'file' in request.files:
                    # 直接文件上传
                    video_file = request.files['file']
                    result = inference_service.inference_video(video_file, parameters, record_id)
                else:
                    # 从URL下载文件，直接传递文件路径
                    temp_dir = tempfile.mkdtemp()
                    temp_file_path = download_file_from_url(data['input_source'], temp_dir)
                    # 直接传递文件路径字符串
                    result = inference_service.inference_video(temp_file_path, parameters, record_id)
                
                # 更新输出路径（视频处理是异步的，返回的是状态信息）
                # 注意：视频处理是异步的，output_path会在后台进程中更新
                if result.get('status') == 'processing':
                    # 异步处理中，保持PROCESSING状态，不更新output_path和end_time
                    # 后台进程会在完成后更新这些字段
                    record.status = 'PROCESSING'
                    db.session.commit()
                else:
                    # 如果不是processing状态（理论上不应该发生），按正常流程处理
                    record.output_path = result.get('output_path') or result.get('result_url')
                    record.status = 'COMPLETED'
                    record.end_time = datetime.utcnow()
                    db.session.commit()
                
                # 视频推理是异步的，直接返回，不继续执行后面的状态更新
                return jsonify({
                    'code': 0,
                    'msg': '推理执行成功',
                    'data': {
                        'record_id': record_id,
                        'result': result
                    }
                })
                
            elif inference_type == 'rtsp':
                result = inference_service.inference_rtsp(data['input_source'], parameters, record_id)
                record.stream_output_url = result.get('stream_url')
                record.status = 'STREAMING'
                record.end_time = datetime.utcnow()
                db.session.commit()
            else:
                raise ValueError(f'不支持的推理类型: {inference_type}')

            # 更新记录状态（仅对图片推理执行，视频和rtsp已在上面处理）
            if inference_type == 'image':
                record.status = 'COMPLETED'
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
        finally:
            # 清理临时文件
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"删除临时文件失败: {temp_file_path}, {str(e)}")
            if temp_dir and os.path.exists(temp_dir):
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"删除临时目录失败: {temp_dir}, {str(e)}")
            # 清理上传文件的临时文件（如果使用了临时文件）
            if uploaded_file_path and os.path.exists(uploaded_file_path):
                try:
                    uploaded_file_dir = os.path.dirname(uploaded_file_path)
                    if os.path.exists(uploaded_file_path):
                        os.unlink(uploaded_file_path)
                    # 如果目录为空，删除目录
                    if os.path.exists(uploaded_file_dir) and not os.listdir(uploaded_file_dir):
                        import shutil
                        shutil.rmtree(uploaded_file_dir)
                except Exception as e:
                    logger.warning(f"删除上传文件临时文件失败: {uploaded_file_path}, {str(e)}")
                    
    except Exception as e:
        # 错误处理
        if 'record' in locals() and record:
            record.status = 'FAILED'
            record.error_message = str(e)
            record.end_time = datetime.utcnow()
            db.session.commit()

        logger.error(f"推理失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 500,
            'msg': f'推理执行失败: {str(e)}',
            'data': {'record_id': record_id if 'record_id' in locals() else None}
        }), 500

# ========== 全局异常处理 ==========
@inference_task_bp.errorhandler(404)
def handle_not_found(e):
    return jsonify({'code': 404, 'msg': '资源不存在'}), 404

@inference_task_bp.errorhandler(500)
def handle_server_error(e):
    logger.error(f'服务器内部错误: {str(e)}')
    return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500