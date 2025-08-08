
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
 * @author IoT
 * @desc    规则日志
 * @created 2024-07-11
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@ApiModel("规则日志")
@Builder
public class RuleLog implements Serializable {


    @TableId(type = IdType.AUTO)
    private String id;

    @ApiModelProperty("规则id")
    private Long ruleId;

    @ApiModelProperty("规则状态   initial:初始   unmatched_condition:未成功匹配条件  matched_condition:成功匹配条件  " +
            "executing_action:执行动作中     executed_action:执行动作完成      executed_fail:执行动作失败")
    private String state;

    @ApiModelProperty("规则执行内容")
    private String content;

    @ApiModelProperty("规则是否成功  0:失败   1:成功")
    private Integer success;

    @ApiModelProperty("日志记录时间")
    private LocalDateTime logAtTime;


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
