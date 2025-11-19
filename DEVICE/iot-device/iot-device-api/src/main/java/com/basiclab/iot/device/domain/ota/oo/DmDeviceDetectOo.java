package com.basiclab.iot.device.domain.ota.oo;

import com.fasterxml.jackson.annotation.JsonIgnore;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.io.Serializable;

/**
 * @author zhangzhixiang on 2020/8/11
 */
@Data
@ApiModel(value = "DmDeviceDetectOo对象", description = "设备检测升级Oo")
public class DmDeviceDetectOo implements Serializable {

    private static final long serialVersionUID = 7111973619211336640L;
    /**
     * 版本包类型[0:app,1:系统,2:电控]
     */
    @JsonIgnore
    private Integer type;
    /**
     * 设备唯一标识
     */
    @JsonIgnore
    private String deviceIdentification;
    /**
     * APP版本
     */
    @ApiModelProperty(value = "APP版本")
    private String appVersion;
    /**
     * 系统版本
     */
    @ApiModelProperty(value = "系统版本")
    private String osVersion;
    /**
     * 电控版本（软件）
     */
    @ApiModelProperty(value = "电控版本（软件）")
    private String ecuVersion;
}