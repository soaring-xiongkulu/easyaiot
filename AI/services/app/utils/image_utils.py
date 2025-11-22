"""
图片处理工具函数

@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import os
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

def download_default_model_image(destination_path: str) -> bool:
    """
    下载默认模型图片
    
    Args:
        destination_path: 保存图片的本地路径
        
    Returns:
        bool: 下载是否成功
    """
    # 使用一个公开的YOLO模型图标URL（可以替换为其他公开图片URL）
    # 使用placeholder图片服务生成一个蓝色背景的YOLO模型图标
    default_image_urls = [
        # 使用placeholder图片服务（AI模型图标风格，蓝色背景）
        "https://via.placeholder.com/400x300/4A90E2/FFFFFF?text=YOLO+Model",
        # 备用URL - 使用picsum的占位图
        "https://picsum.photos/400/300"
    ]
    
    for url in default_image_urls:
        try:
            response = requests.get(url, timeout=10, stream=True)
            if response.status_code == 200:
                # 确保目录存在
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                
                # 保存图片
                with open(destination_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"默认图片下载成功: {url} -> {destination_path}")
                return True
        except Exception as e:
            logger.warning(f"从 {url} 下载默认图片失败: {str(e)}")
            continue
    
    # 如果所有URL都失败，创建一个简单的占位图片
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # 创建一个简单的占位图片
        img = Image.new('RGB', (400, 300), color=(74, 144, 226))
        draw = ImageDraw.Draw(img)
        
        # 尝试使用默认字体
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        except:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
            except:
                font = ImageFont.load_default()
        
        # 绘制文字
        text = "YOLO Model"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = ((400 - text_width) // 2, (300 - text_height) // 2)
        draw.text(position, text, fill=(255, 255, 255), font=font)
        
        # 保存图片
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        img.save(destination_path, 'PNG')
        logger.info(f"创建默认占位图片: {destination_path}")
        return True
    except ImportError:
        logger.error("PIL库未安装，无法创建占位图片")
        return False
    except Exception as e:
        logger.error(f"创建默认占位图片失败: {str(e)}")
        return False
