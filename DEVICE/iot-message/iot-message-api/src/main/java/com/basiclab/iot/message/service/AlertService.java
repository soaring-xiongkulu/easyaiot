package com.basiclab.iot.message.service;

import com.basiclab.iot.message.domain.model.AlertNotificationMessage;

/**
 * 告警处理服务接口
 * 负责：存储告警到数据库、上传图片到MinIO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface AlertService {
    
    /**
     * 处理告警消息：存储到数据库、上传图片到MinIO
     *
     * @param notificationMessage 告警通知消息
     * @return 告警ID（如果存储成功）
     */
    Integer processAlert(AlertNotificationMessage notificationMessage);
}

