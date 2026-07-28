package com.basiclab.iot.transform.core.channel;

/**
 * 对接渠道类型（按渠道拆分模块，而非按业务域）。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public enum ChannelType {

    /** 输入主渠道：iot-sink → Kafka；亦可作为输出渠道 */
    KAFKA("kafka"),
    HTTP("http"),
    MQTT("mqtt"),
    JDBC("jdbc"),
    /** 三方/四方/五方/N 方业务系统连接器聚合渠道 */
    PARTY("party");

    private final String code;

    ChannelType(String code) {
        this.code = code;
    }

    public String code() {
        return code;
    }
}
