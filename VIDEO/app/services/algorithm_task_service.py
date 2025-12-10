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
from app.utils.device_conflict_checker import (
    check_device_conflict_with_stream_forward_tasks,
    format_conflict_message
)
import json

logger = logging.getLogger(__name__)


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
        
        # 获取消息服务API地址
        try:
            from flask import current_app
            message_service_url = current_app.config.get('MESSAGE_SERVICE_URL', 'http://localhost:48080')
            jwt_token = current_app.config.get('JWT_TOKEN', os.getenv('JWT_TOKEN', ''))
        except RuntimeError:
            message_service_url = os.getenv('MESSAGE_SERVICE_URL', 'http://localhost:48080')
            jwt_token = os.getenv('JWT_TOKEN', '')
        
        # 构建认证请求头
        headers = {}
        if jwt_token:
            headers['Authorization'] = f'Bearer {jwt_token}'
        
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
            logger.warning(f"⚠️  请检查：1) 消息模板是否配置了userGroupId 2) 用户组是否包含用户 3) API调用是否成功 4) 用户组中的用户是否有previewUser字段")
        
    except Exception as e:
        logger.error(f"从消息模板提取通知人异常: {str(e)}", exc_info=True)
    
    return notify_users


def create_algorithm_task(task_name: str,
                         task_type: str = 'realtime',
                         device_ids: Optional[List[str]] = None,
                         model_ids: Optional[List[int]] = None,
                         extract_interval: int = 25,
                         tracking_enabled: bool = False,
                         tracking_similarity_threshold: float = 0.2,
                         tracking_max_age: int = 25,
                         tracking_smooth_alpha: float = 0.25,
                         alert_event_enabled: bool = False,
                         alert_notification_enabled: bool = False,
                         alert_notification_config: Optional[str] = None,
                         cron_expression: Optional[str] = None,
                         frame_skip: int = 25,
                         is_enabled: bool = False,
                         defense_mode: Optional[str] = None,
                         defense_schedule: Optional[str] = None) -> AlgorithmTask:
    """创建算法任务"""
    try:
        # 验证任务类型
        if task_type not in ['realtime', 'snap']:
            raise ValueError(f"无效的任务类型: {task_type}，必须是 'realtime' 或 'snap'")
        
        device_id_list = device_ids or []
        
        # 验证所有设备是否存在
        for dev_id in device_id_list:
            Device.query.get_or_404(dev_id)
        
        # 检查摄像头是否已经在启用的推流转发任务中使用
        if device_id_list:
            has_conflict, conflicts = check_device_conflict_with_stream_forward_tasks(device_id_list)
            if has_conflict:
                conflict_msg = format_conflict_message(conflicts, 'stream_forward')
                raise ValueError(f"摄像头冲突：{conflict_msg}。同一个摄像头不能同时用于推流转发和算法任务。")
        
        # 算法任务（实时和抓拍）：验证模型ID列表
        if model_ids:
            # 验证模型是否存在并获取模型名称（支持默认模型和数据库模型）
            model_names_list = []
            # 默认模型映射：负数ID -> 模型文件路径
            default_model_map = {
                -1: 'yolo11n.pt',
                -2: 'yolov8n.pt',
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
        else:
            # 实时算法任务：不需要Cron表达式
            cron_expression = None
            frame_skip = 25
        
        # 生成唯一编号
        prefix = "REALTIME_TASK" if task_type == 'realtime' else "SNAP_TASK"
        task_code = f"{prefix}_{uuid.uuid4().hex[:8].upper()}"
        
        # 处理布防时段配置
        if defense_mode:
            if defense_mode not in ['full', 'half', 'day', 'night']:
                raise ValueError(f"无效的布防模式: {defense_mode}，必须是 'full', 'half', 'day' 或 'night'")
        else:
            defense_mode = 'half'  # 默认半防模式
        
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
                logger.info(f"开始处理告警通知配置: channels数量={len(channels) if channels else 0}")
                if channels:
                    # 从消息模板中提取通知人信息
                    logger.info(f"开始从消息模板提取通知人信息: channels={channels}")
                    notify_users = _extract_notify_users_from_templates(channels)
                    if notify_users:
                        # 将通知人信息添加到配置中
                        config_dict['notify_users'] = notify_users
                        logger.info(f"✅ 从消息模板提取到 {len(notify_users)} 个通知人，已保存到配置中")
                        # 打印每个通知人的详细信息（用于调试）
                        for idx, user in enumerate(notify_users):
                            logger.info(f"  通知人 {idx+1}: id={user.get('id')}, msgType={user.get('msgType')}, "
                                      f"phone={user.get('phone')}, email={user.get('email')}, "
                                      f"wxcp_userid={user.get('wxcp_userid')}, ding_userid={user.get('ding_userid')}, "
                                      f"feishu_userid={user.get('feishu_userid')}, previewUser={user.get('previewUser')}")
                    else:
                        logger.warning(f"⚠️  未能从消息模板提取通知人信息，配置中将不包含通知人。请检查：1) 消息模板是否配置了userGroupId 2) 用户组是否包含用户 3) API调用是否成功")
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
            extract_interval=extract_interval if task_type == 'realtime' else 25,
            rtmp_input_url=None,  # 不再使用，从摄像头列表获取RTSP流地址
            rtmp_output_url=None,  # 不再使用，从摄像头列表获取RTMP流地址
            tracking_enabled=tracking_enabled if task_type == 'realtime' else False,
            tracking_similarity_threshold=tracking_similarity_threshold if task_type == 'realtime' else 0.2,
            tracking_max_age=tracking_max_age if task_type == 'realtime' else 25,
            tracking_smooth_alpha=tracking_smooth_alpha if task_type == 'realtime' else 0.25,
            alert_event_enabled=alert_event_enabled,
            alert_notification_enabled=alert_notification_enabled,
            alert_notification_config=alert_notification_config,
            space_id=None,
            cron_expression=cron_expression,
            frame_skip=frame_skip,
            is_enabled=is_enabled,
            defense_mode=defense_mode,
            defense_schedule=defense_schedule
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
        
        # 处理设备ID列表
        device_id_list = kwargs.pop('device_ids', None)
        
        # 处理模型ID列表
        model_ids = kwargs.pop('model_ids', None)
        
        # 验证所有设备是否存在（如果提供）
        if device_id_list is not None:
            for dev_id in device_id_list:
                Device.query.get_or_404(dev_id)
            
            # 检查摄像头是否已经在启用的推流转发任务中使用（排除当前任务）
            if device_id_list:
                has_conflict, conflicts = check_device_conflict_with_stream_forward_tasks(device_id_list, exclude_task_id=task_id)
                if has_conflict:
                    conflict_msg = format_conflict_message(conflicts, 'stream_forward')
                    raise ValueError(f"摄像头冲突：{conflict_msg}。同一个摄像头不能同时用于推流转发和算法任务。")
        
        # 处理模型ID列表（实时和抓拍算法任务都支持）
        if model_ids is not None:
            if model_ids:
                # 验证模型是否存在并获取模型名称（支持默认模型和数据库模型）
                model_names_list = []
                # 默认模型映射：负数ID -> 模型文件路径
                default_model_map = {
                    -1: 'yolo11n.pt',
                    -2: 'yolov8n.pt',
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
            # 实时算法任务：清除抓拍相关字段
            if 'space_id' in kwargs:
                kwargs['space_id'] = None
            if 'cron_expression' in kwargs:
                kwargs['cron_expression'] = None
            if 'frame_skip' in kwargs:
                kwargs['frame_skip'] = 25
        else:
            # 抓拍算法任务：保留模型字段，不需要清除
            pass
        
        # 验证推送器是否存在（如果提供）
        if 'pusher_id' in kwargs and kwargs['pusher_id']:
            Pusher.query.get_or_404(kwargs['pusher_id'])
        
        updatable_fields = [
            'task_name', 'task_type', 'pusher_id',
            'model_ids', 'model_names',  # 模型配置
            'extract_interval',  # 实时算法任务配置（rtmp_input_url和rtmp_output_url不再使用，从摄像头列表获取）
            'tracking_enabled', 'tracking_similarity_threshold', 'tracking_max_age', 'tracking_smooth_alpha',  # 追踪配置
            'alert_event_enabled', 'alert_notification_enabled', 'alert_notification_config',  # 告警配置
            'cron_expression', 'frame_skip',  # 抓拍算法任务配置
            'is_enabled', 'status', 'exception_reason',
            'defense_mode', 'defense_schedule'
        ]
        
        # 验证布防模式
        if 'defense_mode' in kwargs:
            defense_mode = kwargs['defense_mode']
            if defense_mode and defense_mode not in ['full', 'half', 'day', 'night']:
                raise ValueError(f"无效的布防模式: {defense_mode}，必须是 'full', 'half', 'day' 或 'night'")
        
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
                logger.info(f"开始处理告警通知配置（更新）: channels数量={len(channels) if channels else 0}")
                if channels:
                    # 从消息模板中提取通知人信息
                    logger.info(f"开始从消息模板提取通知人信息（更新）: channels={channels}")
                    notify_users = _extract_notify_users_from_templates(channels)
                    if notify_users:
                        # 将通知人信息添加到配置中
                        config_dict['notify_users'] = notify_users
                        logger.info(f"✅ 从消息模板提取到 {len(notify_users)} 个通知人，已保存到配置中（更新）")
                        # 打印每个通知人的详细信息（用于调试）
                        for idx, user in enumerate(notify_users):
                            logger.info(f"  通知人 {idx+1}: id={user.get('id')}, msgType={user.get('msgType')}, "
                                      f"phone={user.get('phone')}, email={user.get('email')}, "
                                      f"wxcp_userid={user.get('wxcp_userid')}, ding_userid={user.get('ding_userid')}, "
                                      f"feishu_userid={user.get('feishu_userid')}, previewUser={user.get('previewUser')}")
                    else:
                        logger.warning(f"⚠️  未能从消息模板提取通知人信息，配置中将不包含通知人（更新）。请检查：1) 消息模板是否配置了userGroupId 2) 用户组是否包含用户 3) API调用是否成功")
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
        offset = (page_no - 1) * page_size
        tasks = query.order_by(
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
        
        # 检查摄像头是否已经在启用的推流转发任务中使用
        if task.devices:
            device_ids = [d.id for d in task.devices]
            has_conflict, conflicts = check_device_conflict_with_stream_forward_tasks(device_ids)
            if has_conflict:
                conflict_msg = format_conflict_message(conflicts, 'stream_forward')
                raise ValueError(f"摄像头冲突：{conflict_msg}。同一个摄像头不能同时用于推流转发和算法任务。")
        
        task.is_enabled = True
        task.status = 0
        task.exception_reason = None
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
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
        return task, service_message, already_running
    except Exception as e:
        db.session.rollback()
        logger.error(f"启动算法任务失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"启动算法任务失败: {str(e)}")


def stop_algorithm_task(task_id: int):
    """停止算法任务"""
    try:
        task = AlgorithmTask.query.get_or_404(task_id)
        task.is_enabled = False
        task.run_status = 'stopped'
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        # 停止任务相关的服务（抽帧器、推送器、排序器）
        try:
            from app.services.algorithm_task_launcher_service import stop_all_task_services
            stop_all_task_services(task_id)
        except Exception as e:
            logger.warning(f"停止任务 {task_id} 的服务时出错: {str(e)}", exc_info=True)
            # 不抛出异常，允许任务停止但服务可能未停止
        
        logger.info(f"停止算法任务成功: task_id={task_id}")
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

