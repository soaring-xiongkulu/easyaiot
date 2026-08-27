package com.basiclab.iot.device.domain.ota.oo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.io.Serializable;

/**
 * 设备当前版本信息（check 请求中的单项）
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@ApiModel(value = "DmOtaVersionOo对象", description = "设备当前版本Oo")
public class DmOtaVersionOo implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 包类型[0:软件包,1:固件包,2:APP包,3:PC包]
     */
    @ApiModelProperty(value = "包类型[0:软件包,1:固件包,2:APP包,3:PC包]")
    private Integer type;

    /**
     * 当前版本号
     */
    @ApiModelProperty(value = "当前版本号")
    private String version;
}
