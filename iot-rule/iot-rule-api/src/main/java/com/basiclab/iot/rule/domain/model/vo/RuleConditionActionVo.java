package com.basiclab.iot.rule.domain.model.vo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.util.List;

/**
 * @author IoT
 * @desc
 * @created 2024-07-15
 */
@Data
@ApiModel("规则条件和动作传输对象")
public class RuleConditionActionVo {

    @ApiModelProperty(value = "动作集合对象")
    private List<ActionScheme> conditionActionUpdateVos;

    @ApiModelProperty(value = "条件数据")
    private String conditionScheme;

    @ApiModelProperty(value = "规则id")
    private Long ruleId;

    @ApiModelProperty(value = "条件类型(0:匹配设备触发、1:指定设备触发、2:按策略定时触发)")
    private Integer conditionType;

    @ApiModelProperty(value = "状态")
    private  Integer status;

    @ApiModelProperty(value = "id")
    private Long id;

}
