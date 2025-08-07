package com.basiclab.iot.device.controller.admin.rule_alarm_list.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import java.time.LocalDateTime;

@Schema(description = "管理后台 - 告警列新增/修改 Request VO")
@Data
public class RuleAlarmListSaveReqVO {

    @Schema(description = "主键", requiredMode = Schema.RequiredMode.REQUIRED, example = "29955")
    private Long id;

    @Schema(description = "告警时间")
    private LocalDateTime alarmTime;

    @Schema(description = "告警名称", example = "王五")
    private String alarmName;

    @Schema(description = "告警级别")
    private Integer alarmLevel;

    @Schema(description = "告警描述")
    private String alarmDescribe;

    @Schema(description = "处理结果 0 未处理 1已处理")
    private Integer processingResult;

    @Schema(description = "处理意见")
    private String processingOpinions;

    @Schema(description = "告警内容")
    private String alarmContent;

    @Schema(description = "处理人")
    private String processingPeople;

    @Schema(description = "处理时间")
    private LocalDateTime processingTime;

}