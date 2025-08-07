package com.basiclab.iot.device.controller.admin.ota_packages.vo;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import com.basiclab.iot.common.domain.PageParam;
import org.springframework.format.annotation.DateTimeFormat;
import java.time.LocalDateTime;

import static com.basiclab.iot.common.utils.date.DateUtils.FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND;

@Schema(description = "管理后台 - OTA升级包分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class OtaPackagesPageReqVO extends PageParam {

    @Schema(description = "应用ID", example = "25182")
    private String appId;

    @Schema(description = "包名称", example = "王五")
    private String packageName;

    @Schema(description = "升级包类型(0:软件包、1:固件包)", example = "2")
    private Short packageType;

    @Schema(description = "产品标识")
    private String productIdentification;

    @Schema(description = "升级包版本号")
    private String version;

    @Schema(description = "升级包的位置")
    private String fileLocation;

    @Schema(description = "状态", example = "1")
    private Short status;

    @Schema(description = "升级包功能描述", example = "随便")
    private String description;

    @Schema(description = "自定义信息")
    private String customInfo;

    @Schema(description = "描述", example = "随便")
    private String remark;

    @Schema(description = "创建人")
    private Long createdBy;

    @Schema(description = "创建时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] createdTime;

    @Schema(description = "更新人")
    private Long updatedBy;

    @Schema(description = "更新时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] updatedTime;

}