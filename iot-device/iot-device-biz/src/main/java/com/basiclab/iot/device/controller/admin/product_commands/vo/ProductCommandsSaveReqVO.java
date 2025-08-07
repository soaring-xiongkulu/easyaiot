package com.basiclab.iot.device.controller.admin.product_commands.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;

@Schema(description = "管理后台 - 产品模型设备服务命令新增/修改 Request VO")
@Data
public class ProductCommandsSaveReqVO {

    @Schema(description = "命令id", requiredMode = Schema.RequiredMode.REQUIRED, example = "8307")
    private Long id;

    @Schema(description = "服务ID", requiredMode = Schema.RequiredMode.REQUIRED, example = "22067")
    @NotNull(message = "服务ID不能为空")
    private Long serviceId;

    @Schema(description = "指示命令的名字，如门磁的LOCK命令、摄像头的VIDEO_RECORD命令，命令名与参数共同构成一个完整的命令。	支持英文大小写、数字及下划线，长度[2,50]。	", requiredMode = Schema.RequiredMode.REQUIRED, example = "李四")
    @NotEmpty(message = "指示命令的名字，如门磁的LOCK命令、摄像头的VIDEO_RECORD命令，命令名与参数共同构成一个完整的命令。	支持英文大小写、数字及下划线，长度[2,50]。	不能为空")
    private String name;

    @Schema(description = "命令描述。", example = "随便")
    private String description;

    @Schema(description = "创建者")
    private String createBy;

    @Schema(description = "更新者")
    private String updateBy;

}