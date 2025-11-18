package com.basiclab.iot.dataset.domain.warehouse.vo;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import com.basiclab.iot.common.domain.PageParam;

@Schema(description = "管理后台 - 数据仓数据集关联分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)

/**
 * WarehouseDatasetPageReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public class WarehouseDatasetPageReqVO extends PageParam {

    @Schema(description = "数据集ID", example = "24462")
    private Long datasetId;

    @Schema(description = "数据仓ID", example = "28615")
    private Long warehouseId;

    @Schema(description = "计划同步数量", example = "15407")
    private Integer planSyncCount;

    @Schema(description = "已同步数量", example = "13675")
    private Integer syncCount;

    @Schema(description = "同步状态[0:未同步,1:同步中,2:同步完成]", example = "2")
    private Integer syncStatus;

    @Schema(description = "同步失败数量", example = "20923")
    private Integer failCount;

}