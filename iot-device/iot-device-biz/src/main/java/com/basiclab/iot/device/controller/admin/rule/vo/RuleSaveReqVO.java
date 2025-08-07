package com.basiclab.iot.device.controller.admin.rule.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;

@Schema(description = "管理后台 - 规则信息新增/修改 Request VO")
@Data
public class RuleSaveReqVO {

    @Schema(description = "主键", requiredMode = Schema.RequiredMode.REQUIRED, example = "7441")
    private Long id;

    @Schema(description = "应用ID", requiredMode = Schema.RequiredMode.REQUIRED, example = "11787")
    @NotEmpty(message = "应用ID不能为空")
    private String appId;

    @Schema(description = "规则标识", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotEmpty(message = "规则标识不能为空")
    private String ruleCode;

    @Schema(description = "规则名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "赵六")
    @NotEmpty(message = "规则名称不能为空")
    private String ruleName;

    @Schema(description = "任务标识", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotEmpty(message = "任务标识不能为空")
    private String jobCode;

    @Schema(description = "状态(字典值：0启用  1停用)", requiredMode = Schema.RequiredMode.REQUIRED, example = "2")
    @NotEmpty(message = "状态(字典值：0启用  1停用)不能为空")
    private String status;

    @Schema(description = "触发机制（0:全部，1:任意一个）")
    private Short triggering;

    @Schema(description = "规则描述，可以为空", example = "你说的对")
    private String remark;

    @Schema(description = "创建人")
    private String createBy;

    @Schema(description = "更新人")
    private String updateBy;

}