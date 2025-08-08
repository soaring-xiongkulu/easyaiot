package com.basiclab.iot.device.domain.device.so;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import javax.validation.constraints.NotBlank;


/**
 * @author EasyAIoT
 * @desc
 * @created 2025-06-03
 */
@Data
@ApiModel(value = "OpsDeviceLogFileSo对象", description = "设备日志文件")
public class OpsDeviceLogFileSo {

    @ApiModelProperty(required = true, value = "设备唯一ID")
    @NotBlank(message = "deviceIdentification must not be blank")
    private String deviceIentification;

    @ApiModelProperty(required = true, value = "应用编码[GONGMO-工模,ECU-电控,APP-设备APP,GALANZ_OS-设备OS]")
    @NotBlank(message = "appCode must not be blank")
    private String appCode;

    @ApiModelProperty(required = true, value = "功能编码，如：RUN_TEST", example = "RUN_TEST")
    @NotBlank(message = "functionCode must not be blank")
    private String functionCode;

    @ApiModelProperty(required = true, value = "功能名称，如：运行测试", example = "运行测试")
    @NotBlank(message = "functionName must not be blank")
    private String functionName;

    @ApiModelProperty(value = "备注")
    private String remark;

}
