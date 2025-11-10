package com.basiclab.iot.tdengine.constant;

/**
 * 全局基础常量
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @version v1.0
 * @date 2024/4/12 11:05 PM
 * @create [2024/4/12 11:05 PM ] [mqttsnet] [初始创建]
 */
public interface TdsConstants {

    String DATA_BASE = "iot";

    /**
     * 时序数据库主键ID
     */
    String TS = "ts";

    /**
     * 时序数据库标签
     */
    String TAG = "TAG";

    /**
     * 事件上报时间
     */
    String EVENT_TIME = "event_time";

    /**
     * TAG ——》设备标签名
     */
    String DEVICE_IDENTIFICATION = "device_identification";
}
