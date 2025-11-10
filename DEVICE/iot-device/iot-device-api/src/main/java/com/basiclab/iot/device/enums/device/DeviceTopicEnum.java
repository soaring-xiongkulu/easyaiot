package com.basiclab.iot.device.enums.device;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * @program: EasyAIoT
 * @description: 设备Topic枚举
 * @packagename: com.basiclab.iot.common.core.enums
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @date: 2025-08-26 10:49
 **/
@Getter
@AllArgsConstructor
public enum DeviceTopicEnum {
    /**
     * 基础Topic
     */
    BASIS("0","基础Topic"),

    /**
     * 自定义Topic
     */
    CUSTOM("1","自定义Topic");

    private  String key;
    private  String value;
}
