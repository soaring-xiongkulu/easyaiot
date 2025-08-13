package com.basiclab.iot.device.domain.device.vo;

import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

/**
 * @author EasyAIoT
 */
@Data
public class ConnectStatusStatisticsVo {
    /**
     * 在线状态数量
     */
    @ApiModelProperty("在线状态数量")
    private Integer onlineStatusAmount;

    /**
     * 离线状态数量
     */
    @ApiModelProperty("离线状态数量")
    private Integer offlineStatusAmount;
}
