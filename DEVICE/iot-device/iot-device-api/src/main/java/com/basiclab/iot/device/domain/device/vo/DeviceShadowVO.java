package com.basiclab.iot.device.domain.device.vo;

import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.util.List;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
public class DeviceShadowVO {

    /**
     * 期望值
     */
    @ApiModelProperty("期望值")
    private List<DeviceShadowCommandVO> desired;
    /**
     * 实际值
     */
    @ApiModelProperty(value = "实际值")
    private List<TDDeviceDataResp> actual;

}
