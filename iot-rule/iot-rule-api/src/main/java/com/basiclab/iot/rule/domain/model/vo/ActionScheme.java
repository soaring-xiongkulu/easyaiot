package com.basiclab.iot.rule.domain.model.vo;

import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

/**
 * @author IoT
 * @desc    动作内容
 * @created 2024-07-15
 */
@Data
public class ActionScheme {

    /**
     * 规则id
     */
    private Long ruleId;

    /**
     * 条件id
     */
    private Long ruleConditionId;

    /**
     * 动作类型   设备动作  MQTT  HTTP  短信  kafka等
     */
    private String actionType;

    /**
     * 动作内容 json格式
     */
    private String actionContent;


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

}
