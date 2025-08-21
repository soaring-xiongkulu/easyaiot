import os
import tempfile
import logging
import numpy as np
from flask import Blueprint, jsonify, current_app, url_for, send_file, request
from ultralytics import YOLO
from rknn.api import RKNN
from app.services.model_service import ModelService
from models import db, Model, ExportRecord, TrainingRecord

export_bp = Blueprint('export', __name__)
logger = logging.getLogger(__name__)

# 扩展支持的导出格式映射（增加RKNN格式）
SUPPORTED_FORMATS = {
    'onnx': {'ext': '.onnx', 'mime': 'application/octet-stream'},
    'torchscript': {'ext': '.torchscript', 'mime': 'application/octet-stream'},
    'tensorrt': {'ext': '.engine', 'mime': 'application/octet-stream'},
    'openvino': {'ext': '_openvino_model/', 'mime': 'application/octet-stream'},
    'rknn': {'ext': '.rknn', 'mime': 'application/octet-stream'}  # 新增RKNN格式
}


class RknnExporter:
    """RKNN模型转换核心类"""

    # 默认转换配置（可通过请求参数覆盖）
    DEFAULT_CONFIG = {
        'target_platform': 'rk3588',
        'quantization': True,
        'optimization_level': 3,
        'mean_values': [[0, 0, 0]],
        'std_values': [[255, 255, 255]],
        'quantized_dtype': 'asymmetric_quantized-8',
        'img_size': 640,
        'opset': 12  # RKNN推荐opset版本[3](@ref)
    }

    @staticmethod
    def export_from_pytorch(model_id: int, pt_path: str, config: dict = None) -> ExportRecord:
        """
        从PyTorch模型导出RKNN格式（PT → ONNX → RKNN）
        关键技术点：
        1. 使用推荐opset 12确保兼容性[3](@ref)
        2. 动态处理YOLO模型输出层[2](@ref)
        """
        try:
            # 合并配置参数
            cfg = {**RknnExporter.DEFAULT_CONFIG, **(config or {})}

            # 创建临时目录
            with tempfile.TemporaryDirectory() as tmp_dir:
                # 步骤1：导出ONNX中间格式
                onnx_path = os.path.join(tmp_dir, f'model_{model_id}.onnx')
                model = YOLO(pt_path)

                # 导出ONNX（使用Ultralytics内置方法）
                model.export(
                    format='onnx',
                    imgsz=cfg['img_size'],
                    opset=cfg['opset'],  # 使用配置的opset版本
                    simplify=True,
                    dynamic=False
                )

                # 获取导出的ONNX文件（YOLO默认保存位置）
                exported_files = [f for f in os.listdir('.') if f.endswith('.onnx')]
                if exported_files:
                    latest_onnx = max(exported_files, key=os.path.getctime)
                    os.rename(latest_onnx, onnx_path)
                    logger.info(f"ONNX模型导出成功: {onnx_path}")
                else:
                    raise RuntimeError("ONNX导出失败，未找到生成文件")

                # 步骤2：执行RKNN转换
                return RknnExporter.export_from_onnx(model_id, onnx_path, cfg)

        except Exception as e:
            logger.error(f"PyTorch到RKNN转换失败: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def export_from_onnx(model_id: int, onnx_path: str, config: dict = None) -> ExportRecord:
        """执行ONNX到RKNN的转换"""
        rknn = None
        try:
            # 合并配置参数
            cfg = {**RknnExporter.DEFAULT_CONFIG, **(config or {})}

            # 初始化RKNN对象
            rknn = RKNN(verbose=True)
            logger.info(f"初始化RKNN成功, 版本: {rknn.version}")

            # 配置模型参数
            logger.info("配置RKNN参数...")
            config_result = rknn.config(
                mean_values=cfg['mean_values'],
                std_values=cfg['std_values'],
                target_platform=cfg['target_platform'],
                quantized_dtype=cfg['quantized_dtype'],
                optimization_level=cfg['optimization_level'],
                quant_img_RGB2BGR=False  # 保持RGB顺序[3](@ref)
            )
            if config_result != 0:
                raise RuntimeError(f"RKNN配置失败, 错误码: {config_result}")

            # 加载ONNX模型
            logger.info(f"加载ONNX模型: {onnx_path}")
            load_result = rknn.load_onnx(
                model=onnx_path,
                inputs=['images'],
                input_size_list=[[3, cfg['img_size'], cfg['img_size']]]
            )
            if load_result != 0:
                raise RuntimeError(f"ONNX加载失败, 错误码: {load_result}")

            # 构建RKNN模型
            logger.info("构建RKNN模型...")
            build_result = rknn.build(
                do_quantization=cfg['quantization'],
                dataset=cfg.get('dataset')  # 量化数据集路径（可选）
            )
            if build_result != 0:
                raise RuntimeError(f"模型构建失败, 错误码: {build_result}")

            # 导出RKNN文件
            rknn_path = os.path.join(tempfile.gettempdir(), f"model_{model_id}.rknn")
            export_result = rknn.export_rknn(rknn_path)
            if export_result != 0:
                raise RuntimeError(f"RKNN导出失败, 错误码: {export_result}")

            logger.info(f"RKNN模型导出成功: {rknn_path}")

            # 上传到Minio
            minio_path = f"exports/model_{model_id}/rknn/model_{model_id}.rknn"
            if not ModelService.upload_to_minio(
                    bucket_name="export-bucket",
                    object_name=minio_path,
                    file_path=rknn_path
            ):
                raise RuntimeError("Minio上传失败")

            # 创建导出记录
            return ExportRecord(
                model_id=model_id,
                format='rknn',
                minio_path=minio_path,
                local_path=rknn_path,
                export_params=str(config)  # 保存配置参数
            )

        except Exception as e:
            logger.error(f"RKNN转换失败: {str(e)}", exc_info=True)
            raise
        finally:
            # 确保释放资源
            if rknn:
                rknn.release()


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

        # 获取请求参数（RKNN需要额外配置）
        req_data = request.get_json() or {}
        rknn_config = {
            'target_platform': req_data.get('target_platform', 'rk3588'),
            'quantization': req_data.get('quantization', True),
            'img_size': req_data.get('img_size', 640),
            'dataset': req_data.get('dataset'),  # 量化数据集路径
            'opset': req_data.get('opset', 12)  # ONNX opset版本
        }

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

            # 特殊处理：RKNN格式
            if format == 'rknn':
                export_record = RknnExporter.export_from_pytorch(
                    model_id,
                    local_pt_path,
                    config=rknn_config
                )
            else:
                # 其他格式保持原有逻辑
                model = YOLO(local_pt_path)
                export_filename = f"model{SUPPORTED_FORMATS[format]['ext']}"
                export_local_path = os.path.join(tmp_dir, export_filename)

                # 执行模型导出
                export_params = {
                    'format': format,
                    'imgsz': rknn_config['img_size'],  # 使用配置的尺寸
                    'optimize': True if format == 'tensorrt' else False,
                    'device': 'cpu'
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

                # 创建导出记录
                export_record = ExportRecord(
                    model_id=model_id,
                    format=format,
                    minio_path=minio_export_path,
                    local_path=export_local_path if format != 'openvino' else openvino_dir
                )

            # 保存导出记录
            db.session.add(export_record)

            # 更新模型表的对应字段
            if format == 'onnx':
                model_record.onnx_model_path = export_record.minio_path
            elif format == 'torchscript':
                model_record.torchscript_model_path = export_record.minio_path
            elif format == 'tensorrt':
                model_record.tensorrt_model_path = export_record.minio_path
            elif format == 'openvino':
                model_record.openvino_model_path = export_record.minio_path
            elif format == 'rknn':  # 新增RKNN路径更新
                model_record.rknn_model_path = export_record.minio_path

            db.session.commit()

            # 生成下载URL
            download_url = url_for('export.download_export', export_id=export_record.id)

            return jsonify({
                'success': True,
                'message': '模型导出并上传成功',
                'minio_path': export_record.minio_path,
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
        return "文件下载失败", 500