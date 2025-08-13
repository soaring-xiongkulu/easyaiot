package com.basiclab.iot.tdengine.domain;

import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

/**
 * Tdengine中的device_data表
 * @author EasyAIoT
 */
@Data
public class DeviceData {
    /**
     * 设备标识
     */
    @ApiModelProperty("设备标识")
    private String deviceIdentification;
    /**
     * 时间
     */
    @ApiModelProperty("时间")
    private long lastUpdateTime;

    @ApiModelProperty("方法类型 properties:属性 service:服务 event:事件")
    private String functionType;
    /**
     * 标识符
     */
    @ApiModelProperty("标识符")
    private String identifier;
    /**
     * 数据类型
      */
    @ApiModelProperty("数据类型")
    private String dataType;
    /**
     * 数据
     */
    @ApiModelProperty("数据")
    private String dataValue;

}
