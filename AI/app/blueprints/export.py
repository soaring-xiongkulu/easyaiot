"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import os
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from flask import Blueprint, jsonify, current_app, url_for, send_file, request
from ultralytics import YOLO
from sqlalchemy import desc
import pytz

from app.services.minio_service import ModelService
from db_models import db, Model, ExportRecord, TrainTask

export_bp = Blueprint('export', __name__)
logger = logging.getLogger(__name__)

# 创建线程池执行器
executor = ThreadPoolExecutor(max_workers=4)

# 时区设置
BEIJING_TZ = pytz.timezone('Asia/Shanghai')
UTC_TZ = pytz.timezone('UTC')

def get_beijing_now():
    """获取当前北京时间（无时区信息的datetime对象，用于数据库存储）"""
    beijing_dt = datetime.now(BEIJING_TZ)
    # 返回无时区信息的datetime对象，因为数据库字段不支持时区
    return beijing_dt.replace(tzinfo=None)

def utc_to_beijing(utc_dt):
    """将数据库中的时间转换为北京时间（ISO格式字符串）
    
    注意：新数据使用get_beijing_now()存储的是北京时间（无时区信息），
    旧数据使用datetime.utcnow()存储的是UTC时间（无时区信息）。
    为了正确显示新数据，我们假设数据库中存储的就是北京时间，直接标记为北京时间。
    旧数据可能会有8小时的误差，但新数据会正确显示。
    """
    if utc_dt is None:
        return None
    if utc_dt.tzinfo is None:
        # 如果没有时区信息，假设数据库中存储的是北京时间（因为新数据使用get_beijing_now()）
        # 直接标记为北京时间
        beijing_dt = BEIJING_TZ.localize(utc_dt)
    else:
        # 如果有时区信息，转换为北京时间
        beijing_dt = utc_dt.astimezone(BEIJING_TZ)
    return beijing_dt.isoformat()

# 任务状态映射
EXPORT_STATUS = {
    'PENDING': '等待中',
    'PROCESSING': '处理中',
    'COMPLETED': '已完成',
    'FAILED': '失败'
}

SUPPORTED_FORMATS = {
    'onnx': {'ext': '.onnx', 'mime': 'application/octet-stream'},
    'openvino': {'ext': '_openvino_model/', 'mime': 'application/octet-stream'}
}

# 导出任务队列
export_tasks = {}


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

@export_bp.route('/<int:model_id>/export/<format>', methods=['POST'])
def api_export_model(model_id, format):
    try:
        # 验证格式支持
        if format not in SUPPORTED_FORMATS:
            return jsonify({'code': 400, 'msg': f'不支持的导出格式: {format}'}), 400

        # 获取模型信息
        model_record = Model.query.get_or_404(model_id)
        
        # 检查模型路径：优先使用Model.model_path，其次从TrainTask获取minio_model_path
        minio_model_path = None
        if model_record.model_path:
            minio_model_path = model_record.model_path
        else:
            # 查找该模型的最新训练任务（优先查找已完成的，且有minio_model_path的）
            train_task = TrainTask.query.filter_by(
                model_id=model_id
            ).filter(
                TrainTask.minio_model_path.isnot(None),
                TrainTask.minio_model_path != ''
            ).order_by(
                desc(TrainTask.end_time).nullslast(),
                desc(TrainTask.start_time)
            ).first()
            
            if train_task and train_task.minio_model_path:
                minio_model_path = train_task.minio_model_path

        if not minio_model_path:
            return jsonify({'code': 400, 'msg': '模型未上传到Minio，无法导出'}), 400

        # 获取请求参数（图片尺寸写死为640，OPSet使用默认值）
        export_config = {
            'img_size': 640,
            'opset': 12
        }

        # 创建导出记录（初始状态为等待中）
        export_record = ExportRecord(
            model_id=model_id,
            model_name=model_record.name,  # 保存模型名称
            format=format,
            status='PENDING',
            created_at=get_beijing_now()
        )
        db.session.add(export_record)
        db.session.commit()

        # 生成唯一任务ID
        task_id = str(uuid.uuid4())
        export_tasks[task_id] = {
            'status': 'PENDING',
            'export_id': export_record.id,
            'progress': 0
        }

        # 提交异步任务
        executor.submit(
            process_export_async,
            model_id,
            format,
            export_config,
            export_record.id,
            task_id
        )

        return jsonify({
            'code': 0,
            'msg': '导出任务已提交',
            'data': {
                'task_id': task_id,
                'export_id': export_record.id,
                'status_url': url_for('export.get_export_status', task_id_or_export_id=task_id, _external=True)
            }
        }), 202

    except Exception as e:
        current_app.logger.error(f"模型导出失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


def process_export_async(model_id, format, export_config, export_id, task_id):
    """异步处理导出任务"""
    # 需要在Flask应用上下文中运行，因为需要访问数据库和url_for
    from run import create_app
    application = create_app()
    
    export_record = None
    export_local_path = None
    
    with application.app_context():
        try:
            # 更新任务状态为处理中
            export_tasks[task_id]['status'] = 'PROCESSING'
            export_tasks[task_id]['progress'] = 10
            logger.info(f"开始处理导出任务: export_id={export_id}, task_id={task_id}, format={format}")

            # 获取导出记录
            export_record = ExportRecord.query.get(export_id)
            if not export_record:
                raise Exception("导出记录不存在")

            # 获取模型信息
            model_record = Model.query.get(model_id)
            if not model_record:
                raise Exception(f"模型不存在: model_id={model_id}")
            
            # 更新导出记录的模型名称（如果之前没有保存）
            if export_record and not export_record.model_name:
                export_record.model_name = model_record.name
                db.session.commit()
            
            # 检查模型路径：优先使用Model.model_path，其次从TrainTask获取minio_model_path
            minio_model_path = None
            if model_record.model_path:
                minio_model_path = model_record.model_path
            else:
                # 查找该模型的最新训练任务（优先查找已完成的，且有minio_model_path的）
                train_task = TrainTask.query.filter_by(
                    model_id=model_id
                ).filter(
                    TrainTask.minio_model_path.isnot(None),
                    TrainTask.minio_model_path != ''
                ).order_by(
                    desc(TrainTask.end_time).nullslast(),
                    desc(TrainTask.start_time)
                ).first()
                
                if train_task and train_task.minio_model_path:
                    minio_model_path = train_task.minio_model_path
            
            if not minio_model_path:
                raise Exception("未找到有效的模型路径，模型未上传到Minio")

            logger.info(f"找到模型路径: {minio_model_path}")

            # 创建临时目录
            with tempfile.TemporaryDirectory() as tmp_dir:
                # 从Minio下载原始模型
                local_pt_path = os.path.join(tmp_dir, 'model.pt')

                export_tasks[task_id]['progress'] = 20
                export_record.status = 'PROCESSING'
                db.session.commit()
                logger.info(f"状态已更新为PROCESSING，开始下载模型")

                # 解析MinIO URL获取bucket和object名称
                if minio_model_path.startswith('/api/v1/buckets/'):
                    bucket_name, object_name = parse_minio_url(minio_model_path)
                    if not bucket_name or not object_name:
                        raise Exception(f"无法解析MinIO URL: {minio_model_path}")
                else:
                    # 兼容旧格式：直接使用路径（假设bucket为models）
                    bucket_name = "models"
                    object_name = minio_model_path

                logger.info(f"从MinIO下载模型: bucket={bucket_name}, object={object_name}")
                success, error_msg = ModelService.download_from_minio(
                        bucket_name=bucket_name,
                        object_name=object_name,
                        destination_path=local_pt_path
                )
                if not success:
                    raise Exception(f"原始模型下载失败: {bucket_name}/{object_name}. {error_msg or ''}")

                logger.info(f"模型下载成功: {local_pt_path}")
                export_tasks[task_id]['progress'] = 40

                # 执行模型导出
                logger.info(f"开始执行模型导出: format={format}")
                model = YOLO(local_pt_path)
                export_filename = f"model{SUPPORTED_FORMATS[format]['ext']}"
                export_local_path = os.path.join(tmp_dir, export_filename)

                # 执行模型导出
                export_params = {
                    'format': format,
                    'imgsz': export_config['img_size'],
                    'device': 'cpu'
                }

                if format == 'openvino':
                    export_params['half'] = False
                elif format == 'onnx':
                    export_params['opset'] = export_config.get('opset', 12)

                model.export(**export_params)
                logger.info(f"模型导出完成，查找导出文件")

                # 处理导出文件
                if format == 'openvino':
                    # OpenVINO导出为目录
                    exported_files = [f for f in os.listdir(tmp_dir) if f.endswith('_openvino_model')]
                else:
                    # ONNX导出为单个文件
                    exported_files = [f for f in os.listdir(tmp_dir) if f.endswith('.onnx')]
                
                if not exported_files:
                    raise Exception("模型导出失败，未生成目标文件")

                logger.info(f"找到导出文件: {exported_files}")

                if format == 'onnx':
                    # ONNX格式：重命名文件
                    os.rename(os.path.join(tmp_dir, exported_files[0]), export_local_path)
                    logger.info(f"ONNX文件已重命名: {export_local_path}")

                # 上传到Minio
                minio_export_path = f"exports/model_{model_id}/{format}/{export_filename}"
                export_tasks[task_id]['progress'] = 70
                logger.info(f"开始上传到MinIO: {minio_export_path}")
                logger.info(f"本地文件路径: {export_local_path}, 文件是否存在: {os.path.exists(export_local_path) if format == 'onnx' else 'N/A'}")

                if format == 'openvino':
                    openvino_dir = os.path.join(tmp_dir, exported_files[0])
                    logger.info(f"OpenVINO目录路径: {openvino_dir}, 目录是否存在: {os.path.exists(openvino_dir)}")
                    upload_success, upload_error = ModelService.upload_directory_to_minio(
                        bucket_name="export-bucket",
                        object_prefix=minio_export_path.rstrip('/') + '/',
                        local_dir=openvino_dir
                    )
                else:
                    upload_success, upload_error = ModelService.upload_to_minio(
                        bucket_name="export-bucket",
                        object_name=minio_export_path,
                        file_path=export_local_path
                    )

                if not upload_success:
                    error_detail = upload_error or "未知错误"
                    logger.error(f"导出模型上传失败: {error_detail}")
                    raise Exception(f"导出模型上传失败: {error_detail}")

                logger.info(f"模型上传成功: {minio_export_path}")

                # 更新导出记录
                export_record.minio_path = minio_export_path
                export_record.local_path = export_local_path  # 保存本地路径
                export_record.status = 'COMPLETED'
                export_tasks[task_id]['status'] = 'COMPLETED'
                export_tasks[task_id]['progress'] = 100
                
                # 生成下载URL（需要在应用上下文中）
                export_tasks[task_id]['download_url'] = url_for(
                    'export.download_export',
                    export_id=export_record.id,
                    _external=True
                )

                # 更新模型表的对应字段
                if format == 'onnx':
                    model_record.onnx_model_path = minio_export_path
                elif format == 'openvino':
                    model_record.openvino_model_path = minio_export_path

                db.session.commit()
                logger.info(f"导出任务完成: export_id={export_id}, minio_path={minio_export_path}")

        except Exception as e:
            error_msg = f"异步导出失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # 确保在异常处理中也能访问export_record
            if export_record is None:
                try:
                    export_record = ExportRecord.query.get(export_id)
                except Exception as db_error:
                    logger.error(f"无法获取导出记录以更新状态: {str(db_error)}")
                    return
            
            if export_record:
                try:
                    export_record.status = 'FAILED'
                    export_record.message = str(e)
                    export_tasks[task_id]['status'] = 'FAILED'
                    export_tasks[task_id]['error'] = str(e)
                    db.session.commit()
                    logger.info(f"已更新导出记录状态为FAILED: export_id={export_id}")
                except Exception as commit_error:
                    logger.error(f"更新导出记录状态失败: {str(commit_error)}")


@export_bp.route('/status/<task_id_or_export_id>', methods=['GET'])
def get_export_status(task_id_or_export_id):
    """获取导出任务状态，支持通过task_id或export_id查询"""
    # 尝试作为task_id查询
    task = export_tasks.get(task_id_or_export_id)
    
    if task:
        # 通过task_id查询
        export_record = ExportRecord.query.get(task.get('export_id'))
        if not export_record:
            return jsonify({
                'code': 404,
                'msg': '导出记录不存在'
            }), 404

        response_data = {
            'task_id': task_id_or_export_id,
            'status': task['status'],
            'status_text': EXPORT_STATUS.get(task['status'], '未知状态'),
            'progress': task.get('progress', 0),
            'export_id': export_record.id,
            'model_id': export_record.model_id,
            'format': export_record.format,
            'created_at': utc_to_beijing(export_record.created_at),
        }

        if task['status'] == 'COMPLETED':
            response_data['download_url'] = task.get('download_url')
            response_data['minio_path'] = export_record.minio_path
        elif task['status'] == 'FAILED':
            response_data['error'] = task.get('error')

        return jsonify({
            'code': 0,
            'msg': '获取状态成功',
            'data': response_data
        })
    else:
        # 尝试作为export_id查询
        try:
            export_id = int(task_id_or_export_id)
            export_record = ExportRecord.query.get(export_id)
            if not export_record:
                return jsonify({
                    'code': 404,
                    'msg': '导出记录不存在'
                }), 404

            # 查找对应的task_id
            task_id = None
            for tid, t in export_tasks.items():
                if t.get('export_id') == export_id:
                    task_id = tid
                    break

            response_data = {
                'export_id': export_record.id,
                'status': export_record.status,
                'status_text': EXPORT_STATUS.get(export_record.status, '未知状态'),
                'model_id': export_record.model_id,
                'format': export_record.format,
                'created_at': utc_to_beijing(export_record.created_at),
            }

            if task_id:
                task = export_tasks.get(task_id)
                if task:
                    response_data['task_id'] = task_id
                    response_data['progress'] = task.get('progress', 0)
                    if task['status'] == 'COMPLETED':
                        response_data['download_url'] = task.get('download_url')
                    elif task['status'] == 'FAILED':
                        response_data['error'] = task.get('error')

            if export_record.status == 'COMPLETED' and export_record.minio_path:
                response_data['minio_path'] = export_record.minio_path
            elif export_record.status == 'FAILED' and export_record.message:
                response_data['error'] = export_record.message

            return jsonify({
                'code': 0,
                'msg': '获取状态成功',
                'data': response_data
            })
        except ValueError:
            return jsonify({
                'code': 400,
                'msg': '无效的任务ID或导出ID'
            }), 400


@export_bp.route('/list', methods=['GET'])
def get_export_list():
    """获取导出记录列表（分页）"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        model_id = request.args.get('model_id', type=int)
        format_filter = request.args.get('format', type=str)
        status_filter = request.args.get('status', type=str)
        search = request.args.get('search', type=str)  # 支持模型名称搜索

        # 构建查询
        query = ExportRecord.query
        if model_id:
            query = query.filter_by(model_id=model_id)
        if format_filter:
            query = query.filter_by(format=format_filter)
        if status_filter:
            query = query.filter_by(status=status_filter)
        if search:
            # 支持按模型名称搜索
            query = query.filter(ExportRecord.model_name.like(f'%{search}%'))

        # 执行分页查询
        pagination = query.order_by(ExportRecord.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        # 构建响应数据
        items = []
        for record in pagination.items:
            items.append({
                'id': record.id,
                'model_id': record.model_id,
                'model_name': record.model_name,  # 返回模型名称
                'format': record.format,
                'status': record.status,
                'status_text': EXPORT_STATUS.get(record.status, '未知状态'),
                'minio_path': record.minio_path,
                'message': record.message,
                'created_at': utc_to_beijing(record.created_at),
                'download_url': url_for(
                    'export.download_export',
                    export_id=record.id,
                    _external=True
                ) if record.status == 'COMPLETED' else None
            })

        return jsonify({
            'code': 0,
            'msg': '获取列表成功',
            'data': {
                'items': items,
                'total': pagination.total,
                'page': pagination.page,
                'per_page': pagination.per_page,
                'pages': pagination.pages
            }
        })

    except Exception as e:
        current_app.logger.error(f"获取导出列表失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


@export_bp.route('/delete/<int:export_id>', methods=['DELETE'])
def delete_export_record(export_id):
    """删除导出记录"""
    try:
        export_record = ExportRecord.query.get_or_404(export_id)

        # 从Minio删除文件（如果存在）
        if export_record.minio_path:
            ModelService.delete_from_minio(
                bucket_name="export-bucket",
                object_name=export_record.minio_path
            )

        # 删除数据库记录
        db.session.delete(export_record)
        db.session.commit()

        return jsonify({
            'code': 0,
            'msg': '导出记录已删除'
        })

    except Exception as e:
        current_app.logger.error(f"删除导出记录失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


@export_bp.route('/download/<int:export_id>')
def download_export(export_id):
    """下载导出的模型文件"""
    try:
        export_record = ExportRecord.query.get_or_404(export_id)

        if export_record.status != 'COMPLETED':
            return jsonify({
                'code': 400,
                'msg': '导出未完成，无法下载'
            }), 400

        if not export_record.minio_path:
            return jsonify({
                'code': 404,
                'msg': '文件路径不存在'
            }), 404

        # 创建临时文件
        if export_record.format == 'openvino':
            # OpenVINO格式：下载目录并打包为zip
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
            tmp_file.close()
            
            # 从Minio下载目录并打包
            success, error_msg = ModelService.download_directory_from_minio(
                bucket_name="export-bucket",
                object_prefix=export_record.minio_path,
                destination_zip_path=tmp_file.name
            )
            
            if success:
                # 生成zip文件名
                original_name = os.path.basename(export_record.minio_path.rstrip('/'))
                if not original_name.endswith('.zip'):
                    original_name = original_name + '.zip'
                
                # 发送zip文件
                return send_file(
                    tmp_file.name,
                    as_attachment=True,
                    download_name=original_name,
                    mimetype='application/zip'
                )
            else:
                # 如果文件不存在，更新导出记录状态为FAILED
                if error_msg and '不存在' in error_msg:
                    try:
                        export_record.status = 'FAILED'
                        export_record.message = f"文件在MinIO中不存在: {error_msg}"
                        db.session.commit()
                        current_app.logger.warning(f"导出记录 {export_id} 的文件不存在，已更新状态为FAILED")
                    except Exception as commit_error:
                        current_app.logger.error(f"更新导出记录状态失败: {str(commit_error)}")
                
                return jsonify({
                    'code': 404 if error_msg and '不存在' in error_msg else 500,
                    'msg': error_msg or '文件下载失败'
                }), 404 if error_msg and '不存在' in error_msg else 500
        else:
            # ONNX格式：下载单个文件
            tmp_file = tempfile.NamedTemporaryFile(delete=False)
            tmp_file.close()

            # 从Minio下载
            success, error_msg = ModelService.download_from_minio(
                    bucket_name="export-bucket",
                    object_name=export_record.minio_path,
                    destination_path=tmp_file.name
            )
            
            if success:
                # 获取原始文件名
                original_name = os.path.basename(export_record.minio_path)

                # 发送文件
                return send_file(
                    tmp_file.name,
                    as_attachment=True,
                    download_name=original_name,
                    mimetype=SUPPORTED_FORMATS.get(export_record.format, {}).get('mime', 'application/octet-stream')
                )
            else:
                # 如果文件不存在，更新导出记录状态为FAILED
                if error_msg and '不存在' in error_msg:
                    try:
                        export_record.status = 'FAILED'
                        export_record.message = f"文件在MinIO中不存在: {error_msg}"
                        db.session.commit()
                        current_app.logger.warning(f"导出记录 {export_id} 的文件不存在，已更新状态为FAILED")
                    except Exception as commit_error:
                        current_app.logger.error(f"更新导出记录状态失败: {str(commit_error)}")
                
                return jsonify({
                    'code': 404 if error_msg and '不存在' in error_msg else 500,
                    'msg': error_msg or '文件下载失败'
                }), 404 if error_msg and '不存在' in error_msg else 500

    except Exception as e:
        current_app.logger.error(f"文件下载失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500