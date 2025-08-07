package com.basiclab.iot.device.controller.admin.ota_tasks.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;
import java.time.LocalDateTime;

@Schema(description = "管理后台 - OTA升级任务新增/修改 Request VO")
@Data
public class OtaTasksSaveReqVO {

    @Schema(description = "主键", requiredMode = Schema.RequiredMode.REQUIRED, example = "30509")
    private Long id;

    @Schema(description = "升级包ID，关联ota_upgrades表", requiredMode = Schema.RequiredMode.REQUIRED, example = "19197")
    @NotNull(message = "升级包ID，关联ota_upgrades表不能为空")
    private Long upgradeId;

    @Schema(description = "任务名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "赵六")
    @NotEmpty(message = "任务名称不能为空")
    private String taskName;

    @Schema(description = "任务状态(0:待发布、1:进行中、2:已完成、3:已取消)", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    @NotNull(message = "任务状态(0:待发布、1:进行中、2:已完成、3:已取消)不能为空")
    private Short taskStatus;

    @Schema(description = "计划执行时间")
    private LocalDateTime scheduledTime;

    @Schema(description = "任务描述", example = "你说的对")
    private String description;

    @Schema(description = "描述", example = "随便")
    private String remark;

    @Schema(description = "创建人")
    private Long createdBy;

    @Schema(description = "创建时间", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotNull(message = "创建时间不能为空")
    private LocalDateTime createdTime;

    @Schema(description = "更新人")
    private Long updatedBy;

    @Schema(description = "更新时间", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotNull(message = "更新时间不能为空")
    private LocalDateTime updatedTime;

}