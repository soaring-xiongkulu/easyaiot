package com.basiclab.iot.device.domain.device.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;

@Schema(description = "管理后台 - 设备分组新增/修改 Request VO")
@Data
public class DeviceGroupSaveReqVO {

    @Schema(description = "设备ID", example = "19517")
    private Long id;

    @Schema(description = "分组ID", example = "李四")
    @NotEmpty(message = "分组ID不能为空")
    private String groupName;

    @Schema(description = "创建者")
    private String createBy;

    @Schema(description = "更新者")
    private String updateBy;

}