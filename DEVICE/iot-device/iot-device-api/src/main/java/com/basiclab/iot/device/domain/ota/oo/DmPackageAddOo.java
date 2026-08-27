package com.basiclab.iot.device.domain.ota.oo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import javax.validation.constraints.NotEmpty;
import java.io.Serializable;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc
 * @created 2025-05-28
 */
@Data
@ApiModel(value = "DmPackageOo对象", description = "版本包新增Oo")
public class DmPackageAddOo implements Serializable {

    private static final long serialVersionUID = 4046784516959790027L;
    /**
     * 包类型[0:软件包,1:固件包,2:APP包,3:PC包]
     */
    @ApiModelProperty(value = "包类型[0:软件包,1:固件包,2:APP包,3:PC包]")
    private Integer type;
    /**
     * 包名称
     */
    @ApiModelProperty(value = "包名称")
    private String name;
    /**
     * 产品ID(dm_product.id)
     */
    @ApiModelProperty(value = "产品ID(dm_product.id)")
    private Integer productId;
    /**
     * 适用产品标识（空=所有产品适用）
     */
    @ApiModelProperty(value = "适用产品标识（空=所有产品适用）")
    private String productIdentification;
    /**
     * 包版本号
     */
    @NotEmpty(message = "包版本号不能为空")
    @ApiModelProperty(value = "包版本号")
    private String version;
    /**
     * 升级方式[0:非强制升级,1:强制升级]
     */
    @ApiModelProperty(value = "升级方式[0:非强制升级,1:强制升级]")
    private Integer upgradeMode;
    /**
     * 包路径
     */
    @ApiModelProperty(value = "版本包地址")
    private String url;
    /**
     * 文件唯一码（md5）
     */
    @ApiModelProperty(value = "文件唯一码（md5）")
    private String md5;
    /**
     * 文件大小（字节）
     */
    @ApiModelProperty(value = "文件大小（字节）")
    private Long fileSize;
    /**
     * 原始文件名
     */
    @ApiModelProperty(value = "原始文件名")
    private String fileName;
    /**
     * 关键版本标识[0:否,1:是]
     */
    @ApiModelProperty(value = "关键版本标识[0:否,1:是]（关键版本不可跳过，需逐级升级）")
    private Integer keyVersionFlag;
    /**
     * 更新说明
     */
    @ApiModelProperty(value = "更新说明")
    private String changelog;
    /**
     * 系统类型
     */
    @ApiModelProperty(value = "系统类型")
    private String systemType;
    /**
     * 备注
     */
    @ApiModelProperty(value = "备注")
    private String remark;
}
