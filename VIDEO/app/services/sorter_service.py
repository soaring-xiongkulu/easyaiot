"""
排序器管理服务
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import uuid
from datetime import datetime
from typing import List, Optional

from models import db, Sorter

logger = logging.getLogger(__name__)


def create_sorter(sorter_name: str, sorter_type: str = 'confidence',
                 sort_order: str = 'desc', description: Optional[str] = None,
                 is_enabled: bool = True) -> Sorter:
    """创建排序器"""
    try:
        # 生成唯一编号
        sorter_code = f"SORTER_{uuid.uuid4().hex[:8].upper()}"
        
        sorter = Sorter(
            sorter_name=sorter_name,
            sorter_code=sorter_code,
            sorter_type=sorter_type,
            sort_order=sort_order,
            description=description,
            is_enabled=is_enabled
        )
        
        db.session.add(sorter)
        db.session.commit()
        
        logger.info(f"创建排序器成功: sorter_id={sorter.id}, sorter_name={sorter_name}")
        return sorter
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建排序器失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"创建排序器失败: {str(e)}")


def update_sorter(sorter_id: int, **kwargs) -> Sorter:
    """更新排序器"""
    try:
        sorter = Sorter.query.get_or_404(sorter_id)
        
        updatable_fields = [
            'sorter_name', 'sorter_type', 'sort_order',
            'description', 'is_enabled'
        ]
        
        for field in updatable_fields:
            if field in kwargs:
                setattr(sorter, field, kwargs[field])
        
        sorter.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"更新排序器成功: sorter_id={sorter_id}")
        return sorter
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新排序器失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"更新排序器失败: {str(e)}")


def delete_sorter(sorter_id: int):
    """删除排序器"""
    try:
        sorter = Sorter.query.get_or_404(sorter_id)
        db.session.delete(sorter)
        db.session.commit()
        
        logger.info(f"删除排序器成功: sorter_id={sorter_id}")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除排序器失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"删除排序器失败: {str(e)}")


def get_sorter(sorter_id: int) -> Sorter:
    """获取排序器详情"""
    try:
        sorter = Sorter.query.get_or_404(sorter_id)
        return sorter
    except Exception as e:
        logger.error(f"获取排序器失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"获取排序器失败: {str(e)}")


def list_sorters(page_no: int = 1, page_size: int = 10, search: Optional[str] = None) -> dict:
    """查询排序器列表"""
    try:
        query = Sorter.query
        
        if search:
            query = query.filter(
                db.or_(
                    Sorter.sorter_name.like(f'%{search}%'),
                    Sorter.sorter_code.like(f'%{search}%')
                )
            )
        
        total = query.count()
        
        # 分页
        offset = (page_no - 1) * page_size
        sorters = query.order_by(
            Sorter.created_at.desc()
        ).offset(offset).limit(page_size).all()
        
        return {
            'items': [sorter.to_dict() for sorter in sorters],
            'total': total
        }
    except Exception as e:
        logger.error(f"查询排序器列表失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"查询排序器列表失败: {str(e)}")

