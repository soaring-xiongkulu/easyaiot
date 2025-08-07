package com.basiclab.iot.device.controller.admin.ota_packages.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import java.time.LocalDateTime;
import com.alibaba.excel.annotation.*;

@Schema(description = "管理后台 - OTA升级包 Response VO")
@Data
@ExcelIgnoreUnannotated
public class OtaPackagesRespVO {

    @Schema(description = "主键", requiredMode = Schema.RequiredMode.REQUIRED, example = "18516")
    @ExcelProperty("主键")
    private Long id;

    @Schema(description = "应用ID", requiredMode = Schema.RequiredMode.REQUIRED, example = "25182")
    @ExcelProperty("应用ID")
    private String appId;

    @Schema(description = "包名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "王五")
    @ExcelProperty("包名称")
    private String packageName;

    @Schema(description = "升级包类型(0:软件包、1:固件包)", requiredMode = Schema.RequiredMode.REQUIRED, example = "2")
    @ExcelProperty("升级包类型(0:软件包、1:固件包)")
    private Short packageType;

    @Schema(description = "产品标识", requiredMode = Schema.RequiredMode.REQUIRED)
    @ExcelProperty("产品标识")
    private String productIdentification;

    @Schema(description = "升级包版本号", requiredMode = Schema.RequiredMode.REQUIRED)
    @ExcelProperty("升级包版本号")
    private String version;

    @Schema(description = "升级包的位置", requiredMode = Schema.RequiredMode.REQUIRED)
    @ExcelProperty("升级包的位置")
    private String fileLocation;

    @Schema(description = "状态", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    @ExcelProperty("状态")
    private Short status;

    @Schema(description = "升级包功能描述", example = "随便")
    @ExcelProperty("升级包功能描述")
    private String description;

    @Schema(description = "自定义信息")
    @ExcelProperty("自定义信息")
    private String customInfo;

    @Schema(description = "描述", example = "随便")
    @ExcelProperty("描述")
    private String remark;

    @Schema(description = "创建人")
    @ExcelProperty("创建人")
    private Long createdBy;

    @Schema(description = "创建时间", requiredMode = Schema.RequiredMode.REQUIRED)
    @ExcelProperty("创建时间")
    private LocalDateTime createdTime;

    @Schema(description = "更新人")
    @ExcelProperty("更新人")
    private Long updatedBy;

    @Schema(description = "更新时间", requiredMode = Schema.RequiredMode.REQUIRED)
    @ExcelProperty("更新时间")
    private LocalDateTime updatedTime;

}