"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import datetime
import logging
import os
import uuid
import threading
from typing import Optional, Dict, Any, Tuple, List
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2
import numpy as np
from paddleocr import PaddleOCR

from app.services.minio_service import ModelService
from db_models import OCRResult, db

logger = logging.getLogger(__name__)


class OCRService:
    def __init__(self):
        # 不再维护全局OCR引擎实例
        self.oss_bucket_name = "ocr-images"
        self.model_config = self._get_model_config()

        # 创建线程局部存储，确保每个线程有独立的OCR实例
        self.thread_local = threading.local()

    def _get_model_config(self) -> Dict[str, Any]:
        """获取模型配置"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        det_model_dir = os.path.join(base_dir, "PaddleOCR", "PP-OCRv5_server_det")
        rec_model_dir = os.path.join(base_dir, "PaddleOCR", "PP-OCRv5_server_rec")

        # 确保目录存在
        if not os.path.exists(det_model_dir):
            logger.warning(f"检测模型目录不存在: {det_model_dir}")
            os.makedirs(det_model_dir, exist_ok=True)
        if not os.path.exists(rec_model_dir):
            logger.warning(f"识别模型目录不存在: {rec_model_dir}")
            os.makedirs(rec_model_dir, exist_ok=True)

        return {
            'det_model_dir': det_model_dir,
            'rec_model_dir': rec_model_dir,
            'device': "cpu",
            'use_doc_orientation_classify': False,
            'use_doc_unwarping': False,
            'use_textline_orientation': False,
            'lang': "ch"
        }

    def _get_ocr_instance(self):
        """获取当前线程的OCR实例（线程安全）"""
        if not hasattr(self.thread_local, 'ocr_engine'):
            try:
                self.thread_local.ocr_engine = PaddleOCR(
                    text_recognition_model_name="PP-OCRv5_server_rec",
                    text_recognition_model_dir=self.model_config['rec_model_dir'],
                    text_detection_model_name="PP-OCRv5_server_det",
                    text_detection_model_dir=self.model_config['det_model_dir'],
                    device=self.model_config['device'],
                    use_doc_orientation_classify=self.model_config['use_doc_orientation_classify'],
                    use_doc_unwarping=self.model_config['use_doc_unwarping'],
                    use_textline_orientation=self.model_config['use_textline_orientation'],
                    lang=self.model_config['lang']
                )
                logger.info(f"线程 {threading.get_ident()} 创建了新的OCR实例")
            except Exception as e:
                logger.error(f"创建OCR实例失败: {e}")
                raise e
        return self.thread_local.ocr_engine

    def recognize(self, image_path):
        """
        识别图片中的文字（线程安全版本）
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        try:
            # 获取当前线程的OCR实例
            ocr_engine = self._get_ocr_instance()
            result = ocr_engine.ocr(image_path)
            return result
        except Exception as e:
            logger.error(f"OCR识别失败: {str(e)}")
            raise

    def process_image_batch(self, image_paths: List[str], max_workers: int = 4) -> Dict[str, Any]:
        """
        批量处理多张图片（线程安全的多线程实现）

        Args:
            image_paths: 图片路径列表
            max_workers: 最大线程数

        Returns:
            Dict[str, Any]: 处理结果汇总
        """
        all_results = {
            'success': True,
            'processed_count': 0,
            'failed_count': 0,
            'results': [],
            'errors': []
        }

        def process_single_image(image_path):
            """处理单张图片的线程函数"""
            try:
                ocr_result = self.execute_ocr(image_path)
                image_url = self.upload_to_oss(image_path)

                if ocr_result['success']:
                    self.save_ocr_results(image_path, ocr_result, image_url)

                return {
                    'image_path': image_path,
                    'ocr_result': ocr_result,
                    'image_url': image_url,
                    'status': 'success'
                }
            except Exception as e:
                logger.error(f"处理图片 {image_path} 失败: {str(e)}")
                return {
                    'image_path': image_path,
                    'error': str(e),
                    'status': 'failed'
                }

        # 使用线程池处理批量图片[2,4](@ref)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_image = {
                executor.submit(process_single_image, path): path
                for path in image_paths
            }

            # 处理完成的任务
            for future in as_completed(future_to_image):
                image_path = future_to_image[future]
                try:
                    result = future.result()
                    all_results['results'].append(result)

                    if result['status'] == 'success':
                        all_results['processed_count'] += 1
                    else:
                        all_results['failed_count'] += 1
                        all_results['errors'].append({
                            'image_path': image_path,
                            'error': result.get('error', 'Unknown error')
                        })
                except Exception as e:
                    logger.error(f"处理任务异常: {str(e)}")
                    all_results['failed_count'] += 1
                    all_results['errors'].append({
                        'image_path': image_path,
                        'error': str(e)
                    })

        return all_results

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
            upload_success, upload_error = ModelService.upload_to_minio(self.oss_bucket_name, object_key, image_path)
            if upload_success:
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
        执行OCR识别并返回格式化结果

        Args:
            image_path: 图像文件路径

        Returns:
            Dict[str, Any]: 包含文本行信息和完整文本的字典
        """
        try:
            # 预处理图像
            preprocessed_path = self.preprocess_image(image_path)

            # 使用预处理后的图像进行OCR
            raw_result = self.recognize(preprocessed_path)

            # 详细的空值检查和日志记录
            if not raw_result:
                logger.warning("OCR识别返回None结果")
                return {
                    "success": False,
                    "error": "OCR识别返回空结果",
                    "text_lines": [],
                    "full_text": "",
                    "total_lines": 0,
                    "average_confidence": 0
                }

            if len(raw_result) == 0:
                logger.warning("OCR识别返回空数组")
                return {
                    "success": True,
                    "text_lines": [],
                    "full_text": "",
                    "total_lines": 0,
                    "average_confidence": 0
                }

            # 获取JSON结果
            json_result = raw_result[0].json

            if not json_result:
                logger.warning("OCR返回的JSON结果为空")
                # 尝试直接解析raw_result的结构（兼容不同版本的PaddleOCR）
                if isinstance(raw_result[0], list):
                    logger.info("检测到旧版PaddleOCR结果格式，尝试兼容处理")
                    return self._parse_legacy_result(raw_result)

                return {
                    "success": True,
                    "text_lines": [],
                    "full_text": "",
                    "total_lines": 0,
                    "average_confidence": 0
                }

            # 提取OCR结果的核心数据
            ocr_data = json_result.get('res', {})

            # 检查关键数据是否存在
            rec_texts = ocr_data.get('rec_texts', [])
            rec_scores = ocr_data.get('rec_scores', [])
            rec_boxes = ocr_data.get('rec_boxes', [])
            rec_polys = ocr_data.get('rec_polys', [])

            if not rec_texts:
                logger.info("未识别到任何文本")
                return {
                    "success": True,
                    "text_lines": [],
                    "full_text": "",
                    "total_lines": 0,
                    "average_confidence": 0
                }

            # 构建文本行信息
            text_lines = []

            for i, (text, score) in enumerate(zip(rec_texts, rec_scores)):
                # 获取边界框坐标（转换为标准格式）
                bbox = rec_boxes[i] if i < len(rec_boxes) else []
                polygon = rec_polys[i] if i < len(rec_polys) else []

                # 构建文本行信息字典
                text_line = {
                    'text': text,
                    'confidence': float(score),
                    'bbox': bbox,
                    'polygon': polygon,
                    'page_num': 1,
                    'line_num': i + 1,  # 初始行号，排序后会更新
                    'word_num': 1
                }
                text_lines.append(text_line)

            # 根据坐标对文本行进行重新排序
            sorted_text_lines = self.sort_text_lines_by_coordinates(text_lines)

            # 构建完整文本（按正确顺序拼接）
            full_text = "".join(line['text'] for line in sorted_text_lines)

            # 计算平均置信度
            scores = [line['confidence'] for line in sorted_text_lines]
            avg_confidence = sum(scores) / len(scores) if scores else 0

            logger.info(f"成功识别 {len(sorted_text_lines)} 行文本，平均置信度: {avg_confidence:.4f}")

            # 返回结构化结果
            return {
                "success": True,
                "text_lines": sorted_text_lines,
                "full_text": full_text,
                "total_lines": len(sorted_text_lines),
                "average_confidence": avg_confidence
            }

        except FileNotFoundError as e:
            logger.error(f"图像文件未找到: {str(e)}")
            return {"error": f"图像文件未找到: {str(e)}", "success": False}
        except Exception as e:
            logger.error(f"OCR执行失败: {str(e)}")
            return {"error": f"OCR执行失败: {str(e)}", "success": False}

    def sort_text_lines_by_coordinates(self, text_lines, y_threshold=20):
        """
        根据文本框坐标对文本行进行重新排序（Z字形排序）

        Args:
            text_lines: 文本行列表
            y_threshold: Y坐标阈值，用于判断是否在同一行

        Returns:
            list: 按正确阅读顺序排序的文本行
        """
        if not text_lines:
            return []

        # 计算每个文本框的中心Y坐标
        text_lines_with_y = []
        for i, line in enumerate(text_lines):
            bbox = line.get('bbox', [])
            if len(bbox) >= 4:
                # 使用bbox的Y坐标计算中心点（bbox格式为[x1, y1, x2, y2]）
                center_y = (bbox[1] + bbox[3]) / 2
            else:
                # 如果没有bbox，使用polygon的第一个点的Y坐标
                polygon = line.get('polygon', [])
                if polygon and len(polygon) > 0:
                    center_y = polygon[0][1]  # 第一个点的Y坐标
                else:
                    center_y = i * 100  # 降级处理：按原始顺序

            text_lines_with_y.append({
                'line': line,
                'center_y': center_y,
                'bbox': bbox
            })

        # 按Y坐标初步排序
        pre_sorted = sorted(text_lines_with_y, key=lambda x: x['center_y'])

        # 分组和最终排序
        final_sorted = []
        current_group = []
        last_y = None

        for item in pre_sorted:
            current_y = item['center_y']

            if last_y is None or abs(current_y - last_y) <= y_threshold:
                # 如果Y坐标足够接近，添加到当前组（同一行）
                current_group.append(item)
            else:
                # 如果Y坐标相差较大，对当前组按X坐标排序并添加到最终列表
                current_group_sorted = sorted(current_group,
                                              key=lambda x: x['bbox'][0] if x['bbox'] and len(x['bbox']) >= 2 else 0)
                final_sorted.extend(current_group_sorted)
                current_group = [item]

            last_y = current_y

        # 处理最后一组
        if current_group:
            current_group_sorted = sorted(current_group,
                                          key=lambda x: x['bbox'][0] if x['bbox'] and len(x['bbox']) >= 2 else 0)
            final_sorted.extend(current_group_sorted)

        # 提取排序后的文本行，并更新行号
        sorted_lines = []
        for i, item in enumerate(final_sorted):
            line = item['line']
            line['line_num'] = i + 1  # 更新行号
            sorted_lines.append(line)

        return sorted_lines

    def _parse_legacy_result(self, raw_result):
        """
        处理旧版PaddleOCR结果格式（兼容性处理）
        """
        try:
            text_lines = []
            full_text = ""

            for line_idx, line in enumerate(raw_result[0]):
                if line and len(line) >= 2:
                    # 提取文本和置信度
                    text = line[1][0] if len(line[1]) > 0 else ""
                    confidence = float(line[1][1]) if len(line[1]) > 1 else 0.0

                    # 提取坐标信息
                    polygon = [list(map(int, point)) for point in line[0]] if line[0] else []

                    # 计算边界框
                    bbox = [float('inf'), float('inf'), 0, 0]  # x1, y1, x2, y2
                    for point in polygon:
                        bbox[0] = min(bbox[0], point[0])  # min x
                        bbox[1] = min(bbox[1], point[1])  # min y
                        bbox[2] = max(bbox[2], point[0])  # max x
                        bbox[3] = max(bbox[3], point[1])  # max y

                    text_line = {
                        'text': text,
                        'confidence': confidence,
                        'bbox': bbox,
                        'polygon': polygon,
                        'page_num': 1,
                        'line_num': line_idx + 1,
                        'word_num': 1
                    }
                    text_lines.append(text_line)
                    full_text += text + "\n"

            full_text = full_text.strip()

            return {
                "success": True,
                "text_lines": text_lines,
                "full_text": full_text,
                "total_lines": len(text_lines),
                "average_confidence": sum(line['confidence'] for line in text_lines) / len(
                    text_lines) if text_lines else 0
            }

        except Exception as e:
            logger.error(f"解析旧版OCR结果格式失败: {str(e)}")
            return {
                "success": False,
                "error": f"解析旧版OCR结果格式失败: {str(e)}",
                "text_lines": [],
                "full_text": "",
                "total_lines": 0,
                "average_confidence": 0
            }

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