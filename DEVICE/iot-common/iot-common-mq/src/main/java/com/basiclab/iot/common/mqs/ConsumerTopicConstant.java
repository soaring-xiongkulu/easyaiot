package com.basiclab.iot.common.mqs;


/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface ConsumerTopicConstant {

    /**
     * MQTT Broker 监听主题
     */
    interface Mqtt {
        /**
         * MQTT设备消息监听主题——》MQTT消息——》MQS
         */
        String IOT_MQS_MQTT_MSG = "iot-pro-mqs-mqtt-msg";

        /**
         * 设备上线
         */
        String IOT_MQTT_CLIENT_CONNECTED_TOPIC = "mqtt.client.connected.topic";

        /**
         * 客户端设备离线
         */
        String IOT_MQTT_CLIENT_DISCONNECTED_TOPIC = "mqtt.client.disconnect.topic";

        /**
         * 服务端主动断开了与客户端的连接
         */
        String IOT_MQTT_SERVER_CONNECTED_TOPIC = "mqtt.server.disconnect.topic";

        /**
         * 设备离线
         */
        String IOT_MQTT_DEVICE_KICKED_TOPIC = "mqtt.device.kicked.topic";

        /**
         * 消息订阅
         */
        String IOT_MQTT_SUBSCRIPTION_ACKED_TOPIC = "mqtt.subscription.acked.topic";

        /**
         * 取消订阅
         */
        String IOT_MQTT_UNSUBSCRIPTION_ACKED_TOPIC = "mqtt.unsubscription.acked.topic";

        /**
         * 消息分发错误
         */
        String IOT_MQTT_DISTRIBUTION_ERROR_TOPIC = "mqtt.distribution.error.topic";

        /**
         * 消息分发
         */
        String IOT_MQTT_DISTRIBUTION_COMPLETED_TOPIC = "mqtt.distribution.completed.topic";


        /**
         * PING 请求
         */
        String IOT_MQTT_PING_REQ_TOPIC = "mqtt.ping.req.topic";

    }

    interface Device {
        /**
         * 指令响应
         */
        String COMMAND_RESPONSE_TOPIC = "command-response-topic";
        /**
         * 指令下发
         */
        String COMMAND_TOPIC = "command-topic";
        /**
         * 协议脚本更新
         */
        String PROTOCOL_SCRIPT_UPDATE = "protocol-script-update";

        /**
         * 设备日志上传响应
         */
        String DEVICE_LOG_UPLOAD_RESPONSE = "device-log-upload-response";


        /**
         * 产品服务
         */
        String IOT_PRO_PRODUCT_SERVICE_MSG = "iot-pro-product-service-msg";

        /**
         * 产品服务属性
         */
        String IOT_PRO_PRODUCT_PROPERTY_MSG = "iot-pro-product-property-msg";

        /**
         * 点播指令执行成功
         */
        String PLAY_STREAM_SUCCESS_MSG = "play-stream-success-msg";

        /**
         * 点播指令执行失败
         */
        String PLAY_STREAM_ERROR_MSG = "play-stream-error-msg";

        /**
         * 更新设备通道消息
         */
        String RESET_CHANNEL_MSG = "reset-channel-msg";

        /**
         * 更新设备通过定位消息
         */
        String UPDATE_DEVICE_CHANNEL_GPS_MSG = "update-device-channel-gps-msg";

        /**
         * 更新视频设备信息消息
         */
        String UPDATE_VIDEO_DEVICE_MESSAGE = "update-video-device-msg";

        /**
         * 视频设备上线消息
         */
        String VIDEO_DEVICE_ONLINE_MESSAGE = "video-online-device-msg";

        /**
         * 视频设备下线消息
         */
        String VIDEO_DEVICE_OFFLINE_MESSAGE = "video-offline-device-msg";

        /**
         * 录像记录查询成功消息
         */
        String RECORD_QUERY_SUCCESS_MSG = "record-query-success-msg";
    }

    interface Rule {

        /**
         * 规则引擎触发器规则动作监听主题
         */
        String IOT_RULE_TRIGGER = "iot_rule_trigger";
    }

    interface Tdengine {

        /**
         * TDengine超级表创键修改动作监听主题
         */
        String PRODUCTSUPERTABLE_CREATEORUPDATE = "productSuperTable-createOrUpdate";
    }

}
