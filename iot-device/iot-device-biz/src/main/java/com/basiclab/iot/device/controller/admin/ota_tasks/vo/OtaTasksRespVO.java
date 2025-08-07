package com.basiclab.iot.device.controller.admin.ota_tasks.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import java.time.LocalDateTime;
import com.alibaba.excel.annotation.*;

@Schema(description = "管理后台 - OTA升级任务 Response VO")
@Data
@ExcelIgnoreUnannotated
public class OtaTasksRespVO {

    @Schema(description = "主键", requiredMode = Schema.RequiredMode.REQUIRED, example = "30509")
    @ExcelProperty("主键")
    private Long id;

    @Schema(description = "升级包ID，关联ota_upgrades表", requiredMode = Schema.RequiredMode.REQUIRED, example = "19197")
    @ExcelProperty("升级包ID，关联ota_upgrades表")
    private Long upgradeId;

    @Schema(description = "任务名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "赵六")
    @ExcelProperty("任务名称")
    private String taskName;

    @Schema(description = "任务状态(0:待发布、1:进行中、2:已完成、3:已取消)", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    @ExcelProperty("任务状态(0:待发布、1:进行中、2:已完成、3:已取消)")
    private Short taskStatus;

    @Schema(description = "计划执行时间")
    @ExcelProperty("计划执行时间")
    private LocalDateTime scheduledTime;

    @Schema(description = "任务描述", example = "你说的对")
    @ExcelProperty("任务描述")
    private String description;

    @Schema(description = "描述", example = "随便")
    @ExcelProperty("描述")
    private String remark;

    @Schema(description = "创建人")
    @ExcelProperty("创建人")
    private Long createdBy;

    @Schema(description = "创建时间", requiredMode = Schema.RequiredMode.REQUIRED)
    @ExcelProperty("创建时间")
    private LocalDateTime createdTime;

    @Schema(description = "更新人")
    @ExcelProperty("更新人")
    private Long updatedBy;

    @Schema(description = "更新时间", requiredMode = Schema.RequiredMode.REQUIRED)
    @ExcelProperty("更新时间")
    private LocalDateTime updatedTime;

}