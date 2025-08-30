import os
import zipfile
import posixpath
from flask import current_app
from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

class ModelService:
    @staticmethod
    def get_minio_client():
        """创建并返回Minio客户端（从.env加载配置）"""
        minio_endpoint = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
        access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
        secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
        secure = os.getenv('MINIO_SECURE', 'false').lower() == 'true'

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
            minio_client = ModelService.get_minio_client()

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
    def upload_to_minio(bucket_name, object_name, file_path):
        """上传文件到Minio存储"""
        try:
            minio_client = ModelService.get_minio_client()

            # 自动创建存储桶（如果不存在）
            if not minio_client.bucket_exists(bucket_name):
                minio_client.make_bucket(bucket_name)
                current_app.logger.info(f"创建Minio存储桶: {bucket_name}")

            # 执行文件上传
            minio_client.fput_object(bucket_name, object_name, file_path)
            current_app.logger.info(f"文件上传成功: {bucket_name}/{object_name}")
            return True
        except S3Error as e:
            current_app.logger.error(f"Minio上传错误: {str(e)}")
            return False
        except Exception as e:
            current_app.logger.error(f"Minio上传未知错误: {str(e)}")
            return False

    @staticmethod
    def upload_directory_to_minio(bucket_name, object_prefix, local_dir):
        """上传整个目录到Minio"""
        try:
            minio_client = ModelService.get_minio_client()

            # 确保存储桶存在
            if not minio_client.bucket_exists(bucket_name):
                minio_client.make_bucket(bucket_name)

            # 遍历目录并上传
            for root, _, files in os.walk(local_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, local_dir)
                    object_name = os.path.join(object_prefix, relative_path).replace("\\", "/")

                    minio_client.fput_object(
                        bucket_name, object_name, file_path
                    )
                    current_app.logger.info(f"已上传: {object_name}")

            return True
        except S3Error as e:
            current_app.logger.error(f"Minio目录上传错误: {str(e)}")
            return False
        except Exception as e:
            current_app.logger.error(f"Minio目录上传未知错误: {str(e)}")
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
    def get_model_upload_dir(model_id):
        """获取模型上传目录路径"""
        return os.path.join(current_app.root_path, 'static', 'uploads', str(model_id))

    @staticmethod
    def ensure_model_upload_dir(model_id):
        """确保模型上传目录存在"""
        model_dir = ModelService.get_model_upload_dir(model_id)
        os.makedirs(model_dir, exist_ok=True)
        return model_dir

    @staticmethod
    def get_dataset_dir(model_id):
        """获取模型数据集目录路径"""
        return os.path.join(current_app.root_path, 'static', 'datasets', str(model_id))

    @staticmethod
    def ensure_dataset_dir(model_id):
        """确保模型数据集目录存在"""
        model_dir = ModelService.get_dataset_dir(model_id)
        os.makedirs(model_dir, exist_ok=True)
        return model_dir

    @staticmethod
    def get_model_dir(model_id):
        """获取模型存储目录路径"""
        return os.path.join(current_app.root_path, 'static', 'models', str(model_id))

    @staticmethod
    def ensure_model_dir(model_id):
        """确保模型存储目录存在"""
        model_dir = ModelService.get_model_dir(model_id)
        os.makedirs(model_dir, exist_ok=True)
        return model_dir

    @staticmethod
    def get_relative_path(full_path):
        """将绝对路径转换为相对于static目录的路径"""
        static_dir = os.path.join(current_app.root_path, 'static')
        relative_to_static = os.path.relpath(full_path, static_dir)
        return relative_to_static

    @staticmethod
    def get_posix_path(relative_path):
        """将相对路径转换为POSIX风格路径（使用正斜杠）"""
        return posixpath.join(*relative_path.split(os.sep))