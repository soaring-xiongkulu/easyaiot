from flask import Blueprint, request, jsonify
from app.services.nvr_service import *

# 创建NVR蓝图
nvr_bp = Blueprint('nvr', __name__)

@nvr_bp.route('/nvr', methods=['POST'])
def register_nvr():
    """注册NVR"""
    try:
        data = request.get_json()
        nvr_id = register_nvr(data)
        return jsonify({'success': True, 'id': nvr_id})
    except ValueError as e:  # 参数验证失败
        return jsonify({'success': False, 'message': str(e)}), 400
    except LookupError as e:  # 资源不存在
        return jsonify({'success': False, 'message': str(e)}), 404
    except RuntimeError as e:  # 操作执行失败
        return jsonify({'success': False, 'message': str(e)}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'注册失败: {str(e)}'}), 500

@nvr_bp.route('/nvr/<int:nvr_id>', methods=['GET'])
def get_nvr_info(nvr_id):
    """获取NVR信息"""
    try:
        info = get_nvr_info(nvr_id)
        return jsonify({'success': True, 'data': info})
    except LookupError as e:  # NVR不存在
        return jsonify({'success': False, 'message': str(e)}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取信息失败: {str(e)}'}), 500

@nvr_bp.route('/nvr', methods=['GET'])
def get_nvr_list():
    """获取NVR列表"""
    try:
        nvrs = get_nvr_list()
        return jsonify({'success': True, 'data': nvrs})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取列表失败: {str(e)}'}), 500

@nvr_bp.route('/nvr/<int:nvr_id>', methods=['DELETE'])
def delete_nvr(nvr_id):
    """删除NVR"""
    try:
        delete_nvr(nvr_id)
        return jsonify({'success': True, 'message': '删除成功'})
    except LookupError as e:  # NVR不存在
        return jsonify({'success': False, 'message': str(e)}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500

@nvr_bp.route('/nvr/<int:nvr_id>', methods=['PATCH'])
def patch_nvr(nvr_id):
    """修改NVR信息"""
    try:
        data = request.get_json()
        patch_nvr(nvr_id, data)
        return jsonify({'success': True, 'message': '修改成功'})
    except LookupError as e:  # NVR不存在
        return jsonify({'success': False, 'message': str(e)}), 404
    except ValueError as e:  # 参数错误
        return jsonify({'success': False, 'message': str(e)}), 400
    except RuntimeError as e:  # 操作失败
        return jsonify({'success': False, 'message': str(e)}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'修改失败: {str(e)}'}), 500

@nvr_bp.route('/nvr/<int:nvr_id>/camera', methods=['POST'])
def add_nvr_camera(nvr_id):
    """添加NVR子摄像头"""
    try:
        data = request.get_json()
        add_nvr_camera(nvr_id, data)
        return jsonify({'success': True, 'message': '添加成功'})
    except LookupError as e:  # NVR不存在
        return jsonify({'success': False, 'message': str(e)}), 404
    except ValueError as e:  # 参数错误
        return jsonify({'success': False, 'message': str(e)}), 400
    except RuntimeError as e:  # 操作失败
        return jsonify({'success': False, 'message': str(e)}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'添加失败: {str(e)}'}), 500

@nvr_bp.route('/nvr/<int:nvr_id>/camera/<int:nvr_channel>', methods=['GET'])
def get_nvr_camera_info(nvr_id, nvr_channel):
    """获取NVR子摄像头信息"""
    try:
        info = get_nvr_camera_info(nvr_id, nvr_channel)
        return jsonify({'success': True, 'data': info})
    except LookupError as e:  # NVR或摄像头不存在
        return jsonify({'success': False, 'message': str(e)}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取信息失败: {str(e)}'}), 500

@nvr_bp.route('/nvr/<int:nvr_id>/camera/<int:nvr_channel>', methods=['DELETE'])
def delete_nvr_camera(nvr_id, nvr_channel):
    """删除NVR子摄像头"""
    try:
        delete_nvr_camera(nvr_id, nvr_channel)
        return jsonify({'success': True, 'message': '删除成功'})
    except LookupError as e:  # NVR或摄像头不存在
        return jsonify({'success': False, 'message': str(e)}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500

@nvr_bp.route('/nvr/<int:nvr_id>/camera/<int:nvr_channel>', methods=['PATCH'])
def patch_nvr_camera(nvr_id, nvr_channel):
    """修改NVR子摄像头信息"""
    try:
        data = request.get_json()
        patch_nvr_camera(nvr_id, nvr_channel, data)
        return jsonify({'success': True, 'message': '修改成功'})
    except LookupError as e:  # NVR或摄像头不存在
        return jsonify({'success': False, 'message': str(e)}), 404
    except ValueError as e:  # 参数错误
        return jsonify({'success': False, 'message': str(e)}), 400
    except RuntimeError as e:  # 操作失败
        return jsonify({'success': False, 'message': str(e)}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'修改失败: {str(e)}'}), 500