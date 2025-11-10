package com.basiclab.iot.device.domain.device.vo;

import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
public class DeviceDetail {

    @ApiModelProperty(value = "设备信息")
    private DeviceParams device;

    @ApiModelProperty(value = "产品信息")
    private Product product;
}
