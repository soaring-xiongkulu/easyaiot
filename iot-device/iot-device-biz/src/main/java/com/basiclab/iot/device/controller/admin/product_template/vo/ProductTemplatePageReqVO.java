package com.basiclab.iot.device.controller.admin.product_template.vo;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import com.basiclab.iot.common.domain.PageParam;
import org.springframework.format.annotation.DateTimeFormat;
import java.time.LocalDateTime;

import static com.basiclab.iot.common.utils.date.DateUtils.FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND;

@Schema(description = "管理后台 - 产品模板分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class ProductTemplatePageReqVO extends PageParam {

    @Schema(description = "应用ID", example = "11797")
    private String appId;

    @Schema(description = "产品模版标识")
    private String templateCode;

    @Schema(description = "产品模板名称:自定义，支持中文、英文大小写、数字、下划线和中划线", example = "李四")
    private String templateName;

    @Schema(description = "状态(字典值：启用  停用)", example = "1")
    private String status;

    @Schema(description = "产品模型模板描述", example = "你说的对")
    private String remark;

    @Schema(description = "创建者")
    private String createBy;

    @Schema(description = "创建时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] createTime;

    @Schema(description = "更新者")
    private String updateBy;

}