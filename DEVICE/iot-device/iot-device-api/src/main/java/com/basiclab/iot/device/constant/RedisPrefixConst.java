package com.basiclab.iot.device.constant;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc
 * @created 2025-06-03
 */
public class RedisPrefixConst {
    /**
     * Redis下划线分隔符
     */
    public static final String UNDERLINE_SEPARATOR = "_";
    /**
     * Redis文件分隔符
     */
    public static final String SEPARATOR = ":";
    /**
     * OTA设备升级检测（一级key前缀）
     */
    public static final String DETECT_H_KEY_PREFIX = "OTA:DETECT:";
    /**
     * OTA设备升级检测消息推送（一级key前缀）
     */
    public static final String DETECT_MSG_PUSH_H_KEY_PREFIX = "OTA:DETECT:MSG_PUSH:";
    /**
     * key过期时间
     */
    public static final long EXPIRE = 60 * 60 * 24 * 5;

    public static final String DEVICE_BATCH_IMPORT = "DEVICE:BATCH:IMPORT:";
}