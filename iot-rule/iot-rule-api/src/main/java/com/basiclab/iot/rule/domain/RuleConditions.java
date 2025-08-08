package com.basiclab.iot.rule.domain;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.fasterxml.jackson.annotation.JsonFormat;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
* @program: basiclab
* @description: ${description}
* @Author: Basiclab
* @e-mainl: 853017739@qq.com
* @date: 2024-07-21 18:50
**/

/**
 * 规则条件表
 */
@ApiModel(value = "规则条件表")
@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class RuleConditions implements Serializable {
    /**
     * 主键
     */
    @ApiModelProperty(value = "主键")
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 规则ID
     */
    @ApiModelProperty(value = "规则ID")
    private Long ruleId;

    /**
     * 条件类型(0:匹配设备触发、1:指定设备触发、2:按策略定时触发)
     */
    @ApiModelProperty(value = "条件类型(0:匹配设备触发、1:按策略定时触发)")
    private Integer conditionType;

    /**
     * 条件对象 json存储
     */
    @ApiModelProperty(value = "条件对象 json存储")
    private String conditionScheme;

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
