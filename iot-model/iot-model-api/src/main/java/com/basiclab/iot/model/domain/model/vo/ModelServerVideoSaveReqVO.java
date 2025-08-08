package com.basiclab.iot.model.domain.model.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;

@Schema(description = "管理后台 - 模型服务视频新增/修改 Request VO")
@Data
public class ModelServerVideoSaveReqVO {

    @Schema(description = "主键ID", example = "31453")
    private Long id;

    @Schema(description = "模型服务ID", example = "28227")
    @NotNull(message = "模型服务ID不能为空")
    private Long modelServerId;

    @Schema(description = "模型ID", example = "3225")
    private Long modelId;

    @Schema(description = "视频地址")
    @NotEmpty(message = "视频地址不能为空")
    private String videoPath;

    @Schema(description = "标注视频地址")
    private String annoVideoPath;

    @Schema(description = "封面地址")
    private String coverPath;

    @Schema(description = "描述", example = "随便")
    private String description;

    @Schema(description = "视频分辨率")
    private String videoResolution;

    @Schema(description = "视频时长")
    private Integer duration;

    @Schema(description = "视频后缀")
    private String suffix;

    @Schema(description = "视频文件大小")
    private Long fileSize;

}