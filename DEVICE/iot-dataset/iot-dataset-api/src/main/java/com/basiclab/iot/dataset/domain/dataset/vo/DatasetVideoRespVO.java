package com.basiclab.iot.dataset.domain.dataset.vo;

import com.basiclab.iot.common.domain.BaseEntity;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;
import com.alibaba.excel.annotation.*;

import javax.validation.constraints.NotEmpty;

/**
 * DatasetVideoRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 视频数据集 Response VO")
@Data
@ExcelIgnoreUnannotated
public class DatasetVideoRespVO extends BaseEntity {

    @Schema(description = "主键ID", example = "11001")
    @ExcelProperty("主键ID")
    private Long id;

    @Schema(description = "数据集ID", example = "18192")
    @ExcelProperty("数据集ID")
    private Long datasetId;

    @Schema(description = "视频地址")
    @ExcelProperty("视频地址")
    private String videoPath;

    @Schema(description = "封面地址")
    @ExcelProperty("封面地址")
    private String coverPath;

    @Schema(description = "视频名称")
    @ExcelProperty("视频名称")
    private String name;

    @Schema(description = "描述", example = "随便")
    @ExcelProperty("描述")
    private String description;

}