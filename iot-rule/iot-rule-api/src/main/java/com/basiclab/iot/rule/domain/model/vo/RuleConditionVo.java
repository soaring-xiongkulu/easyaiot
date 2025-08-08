package com.basiclab.iot.rule.domain.model.vo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.util.List;

/**
 * @author EasyAIoT
 * @desc   组外条件对象
 * @created 2025-07-15
 */
@Data
@ApiModel("规则条件传输对象")
public class RuleConditionVo {

    @ApiModelProperty(value = "逻辑运算符   AND OR")
    private String logicalOperator;
    @ApiModelProperty(value = "条件类型")
    private String type;
    @ApiModelProperty(value = "条件列表 单个组内条件")
    private List<ChildConditionVo> conditions;
    @ApiModelProperty(value = "唯一标识")
    private String uuid;


    @ApiModel(description = "子条件类")
    @Data
    public static class ChildConditionVo {
        @ApiModelProperty(value = "逻辑运算符   AND OR")
        private String logicalOperator;
        @ApiModelProperty(value = "条件类型")
        private String type;
        @ApiModelProperty(value = "唯一标识")
        private String uuid;
        @ApiModelProperty(value = "左参数")
        private LeftParam leftParam;
        @ApiModelProperty(value = "组内比较运算符   > < >= <= == !=")
        private Operator operator;
        @ApiModelProperty(value = "右参数列表")
        private RightParam rightParams;
    }


    @ApiModel(description = "左参数")
    @Data
    public static class LeftParam {
        @ApiModelProperty(value = "属性Id")
        private Long propertyId;
        @ApiModelProperty(value = "数据类型")
        private String dataType;
        @ApiModelProperty(value = "产品标识")
        private String productIdentification;
        @ApiModelProperty(value = "设备标识   ALL表示所有设备")
        private String deviceIdentification;
        @ApiModelProperty(value = "描述  即属性code")
        private String desc;
    }

    @ApiModel(description = "比较操作符")
    @Data
    public static class Operator {
        @ApiModelProperty(value = "值")
        private String value;
        @ApiModelProperty(value = "描述")
        private String desc;
    }

    @ApiModel(description = "右边比较值")
    @Data
    public static class RightParam {
        @ApiModelProperty(value = "参数类型")
        private String type;
        @ApiModelProperty(value = "值")
        private String value;
        @ApiModelProperty(value = "描述")
        private String desc;
    }


    

}
