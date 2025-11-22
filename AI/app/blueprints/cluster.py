"""
集群推理接口
通过Nacos发现services实例并实现集群推理
使用不同的路由，不影响原有的推理接口
"""
import os
import logging
import tempfile
import uuid
import shutil
from datetime import datetime
from flask import Blueprint, request, jsonify

from db_models import db, InferenceTask, Model
from app.services.cluster_inference_service import ClusterInferenceService
from app.services.minio_service import ModelService

cluster_inference_bp = Blueprint('cluster_inference', __name__, url_prefix='/cluster')
logger = logging.getLogger(__name__)


def _process_cluster_inference_results(
    predictions: list,
    result_image_path: str,
    original_image_url: str,
    task_id: str,
    temp_dir: str
) -> dict:
    """
    处理集群推理结果，上传结果图和JSON到MinIO
    
    Args:
        predictions: 检测结果列表
        result_image_path: 结果图片路径（services实例本地路径或base64编码）
        original_image_url: 原始图片的MinIO URL
        task_id: 任务ID
        temp_dir: 临时目录
    
    Returns:
        处理后的结果字典，包含image_url、result_url、detections、json_url等
    """
    import json
    import base64
    import cv2
    
    result_image_local_path = None
    json_path = None
    
    try:
        # 处理结果图片路径
        if result_image_path:
            # 检查是否是base64编码
            if result_image_path.startswith('data:image'):
                # base64编码的图片
                header, encoded = result_image_path.split(',', 1)
                image_data = base64.b64decode(encoded)
                result_image_local_path = os.path.join(temp_dir, 'result.jpg')
                with open(result_image_local_path, 'wb') as f:
                    f.write(image_data)
                logger.info(f"已解码base64图片并保存到: {result_image_local_path}")
            elif os.path.exists(result_image_path):
                # 本地文件路径
                result_image_local_path = result_image_path
            else:
                logger.warning(f"结果图片路径不存在: {result_image_path}")
        
        # 如果没有结果图片，创建一个空的（不应该发生）
        if not result_image_local_path or not os.path.exists(result_image_local_path):
            logger.error("无法获取结果图片")
            return {
                'image_url': original_image_url,
                'result_url': None,
                'detections': predictions,
                'detection_count': len(predictions),
                'json_url': None
            }
        
        # 保存JSON检测结果到临时文件
        json_path = os.path.join(temp_dir, 'detections.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(predictions, f, indent=2, ensure_ascii=False)
        
        # 上传结果图片到MinIO
        date_str = datetime.now().strftime('%Y%m%d')
        image_filename = f"result_{task_id}_{uuid.uuid4().hex[:8]}.jpg"
        image_object_key = f"images/{date_str}/{image_filename}"
        
        inference_results_bucket = "inference-results"
        upload_success, upload_error = ModelService.upload_to_minio(
            inference_results_bucket,
            image_object_key,
            result_image_local_path
        )
        
        # 上传JSON检测结果到MinIO
        json_filename = f"detections_{task_id}_{uuid.uuid4().hex[:8]}.json"
        json_object_key = f"json/{date_str}/{json_filename}"
        
        json_upload_success, json_upload_error = ModelService.upload_to_minio(
            inference_results_bucket,
            json_object_key,
            json_path
        )
        
        # 生成结果图片的MinIO下载URL
        if upload_success:
            result_url = f"/api/v1/buckets/{inference_results_bucket}/objects/download?prefix={image_object_key}"
        else:
            logger.error(f"结果图片上传到MinIO失败: {image_object_key}, 错误: {upload_error}")
            result_url = None
        
        # 生成JSON结果的MinIO下载URL
        if json_upload_success:
            json_url = f"/api/v1/buckets/{inference_results_bucket}/objects/download?prefix={json_object_key}"
        else:
            logger.error(f"JSON结果上传到MinIO失败: {json_object_key}, 错误: {json_upload_error}")
            json_url = None
        
        # 返回结果
        return {
            'image_url': original_image_url,  # 原始图片的MinIO URL
            'result_url': result_url,  # 分析后的图片MinIO URL
            'detections': predictions,
            'detection_count': len(predictions),
            'json_url': json_url
        }
        
    except Exception as e:
        logger.error(f"处理集群推理结果失败: {str(e)}", exc_info=True)
        return {
            'image_url': original_image_url,
            'result_url': None,
            'detections': predictions,
            'detection_count': len(predictions),
            'json_url': None
        }
    finally:
        # 清理临时文件（但不删除result_image_local_path，因为它可能是services实例的文件）
        if json_path and os.path.exists(json_path):
            try:
                os.unlink(json_path)
            except Exception as e:
                logger.warning(f"删除临时JSON文件失败: {str(e)}")


def download_file_from_url(url: str, temp_dir: str = None) -> str:
    """从MinIO URL下载文件到临时文件，如果本地已存在则直接返回"""
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
        
        # 获取AI模块根目录，用于创建缓存目录
        app_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        cache_dir = os.path.join(app_root, 'data', 'cache', 'inference_inputs')
        os.makedirs(cache_dir, exist_ok=True)
        
        # 根据object_key生成缓存文件路径（使用object_key的basename作为文件名）
        filename = os.path.basename(object_key) or f"file_{uuid.uuid4().hex}"
        # 如果文件名没有扩展名，尝试从object_key中提取
        if not os.path.splitext(filename)[1]:
            ext = os.path.splitext(object_key)[1] or '.jpg'
            filename = f"{os.path.splitext(filename)[0]}{ext}"
        
        cache_file = os.path.join(cache_dir, filename)
        
        # 检查本地缓存文件是否存在
        if os.path.exists(cache_file):
            file_size = os.path.getsize(cache_file)
            logger.info(f"本地文件已存在，跳过下载: {cache_file}, 大小: {file_size} 字节")
            return cache_file
        
        # 如果指定了临时目录，使用临时目录；否则使用缓存目录
        if not temp_dir:
            temp_dir = cache_dir
        
        # 生成临时文件路径（如果缓存文件不存在，使用临时文件名）
        ext = os.path.splitext(object_key)[1] or '.jpg'
        temp_file = os.path.join(temp_dir, f"{uuid.uuid4().hex}{ext}")
        
        # 从MinIO下载文件到临时路径
        logger.info(f"开始从MinIO下载文件: {bucket_name}/{object_key}")
        success, error_msg = ModelService.download_from_minio(bucket_name, object_key, temp_file)
        if not success:
            raise Exception(f"从MinIO下载文件失败: {bucket_name}/{object_key}. {error_msg or ''}")
        
        # 如果下载成功，尝试将文件移动到缓存目录（如果使用临时目录）
        if temp_file != cache_file and os.path.exists(temp_file):
            try:
                # 如果缓存文件已存在（并发下载的情况），删除临时文件
                if os.path.exists(cache_file):
                    os.remove(temp_file)
                    logger.info(f"使用已存在的缓存文件: {cache_file}")
                    return cache_file
                else:
                    # 移动到缓存目录
                    shutil.move(temp_file, cache_file)
                    logger.info(f"文件已缓存到: {cache_file}")
                    return cache_file
            except Exception as e:
                logger.warning(f"移动文件到缓存目录失败: {str(e)}，使用临时文件: {temp_file}")
                return temp_file
        
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
        temp_result_dir = None
        try:
            result = ClusterInferenceService.inference_via_cluster(
                model_id=model_id,
                model_format=model_format,
                model_version=model_version,
                file_path=file_path,
                file_obj=file_obj,
                parameters=parameters
            )
            
            # 处理推理结果，上传到MinIO
            if result.get('code') == 0 and inference_type == 'image':
                result_data = result.get('data', {})
                predictions = result_data.get('predictions', [])
                # 优先使用base64编码的图片，如果没有则使用本地路径
                result_image_base64 = result_data.get('result_image_base64')
                result_image_path = result_data.get('result_image_path')
                
                # 处理结果图片和JSON，上传到MinIO
                temp_result_dir = tempfile.mkdtemp()
                processed_result = _process_cluster_inference_results(
                    predictions=predictions,
                    result_image_path=result_image_base64 or result_image_path,  # 优先使用base64
                    original_image_url=actual_input_source,
                    task_id=str(record_id),
                    temp_dir=temp_result_dir
                )
                
                # 更新任务记录的output_path
                if processed_result.get('result_url'):
                    record.output_path = processed_result['result_url']
                
                # 更新任务记录状态
                record.status = 'COMPLETED'
                record.end_time = datetime.now()
                db.session.commit()
                
                # 返回与普通推理接口一致的格式
                return jsonify({
                    'code': 0,
                    'msg': '推理执行成功',
                    'data': {
                        'record_id': record_id,
                        'result': {
                            'image_url': processed_result.get('image_url'),  # 原始图片URL
                            'result_url': processed_result.get('result_url'),  # 结果图片URL
                            'detections': processed_result.get('detections', []),
                            'detection_count': processed_result.get('detection_count', 0),
                            'json_url': processed_result.get('json_url')  # JSON结果URL
                        }
                    }
                })
            else:
                # 非图片推理或其他情况，直接返回原结果
                record.status = 'COMPLETED'
                record.end_time = datetime.now()
                db.session.commit()
                
                return jsonify(result)
            
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            logger.error(f"集群推理失败 [{error_type}]: {error_msg}", exc_info=True)
            record.status = 'ERROR'
            record.end_time = datetime.now()
            db.session.commit()
            
            return jsonify({
                'code': 500,
                'msg': f'集群推理失败: {error_msg}',
                'error_type': error_type
            }), 500
            
    except Exception as e:
        logger.error(f"执行集群推理失败: {str(e)}")
        if 'record' in locals() and record:
            record.status = 'FAILED'
            record.error_message = str(e)
            record.end_time = datetime.now()
            db.session.commit()
        else:
            db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500
    finally:
        # 清理临时目录
        if 'temp_result_dir' in locals() and temp_result_dir and os.path.exists(temp_result_dir):
            try:
                shutil.rmtree(temp_result_dir)
            except Exception as e:
                logger.warning(f"删除临时结果目录失败: {temp_result_dir}, {str(e)}")
        # 清理上传文件的临时文件
        if 'uploaded_file_path' in locals() and uploaded_file_path and os.path.exists(uploaded_file_path):
            try:
                uploaded_file_dir = os.path.dirname(uploaded_file_path)
                if os.path.exists(uploaded_file_path):
                    os.unlink(uploaded_file_path)
                # 如果目录为空，删除目录
                if os.path.exists(uploaded_file_dir) and not os.listdir(uploaded_file_dir):
                    shutil.rmtree(uploaded_file_dir)
            except Exception as e:
                logger.warning(f"删除上传文件临时文件失败: {uploaded_file_path}, {str(e)}")

