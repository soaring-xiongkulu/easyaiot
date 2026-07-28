package com.basiclab.iot.transform.core.group;

import com.basiclab.iot.transform.core.channel.ChannelType;

/**
 * 各渠道约定的 Kafka Consumer Group / 投递协调 Group 命名。
 * <p>
 * 规则：{@code transform.{channel}.{direction}.{purpose}}
 * <ul>
 *   <li>同 Group 内多实例自动再均衡 → 横向扩展消费/投递</li>
 *   <li>不同渠道使用独立 Group，互不抢占分区</li>
 *   <li>实例启动后按启用渠道自动 join，退出自动 leave</li>
 * </ul>
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public final class GroupNames {

    private GroupNames() {
    }

    public static final String PREFIX = "transform";

    /** 从 iot-sink Kafka 消费设备消息 */
    public static final String KAFKA_CONSUME_DEVICE = "transform.kafka.consume.device";

    /** 从 iot-sink Kafka 消费告警 */
    public static final String KAFKA_CONSUME_ALERT = "transform.kafka.consume.alert";

    /** 从 iot-sink Kafka 消费抓拍/视觉事件 */
    public static final String KAFKA_CONSUME_VISION = "transform.kafka.consume.vision";

    /** Kafka 渠道投递协调（若投递目标仍为 Kafka） */
    public static final String KAFKA_DELIVER = "transform.kafka.deliver";

    public static final String HTTP_DELIVER = "transform.http.deliver";
    public static final String MQTT_DELIVER = "transform.mqtt.deliver";
    public static final String JDBC_DELIVER = "transform.jdbc.deliver";
    public static final String PARTY_DELIVER = "transform.party.deliver";

    /** 备份能力独立 Group，避免与业务投递争抢 */
    public static final String BACKUP = "transform.capability.backup";

    public static String consume(ChannelType channel, String purpose) {
        return PREFIX + "." + channel.code() + ".consume." + purpose;
    }

    public static String deliver(ChannelType channel) {
        return PREFIX + "." + channel.code() + ".deliver";
    }
}
