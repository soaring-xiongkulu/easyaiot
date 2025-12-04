package com.basiclab.iot.message.service;

import com.basiclab.iot.message.domain.model.AlertNotificationMessage;

/**
 * 告警通知服务接口
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface AlertNotificationService {
    
    /**
     * 处理告警通知
     *
     * @param notificationMessage 告警通知消息
     */
    void processAlertNotification(AlertNotificationMessage notificationMessage);
}

