import os
import threading

from flask import request, send_file, url_for

from . import service
from ...base.app import get_blueprint, make_manager_response

train_bp = get_blueprint('train', __name__)

@train_bp.route('/<int:project_id>/start', methods=['POST'])
def start_training(project_id: int):
    try:
        data = request.get_json()
        epochs = data.get('epochs', 20)
        model_arch = data.get('model_arch', 'yolov8n.pt')
        img_size = data.get('img_size', 640)
        batch_size = data.get('batch_size', 16)
        use_gpu = data.get('use_gpu', True)
        oss_dataset_path = data.get('oss_dataset_path')

        if not oss_dataset_path:
            return make_manager_response({'error': 'OSS数据集路径未提供'}, status=400)

        # 检查是否已有训练在进行
        current_status = service.get_training_status(project_id)
        if current_status['status'] in ['preparing', 'training']:
            return make_manager_response({'error': '训练已在进行中'}, status=400)

        # 在后台线程中启动训练
        thread = threading.Thread(
            target=service.train_model,
            args=(project_id, epochs, model_arch, img_size, batch_size, use_gpu, oss_dataset_path)
        )
        thread.daemon = True
        thread.start()

        return make_manager_response({'message': '训练已启动'})
    except Exception as e:
        return make_manager_response({'error': str(e)}, status=500)

@train_bp.route('/<int:project_id>/status')
def get_training_status(project_id: int):
    status = service.get_training_status(project_id)
    return make_manager_response(status)

@train_bp.route('/<int:project_id>/stop', methods=['POST'])
def stop_training(project_id: int):
    service.stop_training(project_id)
    return make_manager_response({'message': '停止请求已发送'})

@train_bp.route('/<int:project_id>/export/<format>', methods=['POST'])
def export_model(project_id: int, format: str):
    try:
        export_filepath = service.export_model(project_id, format)
        relative_path = os.path.relpath(export_filepath, os.getcwd())

        return make_manager_response({
            'path': export_filepath,
            'download_url': url_for('train.download_file', filename=relative_path)
        })
    except Exception as e:
        return make_manager_response({'error': str(e)}, status=500)

@train_bp.route('/download/<path:filename>')
def download_file(filename: str):
    full_path = os.path.join(os.getcwd(), filename)
    if not os.path.exists(full_path):
        return make_manager_response({'error': '文件不存在'}, status=404)

    return send_file(
        full_path,
        as_attachment=True,
        download_name=os.path.basename(filename)
    )
