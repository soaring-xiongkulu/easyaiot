package com.basiclab.iot.rule.domain.model.vo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.util.List;

/**
 * @author EasyAIoT
 * @desc
 * @created 2025-07-10
 */
@Data
@ApiModel("前端规则传输对象")
public class RuleVo {

    /**
     * id
     */
    private String id;

    /**
     * 规则id
     */
    @ApiModelProperty(value = "规则id")
    private String ruleId;

    /**
     * 规则名称
     */
    @ApiModelProperty(value = "规则名称")
    private String ruleName;

    /**
     * 类型   暂时不考虑数据流
     */
    @ApiModelProperty(value = "类型   scense 场景 ")
    private String type;

    /**
     * 状态(字典值：0启用  1停用)
     */
    @ApiModelProperty(value = "状态(字典值：0启用  1停用)")
    private String status;

    /**
     * 条件类型(0:匹配设备触发、1:指定设备触发、2:按策略定时触发)
     */
    @ApiModelProperty(value = "条件类型(0:匹配设备触发、1:指定设备触发、2:按策略定时触发)")
    private String conditionType;

    @ApiModelProperty(value = "条件过滤信息（某个熟悉过滤信息 如 满足温度=1）")
    private List<String> conditionScheme;

    @ApiModelProperty(value = "执行动作信息（满足条件后所需执行的动作）")
    private List<ActionScheme> actionScheme;

}
