package com.basiclab.iot.tdengine.constant;

/**
 * TDEngine 超级表类型常量
 * 
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public class SuperTableTypeConstant {
    
    /**
     * 属性上报超级表
     */
    public static final String PROPERTY_UPSTREAM_REPORT = "st_property_upstream_report";
    
    /**
     * 属性期望值设置确认超级表
     */
    public static final String PROPERTY_UPSTREAM_DESIRED_SET_ACK = "st_property_upstream_desired_set_ack";
    
    /**
     * 属性期望值查询响应超级表
     */
    public static final String PROPERTY_UPSTREAM_DESIRED_QUERY_RESPONSE = "st_property_upstream_desired_query_response";
    
    /**
     * 事件上报超级表
     */
    public static final String EVENT_UPSTREAM_REPORT = "st_event_upstream_report";
    
    /**
     * 服务调用响应超级表
     */
    public static final String SERVICE_UPSTREAM_INVOKE_RESPONSE = "st_service_upstream_invoke_response";
    
    /**
     * 设备标签上报超级表
     */
    public static final String DEVICE_TAG_UPSTREAM_REPORT = "st_device_tag_upstream_report";
    
    /**
     * 设备标签删除超级表
     */
    public static final String DEVICE_TAG_UPSTREAM_DELETE = "st_device_tag_upstream_delete";
    
    /**
     * 影子上报超级表
     */
    public static final String SHADOW_UPSTREAM_REPORT = "st_shadow_upstream_report";
    
    /**
     * 配置查询超级表
     */
    public static final String CONFIG_UPSTREAM_QUERY = "st_config_upstream_query";
    
    /**
     * NTP请求超级表
     */
    public static final String NTP_UPSTREAM_REQUEST = "st_ntp_upstream_request";
    
    /**
     * OTA版本上报超级表
     */
    public static final String OTA_UPSTREAM_VERSION_REPORT = "st_ota_upstream_version_report";
    
    /**
     * OTA进度上报超级表
     */
    public static final String OTA_UPSTREAM_PROGRESS_REPORT = "st_ota_upstream_progress_report";
    
    /**
     * OTA固件查询超级表
     */
    public static final String OTA_UPSTREAM_FIRMWARE_QUERY = "st_ota_upstream_firmware_query";
}

