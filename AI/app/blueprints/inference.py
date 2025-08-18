from flask import Blueprint, request, jsonify
from models import Project
from app.services.inference_service import InferenceService

inference_bp = Blueprint('inference', __name__)

@inference_bp.route('/project/<int:project_id>/inference/run', methods=['POST'])
def run_inference(project_id):
    """执行模型推理"""
    project = Project.query.get_or_404(project_id)

    try:
        # 获取表单数据
        model_type = request.form.get('model_type')
        inference_type = request.form.get('inference_type')
        system_model = request.form.get('system_model')

        # 获取上传的文件
        model_file = request.files.get('model_file')
        image_file = request.files.get('image_file')
        video_file = request.files.get('video_file')
        rtsp_url = request.form.get('rtsp_url')

        # 创建推理管理器
        inference_manager = InferenceService(project_id)

        # 加载模型
        model = inference_manager.load_model(model_type, system_model, model_file)

        # 根据推理类型执行推理
        if inference_type == 'image':
            if not image_file or image_file.filename == '':
                return jsonify({
                    'success': False,
                    'error': '未选择图片文件'
                })

            result = inference_manager.inference_image(model, image_file)
            return jsonify({
                'success': True,
                'result': result
            })

        elif inference_type == 'video':
            if not video_file or video_file.filename == '':
                return jsonify({
                    'success': False,
                    'error': '未选择视频文件'
                })

            result = inference_manager.inference_video(model, video_file)
            return jsonify({
                'success': True,
                'result': result
            })

        elif inference_type == 'rtsp':
            if not rtsp_url:
                return jsonify({
                    'success': False,
                    'error': '未提供RTSP流地址'
                })

            result = inference_manager.inference_rtsp(model, rtsp_url)
            return jsonify({
                'success': True,
                'result': result
            })

        else:
            return jsonify({
                'success': False,
                'error': f'不支持的推理类型: {inference_type}'
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })