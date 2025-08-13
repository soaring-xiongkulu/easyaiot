package com.basiclab.iot.device.domain.device.qo;

import com.basiclab.iot.common.domain.PageQo;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;
import lombok.ToString;

/**
 * @author EasyAIoT
 * @desc
 * @created 2025-06-03
 */
@Data
@ToString
@ApiModel(value = "OpsDeviceLogPageQueryQo对象", description = "分页查询设备上报日志记录接口参数模型")
public class OpsDeviceLogPageQueryQo extends PageQo {

    private static final long serialVersionUID = -5357130766490913044L;

    @ApiModelProperty(value = "设备唯一ID")
    private String deviceIdentification;
}
