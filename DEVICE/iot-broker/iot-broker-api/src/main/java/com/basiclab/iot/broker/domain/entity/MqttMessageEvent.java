package com.basiclab.iot.broker.domain.entity;

import lombok.Getter;
import org.springframework.context.ApplicationEvent;

/**
 * @program: easyaiot-cloud-pro-datasource-column
 * @description: MqttMessageEvent
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @date: 2023-04-28 14:42
 **/
@Getter
public class MqttMessageEvent extends ApplicationEvent {
    private final String topic;
    private final String qos;
    private final String message;
    private final String time;

    public MqttMessageEvent(Object source, String topic, String qos, String message, String time) {
        super(source);
        this.topic = topic;
        this.qos = qos;
        this.message = message;
        this.time = time;
    }


    public class AddSubDeviceEvent extends MqttMessageEvent {
        public AddSubDeviceEvent(Object source, String topic, String qos, String body, String time) {
            super(source, topic, qos, body, time);
        }
    }

    public class AddSubDeviceResponseEvent extends MqttMessageEvent {
        public AddSubDeviceResponseEvent(Object source, String topic, String qos, String body, String time) {
            super(source, topic, qos, body, time);
        }
    }

    public class DeviceStatusEvent extends MqttMessageEvent {
        public DeviceStatusEvent(Object source, String topic, String qos, String body, String time) {
            super(source, topic, qos, body, time);
        }
    }

    public class DeviceStatusResponseEvent extends MqttMessageEvent {
        public DeviceStatusResponseEvent(Object source, String topic, String qos, String body, String time) {
            super(source, topic, qos, body, time);
        }
    }

    public class DeviceControlEvent extends MqttMessageEvent {
        public DeviceControlEvent(Object source, String topic, String qos, String body, String time) {
            super(source, topic, qos, body, time);
        }
    }

    public class DeviceControlResponseEvent extends MqttMessageEvent {
        public DeviceControlResponseEvent(Object source, String topic, String qos, String body, String time) {
            super(source, topic, qos, body, time);
        }
    }

    public class DeviceDataReportEvent extends MqttMessageEvent {
        public DeviceDataReportEvent(Object source, String topic, String qos, String body, String time) {
            super(source, topic, qos, body, time);
        }
    }

    public class DeviceDataReportResponseEvent extends MqttMessageEvent {
        public DeviceDataReportResponseEvent(Object source, String topic, String qos, String body, String time) {
            super(source, topic, qos, body, time);
        }
    }
}
