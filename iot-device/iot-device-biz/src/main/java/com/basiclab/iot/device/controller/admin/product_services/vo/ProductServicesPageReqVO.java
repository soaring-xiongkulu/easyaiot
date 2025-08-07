package com.basiclab.iot.device.controller.admin.product_services.vo;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import com.basiclab.iot.common.domain.PageParam;
import org.springframework.format.annotation.DateTimeFormat;
import java.time.LocalDateTime;

import static com.basiclab.iot.common.utils.date.DateUtils.FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND;

@Schema(description = "管理后台 - 产品模型服务分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class ProductServicesPageReqVO extends PageParam {

    @Schema(description = "服务编码:支持英文大小写、数字、下划线和中划线")
    private String serviceCode;

    @Schema(description = "服务名称", example = "李四")
    private String serviceName;

    @Schema(description = "产品模版标识")
    private String templateCode;

    @Schema(description = "产品标识", example = "16556")
    private String pid;

    @Schema(description = "状态(字典值：0启用  1停用)", example = "1")
    private String status;

    @Schema(description = "服务的描述信息:文本描述，不影响实际功能，可配置为空字符串。	", example = "随便")
    private String description;

    @Schema(description = "创建者")
    private String createBy;

    @Schema(description = "创建时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] createTime;

    @Schema(description = "更新者")
    private String updateBy;

}