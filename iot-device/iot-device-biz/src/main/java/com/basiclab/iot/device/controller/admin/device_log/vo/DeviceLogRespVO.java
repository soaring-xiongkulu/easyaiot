package com.basiclab.iot.device.controller.admin.device_log.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import java.time.LocalDateTime;
import com.alibaba.excel.annotation.*;

@Schema(description = "管理后台 - 设备日志 Response VO")
@Data
@ExcelIgnoreUnannotated
public class DeviceLogRespVO {

    @Schema(description = "id", requiredMode = Schema.RequiredMode.REQUIRED, example = "4942")
    @ExcelProperty("id")
    private Long id;

    @Schema(description = "设备唯一标识", example = "3362")
    @ExcelProperty("设备唯一标识")
    private String did;

    @Schema(description = "文件地址", example = "https://www.iocoder.cn")
    @ExcelProperty("文件地址")
    private String fileUrl;

    @Schema(description = "上传时间")
    @ExcelProperty("上传时间")
    private LocalDateTime uploadTime;

    @Schema(description = "文件名称", example = "赵六")
    @ExcelProperty("文件名称")
    private String fileName;

    @Schema(description = "文件大小")
    @ExcelProperty("文件大小")
    private Long fileSize;

    @Schema(description = "备注", example = "你说的对")
    @ExcelProperty("备注")
    private String remark;

    @Schema(description = "状态[0:成功, 1:未开始, 2:上传中, 3:失败]", example = "2")
    @ExcelProperty("状态[0:成功, 1:未开始, 2:上传中, 3:失败]")
    private Short status;

    @Schema(description = "创建者")
    @ExcelProperty("创建者")
    private String createdBy;

    @Schema(description = "创建时间")
    @ExcelProperty("创建时间")
    private LocalDateTime createdTime;

    @Schema(description = "更新者")
    @ExcelProperty("更新者")
    private String updatedBy;

    @Schema(description = "更新时间")
    @ExcelProperty("更新时间")
    private LocalDateTime updatedTime;

}