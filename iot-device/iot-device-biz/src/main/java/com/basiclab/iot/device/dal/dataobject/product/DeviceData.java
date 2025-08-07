package com.basiclab.iot.device.dal.dataobject.product;

import lombok.Data;

/**
 * Tdengine中的device_data表
 * @author Basiclab
 */
@Data
public class DeviceData {
    /**
     * 设备标识
     */
    private String deviceIdentification;
    /**
     * 时间
     */
    private long lastUpdateTime;

    private String functionType;
    /**
     * 标识符
     */
    private String identifier;
    /**
     * 数据类型
      */
    private String dataType;
    /**
     * 数据
     */
    private String dataValue;

}
