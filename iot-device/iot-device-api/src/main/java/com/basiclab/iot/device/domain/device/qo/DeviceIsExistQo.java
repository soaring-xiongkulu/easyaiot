package com.basiclab.iot.device.domain.device.qo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.io.Serializable;

/**
 * @author zhangzhixiang on 2024/7/31
 */
@Data
@ApiModel(value = "DmDeviceIsExistQo对象", description = "DmDeviceIsExistQo对象")
public class DeviceIsExistQo implements Serializable {

    private static final long serialVersionUID = -2247287287146748962L;
    /**
     * 设备did
     */
    @ApiModelProperty(value = "设备唯一ID")
    private String deviceIdentification;
    /**
     * 设备sn
     */
    @ApiModelProperty(value = "设备SN")
    private String deviceSn;
}