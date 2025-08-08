package com.basiclab.iot.device.enums.device;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.Optional;
import java.util.stream.Stream;

/**
 * @Description: 连接状态
 * @author EasyAIoT
 * @CreateDate: 2024/10/25$ 15:54$
 * @UpdateDate: 2024/10/25$ 15:54$
 */
@Getter
@AllArgsConstructor
@NoArgsConstructor
public enum DeviceConnectStatusEnum {
    /**
     * 初始化
     */
    INIT("INIT", "INIT"),

    /**
     * 在线
     */
    ONLINE("ONLINE", "ONLINE"),

    /**
     * 离线
     */
    OFFLINE("OFFLINE", "OFFLINE");

    private String key;
    private String value;

    /**
     * 根据key获取对应的枚举
     *
     * @param key 设备连接的状态值
     * @return 返回对应的枚举，如果没找到则返回 Optional.empty()
     */
    public static Optional<DeviceConnectStatusEnum> fromValue(String key) {
        return Stream.of(DeviceConnectStatusEnum.values())
                .filter(status -> status.getValue().equals(key))
                .findFirst();
    }

    public String getKey() {
        return key;
    }

    public void setKey(String key) {
        this.key = key;
    }

    public String getValue() {
        return value;
    }

    public void setValue(String value) {
        this.value = value;
    }
}
