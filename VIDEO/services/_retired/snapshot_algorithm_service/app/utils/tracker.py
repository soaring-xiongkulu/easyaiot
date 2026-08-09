"""
目标追踪器工具类
基于框相似度算法匹配，不依赖识别结果
"""
import time
import threading
import numpy as np
from typing import List, Dict, Optional


class SimpleTracker:
    """目标追踪器，使用框近似度算法匹配，不依赖识别结果"""
    
    def __init__(self, similarity_threshold=0.2, max_age=25, smooth_alpha=0.25, 
                 center_similarity_threshold=150, leave_time_threshold=0.5, leave_percent_threshold=0.0):
        """
        初始化追踪器
        
        Args:
            similarity_threshold: 框相似度匹配阈值
            max_age: 追踪目标最大存活帧数（未匹配时保留的帧数）
            smooth_alpha: 框位置平滑系数（0-1），值越大越平滑
            center_similarity_threshold: 中心点相似度阈值（像素）
            leave_time_threshold: 确认物体离开所需的时间阈值（秒）
            leave_percent_threshold: 确认物体离开时所需的检测比
        """
        self.similarity_threshold = similarity_threshold
        self.max_age = max_age
        self.smooth_alpha = smooth_alpha
        self.center_similarity_threshold = center_similarity_threshold
        self.leave_time_threshold = leave_time_threshold
        self.leave_percent_threshold = leave_percent_threshold
        self.tracks = {}  # {track_id: {'bbox': [x1, y1, x2, y2], 'class_id': int, 'class_name': str, 'confidence': float, 'age': int, 'last_seen': int, 'first_seen_time': float, 'leave_time': float, 'ex_trace_count': int, 'total_trace_count': int, 'last_trace_time': float, 'velocity': [vx, vy], 'last_bbox': [x1, y1, x2, y2]}}
        self.next_id = 1  # 下一个追踪ID
        self.lock = threading.Lock()
    
    def calculate_box_similarity(self, box1, box2):
        """计算两个框的相似度（基于IOU、中心点距离、形状相似度）"""
        xmin1, ymin1, xmax1, ymax1 = box1
        xmin2, ymin2, xmax2, ymax2 = box2
        w1, h1, w2, h2 = xmax1 - xmin1, ymax1 - ymin1, xmax2 - xmin2, ymax2 - ymin2
        
        # 计算IOU
        inter = max(0, min(xmax1, xmax2) - max(xmin1, xmin2)) * max(0, min(ymax1, ymax2) - max(ymin1, ymin2))
        union = w1 * h1 + w2 * h2 - inter
        if inter <= 0 or union <= 0:
            iou = 0
        else:
            iou = inter / union
        
        # 计算包围框
        xmin = min(xmin1, xmin2)
        ymin = min(ymin1, ymin2)
        xmax = max(xmax1, xmax2)
        ymax = max(ymax1, ymax2)
        w, h = xmax - xmin, ymax - ymin
        
        # 中心点距离相似度（0~1）
        try:
            center1_x = (xmin1 + xmax1) / 2
            center1_y = (ymin1 + ymax1) / 2
            center2_x = (xmin2 + xmax2) / 2
            center2_y = (ymin2 + ymax2) / 2
            center_distance = np.sqrt((center1_x - center2_x) ** 2 + (center1_y - center2_y) ** 2)
            diagonal = np.sqrt(w ** 2 + h ** 2)
            if diagonal > 0:
                normalized_distance = center_distance / (diagonal * 1.5)
                dis_sim = max(0, 1 - normalized_distance)
            else:
                dis_sim = 1
        except (ZeroDivisionError, ValueError):
            dis_sim = 1
        
        # 形状相似度
        try:
            if w > 0 and h > 0:
                width_diff = abs(w1 - w2) / max(w, 1)
                height_diff = abs(h1 - h2) / max(h, 1)
                shape_sim = 1 - (width_diff + height_diff) / 2
                shape_sim = max(0, shape_sim)
            else:
                shape_sim = 1
        except (ZeroDivisionError, ValueError):
            shape_sim = 1
        
        # 综合相似度：IOU * 0.6 + 中心点距离 * 0.35 + 形状 * 0.05
        return iou * 0.6 + dis_sim * 0.35 + shape_sim * 0.05
    
    def update(self, detections: List[Dict], frame_number: int, current_time: Optional[float] = None) -> List[Dict]:
        """
        更新追踪器，匹配检测结果和已有追踪目标
        
        Args:
            detections: 当前帧的检测结果列表，每个元素包含 'bbox', 'class_id', 'class_name', 'confidence'
            frame_number: 当前帧号
            current_time: 当前时间戳（秒），如果为None则使用time.time()
        
        Returns:
            tracked_detections: 带追踪ID的检测结果列表，包含时间信息
        """
        if current_time is None:
            current_time = time.time()
        
        with self.lock:
            # 更新所有追踪目标的age和检测计数
            tracks_to_remove = []
            for track_id, track in self.tracks.items():
                track['age'] += 1
                track['total_trace_count'] = track.get('total_trace_count', 0) + 1
                
                if track['age'] > self.max_age:
                    tracks_to_remove.append(track_id)
                    continue
                
                # 基于时间阈值和检测比判断离开
                last_trace_time = track.get('last_trace_time', current_time)
                if current_time - last_trace_time > self.leave_time_threshold:
                    ex_trace_count = track.get('ex_trace_count', 0)
                    total_trace_count = track.get('total_trace_count', 1)
                    trace_percent = ex_trace_count / total_trace_count if total_trace_count > 0 else 0
                    
                    if trace_percent <= self.leave_percent_threshold:
                        track['leave_time'] = current_time
                        tracks_to_remove.append(track_id)
                        continue
                    
                    # 重置计数器
                    track['ex_trace_count'] = 0
                    track['total_trace_count'] = 0
                    track['last_trace_time'] = current_time
            
            # 删除标记为删除的追踪目标
            for track_id in tracks_to_remove:
                del self.tracks[track_id]
            
            # 如果没有检测结果，返回缓存的追踪目标
            if not detections:
                tracked_detections = []
                for track_id, track in self.tracks.items():
                    first_seen_time = track.get('first_seen_time', current_time)
                    duration = current_time - first_seen_time
                    tracked_detections.append({
                        'track_id': track_id,
                        'bbox': track['bbox'],
                        'class_id': track['class_id'],
                        'class_name': track['class_name'],
                        'confidence': track['confidence'],
                        'is_cached': True,
                        'first_seen_time': first_seen_time,
                        'duration': duration
                    })
                return tracked_detections
            
            # 匹配检测结果和已有追踪目标
            matched_tracks = set()
            matched_detections = set()
            tracked_detections = []
            
            # 对每个检测结果，找到最佳匹配的追踪目标
            for det_idx, detection in enumerate(detections):
                best_similarity = 0
                best_track_id = None
                
                bbox = detection['bbox']
                det_center = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
                
                for track_id, track in self.tracks.items():
                    if track_id in matched_tracks:
                        continue
                    
                    # 方法1：直接使用当前框位置计算相似度
                    similarity1 = self.calculate_box_similarity(bbox, track['bbox'])
                    
                    # 方法2：如果目标有速度信息，使用预测位置计算相似度
                    similarity2 = similarity1
                    if 'velocity' in track and track['velocity'] is not None:
                        vx, vy = track['velocity']
                        predicted_bbox = [
                            int(track['bbox'][0] + vx),
                            int(track['bbox'][1] + vy),
                            int(track['bbox'][2] + vx),
                            int(track['bbox'][3] + vy)
                        ]
                        similarity2 = self.calculate_box_similarity(bbox, predicted_bbox)
                    
                    # 方法3：基于中心点距离的快速匹配
                    similarity3 = similarity1
                    if 'last_bbox' in track and track['last_bbox'] is not None:
                        track_center = ((track['bbox'][0] + track['bbox'][2]) / 2,
                                       (track['bbox'][1] + track['bbox'][3]) / 2)
                        center_distance = np.sqrt((det_center[0] - track_center[0]) ** 2 + 
                                                  (det_center[1] - track_center[1]) ** 2)
                        if center_distance <= self.center_similarity_threshold:
                            distance_bonus = max(0, 0.3 * (1 - center_distance / self.center_similarity_threshold))
                            similarity3 = min(1.0, similarity1 + distance_bonus)
                    
                    similarity = max(similarity1, similarity2, similarity3)
                    
                    if similarity > best_similarity and similarity >= self.similarity_threshold:
                        best_similarity = similarity
                        best_track_id = track_id
                
                if best_track_id is not None:
                    # 匹配成功，更新追踪目标
                    matched_tracks.add(best_track_id)
                    matched_detections.add(det_idx)
                    
                    track = self.tracks[best_track_id]
                    old_bbox = track['bbox']
                    new_bbox = bbox
                    smoothed_bbox = [
                        int(old_bbox[0] * self.smooth_alpha + new_bbox[0] * (1 - self.smooth_alpha)),
                        int(old_bbox[1] * self.smooth_alpha + new_bbox[1] * (1 - self.smooth_alpha)),
                        int(old_bbox[2] * self.smooth_alpha + new_bbox[2] * (1 - self.smooth_alpha)),
                        int(old_bbox[3] * self.smooth_alpha + new_bbox[3] * (1 - self.smooth_alpha))
                    ]
                    
                    # 计算速度
                    if 'last_bbox' in track and track['last_bbox'] is not None:
                        old_center = ((old_bbox[0] + old_bbox[2]) / 2, (old_bbox[1] + old_bbox[3]) / 2)
                        new_center = ((new_bbox[0] + new_bbox[2]) / 2, (new_bbox[1] + new_bbox[3]) / 2)
                        velocity_alpha = 0.7
                        if 'velocity' in track and track['velocity'] is not None:
                            old_velocity = track['velocity']
                            new_velocity = [
                                old_velocity[0] * velocity_alpha + (new_center[0] - old_center[0]) * (1 - velocity_alpha),
                                old_velocity[1] * velocity_alpha + (new_center[1] - old_center[1]) * (1 - velocity_alpha)
                            ]
                        else:
                            new_velocity = [new_center[0] - old_center[0], new_center[1] - old_center[1]]
                        track['velocity'] = new_velocity
                    else:
                        track['velocity'] = [0, 0]
                    
                    track['last_bbox'] = old_bbox.copy()
                    first_seen_time = track.get('first_seen_time', current_time)
                    
                    track['bbox'] = smoothed_bbox
                    track['class_id'] = detection['class_id']
                    track['class_name'] = detection['class_name']
                    track['confidence'] = detection['confidence']
                    track['age'] = 0
                    track['last_seen'] = frame_number
                    track['first_seen_time'] = first_seen_time
                    track['ex_trace_count'] = track.get('ex_trace_count', 0) + 1
                    track['last_trace_time'] = current_time
                    
                    duration = current_time - first_seen_time
                    tracked_detections.append({
                        'track_id': best_track_id,
                        'bbox': smoothed_bbox,
                        'class_id': detection['class_id'],
                        'class_name': detection['class_name'],
                        'confidence': detection['confidence'],
                        'is_cached': False,
                        'first_seen_time': first_seen_time,
                        'duration': duration
                    })
                else:
                    # 未匹配，创建新的追踪目标
                    new_track_id = self.next_id
                    self.next_id += 1
                    
                    self.tracks[new_track_id] = {
                        'bbox': bbox,
                        'class_id': detection['class_id'],
                        'class_name': detection['class_name'],
                        'confidence': detection['confidence'],
                        'age': 0,
                        'last_seen': frame_number,
                        'first_seen_time': current_time,
                        'ex_trace_count': 1,
                        'total_trace_count': 1,
                        'last_trace_time': current_time,
                        'velocity': [0, 0],
                        'last_bbox': None
                    }
                    
                    tracked_detections.append({
                        'track_id': new_track_id,
                        'bbox': bbox,
                        'class_id': detection['class_id'],
                        'class_name': detection['class_name'],
                        'confidence': detection['confidence'],
                        'is_cached': False,
                        'first_seen_time': current_time,
                        'duration': 0.0
                    })
            
            # 对于未匹配的追踪目标，也添加到结果中
            for track_id, track in self.tracks.items():
                if track_id not in matched_tracks:
                    first_seen_time = track.get('first_seen_time', current_time)
                    duration = current_time - first_seen_time
                    tracked_detections.append({
                        'track_id': track_id,
                        'bbox': track['bbox'],
                        'class_id': track['class_id'],
                        'class_name': track['class_name'],
                        'confidence': track['confidence'],
                        'is_cached': True,
                        'first_seen_time': first_seen_time,
                        'duration': duration
                    })
            
            return tracked_detections
    
    def get_all_tracks(self, current_time: Optional[float] = None, frame_number: Optional[int] = None) -> List[Dict]:
        """获取所有当前追踪目标的缓存框信息"""
        if current_time is None:
            current_time = time.time()
        
        tracked_detections = []
        with self.lock:
            tracks_to_remove = []
            for track_id, track in self.tracks.items():
                if track['age'] > self.max_age:
                    tracks_to_remove.append(track_id)
            
            for track_id in tracks_to_remove:
                del self.tracks[track_id]
            
            for track_id, track in self.tracks.items():
                first_seen_time = track.get('first_seen_time', current_time)
                duration = current_time - first_seen_time
                tracked_detections.append({
                    'track_id': track_id,
                    'bbox': track['bbox'].copy(),
                    'class_id': track['class_id'],
                    'class_name': track['class_name'],
                    'confidence': track['confidence'],
                    'is_cached': True,
                    'first_seen_time': first_seen_time,
                    'duration': duration
                })
        
        return tracked_detections
    
    def get_tracks_for_save(self) -> List[Dict]:
        """获取需要保存到数据库的追踪目标（已离开的目标）"""
        with self.lock:
            tracks_to_save = []
            for track_id, track in self.tracks.items():
                if 'leave_time' in track and track['leave_time']:
                    tracks_to_save.append({
                        'track_id': track_id,
                        'class_id': track.get('class_id'),
                        'class_name': track.get('class_name'),
                        'first_seen_time': track.get('first_seen_time'),
                        'leave_time': track.get('leave_time'),
                        'duration': track.get('leave_time', 0) - track.get('first_seen_time', 0),
                        'first_seen_frame': track.get('first_seen_frame'),
                        'last_seen_frame': track.get('last_seen'),
                        'total_detections': track.get('total_trace_count', 0)
                    })
            return tracks_to_save

