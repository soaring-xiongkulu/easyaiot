package com.basiclab.iot.device.domain.device.oo;

import io.swagger.annotations.ApiModelProperty;
import lombok.Data;
import lombok.ToString;

import java.io.Serializable;

/**
 * @author EasyAIoT
 * @desc    日志处理对象
 * @created 2025-06-25
 */
@Data
@ToString
public class BaseDeviceLogOo implements Serializable {


    @ApiModelProperty(value = "deviceIdentification", notes = "设备的唯一标识")
    private String deviceIdentification;

    @ApiModelProperty(value = "protocolType", notes = "协议类型")
    private String protocolType;

    @ApiModelProperty(value = "deviceVerSion", notes = "设备版本号")
    private String deviceVersion;

    @ApiModelProperty(value = "版本号", notes = "同一个指令版本号保持一致")
    private String version;

    @ApiModelProperty(value = "指令类型", notes = "1:上传日志，2:日志上报存储成功，3:日志上报失败")
    private String type;

    @ApiModelProperty(value = "时长", notes = "区间时长(eventTime前多少时长的日志)，单位分钟")
    private String interval;

    @ApiModelProperty(value = "模式", notes = "日志模式，扩展参数")
    private String model;


}
