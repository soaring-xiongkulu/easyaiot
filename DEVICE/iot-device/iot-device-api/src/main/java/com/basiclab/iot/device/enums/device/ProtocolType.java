package com.basiclab.iot.device.enums.device;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * @Description: 产品协议类型
 * @author EasyAIoT
 * @CreateDate: 2024/10/25$ 15:57$
 * @UpdateDate: 2024/10/25$ 15:57$
 */
@Getter
@AllArgsConstructor
public enum ProtocolType {

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
    HTTP("HTTP","HTTP");

    private  String key;
    private  String value;
}
