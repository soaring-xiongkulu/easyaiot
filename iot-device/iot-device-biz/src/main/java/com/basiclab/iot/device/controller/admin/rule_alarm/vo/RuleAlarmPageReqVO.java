package com.basiclab.iot.device.controller.admin.rule_alarm.vo;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import com.basiclab.iot.common.domain.PageParam;
import org.springframework.format.annotation.DateTimeFormat;
import java.time.LocalDateTime;

import static com.basiclab.iot.common.utils.date.DateUtils.FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND;

@Schema(description = "管理后台 - 规则告警分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class RuleAlarmPageReqVO extends PageParam {

    @Schema(description = "规则ID", example = "15919")
    private Long ruleId;

    @Schema(description = "告警规则名称", example = "王五")
    private String ruleAlarmName;

    @Schema(description = "告警状态0 未启动  1运行中", example = "1")
    private Integer ruleAlarmStatus;

    @Schema(description = "告警规则描述", example = "随便")
    private String ruleAlarmRemark;

    @Schema(description = "告警级别")
    private Integer ruleLevel;

    @Schema(description = "通知方式", example = "2")
    private Integer noticeType;

    @Schema(description = "创建人")
    private String createBy;

    @Schema(description = "创建时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] createTime;

    @Schema(description = "更新人")
    private String updateBy;

}