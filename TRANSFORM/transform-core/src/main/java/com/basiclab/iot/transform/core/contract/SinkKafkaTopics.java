package com.basiclab.iot.transform.core.contract;

/**
 * DEVICE/iot-sink 投递到 Kafka 的 Topic 契约（TRANSFORM 唯一输入源头）。
 * <p>
 * 告警事件、图片地址、视频地址、传感器/设备数据最终均经由 iot-sink 落入这些 Topic，
 * 或可从其中拿到等价信息。TRANSFORM 只消费、不反向改写 sink 协议层。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public final class SinkKafkaTopics {

    private SinkKafkaTopics() {
    }

    /**
     * 设备消息总线（属性/事件/服务/状态等标准化消息）
     * 对应 {@code IotDeviceMessage.MESSAGE_BUS_DEVICE_MESSAGE_TOPIC}
     */
    public static final String DEVICE_MESSAGE = "iot_device_message";

    /** 告警通知（VIDEO/AI → sink） */
    public static final String ALERT_NOTIFICATION = "iot-alert-notification";

    /** 抓拍告警 */
    public static final String SNAPSHOT_ALERT = "iot-snapshot-alert";

    /** 人脸匹配 */
    public static final String FACE_MATCHING = "iot-face-matching";

    /** 车牌匹配 */
    public static final String PLATE_MATCHING = "iot-plate-matching";

    /** 算法后处理请求 */
    public static final String POST_PROCESS_REQUEST = "iot-post-process-request";

    /** 算法后处理结果 */
    public static final String POST_PROCESS_RESULT = "iot-post-process-result";

    /** 产品编解码脚本热更新（一般不作为业务流转源，仅感知用） */
    public static final String PRODUCT_SCRIPT_CHANGE = "iot_product_script_change";
}
