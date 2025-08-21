import logging
import os
import tempfile

from rknn.api import RKNN

from app.services.model_service import ModelService
from models import ExportRecord

logger = logging.getLogger(__name__)

class RknnExporter:
    """RKNN模型转换核心类"""

    # 默认转换配置（可通过请求参数覆盖）
    DEFAULT_CONFIG = {
        'target_platform': 'rk3588',
        'quantization': True,
        'optimization_level': 3,
        'mean_values': [[0, 0, 0]],
        'std_values': [[255, 255, 255]],
        'quantized_dtype': 'asymmetric_quantized-8'
    }

    @staticmethod
    def export_from_onnx(model_id: int, onnx_path: str, config: dict = None) -> ExportRecord:
        """执行ONNX到RKNN的转换"""
        try:
            # 合并配置参数
            cfg = {**RknnExporter.DEFAULT_CONFIG, **(config or {})}

            # 创建临时目录
            with tempfile.TemporaryDirectory() as tmp_dir:
                # 步骤1：初始化RKNN对象
                rknn = RKNN(verbose=True)

                # 步骤2：配置模型参数
                rknn.config(
                    mean_values=cfg['mean_values'],
                    std_values=cfg['std_values'],
                    target_platform=cfg['target_platform'],
                    optimization_level=cfg['optimization_level'],
                    quantized_dtype=cfg['quantized_dtype']
                )

                # 步骤3：加载ONNX模型
                if rknn.load_onnx(
                        model=onnx_path,
                        inputs=['images'],
                        input_size_list=[[3, cfg.get('img_size', 640), cfg.get('img_size', 640)]]
                ) != 0:
                    raise RuntimeError("ONNX模型加载失败")

                # 步骤4：构建RKNN模型
                build_status = rknn.build(
                    do_quantization=cfg['quantization'],
                    dataset=cfg.get('dataset')  # 量化数据集路径（可选）
                )
                if build_status != 0:
                    raise RuntimeError(f"模型构建失败，错误码: {build_status}")

                # 步骤5：导出RKNN文件
                rknn_path = os.path.join(tmp_dir, f"model_{model_id}.rknn")
                if rknn.export_rknn(rknn_path) != 0:
                    raise RuntimeError("RKNN模型导出失败")

                # 步骤6：上传到Minio
                minio_path = f"exports/model_{model_id}/rknn/model_{model_id}.rknn"
                if not ModelService.upload_to_minio(
                        bucket_name="export-bucket",
                        object_name=minio_path,
                        file_path=rknn_path
                ):
                    raise RuntimeError("Minio上传失败")

                # 步骤7：创建导出记录
                return ExportRecord(
                    model_id=model_id,
                    format='rknn',
                    minio_path=minio_path,
                    local_path=rknn_path
                )

        except Exception as e:
            # 记录详细错误日志
            error_msg = f"RKNN转换失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise
        finally:
            # 确保释放资源
            if 'rknn' in locals():
                rknn.release()