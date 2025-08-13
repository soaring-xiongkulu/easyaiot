package com.basiclab.iot.device.enums.device;

import io.swagger.annotations.ApiModel;
import lombok.Getter;
import lombok.NoArgsConstructor;

/**
 * <p>
 * 设备动作类型 枚举
 * </p>
 *
 * @author EasyAIoT
 * @date 2023-08-20
 */
@Getter
@NoArgsConstructor
@ApiModel(value = "DeviceEventTypeEnum", description = "设备动作类型 枚举")
public enum DeviceEventTypeEnum {

    PUBLISH("PUBLISH", "Publishing data to a topic."),
    WRITE("WRITE", "Writing data to a device or topic."),

    CLUSTER("CLUSTER", "Cluster-based actions or references to clusters."),
    CONNECT("CONNECT", "Initiating a connection to a server."),
    CLOSE("CLOSE", "Closing a connection to a server."),

    SUBSCRIBE("SUBSCRIBE", "Subscribing to a topic to receive messages."),

    UNSUBSCRIBE("UNSUBSCRIBE", "Unsubscribing from a topic to stop receiving messages."),

    BRIDGE("BRIDGE", "Bridging or connecting two different networks or brokers."),
    DISCONNECT("DISCONNECT", "Terminating a connection gracefully."),
    PING("PING", "Sending a ping request to maintain or check a connection."),

    PUBLISH_ACK("PUBLISH_ACK", "Acknowledging the receipt of a published message."),

    RETRY("RETRY", "Retrying a certain event or request after a failure."),

    HEART_TIMEOUT("HEART_TIMEOUT", "An event indicating a timeout due to lack of heartbeat or keep-alive signal."),

    SYSTEM("SYSTEM", "System level or internal events."),

    UNKNOWN("UNKNOWN", "Unknown event type.");

    private String event;
    private String description;

    DeviceEventTypeEnum(String event, String description) {
        this.event = event;
        this.description = description;
    }


}
