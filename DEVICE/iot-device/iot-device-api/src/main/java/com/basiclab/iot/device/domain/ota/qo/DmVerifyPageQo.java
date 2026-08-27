package com.basiclab.iot.device.domain.ota.qo;

import com.basiclab.iot.common.domain.PageQo;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.io.Serializable;

/**
 * 测试白名单分页查询
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@ApiModel(value = "DmVerifyPageQo对象", description = "测试白名单分页Qo")
public class DmVerifyPageQo extends PageQo implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 版本包ID
     */
    @ApiModelProperty(value = "版本包ID")
    private Long pkgId;

    /**
     * 设备唯一标识
     */
    @ApiModelProperty(value = "设备唯一标识")
    private String deviceIdentification;

    /**
     * 设备名称
     */
    @ApiModelProperty(value = "设备名称")
    private String deviceName;
}
