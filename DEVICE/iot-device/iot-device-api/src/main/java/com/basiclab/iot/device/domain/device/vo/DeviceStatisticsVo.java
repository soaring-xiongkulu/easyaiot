package com.basiclab.iot.device.domain.device.vo;

import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
public class DeviceStatisticsVo {

    /**
     * 设备总数
     */
    @ApiModelProperty("设备总数")
    private Integer deviceTotal;
    /**
     * 普通设备数量
     */
    @ApiModelProperty("普通设备数量")
    private Integer commonDeviceAmount;

    /**
     * 网关设备数量
     */
    @ApiModelProperty("网关设备数量")
    private Integer gatewayDeviceAmount;

    /**
     * 子设备数量
     */
    @ApiModelProperty("子设备数量")
    private Integer subsetDeviceAmount;
}
