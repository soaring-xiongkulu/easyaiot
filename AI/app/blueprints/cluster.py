"""
集群推理接口
通过Nacos发现services实例并实现集群推理
使用不同的路由，不影响原有的推理接口
"""
import os
import logging
import tempfile
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify

from db_models import db, InferenceTask, Model
from app.services.cluster_inference_service import ClusterInferenceService
from app.services.minio_service import ModelService

cluster_inference_bp = Blueprint('cluster_inference', __name__, url_prefix='/cluster')
logger = logging.getLogger(__name__)


def download_file_from_url(url: str, temp_dir: str = None) -> str:
    """从MinIO URL下载文件到临时文件"""
    from urllib.parse import urlparse, parse_qs
    
    try:
        parsed = urlparse(url)
        path_parts = parsed.path.split('/')
        
        if len(path_parts) >= 5 and path_parts[3] == 'buckets':
            bucket_name = path_parts[4]
        else:
            raise Exception("无法解析MinIO URL")
        
        query_params = parse_qs(parsed.query)
        object_key = query_params.get('prefix', [None])[0]
        
        if not object_key:
            raise Exception("无法从URL中提取object_key")
        
        if not temp_dir:
            temp_dir = tempfile.mkdtemp()
        
        # 下载文件
        file_data = ModelService.download_from_minio(bucket_name, object_key)
        if not file_data:
            raise Exception("下载文件失败")
        
        # 保存到临时文件
        ext = os.path.splitext(object_key)[1] or '.jpg'
        temp_file = os.path.join(temp_dir, f"{uuid.uuid4().hex}{ext}")
        with open(temp_file, 'wb') as f:
            f.write(file_data)
        
        return temp_file
    except Exception as e:
        logger.error(f"下载文件失败: {str(e)}")
        raise


@cluster_inference_bp.route('/<int:model_id>/inference/run', methods=['POST'])
def run_cluster_inference(model_id):
    """
    执行集群推理任务
    通过Nacos发现services实例并实现集群推理
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
        return jsonify({'code': 400, 'msg': '集群推理暂不支持RTSP流'}), 400
    elif inference_type not in ['image', 'video']:
        return jsonify({'code': 400, 'msg': f'不支持的推理类型: {inference_type}'}), 400
    
    # 验证并处理 model_id
    if model_id <= 0:
        return jsonify({'code': 400, 'msg': '无效的model_id'}), 400
    
    model = Model.query.get(model_id)
    if not model:
        return jsonify({'code': 404, 'msg': '模型不存在'}), 404
    
    # 处理输入源：如果是直接上传文件，需要先上传到MinIO获取URL
    actual_input_source = input_source
    uploaded_file_path = None
    
    if 'file' in request.files and not input_source:
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
        model_id=model_id,
        inference_type=inference_type,
        input_source=actual_input_source or '',
        status='PROCESSING'
    )
    
    try:
        db.session.add(new_record)
        db.session.commit()
        record_id = new_record.id
        record = new_record
        
        # 推断模型格式
        model_path = model.model_path or model.onnx_model_path or model.torchscript_model_path or model.tensorrt_model_path or model.openvino_model_path
        if not model_path:
            return jsonify({'code': 400, 'msg': '模型没有可用的模型文件路径'}), 400
        
        model_format = ClusterInferenceService.get_model_format(model_path)
        model_version = model.version or 'V1.0.0'
        
        # 准备文件
        file_path = None
        file_obj = None
        
        if uploaded_file_path and os.path.exists(uploaded_file_path):
            file_path = uploaded_file_path
        elif 'file' in request.files:
            file_obj = request.files['file']
        elif input_source:
            # 从URL下载文件
            temp_dir = tempfile.mkdtemp()
            file_path = download_file_from_url(input_source, temp_dir)
        else:
            return jsonify({'code': 400, 'msg': '请提供输入源URL（input_source）或上传文件（file）'}), 400
        
        # 获取推理参数
        parameters = data.get('parameters', {})
        
        # 通过集群推理
        try:
            result = ClusterInferenceService.inference_via_cluster(
                model_id=model_id,
                model_format=model_format,
                model_version=model_version,
                file_path=file_path,
                file_obj=file_obj,
                parameters=parameters
            )
            
            # 更新任务记录
            record.status = 'COMPLETED'
            record.end_time = datetime.now()
            db.session.commit()
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"集群推理失败: {str(e)}")
            record.status = 'ERROR'
            record.end_time = datetime.now()
            db.session.commit()
            
            return jsonify({
                'code': 500,
                'msg': f'集群推理失败: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"执行集群推理失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500

