package com.basiclab.iot.device.domain.ota.vo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc
 * @created 2025-05-27
 */
@Data
@ApiModel(value = "PackageListVo对象", description = "版本包")
public class DmPackagePageVo implements Serializable {

    private static final long serialVersionUID = 7223864037660091822L;
    /**
     * 主键ID
     */
    @ApiModelProperty(value = "主键ID")
    private Long id;
    /**
     * 包类型[0:app,1:系统,2:电控]
     */
    @ApiModelProperty(value = "包类型[0:app,1:系统,2:电控]")
    private String type;
    /**
     * 包版本号
     */
    @ApiModelProperty(value = "包版本号")
    private String version;
    /**
     * 包名称
     */
    @ApiModelProperty(value = "包名称")
    private String name;
    /**
     * 升级方式[0:非强制升级,1:强制升级]
     */
    @ApiModelProperty(value = "升级方式[0:非强制升级,1:强制升级]")
    private Integer upgradeMode;
    /**
     * 上传时间
     */
    @ApiModelProperty(value = "上传时间")
    private LocalDateTime uploadTime;
    /**
     * 发布时间
     */
    @ApiModelProperty(value = "发布时间")
    private LocalDateTime publishTime;
    /**
     * 发布时间
     */
    @ApiModelProperty(value = "上传时间")
    private LocalDateTime updatedTime;
    /**
     * 关键版本标识[0:否,1:是]
     */
    @ApiModelProperty(value = "关键版本标识[0:否,1:是]")
    private Integer keyVersionFlag;
    /**
     * 状态[0:未验证,1:已验证,2:已发布]
     */
    @ApiModelProperty(value = "状态[0:未验证,1:已验证,2:已发布]")
    private Integer status;
    /**
     * 图片地址
     */
    @ApiModelProperty(value = "图片地址")
    private String url;
    /**
     * 系统类型
     */
    @ApiModelProperty(value = "系统类型")
    private Integer systemType;
    /**
     * 备注
     */
    @ApiModelProperty(value = "备注")
    private String remark;
}