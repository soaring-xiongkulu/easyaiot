import os
import tempfile

from flask import Blueprint, jsonify, current_app, url_for, send_file
from ultralytics import YOLO

from app.services.model_service import ModelService  # Minio操作类
from models import db, Model, ExportRecord, TrainingRecord

export_bp = Blueprint('export', __name__)

# 支持的导出格式映射
SUPPORTED_FORMATS = {
    'onnx': {'ext': '.onnx', 'mime': 'application/octet-stream'},
    'torchscript': {'ext': '.torchscript', 'mime': 'application/octet-stream'},
    'tensorrt': {'ext': '.engine', 'mime': 'application/octet-stream'},
    'openvino': {'ext': '_openvino_model/', 'mime': 'application/octet-stream'}
}


@export_bp.route('/api/model/<int:model_id>/export/<format>', methods=['POST'])
def api_export_model(model_id, format):
    try:
        # 验证格式支持
        if format not in SUPPORTED_FORMATS:
            return jsonify({'success': False, 'message': f'不支持的导出格式: {format}'}), 400

        # 获取模型信息
        model_record = Model.query.get_or_404(model_id)
        training_record = TrainingRecord.query.get(model_record.training_record_id)

        if not training_record or not training_record.minio_model_path:
            return jsonify({'success': False, 'message': '模型未发布或未上传到Minio'}), 400

        # 创建临时目录
        with tempfile.TemporaryDirectory() as tmp_dir:
            # 步骤1：从Minio下载原始模型
            minio_model_path = training_record.minio_model_path
            local_pt_path = os.path.join(tmp_dir, 'model.pt')

            if not ModelService.download_from_minio(
                    bucket_name="model-bucket",
                    object_name=minio_model_path,
                    destination_path=local_pt_path
            ):
                return jsonify({'success': False, 'message': '原始模型下载失败'}), 500

            # 步骤2：转换模型格式
            model = YOLO(local_pt_path)
            export_filename = f"model{SUPPORTED_FORMATS[format]['ext']}"
            export_local_path = os.path.join(tmp_dir, export_filename)

            # 执行模型导出
            export_params = {
                'format': format,
                'imgsz': 640,  # 根据需要调整
                'optimize': True if format == 'tensorrt' else False,
                'device': 'cpu'  # 或根据配置选择
            }

            # 特殊格式处理
            if format == 'openvino':
                export_params['half'] = False  # OpenVINO不支持FP16

            model.export(**export_params)

            # 重命名导出文件（YOLO导出有固定命名）
            exported_files = [f for f in os.listdir(tmp_dir) if
                              f.endswith(SUPPORTED_FORMATS[format]['ext']) or f.endswith('.engine')]
            if not exported_files:
                return jsonify({'success': False, 'message': '模型导出失败，未生成目标文件'}), 500

            if format != 'openvino':  # 目录格式特殊处理
                os.rename(os.path.join(tmp_dir, exported_files[0]), export_local_path)

            # 步骤3：上传到Minio
            minio_export_path = f"exports/model_{model_id}/{format}/{export_filename}"

            upload_success = False
            if format == 'openvino':
                # 处理目录上传
                openvino_dir = os.path.join(tmp_dir, exported_files[0])
                upload_success = ModelService.upload_directory_to_minio(
                    bucket_name="export-bucket",
                    object_prefix=minio_export_path.rstrip('/') + '/',
                    local_dir=openvino_dir
                )
            else:
                upload_success = ModelService.upload_to_minio(
                    bucket_name="export-bucket",
                    object_name=minio_export_path,
                    file_path=export_local_path
                )

            if not upload_success:
                return jsonify({'success': False, 'message': '导出模型上传失败'}), 500

            # 步骤4：保存导出记录
            export_record = ExportRecord(
                model_id=model_id,
                format=format,
                minio_path=minio_export_path,
                local_path=export_local_path if format != 'openvino' else openvino_dir
            )
            db.session.add(export_record)

            # 步骤5：更新模型表的对应字段
            if format == 'onnx':
                model_record.onnx_model_path = minio_export_path
            elif format == 'torchscript':
                model_record.torchscript_model_path = minio_export_path
            elif format == 'tensorrt':
                model_record.tensorrt_model_path = minio_export_path
            elif format == 'openvino':
                model_record.openvino_model_path = minio_export_path

            db.session.commit()

            # 步骤6：生成下载URL
            download_url = url_for('export.download_export', export_id=export_record.id)

            return jsonify({
                'success': True,
                'message': '模型导出并上传成功',
                'minio_path': minio_export_path,
                'download_url': download_url
            })

    except Exception as e:
        current_app.logger.error(f"模型导出失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'服务器内部错误: {str(e)}'
        }), 500


@export_bp.route('/download/export/<int:export_id>')
def download_export(export_id):
    export_record = ExportRecord.query.get_or_404(export_id)

    # 创建临时文件
    tmp_file = tempfile.NamedTemporaryFile(delete=False)

    # 从Minio下载
    if ModelService.download_from_minio(
            bucket_name="export-bucket",
            object_name=export_record.minio_path,
            destination_path=tmp_file.name
    ):
        # 发送文件
        return send_file(
            tmp_file.name,
            as_attachment=True,
            download_name=os.path.basename(export_record.minio_path),
            mimetype=SUPPORTED_FORMATS.get(export_record.format, {}).get('mime', 'application/octet-stream')
        )
    else:
        return "文件下载失败", 500
