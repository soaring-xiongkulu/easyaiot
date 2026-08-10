"""
算法任务管理服务
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.orm import joinedload

from models import db, AlgorithmTask, Device, SnapSpace, algorithm_task_device, Pusher
from app.utils.cron_utils import validate_snap_cron_min_interval
# 注意：已移除冲突检查，推流转发任务和算法任务可以共存
# 推流转发任务使用 rtmp_stream/http_stream，算法任务使用 ai_rtmp_stream/ai_http_stream
import json

logger = logging.getLogger(__name__)

ALERT_EVENT_SUPPRESS_MIN = 1
ALERT_EVENT_SUPPRESS_MAX = 3600
ALARM_SUPPRESS_MIN = 0
ALARM_SUPPRESS_MAX = 86400
_USERLESS_NOTIFY_METHODS = frozenset({'http', 'webhook'})


def _full_defense_schedule_json() -> str:
    return json.dumps([[1] * 24 for _ in range(7)])


def _parse_defense_schedule_matrix(defense_schedule) -> Optional[list]:
    if not defense_schedule:
        return None
    try:
        matrix = json.loads(defense_schedule) if isinstance(defense_schedule, str) else defense_schedule
        if isinstance(matrix, list) and len(matrix) == 7:
            return matrix
    except (TypeError, ValueError, json.JSONDecodeError):
        pass
    return None


def _is_defense_schedule_empty(schedule_matrix: list) -> bool:
    return all(int(h or 0) != 1 for day in schedule_matrix for h in (day or []))


def _normalize_defense_for_alert_event(
        defense_mode: Optional[str],
        defense_schedule: Optional[str],
        alert_event_enabled: bool,
) -> tuple:
    """
    启用告警事件时，若布防时段全为 0，iot-sink 会丢弃全部告警，自动升级为全防。
    """
    mode = (defense_mode or 'full').strip() or 'full'
    if not alert_event_enabled:
        return mode, defense_schedule

    if mode == 'full':
        return 'full', defense_schedule or _full_defense_schedule_json()

    schedule_matrix = _parse_defense_schedule_matrix(defense_schedule)
    if schedule_matrix and _is_defense_schedule_empty(schedule_matrix):
        logger.info('启用告警事件且布防时段为空，自动切换为全防模式')
        return 'full', _full_defense_schedule_json()
    return mode, defense_schedule


def _serialize_matching_business_tags(tags) -> Optional[str]:
    from app.services.library_matching_service import parse_business_tags
    parsed = parse_business_tags(tags)
    return json.dumps(parsed, ensure_ascii=False) if parsed else None


def _serialize_alert_class_names(class_names) -> Optional[str]:
    from app.utils.alert_class_filter import parse_alert_class_names
    parsed = parse_alert_class_names(class_names)
    return json.dumps(parsed, ensure_ascii=False) if parsed else None


def _normalize_library_ids(ids) -> List[int]:
    if ids is None:
        return []
    if isinstance(ids, int):
        return [ids]
    if isinstance(ids, str):
        text = ids.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [int(x) for x in parsed if x is not None and str(x).strip() != '']
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
        try:
            return [int(text)]
        except (TypeError, ValueError):
            return []
    if isinstance(ids, list):
        result = []
        for item in ids:
            try:
                result.append(int(item))
            except (TypeError, ValueError):
                continue
        return result
    return []


def _serialize_library_ids(ids) -> Optional[str]:
    parsed = _normalize_library_ids(ids)
    return json.dumps(parsed, ensure_ascii=False) if parsed else None


def _serialize_sam_supplement_config(config) -> Optional[str]:
    if config is None:
        return None
    if isinstance(config, str):
        return config if config.strip() else None
    if isinstance(config, dict):
        return json.dumps(config, ensure_ascii=False)
    return None


def _serialize_motion_gate_config(config) -> Optional[str]:
    if config is None:
        return None
    if isinstance(config, str):
        return config if config.strip() else None
    if isinstance(config, dict):
        return json.dumps(config, ensure_ascii=False)
    return None


def _serialize_pose_analysis_config(config) -> Optional[str]:
    if config is None:
        return None
    if isinstance(config, str):
        return config if config.strip() else None
    if isinstance(config, dict):
        return json.dumps(config, ensure_ascii=False)
    return None


def _serialize_pose_intent_config(config) -> Optional[str]:
    if config is None:
        return None
    if isinstance(config, str):
        return config if config.strip() else None
    if isinstance(config, dict):
        return json.dumps(config, ensure_ascii=False)
    return None


def _normalize_pose_intent_fields(
    *,
    pose_intent_enabled: bool,
    pose_analysis_enabled: bool,
    pose_library_ids,
) -> tuple:
    """姿态意图启用时自动开启姿态分析，并校验库绑定。"""
    intent_on = bool(pose_intent_enabled)
    pose_on = bool(pose_analysis_enabled) or intent_on
    lib_ids = _normalize_library_ids(pose_library_ids)
    if intent_on:
        if not _has_library_matching_scope(lib_ids):
            raise ValueError('启用姿态意图分析时必须指定至少一个场景姿态库')
        from models import ScenarioPoseLibrary
        for lib_id in lib_ids:
            ScenarioPoseLibrary.query.get_or_404(lib_id)
    elif not intent_on:
        lib_ids = []
    return intent_on, pose_on, lib_ids


def _normalize_detect_conf(value) -> float:
    if value is None:
        return 0.5
    try:
        conf = float(value)
    except (TypeError, ValueError):
        raise ValueError('检测置信度格式无效')
    if conf < 0.01 or conf > 0.99:
        raise ValueError('检测置信度必须在 1% ~ 99% 之间')
    return conf


def _has_library_matching_scope(library_ids) -> bool:
    return bool(_normalize_library_ids(library_ids))


def _has_userless_channel(channels: List[Dict]) -> bool:
    return any(_is_userless_channel(ch) for ch in (channels or []))


def _is_userless_channel(channel: Dict) -> bool:
    if not channel:
        return False
    if channel.get('userless'):
        return True
    method = (channel.get('method') or '').lower()
    if method in _USERLESS_NOTIFY_METHODS:
        return True
    return False


def _enrich_channels_userless_flags(channels: List[Dict]) -> List[Dict]:
    """为无需通知人的渠道（HTTP/Webhook、企业微信/钉钉/飞书群机器人）标记 userless。"""
    if not channels:
        return channels

    enriched = []
    for channel in channels:
        ch = dict(channel)
        method = (ch.get('method') or '').lower()
        if _is_userless_channel(ch):
            ch['userless'] = True
            enriched.append(ch)
            continue

        if method in ('wxcp', 'wechat', 'weixin') and ch.get('template_id'):
            template_meta = _fetch_message_template_meta(method, ch.get('template_id'))
            if template_meta and (
                template_meta.get('radioType') == '群机器人消息'
                or template_meta.get('webHook')
            ):
                ch['userless'] = True
        elif method in ('ding', 'dingtalk') and ch.get('template_id'):
            template_meta = _fetch_message_template_meta(method, ch.get('template_id'))
            if template_meta and (
                template_meta.get('radioType') == '群机器人消息'
                or template_meta.get('webHook')
            ):
                ch['userless'] = True
        elif method in ('feishu', 'lark') and ch.get('template_id'):
            template_meta = _fetch_message_template_meta(method, ch.get('template_id'))
            if template_meta and (
                template_meta.get('radioType') == '群机器人消息'
                or template_meta.get('webHook')
            ):
                ch['userless'] = True
        enriched.append(ch)
    return enriched


def _message_service_base_url() -> str:
    import os
    try:
        from flask import current_app
        url = current_app.config.get('MESSAGE_SERVICE_URL') or os.getenv('MESSAGE_SERVICE_URL', 'http://localhost:48080')
    except RuntimeError:
        url = os.getenv('MESSAGE_SERVICE_URL', 'http://localhost:48080')
    return str(url).rstrip('/')


def _message_internal_api_headers() -> Dict[str, str]:
    """告警通知链路内网调用消息服务：仅传 tenant-id，不传 JWT（过期 Token 会被网关 401 拦截）。"""
    import os
    tenant_id = '1'
    try:
        from flask import current_app
        tenant_id = str(current_app.config.get('TENANT_ID', os.getenv('TENANT_ID', '1')))
    except RuntimeError:
        tenant_id = str(os.getenv('TENANT_ID', '1'))
    return {'tenant-id': tenant_id}


def _message_database_url() -> str:
    """消息服务数据库连接串（API 不可用时用于查询群机器人模板元数据）。"""
    import os
    url = (os.getenv('MESSAGE_DATABASE_URL') or '').strip()
    if url:
        return url
    video_url = (os.getenv('DATABASE_URL') or '').strip()
    if video_url and 'iot-video' in video_url:
        return video_url.replace('iot-video20', 'iot-message20')
    return 'postgresql://postgres:iot45722414822@localhost:5432/iot-message20'


def _fetch_message_template_meta_from_db(method: str, template_id) -> Optional[Dict]:
    """从消息库直接查询模板元数据（HTTP API 鉴权失败时的后备）。"""
    if not template_id:
        return None
    try:
        import psycopg2

        method = (method or '').lower()
        conn = psycopg2.connect(_message_database_url())
        try:
            cur = conn.cursor()
            if method in ('wxcp', 'wechat', 'weixin'):
                cur.execute(
                    'SELECT radio_type, web_hook FROM t_msg_wx_cp WHERE id = %s',
                    (str(template_id),),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return {'radioType': row[0], 'webHook': row[1]}
            if method in ('ding', 'dingtalk'):
                cur.execute(
                    'SELECT radio_type, web_hook FROM t_msg_ding WHERE id = %s',
                    (str(template_id),),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return {'radioType': row[0], 'webHook': row[1]}
            if method in ('feishu', 'lark'):
                cur.execute(
                    'SELECT web_hook FROM t_msg_feishu WHERE id = %s',
                    (str(template_id),),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return {'webHook': row[0]}
            if method in ('http', 'webhook'):
                cur.execute(
                    'SELECT url FROM t_msg_http WHERE id = %s',
                    (str(template_id),),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return {'url': row[0]}
        finally:
            conn.close()
    except Exception as e:
        logger.debug(
            f"从消息库查询模板元数据失败: method={method}, template_id={template_id}, error={e}"
        )
    return None


def _fetch_message_template_meta(method: str, template_id) -> Optional[Dict]:
    """查询消息模板元数据，用于判断企业微信群机器人等免通知人渠道。"""
    if not template_id:
        return None
    try:
        import os
        import requests

        method_to_msg_type = {
            'wxcp': 4, 'wechat': 4, 'weixin': 4,
            'http': 5, 'webhook': 5,
            'ding': 6, 'dingtalk': 6,
            'feishu': 7, 'lark': 7,
        }
        msg_type = method_to_msg_type.get((method or '').lower())
        if not msg_type:
            return None

        try:
            from flask import current_app
            message_service_url = _message_service_base_url()
        except RuntimeError:
            message_service_url = _message_service_base_url()

        headers = _message_internal_api_headers()
        try:
            response = requests.get(
                f"{message_service_url}/admin-api/message/template/get",
                params={'id': template_id, 'msgType': msg_type},
                headers=headers,
                timeout=5,
            )
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0 or result.get('success'):
                    data = result.get('data') or result
                    if isinstance(data, dict):
                        return data
        except Exception:
            pass
    except Exception as e:
        logger.debug(f"查询消息模板元数据失败: method={method}, template_id={template_id}, error={e}")
    return _fetch_message_template_meta_from_db(method, template_id)


def _normalize_alert_interval_fields(
    alert_event_suppress_time: Optional[int] = None,
    alarm_suppress_time: Optional[int] = None,
) -> Dict[str, int]:
    """校验并规范化告警事件/通知抑制时间（秒）。"""
    result = {}
    if alert_event_suppress_time is not None:
        try:
            event_sec = int(alert_event_suppress_time)
        except (TypeError, ValueError):
            raise ValueError('告警事件抑制时间必须是整数（秒）')
        if event_sec < ALERT_EVENT_SUPPRESS_MIN or event_sec > ALERT_EVENT_SUPPRESS_MAX:
            raise ValueError(
                f'告警事件抑制时间须在 {ALERT_EVENT_SUPPRESS_MIN}-{ALERT_EVENT_SUPPRESS_MAX} 秒之间'
            )
        result['alert_event_suppress_time'] = event_sec
    if alarm_suppress_time is not None:
        try:
            notify_sec = int(alarm_suppress_time)
        except (TypeError, ValueError):
            raise ValueError('告警通知抑制时间必须是整数（秒）')
        if notify_sec < ALARM_SUPPRESS_MIN or notify_sec > ALARM_SUPPRESS_MAX:
            raise ValueError(
                f'告警通知抑制时间须在 {ALARM_SUPPRESS_MIN}-{ALARM_SUPPRESS_MAX} 秒之间'
            )
        result['alarm_suppress_time'] = notify_sec
    return result


def _extract_notify_users_from_templates(channels: List[Dict]) -> List[Dict]:
    """
    从消息模板中提取通知人信息并保存到配置中
    通知人不只是推送消息的信息，推送消息下面还关联着用户分组和用户管理，
    最终要拿到具体每个用户的通知方式和具体内容（邮箱号、手机号等）
    
    Args:
        channels: 通知渠道列表，格式：[{"method": "sms", "template_id": "xxx", "template_name": "xxx"}, ...]
    
    Returns:
        list: 通知人列表，格式：[{"id": "xxx", "name": "xxx", "phone": "xxx", "email": "xxx", ...}, ...]
    """
    notify_users = []
    if not channels:
        return notify_users
    
    try:
        import os
        import requests
        
        # 获取消息服务API地址（内网免 Token 调用）
        message_service_url = _message_service_base_url()
        headers = _message_internal_api_headers()
        
        # 消息类型映射
        method_to_msg_type = {
            'sms': 1,  # 短信（阿里云/腾讯云）
            'email': 3,  # 邮件
            'mail': 3,  # 邮件（别名）
            'wxcp': 4,  # 企业微信
            'wechat': 4,  # 企业微信（别名）
            'weixin': 4,  # 企业微信（别名）
            'http': 5,  # HTTP
            'webhook': 5,  # HTTP（别名）
            'ding': 6,  # 钉钉
            'dingtalk': 6,  # 钉钉（别名）
            'feishu': 7,  # 飞书
            'lark': 7,  # 飞书（别名）
        }
        
        # 使用字典去重，key为用户ID
        all_notify_users = {}
        
        for channel in channels:
            method = channel.get('method', '').lower()
            if _is_userless_channel(channel):
                continue
            template_id = channel.get('template_id')
            
            if not template_id:
                continue
            
            msg_type = method_to_msg_type.get(method)
            if not msg_type:
                logger.warning(f"不支持的通知方式: {method}")
                continue
            
            try:
                # 调用消息服务API获取模板详情（通过网关访问）
                template_url = f"{message_service_url}/admin-api/message/template/get"
                params = {
                    'id': template_id,
                    'msgType': msg_type
                }
                
                logger.info(f"📞 调用消息服务API获取模板详情: method={method}, template_id={template_id}, msg_type={msg_type}, url={template_url}")
                
                response = requests.get(template_url, params=params, headers=headers, timeout=5)
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"📥 模板API响应: code={result.get('code')}, success={result.get('success')}")
                    if result.get('code') == 0 or result.get('success'):
                        template_data = result.get('data') or result
                        logger.info(f"📋 模板数据: {template_data}")
                        
                        # 获取userGroupId
                        user_group_id = template_data.get('userGroupId') or template_data.get('user_group_id')
                        logger.info(f"👥 从模板获取到userGroupId: {user_group_id}")
                        
                        if user_group_id:
                            # 第一步：调用用户组API获取用户组详情（包含preview_user_id和用户列表）（通过网关访问）
                            user_group_detail_url = f"{message_service_url}/admin-api/message/preview/user/group/query"
                            user_group_detail_params = {'id': user_group_id}
                            
                            logger.info(f"📞 调用用户组API: url={user_group_detail_url}, params={user_group_detail_params}")
                            user_group_detail_response = requests.get(user_group_detail_url, params=user_group_detail_params, headers=headers, timeout=5)
                            
                            if user_group_detail_response.status_code == 200:
                                user_group_detail_result = user_group_detail_response.json()
                                logger.info(f"📥 用户组API响应: code={user_group_detail_result.get('code')}, success={user_group_detail_result.get('success')}")
                                if user_group_detail_result.get('code') == 0 or user_group_detail_result.get('success'):
                                    # 获取用户组数据（TableDataInfo的data字段是列表）
                                    user_group_list = user_group_detail_result.get('data', [])
                                    if not isinstance(user_group_list, list):
                                        user_group_list = []
                                    
                                    logger.info(f"👥 用户组列表长度: {len(user_group_list)}")
                                    if user_group_list and len(user_group_list) > 0:
                                        user_group_data = user_group_list[0]
                                        logger.info(f"📋 用户组数据: {user_group_data}")
                                        
                                        # 优先使用用户组返回的用户列表（如果包含）
                                        t_preview_users = user_group_data.get('tPreviewUsers') or user_group_data.get('t_preview_users')
                                        logger.info(f"👤 用户组中的用户列表: tPreviewUsers={t_preview_users}")
                                        
                                        if t_preview_users and isinstance(t_preview_users, list) and len(t_preview_users) > 0:
                                            # 直接使用用户组返回的用户列表
                                            for user_detail_data in t_preview_users:
                                                if isinstance(user_detail_data, dict):
                                                    # 获取用户的msgType（优先使用用户自己的msgType）
                                                    user_msg_type = user_detail_data.get('msgType') or msg_type
                                                    
                                                    # 构建完整的用户信息（提取所有字段）
                                                    user_info = {
                                                        'id': user_detail_data.get('id'),
                                                        'msgType': user_msg_type,
                                                        'previewUser': user_detail_data.get('previewUser') or user_detail_data.get('preview_user'),
                                                        'name': user_detail_data.get('name'),  # 如果有name字段
                                                    }
                                                    
                                                    # 根据用户的msgType提取对应的联系方式（而不是channel的method）
                                                    preview_user = user_info.get('previewUser')
                                                    if preview_user:
                                                        # 根据msgType设置联系方式
                                                        if user_msg_type == 1:  # 短信
                                                            user_info['phone'] = preview_user
                                                            user_info['mobile'] = preview_user
                                                        elif user_msg_type == 3:  # 邮件
                                                            user_info['email'] = preview_user
                                                            user_info['mail'] = preview_user
                                                        elif user_msg_type == 4:  # 企业微信
                                                            user_info['wxcp_userid'] = preview_user
                                                            user_info['wechat_userid'] = preview_user
                                                        elif user_msg_type == 6:  # 钉钉
                                                            user_info['ding_userid'] = preview_user
                                                            user_info['dingtalk_userid'] = preview_user
                                                        elif user_msg_type == 7:  # 飞书
                                                            user_info['feishu_userid'] = preview_user
                                                            user_info['lark_userid'] = preview_user
                                                    
                                                    # 使用用户ID作为key去重
                                                    user_key = user_info.get('id')
                                                    if user_key and user_key not in all_notify_users:
                                                        all_notify_users[user_key] = user_info
                                                    elif user_key in all_notify_users:
                                                        # 如果已存在，合并信息（保留所有联系方式）
                                                        existing_user = all_notify_users[user_key]
                                                        # 合并时，保留所有联系方式字段
                                                        for key, value in user_info.items():
                                                            if value is not None:
                                                                existing_user[key] = value
                                            
                                            logger.info(f"从模板 {template_id} 的用户组 {user_group_id} 获取到 {len(t_preview_users)} 个用户（从用户组API）")
                                        else:
                                            # 如果用户组API没有返回用户列表，则通过preview_user_id获取
                                            preview_user_ids_str = user_group_data.get('previewUserId') or user_group_data.get('preview_user_id')
                                            
                                            if preview_user_ids_str:
                                                # 第二步：根据用户ID列表获取用户详情
                                                preview_user_ids = [uid.strip() for uid in preview_user_ids_str.split(',') if uid.strip()]
                                                
                                                if preview_user_ids:
                                                    # 调用用户API获取用户详情（通过网关访问）
                                                    for user_id in preview_user_ids:
                                                        try:
                                                            user_detail_url = f"{message_service_url}/admin-api/message/preview/user/query"
                                                            user_detail_params = {'id': user_id, 'msgType': msg_type}
                                                            
                                                            user_detail_response = requests.get(user_detail_url, params=user_detail_params, headers=headers, timeout=5)
                                                            
                                                            if user_detail_response.status_code == 200:
                                                                user_detail_result = user_detail_response.json()
                                                                if user_detail_result.get('code') == 0 or user_detail_result.get('success'):
                                                                    # 获取用户数据（TableDataInfo的data字段是列表）
                                                                    user_detail_list = user_detail_result.get('data', [])
                                                                    if not isinstance(user_detail_list, list):
                                                                        user_detail_list = []
                                                                    
                                                                    if user_detail_list and len(user_detail_list) > 0:
                                                                        user_detail_data = user_detail_list[0]
                                                                        
                                                                        # 获取用户的msgType（优先使用用户自己的msgType）
                                                                        user_msg_type = user_detail_data.get('msgType') or msg_type
                                                                        
                                                                        # 构建完整的用户信息（提取所有字段）
                                                                        user_info = {
                                                                            'id': user_detail_data.get('id') or user_id,
                                                                            'msgType': user_msg_type,
                                                                            'previewUser': user_detail_data.get('previewUser') or user_detail_data.get('preview_user'),
                                                                            'name': user_detail_data.get('name'),  # 如果有name字段
                                                                        }
                                                                        
                                                                        # 根据用户的msgType提取对应的联系方式（而不是channel的method）
                                                                        preview_user = user_info.get('previewUser')
                                                                        if preview_user:
                                                                            # 根据msgType设置联系方式
                                                                            if user_msg_type == 1:  # 短信
                                                                                user_info['phone'] = preview_user
                                                                                user_info['mobile'] = preview_user
                                                                            elif user_msg_type == 3:  # 邮件
                                                                                user_info['email'] = preview_user
                                                                                user_info['mail'] = preview_user
                                                                            elif user_msg_type == 4:  # 企业微信
                                                                                user_info['wxcp_userid'] = preview_user
                                                                                user_info['wechat_userid'] = preview_user
                                                                            elif user_msg_type == 6:  # 钉钉
                                                                                user_info['ding_userid'] = preview_user
                                                                                user_info['dingtalk_userid'] = preview_user
                                                                            elif user_msg_type == 7:  # 飞书
                                                                                user_info['feishu_userid'] = preview_user
                                                                                user_info['lark_userid'] = preview_user
                                                                        
                                                                        # 使用用户ID作为key去重
                                                                        user_key = user_info.get('id')
                                                                        if user_key and user_key not in all_notify_users:
                                                                            all_notify_users[user_key] = user_info
                                                                        elif user_key in all_notify_users:
                                                                            # 如果已存在，合并信息（保留所有联系方式）
                                                                            existing_user = all_notify_users[user_key]
                                                                            # 合并时，保留所有联系方式字段
                                                                            for key, value in user_info.items():
                                                                                if value is not None:
                                                                                    existing_user[key] = value
                                                                            
                                                        except requests.exceptions.RequestException as e:
                                                            logger.warning(f"获取用户 {user_id} 详情失败: {str(e)}")
                                                            continue
                                                        except Exception as e:
                                                            logger.warning(f"获取用户 {user_id} 详情异常: {str(e)}")
                                                            continue
                                                    
                                                    logger.info(f"从模板 {template_id} 的用户组 {user_group_id} 获取到 {len(preview_user_ids)} 个用户（通过用户API）")
                                                else:
                                                    logger.warning(f"用户组 {user_group_id} 中没有配置用户ID")
                                            else:
                                                logger.warning(f"用户组 {user_group_id} 中没有配置 previewUserId")
                                    else:
                                        logger.warning(f"用户组 {user_group_id} 查询结果为空")
                                else:
                                    logger.warning(f"⚠️  获取用户组 {user_group_id} 详情失败: code={user_group_detail_result.get('code')}, msg={user_group_detail_result.get('msg')}, result={user_group_detail_result}")
                            else:
                                logger.warning(f"⚠️  调用用户组API失败: HTTP {user_group_detail_response.status_code}, response={user_group_detail_response.text[:200]}")
                        else:
                            logger.warning(f"⚠️  模板 {template_id} 中没有配置 userGroupId，无法获取通知人信息")
                    else:
                        logger.warning(f"⚠️  获取模板 {template_id} 详情失败: code={result.get('code')}, msg={result.get('msg')}, result={result}")
                else:
                    logger.warning(f"⚠️  调用消息服务API失败: HTTP {response.status_code}, template_id={template_id}, response={response.text[:200]}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"调用消息服务API异常: method={method}, template_id={template_id}, error={str(e)}")
                continue
            except Exception as e:
                logger.warning(f"从消息模板获取通知人异常: method={method}, template_id={template_id}, error={str(e)}")
                continue
        
        # 将字典转换为列表
        notify_users = list(all_notify_users.values())
        
        if notify_users:
            logger.info(f"✅ 从消息模板提取到 {len(notify_users)} 个通知人（包含完整用户信息）")
            # 打印每个通知人的详细信息（用于调试）
            for idx, user in enumerate(notify_users):
                logger.info(f"  通知人 {idx+1}: id={user.get('id')}, msgType={user.get('msgType')}, "
                          f"phone={user.get('phone')}, email={user.get('email')}, "
                          f"wxcp_userid={user.get('wxcp_userid')}, ding_userid={user.get('ding_userid')}, "
                          f"feishu_userid={user.get('feishu_userid')}, previewUser={user.get('previewUser')}, "
                          f"name={user.get('name')}")
        else:
            logger.warning(f"⚠️  从消息模板提取通知人失败，返回空列表: channels={channels}")
            logger.warning(
                "⚠️  请检查：1) 消息模板是否配置了 userGroupId 2) 用户组是否包含用户 "
                "3) MESSAGE_SERVICE_URL 是否可达且 message 服务已放行内网接口"
            )
        
    except Exception as e:
        logger.error(f"从消息模板提取通知人异常: {str(e)}", exc_info=True)
    
    return notify_users


def _parse_stored_notify_users(raw_config) -> List[Dict]:
    if not raw_config:
        return []
    try:
        config = json.loads(raw_config) if isinstance(raw_config, str) else raw_config
        if not isinstance(config, dict):
            return []
        users = config.get('notify_users') or []
        return users if isinstance(users, list) else []
    except Exception:
        return []


def _merge_notify_users_for_save(
        config_dict: Dict,
        channels: List[Dict],
        existing_notify_users: Optional[List[Dict]] = None) -> None:
    """保存任务时通过 message API 提取 notify_users；提取失败则保留已有配置。"""
    notify_users = _extract_notify_users_from_templates(channels)
    if notify_users:
        config_dict['notify_users'] = notify_users
        logger.info(f"✅ 从消息模板提取到 {len(notify_users)} 个通知人，已保存到配置中")
        for idx, user in enumerate(notify_users):
            logger.info(
                f"  通知人 {idx+1}: id={user.get('id')}, msgType={user.get('msgType')}, "
                f"wxcp_userid={user.get('wxcp_userid')}, previewUser={user.get('previewUser')}"
            )
        return

    if _has_userless_channel(channels):
        logger.info("ℹ️  包含 HTTP/Webhook 或群机器人渠道，无需 notify_users")
        config_dict.pop('notify_users', None)
        return

    if existing_notify_users:
        config_dict['notify_users'] = existing_notify_users
        logger.warning(
            f"⚠️  未能重新提取通知人，保留已有 {len(existing_notify_users)} 个 notify_users"
        )
        return

    config_dict.pop('notify_users', None)
    logger.warning(
        "⚠️  未能从消息模板提取通知人，配置中将不包含 notify_users。"
        "请检查模板 userGroupId 及 MESSAGE_SERVICE_URL 配置"
    )


def create_algorithm_task(task_name: str,
                         task_type: str = 'realtime',
                         device_ids: Optional[List[str]] = None,
                         model_ids: Optional[List[int]] = None,
                         extract_interval: Optional[int] = 12,
                         tracking_enabled: bool = False,
                         tracking_similarity_threshold: float = 0.2,
                         tracking_max_age: int = 25,
                         tracking_smooth_alpha: float = 0.25,
                         alert_event_enabled: bool = False,
                         alert_event_suppress_time: int = 5,
                         alert_class_names=None,
                         face_detection_enabled: bool = True,
                         plate_detection_enabled: bool = False,
                         face_matching_enabled: bool = False,
                         face_library_ids=None,
                         face_matching_threshold: Optional[float] = None,
                         plate_matching_enabled: bool = False,
                         plate_library_ids=None,
                         matching_business_tags=None,
                         alert_notification_enabled: bool = False,
                         alert_notification_config: Optional[str] = None,
                         alarm_suppress_time: int = 300,
                         cron_expression: Optional[str] = None,
                         frame_skip: int = 25,
                         is_enabled: bool = False,
                         defense_mode: Optional[str] = None,
                         defense_schedule: Optional[str] = None,
                         schedule_policy: str = 'local',
                         prefer_gpu: bool = True,
                         target_node_id: Optional[int] = None,
                         patrol_mode: str = 'pool',
                         patrol_interval_sec: int = 10,
                         patrol_pool_size: int = 4,
                         focus_device_id: Optional[str] = None,
                         sam_supplement_enabled: bool = False,
                         sam_supplement_config=None,
                         motion_gate_enabled: bool = False,
                         motion_gate_config=None,
                         detect_conf: float = 0.5,
                         pose_analysis_enabled: bool = False,
                         pose_analysis_config=None,
                         pose_intent_enabled: bool = False,
                         pose_library_ids=None,
                         pose_intent_threshold: Optional[float] = None,
                         pose_intent_config=None,
                         post_process_enabled: bool = False,
                         post_process_replicas: int = 1,
                         executor: str = 'cpp',
                         runtime_bin_path: Optional[str] = None,
                         runtime_control_port: Optional[int] = None) -> AlgorithmTask:
    """创建算法任务"""
    try:
        # 验证任务类型
        if task_type not in ['realtime', 'snap', 'patrol']:
            raise ValueError(f"无效的任务类型: {task_type}，必须是 'realtime'、'snap' 或 'patrol'")

        from app.services.runtime_config_service import normalize_executor, ensure_runtime_bin_ready
        executor = normalize_executor(executor)
        if executor == 'cpp':
            if task_type not in ('realtime', 'snap', 'patrol'):
                raise ValueError(f'executor=cpp 不支持任务类型: {task_type}')
            # 本机需已编译 RUNTIME；远程依赖 iot-node 分发到节点
            if (schedule_policy or 'local') == 'local':
                ensure_runtime_bin_ready(None)
        if runtime_control_port is not None:
            runtime_control_port = int(runtime_control_port)
            if runtime_control_port < 8000 or runtime_control_port > 9000:
                raise ValueError('runtime_control_port 必须在 8000-9000 之间')

        from app.utils.alert_class_filter import parse_alert_class_names
        if alert_event_enabled and not parse_alert_class_names(alert_class_names):
            raise ValueError('启用告警事件时必须指定至少一个告警触发标签')
        
        device_id_list = device_ids or []
        
        # 验证所有设备是否存在
        for dev_id in device_id_list:
            Device.query.get_or_404(dev_id)
        
        # 注意：推流转发任务和算法任务可以共存，因为它们使用不同的流地址
        # 推流转发任务使用 rtmp_stream/http_stream，算法任务使用 ai_rtmp_stream/ai_http_stream
        
        # 算法任务（实时和抓拍）：验证模型ID列表
        if model_ids:
            # 验证模型是否存在并获取模型名称（支持默认模型和数据库模型）
            model_names_list = []
            # 默认模型映射：负数ID -> 模型文件路径
            default_model_map = {
                -1: 'yolo11n.pt',
                -2: 'yolov8n.pt',
                -3: 'yolo26n.pt',
            }
            try:
                # 调用AI模块API获取模型信息（仅对正数ID，即数据库中的模型）
                import requests
                import os
                ai_service_url = os.getenv('AI_SERVICE_URL', 'http://localhost:5000')
                for model_id in model_ids:
                    # 如果是负数ID，表示默认模型
                    if model_id < 0:
                        model_file = default_model_map.get(model_id)
                        if model_file:
                            model_names_list.append(f"{model_file} (默认模型)")
                        else:
                            logger.warning(f"未知的默认模型ID: {model_id}")
                            model_names_list.append(f"默认模型_{model_id}")
                    else:
                        # 正数ID，从数据库获取模型信息
                        try:
                            response = requests.get(
                                f"{ai_service_url}/model/{model_id}",
                                headers={'X-Authorization': f'Bearer {os.getenv("JWT_TOKEN", "")}'},
                                timeout=5
                            )
                            if response.status_code == 200:
                                model_data = response.json()
                                if model_data.get('code') == 0:
                                    model_info = model_data.get('data', {})
                                    model_name = model_info.get('name', f'Model_{model_id}')
                                    model_version = model_info.get('version', '')
                                    if model_version:
                                        model_names_list.append(f"{model_name} (v{model_version})")
                                    else:
                                        model_names_list.append(model_name)
                                else:
                                    logger.warning(f"获取模型 {model_id} 信息失败: {model_data.get('msg')}")
                                    model_names_list.append(f"Model_{model_id}")
                            else:
                                logger.warning(f"获取模型 {model_id} 信息失败: HTTP {response.status_code}")
                                model_names_list.append(f"Model_{model_id}")
                        except Exception as e:
                            logger.warning(f"获取模型 {model_id} 信息异常: {str(e)}")
                            model_names_list.append(f"Model_{model_id}")
            except Exception as e:
                logger.warning(f"调用AI模块API获取模型信息失败: {str(e)}，使用默认名称")
                # 对于默认模型，使用模型文件名；对于数据库模型，使用Model_ID格式
                model_names_list = []
                for mid in model_ids:
                    if mid < 0:
                        model_file = default_model_map.get(mid)
                        if model_file:
                            model_names_list.append(f"{model_file} (默认模型)")
                        else:
                            model_names_list.append(f"默认模型_{mid}")
                    else:
                        model_names_list.append(f"Model_{mid}")
            
            model_ids_json = json.dumps(model_ids)
            model_names = ','.join(model_names_list) if model_names_list else None
        else:
            # 如果没有提供模型ID列表，设置为None
            model_ids_json = None
            model_names = None
        
        # 抓拍算法任务：验证Cron表达式
        if task_type == 'snap':
            if not cron_expression:
                raise ValueError("抓拍算法任务必须指定Cron表达式")
            cron_expression = validate_snap_cron_min_interval(cron_expression)
        elif task_type == 'patrol':
            cron_expression = None
            frame_skip = 25
            patrol_mode = 'pool'
            patrol_interval_sec = max(3, int(patrol_interval_sec or 10))
            patrol_pool_size = max(1, min(int(patrol_pool_size or 4), 16))
            focus_device_id = None
        else:
            cron_expression = None
            frame_skip = 25

        face_lib_ids = _normalize_library_ids(face_library_ids)
        plate_lib_ids = _normalize_library_ids(plate_library_ids)

        if face_matching_enabled:
            if not _has_library_matching_scope(face_lib_ids):
                raise ValueError('启用人脸匹配时必须指定至少一个人脸库')
            from models import FaceLibrary
            for lib_id in face_lib_ids:
                FaceLibrary.query.get_or_404(lib_id)

        if plate_matching_enabled:
            if not _has_library_matching_scope(plate_lib_ids):
                raise ValueError('启用车牌匹配时必须指定至少一个车牌库')
            from models import PlateLibrary
            for lib_id in plate_lib_ids:
                PlateLibrary.query.get_or_404(lib_id)

        pose_lib_ids = _normalize_library_ids(pose_library_ids)
        pose_intent_enabled, pose_analysis_enabled, pose_lib_ids = _normalize_pose_intent_fields(
            pose_intent_enabled=bool(pose_intent_enabled),
            pose_analysis_enabled=bool(pose_analysis_enabled),
            pose_library_ids=pose_lib_ids,
        )
        
        # 生成唯一编号
        prefix_map = {'realtime': 'REALTIME_TASK', 'snap': 'SNAP_TASK', 'patrol': 'PATROL_TASK'}
        prefix = prefix_map.get(task_type, 'REALTIME_TASK')
        task_code = f"{prefix}_{uuid.uuid4().hex[:8].upper()}"
        
        # 处理布防时段配置
        if defense_mode:
            if defense_mode not in ['full', 'half', 'day', 'night']:
                raise ValueError(f"无效的布防模式: {defense_mode}，必须是 'full', 'half', 'day' 或 'night'")
        else:
            defense_mode = 'full'  # 默认全防，避免半防空时段导致告警全部被 iot-sink 丢弃
        
        # 如果未提供defense_schedule，根据模式生成默认值
        if not defense_schedule:
            if defense_mode == 'full':
                # 全防模式：全部填充
                schedule = [[1] * 24 for _ in range(7)]
                defense_schedule = json.dumps(schedule)
            elif defense_mode == 'day':
                # 白天模式：6:00-18:00填充
                schedule = [[1 if 6 <= h < 18 else 0 for h in range(24)] for _ in range(7)]
                defense_schedule = json.dumps(schedule)
            elif defense_mode == 'night':
                # 夜间模式：18:00-6:00填充
                schedule = [[1 if h >= 18 or h < 6 else 0 for h in range(24)] for _ in range(7)]
                defense_schedule = json.dumps(schedule)
            else:
                # 半防模式：全部清空
                schedule = [[0] * 24 for _ in range(7)]
                defense_schedule = json.dumps(schedule)

        defense_mode, defense_schedule = _normalize_defense_for_alert_event(
            defense_mode, defense_schedule, alert_event_enabled
        )
        interval_fields = _normalize_alert_interval_fields(
            alert_event_suppress_time=alert_event_suppress_time,
            alarm_suppress_time=alarm_suppress_time,
        )
        alert_event_suppress_time = interval_fields.get('alert_event_suppress_time', 5)
        alarm_suppress_time = interval_fields.get('alarm_suppress_time', 300)

        # 处理告警通知配置（如果是字典或字符串，需要转换为JSON字符串）
        # 在保存前，从消息模板中提取通知人信息并保存到配置中
        if alert_notification_config:
            # 如果是字符串，先解析为字典
            if isinstance(alert_notification_config, str):
                try:
                    config_dict = json.loads(alert_notification_config)
                except json.JSONDecodeError:
                    logger.warning(f"⚠️  告警通知配置JSON解析失败: {alert_notification_config[:100]}")
                    config_dict = {}
            elif isinstance(alert_notification_config, dict):
                config_dict = alert_notification_config
            else:
                logger.warning(f"⚠️  告警通知配置类型不支持: {type(alert_notification_config)}")
                config_dict = {}
            
            # 确保config_dict是字典
            if isinstance(config_dict, dict):
                channels = config_dict.get('channels', [])
                if channels:
                    channels = _enrich_channels_userless_flags(channels)
                    config_dict['channels'] = channels
                logger.info(f"开始处理告警通知配置: channels数量={len(channels) if channels else 0}")
                if channels:
                    # 从消息模板中提取通知人信息
                    logger.info(f"开始从消息模板提取通知人信息: channels={channels}")
                    _merge_notify_users_for_save(config_dict, channels)
                else:
                    logger.warning(f"⚠️  告警通知配置中没有channels字段或channels为空")
                
                # 确保channels字段存在（即使为空）
                if 'channels' not in config_dict:
                    config_dict['channels'] = []
                
                # 转换为JSON字符串保存
                alert_notification_config = json.dumps(config_dict, ensure_ascii=False)
                logger.info(f"最终保存的告警通知配置: {alert_notification_config[:500]}")  # 只打印前500字符，避免日志过长
            else:
                logger.warning(f"⚠️  告警通知配置解析后不是字典类型: {type(config_dict)}")
                alert_notification_config = None
        
        task = AlgorithmTask(
            task_name=task_name,
            task_code=task_code,
            task_type=task_type,
            model_ids=model_ids_json,
            model_names=model_names,
            detect_conf=_normalize_detect_conf(detect_conf),
            extract_interval=extract_interval if task_type == 'realtime' else None,
            rtmp_input_url=None,  # 不再使用，从摄像头列表获取RTSP流地址
            rtmp_output_url=None,  # 不再使用，从摄像头列表获取RTMP流地址
            tracking_enabled=tracking_enabled if task_type == 'realtime' else False,
            tracking_similarity_threshold=tracking_similarity_threshold if task_type == 'realtime' else 0.2,
            tracking_max_age=tracking_max_age if task_type == 'realtime' else 25,
            tracking_smooth_alpha=tracking_smooth_alpha if task_type == 'realtime' else 0.25,
            alert_event_enabled=alert_event_enabled,
            alert_event_suppress_time=alert_event_suppress_time,
            alert_class_names=_serialize_alert_class_names(alert_class_names),
            face_detection_enabled=face_detection_enabled,
            plate_detection_enabled=plate_detection_enabled,
            face_matching_enabled=face_matching_enabled if task_type != 'patrol' else False,
            face_library_ids=_serialize_library_ids(face_lib_ids) if task_type != 'patrol' else None,
            face_matching_threshold=face_matching_threshold if task_type != 'patrol' else None,
            plate_matching_enabled=plate_matching_enabled if task_type != 'patrol' else False,
            plate_library_ids=_serialize_library_ids(plate_lib_ids) if task_type != 'patrol' else None,
            matching_business_tags=_serialize_matching_business_tags(matching_business_tags),
            alert_notification_enabled=alert_notification_enabled,
            alert_notification_config=alert_notification_config,
            alarm_suppress_time=alarm_suppress_time,
            space_id=None,
            cron_expression=cron_expression,
            frame_skip=frame_skip,
            patrol_mode=patrol_mode if task_type == 'patrol' else None,
            patrol_interval_sec=patrol_interval_sec if task_type == 'patrol' else None,
            patrol_pool_size=patrol_pool_size if task_type == 'patrol' else None,
            focus_device_id=focus_device_id if task_type == 'patrol' else None,
            is_enabled=is_enabled,
            defense_mode=defense_mode,
            defense_schedule=defense_schedule,
            schedule_policy=schedule_policy or 'local',
            prefer_gpu=prefer_gpu if prefer_gpu is not None else True,
            target_node_id=target_node_id,
            sam_supplement_enabled=bool(sam_supplement_enabled),
            sam_supplement_config=_serialize_sam_supplement_config(sam_supplement_config),
            motion_gate_enabled=bool(motion_gate_enabled) if task_type == 'realtime' else False,
            motion_gate_config=_serialize_motion_gate_config(motion_gate_config) if task_type == 'realtime' else None,
            pose_analysis_enabled=bool(pose_analysis_enabled),
            pose_analysis_config=_serialize_pose_analysis_config(pose_analysis_config),
            pose_intent_enabled=bool(pose_intent_enabled),
            pose_library_ids=_serialize_library_ids(pose_lib_ids) if pose_intent_enabled else None,
            pose_intent_threshold=pose_intent_threshold if pose_intent_enabled else None,
            pose_intent_config=_serialize_pose_intent_config(pose_intent_config),
            post_process_enabled=bool(post_process_enabled),
            post_process_replicas=max(1, int(post_process_replicas or 1)),
            executor=executor or 'cpp',
            runtime_bin_path=(runtime_bin_path or None),
            runtime_control_port=runtime_control_port,
        )
        
        db.session.add(task)
        db.session.flush()  # 先flush以获取task.id
        
        # 关联多个摄像头
        if device_id_list:
            devices = Device.query.filter(Device.id.in_(device_id_list)).all()
            task.devices = devices
        
        # 提交所有更改（包括任务和算法服务）
        db.session.commit()
        
        logger.info(f"创建算法任务成功: task_id={task.id}, task_name={task_name}, task_type={task_type}, device_ids={device_id_list}, model_ids={model_ids}")
        return task
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建算法任务失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"创建算法任务失败: {str(e)}")


def update_algorithm_task(task_id: int, **kwargs) -> AlgorithmTask:
    """更新算法任务"""
    try:
        task = AlgorithmTask.query.get_or_404(task_id)
        
        # 校验：只有在停用状态下才能编辑（排除is_enabled字段本身的更新）
        if task.is_enabled and 'is_enabled' not in kwargs:
            raise ValueError('任务运行中，无法编辑，请先停止任务')
        
        task_type = kwargs.get('task_type', task.task_type)

        if 'executor' in kwargs or 'task_type' in kwargs or 'schedule_policy' in kwargs:
            from app.services.runtime_config_service import normalize_executor, ensure_runtime_bin_ready
            if 'executor' in kwargs:
                kwargs['executor'] = normalize_executor(kwargs.get('executor'))
            effective_executor = normalize_executor(
                kwargs.get('executor', getattr(task, 'executor', None) or 'cpp')
            )
            effective_type = kwargs.get('task_type', task.task_type)
            effective_policy = kwargs.get(
                'schedule_policy', getattr(task, 'schedule_policy', None) or 'local'
            )
            if effective_executor == 'cpp':
                if effective_type not in ('realtime', 'snap', 'patrol'):
                    raise ValueError(f'executor=cpp 不支持任务类型: {effective_type}')
                if (effective_policy or 'local') == 'local':
                    ensure_runtime_bin_ready(task)
        if 'runtime_control_port' in kwargs and kwargs['runtime_control_port'] is not None:
            port = int(kwargs['runtime_control_port'])
            if port < 8000 or port > 9000:
                raise ValueError('runtime_control_port 必须在 8000-9000 之间')
            kwargs['runtime_control_port'] = port
        
        # 处理设备ID列表
        device_id_list = kwargs.pop('device_ids', None)
        
        # 处理模型ID列表
        model_ids = kwargs.pop('model_ids', None)
        
        # 验证所有设备是否存在（如果提供）
        if device_id_list is not None:
            for dev_id in device_id_list:
                Device.query.get_or_404(dev_id)
            
            # 注意：推流转发任务和算法任务可以共存，因为它们使用不同的流地址
            # 推流转发任务使用 rtmp_stream/http_stream，算法任务使用 ai_rtmp_stream/ai_http_stream
            # 已移除冲突检查，允许同一个摄像头同时用于推流转发和算法任务
        
        # 处理模型ID列表（实时和抓拍算法任务都支持）
        if model_ids is not None:
            if model_ids:
                # 验证模型是否存在并获取模型名称（支持默认模型和数据库模型）
                model_names_list = []
                # 默认模型映射：负数ID -> 模型文件路径
                default_model_map = {
                    -1: 'yolo11n.pt',
                    -2: 'yolov8n.pt',
                    -3: 'yolo26n.pt',
                }
                try:
                    # 调用AI模块API获取模型信息（仅对正数ID，即数据库中的模型）
                    import requests
                    import os
                    ai_service_url = os.getenv('AI_SERVICE_URL', 'http://localhost:5000')
                    for model_id in model_ids:
                        # 如果是负数ID，表示默认模型
                        if model_id < 0:
                            model_file = default_model_map.get(model_id)
                            if model_file:
                                model_names_list.append(f"{model_file} (默认模型)")
                            else:
                                logger.warning(f"未知的默认模型ID: {model_id}")
                                model_names_list.append(f"默认模型_{model_id}")
                        else:
                            # 正数ID，从数据库获取模型信息
                            try:
                                response = requests.get(
                                    f"{ai_service_url}/model/{model_id}",
                                    headers={'X-Authorization': f'Bearer {os.getenv("JWT_TOKEN", "")}'},
                                    timeout=5
                                )
                                if response.status_code == 200:
                                    model_data = response.json()
                                    if model_data.get('code') == 0:
                                        model_info = model_data.get('data', {})
                                        model_name = model_info.get('name', f'Model_{model_id}')
                                        model_version = model_info.get('version', '')
                                        if model_version:
                                            model_names_list.append(f"{model_name} (v{model_version})")
                                        else:
                                            model_names_list.append(model_name)
                                    else:
                                        logger.warning(f"获取模型 {model_id} 信息失败: {model_data.get('msg')}")
                                        model_names_list.append(f"Model_{model_id}")
                                else:
                                    logger.warning(f"获取模型 {model_id} 信息失败: HTTP {response.status_code}")
                                    model_names_list.append(f"Model_{model_id}")
                            except Exception as e:
                                logger.warning(f"获取模型 {model_id} 信息异常: {str(e)}")
                                model_names_list.append(f"Model_{model_id}")
                except Exception as e:
                    logger.warning(f"调用AI模块API获取模型信息失败: {str(e)}，使用默认名称")
                    # 对于默认模型，使用模型文件名；对于数据库模型，使用Model_ID格式
                    model_names_list = []
                    for mid in model_ids:
                        if mid < 0:
                            model_file = default_model_map.get(mid)
                            if model_file:
                                model_names_list.append(f"{model_file} (默认模型)")
                            else:
                                model_names_list.append(f"默认模型_{mid}")
                        else:
                            model_names_list.append(f"Model_{mid}")
                
                kwargs['model_ids'] = json.dumps(model_ids)
                kwargs['model_names'] = ','.join(model_names_list) if model_names_list else None
            else:
                # 如果传入空列表，清空模型关联
                kwargs['model_ids'] = None
                kwargs['model_names'] = None
        
        # 根据任务类型清除不相关字段
        if task_type == 'realtime':
            if 'space_id' in kwargs:
                kwargs['space_id'] = None
            if 'cron_expression' in kwargs:
                kwargs['cron_expression'] = None
            if 'frame_skip' in kwargs:
                kwargs['frame_skip'] = 25
            kwargs.pop('patrol_mode', None)
            kwargs.pop('patrol_interval_sec', None)
            kwargs.pop('patrol_pool_size', None)
            kwargs.pop('focus_device_id', None)
        elif task_type == 'patrol':
            if 'cron_expression' in kwargs:
                kwargs['cron_expression'] = None
            if 'space_id' in kwargs:
                kwargs['space_id'] = None
            kwargs['patrol_mode'] = 'pool'
            kwargs['focus_device_id'] = None
            if 'patrol_interval_sec' in kwargs:
                kwargs['patrol_interval_sec'] = max(3, int(kwargs['patrol_interval_sec'] or 10))
            if 'patrol_pool_size' in kwargs:
                kwargs['patrol_pool_size'] = max(1, min(int(kwargs['patrol_pool_size'] or 4), 16))
        else:
            # 抓拍算法任务：校验 cron 最短间隔
            if 'cron_expression' in kwargs and kwargs['cron_expression']:
                kwargs['cron_expression'] = validate_snap_cron_min_interval(
                    kwargs['cron_expression']
                )
        
        # 验证推送器是否存在（如果提供）
        if 'pusher_id' in kwargs and kwargs['pusher_id']:
            Pusher.query.get_or_404(kwargs['pusher_id'])
        
        updatable_fields = [
            'task_name', 'task_type', 'pusher_id',
            'model_ids', 'model_names',  # 模型配置
            'detect_conf',
            'extract_interval',  # 实时算法任务配置（rtmp_input_url和rtmp_output_url不再使用，从摄像头列表获取）
            'tracking_enabled', 'tracking_similarity_threshold', 'tracking_max_age', 'tracking_smooth_alpha',  # 追踪配置
            'alert_event_enabled', 'alert_event_suppress_time', 'alert_class_names',
            'face_detection_enabled', 'plate_detection_enabled',
            'face_matching_enabled', 'face_library_ids', 'face_matching_threshold',
            'plate_matching_enabled', 'plate_library_ids',
            'matching_business_tags',
            'alert_notification_enabled', 'alert_notification_config',
            'alarm_suppress_time',  # 告警配置
            'cron_expression', 'frame_skip',
            'patrol_mode', 'patrol_interval_sec', 'patrol_pool_size', 'focus_device_id',
            'is_enabled', 'status', 'exception_reason',
            'defense_mode', 'defense_schedule',
            'schedule_policy', 'prefer_gpu', 'target_node_id',
            'sam_supplement_enabled', 'sam_supplement_config',
            'motion_gate_enabled', 'motion_gate_config',
            'pose_analysis_enabled', 'pose_analysis_config',
            'pose_intent_enabled', 'pose_library_ids', 'pose_intent_threshold', 'pose_intent_config',
            'post_process_enabled', 'post_process_script', 'post_process_replicas',
            'executor', 'runtime_bin_path', 'runtime_control_port',
        ]
        
        if 'sam_supplement_config' in kwargs:
            kwargs['sam_supplement_config'] = _serialize_sam_supplement_config(
                kwargs['sam_supplement_config']
            )

        if 'motion_gate_config' in kwargs:
            kwargs['motion_gate_config'] = _serialize_motion_gate_config(
                kwargs['motion_gate_config']
            )

        if 'pose_analysis_config' in kwargs:
            kwargs['pose_analysis_config'] = _serialize_pose_analysis_config(
                kwargs['pose_analysis_config']
            )

        if 'pose_intent_config' in kwargs:
            kwargs['pose_intent_config'] = _serialize_pose_intent_config(
                kwargs['pose_intent_config']
            )

        if 'pose_library_ids' in kwargs:
            kwargs['pose_library_ids'] = _serialize_library_ids(
                _normalize_library_ids(kwargs.get('pose_library_ids'))
            )

        intent_enabled = kwargs.get('pose_intent_enabled')
        if intent_enabled is None:
            intent_enabled = bool(getattr(task, 'pose_intent_enabled', False))
        pose_enabled = kwargs.get('pose_analysis_enabled')
        if pose_enabled is None:
            pose_enabled = bool(getattr(task, 'pose_analysis_enabled', False))
        lib_ids_raw = kwargs.get('pose_library_ids') if 'pose_library_ids' in kwargs else getattr(task, 'pose_library_ids', None)
        if intent_enabled or 'pose_intent_enabled' in kwargs or 'pose_library_ids' in kwargs or 'pose_analysis_enabled' in kwargs:
            intent_on, pose_on, lib_ids = _normalize_pose_intent_fields(
                pose_intent_enabled=bool(intent_enabled),
                pose_analysis_enabled=bool(pose_enabled),
                pose_library_ids=lib_ids_raw,
            )
            kwargs['pose_intent_enabled'] = intent_on
            kwargs['pose_analysis_enabled'] = pose_on
            kwargs['pose_library_ids'] = _serialize_library_ids(lib_ids) if intent_on else None
            if not intent_on:
                kwargs['pose_intent_threshold'] = None
        elif 'pose_intent_enabled' in kwargs and not kwargs.get('pose_intent_enabled'):
            kwargs['pose_library_ids'] = None
            kwargs['pose_intent_threshold'] = None

        if 'detect_conf' in kwargs:
            kwargs['detect_conf'] = _normalize_detect_conf(kwargs.get('detect_conf'))
        
        # 验证布防模式
        if 'defense_mode' in kwargs:
            defense_mode = kwargs['defense_mode']
            if defense_mode and defense_mode not in ['full', 'half', 'day', 'night']:
                raise ValueError(f"无效的布防模式: {defense_mode}，必须是 'full', 'half', 'day' 或 'night'")

        interval_kwargs = _normalize_alert_interval_fields(
            alert_event_suppress_time=kwargs.get('alert_event_suppress_time'),
            alarm_suppress_time=kwargs.get('alarm_suppress_time'),
        )
        kwargs.update(interval_kwargs)

        if 'face_library_ids' in kwargs:
            face_lib_ids = _normalize_library_ids(kwargs.get('face_library_ids'))
            kwargs['face_library_ids'] = _serialize_library_ids(face_lib_ids)

        if 'plate_library_ids' in kwargs:
            plate_lib_ids = _normalize_library_ids(kwargs.get('plate_library_ids'))
            kwargs['plate_library_ids'] = _serialize_library_ids(plate_lib_ids)

        if kwargs.get('face_matching_enabled') or (
            'face_matching_enabled' not in kwargs and task.face_matching_enabled
        ):
            lib_ids_raw = kwargs.get('face_library_ids') if 'face_library_ids' in kwargs else task.face_library_ids
            face_lib_ids = _normalize_library_ids(lib_ids_raw)
            if not _has_library_matching_scope(face_lib_ids):
                raise ValueError('启用人脸匹配时必须指定至少一个人脸库')
            from models import FaceLibrary
            for lid in face_lib_ids:
                FaceLibrary.query.get_or_404(lid)
        elif 'face_matching_enabled' in kwargs and not kwargs.get('face_matching_enabled'):
            kwargs['face_library_ids'] = None
            kwargs['face_matching_threshold'] = None

        if kwargs.get('plate_matching_enabled') or (
            'plate_matching_enabled' not in kwargs and task.plate_matching_enabled
        ):
            lib_ids_raw = kwargs.get('plate_library_ids') if 'plate_library_ids' in kwargs else task.plate_library_ids
            plate_lib_ids = _normalize_library_ids(lib_ids_raw)
            if not _has_library_matching_scope(plate_lib_ids):
                raise ValueError('启用车牌匹配时必须指定至少一个车牌库')
            from models import PlateLibrary
            for lid in plate_lib_ids:
                PlateLibrary.query.get_or_404(lid)
        elif 'plate_matching_enabled' in kwargs and not kwargs.get('plate_matching_enabled'):
            kwargs['plate_library_ids'] = None

        if 'matching_business_tags' in kwargs:
            kwargs['matching_business_tags'] = _serialize_matching_business_tags(kwargs['matching_business_tags'])

        if 'alert_class_names' in kwargs:
            kwargs['alert_class_names'] = _serialize_alert_class_names(kwargs['alert_class_names'])

        if 'alert_event_enabled' in kwargs or 'alert_class_names' in kwargs:
            from app.utils.alert_class_filter import parse_alert_class_names
            alert_enabled = kwargs.get('alert_event_enabled', task.alert_event_enabled)
            if alert_enabled:
                if 'alert_class_names' in kwargs:
                    alert_names = parse_alert_class_names(kwargs.get('alert_class_names'))
                else:
                    alert_names = task._parse_alert_class_names()
                if not alert_names:
                    raise ValueError('启用告警事件时必须指定至少一个告警触发标签')
        
        # 处理告警通知配置（如果是字典或字符串，需要转换为JSON字符串）
        # 在保存前，从消息模板中提取通知人信息并保存到配置中
        if 'alert_notification_config' in kwargs and kwargs['alert_notification_config']:
            alert_notification_config = kwargs['alert_notification_config']
            # 如果是字符串，先解析为字典
            if isinstance(alert_notification_config, str):
                try:
                    config_dict = json.loads(alert_notification_config)
                except json.JSONDecodeError:
                    logger.warning(f"⚠️  告警通知配置JSON解析失败: {alert_notification_config[:100]}")
                    config_dict = {}
            elif isinstance(alert_notification_config, dict):
                config_dict = alert_notification_config
            else:
                logger.warning(f"⚠️  告警通知配置类型不支持: {type(alert_notification_config)}")
                config_dict = {}
            
            # 确保config_dict是字典
            if isinstance(config_dict, dict):
                channels = config_dict.get('channels', [])
                if channels:
                    channels = _enrich_channels_userless_flags(channels)
                    config_dict['channels'] = channels
                logger.info(f"开始处理告警通知配置（更新）: channels数量={len(channels) if channels else 0}")
                if channels:
                    # 从消息模板中提取通知人信息
                    logger.info(f"开始从消息模板提取通知人信息（更新）: channels={channels}")
                    existing_notify_users = _parse_stored_notify_users(task.alert_notification_config)
                    _merge_notify_users_for_save(
                        config_dict, channels, existing_notify_users=existing_notify_users
                    )
                else:
                    logger.warning(f"⚠️  告警通知配置中没有channels字段或channels为空（更新）")
                
                # 确保channels字段存在（即使为空）
                if 'channels' not in config_dict:
                    config_dict['channels'] = []
                
                # 转换为JSON字符串保存
                kwargs['alert_notification_config'] = json.dumps(config_dict, ensure_ascii=False)
                logger.info(f"最终保存的告警通知配置（更新）: {kwargs['alert_notification_config'][:500]}")  # 只打印前500字符
            else:
                logger.warning(f"⚠️  告警通知配置解析后不是字典类型（更新）: {type(config_dict)}")
                kwargs['alert_notification_config'] = None

        alert_event_on = kwargs.get('alert_event_enabled', task.alert_event_enabled)
        merged_defense_mode = kwargs.get('defense_mode', task.defense_mode)
        merged_defense_schedule = kwargs.get('defense_schedule', task.defense_schedule)
        merged_defense_mode, merged_defense_schedule = _normalize_defense_for_alert_event(
            merged_defense_mode, merged_defense_schedule, bool(alert_event_on)
        )
        kwargs['defense_mode'] = merged_defense_mode
        kwargs['defense_schedule'] = merged_defense_schedule
        
        for field in updatable_fields:
            if field in kwargs:
                setattr(task, field, kwargs[field])
        
        # 更新多对多关系
        if device_id_list is not None:
            devices = Device.query.filter(Device.id.in_(device_id_list)).all() if device_id_list else []
            task.devices = devices
        
        task.updated_at = datetime.utcnow()
        db.session.flush()  # 先flush以获取最新的task状态
        
        # 如果算法任务的模型列表被清空（实时算法任务），自动禁用相关设备的区域检测配置
        if task_type == 'realtime':
            # 检查更新后的模型列表是否为空
            final_model_ids = task.model_ids
            model_ids_empty = False
            if not final_model_ids:
                model_ids_empty = True
            elif isinstance(final_model_ids, str):
                if final_model_ids.strip() == '' or final_model_ids.strip() == '[]':
                    model_ids_empty = True
                else:
                    try:
                        model_ids_list = json.loads(final_model_ids)
                        if not model_ids_list or len(model_ids_list) == 0:
                            model_ids_empty = True
                    except:
                        # 如果解析失败，认为为空
                        model_ids_empty = True
            elif isinstance(final_model_ids, list):
                if len(final_model_ids) == 0:
                    model_ids_empty = True
            
            if model_ids_empty:
                # 获取任务关联的所有设备
                task_devices = task.devices if task.devices else []
                if task_devices:
                    from models import DeviceDetectionRegion
                    for device in task_devices:
                        # 禁用该设备的所有区域检测配置
                        regions = DeviceDetectionRegion.query.filter_by(device_id=device.id).all()
                        for region in regions:
                            region.is_enabled = False
                        logger.info(f"算法任务模型列表为空，自动禁用设备 {device.id} 的所有区域检测配置")
        
        db.session.commit()
        
        logger.info(f"更新算法任务成功: task_id={task_id}, task_type={task_type}, device_ids={device_id_list}, model_ids={model_ids}")
        return task
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新算法任务失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"更新算法任务失败: {str(e)}")


def delete_algorithm_task(task_id: int):
    """删除算法任务"""
    try:
        task = AlgorithmTask.query.get_or_404(task_id)
        
        # 校验：只有在停用状态下才能删除
        if task.is_enabled:
            raise ValueError('任务运行中，无法删除，请先停止任务')
        
        db.session.delete(task)
        db.session.commit()
        
        logger.info(f"删除算法任务成功: task_id={task_id}")
        return True
    except ValueError:
        raise
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除算法任务失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"删除算法任务失败: {str(e)}")


def get_algorithm_task(task_id: int) -> AlgorithmTask:
    """获取算法任务详情"""
    try:
        task = AlgorithmTask.query.options(
            joinedload(AlgorithmTask.devices),
            joinedload(AlgorithmTask.snap_space)
        ).get_or_404(task_id)
        return task
    except Exception as e:
        logger.error(f"获取算法任务失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"获取算法任务失败: {str(e)}")


def list_algorithm_tasks(page_no: int = 1, page_size: int = 10,
                        search: Optional[str] = None,
                        device_id: Optional[str] = None,
                        task_type: Optional[str] = None,
                        is_enabled: Optional[bool] = None) -> dict:
    """查询算法任务列表"""
    try:
        query = AlgorithmTask.query.options(
            joinedload(AlgorithmTask.devices),
            joinedload(AlgorithmTask.snap_space)
        )
        
        if search:
            query = query.filter(
                db.or_(
                    AlgorithmTask.task_name.like(f'%{search}%'),
                    AlgorithmTask.task_code.like(f'%{search}%')
                )
            )
        
        if device_id:
            # 通过多对多关系查询
            query = query.filter(AlgorithmTask.devices.any(Device.id == device_id))
        
        if task_type:
            query = query.filter_by(task_type=task_type)
        
        if is_enabled is not None:
            query = query.filter_by(is_enabled=is_enabled)
        
        total = query.count()
        
        # 分页
        # 排序：已开启(启动)的任务始终排在未开启的前面，同状态内再按最近更新时间倒序，
        # 避免因 updated_at 被刷新而导致开启中的任务被挤到后面。
        offset = (page_no - 1) * page_size
        tasks = query.order_by(
            AlgorithmTask.is_enabled.desc(),
            AlgorithmTask.updated_at.desc()
        ).offset(offset).limit(page_size).all()
        
        return {
            'items': [task.to_dict() for task in tasks],
            'total': total
        }
    except Exception as e:
        logger.error(f"查询算法任务列表失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"查询算法任务列表失败: {str(e)}")


def start_algorithm_task(task_id: int):
    """启动算法任务
    
    Returns:
        tuple[AlgorithmTask, str, bool]: (任务对象, 消息, 是否已运行)
    """
    try:
        task = AlgorithmTask.query.get_or_404(task_id)
        
        # 注意：推流转发任务和算法任务可以共存，因为它们使用不同的流地址
        # 推流转发任务使用 rtmp_stream/http_stream，算法任务使用 ai_rtmp_stream/ai_http_stream
        
        task.is_enabled = True
        task.status = 0
        task.exception_reason = None
        task.updated_at = datetime.utcnow()
        db.session.commit()

        try:
            from app.services.gb28181_sync_service import backfill_gb28181_ai_stream_urls
            backfill_gb28181_ai_stream_urls()
        except Exception as e:
            logger.warning(f'启动任务前回填国标 AI 推流地址失败: {e}')
        
        # 启动任务相关的服务（抽帧器、推送器、排序器）
        service_message = "启动成功"
        already_running = False
        try:
            from app.services.algorithm_task_launcher_service import start_task_services
            success, msg, is_running = start_task_services(task_id, task)
            if success:
                service_message = msg
                already_running = is_running
            else:
                service_message = msg
                logger.warning(f"启动任务 {task_id} 的服务失败: {msg}")
        except Exception as e:
            logger.warning(f"启动任务 {task_id} 的服务时出错: {str(e)}", exc_info=True)
            service_message = f"服务启动异常: {str(e)}"
        
        logger.info(f"启动算法任务成功: task_id={task_id}, message={service_message}, already_running={already_running}")
        try:
            from app.services.runtime_config_service import normalize_executor
            if normalize_executor(task.executor) == 'cpp' and task.task_type == 'realtime':
                from app.services.stream_forward_service import refresh_stream_forward_rtsp_for_devices
                refresh_stream_forward_rtsp_for_devices([d.id for d in (task.devices or [])])
        except Exception as e:
            logger.warning('启动算法后刷新推流转发 RTSP 失败 task_id=%s: %s', task_id, e)
        return task, service_message, already_running
    except Exception as e:
        db.session.rollback()
        logger.error(f"启动算法任务失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"启动算法任务失败: {str(e)}")


def stop_algorithm_task(task_id: int):
    """停止算法任务"""
    try:
        task = AlgorithmTask.query.get_or_404(task_id)
        device_ids = [d.id for d in (task.devices or [])]
        task.is_enabled = False
        task.run_status = 'stopped'
        task.updated_at = datetime.utcnow()
        db.session.commit()

        # 停止任务相关的服务（抽帧器、推送器、排序器）放到后台线程执行。
        # 进程清理（daemon.stop 的 SIGTERM 等待最长 10s + 孤儿进程 cleanup）耗时较长，
        # 若同步执行会阻塞 HTTP 请求超过前端 10s 超时，导致前端报超时但后端仍在停止。
        # 任务状态此处已提交（is_enabled=False / run_status=stopped），故清理可异步完成。
        import threading
        from flask import current_app

        from app.services.algorithm_task_launcher_service import (
            _issue_stop_request,
            _is_stop_request_current,
            stop_all_task_services,
        )

        stop_request_id = _issue_stop_request(task_id)
        app = current_app._get_current_object()

        def _teardown(tid: int, request_id: int, flask_app):
            try:
                with flask_app.app_context():
                    latest = AlgorithmTask.query.get(tid)
                    if latest and latest.is_enabled:
                        logger.info(
                            '任务 %s 已重新启用，跳过过期异步停止', tid
                        )
                        return
                if not _is_stop_request_current(tid, request_id):
                    logger.info('任务 %s 停止请求已过期，跳过', tid)
                    return
                stop_all_task_services(tid, stop_request_id=request_id)
            except Exception as e:
                logger.warning(f"停止任务 {tid} 的服务时出错: {str(e)}", exc_info=True)

        threading.Thread(
            target=_teardown,
            args=(task_id, stop_request_id, app),
            daemon=True,
            name=f"stop-task-{task_id}",
        ).start()

        try:
            from app.services.runtime_config_service import normalize_executor
            if normalize_executor(task.executor) == 'cpp' and task.task_type == 'realtime':
                from app.services.stream_forward_service import refresh_stream_forward_rtsp_for_devices
                refresh_stream_forward_rtsp_for_devices(device_ids)
        except Exception as e:
            logger.warning('停止算法后刷新推流转发 RTSP 失败 task_id=%s: %s', task_id, e)

        logger.info(f"停止算法任务成功(服务清理已转后台执行): task_id={task_id}")
        return task
    except Exception as e:
        db.session.rollback()
        logger.error(f"停止算法任务失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"停止算法任务失败: {str(e)}")


def restart_algorithm_task(task_id: int):
    """重启算法任务（使用守护进程的 restart 方法，更高效）"""
    try:
        task = AlgorithmTask.query.get_or_404(task_id)
        task.is_enabled = True
        task.status = 0
        task.exception_reason = None
        task.updated_at = datetime.utcnow()
        db.session.commit()

        try:
            from app.services.gb28181_sync_service import backfill_gb28181_ai_stream_urls
            backfill_gb28181_ai_stream_urls()
        except Exception as e:
            logger.warning(f'重启任务前回填国标 AI 推流地址失败: {e}')
        
        # 尝试使用守护进程的 restart 方法（如果守护进程在运行）
        try:
            from app.services.algorithm_task_launcher_service import restart_task_services, start_task_services
            # 先尝试重启（如果守护进程在运行）
            if not restart_task_services(task_id):
                # 如果重启失败（守护进程未运行），则启动服务
                logger.info(f"守护进程未运行，启动服务: task_id={task_id}")
                start_task_services(task_id, task)
        except Exception as e:
            logger.warning(f"重启任务 {task_id} 的服务时出错: {str(e)}", exc_info=True)
            # 如果出错，尝试启动服务
            try:
                start_task_services(task_id, task)
            except Exception as e2:
                logger.error(f"启动任务 {task_id} 的服务也失败: {str(e2)}", exc_info=True)
        
        logger.info(f"重启算法任务成功: task_id={task_id}")
        return task
    except Exception as e:
        db.session.rollback()
        logger.error(f"重启算法任务失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"重启算法任务失败: {str(e)}")

