"""
帧队列管理器 - 管理抽帧器、排序器、推送器的内存队列
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import threading
from collections import defaultdict
from queue import Queue, Empty
from typing import Optional, Dict, List
from app.utils.frame_data import FrameData

logger = logging.getLogger(__name__)


class FrameQueueManager:
    """帧队列管理器 - 管理3个内存队列(抽帧器、排序器、推送器)"""
    
    def __init__(self, max_size: int = 1000):
        """
        初始化队列管理器
        
        Args:
            max_size: 每个队列的最大容量
        """
        self.max_size = max_size
        
        # 3个主队列
        self.extractor_queue = Queue(maxsize=max_size)  # 抽帧器队列
        self.sorter_queue = Queue(maxsize=max_size)  # 排序器队列
        self.pusher_queue = Queue(maxsize=max_size)  # 推送器队列
        
        # 按设备ID分组的队列(用于统计和监控)
        self.device_queues: Dict[str, Dict[str, Queue]] = defaultdict(lambda: {
            'extractor': Queue(maxsize=max_size),
            'sorter': Queue(maxsize=max_size),
            'pusher': Queue(maxsize=max_size)
        })
        
        # 线程锁
        self._lock = threading.RLock()
        
        # 统计信息
        self.stats = {
            'extractor_queue_size': 0,
            'sorter_queue_size': 0,
            'pusher_queue_size': 0,
            'total_frames_processed': 0,
            'total_frames_sorted': 0,
            'total_frames_pushed': 0,
            'device_stats': defaultdict(lambda: {
                'extractor_count': 0,
                'sorter_count': 0,
                'pusher_count': 0
            })
        }
    
    def put_to_extractor_queue(self, frame_data: FrameData, block: bool = True, timeout: Optional[float] = None) -> bool:
        """
        将帧数据放入抽帧器队列
        
        Args:
            frame_data: 帧数据对象
            block: 是否阻塞
            timeout: 超时时间(秒)
        
        Returns:
            bool: 是否成功
        """
        try:
            self.extractor_queue.put(frame_data, block=block, timeout=timeout)
            # 同时放入设备特定队列
            device_queue = self.device_queues[frame_data.device_id]['extractor']
            device_queue.put(frame_data, block=False)
            
            with self._lock:
                self.stats['extractor_queue_size'] = self.extractor_queue.qsize()
                self.stats['device_stats'][frame_data.device_id]['extractor_count'] += 1
            
            logger.debug(f"帧数据已放入抽帧器队列: device_id={frame_data.device_id}, frame_index={frame_data.frame_index}")
            return True
        except Exception as e:
            logger.error(f"放入抽帧器队列失败: {str(e)}", exc_info=True)
            return False
    
    def get_from_extractor_queue(self, device_id: Optional[str] = None, block: bool = True, timeout: Optional[float] = None) -> Optional[FrameData]:
        """
        从抽帧器队列获取帧数据
        
        Args:
            device_id: 设备ID(如果指定,则从设备特定队列获取)
            block: 是否阻塞
            timeout: 超时时间(秒)
        
        Returns:
            FrameData: 帧数据对象,如果队列为空则返回None
        """
        try:
            if device_id:
                # 从设备特定队列获取
                device_queue = self.device_queues[device_id]['extractor']
                frame_data = device_queue.get(block=block, timeout=timeout)
            else:
                # 从主队列获取
                frame_data = self.extractor_queue.get(block=block, timeout=timeout)
            
            with self._lock:
                self.stats['extractor_queue_size'] = self.extractor_queue.qsize()
                self.stats['total_frames_processed'] += 1
            
            return frame_data
        except Empty:
            return None
        except Exception as e:
            logger.error(f"从抽帧器队列获取失败: {str(e)}", exc_info=True)
            return None
    
    def put_to_sorter_queue(self, frame_data: FrameData, block: bool = True, timeout: Optional[float] = None) -> bool:
        """
        将帧数据放入排序器队列
        
        Args:
            frame_data: 帧数据对象
            block: 是否阻塞
            timeout: 超时时间(秒)
        
        Returns:
            bool: 是否成功
        """
        try:
            self.sorter_queue.put(frame_data, block=block, timeout=timeout)
            # 同时放入设备特定队列
            device_queue = self.device_queues[frame_data.device_id]['sorter']
            device_queue.put(frame_data, block=False)
            
            with self._lock:
                self.stats['sorter_queue_size'] = self.sorter_queue.qsize()
                self.stats['device_stats'][frame_data.device_id]['sorter_count'] += 1
            
            logger.debug(f"帧数据已放入排序器队列: device_id={frame_data.device_id}, frame_index={frame_data.frame_index}")
            return True
        except Exception as e:
            logger.error(f"放入排序器队列失败: {str(e)}", exc_info=True)
            return False
    
    def get_from_sorter_queue(self, device_id: Optional[str] = None, block: bool = True, timeout: Optional[float] = None) -> Optional[FrameData]:
        """
        从排序器队列获取帧数据
        
        Args:
            device_id: 设备ID(如果指定,则从设备特定队列获取)
            block: 是否阻塞
            timeout: 超时时间(秒)
        
        Returns:
            FrameData: 帧数据对象,如果队列为空则返回None
        """
        try:
            if device_id:
                # 从设备特定队列获取
                device_queue = self.device_queues[device_id]['sorter']
                frame_data = device_queue.get(block=block, timeout=timeout)
            else:
                # 从主队列获取
                frame_data = self.sorter_queue.get(block=block, timeout=timeout)
            
            with self._lock:
                self.stats['sorter_queue_size'] = self.sorter_queue.qsize()
                self.stats['total_frames_sorted'] += 1
            
            return frame_data
        except Empty:
            return None
        except Exception as e:
            logger.error(f"从排序器队列获取失败: {str(e)}", exc_info=True)
            return None
    
    def put_to_pusher_queue(self, frame_data: FrameData, block: bool = True, timeout: Optional[float] = None) -> bool:
        """
        将帧数据放入推送器队列
        
        Args:
            frame_data: 帧数据对象
            block: 是否阻塞
            timeout: 超时时间(秒)
        
        Returns:
            bool: 是否成功
        """
        try:
            self.pusher_queue.put(frame_data, block=block, timeout=timeout)
            # 同时放入设备特定队列
            device_queue = self.device_queues[frame_data.device_id]['pusher']
            device_queue.put(frame_data, block=False)
            
            with self._lock:
                self.stats['pusher_queue_size'] = self.pusher_queue.qsize()
                self.stats['device_stats'][frame_data.device_id]['pusher_count'] += 1
            
            logger.debug(f"帧数据已放入推送器队列: device_id={frame_data.device_id}, frame_index={frame_data.frame_index}")
            return True
        except Exception as e:
            logger.error(f"放入推送器队列失败: {str(e)}", exc_info=True)
            return False
    
    def get_from_pusher_queue(self, device_id: Optional[str] = None, block: bool = True, timeout: Optional[float] = None) -> Optional[FrameData]:
        """
        从推送器队列获取帧数据
        
        Args:
            device_id: 设备ID(如果指定,则从设备特定队列获取)
            block: 是否阻塞
            timeout: 超时时间(秒)
        
        Returns:
            FrameData: 帧数据对象,如果队列为空则返回None
        """
        try:
            if device_id:
                # 从设备特定队列获取
                device_queue = self.device_queues[device_id]['pusher']
                frame_data = device_queue.get(block=block, timeout=timeout)
            else:
                # 从主队列获取
                frame_data = self.pusher_queue.get(block=block, timeout=timeout)
            
            with self._lock:
                self.stats['pusher_queue_size'] = self.pusher_queue.qsize()
                self.stats['total_frames_pushed'] += 1
            
            return frame_data
        except Empty:
            return None
        except Exception as e:
            logger.error(f"从推送器队列获取失败: {str(e)}", exc_info=True)
            return None
    
    def get_queue_sizes(self) -> Dict[str, int]:
        """获取所有队列的大小"""
        with self._lock:
            return {
                'extractor_queue_size': self.extractor_queue.qsize(),
                'sorter_queue_size': self.sorter_queue.qsize(),
                'pusher_queue_size': self.pusher_queue.qsize(),
                'device_queues': {
                    device_id: {
                        'extractor': queue['extractor'].qsize(),
                        'sorter': queue['sorter'].qsize(),
                        'pusher': queue['pusher'].qsize()
                    }
                    for device_id, queue in self.device_queues.items()
                }
            }
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        with self._lock:
            queue_sizes = self.get_queue_sizes()
            return {
                **self.stats,
                **queue_sizes
            }
    
    def clear_queues(self, device_id: Optional[str] = None):
        """
        清空队列
        
        Args:
            device_id: 设备ID(如果指定,则只清空该设备的队列)
        """
        with self._lock:
            if device_id:
                # 清空指定设备的队列
                if device_id in self.device_queues:
                    for queue in self.device_queues[device_id].values():
                        while not queue.empty():
                            try:
                                queue.get_nowait()
                            except Empty:
                                break
            else:
                # 清空所有队列
                while not self.extractor_queue.empty():
                    try:
                        self.extractor_queue.get_nowait()
                    except Empty:
                        break
                while not self.sorter_queue.empty():
                    try:
                        self.sorter_queue.get_nowait()
                    except Empty:
                        break
                while not self.pusher_queue.empty():
                    try:
                        self.pusher_queue.get_nowait()
                    except Empty:
                        break
                
                # 清空设备队列
                self.device_queues.clear()
            
            # 重置统计信息
            self.stats['extractor_queue_size'] = 0
            self.stats['sorter_queue_size'] = 0
            self.stats['pusher_queue_size'] = 0


# 全局队列管理器实例
_global_queue_manager: Optional[FrameQueueManager] = None


def get_queue_manager() -> FrameQueueManager:
    """获取全局队列管理器实例"""
    global _global_queue_manager
    if _global_queue_manager is None:
        _global_queue_manager = FrameQueueManager()
    return _global_queue_manager


def reset_queue_manager():
    """重置全局队列管理器(用于测试)"""
    global _global_queue_manager
    _global_queue_manager = None

