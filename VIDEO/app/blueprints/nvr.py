from flask import Blueprint, request, jsonify
from app.services.nvr_service import *

# 创建NVR蓝图
nvr_bp = Blueprint('nvr', __name__)

@nvr_bp.route('/register', methods=['POST'])
def api_register_nvr():
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

@nvr_bp.route('/info/<int:nvr_id>', methods=['GET'])
def api_get_nvr_info(nvr_id):
    """获取NVR信息"""
    try:
        info = get_nvr_info(nvr_id)
        return jsonify({'success': True, 'data': info})
    except LookupError as e:  # NVR不存在
        return jsonify({'success': False, 'message': str(e)}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取信息失败: {str(e)}'}), 500

@nvr_bp.route('/delete/<int:nvr_id>', methods=['DELETE'])
def api_delete_nvr(nvr_id):
    """删除NVR"""
    try:
        delete_nvr(nvr_id)
        return jsonify({'success': True, 'message': '删除成功'})
    except LookupError as e:  # NVR不存在
        return jsonify({'success': False, 'message': str(e)}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500

@nvr_bp.route('/create/<int:nvr_id>/camera', methods=['POST'])
def api_add_nvr_camera(nvr_id):
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