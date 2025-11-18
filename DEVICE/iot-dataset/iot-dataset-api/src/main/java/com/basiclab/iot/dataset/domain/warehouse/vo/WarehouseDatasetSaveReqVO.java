package com.basiclab.iot.dataset.domain.warehouse.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;

/**
 * WarehouseDatasetSaveReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 数据仓数据集关联新增/修改 Request VO")
@Data
public class WarehouseDatasetSaveReqVO {

    @Schema(description = "主键ID", example = "2401")
    private Long id;

    @Schema(description = "数据集ID", example = "24462")
    @NotNull(message = "数据集ID不能为空")
    private Long datasetId;

    @Schema(description = "数据仓ID", example = "28615")
    @NotNull(message = "数据仓ID不能为空")
    private Long warehouseId;

    @Schema(description = "计划同步数量", example = "15407")
    @NotNull(message = "计划同步数量不能为空")
    private Integer planSyncCount;

    @Schema(description = "已同步数量", example = "13675")
    @NotNull(message = "已同步数量不能为空")
    private Integer syncCount;

    @Schema(description = "同步状态[0:未同步,1:同步中,2:同步完成]", example = "2")
    @NotNull(message = "同步状态[0:未同步,1:同步中,2:同步完成]不能为空")
    private Integer syncStatus;

    @Schema(description = "同步失败数量", example = "20923")
    @NotNull(message = "同步失败数量不能为空")
    private Integer failCount;

}