package com.basiclab.iot.device.domain.ota.vo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 设备版本档案
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@ApiModel(value = "DmDeviceVersionVo对象", description = "设备版本档案")
public class DmDeviceVersionVo implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 主键ID
     */
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
     * 软件包ID
     */
    @ApiModelProperty(value = "软件包ID")
    private Long appPkgId;

    /**
     * 软件包名称
     */
    @ApiModelProperty(value = "软件包名称")
    private String appPkgName;

    /**
     * 固件包ID
     */
    @ApiModelProperty(value = "固件包ID")
    private Long osPkgId;

    /**
     * 固件包名称
     */
    @ApiModelProperty(value = "固件包名称")
    private String osPkgName;

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

    /**
     * 创建时间
     */
    @ApiModelProperty(value = "创建时间")
    private LocalDateTime createdTime;

    /**
     * 更新时间
     */
    @ApiModelProperty(value = "更新时间")
    private LocalDateTime updatedTime;
}
