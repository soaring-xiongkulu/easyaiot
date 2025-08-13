package com.basiclab.iot.model.domain.model.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import java.time.LocalDateTime;
import com.alibaba.excel.annotation.*;

@Schema(description = "管理后台 - 模型测试图片 Response VO")
@Data
@ExcelIgnoreUnannotated
public class ModelServerTestImageRespVO {

    @Schema(description = "主键ID", example = "5620")
    @ExcelProperty("主键ID")
    private Long id;

    @Schema(description = "测试模型服务ID", example = "30001")
    @ExcelProperty("测试模型服务ID")
    private Long modelServerTestId;

    @Schema(description = "模型ID", example = "19598")
    @ExcelProperty("模型ID")
    private Long modelId;

    @Schema(description = "数据集图片ID", example = "6520")
    @ExcelProperty("数据集图片ID")
    private Long datasetImageId;

    @Schema(description = "标注时间")
    @ExcelProperty("标注时间")
    private LocalDateTime annoTime;

    @Schema(description = "标注后图片路径")
    @ExcelProperty("标注后图片路径")
    private String annoImagePath;

    @Schema(description = "选取次数", example = "9495")
    @ExcelProperty("选取次数")
    private Integer modificationCount;

}