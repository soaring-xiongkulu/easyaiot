"""
抽帧器管理服务
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import uuid
from datetime import datetime
from typing import List, Optional

from models import db, FrameExtractor

logger = logging.getLogger(__name__)


def create_frame_extractor(extractor_name: str, extractor_type: str = 'interval',
                          interval: int = 1, description: Optional[str] = None,
                          is_enabled: bool = True) -> FrameExtractor:
    """创建抽帧器"""
    try:
        # 生成唯一编号
        extractor_code = f"EXTRACTOR_{uuid.uuid4().hex[:8].upper()}"
        
        extractor = FrameExtractor(
            extractor_name=extractor_name,
            extractor_code=extractor_code,
            extractor_type=extractor_type,
            interval=interval,
            description=description,
            is_enabled=is_enabled
        )
        
        db.session.add(extractor)
        db.session.commit()
        
        logger.info(f"创建抽帧器成功: extractor_id={extractor.id}, extractor_name={extractor_name}")
        return extractor
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建抽帧器失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"创建抽帧器失败: {str(e)}")


def update_frame_extractor(extractor_id: int, **kwargs) -> FrameExtractor:
    """更新抽帧器"""
    try:
        extractor = FrameExtractor.query.get_or_404(extractor_id)
        
        updatable_fields = [
            'extractor_name', 'extractor_type', 'interval',
            'description', 'is_enabled'
        ]
        
        for field in updatable_fields:
            if field in kwargs:
                setattr(extractor, field, kwargs[field])
        
        extractor.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"更新抽帧器成功: extractor_id={extractor_id}")
        return extractor
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新抽帧器失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"更新抽帧器失败: {str(e)}")


def delete_frame_extractor(extractor_id: int):
    """删除抽帧器"""
    try:
        extractor = FrameExtractor.query.get_or_404(extractor_id)
        db.session.delete(extractor)
        db.session.commit()
        
        logger.info(f"删除抽帧器成功: extractor_id={extractor_id}")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除抽帧器失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"删除抽帧器失败: {str(e)}")


def get_frame_extractor(extractor_id: int) -> FrameExtractor:
    """获取抽帧器详情"""
    try:
        extractor = FrameExtractor.query.get_or_404(extractor_id)
        return extractor
    except Exception as e:
        logger.error(f"获取抽帧器失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"获取抽帧器失败: {str(e)}")


def list_frame_extractors(page_no: int = 1, page_size: int = 10, search: Optional[str] = None) -> dict:
    """查询抽帧器列表"""
    try:
        query = FrameExtractor.query
        
        if search:
            query = query.filter(
                db.or_(
                    FrameExtractor.extractor_name.like(f'%{search}%'),
                    FrameExtractor.extractor_code.like(f'%{search}%')
                )
            )
        
        total = query.count()
        
        # 分页
        offset = (page_no - 1) * page_size
        extractors = query.order_by(
            FrameExtractor.created_at.desc()
        ).offset(offset).limit(page_size).all()
        
        return {
            'items': [extractor.to_dict() for extractor in extractors],
            'total': total
        }
    except Exception as e:
        logger.error(f"查询抽帧器列表失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"查询抽帧器列表失败: {str(e)}")

