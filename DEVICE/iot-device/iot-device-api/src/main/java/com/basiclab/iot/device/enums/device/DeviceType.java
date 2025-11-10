package com.basiclab.iot.device.enums.device;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * @Description: 设备类型
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @CreateDate: 2024/10/25$ 16:19$
 * @UpdateDate: 2024/10/25$ 16:19$
 */
@Getter
@AllArgsConstructor
public enum DeviceType {

    /**
     * 普通设备（无子设备也无父设备）
     */
    COMMON("COMMON", "COMMON"),

    /**
     * 网关设备(可挂载子设备)
     */
    GATEWAY("GATEWAY", "GATEWAY"),

    /**
     * 子设备(归属于某个网关设备)
     */
    SUBSET("SUBSET", "SUBSET");

    private String key;
    private String value;
}
