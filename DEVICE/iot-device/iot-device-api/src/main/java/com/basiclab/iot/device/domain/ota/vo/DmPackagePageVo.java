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
     * 包类型[0:软件包,1:固件包,2:APP包,3:PC包]
     */
    @ApiModelProperty(value = "包类型[0:软件包,1:固件包,2:APP包,3:PC包]")
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
     * 状态[0:未验证,1:测试中,2:已发布,3:待发布,4:已撤回]
     */
    @ApiModelProperty(value = "状态[0:未验证,1:测试中,2:已发布,3:待发布,4:已撤回]")
    private Integer status;
    /**
     * 包地址
     */
    @ApiModelProperty(value = "包地址")
    private String url;
    /**
     * 文件MD5值
     */
    @ApiModelProperty(value = "文件MD5值")
    private String fileMd5;
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
     * 更新说明
     */
    @ApiModelProperty(value = "更新说明")
    private String changelog;
    /**
     * 适用产品标识（空=所有产品适用）
     */
    @ApiModelProperty(value = "适用产品标识（空=所有产品适用）")
    private String productIdentification;
    /**
     * 发布策略[0:全量,1:灰度]
     */
    @ApiModelProperty(value = "发布策略[0:全量,1:灰度]")
    private Integer publishStrategy;
    /**
     * 灰度阶梯[1:设备级,2:产品级,3:全量]
     */
    @ApiModelProperty(value = "灰度阶梯[1:设备级,2:产品级,3:全量]")
    private Integer grayLadder;
    /**
     * 测试是否通过[0:否,1:是]
     */
    @ApiModelProperty(value = "测试是否通过[0:否,1:是]")
    private Integer testPassed;
    /**
     * 撤回原因
     */
    @ApiModelProperty(value = "撤回原因")
    private String withdrawReason;
    /**
     * 撤回时间
     */
    @ApiModelProperty(value = "撤回时间")
    private LocalDateTime withdrawTime;
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
