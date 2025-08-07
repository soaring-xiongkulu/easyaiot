package com.basiclab.iot.device.controller.admin.product_commands.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import java.time.LocalDateTime;
import com.alibaba.excel.annotation.*;

@Schema(description = "管理后台 - 产品模型设备服务命令 Response VO")
@Data
@ExcelIgnoreUnannotated
public class ProductCommandsRespVO {

    @Schema(description = "命令id", requiredMode = Schema.RequiredMode.REQUIRED, example = "8307")
    @ExcelProperty("命令id")
    private Long id;

    @Schema(description = "服务ID", requiredMode = Schema.RequiredMode.REQUIRED, example = "22067")
    @ExcelProperty("服务ID")
    private Long serviceId;

    @Schema(description = "指示命令的名字，如门磁的LOCK命令、摄像头的VIDEO_RECORD命令，命令名与参数共同构成一个完整的命令。	支持英文大小写、数字及下划线，长度[2,50]。	", requiredMode = Schema.RequiredMode.REQUIRED, example = "李四")
    @ExcelProperty("指示命令的名字，如门磁的LOCK命令、摄像头的VIDEO_RECORD命令，命令名与参数共同构成一个完整的命令。	支持英文大小写、数字及下划线，长度[2,50]。	")
    private String name;

    @Schema(description = "命令描述。", example = "随便")
    @ExcelProperty("命令描述。")
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