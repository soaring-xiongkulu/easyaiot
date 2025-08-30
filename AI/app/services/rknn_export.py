import logging
import os
import tempfile

from rknn.api import RKNN
from ultralytics import YOLO

from app.services.minio_service import ModelService
from models import ExportRecord

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