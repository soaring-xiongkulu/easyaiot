import os

from flask import Blueprint, jsonify
from flask import current_app
from flask import send_file, url_for
from ultralytics import YOLO

from models import db

export_bp = Blueprint('export', __name__)

@export_bp.route('/api/project/<int:project_id>/export/<format>', methods=['POST'])
def api_export_model(project_id, format):
    try:
        # 检查原始模型文件是否存在
        model_path = os.path.join(current_app.root_path, 'data/models', str(project_id), 'train', 'weights',
                                  'best.pt')
        if not os.path.exists(model_path):
            return jsonify({'success': False, 'message': '模型文件不存在，请先训练模型'})

        # 确定导出目录和文件路径
        export_dir = os.path.join(current_app.root_path, 'data/models', str(project_id), 'export')
        os.makedirs(export_dir, exist_ok=True)

        export_filepath = ''
        source_filepath = ''  # 已存在的导出文件路径

        if format == 'onnx':
            export_filepath = os.path.join(export_dir, 'model.onnx')
            # 检查是否已存在导出的ONNX文件
            existing_onnx = os.path.join(current_app.root_path, 'data/models', str(project_id), 'train', 'weights',
                                         'best.onnx')
            if os.path.exists(existing_onnx):
                source_filepath = existing_onnx
        elif format == 'torchscript':
            export_filepath = os.path.join(export_dir, 'model.torchscript')
        else:
            return jsonify({'success': False, 'message': f'不支持的导出格式: {format}'})

        # 如果有已存在的导出文件，直接复制
        if source_filepath and os.path.exists(source_filepath):
            import shutil
            shutil.copy2(source_filepath, export_filepath)
        # 否则重新导出
        elif not os.path.exists(export_filepath):
            # 加载模型
            model = YOLO(model_path)

            # 使用正确的参数进行导出
            if format == 'onnx':
                # 对于ONNX导出，使用正确的参数
                model.export(format='onnx', project=export_dir, name='model')
            elif format == 'torchscript':
                # 对于TorchScript导出，使用正确的参数
                model.export(format='torchscript', project=export_dir, name='model')

        # 保存导出记录到数据库
        from models import ExportRecord
        export_record = ExportRecord(
            project_id=project_id,
            format=format,
            path=export_filepath
        )
        db.session.add(export_record)
        db.session.commit()

        # 生成相对于static目录的路径，用于下载
        relative_export_path = os.path.relpath(export_filepath, current_app.root_path)

        return jsonify({
            'success': True,
            'message': '导出成功',
            'path': export_filepath,
            'download_url': url_for('main.download_file', filename=relative_export_path)
        })
    except Exception as e:
        import traceback
        error_msg = f'导出失败: {str(e)}'
        print(f"导出错误详情: {error_msg}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': error_msg})


@export_bp.route('/download/<path:filename>')
def download_file(filename):
    # 构造完整文件路径
    full_path = os.path.join(current_app.root_path, filename)

    # 检查文件是否存在
    if not os.path.exists(full_path):
        return "文件不存在", 404

    # 确定文件的MIME类型和下载文件名
    mimetype = 'application/octet-stream'
    download_name = os.path.basename(filename)

    # 根据文件扩展名设置特定的MIME类型
    if filename.endswith('.onnx'):
        mimetype = 'application/octet-stream'
        download_name = filename.split('/')[-1]  # 确保获取正确的文件名
    elif filename.endswith('.pt'):
        mimetype = 'application/octet-stream'
        download_name = filename.split('/')[-1]
    elif filename.endswith('.torchscript'):
        mimetype = 'application/octet-stream'
        download_name = filename.split('/')[-1]

    return send_file(
        full_path,
        as_attachment=True,
        mimetype=mimetype,
        download_name=download_name
    )
