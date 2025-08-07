package com.basiclab.iot.device.controller.admin.device_log.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import java.time.LocalDateTime;

@Schema(description = "管理后台 - 设备日志新增/修改 Request VO")
@Data
public class DeviceLogSaveReqVO {

    @Schema(description = "id", requiredMode = Schema.RequiredMode.REQUIRED, example = "4942")
    private Long id;

    @Schema(description = "设备唯一标识", example = "3362")
    private String did;

    @Schema(description = "文件地址", example = "https://www.iocoder.cn")
    private String fileUrl;

    @Schema(description = "上传时间")
    private LocalDateTime uploadTime;

    @Schema(description = "文件名称", example = "赵六")
    private String fileName;

    @Schema(description = "文件大小")
    private Long fileSize;

    @Schema(description = "备注", example = "你说的对")
    private String remark;

    @Schema(description = "状态[0:成功, 1:未开始, 2:上传中, 3:失败]", example = "2")
    private Short status;

    @Schema(description = "创建者")
    private String createdBy;

    @Schema(description = "创建时间")
    private LocalDateTime createdTime;

    @Schema(description = "更新者")
    private String updatedBy;

    @Schema(description = "更新时间")
    private LocalDateTime updatedTime;

}