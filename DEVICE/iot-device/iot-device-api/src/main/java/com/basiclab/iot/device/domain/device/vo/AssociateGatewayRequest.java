package com.basiclab.iot.device.domain.device.vo;

import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.util.List;

/**
 * @author EasyAIoT
 */
@Data
public class AssociateGatewayRequest {
    /**
     * 设备id列表
     */
    @ApiModelProperty(value = "设备id列表")
    private List<Long> idList;
    /**
     * 目标网关设备标识
     */
    @ApiModelProperty(value = "目标网关设备标识")
    private String targetDeviceIdentification;
}