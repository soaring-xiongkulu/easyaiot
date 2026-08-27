package com.basiclab.iot.device.domain.ota.vo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 测试白名单记录
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@ApiModel(value = "DmVerifyVo对象", description = "测试白名单记录")
public class DmVerifyVo implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 主键ID
     */
    @ApiModelProperty(value = "主键ID")
    private Long id;

    /**
     * 版本包ID
     */
    @ApiModelProperty(value = "版本包ID")
    private Long pkgId;

    /**
     * 版本包名称
     */
    @ApiModelProperty(value = "版本包名称")
    private String pkgName;

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

    /**
     * 状态[1:有效,0:已移除]
     */
    @ApiModelProperty(value = "状态[1:有效,0:已移除]")
    private Integer status;

    /**
     * 备注
     */
    @ApiModelProperty(value = "备注")
    private String remark;

    /**
     * 创建时间
     */
    @ApiModelProperty(value = "创建时间")
    private LocalDateTime createdTime;
}
