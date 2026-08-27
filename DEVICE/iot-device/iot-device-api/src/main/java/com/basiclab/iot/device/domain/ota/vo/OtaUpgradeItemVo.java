package com.basiclab.iot.device.domain.ota.vo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.io.Serializable;

/**
 * 设备待升级项（四类包统一返回结构，check 检测应答返回）
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@ApiModel(value = "OtaUpgradeItemVo对象", description = "设备待升级项")
public class OtaUpgradeItemVo implements Serializable {

    private static final long serialVersionUID = 1L;

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
     * 升级包ID
     */
    @ApiModelProperty(value = "升级包ID")
    private Long pkgId;

    /**
     * 包名称
     */
    @ApiModelProperty(value = "包名称")
    private String name;

    /**
     * 目标版本号
     */
    @ApiModelProperty(value = "目标版本号")
    private String version;

    /**
     * 是否强制升级[0:否,1:是]
     */
    @ApiModelProperty(value = "是否强制升级[0:否,1:是]")
    private Integer forceUpdate;

    /**
     * 是否关键版本[0:否,1:是]（关键版本不可跳过）
     */
    @ApiModelProperty(value = "是否关键版本[0:否,1:是]")
    private Integer mustPass;

    /**
     * 下载地址
     */
    @ApiModelProperty(value = "下载地址")
    private String downloadUrl;

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
     * 通道[1:测试,2:正式]
     */
    @ApiModelProperty(value = "通道[1:测试,2:正式]")
    private Integer channel;

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
}
