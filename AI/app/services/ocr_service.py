import datetime
import logging
import os
import uuid
from typing import Dict, List, Any, Optional, Tuple

import cv2
import numpy as np
from paddleocr import PaddleOCR

from app.services.minio_service import ModelService
from models import OCRResult, db

# 配置日志
logger = logging.getLogger(__name__)


class OCRService:
    def __init__(self,
                 rec_model_name: str = "PP-OCRv4_server_rec",
                 rec_model_dir: str = "pyModel/PP-OCRv4_server_rec",
                 det_model_name: str = "PP-OCRv4_server_det",
                 det_model_dir: str = "pyModel/PP-OCRv4_server_det",
                 lang: str = 'ch',
                 use_gpu: bool = False,
                 oss_bucket_name: str = 'ocr-images'):  # 新增OSS存储桶配置
        """
        初始化PaddleOCR服务

        Args:
            oss_bucket_name: OSS存储桶名称
        """
        self.ocr_engine = None
        self.rec_model_name = rec_model_name
        self.rec_model_dir = rec_model_dir
        self.det_model_name = det_model_name
        self.det_model_dir = det_model_dir
        self.lang = lang
        self.use_gpu = use_gpu
        self.oss_bucket_name = oss_bucket_name  # 新增
        self._initialize_ocr_engine()

    def _initialize_ocr_engine(self) -> None:
        """初始化PaddleOCR引擎"""
        try:
            self.ocr_engine = PaddleOCR(
                text_recognition_model_name=self.rec_model_name,
                text_recognition_model_dir=self.rec_model_dir,
                text_detection_model_name=self.det_model_name,
                text_detection_model_dir=self.det_model_dir,
                use_angle_cls=True,
                lang=self.lang,
                use_gpu=self.use_gpu,
                show_log=False,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False
            )
            logger.info("PaddleOCR引擎初始化成功")
        except Exception as e:
            logger.error(f"PaddleOCR引擎初始化失败: {e}")
            raise

    def execute_ocr(self, image_path: str, **kwargs) -> Dict[str, Any]:
        """
        执行OCR识别

        Args:
            image_path: 图像文件路径
            **kwargs: 额外参数（如use_angle_cls）

        Returns:
            Dict[str, Any]: OCR识别结果

        Raises:
            Exception: 当OCR识别失败时
        """
        try:
            # 检查图像是否能正常读取
            img = cv2.imread(image_path)
            if img is None:
                logger.error(f"图片读取失败: {image_path}")
                return {"error": "图片读取失败", "text_lines": []}

            # 执行OCR识别 - 使用predict方法（根据第一张图）
            result = self.ocr_engine.predict(image_path, cls=kwargs.get('use_angle_cls', True))

            # 处理识别结果
            processed_result = self._process_ocr_result(result)
            return processed_result

        except Exception as error:
            logger.error(f"OCR执行失败: {error}")
            raise

    def _process_ocr_result(self, result: List) -> Dict[str, Any]:
        """
        处理PaddleOCR返回的结果，转换为结构化数据

        Args:
            result: PaddleOCR原始结果

        Returns:
            Dict[str, Any]: 处理后的结构化结果
        """
        try:
            processed_result = {
                "text_lines": [],
                "confidence_avg": 0.0,
                "total_text_lines": 0
            }

            total_confidence = 0.0
            line_count = 0

            for page_idx, page in enumerate(result):
                for line_idx, line in enumerate(page):
                    if line and len(line) >= 2:
                        box, (text, confidence) = line[0], line[1]

                        # 处理文本行
                        text_line = {
                            "text": text,
                            "confidence": confidence,
                            "bbox": [box[0][0], box[0][1], box[2][0], box[2][1]],
                            "polygon": [[point[0], point[1]] for point in box],
                            "line_num": line_idx + 1,
                            "page_num": page_idx + 1,
                            "word_num": line_idx + 1  # 默认使用行号作为单词序号
                        }

                        processed_result["text_lines"].append(text_line)
                        total_confidence += confidence
                        line_count += 1

            # 计算平均置信度
            if line_count > 0:
                processed_result["confidence_avg"] = total_confidence / line_count
                processed_result["total_text_lines"] = line_count

            return processed_result

        except Exception as error:
            logger.error(f"处理OCR结果失败: {error}")
            return {"error": str(error), "text_lines": []}

    def upload_to_oss(self, image_path: str) -> Optional[str]:
        """
        上传图片到OSS

        Args:
            image_path: 本地图片路径

        Returns:
            str: OSS中的图片URL，失败返回None
        """
        try:
            # 生成唯一的文件名
            ext = os.path.splitext(image_path)[1]
            unique_filename = f"{uuid.uuid4().hex}{ext}"
            object_key = f"ocr-images/{unique_filename}"

            # 上传到OSS
            if ModelService.upload_to_minio(self.oss_bucket_name, object_key, image_path):
                # 按照指定结构生成访问URL
                image_url = f"/api/v1/buckets/{self.oss_bucket_name}/objects/download?prefix={object_key}"
                return image_url
            return None
        except Exception as e:
            logger.error(f"上传图片到OSS失败: {str(e)}")
            return None

    def save_ocr_results(self, image_path: str, ocr_results: Dict[str, Any], image_url: str = None) -> bool:
        """
        保存OCR识别结果到数据库（OCRResult表）

        Args:
            image_path: 图像文件路径，用于记录来源
            ocr_results: OCR识别结果
            image_url: OSS中的图片URL

        Returns:
            bool: 是否保存成功
        """
        try:
            if "text_lines" not in ocr_results:
                logger.error("OCR结果中缺少text_lines字段")
                return False

            for line_result in ocr_results["text_lines"]:
                ocr_result = OCRResult(
                    text=line_result.get('text', ''),
                    confidence=line_result.get('confidence', 0.0),
                    bbox=line_result.get('bbox', []),
                    polygon=line_result.get('polygon', []),
                    page_num=line_result.get('page_num', 1),
                    line_num=line_result.get('line_num'),
                    word_num=line_result.get('word_num'),
                    image_url=image_url,  # 新增OSS图片URL
                    created_at=datetime.datetime.utcnow()
                )
                db.session.add(ocr_result)

            db.session.commit()
            logger.info(f"OCR结果成功保存到数据库，共{len(ocr_results['text_lines'])}条记录")
            return True

        except Exception as error:
            db.session.rollback()
            logger.error(f"保存OCR结果失败: {error}")
            return False

    def process_image(self, image_path: str, save_to_db: bool = True, upload_to_oss: bool = True) -> Dict[str, Any]:
        """
        完整的OCR处理流程

        Args:
            image_path: 图像文件路径
            save_to_db: 是否保存结果到数据库
            upload_to_oss: 是否上传图片到OSS

        Returns:
            Dict[str, Any]: OCR处理结果
        """
        try:
            # 执行OCR识别
            ocr_results = self.execute_ocr(image_path)

            # 上传到OSS
            image_url = None
            if upload_to_oss:
                image_url = self.upload_to_oss(image_path)
                if image_url:
                    logger.info(f"图片已上传到OSS: {image_url}")
                else:
                    logger.warning("图片上传到OSS失败")

            # 保存到数据库
            if save_to_db and "error" not in ocr_results:
                self.save_ocr_results(image_path, ocr_results, image_url)

            # 在返回结果中添加OSS图片URL
            if "error" not in ocr_results:
                ocr_results["image_url"] = image_url

            return ocr_results

        except Exception as error:
            logger.error(f"处理图像失败: {error}")
            return {"error": str(error)}

    def verify_service_connectivity(self) -> Tuple[bool, str]:
        """
        验证PaddleOCR服务连接性

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            # 创建测试图像
            test_image = np.zeros((100, 100, 3), dtype=np.uint8)
            cv2.putText(test_image, "Test", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            # 保存临时图像
            temp_path = "/tmp/test_ocr.png"
            cv2.imwrite(temp_path, test_image)

            # 执行OCR
            result = self.execute_ocr(temp_path)
            if "error" in result:
                return False, f"连接测试失败: {result['error']}"
            return True, "PaddleOCR连接测试成功"

        except Exception as error:
            return False, f"连接测试失败: {str(error)}"

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        获取OCR服务的性能指标

        Returns:
            Dict[str, Any]: 性能指标字典
        """
        return {
            "engine_initialized": self.ocr_engine is not None,
            "rec_model_name": self.rec_model_name,
            "det_model_name": self.det_model_name,
            "lang": self.lang,
            "using_gpu": self.use_gpu
        }

    def preprocess_image(self, image_path: str, output_path: str = None) -> str:
        """
        图像预处理（可选），提高OCR识别率
        参考第四张图中的EasyOCR预处理方法

        Args:
            image_path: 输入图像路径
            output_path: 输出图像路径（可选）

        Returns:
            str: 处理后的图像路径
        """
        try:
            # 读取图像
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError("无法读取图像")

            # 转换为灰度图
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # 自适应阈值处理，提高文字对比度
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 25, 15
            )

            # 形态学操作（膨胀）
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
            binary = cv2.dilate(binary, kernel, iterations=1)

            # 保存处理后的图像
            if output_path is None:
                output_path = image_path.replace(".", "_preprocessed.")

            cv2.imwrite(output_path, binary)
            return output_path

        except Exception as error:
            logger.error(f"图像预处理失败: {error}")
            return image_path  # 失败时返回原图像路径