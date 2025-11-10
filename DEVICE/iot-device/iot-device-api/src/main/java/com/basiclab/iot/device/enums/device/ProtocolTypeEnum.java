package com.basiclab.iot.device.enums.device;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * @Description: 产品协议类型
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @CreateDate: 2024/10/25$ 15:57$
 * @UpdateDate: 2024/10/25$ 15:57$
 */
@Getter
@AllArgsConstructor
public enum ProtocolTypeEnum {

    /**
     * MQTT协议
     */
    MQTT("MQTT","MQTT"),


    /**
     * COAP协议
     */
    COAP("COAP","COAP"),

    /**
     * MODBUS协议
     */
    MODBUS("MODBUS","MODBUS"),

    /**
     * HTTP协议
     */
    HTTP("HTTP","HTTP"),

    /**
     * TCP协议
     */
    TCP("TCP", "TCP协议"),

    /**
     * WEBSOCKET协议
     */
    WEBSOCKET("WEBSOCKET", "WEBSOCKET协议");

    private  String key;
    private  String value;
}
