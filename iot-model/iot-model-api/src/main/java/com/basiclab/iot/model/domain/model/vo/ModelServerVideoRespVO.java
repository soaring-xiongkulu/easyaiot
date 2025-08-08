package com.basiclab.iot.model.domain.model.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;
import com.alibaba.excel.annotation.*;

@Schema(description = "管理后台 - 模型服务视频 Response VO")
@Data
@ExcelIgnoreUnannotated
public class ModelServerVideoRespVO {

    @Schema(description = "主键ID", example = "31453")
    @ExcelProperty("主键ID")
    private Long id;

    @Schema(description = "模型服务ID", example = "28227")
    @ExcelProperty("模型服务ID")
    private Long modelServerId;

    @Schema(description = "模型ID", example = "3225")
    @ExcelProperty("模型ID")
    private Long modelId;

    @Schema(description = "视频地址")
    @ExcelProperty("视频地址")
    private String videoPath;

    @Schema(description = "标注视频地址")
    @ExcelProperty("标注视频地址")
    private String annoVideoPath;

    @Schema(description = "封面地址")
    @ExcelProperty("封面地址")
    private String coverPath;

    @Schema(description = "描述", example = "随便")
    @ExcelProperty("描述")
    private String description;

    @Schema(description = "视频分辨率")
    @ExcelProperty("视频分辨率")
    private String videoResolution;

    @Schema(description = "视频时长")
    @ExcelProperty("视频时长")
    private Integer duration;

    @Schema(description = "视频后缀")
    @ExcelProperty("视频后缀")
    private String suffix;

    @Schema(description = "视频文件大小")
    @ExcelProperty("视频文件大小")
    private Long fileSize;

}