package com.basiclab.iot.device.domain.device.vo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 设备扩展数据响应VO
 * 
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@ApiModel("设备扩展数据响应")
@Data
public class DeviceExtensionDataVO implements Serializable {
    
    /**
     * 设备ID
     */
    @ApiModelProperty(value = "设备ID")
    private Long deviceId;
    
    /**
     * 设备标识
     */
    @ApiModelProperty(value = "设备标识")
    private String deviceIdentification;
    
    /**
     * 扩展信息类型
     */
    @ApiModelProperty(value = "扩展信息类型")
    private String extensionType;
    
    /**
     * 扩展数据（JSON格式）
     */
    @ApiModelProperty(value = "扩展数据（JSON格式）")
    private Object extensionData;
    
    /**
     * 最后更新时间
     */
    @ApiModelProperty(value = "最后更新时间")
    private LocalDateTime updateTime;
}

