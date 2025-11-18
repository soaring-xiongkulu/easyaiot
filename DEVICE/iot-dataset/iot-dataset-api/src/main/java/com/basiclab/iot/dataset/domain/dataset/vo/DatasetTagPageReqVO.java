package com.basiclab.iot.dataset.domain.dataset.vo;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import com.basiclab.iot.common.domain.PageParam;

import javax.validation.constraints.NotEmpty;

/**
 * DatasetTagPageReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 数据集标签分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class DatasetTagPageReqVO extends PageParam {

    @Schema(description = "标签名称", example = "张三")
    private String name;

    @Schema(description = "标签颜色")
    private String color;

    @Schema(description = "数据集ID", example = "13288")
    private Long datasetId;

    @Schema(description = "数据仓ID", example = "13910")
    private Long warehouseId;

    @Schema(description = "描述", example = "你说的对")
    private String description;

    @Schema(description = "快捷键", example = "1")
    private Integer shortcut;

}