package com.basiclab.iot.device.controller.admin.rule_alarm_list.vo;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import com.basiclab.iot.common.domain.PageParam;
import org.springframework.format.annotation.DateTimeFormat;
import java.time.LocalDateTime;

import static com.basiclab.iot.common.utils.date.DateUtils.FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND;

@Schema(description = "管理后台 - 告警列分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class RuleAlarmListPageReqVO extends PageParam {

    @Schema(description = "告警时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] alarmTime;

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
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] processingTime;

}