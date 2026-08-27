package com.basiclab.iot.device.domain.ota.vo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.io.Serializable;

/**
 * 灰度范围
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@ApiModel(value = "DmGrayScopeVo对象", description = "灰度范围")
public class DmGrayScopeVo implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 范围类型[1:设备,2:产品]
     */
    @ApiModelProperty(value = "范围类型[1:设备,2:产品]")
    private Integer scopeType;

    /**
     * 范围类型名称
     */
    @ApiModelProperty(value = "范围类型名称")
    private String scopeTypeName;

    /**
     * 范围值（设备唯一标识/产品标识）
     */
    @ApiModelProperty(value = "范围值（设备唯一标识/产品标识）")
    private String scopeValue;
}
