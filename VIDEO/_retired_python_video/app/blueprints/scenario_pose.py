"""场景姿态库 HTTP 路由"""
import logging

from flask import Blueprint, jsonify, request

from app.services import scenario_pose_library_service as pose_lib_svc

scenario_pose_bp = Blueprint('scenario_pose', __name__)
logger = logging.getLogger(__name__)


def _read_upload_bytes() -> bytes:
    if 'file' not in request.files:
        raise ValueError('请上传文件字段 file')
    file_obj = request.files['file']
    if file_obj is None or file_obj.filename is None or not file_obj.filename.strip():
        raise ValueError('上传文件不能为空')
    return file_obj.read()


@scenario_pose_bp.route('/libraries', methods=['GET'])
def list_libraries():
    try:
        search = request.args.get('search', '').strip() or None
        is_enabled_raw = request.args.get('is_enabled')
        is_enabled = None
        if is_enabled_raw is not None and is_enabled_raw != '':
            is_enabled = str(is_enabled_raw).lower() in {'1', 'true', 'yes'}
        data = pose_lib_svc.list_libraries(search=search, is_enabled=is_enabled)
        return jsonify({'code': 0, 'msg': 'success', 'data': data, 'total': len(data)})
    except Exception as e:
        logger.error('查询场景姿态库列表失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'查询失败: {str(e)}'}), 500


@scenario_pose_bp.route('/libraries/<int:library_id>', methods=['GET'])
def get_library(library_id: int):
    try:
        include_entries = str(request.args.get('include_entries', 'false')).lower() in {'1', 'true', 'yes'}
        data = pose_lib_svc.get_library(library_id, include_entries=include_entries)
        return jsonify({'code': 0, 'msg': 'success', 'data': data})
    except Exception as e:
        logger.error('查询场景姿态库失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'查询失败: {str(e)}'}), 500


@scenario_pose_bp.route('/libraries', methods=['POST'])
def create_library():
    try:
        data = request.get_json(silent=True) or {}
        library = pose_lib_svc.create_library(
            name=data.get('name'),
            scene_category=data.get('scene_category'),
            business_tags=data.get('business_tags'),
            description=data.get('description'),
            similarity_threshold=data.get('similarity_threshold', 0.72),
            match_mode=data.get('match_mode', 'angle'),
            intent_event=data.get('intent_event'),
            intent_object=data.get('intent_object'),
            alert_level=data.get('alert_level', 'warning'),
            is_enabled=data.get('is_enabled', True),
        )
        return jsonify({'code': 0, 'msg': '创建成功', 'data': library.to_dict()})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error('创建场景姿态库失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'创建失败: {str(e)}'}), 500


@scenario_pose_bp.route('/libraries/<int:library_id>', methods=['PUT'])
def update_library(library_id: int):
    try:
        data = request.get_json(silent=True) or {}
        library = pose_lib_svc.update_library(library_id, **data)
        return jsonify({'code': 0, 'msg': '更新成功', 'data': library.to_dict()})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error('更新场景姿态库失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'更新失败: {str(e)}'}), 500


@scenario_pose_bp.route('/libraries/<int:library_id>', methods=['DELETE'])
def delete_library(library_id: int):
    try:
        pose_lib_svc.delete_library(library_id)
        return jsonify({'code': 0, 'msg': '删除成功'})
    except Exception as e:
        logger.error('删除场景姿态库失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'删除失败: {str(e)}'}), 500


@scenario_pose_bp.route('/libraries/<int:library_id>/entries', methods=['GET'])
def list_entries(library_id: int):
    try:
        search = request.args.get('search', '').strip() or None
        data = pose_lib_svc.list_entries(library_id, search=search)
        return jsonify({'code': 0, 'msg': 'success', 'data': data, 'total': len(data)})
    except Exception as e:
        logger.error('查询场景姿态条目失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'查询失败: {str(e)}'}), 500


@scenario_pose_bp.route('/libraries/<int:library_id>/entries', methods=['POST'])
def add_entry(library_id: int):
    try:
        data = request.get_json(silent=True) or {}
        name = (request.form.get('name') or data.get('name') or '参考姿态').strip()
        remark = request.form.get('remark') or data.get('remark')
        conf = float(request.form.get('conf') or data.get('conf') or 0.25)
        if 'file' in request.files:
            image_bytes = _read_upload_bytes()
            entry = pose_lib_svc.add_entry_from_image(library_id, name, image_bytes, remark=remark, conf=conf)
        else:
            data = request.get_json(silent=True) or {}
            if data.get('source_type') == 'rule' or data.get('extra_rules'):
                entry = pose_lib_svc.add_rule_entry(
                    library_id, data.get('name') or name,
                    data.get('extra_rules') or {},
                    remark=data.get('remark') or remark,
                )
            else:
                return jsonify({'code': 400, 'msg': '请上传参考图片或提供规则条目'}), 400
        return jsonify({'code': 0, 'msg': '添加成功', 'data': entry.to_dict()})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error('添加场景姿态条目失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'添加失败: {str(e)}'}), 500


@scenario_pose_bp.route('/entries/<int:entry_id>', methods=['PUT'])
def update_entry(entry_id: int):
    try:
        data = request.get_json(silent=True) or {}
        entry = pose_lib_svc.update_entry(entry_id, **data)
        return jsonify({'code': 0, 'msg': '更新成功', 'data': entry.to_dict()})
    except Exception as e:
        logger.error('更新场景姿态条目失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'更新失败: {str(e)}'}), 500


@scenario_pose_bp.route('/entries/<int:entry_id>', methods=['DELETE'])
def delete_entry(entry_id: int):
    try:
        pose_lib_svc.delete_entry(entry_id)
        return jsonify({'code': 0, 'msg': '删除成功'})
    except Exception as e:
        logger.error('删除场景姿态条目失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'删除失败: {str(e)}'}), 500


@scenario_pose_bp.route('/entries/<int:entry_id>/re-extract', methods=['POST'])
def re_extract_entry(entry_id: int):
    try:
        data = request.get_json(silent=True) or {}
        conf = float(data.get('conf') or 0.25)
        entry = pose_lib_svc.re_extract_entry(entry_id, conf=conf)
        return jsonify({'code': 0, 'msg': '重新提取成功', 'data': entry.to_dict()})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error('重新提取姿态失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'提取失败: {str(e)}'}), 500


@scenario_pose_bp.route('/entries/extract', methods=['POST'])
def extract_preview():
    try:
        conf = float(request.form.get('conf') or 0.25)
        image_bytes = _read_upload_bytes()
        data = pose_lib_svc.extract_preview(image_bytes, conf=conf)
        return jsonify({'code': 0, 'msg': 'success', 'data': data})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error('姿态提取预览失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'提取失败: {str(e)}'}), 500


@scenario_pose_bp.route('/libraries/<int:library_id>/match-test', methods=['POST'])
def match_test(library_id: int):
    try:
        conf = float(request.form.get('conf') or 0.25)
        image_bytes = _read_upload_bytes()
        data = pose_lib_svc.match_test(library_id, image_bytes, conf=conf)
        return jsonify({'code': 0, 'msg': 'success', 'data': data})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error('姿态匹配测试失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'测试失败: {str(e)}'}), 500


@scenario_pose_bp.route('/scene-templates', methods=['GET'])
def list_scene_templates():
    try:
        return jsonify({'code': 0, 'msg': 'success', 'data': pose_lib_svc.list_scene_templates()})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'查询失败: {str(e)}'}), 500


@scenario_pose_bp.route('/libraries/<int:library_id>/import-template', methods=['POST'])
def import_template(library_id: int):
    try:
        data = request.get_json(silent=True) or {}
        template_key = (data.get('template_key') or data.get('key') or '').strip()
        if not template_key:
            return jsonify({'code': 400, 'msg': 'template_key 不能为空'}), 400
        entry = pose_lib_svc.import_scene_template(library_id, template_key)
        return jsonify({'code': 0, 'msg': '导入成功', 'data': entry.to_dict()})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error('导入场景模板失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'导入失败: {str(e)}'}), 500
