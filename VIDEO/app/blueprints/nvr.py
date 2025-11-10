"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
from flask import Blueprint, request, jsonify
from app.services.nvr_service import *

# 创建NVR蓝图
nvr_bp = Blueprint('nvr', __name__)

def api_response(code=200, message="success", data=None):
    """统一API响应格式"""
    response = {
        "code": code,
        "message": message,
        "data": data
    }
    return jsonify(response), code

@nvr_bp.route('/register', methods=['POST'])
def api_register_nvr():
    """注册NVR"""
    try:
        data = request.get_json()
        if not data:
            return api_response(400, "请求数据不能为空")

        nvr_id = register_nvr(data)
        return api_response(data={'id': nvr_id})

    except ValueError as e:  # 参数验证失败
        logger.error(f'注册失败: {str(e)}')
        return api_response(400, str(e))
    except LookupError as e:  # 资源不存在
        logger.error(f'注册失败: {str(e)}')
        return api_response(404, str(e))
    except RuntimeError as e:  # 操作执行失败
        logger.error(f'注册失败: {str(e)}')
        return api_response(500, str(e))
    except Exception as e:
        logger.error(f'注册失败: {str(e)}')
        return api_response(500, f'注册失败: {str(e)}')


@nvr_bp.route('/info/<int:nvr_id>', methods=['GET'])
def api_get_nvr_info(nvr_id):
    """获取NVR信息"""
    try:
        info = get_nvr_info(nvr_id)
        return api_response(data=info)

    except LookupError as e:  # NVR不存在
        logger.error(f'获取信息失败: {str(e)}')
        return api_response(404, str(e))
    except Exception as e:
        logger.error(f'获取信息失败: {str(e)}')
        return api_response(500, f'获取信息失败: {str(e)}')


@nvr_bp.route('/delete/<int:nvr_id>', methods=['DELETE'])
def api_delete_nvr(nvr_id):
    """删除NVR"""
    try:
        delete_nvr(nvr_id)
        return api_response(message='删除成功')

    except LookupError as e:  # NVR不存在
        logger.error(f'删除NVR失败: {str(e)}')
        return api_response(404, str(e))
    except Exception as e:
        logger.error(f'删除NVR失败: {str(e)}')
        return api_response(500, f'删除失败: {str(e)}')


@nvr_bp.route('/create/<int:nvr_id>/camera', methods=['POST'])
def api_add_nvr_camera(nvr_id):
    """添加NVR子摄像头"""
    try:
        data = request.get_json()
        if not data:
            return api_response(400, "请求数据不能为空")

        add_nvr_camera(nvr_id, data)
        return api_response(message='添加成功')

    except LookupError as e:  # NVR不存在
        logger.error(f'添加NVR子摄像头失败: {str(e)}')
        return api_response(404, str(e))
    except ValueError as e:  # 参数错误
        logger.error(f'添加NVR子摄像头失败: {str(e)}')
        return api_response(400, str(e))
    except RuntimeError as e:  # 操作失败
        logger.error(f'添加NVR子摄像头失败: {str(e)}')
        return api_response(500, str(e))
    except Exception as e:
        logger.error(f'添加NVR子摄像头失败: {str(e)}')
        return api_response(500, f'添加失败: {str(e)}')