package com.basiclab.iot.device.controller.admin.ota_tasks.vo;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import com.basiclab.iot.common.domain.PageParam;
import org.springframework.format.annotation.DateTimeFormat;
import java.time.LocalDateTime;

import static com.basiclab.iot.common.utils.date.DateUtils.FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND;

@Schema(description = "管理后台 - OTA升级任务分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class OtaTasksPageReqVO extends PageParam {

    @Schema(description = "升级包ID，关联ota_upgrades表", example = "19197")
    private Long upgradeId;

    @Schema(description = "任务名称", example = "赵六")
    private String taskName;

    @Schema(description = "任务状态(0:待发布、1:进行中、2:已完成、3:已取消)", example = "1")
    private Short taskStatus;

    @Schema(description = "计划执行时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] scheduledTime;

    @Schema(description = "任务描述", example = "你说的对")
    private String description;

    @Schema(description = "描述", example = "随便")
    private String remark;

    @Schema(description = "创建人")
    private Long createdBy;

    @Schema(description = "创建时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] createdTime;

    @Schema(description = "更新人")
    private Long updatedBy;

    @Schema(description = "更新时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] updatedTime;

}