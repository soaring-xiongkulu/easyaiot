package com.basiclab.iot.device.controller.admin.rule_alarm.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import java.time.LocalDateTime;
import com.alibaba.excel.annotation.*;

@Schema(description = "管理后台 - 规则告警 Response VO")
@Data
@ExcelIgnoreUnannotated
public class RuleAlarmRespVO {

    @Schema(description = "规则告警ID", requiredMode = Schema.RequiredMode.REQUIRED, example = "13623")
    @ExcelProperty("规则告警ID")
    private Long id;

    @Schema(description = "规则ID", example = "15919")
    @ExcelProperty("规则ID")
    private Long ruleId;

    @Schema(description = "告警规则名称", example = "王五")
    @ExcelProperty("告警规则名称")
    private String ruleAlarmName;

    @Schema(description = "告警状态0 未启动  1运行中", example = "1")
    @ExcelProperty("告警状态0 未启动  1运行中")
    private Integer ruleAlarmStatus;

    @Schema(description = "告警规则描述", example = "随便")
    @ExcelProperty("告警规则描述")
    private String ruleAlarmRemark;

    @Schema(description = "告警级别")
    @ExcelProperty("告警级别")
    private Integer ruleLevel;

    @Schema(description = "通知方式", example = "2")
    @ExcelProperty("通知方式")
    private Integer noticeType;

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