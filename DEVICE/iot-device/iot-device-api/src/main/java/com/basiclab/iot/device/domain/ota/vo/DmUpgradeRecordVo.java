package com.basiclab.iot.device.domain.ota.vo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 升级记录
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@ApiModel(value = "DmUpgradeRecordVo对象", description = "升级记录")
public class DmUpgradeRecordVo implements Serializable {

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
     * 包类型[0:软件包,1:固件包,2:APP包,3:PC包]
     */
    @ApiModelProperty(value = "包类型[0:软件包,1:固件包,2:APP包,3:PC包]")
    private Integer type;

    /**
     * 包类型名称
     */
    @ApiModelProperty(value = "包类型名称")
    private String typeName;

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
     * 产品标识
     */
    @ApiModelProperty(value = "产品标识")
    private String productIdentification;

    /**
     * 升级前版本
     */
    @ApiModelProperty(value = "升级前版本")
    private String fromVersion;

    /**
     * 升级目标版本
     */
    @ApiModelProperty(value = "升级目标版本")
    private String toVersion;

    /**
     * 通道[1:测试,2:正式]
     */
    @ApiModelProperty(value = "通道[1:测试,2:正式]")
    private Integer channel;

    /**
     * 升级阶段[0:检测,1:命中,2:下载完成,3:下载失败,4:MD5校验失败,5:安装结果,6:启动成功]
     */
    @ApiModelProperty(value = "升级阶段[0:检测,1:命中,2:下载完成,3:下载失败,4:MD5校验失败,5:安装结果,6:启动成功]")
    private Integer phase;

    /**
     * 升级阶段名称
     */
    @ApiModelProperty(value = "升级阶段名称")
    private String phaseName;

    /**
     * 升级进度（0-100）
     */
    @ApiModelProperty(value = "升级进度（0-100）")
    private Integer progress;

    /**
     * 是否成功[0:否,1:是]
     */
    @ApiModelProperty(value = "是否成功[0:否,1:是]")
    private Integer success;

    /**
     * 错误码
     */
    @ApiModelProperty(value = "错误码")
    private String errorCode;

    /**
     * 错误信息
     */
    @ApiModelProperty(value = "错误信息")
    private String errorMsg;

    /**
     * 升级耗时（毫秒）
     */
    @ApiModelProperty(value = "升级耗时（毫秒）")
    private Long costMs;

    /**
     * 升级发生时间
     */
    @ApiModelProperty(value = "升级发生时间")
    private LocalDateTime upgradeTime;

    /**
     * 创建时间
     */
    @ApiModelProperty(value = "创建时间")
    private LocalDateTime createdTime;
}
