package com.basiclab.iot.device.domain.device.vo;

import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import javax.validation.constraints.NotNull;
import java.util.Map;

/**
 * @author EasyAIoT
 */
@Data
public class DeviceShadowCommand {
    @ApiModelProperty(value = "命令名称")
    private String commandName;

    @ApiModelProperty(value = "命令名称")
    private String commandCode;

    @ApiModelProperty(value = "命令参数")
    @NotNull(message = "命令参数不能为空")
    private Map<String, Object> params;
}
