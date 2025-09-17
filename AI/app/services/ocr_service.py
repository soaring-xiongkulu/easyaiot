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
        self.oss_bucket_name = "ocr-images"
        self._initialize_ocr_engine()

    def _initialize_ocr_engine(self):
        """初始化PaddleOCR引擎"""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))  # 当前文件所在目录
            det_model_dir = os.path.join(base_dir, "PaddleOCR", "PP-OCRv5_server_det")
            rec_model_dir = os.path.join(base_dir, "PaddleOCR", "PP-OCRv5_server_rec")

            # 确保目录存在，如果不存在，PaddleOCR 可能会尝试自动下载，但服务器模型较大，建议预先准备好
            if not os.path.exists(det_model_dir):
                print(f"警告: 检测模型目录不存在: {det_model_dir}")
                os.makedirs(det_model_dir, exist_ok=True)
            if not os.path.exists(rec_model_dir):
                print(f"警告: 识别模型目录不存在: {rec_model_dir}")
                os.makedirs(rec_model_dir, exist_ok=True)

            self.ocr_engine = PaddleOCR(
                text_recognition_model_name="PP-OCRv5_server_rec",  # 指定模型名称
                text_recognition_model_dir=rec_model_dir,  # 指定模型路径（绝对路径）
                text_detection_model_name="PP-OCRv5_server_det",
                text_detection_model_dir=det_model_dir,
                device="cpu",
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )
            print("PaddleOCR引擎初始化成功。")
        except Exception as e:
            print(f"PaddleOCR引擎初始化失败: {e}")
            raise e

    def recognize(self, image_path):
        """
        识别图片中的文字
        """
        if not self.ocr_engine:
            raise Exception("OCR引擎未初始化")

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        try:
            result = self.ocr_engine.ocr(image_path)  # 修改这里
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
            object_key = f"{unique_filename}"

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

    def execute_ocr(self, image_path: str) -> Dict[str, Any]:
        """
        执行OCR识别并格式化结果

        Args:
            image_path: 要识别的图像路径

        Returns:
            Dict[str, Any]: 结构化的OCR识别结果，包含文本行、完整文本和可能的错误信息
        """
        try:
            # 使用PaddleOCR进行识别
            raw_result = self.recognize(image_path)

            # 解析和格式化结果
            text_lines = []
            full_text = ""

            # 检查结果结构 (PaddleOCR返回结构可能是列表的列表)
            if raw_result and len(raw_result) > 0:
                # 遍历每个检测到的文本行
                for line_idx, line in enumerate(raw_result[0]):
                    if line and len(line) >= 2:
                        # 提取边界框坐标
                        bbox = line[0]
                        # 提取文本和置信度
                        text_info = line[1]
                        text = text_info[0]
                        confidence = float(text_info[1]) if len(text_info) > 1 else 0.0

                        # 创建标准化多边形坐标（如果可用）
                        polygon = []
                        if bbox and len(bbox) >= 4:
                            for point in bbox:
                                polygon.append([float(point[0]), float(point[1])])

                        # 添加到文本行列表
                        text_lines.append({
                            'text': text,
                            'confidence': confidence,
                            'bbox': bbox,
                            'polygon': polygon,
                            'page_num': 1,  # 单图像默认为第1页
                            'line_num': line_idx + 1,
                            'word_num': None  # 单词级编号可选
                        })

                        # 添加到完整文本
                        full_text += text + "\n"

            # 返回结构化的OCR结果
            return {
                "success": True,
                "text_lines": text_lines,
                "full_text": full_text.strip(),
                "total_lines": len(text_lines),
                "average_confidence": sum(line['confidence'] for line in text_lines) / len(
                    text_lines) if text_lines else 0
            }

        except FileNotFoundError as e:
            logger.error(f"图像文件未找到: {str(e)}")
            return {"error": f"图像文件未找到: {str(e)}", "success": False}
        except Exception as e:
            logger.error(f"OCR执行失败: {str(e)}")
            return {"error": f"OCR执行失败: {str(e)}", "success": False}

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