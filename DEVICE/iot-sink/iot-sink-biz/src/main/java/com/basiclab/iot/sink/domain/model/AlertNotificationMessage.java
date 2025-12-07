package com.basiclab.iot.sink.domain.model;

import lombok.Data;

import java.util.List;
import java.util.Map;

/**
 * 告警通知消息DTO（用于Kafka消息传输）
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
public class AlertNotificationMessage {
    
    /**
     * 告警ID
     */
    private Integer alertId;
    
    /**
     * 任务ID
     */
    private Integer taskId;
    
    /**
     * 任务名称
     */
    private String taskName;
    
    /**
     * 设备ID
     */
    private String deviceId;
    
    /**
     * 设备名称
     */
    private String deviceName;
    
    /**
     * 告警信息
     */
    private AlertInfo alert;
    
    /**
     * 通知人列表
     */
    private List<Map<String, Object>> notifyUsers;
    
    /**
     * 通知方式列表
     */
    private List<String> notifyMethods;
    
    /**
     * 通知渠道和模板配置列表
     */
    private List<Map<String, Object>> channels;
    
    /**
     * 时间戳
     */
    private String timestamp;
    
    /**
     * 告警信息内部类
     */
    @Data
    public static class AlertInfo {
        private String object;
        private String event;
        private String region;
        private Object information;
        private String imagePath;
        private String recordPath;
        private String time;
    }
}

