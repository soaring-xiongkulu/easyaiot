package com.basiclab.iot.broker.mqs.mqtt.event;

import com.basiclab.iot.broker.domain.enumeration.MqttEventEnum;
import org.springframework.context.ApplicationEvent;

/**
 * @description: MqttSubscribeEvent
 * @packagename: com.basiclab.iot.mqtt.event
 * @author: EasyAIoT
 * @email: andywebjava@163.com
 * @date: 2023-04-28 01:52
 **/
public class MqttSubscribeEvent extends ApplicationEvent {
    private String message;
    private MqttEventEnum eventType;

    public MqttSubscribeEvent(Object source, MqttEventEnum eventType, String message) {
        super(source);
        this.message = message;
        this.eventType = eventType;
    }

    public String getMessage() {
        return message;
    }

    public MqttEventEnum getEventType() {
        return eventType;
    }
}
