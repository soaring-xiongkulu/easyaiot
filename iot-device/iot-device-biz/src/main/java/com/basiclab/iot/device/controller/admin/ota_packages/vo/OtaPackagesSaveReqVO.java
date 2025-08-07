package com.basiclab.iot.device.controller.admin.ota_packages.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;
import java.time.LocalDateTime;

@Schema(description = "管理后台 - OTA升级包新增/修改 Request VO")
@Data
public class OtaPackagesSaveReqVO {

    @Schema(description = "主键", requiredMode = Schema.RequiredMode.REQUIRED, example = "18516")
    private Long id;

    @Schema(description = "应用ID", requiredMode = Schema.RequiredMode.REQUIRED, example = "25182")
    @NotEmpty(message = "应用ID不能为空")
    private String appId;

    @Schema(description = "包名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "王五")
    @NotEmpty(message = "包名称不能为空")
    private String packageName;

    @Schema(description = "升级包类型(0:软件包、1:固件包)", requiredMode = Schema.RequiredMode.REQUIRED, example = "2")
    @NotNull(message = "升级包类型(0:软件包、1:固件包)不能为空")
    private Short packageType;

    @Schema(description = "产品标识", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotEmpty(message = "产品标识不能为空")
    private String productIdentification;

    @Schema(description = "升级包版本号", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotEmpty(message = "升级包版本号不能为空")
    private String version;

    @Schema(description = "升级包的位置", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotEmpty(message = "升级包的位置不能为空")
    private String fileLocation;

    @Schema(description = "状态", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    @NotNull(message = "状态不能为空")
    private Short status;

    @Schema(description = "升级包功能描述", example = "随便")
    private String description;

    @Schema(description = "自定义信息")
    private String customInfo;

    @Schema(description = "描述", example = "随便")
    private String remark;

    @Schema(description = "创建人")
    private Long createdBy;

    @Schema(description = "创建时间", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotNull(message = "创建时间不能为空")
    private LocalDateTime createdTime;

    @Schema(description = "更新人")
    private Long updatedBy;

    @Schema(description = "更新时间", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotNull(message = "更新时间不能为空")
    private LocalDateTime updatedTime;

}