package com.basiclab.iot.dataset.domain.warehouse.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;

/**
 * WarehouseSaveReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 数据仓新增/修改 Request VO")
@Data
public class WarehouseSaveReqVO {

    @Schema(description = "主键ID", example = "21541")
    private Long id;

    @Schema(description = "仓库名称", example = "李四")
    @NotEmpty(message = "仓库名称不能为空")
    private String name;

    @Schema(description = "封面地址")
    private String coverPath;

    @Schema(description = "描述", example = "你猜")
    private String description;

}