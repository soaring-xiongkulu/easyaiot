package com.basiclab.iot.device.controller.admin.rule_conditions.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;

@Schema(description = "管理后台 - 规则条件新增/修改 Request VO")
@Data
public class RuleConditionsSaveReqVO {

    @Schema(description = "主键", requiredMode = Schema.RequiredMode.REQUIRED, example = "8281")
    private Long id;

    @Schema(description = "规则ID", requiredMode = Schema.RequiredMode.REQUIRED, example = "15131")
    @NotNull(message = "规则ID不能为空")
    private Long ruleId;

    @Schema(description = "条件类型(0:匹配设备触发、1:指定设备触发、2:按策略定时触发)", requiredMode = Schema.RequiredMode.REQUIRED, example = "2")
    @NotNull(message = "条件类型(0:匹配设备触发、1:指定设备触发、2:按策略定时触发)不能为空")
    private Short conditionType;

    @Schema(description = "设备标识(匹配设备设备类型存储一个产品下所有的设备标识逗号分隔，指定设备触发存储指定的设备标识)", example = "23118")
    private String did;

    @Schema(description = "产品标识", example = "24713")
    private String pid;

    @Schema(description = "服务ID", example = "25308")
    private Long serviceId;

    @Schema(description = "属性ID", example = "15591")
    private Long propertiesId;

    @Schema(description = "比较模式	<	<=	>	>=	==	!=	in	between")
    private String comparisonMode;

    @Schema(description = "比较值		between类型传值例子  [10,15] 必须是两位，且数字不能重复	判断数据是否处于一个离散的取值范围内，例如输入[1,2,3,4]，取值范围是1、2、3、4四个值，如果比较值类型为float(double)，两个float（double）型数值相差在0.000001范围内即为相等")
    private String comparisonValue;

    @Schema(description = "创建人")
    private String createBy;

    @Schema(description = "更新人")
    private String updateBy;

}