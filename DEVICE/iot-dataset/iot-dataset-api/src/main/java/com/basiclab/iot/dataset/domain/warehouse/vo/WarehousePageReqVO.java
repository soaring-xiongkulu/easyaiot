package com.basiclab.iot.dataset.domain.warehouse.vo;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import com.basiclab.iot.common.domain.PageParam;

/**
 * WarehousePageReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 数据仓分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class WarehousePageReqVO extends PageParam {

    @Schema(description = "仓库名称", example = "李四")
    private String name;

    @Schema(description = "封面地址")
    private String coverPath;

    @Schema(description = "描述", example = "你猜")
    private String description;

}