package com.basiclab.iot.sink.service;

import com.basiclab.iot.sink.domain.model.AlertNotificationMessage;

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
     * 无论是否开启通知，都会执行存储和上传操作
     *
     * @param notificationMessage 告警通知消息
     * @return 告警ID（如果存储成功）
     */
    Integer processAlert(AlertNotificationMessage notificationMessage);
    
    /**
     * 处理抓拍算法任务告警消息：存储到数据库（类型为抓拍算法任务）、上传图片到MinIO抓拍空间
     * 无论是否开启通知，都会执行存储和上传操作
     *
     * @param notificationMessage 告警通知消息
     * @return 告警ID（如果存储成功）
     */
    Integer processSnapshotAlert(AlertNotificationMessage notificationMessage);
}

