package com.basiclab.iot.device.controller.admin.ota_records.vo;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import com.basiclab.iot.common.domain.PageParam;
import org.springframework.format.annotation.DateTimeFormat;
import java.time.LocalDateTime;

import static com.basiclab.iot.common.utils.date.DateUtils.FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND;

@Schema(description = "管理后台 - OTA升级记录分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class OtaRecordsPageReqVO extends PageParam {

    @Schema(description = "任务ID，关联ota_upgrade_tasks表", example = "10252")
    private Long taskId;

    @Schema(description = "设备标识", example = "26548")
    private String did;

    @Schema(description = "升级状态(0:待升级、1:升级中、2:升级成功、3:升级失败)", example = "1")
    private Short upgradeStatus;

    @Schema(description = "升级进度（百分比）")
    private Short progress;

    @Schema(description = "错误代码")
    private String errorCode;

    @Schema(description = "错误信息")
    private String errorMessage;

    @Schema(description = "升级开始时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] startTime;

    @Schema(description = "升级结束时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] endTime;

    @Schema(description = "升级成功详细信息")
    private String successDetails;

    @Schema(description = "升级失败详细信息")
    private String failureDetails;

    @Schema(description = "升级过程日志")
    private String logDetails;

    @Schema(description = "描述", example = "你说的对")
    private String remark;

    @Schema(description = "记录创建时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] createdTime;

    @Schema(description = "创建人")
    private Long createdBy;

    @Schema(description = "更新人")
    private Long updatedBy;

    @Schema(description = "更新时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] updatedTime;

}