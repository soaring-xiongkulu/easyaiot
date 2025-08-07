package com.basiclab.iot.device.controller.admin.product_event.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;

@Schema(description = "管理后台 - 产品模型事件新增/修改 Request VO")
@Data
public class ProductEventSaveReqVO {

    @Schema(description = "id", requiredMode = Schema.RequiredMode.REQUIRED, example = "18852")
    private Long id;

    @Schema(description = "事件名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "王五")
    @NotEmpty(message = "事件名称不能为空")
    private String eventName;

    @Schema(description = "事件code", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotEmpty(message = "事件code不能为空")
    private String eventCode;

    @Schema(description = "事件类型。	INFO_EVENT_TYPE：信息。	ALERT_EVENT_TYPE：告警。	ERROR_EVENT_TYPE：故障", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    @NotEmpty(message = "事件类型。	INFO_EVENT_TYPE：信息。	ALERT_EVENT_TYPE：告警。	ERROR_EVENT_TYPE：故障不能为空")
    private String eventType;

    @Schema(description = "模板code")
    private String templateCode;

    @Schema(description = "产品唯一标识", example = "3944")
    private String pid;

    @Schema(description = "状态(字典值：0启用  1停用)", example = "2")
    private String enabledStatus;

    @Schema(description = "描述", example = "你说的对")
    private String description;

    @Schema(description = "创建者")
    private String createBy;

    @Schema(description = "更新者")
    private String updateBy;

}