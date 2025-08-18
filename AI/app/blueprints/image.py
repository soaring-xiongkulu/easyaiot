import json
import logging
import os
import posixpath
import shutil
import tempfile
import zipfile
from datetime import datetime

from PIL import Image as PILImage
from flask import Blueprint, request
from flask import current_app
from flask import redirect, url_for, flash

from models import db, Project, Image
from app.services.project_service import ProjectService

image_bp = Blueprint('image', __name__)


@image_bp.route('/project/<int:project_id>/image/<int:image_id>/delete', methods=['POST'])
def delete_image(project_id, image_id):
    project = Project.query.get_or_404(project_id)
    image = Image.query.get_or_404(image_id)

    # 确保图片属于该项目
    if image.project_id != project_id:
        flash('无效的图片ID', 'error')
        return redirect(url_for('main.project_images', project_id=project_id))

    # 获取图片文件路径
    image_path = os.path.join(current_app.root_path, image.path)

    try:
        # 删除数据库记录
        db.session.delete(image)
        db.session.commit()

        # 删除图片文件
        if os.path.exists(image_path):
            os.remove(image_path)

        # 删除对应的YOLO格式标注文件（.txt文件）
        txt_file_path = os.path.splitext(image_path)[0] + '.txt'
        if os.path.exists(txt_file_path):
            os.remove(txt_file_path)

        flash(f'图片 "{image.original_filename}" 已删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除图片时出错: {str(e)}', 'error')

    return redirect(url_for('main.project_images', project_id=project_id))


@image_bp.route('/project/<int:project_id>/delete_selected_images', methods=['POST'])
def delete_selected_images(project_id):
    """批量删除选中的图片"""
    from app.utils.image_utils import ImageService

    project = Project.query.get_or_404(project_id)

    try:
        # 获取选中的图片ID列表
        image_ids_json = request.form.get('image_ids', '[]')
        image_ids = json.loads(image_ids_json)

        if not image_ids:
            flash('未选择任何图片', 'warning')
            return redirect(url_for('main.project_images', project_id=project_id))

        # 使用图片服务删除选中的图片
        deleted_count, errors = ImageService.delete_images(image_ids)

        if errors:
            for error in errors:
                flash(error, 'error')

        if deleted_count > 0:
            flash(f'成功删除 {deleted_count} 张图片', 'success')
        elif not errors:
            flash('未删除任何图片', 'warning')

    except Exception as e:
        flash(f'批量删除图片时出错: {str(e)}', 'error')

    return redirect(url_for('main.project_images', project_id=project_id))


@image_bp.route('/project/<int:project_id>/delete_unannotated_images', methods=['POST'])
def delete_unannotated_images(project_id):
    """删除项目中所有未标注的图片"""
    from app.utils.image_utils import ImageService

    project = Project.query.get_or_404(project_id)

    try:
        # 使用图片服务删除所有未标注的图片
        deleted_count, errors = ImageService.delete_unannotated_images(project_id)

        if errors:
            for error in errors:
                flash(error, 'error')

        if deleted_count > 0:
            flash(f'成功删除 {deleted_count} 张未标注的图片', 'success')
        elif deleted_count == 0:
            flash('没有未标注的图片需要删除', 'info')

    except Exception as e:
        flash(f'删除未标注图片时出错: {str(e)}', 'error')

    return redirect(url_for('main.project_images', project_id=project_id))


@image_bp.route('/project/<int:project_id>/upload_images', methods=['POST'])
def upload_images(project_id):
    project = Project.query.get_or_404(project_id)

    # 处理Minio数据集下载
    if 'minio_dataset' in request.form:
        minio_bucket = request.form.get('minio_bucket')
        minio_object = request.form.get('minio_object')

        if minio_bucket and minio_object:
            # 创建临时目录
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "dataset.zip")

            try:
                # 从Minio下载数据集
                if ProjectService.download_from_minio(minio_bucket, minio_object, zip_path):
                    # 解压数据集
                    extract_path = ProjectService.ensure_project_upload_dir(project_id)

                    if ProjectService.extract_zip(zip_path, extract_path):
                        # 遍历解压后的文件并添加到数据库
                        image_count = 0
                        for root, dirs, files in os.walk(extract_path):
                            for file in files:
                                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                                    file_path = os.path.join(root, file)
                                    relative_path = os.path.relpath(file_path,
                                                                    os.path.join(current_app.root_path, 'static'))
                                    relative_path = relative_path.replace('\\', '/')  # 确保使用正斜杠

                                    try:
                                        with PILImage.open(file_path) as img:
                                            width, height = img.size

                                        image = Image(
                                            filename=file,
                                            original_filename=file,
                                            path=relative_path,
                                            project_id=project_id,
                                            width=width,
                                            height=height
                                        )
                                        db.session.add(image)
                                        image_count += 1
                                    except Exception as e:
                                        logging.error(f"处理图片 {file} 出错: {str(e)}")

                        db.session.commit()
                        flash(f'成功从Minio下载并添加 {image_count} 张图片', 'success')
                    else:
                        flash('数据集解压失败，请检查文件格式', 'error')
                else:
                    flash('Minio数据集下载失败，请检查存储桶和对象名称', 'error')
            except Exception as e:
                logging.error(f"处理Minio数据集时出错: {str(e)}")
                flash('处理Minio数据集时发生错误', 'error')
            finally:
                # 清理临时目录
                shutil.rmtree(temp_dir, ignore_errors=True)

            return redirect(url_for('main.project_images', project_id=project_id))

    # 处理ZIP文件上传
    if 'zip_file' in request.files:
        zip_file = request.files['zip_file']
        if zip_file.filename != '':
            # 保存ZIP文件
            zip_path = os.path.join('data/uploads', f"{project_id}_{zip_file.filename}")
            zip_file.save(zip_path)

            # 解压ZIP文件
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                extract_path = os.path.join('data/uploads', str(project_id))
                os.makedirs(extract_path, exist_ok=True)
                zip_ref.extractall(extract_path)

            # 删除ZIP文件
            os.remove(zip_path)

            # 遍历解压后的文件并添加到数据库
            for root, dirs, files in os.walk(extract_path):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, 'static')
                        # 使用posixpath处理URL路径，确保在Windows上也使用正斜杠
                        relative_path = posixpath.join(*relative_path.split(os.sep))
                        img = PILImage.open(file_path)
                        width, height = img.size

                        image = Image(
                            filename=file,
                            original_filename=file,
                            path=relative_path,
                            project_id=project_id,
                            width=width,
                            height=height
                        )
                        db.session.add(image)

            db.session.commit()
            flash('ZIP文件上传并解压成功', 'success')
            return redirect(url_for('main.project_images', project_id=project_id))

    # 处理单个或多个图片上传
    if 'images' in request.files:
        images = request.files.getlist('images')
        for image_file in images:
            if image_file.filename != '':
                # 保存图片
                filename = f"{project_id}_{int(datetime.now().timestamp() * 1000)}_{image_file.filename}"
                file_path = os.path.join('data/uploads', filename)
                image_file.save(file_path)

                # 获取图片尺寸
                img = PILImage.open(file_path)
                width, height = img.size

                # 保存到数据库，确保路径正确
                relative_path = os.path.join('uploads', filename)
                # 使用posixpath处理URL路径，确保在Windows上也使用正斜杠
                relative_path = posixpath.join(*relative_path.split(os.sep))
                image = Image(
                    filename=filename,
                    original_filename=image_file.filename,
                    path=relative_path,
                    project_id=project_id,
                    width=width,
                    height=height
                )
                db.session.add(image)

        db.session.commit()
        flash('图片上传成功', 'success')

    return redirect(url_for('main.project_images', project_id=project_id))
