package com.basiclab.iot.device.controller.admin.rule.vo;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import com.basiclab.iot.common.domain.PageParam;
import org.springframework.format.annotation.DateTimeFormat;
import java.time.LocalDateTime;

import static com.basiclab.iot.common.utils.date.DateUtils.FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND;

@Schema(description = "管理后台 - 规则信息分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class RulePageReqVO extends PageParam {

    @Schema(description = "应用ID", example = "11787")
    private String appId;

    @Schema(description = "规则标识")
    private String ruleCode;

    @Schema(description = "规则名称", example = "赵六")
    private String ruleName;

    @Schema(description = "任务标识")
    private String jobCode;

    @Schema(description = "状态(字典值：0启用  1停用)", example = "2")
    private String status;

    @Schema(description = "触发机制（0:全部，1:任意一个）")
    private Short triggering;

    @Schema(description = "规则描述，可以为空", example = "你说的对")
    private String remark;

    @Schema(description = "创建人")
    private String createBy;

    @Schema(description = "创建时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] createTime;

    @Schema(description = "更新人")
    private String updateBy;

}