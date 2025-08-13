package com.basiclab.iot.device.enums.device;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 *  设备状态
 * @author EasyAIoT
 * @date 2024-10-22
 */
@Getter
@AllArgsConstructor
public enum DeviceStatusEnum {

    /**
     * 启用
     */
    ENABLE("ENABLE","ENABLE"),

    /**
     * 禁用
     */
    DISABLE("DISABLE","DISABLE");

    private  String key;
    private  String value;

}
