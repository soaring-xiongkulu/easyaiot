"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import os
from flask import current_app
from models import db, Image

class ImageService:
    @staticmethod
    def delete_images(image_ids):
        """
        批量删除图片
        
        Args:
            image_ids: 要删除的图片ID列表
            
        Returns:
            tuple: (成功删除的数量, 错误信息列表)
        """
        deleted_count = 0
        errors = []
        
        for image_id in image_ids:
            try:
                image = Image.query.get(image_id)
                if not image:
                    errors.append(f"图片ID {image_id} 不存在")
                    continue
                
                # 获取图片文件路径
                image_path = os.path.join(current_app.root_path, image.path)
                
                # 删除数据库记录
                db.session.delete(image)
                
                # 删除图片文件
                if os.path.exists(image_path):
                    os.remove(image_path)
                    
                # 删除对应的YOLO格式标注文件（.txt文件）
                txt_file_path = os.path.splitext(image_path)[0] + '.txt'
                if os.path.exists(txt_file_path):
                    os.remove(txt_file_path)
                    
                deleted_count += 1
            except Exception as e:
                errors.append(f"删除图片ID {image_id} 时出错: {str(e)}")
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            errors.append(f"数据库提交失败: {str(e)}")
            deleted_count = 0
            
        return deleted_count, errors
    
    @staticmethod
    def delete_unannotated_images(project_id):
        """
        删除项目中所有未标注的图片
        
        Args:
            project_id: 项目ID
            
        Returns:
            tuple: (成功删除的数量, 错误信息列表)
        """
        # 查询所有未标注的图片
        unannotated_images = Image.query.filter(
            Image.project_id == project_id,
            ~Image.annotations.any()  # 没有关联的标注
        ).all()
        
        image_ids = [image.id for image in unannotated_images]
        return ImageService.delete_images(image_ids)