package com.basiclab.iot.dataset.domain.dataset.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;

/**
 * DatasetTagSaveReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 数据集标签新增/修改 Request VO")
@Data
public class DatasetTagSaveReqVO {

    @Schema(description = "主键ID", example = "10257")
    private Long id;

    @Schema(description = "标签名称", example = "张三")
    @NotEmpty(message = "标签名称不能为空")
    private String name;

    @Schema(description = "标签颜色")
    private String color;

    @Schema(description = "数据集ID", example = "13288")
    @NotNull(message = "数据集ID不能为空")
    private Long datasetId;

    @Schema(description = "数据仓ID", example = "13910")
    private Long warehouseId;

    @Schema(description = "描述", example = "你说的对")
    private String description;

    @Schema(description = "快捷键", example = "1")
    @NotNull(message = "快捷键不能为空")
    private Integer shortcut;

}