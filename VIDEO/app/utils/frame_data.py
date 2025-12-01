"""
帧数据结构 - 用于多摄像头帧传输
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import time
import numpy as np
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FrameData:
    """帧数据结构 - 用于在抽帧器、排序器、推送器之间传输"""
    
    # 基础信息
    device_id: str  # 摄像头ID
    task_id: int  # 算法任务ID
    frame_index: int  # 帧序号
    
    # 帧数据
    frame_data: Optional[np.ndarray] = None  # OpenCV帧数据(numpy数组)
    frame_bytes: Optional[bytes] = None  # 帧字节流(用于序列化传输)
    
    # 时间戳
    timestamp: float = field(default_factory=time.time)  # 时间戳(秒)
    capture_time: Optional[datetime] = None  # 捕获时间
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)  # 其他元数据
    
    # 算法处理结果
    detection_results: Optional[list] = None  # 检测结果列表
    confidence_scores: Optional[list] = None  # 置信度分数列表
    processed_frame: Optional[np.ndarray] = None  # 处理后的帧(带标注)
    
    # 状态标记
    is_processed: bool = False  # 是否已处理
    is_sorted: bool = False  # 是否已排序
    is_pushed: bool = False  # 是否已推送
    
    def __post_init__(self):
        """初始化后处理"""
        if self.capture_time is None:
            self.capture_time = datetime.fromtimestamp(self.timestamp)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典(用于序列化)"""
        return {
            'device_id': self.device_id,
            'task_id': self.task_id,
            'frame_index': self.frame_index,
            'timestamp': self.timestamp,
            'capture_time': self.capture_time.isoformat() if self.capture_time else None,
            'metadata': self.metadata,
            'detection_results': self.detection_results,
            'confidence_scores': self.confidence_scores,
            'is_processed': self.is_processed,
            'is_sorted': self.is_sorted,
            'is_pushed': self.is_pushed,
            # 注意: frame_data和frame_bytes不包含在字典中,需要单独处理
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FrameData':
        """从字典创建FrameData对象"""
        frame_data = cls(
            device_id=data['device_id'],
            task_id=data['task_id'],
            frame_index=data['frame_index'],
            timestamp=data.get('timestamp', time.time()),
            metadata=data.get('metadata', {}),
            detection_results=data.get('detection_results'),
            confidence_scores=data.get('confidence_scores'),
            is_processed=data.get('is_processed', False),
            is_sorted=data.get('is_sorted', False),
            is_pushed=data.get('is_pushed', False),
        )
        
        if data.get('capture_time'):
            frame_data.capture_time = datetime.fromisoformat(data['capture_time'])
        
        return frame_data
    
    def get_frame_for_processing(self) -> Optional[np.ndarray]:
        """获取用于处理的帧数据"""
        if self.frame_data is not None:
            return self.frame_data
        elif self.frame_bytes is not None:
            # 从字节流解码
            import cv2
            nparr = np.frombuffer(self.frame_bytes, np.uint8)
            self.frame_data = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return self.frame_data
        return None
    
    def set_frame_data(self, frame: np.ndarray):
        """设置帧数据"""
        self.frame_data = frame
        # 同时更新字节流(用于序列化)
        import cv2
        _, buffer = cv2.imencode('.jpg', frame)
        self.frame_bytes = buffer.tobytes()
    
    def get_max_confidence(self) -> float:
        """获取最大置信度"""
        if self.confidence_scores:
            return max(self.confidence_scores)
        return 0.0
    
    def has_detections(self) -> bool:
        """是否有检测结果"""
        return self.detection_results is not None and len(self.detection_results) > 0

