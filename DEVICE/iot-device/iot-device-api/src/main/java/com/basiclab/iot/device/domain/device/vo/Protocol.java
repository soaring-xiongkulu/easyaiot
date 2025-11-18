package com.basiclab.iot.device.domain.device.vo;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.*;
import lombok.experimental.Accessors;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
* @description: ${description}
* @packagename: com.basiclab.iot.device.api.domain.protocol
* @author 翱翔的雄库鲁
* @email andywebjava@163.com
* @wechat EasyAIoT2025
* @date: 2025-07-01 17:56
**/

/**
    * 协议信息表
    */
@ApiModel(value="协议信息表")
@Data
@NoArgsConstructor
@AllArgsConstructor
@ToString(callSuper = true)
@Accessors(chain = true)
@Builder
@TableName("protocol")
public class Protocol implements Serializable {
    /**
    * id
    */
    @ApiModelProperty(value="id")
    @TableId(type = IdType.AUTO)
    private Long id;

    @ApiModelProperty(value="应用ID")
    private String appId;
    /**
    * 产品标识
    */
    @ApiModelProperty(value="产品标识")
    private String productIdentification;

    /**
    * 协议名称
    */
    @ApiModelProperty(value="协议名称")
    private String protocolName;

    /**
    * 协议标识
    */
    @ApiModelProperty(value="协议标识")
    private String protocolIdentification;

    /**
    * 协议版本
    */
    @ApiModelProperty(value="协议版本")
    private String protocolVersion;

    /**
    * 协议类型 ：mqtt || coap || modbus || http
    */
    @ApiModelProperty(value="协议类型 ：mqtt || coap || modbus || http")
    private String protocolType;

    /**
    * 协议语言
    */
    @ApiModelProperty(value="协议语言")
    private String protocolVoice;

    /**
    * 类名
    */
    @ApiModelProperty(value="类名")
    private String className;

    /**
    * 文件地址
    */
    @ApiModelProperty(value="文件地址")
    private String filePath;

    /**
    * 内容
    */
    @ApiModelProperty(value="内容")
    private String content;

    /**
    * 状态(字典值：0启用  1停用)
    */
    @ApiModelProperty(value="状态(字典值：0启用  1停用)")
    private String status;

    /**
    * 创建者
    */
    @ApiModelProperty(value="创建者")
    private String createBy;

    /**
    * 创建时间
    */
    @ApiModelProperty(value="创建时间")
    private LocalDateTime createTime;

    /**
    * 更新者
    */
    @ApiModelProperty(value="更新者")
    private String updateBy;

    /**
    * 更新时间
    */
    @ApiModelProperty(value="更新时间")
    private LocalDateTime updateTime;

    /**
    * 备注
    */
    @ApiModelProperty(value="备注")
    private String remark;

    private static final long serialVersionUID = 1L;
}