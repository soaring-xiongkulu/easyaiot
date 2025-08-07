package com.basiclab.iot.device.controller.admin.product_services.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;

@Schema(description = "管理后台 - 产品模型服务新增/修改 Request VO")
@Data
public class ProductServicesSaveReqVO {

    @Schema(description = "服务id", requiredMode = Schema.RequiredMode.REQUIRED, example = "20066")
    private Long id;

    @Schema(description = "服务编码:支持英文大小写、数字、下划线和中划线", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotEmpty(message = "服务编码:支持英文大小写、数字、下划线和中划线不能为空")
    private String serviceCode;

    @Schema(description = "服务名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "李四")
    @NotEmpty(message = "服务名称不能为空")
    private String serviceName;

    @Schema(description = "产品模版标识")
    private String templateCode;

    @Schema(description = "产品标识", example = "16556")
    private String pid;

    @Schema(description = "状态(字典值：0启用  1停用)", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    @NotEmpty(message = "状态(字典值：0启用  1停用)不能为空")
    private String status;

    @Schema(description = "服务的描述信息:文本描述，不影响实际功能，可配置为空字符串。	", example = "随便")
    private String description;

    @Schema(description = "创建者")
    private String createBy;

    @Schema(description = "更新者")
    private String updateBy;

}