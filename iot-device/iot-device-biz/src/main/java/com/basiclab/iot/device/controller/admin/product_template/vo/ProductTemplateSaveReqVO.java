package com.basiclab.iot.device.controller.admin.product_template.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;

@Schema(description = "管理后台 - 产品模板新增/修改 Request VO")
@Data
public class ProductTemplateSaveReqVO {

    @Schema(description = "id", requiredMode = Schema.RequiredMode.REQUIRED, example = "17029")
    private Long id;

    @Schema(description = "应用ID", requiredMode = Schema.RequiredMode.REQUIRED, example = "11797")
    @NotEmpty(message = "应用ID不能为空")
    private String appId;

    @Schema(description = "产品模版标识", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotEmpty(message = "产品模版标识不能为空")
    private String templateCode;

    @Schema(description = "产品模板名称:自定义，支持中文、英文大小写、数字、下划线和中划线", requiredMode = Schema.RequiredMode.REQUIRED, example = "李四")
    @NotEmpty(message = "产品模板名称:自定义，支持中文、英文大小写、数字、下划线和中划线不能为空")
    private String templateName;

    @Schema(description = "状态(字典值：启用  停用)", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    @NotEmpty(message = "状态(字典值：启用  停用)不能为空")
    private String status;

    @Schema(description = "产品模型模板描述", example = "你说的对")
    private String remark;

    @Schema(description = "创建者")
    private String createBy;

    @Schema(description = "更新者")
    private String updateBy;

}