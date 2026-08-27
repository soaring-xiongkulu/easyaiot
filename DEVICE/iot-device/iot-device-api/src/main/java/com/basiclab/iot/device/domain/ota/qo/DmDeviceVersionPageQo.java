package com.basiclab.iot.device.domain.ota.qo;

import com.basiclab.iot.common.domain.PageQo;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.io.Serializable;

/**
 * 设备版本档案分页查询
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@ApiModel(value = "DmDeviceVersionPageQo对象", description = "设备版本档案分页Qo")
public class DmDeviceVersionPageQo extends PageQo implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 设备版本号
     */
    @ApiModelProperty(value = "设备版本号")
    private String deviceVersion;

    /**
     * 所属产品标识
     */
    @ApiModelProperty(value = "所属产品标识")
    private String productIdentification;
}
