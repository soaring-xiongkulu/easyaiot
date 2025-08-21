import os
import cv2
from ultralytics import YOLO
from flask import current_app
import tempfile
import shutil
from app.services.model_service import ProjectService


class InferenceService:
    def __init__(self, project_id):
        self.project_id = project_id
        self.project_model_dir = ProjectService.get_project_model_dir(project_id)
        self.project_dataset_dir = ProjectService.get_project_dataset_dir(project_id)
        ProjectService.ensure_project_model_dir(project_id)

    def get_system_model_path(self, model_name):
        """
        获取系统训练模型的路径
        
        Args:
            model_name (str): 模型文件名 (如 'best.pt', 'last.pt')
            
        Returns:
            str: 模型文件的完整路径
        """
        train_results_dir = os.path.join(self.project_dataset_dir, 'train_results', 'weights')
        model_path = os.path.join(train_results_dir, model_name)
        
        if os.path.exists(model_path):
            return model_path
        return None

    def save_uploaded_model(self, model_file):
        """
        保存上传的模型文件
        
        Args:
            model_file (FileStorage): 上传的模型文件
            
        Returns:
            str: 保存的模型文件路径
        """
        if not model_file or not model_file.filename:
            raise ValueError('未提供模型文件')
            
        filename = model_file.filename
        # 确保文件名安全
        from werkzeug.utils import secure_filename
        filename = secure_filename(filename)
        
        # 确保文件扩展名为.pt
        if not filename.endswith('.pt'):
            filename += '.pt' if '.' not in filename else ''
            
        model_path = os.path.join(self.project_model_dir, filename)
        model_file.save(model_path)
        
        # 确保文件已正确保存
        if not os.path.exists(model_path):
            raise ValueError('模型文件保存失败')
            
        return model_path

    def load_model(self, model_type, system_model=None, model_file=None):
        """
        加载模型
        
        Args:
            model_type (str): 模型类型 ('system' 或 'upload')
            system_model (str): 系统模型名称
            model_file (FileStorage): 上传的模型文件
            
        Returns:
            YOLO: 加载的模型对象
            
        Raises:
            ValueError: 当模型无法加载时抛出异常
        """
        model_path = None
        
        if model_type == 'system':
            if not system_model:
                raise ValueError('未指定系统模型')
            
            model_path = self.get_system_model_path(system_model)
            if not model_path:
                raise ValueError(f'系统模型 {system_model} 不存在')
        elif model_type == 'upload':
            if not model_file or not model_file.filename:
                raise ValueError('未提供上传的模型文件')
            
            model_path = self.save_uploaded_model(model_file)
        else:
            raise ValueError(f'不支持的模型类型: {model_type}')
        
        try:
            model = YOLO(model_path)
            return model
        except Exception as e:
            raise ValueError(f'模型加载失败: {str(e)}')

    def inference_image(self, model, image_file):
        """
        对图片进行推理
        
        Args:
            model (YOLO): YOLO模型对象
            image_file (FileStorage): 上传的图片文件
            
        Returns:
            dict: 推理结果
        """
        # 保存上传的图片到临时文件
        temp_dir = tempfile.mkdtemp()
        try:
            # 保存上传的图片
            image_path = os.path.join(temp_dir, image_file.filename)
            image_file.save(image_path)
            
            # 执行推理
            results = model(image_path)
            
            # 处理结果
            result = results[0]
            
            # 自定义绘制函数，添加对象编号
            def custom_plot(result, model_names):
                # 获取原始图像
                image = cv2.imread(image_path)
                
                # 统计每个类别的对象数量
                class_counts = {}
                
                if hasattr(result, 'boxes') and result.boxes is not None:
                    boxes = result.boxes
                    for box in boxes:
                        # 获取边界框坐标
                        xyxy = box.xyxy[0].cpu().numpy()
                        class_id = int(box.cls[0].cpu().numpy())
                        confidence = float(box.conf[0].cpu().numpy())
                        
                        # 获取类别名称
                        class_name = model_names[class_id] if class_id < len(model_names) else f"Class {class_id}"
                        
                        # 更新类别计数
                        if class_name not in class_counts:
                            class_counts[class_name] = 1
                        else:
                            class_counts[class_name] += 1
                            
                        object_number = class_counts[class_name]
                        
                        # 绘制边界框
                        x1, y1, x2, y2 = map(int, xyxy)
                        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        
                        # 准备标签文本
                        label = f"{class_name} #{object_number} {confidence:.2f}"
                        
                        # 计算标签尺寸并绘制标签背景
                        (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                        cv2.rectangle(image, (x1, y1 - text_height - baseline - 2), 
                                    (x1 + text_width, y1), (0, 255, 0), -1)
                        
                        # 绘制标签文本
                        cv2.putText(image, label, (x1, y1 - baseline), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                
                return image
            
            # 保存带有标注的结果图片
            result_image_path = os.path.join(temp_dir, 'result_' + image_file.filename)
            plotted_image = custom_plot(result, model.names)
            cv2.imwrite(result_image_path, plotted_image)
            
            # 复制结果图片到静态目录
            static_result_dir = os.path.join(current_app.root_path, 'static', 'inference_results', str(self.project_id))
            os.makedirs(static_result_dir, exist_ok=True)
            result_filename = f"inference_result_{os.path.splitext(image_file.filename)[0]}.jpg"
            final_result_path = os.path.join(static_result_dir, result_filename)
            shutil.copy2(result_image_path, final_result_path)
            
            # 提取检测框信息
            detections = []
            class_counts = {}
            if hasattr(result, 'boxes') and result.boxes is not None:
                boxes = result.boxes
                for i, box in enumerate(boxes):
                    # 获取边界框坐标
                    xyxy = box.xyxy[0].cpu().numpy()
                    class_id = int(box.cls[0].cpu().numpy())
                    confidence = float(box.conf[0].cpu().numpy())
                    
                    # 获取类别名称
                    class_name = model.names[class_id] if class_id < len(model.names) else f"Class {class_id}"
                    
                    # 更新类别计数
                    if class_name not in class_counts:
                        class_counts[class_name] = 1
                    else:
                        class_counts[class_name] += 1
                        
                    object_number = class_counts[class_name]
                    
                    detections.append({
                        'box': {
                            'x1': float(xyxy[0]),
                            'y1': float(xyxy[1]),
                            'x2': float(xyxy[2]),
                            'y2': float(xyxy[3])
                        },
                        'class_id': class_id,
                        'class_name': class_name,
                        'confidence': confidence,
                        'object_number': object_number
                    })
            
            return {
                'type': 'image',
                'image_url': f"/data/inference_results/{self.project_id}/{result_filename}",
                'detections': detections
            }
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)

    def inference_video(self, model, video_file):
        """
        对视频进行推理
        
        Args:
            model (YOLO): YOLO模型对象
            video_file (FileStorage): 上传的视频文件
            
        Returns:
            dict: 推理结果信息
        """
        # 创建临时目录保存处理过程中的文件
        temp_dir = tempfile.mkdtemp()
        try:
            # 保存上传的视频
            video_filename = video_file.filename
            video_path = os.path.join(temp_dir, video_filename)
            video_file.save(video_path)
            
            # 打开视频文件
            cap = cv2.VideoCapture(video_path)
            
            # 获取视频属性
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # 创建输出视频文件
            output_filename = f"result_{os.path.splitext(video_filename)[0]}.mp4"
            output_path = os.path.join(temp_dir, output_filename)
            
            # 创建视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            # 处理视频帧
            frame_count = 0
            detection_results = []
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 每隔一定帧数进行推理以提高性能
                if frame_count % 5 == 0:  # 每5帧处理一次
                    # 执行推理
                    results = model(frame)
                    result = results[0]
                    
                    # 在帧上绘制检测结果
                    plotted_frame = result.plot()
                    
                    # 提取检测信息
                    frame_detections = []
                    if hasattr(result, 'boxes') and result.boxes is not None:
                        boxes = result.boxes
                        for i, box in enumerate(boxes):
                            # 获取边界框坐标
                            xyxy = box.xyxy[0].cpu().numpy()
                            class_id = int(box.cls[0].cpu().numpy())
                            confidence = float(box.conf[0].cpu().numpy())
                            
                            # 获取类别名称
                            class_name = model.names[class_id] if class_id < len(model.names) else f"Class {class_id}"
                            
                            frame_detections.append({
                                'box': {
                                    'x1': float(xyxy[0]),
                                    'y1': float(xyxy[1]),
                                    'x2': float(xyxy[2]),
                                    'y2': float(xyxy[3])
                                },
                                'class_id': class_id,
                                'class_name': class_name,
                                'confidence': confidence
                            })
                    
                    detection_results.append({
                        'frame': frame_count,
                        'detections': frame_detections
                    })
                    
                    # 写入处理后的帧
                    out.write(plotted_frame)
                else:
                    # 直接写入原始帧
                    out.write(frame)
                
                frame_count += 1
            
            # 释放资源
            cap.release()
            out.release()
            
            # 复制结果视频到静态目录
            static_result_dir = os.path.join(current_app.root_path, 'static', 'inference_results', str(self.project_id))
            os.makedirs(static_result_dir, exist_ok=True)
            final_result_path = os.path.join(static_result_dir, output_filename)
            shutil.copy2(output_path, final_result_path)
            
            return {
                'type': 'video',
                'video_url': f"/data/inference_results/{self.project_id}/{output_filename}",
                'total_frames': total_frames,
                'processed_frames': frame_count,
                'fps': fps,
                'detection_results': detection_results
            }
        except Exception as e:
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise Exception(f"视频推理失败: {str(e)}")
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)

    def inference_rtsp(self, model, rtsp_url):
        """
        对RTSP流进行推理
        
        Args:
            model (YOLO): YOLO模型对象
            rtsp_url (str): RTSP流地址
            
        Returns:
            dict: 推理结果信息
        """
        # 创建临时目录保存处理过程中的文件
        temp_dir = tempfile.mkdtemp()
        try:
            # 打开RTSP流
            cap = cv2.VideoCapture(rtsp_url)
            
            # 检查流是否成功打开
            if not cap.isOpened():
                raise Exception("无法打开RTSP流")
            
            # 获取流属性
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 30  # 默认FPS
            
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # 创建输出视频文件（保存为MP4）
            output_filename = f"rtsp_result_{int(cv2.getTickCount())}.mp4"
            output_path = os.path.join(temp_dir, output_filename)
            
            # 创建视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            # 处理视频帧（限制处理帧数以避免无限循环）
            frame_count = 0
            max_frames = 300  # 最多处理300帧
            detection_results = []
            
            while frame_count < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 每隔一定帧数进行推理以提高性能
                if frame_count % 5 == 0:  # 每5帧处理一次
                    # 执行推理
                    results = model(frame)
                    result = results[0]
                    
                    # 在帧上绘制检测结果
                    plotted_frame = result.plot()
                    
                    # 提取检测信息
                    frame_detections = []
                    if hasattr(result, 'boxes') and result.boxes is not None:
                        boxes = result.boxes
                        for i, box in enumerate(boxes):
                            # 获取边界框坐标
                            xyxy = box.xyxy[0].cpu().numpy()
                            class_id = int(box.cls[0].cpu().numpy())
                            confidence = float(box.conf[0].cpu().numpy())
                            
                            # 获取类别名称
                            class_name = model.names[class_id] if class_id < len(model.names) else f"Class {class_id}"
                            
                            frame_detections.append({
                                'box': {
                                    'x1': float(xyxy[0]),
                                    'y1': float(xyxy[1]),
                                    'x2': float(xyxy[2]),
                                    'y2': float(xyxy[3])
                                },
                                'class_id': class_id,
                                'class_name': class_name,
                                'confidence': confidence
                            })
                    
                    detection_results.append({
                        'frame': frame_count,
                        'detections': frame_detections
                    })
                    
                    # 写入处理后的帧
                    out.write(plotted_frame)
                else:
                    # 直接写入原始帧
                    out.write(frame)
                
                frame_count += 1
            
            # 释放资源
            cap.release()
            out.release()
            
            # 如果没有处理任何帧，抛出异常
            if frame_count == 0:
                raise Exception("未能从RTSP流读取任何帧")
            
            # 复制结果视频到静态目录
            static_result_dir = os.path.join(current_app.root_path, 'static', 'inference_results', str(self.project_id))
            os.makedirs(static_result_dir, exist_ok=True)
            final_result_path = os.path.join(static_result_dir, output_filename)
            shutil.copy2(output_path, final_result_path)
            
            return {
                'type': 'rtsp',
                'video_url': f"/data/inference_results/{self.project_id}/{output_filename}",
                'processed_frames': frame_count,
                'fps': fps,
                'detection_results': detection_results
            }
        except Exception as e:
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise Exception(f"RTSP流推理失败: {str(e)}")
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)

    def check_system_models(self):
        """
        检查系统训练的模型是否存在
        
        Returns:
            dict: 包含best.pt和last.pt模型存在状态的字典
        """
        train_results_dir = os.path.join(self.project_dataset_dir, 'train_results', 'weights')
        
        return {
            'best_model_exists': os.path.exists(os.path.join(train_results_dir, 'best.pt')),
            'last_model_exists': os.path.exists(os.path.join(train_results_dir, 'last.pt'))
        }