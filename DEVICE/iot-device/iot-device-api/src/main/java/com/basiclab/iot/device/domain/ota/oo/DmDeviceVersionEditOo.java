package com.basiclab.iot.device.domain.ota.oo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import javax.validation.constraints.NotNull;
import java.io.Serializable;

/**
 * 设备版本档案编辑
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@ApiModel(value = "DmDeviceVersionEditOo对象", description = "设备版本档案编辑Oo")
public class DmDeviceVersionEditOo implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 主键ID
     */
    @NotNull(message = "设备版本ID不能为空")
    @ApiModelProperty(value = "主键ID")
    private Long id;

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

    /**
     * 软件包ID（device_ota_pkg.id）
     */
    @ApiModelProperty(value = "软件包ID")
    private Long appPkgId;

    /**
     * 固件包ID（device_ota_pkg.id）
     */
    @ApiModelProperty(value = "固件包ID")
    private Long osPkgId;

    /**
     * 升级方式[0:非强制升级,1:强制升级]
     */
    @ApiModelProperty(value = "升级方式[0:非强制升级,1:强制升级]")
    private Integer upgradeMode;

    /**
     * 升级描述
     */
    @ApiModelProperty(value = "升级描述")
    private String remark;
}
