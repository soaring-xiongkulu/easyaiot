package com.basiclab.iot.message.domain.model;

import lombok.Data;

import java.util.List;
import java.util.Map;

/**
 * 告警通知消息DTO
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
     * 支持6种通知方式：
     * - sms: 短信（阿里云/腾讯云）
     * - email: 邮件
     * - wxcp/wechat/weixin: 企业微信
     * - http/webhook: HTTP请求
     * - ding/dingtalk: 钉钉
     * - feishu/lark: 飞书
     */
    private List<String> notifyMethods;
    
    /**
     * 通知渠道和模板配置列表
     * 格式：[{"method": "sms", "template_id": "xxx", "template_name": "xxx"}, ...]
     */
    private List<Map<String, Object>> channels;
    
    /**
     * 时间戳
     */
    private String timestamp;
    
    /**
     * 是否需要发送通知
     * true: 需要发送通知（有通知配置且通知人列表不为空）
     * false: 不需要发送通知（没有通知配置或通知人列表为空）
     */
    private Boolean shouldNotify;
    
    /**
     * 告警信息内部类
     */
    @Data
    public static class AlertInfo {
        /**
         * 对象类型
         */
        private String object;
        
        /**
         * 事件类型
         */
        private String event;
        
        /**
         * 区域
         */
        private String region;
        
        /**
         * 详细信息
         */
        private Object information;
        
        /**
         * 图片路径
         */
        private String imagePath;
        
        /**
         * 录像路径
         */
        private String recordPath;
        
        /**
         * 告警时间
         */
        private String time;
        
        /**
         * 告警事件类型[realtime:实时算法任务,snap:抓拍算法任务]
         */
        private String taskType;
    }
}

