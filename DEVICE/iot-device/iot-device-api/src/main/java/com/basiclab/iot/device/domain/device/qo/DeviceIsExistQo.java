package com.basiclab.iot.device.domain.device.qo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.io.Serializable;

/**
 * DeviceIsExistQo
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
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