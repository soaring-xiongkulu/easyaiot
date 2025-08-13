package com.basiclab.iot.model.domain.model.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import java.time.LocalDateTime;
import com.alibaba.excel.annotation.*;

@Schema(description = "管理后台 - 模型测试视频 Response VO")
@Data
@ExcelIgnoreUnannotated
public class ModelServerTestVideoRespVO {

    @Schema(description = "主键ID", example = "7926")
    @ExcelProperty("主键ID")
    private Long id;

    @Schema(description = "测试模型服务ID", example = "16349")
    @ExcelProperty("测试模型服务ID")
    private Long modelServerTestId;

    @Schema(description = "模型ID", example = "15989")
    @ExcelProperty("模型ID")
    private Long modelId;

    @Schema(description = "数据集视频ID", example = "15909")
    @ExcelProperty("数据集视频ID")
    private Long datasetVideoId;

    @Schema(description = "标注时间")
    @ExcelProperty("标注时间")
    private LocalDateTime annoTime;

    @Schema(description = "标注后视频路径")
    @ExcelProperty("标注后视频路径")
    private String annoVideoPath;

    @Schema(description = "状态[0:运行中,1:成功,2:失败]")
    @ExcelProperty("状态[0:运行中,1:成功,2:失败]")
    private Short state;

}