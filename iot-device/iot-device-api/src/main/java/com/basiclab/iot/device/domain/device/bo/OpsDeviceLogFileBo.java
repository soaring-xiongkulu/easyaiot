package com.basiclab.iot.device.domain.device.bo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;
import lombok.ToString;

import javax.validation.constraints.NotBlank;
import java.io.Serializable;

/**
 * @author EasyAIoT
 * @desc
 * @created 2025-06-03
 */
@Data
@ToString
@ApiModel(value = "OpsDeviceLogFileBo对象", description = "设备app和设备系统日志上传接口参数模型")
public class OpsDeviceLogFileBo implements Serializable {

    private static final long serialVersionUID = 508391968106131498L;

    @ApiModelProperty(required = true, value = "指令版本号同时也是记录主键")
    @NotBlank(message = "version must not be blank")
    private String version;

    @ApiModelProperty(value = "备注")
    private String remark;
}
