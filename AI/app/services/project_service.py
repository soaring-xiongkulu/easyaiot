import os
import zipfile

from flask import current_app
from minio import Minio
from minio.error import S3Error


class ProjectService:
    @staticmethod
    def get_minio_client():
        """创建并返回Minio客户端"""
        minio_endpoint = os.environ.get('MINIO_ENDPOINT', 'localhost:9000')
        access_key = os.environ.get('MINIO_ACCESS_KEY', 'minioadmin')
        secret_key = os.environ.get('MINIO_SECRET_KEY', 'minioadmin')
        secure = os.environ.get('MINIO_SECURE', 'false').lower() == 'true'

        return Minio(
            minio_endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )

    @staticmethod
    def download_from_minio(bucket_name, object_name, destination_path):
        """从Minio下载文件"""
        try:
            minio_client = ProjectService.get_minio_client()

            # 检查对象是否存在
            stat = minio_client.stat_object(bucket_name, object_name)
            if not stat:
                current_app.logger.error(f"Minio对象不存在: {bucket_name}/{object_name}")
                return False

            # 下载文件
            minio_client.fget_object(bucket_name, object_name, destination_path)
            current_app.logger.info(f"成功下载Minio对象: {bucket_name}/{object_name} -> {destination_path}")
            return True
        except S3Error as e:
            current_app.logger.error(f"Minio下载错误: {str(e)}")
            return False
        except Exception as e:
            current_app.logger.error(f"Minio下载未知错误: {str(e)}")
            return False

    @staticmethod
    def extract_zip(zip_path, extract_path):
        """解压ZIP文件"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            current_app.logger.info(f"成功解压ZIP文件: {zip_path} -> {extract_path}")
            return True
        except zipfile.BadZipFile:
            current_app.logger.error(f"ZIP文件损坏: {zip_path}")
            return False
        except Exception as e:
            current_app.logger.error(f"解压ZIP文件错误: {str(e)}")
            return False

    @staticmethod
    def get_project_upload_dir(project_id):
        """获取项目上传目录路径"""
        return os.path.join(current_app.root_path, 'static', 'uploads', str(project_id))

    @staticmethod
    def ensure_project_upload_dir(project_id):
        """确保项目上传目录存在"""
        project_dir = ProjectService.get_project_upload_dir(project_id)
        os.makedirs(project_dir, exist_ok=True)
        return project_dir

    @staticmethod
    def get_project_dataset_dir(project_id):
        """获取项目数据集目录路径"""
        return os.path.join(current_app.root_path, 'static', 'datasets', str(project_id))

    @staticmethod
    def ensure_project_dataset_dir(project_id):
        """确保项目数据集目录存在"""
        project_dir = ProjectService.get_project_dataset_dir(project_id)
        os.makedirs(project_dir, exist_ok=True)
        return project_dir

    @staticmethod
    def get_project_model_dir(project_id):
        """获取项目模型目录路径"""
        return os.path.join(current_app.root_path, 'static', 'models', str(project_id))

    @staticmethod
    def ensure_project_model_dir(project_id):
        """确保项目模型目录存在"""
        project_dir = ProjectService.get_project_model_dir(project_id)
        os.makedirs(project_dir, exist_ok=True)
        return project_dir

    @staticmethod
    def get_relative_path(full_path):
        """将绝对路径转换为相对于static目录的路径"""
        static_dir = os.path.join(current_app.root_path, 'static')
        relative_to_static = os.path.relpath(full_path, static_dir)
        return relative_to_static

    @staticmethod
    def get_posix_path(relative_path):
        """将相对路径转换为POSIX风格路径（使用正斜杠）"""
        import posixpath
        import os
        return posixpath.join(*relative_path.split(os.sep))