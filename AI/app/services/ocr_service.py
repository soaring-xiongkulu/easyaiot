import datetime
import logging
import os
import uuid
from typing import Optional, Dict, Any, Tuple

import cv2
import numpy as np
from paddleocr import PaddleOCR

from app.services.minio_service import ModelService
from models import OCRResult, db

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        self.ocr_engine = None
        self._initialize_ocr_engine()

    def _initialize_ocr_engine(self):
        """
        初始化PaddleOCR引擎
        解决use_angle_cls和use_textline_orientation互斥问题
        """
        try:
            self.ocr_engine = PaddleOCR(
                text_recognition_model_name="PP-OCRv5_server_rec",
                text_recognition_model_dir="pyModel/PP-OCRv5_server_rec",
                text_detection_model_name="PP-OCRv5_server_det",
                text_detection_model_dir="pyModel/PP-OCRv5_server_det",
                device="cpu",
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )
            logger.info("PaddleOCR引擎初始化成功")
        except Exception as e:
            logger.error(f"PaddleOCR引擎初始化失败: {str(e)}")
            raise

    def recognize(self, image_path):
        """
        识别图片中的文字
        """
        if not self.ocr_engine:
            raise Exception("OCR引擎未初始化")
            
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
            
        try:
            result = self.ocr_engine.ocr(image_path, cls=True)
            return result
        except Exception as e:
            logger.error(f"OCR识别失败: {str(e)}")
            raise

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