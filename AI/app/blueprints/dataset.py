import os
import shutil

import yaml
from flask import Blueprint, request, jsonify, current_app, send_file

from models import db, Project, Image, Label

dataset_bp = Blueprint('dataset', __name__)


@dataset_bp.route('/api/project/<int:project_id>/dataset/update', methods=['POST'])
def api_update_dataset(project_id):
    data = request.get_json()
    image_ids = data.get('image_ids', [])
    dataset_type = data.get('dataset_type')

    # 更新数据集类型
    Image.query.filter(Image.id.in_(image_ids)).update(
        {Image.dataset_type: dataset_type},
        synchronize_session=False
    )
    db.session.commit()

    # 重新组织数据集目录结构
    organize_dataset_directories(project_id)

    return jsonify({'success': True})


@dataset_bp.route('/api/project/<int:project_id>/dataset/auto_assign', methods=['POST'])
def api_auto_assign_dataset(project_id):
    # 获取所有已标注的图片
    annotated_images = Image.query.filter(
        Image.project_id == project_id,
        Image.annotations.any()
    ).all()

    # 如果没有已标注的图片，返回错误
    if not annotated_images:
        return jsonify({
            'success': False,
            'message': '没有找到已标注的图片'
        }), 400

    # 打乱图片顺序以确保随机性
    import random
    random.shuffle(annotated_images)

    # 按照最佳实践比例划分数据集: 70% 训练集, 20% 验证集, 10% 测试集
    total_count = len(annotated_images)
    train_count = int(total_count * 0.7)
    val_count = int(total_count * 0.2)
    # 剩余的为测试集

    # 分配数据集类型
    for i, image in enumerate(annotated_images):
        if i < train_count:
            image.dataset_type = 'train'
        elif i < train_count + val_count:
            image.dataset_type = 'val'
        else:
            image.dataset_type = 'test'

    # 提交更改到数据库
    db.session.commit()

    # 立即组织数据集目录结构
    organize_dataset_directories(project_id)

    # 返回划分结果
    return jsonify({
        'success': True,
        'train_count': train_count,
        'val_count': val_count,
        'test_count': total_count - train_count - val_count
    })


@dataset_bp.route('/api/project/<int:project_id>/dataset/download')
def api_download_dataset(project_id):
    try:
        project = Project.query.get_or_404(project_id)

        # 检查数据集目录是否存在
        project_dir = os.path.join(current_app.root_path, 'data/datasets', str(project_id))
        if not os.path.exists(project_dir):
            # 如果目录不存在，重新组织一次
            organize_dataset_directories(project_id)

        if not os.path.exists(project_dir):
            return jsonify({'success': False, 'message': '数据集目录不存在'}), 404

        # 创建临时ZIP文件
        import tempfile
        import zipfile

        temp_dir = tempfile.mkdtemp()
        zip_filename = f'dataset_{project_id}.zip'
        zip_filepath = os.path.join(temp_dir, zip_filename)

        # 创建ZIP文件
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(project_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, project_dir)
                    zipf.write(file_path, arcname)

        # 发送ZIP文件
        return send_file(
            zip_filepath,
            as_attachment=True,
            download_name=zip_filename,
            mimetype='application/zip'
        )

    except Exception as e:
        print(f"下载数据集时出错: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


def organize_dataset_directories(project_id):
    """组织数据集目录结构，将图片和标注文件放到对应目录中"""
    with current_app.app_context():
        project = Project.query.get(project_id)
        if not project:
            return

        # 创建数据集目录结构
        project_dir = os.path.join(current_app.root_path, 'data/datasets', str(project_id))
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir)

        os.makedirs(project_dir, exist_ok=True)

        # 创建images和labels子目录
        for dataset_type in ['train', 'val', 'test']:
            img_dir = os.path.join(project_dir, 'images', dataset_type)
            label_dir = os.path.join(project_dir, 'labels', dataset_type)
            os.makedirs(img_dir, exist_ok=True)
            os.makedirs(label_dir, exist_ok=True)

        # 获取所有已分配的图片
        assigned_images = Image.query.filter(
            Image.project_id == project_id,
            Image.dataset_type.in_(['train', 'val', 'test'])
        ).all()

        # 复制图片和标注文件到对应目录
        for img in assigned_images:
            # 源文件路径
            src_img_path = os.path.join(current_app.root_path, 'static', img.path)
            src_label_path = os.path.splitext(src_img_path)[0] + '.txt'

            # 目标文件路径
            dst_img_path = os.path.join(project_dir, 'images', img.dataset_type, img.filename)
            dst_label_path = os.path.join(project_dir, 'labels', img.dataset_type,
                                          os.path.splitext(img.filename)[0] + '.txt')

            # 复制图片文件
            if os.path.exists(src_img_path):
                shutil.copy(src_img_path, dst_img_path)

            # 复制标注文件
            if os.path.exists(src_label_path):
                shutil.copy(src_label_path, dst_label_path)

        # 创建data.yaml文件
        labels = Label.query.filter_by(project_id=project_id).all()
        names = [label.name for label in labels]

        data_yaml = {
            'path': project_dir,
            'train': os.path.join('images', 'train'),
            'val': os.path.join('images', 'val'),
            'test': os.path.join('images', 'test'),
            'nc': len(names),
            'names': names
        }

        with open(os.path.join(project_dir, 'data.yaml'), 'w') as f:
            yaml.dump(data_yaml, f, default_flow_style=False, allow_unicode=True)
