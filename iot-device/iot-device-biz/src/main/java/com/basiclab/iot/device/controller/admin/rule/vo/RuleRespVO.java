package com.basiclab.iot.device.controller.admin.rule.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import java.time.LocalDateTime;
import com.alibaba.excel.annotation.*;

@Schema(description = "管理后台 - 规则信息 Response VO")
@Data
@ExcelIgnoreUnannotated
public class RuleRespVO {

    @Schema(description = "主键", requiredMode = Schema.RequiredMode.REQUIRED, example = "7441")
    @ExcelProperty("主键")
    private Long id;

    @Schema(description = "应用ID", requiredMode = Schema.RequiredMode.REQUIRED, example = "11787")
    @ExcelProperty("应用ID")
    private String appId;

    @Schema(description = "规则标识", requiredMode = Schema.RequiredMode.REQUIRED)
    @ExcelProperty("规则标识")
    private String ruleCode;

    @Schema(description = "规则名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "赵六")
    @ExcelProperty("规则名称")
    private String ruleName;

    @Schema(description = "任务标识", requiredMode = Schema.RequiredMode.REQUIRED)
    @ExcelProperty("任务标识")
    private String jobCode;

    @Schema(description = "状态(字典值：0启用  1停用)", requiredMode = Schema.RequiredMode.REQUIRED, example = "2")
    @ExcelProperty("状态(字典值：0启用  1停用)")
    private String status;

    @Schema(description = "触发机制（0:全部，1:任意一个）")
    @ExcelProperty("触发机制（0:全部，1:任意一个）")
    private Short triggering;

    @Schema(description = "规则描述，可以为空", example = "你说的对")
    @ExcelProperty("规则描述，可以为空")
    private String remark;

    @Schema(description = "创建人")
    @ExcelProperty("创建人")
    private String createBy;

    @Schema(description = "创建时间", requiredMode = Schema.RequiredMode.REQUIRED)
    @ExcelProperty("创建时间")
    private LocalDateTime createTime;

    @Schema(description = "更新人")
    @ExcelProperty("更新人")
    private String updateBy;

}