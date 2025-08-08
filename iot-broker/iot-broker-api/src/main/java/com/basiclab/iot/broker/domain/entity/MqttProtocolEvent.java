package com.basiclab.iot.broker.domain.entity;


import com.basiclab.iot.broker.domain.enumeration.MqttEventEnum;

/**
 * @program: easyaiot-cloud-pro-datasource-column
 * @description: MQTT协议事件类
 * @packagename: com.basiclab.iot.mqtt.entity
 * @author EasyAIoT
 * @date: 2023-04-28 00:10
 **/
public class MqttProtocolEvent {
    private final MqttEventEnum eventEnum;
    private final String message;

    public MqttProtocolEvent(MqttEventEnum eventEnum, String message) {
        this.eventEnum = eventEnum;
        this.message = message;
    }

    public MqttEventEnum getEventEnum() {
        return eventEnum;
    }

    public String getMessage() {
        return message;
    }
}
