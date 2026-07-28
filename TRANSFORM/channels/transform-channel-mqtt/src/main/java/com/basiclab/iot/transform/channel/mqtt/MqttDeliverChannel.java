package com.basiclab.iot.transform.channel.mqtt;

import com.basiclab.iot.transform.core.channel.ChannelType;
import com.basiclab.iot.transform.core.envelope.TransformEnvelope;
import com.basiclab.iot.transform.core.group.GroupNames;
import com.basiclab.iot.transform.core.spi.TransformChannel;
import lombok.extern.slf4j.Slf4j;

/**
 * MQTT 投递渠道：面向第三方 MQTT 系统 / 桥接。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
public class MqttDeliverChannel implements TransformChannel {

    private volatile boolean joined;

    @Override
    public ChannelType type() {
        return ChannelType.MQTT;
    }

    @Override
    public String deliverGroup() {
        return GroupNames.MQTT_DELIVER;
    }

    @Override
    public void join() {
        joined = true;
        log.info("[MqttDeliverChannel] joined deliver group={}", deliverGroup());
    }

    @Override
    public void leave() {
        joined = false;
    }

    @Override
    public void deliver(TransformEnvelope envelope) {
        log.debug("[MqttDeliverChannel] deliver eventId={}", envelope.getEventId());
    }

    @Override
    public boolean healthy() {
        return joined;
    }
}
