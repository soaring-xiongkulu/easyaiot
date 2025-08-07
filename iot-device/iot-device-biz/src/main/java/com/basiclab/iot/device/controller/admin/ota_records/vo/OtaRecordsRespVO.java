package com.basiclab.iot.device.controller.admin.ota_records.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import java.time.LocalDateTime;
import com.alibaba.excel.annotation.*;

@Schema(description = "管理后台 - OTA升级记录 Response VO")
@Data
@ExcelIgnoreUnannotated
public class OtaRecordsRespVO {

    @Schema(description = "主键", requiredMode = Schema.RequiredMode.REQUIRED, example = "19986")
    @ExcelProperty("主键")
    private Long id;

    @Schema(description = "任务ID，关联ota_upgrade_tasks表", requiredMode = Schema.RequiredMode.REQUIRED, example = "10252")
    @ExcelProperty("任务ID，关联ota_upgrade_tasks表")
    private Long taskId;

    @Schema(description = "设备标识", requiredMode = Schema.RequiredMode.REQUIRED, example = "26548")
    @ExcelProperty("设备标识")
    private String did;

    @Schema(description = "升级状态(0:待升级、1:升级中、2:升级成功、3:升级失败)", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    @ExcelProperty("升级状态(0:待升级、1:升级中、2:升级成功、3:升级失败)")
    private Short upgradeStatus;

    @Schema(description = "升级进度（百分比）", requiredMode = Schema.RequiredMode.REQUIRED)
    @ExcelProperty("升级进度（百分比）")
    private Short progress;

    @Schema(description = "错误代码")
    @ExcelProperty("错误代码")
    private String errorCode;

    @Schema(description = "错误信息")
    @ExcelProperty("错误信息")
    private String errorMessage;

    @Schema(description = "升级开始时间")
    @ExcelProperty("升级开始时间")
    private LocalDateTime startTime;

    @Schema(description = "升级结束时间")
    @ExcelProperty("升级结束时间")
    private LocalDateTime endTime;

    @Schema(description = "升级成功详细信息")
    @ExcelProperty("升级成功详细信息")
    private String successDetails;

    @Schema(description = "升级失败详细信息")
    @ExcelProperty("升级失败详细信息")
    private String failureDetails;

    @Schema(description = "升级过程日志")
    @ExcelProperty("升级过程日志")
    private String logDetails;

    @Schema(description = "描述", example = "你说的对")
    @ExcelProperty("描述")
    private String remark;

    @Schema(description = "记录创建时间", requiredMode = Schema.RequiredMode.REQUIRED)
    @ExcelProperty("记录创建时间")
    private LocalDateTime createdTime;

    @Schema(description = "创建人")
    @ExcelProperty("创建人")
    private Long createdBy;

    @Schema(description = "更新人")
    @ExcelProperty("更新人")
    private Long updatedBy;

    @Schema(description = "更新时间", requiredMode = Schema.RequiredMode.REQUIRED)
    @ExcelProperty("更新时间")
    private LocalDateTime updatedTime;

}