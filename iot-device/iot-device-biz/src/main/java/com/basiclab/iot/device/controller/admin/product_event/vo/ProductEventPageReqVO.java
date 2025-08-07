package com.basiclab.iot.device.controller.admin.product_event.vo;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import com.basiclab.iot.common.domain.PageParam;
import org.springframework.format.annotation.DateTimeFormat;
import java.time.LocalDateTime;

import static com.basiclab.iot.common.utils.date.DateUtils.FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND;

@Schema(description = "管理后台 - 产品模型事件分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class ProductEventPageReqVO extends PageParam {

    @Schema(description = "事件名称", example = "王五")
    private String eventName;

    @Schema(description = "事件code")
    private String eventCode;

    @Schema(description = "事件类型。	INFO_EVENT_TYPE：信息。	ALERT_EVENT_TYPE：告警。	ERROR_EVENT_TYPE：故障", example = "1")
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

    @Schema(description = "创建时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] createTime;

    @Schema(description = "更新者")
    private String updateBy;

}