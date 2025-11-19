package com.basiclab.iot.device.domain.ota.oo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.io.Serializable;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc
 * @created 2025-05-28
 */
@Data
@ApiModel(value = "DmPackageEditOo对象", description = "版本包编辑Oo")
public class DmPackageEditOo implements Serializable {
    private static final long serialVersionUID = 4046784516959790027L;
    /**
     * 主键ID
     */
    @ApiModelProperty(value = "主键ID")
    private Long id;
    /**
     * 包类型[0:app,1:系统,2:电控]
     */
    @ApiModelProperty(value = "包类型[0:app,1:系统,2:电控]")
    private Integer type;
    /**
     * 包名称
     */
    @ApiModelProperty(value = "包名称")
    private String name;
    /**
     * 产品类型ID(dm_product_type.id)
     */
    @ApiModelProperty(value = "产品类型ID(dm_product_type.id)")
    private Integer productTypeId;
    /**
     * 产品ID(dm_product.id)
     */
    @ApiModelProperty(value = "产品ID(dm_product.id)")
    private Integer productId;
    /**
     * 包版本号
     */
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
    @ApiModelProperty(value = "包路径")
    private String url;
    /**
     * 文件Md5值
     */
    @ApiModelProperty(value = "文件Md5值")
    private String md5;
    /**
     * 关键版本标识[0:否,1:是]
     */
    @ApiModelProperty(value = "关键版本标识[0:否,1:是]")
    private Integer keyVersionFlag;
    /**
     * 备注
     */
    @ApiModelProperty(value = "备注")
    private String remark;
}