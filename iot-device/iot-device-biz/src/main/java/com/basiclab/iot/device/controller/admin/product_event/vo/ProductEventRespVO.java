package com.basiclab.iot.device.controller.admin.product_event.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import java.time.LocalDateTime;
import com.alibaba.excel.annotation.*;

@Schema(description = "管理后台 - 产品模型事件 Response VO")
@Data
@ExcelIgnoreUnannotated
public class ProductEventRespVO {

    @Schema(description = "id", requiredMode = Schema.RequiredMode.REQUIRED, example = "18852")
    @ExcelProperty("id")
    private Long id;

    @Schema(description = "事件名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "王五")
    @ExcelProperty("事件名称")
    private String eventName;

    @Schema(description = "事件code", requiredMode = Schema.RequiredMode.REQUIRED)
    @ExcelProperty("事件code")
    private String eventCode;

    @Schema(description = "事件类型。	INFO_EVENT_TYPE：信息。	ALERT_EVENT_TYPE：告警。	ERROR_EVENT_TYPE：故障", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    @ExcelProperty("事件类型。	INFO_EVENT_TYPE：信息。	ALERT_EVENT_TYPE：告警。	ERROR_EVENT_TYPE：故障")
    private String eventType;

    @Schema(description = "模板code")
    @ExcelProperty("模板code")
    private String templateCode;

    @Schema(description = "产品唯一标识", example = "3944")
    @ExcelProperty("产品唯一标识")
    private String pid;

    @Schema(description = "状态(字典值：0启用  1停用)", example = "2")
    @ExcelProperty("状态(字典值：0启用  1停用)")
    private String enabledStatus;

    @Schema(description = "描述", example = "你说的对")
    @ExcelProperty("描述")
    private String description;

    @Schema(description = "创建者")
    @ExcelProperty("创建者")
    private String createBy;

    @Schema(description = "创建时间")
    @ExcelProperty("创建时间")
    private LocalDateTime createTime;

    @Schema(description = "更新者")
    @ExcelProperty("更新者")
    private String updateBy;

}