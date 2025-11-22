"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import os
import zipfile
import tempfile
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
        minio_endpoint = os.getenv('MINIO_ENDPOINT', 'MinIO:9000')
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
        """从Minio下载文件
        
        Returns:
            tuple: (success: bool, error_message: str or None)
        """
        try:
            minio_client = ModelService.get_minio_client()

            # 检查对象是否存在
            try:
                stat = minio_client.stat_object(bucket_name, object_name)
                if not stat:
                    error_msg = f"Minio对象不存在: {bucket_name}/{object_name}"
                    current_app.logger.error(error_msg)
                    return False, error_msg
            except S3Error as e:
                if e.code == 'NoSuchKey':
                    error_msg = f"Minio对象不存在: {bucket_name}/{object_name}"
                    current_app.logger.error(error_msg)
                    return False, error_msg
                else:
                    raise

            # 下载文件
            minio_client.fget_object(bucket_name, object_name, destination_path)
            current_app.logger.info(f"成功下载Minio对象: {bucket_name}/{object_name} -> {destination_path}")
            return True, None
        except S3Error as e:
            error_msg = f"Minio下载错误: {str(e)}"
            current_app.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Minio下载未知错误: {str(e)}"
            current_app.logger.error(error_msg)
            return False, error_msg

    @staticmethod
    def download_directory_from_minio(bucket_name, object_prefix, destination_zip_path):
        """从Minio下载目录并打包为zip文件
        
        Args:
            bucket_name: Minio存储桶名称
            object_prefix: 对象前缀（目录路径，应以'/'结尾）
            destination_zip_path: 目标zip文件路径
        
        Returns:
            tuple: (success: bool, error_message: str or None)
        """
        try:
            minio_client = ModelService.get_minio_client()
            
            # 确保前缀以'/'结尾
            if not object_prefix.endswith('/'):
                object_prefix = object_prefix + '/'
            
            # 列出目录下的所有对象
            objects = minio_client.list_objects(
                bucket_name,
                prefix=object_prefix,
                recursive=True
            )
            
            objects_list = list(objects)
            if not objects_list:
                error_msg = f"Minio目录为空或不存在: {bucket_name}/{object_prefix}"
                current_app.logger.error(error_msg)
                return False, error_msg
            
            # 创建临时目录用于下载文件
            with tempfile.TemporaryDirectory() as tmp_dir:
                # 下载所有文件到临时目录
                for obj in objects_list:
                    # 获取相对路径
                    relative_path = obj.object_name[len(object_prefix):]
                    if not relative_path:  # 跳过目录本身
                        continue
                    
                    # 构建本地文件路径
                    local_file_path = os.path.join(tmp_dir, relative_path)
                    local_dir = os.path.dirname(local_file_path)
                    if local_dir:
                        os.makedirs(local_dir, exist_ok=True)
                    
                    # 下载文件
                    minio_client.fget_object(bucket_name, obj.object_name, local_file_path)
                    current_app.logger.debug(f"已下载: {obj.object_name} -> {local_file_path}")
                
                # 打包为zip文件
                with zipfile.ZipFile(destination_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(tmp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # 计算在zip中的相对路径
                            arcname = os.path.relpath(file_path, tmp_dir)
                            zipf.write(file_path, arcname)
                
                current_app.logger.info(f"成功下载并打包Minio目录: {bucket_name}/{object_prefix} -> {destination_zip_path}")
                return True, None
                
        except S3Error as e:
            error_msg = f"Minio目录下载错误: {str(e)}"
            current_app.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Minio目录下载未知错误: {str(e)}"
            current_app.logger.error(error_msg)
            return False, error_msg

    @staticmethod
    def upload_to_minio(bucket_name, object_name, file_path):
        """上传文件到Minio存储
        
        Returns:
            tuple: (success: bool, error_message: str or None)
        """
        try:
            minio_client = ModelService.get_minio_client()

            # 检查本地文件是否存在
            if not os.path.exists(file_path):
                error_msg = f"本地文件不存在: {file_path}"
                current_app.logger.error(error_msg)
                return False, error_msg

            # 自动创建存储桶（如果不存在）
            if not minio_client.bucket_exists(bucket_name):
                minio_client.make_bucket(bucket_name)
                current_app.logger.info(f"创建Minio存储桶: {bucket_name}")

            # 执行文件上传
            minio_client.fput_object(bucket_name, object_name, file_path)
            current_app.logger.info(f"文件上传完成: {bucket_name}/{object_name}")

            # 验证上传是否成功：检查对象是否存在
            try:
                stat = minio_client.stat_object(bucket_name, object_name)
                if stat:
                    current_app.logger.info(f"文件上传验证成功: {bucket_name}/{object_name}, 大小: {stat.size} 字节")
                    return True, None
                else:
                    error_msg = f"文件上传后验证失败: {bucket_name}/{object_name} 不存在"
                    current_app.logger.error(error_msg)
                    return False, error_msg
            except S3Error as verify_error:
                error_msg = f"文件上传后验证失败: {bucket_name}/{object_name}, 错误: {str(verify_error)}"
                current_app.logger.error(error_msg)
                return False, error_msg

        except S3Error as e:
            error_msg = f"Minio上传错误: {str(e)}"
            current_app.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Minio上传未知错误: {str(e)}"
            current_app.logger.error(error_msg)
            return False, error_msg

    @staticmethod
    def upload_directory_to_minio(bucket_name, object_prefix, local_dir):
        """上传整个目录到Minio
        
        Returns:
            tuple: (success: bool, error_message: str or None)
        """
        try:
            minio_client = ModelService.get_minio_client()

            # 检查本地目录是否存在
            if not os.path.exists(local_dir):
                error_msg = f"本地目录不存在: {local_dir}"
                current_app.logger.error(error_msg)
                return False, error_msg

            # 确保存储桶存在
            if not minio_client.bucket_exists(bucket_name):
                minio_client.make_bucket(bucket_name)
                current_app.logger.info(f"创建Minio存储桶: {bucket_name}")

            uploaded_files = []
            # 遍历目录并上传
            for root, _, files in os.walk(local_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, local_dir)
                    object_name = os.path.join(object_prefix, relative_path).replace("\\", "/")

                    minio_client.fput_object(
                        bucket_name, object_name, file_path
                    )
                    uploaded_files.append(object_name)
                    current_app.logger.info(f"已上传: {object_name}")

            # 验证至少有一个文件被上传
            if not uploaded_files:
                error_msg = f"目录中没有文件可上传: {local_dir}"
                current_app.logger.error(error_msg)
                return False, error_msg

            # 验证第一个文件是否存在（作为上传成功的标志）
            if uploaded_files:
                try:
                    first_object = uploaded_files[0]
                    stat = minio_client.stat_object(bucket_name, first_object)
                    if stat:
                        current_app.logger.info(f"目录上传验证成功: 共上传 {len(uploaded_files)} 个文件")
                        return True, None
                    else:
                        error_msg = f"目录上传后验证失败: {bucket_name}/{first_object} 不存在"
                        current_app.logger.error(error_msg)
                        return False, error_msg
                except S3Error as verify_error:
                    error_msg = f"目录上传后验证失败: {bucket_name}/{uploaded_files[0]}, 错误: {str(verify_error)}"
                    current_app.logger.error(error_msg)
                    return False, error_msg

            return True, None
        except S3Error as e:
            error_msg = f"Minio目录上传错误: {str(e)}"
            current_app.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Minio目录上传未知错误: {str(e)}"
            current_app.logger.error(error_msg)
            return False, error_msg

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

    @staticmethod
    def delete_from_minio(bucket_name, object_name):
        """从Minio删除文件或目录"""
        try:
            minio_client = ModelService.get_minio_client()

            # 检查存储桶是否存在
            if not minio_client.bucket_exists(bucket_name):
                current_app.logger.warning(f"Minio存储桶不存在: {bucket_name}")
                return False

            # 判断是文件还是目录
            # 如果 object_name 以 '/' 结尾，需要递归删除目录
            if object_name.endswith('/'):
                # 删除目录下的所有对象
                objects_to_delete = minio_client.list_objects(
                    bucket_name, 
                    prefix=object_name, 
                    recursive=True
                )
                objects_list = list(objects_to_delete)
                
                if not objects_list:
                    current_app.logger.warning(f"Minio目录为空或不存在: {bucket_name}/{object_name}")
                    return True
                
                # 批量删除对象
                from minio.deleteobjects import DeleteObject
                delete_object_list = [DeleteObject(obj.object_name) for obj in objects_list]
                errors = minio_client.remove_objects(bucket_name, delete_object_list)
                
                # 检查是否有错误
                error_list = list(errors)
                if error_list:
                    for error in error_list:
                        current_app.logger.error(f"删除Minio对象失败: {error}")
                    return False
                
                current_app.logger.info(f"成功删除Minio目录: {bucket_name}/{object_name} (共 {len(objects_list)} 个对象)")
                return True
            else:
                # 先尝试作为单个文件删除
                try:
                    # 检查是否存在以该路径为前缀的多个对象（可能是目录）
                    objects_to_check = minio_client.list_objects(
                        bucket_name,
                        prefix=object_name + '/',
                        recursive=False
                    )
                    objects_list = list(objects_to_check)
                    
                    if objects_list:
                        # 存在以该路径为前缀的对象，作为目录处理
                        # 删除所有以该路径为前缀的对象
                        objects_to_delete = minio_client.list_objects(
                            bucket_name,
                            prefix=object_name + '/',
                            recursive=True
                        )
                        objects_list = list(objects_to_delete)
                        
                        if objects_list:
                            from minio.deleteobjects import DeleteObject
                            delete_object_list = [DeleteObject(obj.object_name) for obj in objects_list]
                            errors = minio_client.remove_objects(bucket_name, delete_object_list)
                            
                            error_list = list(errors)
                            if error_list:
                                for error in error_list:
                                    current_app.logger.error(f"删除Minio对象失败: {error}")
                                return False
                            
                            current_app.logger.info(f"成功删除Minio目录: {bucket_name}/{object_name} (共 {len(objects_list)} 个对象)")
                            return True
                    
                    # 作为单个文件删除
                    minio_client.remove_object(bucket_name, object_name)
                    current_app.logger.info(f"成功删除Minio对象: {bucket_name}/{object_name}")
                    return True
                except S3Error as e:
                    # 如果文件不存在，记录警告但不视为错误
                    if e.code == 'NoSuchKey':
                        current_app.logger.warning(f"Minio对象不存在: {bucket_name}/{object_name}")
                        return True
                    else:
                        raise
                        
        except S3Error as e:
            current_app.logger.error(f"Minio删除错误: {str(e)}")
            return False
        except Exception as e:
            current_app.logger.error(f"Minio删除未知错误: {str(e)}")
            return False