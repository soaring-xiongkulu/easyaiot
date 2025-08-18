from flask import Blueprint, request, jsonify

from models import Project
camera_bp = Blueprint('camera', __name__)

@camera_bp.route('/api/project/<int:project_id>/rtsp/start', methods=['POST'])
def api_start_rtsp_capture(project_id):
    """启动RTSP截图"""
    try:
        project = Project.query.get_or_404(project_id)
        data = request.get_json()

        rtsp_url = data.get('rtsp_url')
        interval = data.get('interval', 5)
        max_count = data.get('max_count', 10)

        if not rtsp_url:
            return jsonify({'success': False, 'message': 'RTSP地址不能为空'})

        # 启动RTSP截图线程
        from app import create_app
        application = create_app()

        def rtsp_thread():
            with application.app_context():
                camera_capture = application.camera_capture
                camera_capture.capture_rtsp_images(project_id, rtsp_url, interval, max_count)

        thread = threading.Thread(target=rtsp_thread)
        thread.daemon = True
        thread.start()

        return jsonify({'success': True, 'message': 'RTSP截图已启动'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@camera_bp.route('/api/project/<int:project_id>/rtsp/stop', methods=['POST'])
def api_stop_rtsp_capture(project_id):
    """停止RTSP截图"""
    try:
        from app import create_app
        application = create_app()
        with application.app_context():
            camera_capture = application.camera_capture
            camera_capture.stop_rtsp_capture(project_id)

        return jsonify({'success': True, 'message': 'RTSP截图已停止'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@camera_bp.route('/api/project/<int:project_id>/rtsp/status')
def api_rtsp_status(project_id):
    """获取RTSP截图状态"""
    try:
        from app import create_app
        application = create_app()
        with application.app_context():
            camera_capture = application.camera_capture
            status = camera_capture.get_rtsp_status(project_id)

        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@camera_bp.route('/api/onvif/discover')
def api_discover_onvif_devices():
    """发现ONVIF设备"""
    try:
        from app import create_app
        application = create_app()
        with application.app_context():
            camera_capture = application.camera_capture
            devices = camera_capture.discover_onvif_devices()

        return jsonify({'success': True, 'devices': devices})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@camera_bp.route('/api/onvif/<device_ip>/<device_port>/profiles', methods=['POST'])
def api_get_onvif_profiles(device_ip, device_port):
    """获取ONVIF设备的配置文件列表"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'})

        from app import create_app
        application = create_app()
        with application.app_context():
            camera_capture = application.camera_capture
            profiles = camera_capture.get_onvif_profiles(device_ip, device_port, username, password)

        return jsonify({'success': True, 'profiles': profiles})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@camera_bp.route('/api/project/<int:project_id>/onvif/start', methods=['POST'])
def api_start_onvif_capture(project_id):
    """启动ONVIF截图"""
    try:
        project = Project.query.get_or_404(project_id)
        data = request.get_json()

        device_ip = data.get('device_ip')
        device_port = data.get('device_port')
        username = data.get('username')
        password = data.get('password')
        profile_token = data.get('profile_token')
        interval = data.get('interval', 5)
        max_count = data.get('max_count', 10)

        if not all([device_ip, device_port, username, password, profile_token]):
            return jsonify({'success': False, 'message': '设备信息不完整'})

        # 启动ONVIF截图线程（使用改进版本）
        from app import create_app
        application = create_app()

        def onvif_thread():
            with application.app_context():
                camera_capture = application.camera_capture
                # 使用改进的截图方法
                camera_capture.capture_onvif_images_improved(
                    project_id, device_ip, device_port, username, password,
                    profile_token, interval, max_count)

        thread = threading.Thread(target=onvif_thread)
        thread.daemon = True
        thread.start()

        return jsonify({'success': True, 'message': 'ONVIF截图已启动'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@camera_bp.route('/api/project/<int:project_id>/onvif/stop', methods=['POST'])
def api_stop_onvif_capture(project_id):
    """停止ONVIF截图"""
    try:
        data = request.get_json()
        profile_token = data.get('profile_token')

        if not profile_token:
            return jsonify({'success': False, 'message': '配置文件token不能为空'})

        from app import create_app
        application = create_app()
        with application.app_context():
            camera_capture = application.camera_capture
            camera_capture.stop_onvif_capture(project_id, profile_token)

        return jsonify({'success': True, 'message': 'ONVIF截图已停止'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@camera_bp.route('/api/project/<int:project_id>/onvif/status', methods=['POST'])
def api_onvif_status(project_id):
    """获取ONVIF截图状态"""
    try:
        data = request.get_json()
        profile_token = data.get('profile_token')

        if not profile_token:
            return jsonify({'success': False, 'message': '配置文件token不能为空'})

        from app import create_app
        application = create_app()
        with application.app_context():
            camera_capture = application.camera_capture
            status = camera_capture.get_onvif_status(project_id, profile_token)

        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
