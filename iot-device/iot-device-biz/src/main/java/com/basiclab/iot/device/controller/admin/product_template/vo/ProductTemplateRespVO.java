package com.basiclab.iot.device.controller.admin.product_template.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import java.time.LocalDateTime;
import com.alibaba.excel.annotation.*;

@Schema(description = "管理后台 - 产品模板 Response VO")
@Data
@ExcelIgnoreUnannotated
public class ProductTemplateRespVO {

    @Schema(description = "id", requiredMode = Schema.RequiredMode.REQUIRED, example = "17029")
    @ExcelProperty("id")
    private Long id;

    @Schema(description = "应用ID", requiredMode = Schema.RequiredMode.REQUIRED, example = "11797")
    @ExcelProperty("应用ID")
    private String appId;

    @Schema(description = "产品模版标识", requiredMode = Schema.RequiredMode.REQUIRED)
    @ExcelProperty("产品模版标识")
    private String templateCode;

    @Schema(description = "产品模板名称:自定义，支持中文、英文大小写、数字、下划线和中划线", requiredMode = Schema.RequiredMode.REQUIRED, example = "李四")
    @ExcelProperty("产品模板名称:自定义，支持中文、英文大小写、数字、下划线和中划线")
    private String templateName;

    @Schema(description = "状态(字典值：启用  停用)", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    @ExcelProperty("状态(字典值：启用  停用)")
    private String status;

    @Schema(description = "产品模型模板描述", example = "你说的对")
    @ExcelProperty("产品模型模板描述")
    private String remark;

    @Schema(description = "创建者")
    @ExcelProperty("创建者")
    private String createBy;

    @Schema(description = "创建时间", requiredMode = Schema.RequiredMode.REQUIRED)
    @ExcelProperty("创建时间")
    private LocalDateTime createTime;

    @Schema(description = "更新者")
    @ExcelProperty("更新者")
    private String updateBy;

}