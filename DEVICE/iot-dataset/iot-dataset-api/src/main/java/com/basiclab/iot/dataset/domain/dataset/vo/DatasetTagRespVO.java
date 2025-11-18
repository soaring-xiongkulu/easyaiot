package com.basiclab.iot.dataset.domain.dataset.vo;

import com.basiclab.iot.common.domain.BaseEntity;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;
import com.alibaba.excel.annotation.*;

import javax.validation.constraints.NotEmpty;

@Schema(description = "管理后台 - 数据集标签 Response VO")
@Data

/**
 * DatasetTagRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@ExcelIgnoreUnannotated
public class DatasetTagRespVO extends BaseEntity {

    @Schema(description = "主键ID", example = "10257")
    @ExcelProperty("主键ID")
    private Long id;

    @Schema(description = "标签名称", example = "张三")
    @ExcelProperty("标签名称")
    private String name;

    @Schema(description = "标签颜色", example = "#FF5733")
    @ExcelProperty("标签颜色")
    private String color;

    @Schema(description = "数据集ID", example = "13288")
    @ExcelProperty("数据集ID")
    private Long datasetId;

    @Schema(description = "数据仓ID", example = "13910")
    @ExcelProperty("数据仓ID")
    private Long warehouseId;

    @Schema(description = "描述", example = "你说的对")
    @ExcelProperty("描述")
    private String description;

    @Schema(description = "快捷键", example = "1")
    @ExcelProperty("快捷键")
    private Integer shortcut;

}