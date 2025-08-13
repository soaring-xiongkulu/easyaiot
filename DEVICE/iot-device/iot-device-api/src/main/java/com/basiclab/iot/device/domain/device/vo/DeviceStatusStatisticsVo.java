package com.basiclab.iot.device.domain.device.vo;

import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

/**
 * @author EasyAIoT
 */
@Data
public class DeviceStatusStatisticsVo {

    /**
     * 已激活数量
     */
    @ApiModelProperty("已激活数量")
    private Integer activatedAmount;

    /**
     * 未激活数量
     */
    @ApiModelProperty("未激活数量")
    private Integer inactivatedAmount;
}
