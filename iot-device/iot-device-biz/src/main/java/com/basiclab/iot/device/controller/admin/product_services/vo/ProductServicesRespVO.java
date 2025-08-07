package com.basiclab.iot.device.controller.admin.product_services.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import java.time.LocalDateTime;
import com.alibaba.excel.annotation.*;

@Schema(description = "管理后台 - 产品模型服务 Response VO")
@Data
@ExcelIgnoreUnannotated
public class ProductServicesRespVO {

    @Schema(description = "服务id", requiredMode = Schema.RequiredMode.REQUIRED, example = "20066")
    @ExcelProperty("服务id")
    private Long id;

    @Schema(description = "服务编码:支持英文大小写、数字、下划线和中划线", requiredMode = Schema.RequiredMode.REQUIRED)
    @ExcelProperty("服务编码:支持英文大小写、数字、下划线和中划线")
    private String serviceCode;

    @Schema(description = "服务名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "李四")
    @ExcelProperty("服务名称")
    private String serviceName;

    @Schema(description = "产品模版标识")
    @ExcelProperty("产品模版标识")
    private String templateCode;

    @Schema(description = "产品标识", example = "16556")
    @ExcelProperty("产品标识")
    private String pid;

    @Schema(description = "状态(字典值：0启用  1停用)", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    @ExcelProperty("状态(字典值：0启用  1停用)")
    private String status;

    @Schema(description = "服务的描述信息:文本描述，不影响实际功能，可配置为空字符串。	", example = "随便")
    @ExcelProperty("服务的描述信息:文本描述，不影响实际功能，可配置为空字符串。	")
    private String description;

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