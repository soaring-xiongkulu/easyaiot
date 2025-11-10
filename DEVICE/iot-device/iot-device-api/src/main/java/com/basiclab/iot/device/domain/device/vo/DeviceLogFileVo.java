package com.basiclab.iot.device.domain.device.vo;

import io.swagger.annotations.ApiModelProperty;
import lombok.Data;
import lombok.ToString;

import java.io.Serializable;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc
 * @created 2025-06-25
 */
@Data
@ToString
public class DeviceLogFileVo extends OpsDeviceLogFilePo implements Serializable {

    @ApiModelProperty(value = "主键转的字符串")
    private String version;

    @ApiModelProperty(value = "状态名称")
    private String statusName;
}
