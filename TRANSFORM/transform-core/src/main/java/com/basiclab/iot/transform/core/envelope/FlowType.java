package com.basiclab.iot.transform.core.envelope;

/**
 * 四流类型：由 iot-sink Kafka 消息归一化而来。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public enum FlowType {

    /** 设备/传感器属性与事件（iot_device_message） */
    DATA,
    /** 传感器时序侧重（同源 DATA，映射标签区分） */
    SENSOR,
    /** 告警（iot-alert-notification / iot-snapshot-alert） */
    ALERT,
    /** 视频/图片地址与视觉事件（抓拍、人脸、车牌、后处理结果等） */
    VIDEO_META
}
