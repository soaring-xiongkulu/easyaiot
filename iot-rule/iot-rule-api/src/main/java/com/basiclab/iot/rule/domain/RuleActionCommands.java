package com.basiclab.iot.rule.domain;

import com.baomidou.mybatisplus.annotation.*;
import com.fasterxml.jackson.annotation.JsonFormat;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
* @description: ${description}
* @author EasyIoT
* @date: 2025-12-04 21:39
**/
/**
    * 动作命令信息表
    */
@ApiModel(value="动作命令执行信息表")
@Data
@AllArgsConstructor
@NoArgsConstructor
@TableName("rule_action_commands")
public class RuleActionCommands implements Serializable {

    @ApiModelProperty(value="主键id")
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 规则标识
     */
    @ApiModelProperty(value="动作类型  设备执行动作类型 " +
            "ALARM 告警动作 " +
            "MQTT mqtt动作  " +
            "DEVICE 设备指令下发动作 " +
            "KAFKA kafka消息发送动作等")
    private String actionType;

    /**
    * 规则标识
    */
    @ApiModelProperty(value="规则标识")
    private Long ruleId;

    /**
     * 规则标识
     */
    @ApiModelProperty(value="规则标识")
    private Long ruleConditionId;

    /**
    * 产品标识
    */
    @ApiModelProperty(value="产品标识")
    private String productIdentification;

    /**
    * 设备标识
    */
    @ApiModelProperty(value="设备标识")
    private String deviceIdentification;


    /**
    * json命令参数及参数值{"key":"value","key1":"value1"}
    */
    @ApiModelProperty(value="json命令参数及参数值{'key':'value','key1':'value1'}")
    private String actionContent;


    /** 创建者 */
    @TableField(value = "create_by", fill = FieldFill.INSERT)
    @ApiModelProperty(value = "创建者")
    private String createBy;

    /** 创建时间 */
    @TableField(value = "create_time", fill = FieldFill.INSERT)
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @ApiModelProperty(value = "创建时间")
    private LocalDateTime createTime;

    /** 更新者 */
    @TableField(value = "update_by", fill = FieldFill.INSERT_UPDATE)
    @ApiModelProperty(value = "更新时间")
    private String updateBy;

    /** 更新时间 */
    @TableField(value = "update_time", fill = FieldFill.INSERT_UPDATE)
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @ApiModelProperty(value = "更新时间")
    private LocalDateTime updateTime;


    private static final long serialVersionUID = 1L;
}