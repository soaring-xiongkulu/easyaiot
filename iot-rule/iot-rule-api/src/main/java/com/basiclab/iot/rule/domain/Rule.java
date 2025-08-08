package com.basiclab.iot.rule.domain;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.basiclab.iot.common.annotation.Excel;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * @program: basiclab
 * @description: ${description}
 * @Author: Basiclab
 * @e-mainl: 853017739@qq.com
 * @date: 2024-11-18 20:39
 **/

/**
 * 规则信息表
 */
@ApiModel(value = "规则信息表")
@Data
@AllArgsConstructor
@NoArgsConstructor
public class Rule implements Serializable {
    /**
     * 主键
     */
    @ApiModelProperty(value = "主键")
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 应用ID
     */
    @ApiModelProperty(value = "应用ID  应用场景")
    private String appId;

    /**
     * 条件类型(0:匹配设备触发、1:指定设备触发、2:按策略定时触发)
     */
    @ApiModelProperty(value = "条件类型(0:匹配设备触发、1:按策略定时触发)")
    private Integer conditionType;

    /**
     * 规则标识
     */
    @ApiModelProperty(value = "规则标识")
    private String ruleIdentification;

    /**
     * 预约执行时间
     */
    @ApiModelProperty(value = "cron表达式  可指定生效时间")
    private String cronExpression;

    /**
     * 定时任务执行策略
     */
//    @ApiModelProperty(value = "生效类型  0  一直生效   1指定时间生效")
    @ApiModelProperty(value = "0=默认,1=立即触发执行,2=触发一次执行,3=不触发立即执行")
    private String misfirePolicy;

    /** 是否并发执行（0允许 1禁止） */
    @Excel(name = "并发执行", readConverterExp = "0=允许,1=禁止")
    private String concurrent;

    /**
     * 规则名称
     */
    @ApiModelProperty(value = "规则名称")
    private String ruleName;

    /**
     * 任务标识
     */
    @ApiModelProperty(value = "任务标识 实际为jobid")
    private String jobIdentification;

    /**
     * 状态(字典值：0启用  1停用)  与定时任务中的状态保持一致
     */
    @ApiModelProperty(value = "状态(字典值：0启用  1停用)")
    private String status;

    /**
     * 规则描述，可以为空
     */
    @ApiModelProperty(value = "规则描述，可以为空")
    private String remark;


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